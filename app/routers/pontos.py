from pathlib import Path
from uuid import uuid4

from fastapi import APIRouter, Depends, HTTPException, Query, Request, UploadFile, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
import jwt
from sqlalchemy import or_
from sqlalchemy.orm import Session, selectinload

from app.database import get_db, using_mongodb
from app.models.avaliacao import Avaliacao
from app.models.ponto import PontoTuristico, StatusPonto
from app.models.ponto_salvo import PontoSalvo
from app.models.usuario import TipoUsuario, Usuario
from app.schemas.ponto import (
    AvaliacaoInput,
    AvaliacaoResponse,
    PontoAtualizacaoInput,
    PontoCadastroInput,
    PontoResponse,
)
from app.security import ALGORITHM, SECRET_KEY, exigir_admin, obter_usuario_atual

router = APIRouter(prefix="/pontos", tags=["Pontos turisticos"])
optional_bearer_scheme = HTTPBearer(auto_error=False)
UPLOAD_DIR = Path(__file__).resolve().parents[1] / "uploads"
EXTENSOES_IMAGEM = {".jpg", ".jpeg", ".png", ".webp", ".gif"}
TAMANHO_MAXIMO_IMAGEM = 5 * 1024 * 1024


def montar_ponto_response(ponto: PontoTuristico, salvo: bool = False) -> PontoResponse:
    notas = [avaliacao.nota for avaliacao in ponto.avaliacoes]
    media = round(sum(notas) / len(notas), 2) if notas else 0
    imagens_urls = list(getattr(ponto, "imagens_urls", []) or [])
    imagem_url = getattr(ponto, "imagem_url", None)
    if not imagens_urls and imagem_url:
        imagens_urls = [imagem_url]
    return PontoResponse.model_validate(
        {
            "id": ponto.id,
            "nome": ponto.nome,
            "descricao": ponto.descricao,
            "categoria": ponto.categoria,
            "cidade": ponto.cidade,
            "bairro": ponto.bairro,
            "endereco": ponto.endereco,
            "latitude": ponto.latitude,
            "longitude": ponto.longitude,
            "imagem_url": imagem_url,
            "imagens_urls": imagens_urls,
            "status": ponto.status,
            "criado_em": ponto.criado_em,
            "criado_por_id": ponto.criado_por_id,
            "media_avaliacoes": media,
            "total_avaliacoes": len(notas),
            "salvo": salvo,
            "avaliacoes": [  # ← adicionado
                {
                    "id": a.id,
                    "usuario_id": a.usuario_id,
                    "usuario_nome": getattr(getattr(a, "usuario", None), "nome", None)
                    or getattr(a, "usuario_nome", None)
                    or f"Usuario {a.usuario_id}",
                    "ponto_id": a.ponto_id,
                    "nota": a.nota,
                    "comentario": a.comentario,
                    "criado_em": a.criado_em,
                }
                for a in ponto.avaliacoes
            ],
        }
    )


def buscar_ponto_ou_404(db: Session, ponto_id: int) -> PontoTuristico:
    if using_mongodb():
        ponto = db.ponto_by_id(ponto_id)
        if ponto is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Ponto turistico nao encontrado.")
        return ponto

    ponto = (
        db.query(PontoTuristico)
        .options(selectinload(PontoTuristico.avaliacoes).selectinload(Avaliacao.usuario))
        .filter(PontoTuristico.id == ponto_id)
        .first()
    )
    if ponto is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Ponto turistico nao encontrado.")
    return ponto


def obter_usuario_opcional(
    credenciais: HTTPAuthorizationCredentials | None,
    db: Session,
) -> Usuario | None:
    if credenciais is None:
        return None
    try:
        payload = jwt.decode(credenciais.credentials, SECRET_KEY, algorithms=[ALGORITHM])
        usuario_id = int(payload.get("sub"))
    except (jwt.PyJWTError, TypeError, ValueError):
        return None
    return db.usuario_by_id(usuario_id) if using_mongodb() else db.get(Usuario, usuario_id)


@router.get("", response_model=list[PontoResponse])
def listar_pontos(
    busca: str | None = Query(default=None, description="Busca por nome, categoria, cidade ou bairro"),
    cidade: str | None = None,
    categoria: str | None = None,
    ordenar: str = Query(default="nome", pattern="^(nome|avaliacao_desc|avaliacao_asc|nota_desc|nota_asc)$"),
    incluir_pendentes: bool = False,
    db: Session = Depends(get_db),
    credenciais: HTTPAuthorizationCredentials | None = Depends(optional_bearer_scheme),
) -> list[PontoResponse]:
    if using_mongodb():
        usuario = obter_usuario_opcional(credenciais, db)
        if incluir_pendentes and (usuario is None or usuario.tipo != TipoUsuario.ADMIN):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Apenas administradores podem listar pontos pendentes.",
            )
        pontos = db.listar_pontos(busca=busca, cidade=cidade, categoria=categoria, incluir_pendentes=incluir_pendentes)
        salvos_ids = db.salvos_ids_usuario(usuario.id) if usuario is not None else set()
        respostas = [montar_ponto_response(ponto, ponto.id in salvos_ids) for ponto in pontos]
        if ordenar in ("avaliacao_desc", "nota_desc"):
            respostas.sort(key=lambda ponto: (ponto.media_avaliacoes, ponto.total_avaliacoes), reverse=True)
        elif ordenar in ("avaliacao_asc", "nota_asc"):
            respostas.sort(key=lambda ponto: (ponto.media_avaliacoes, ponto.total_avaliacoes))
        return respostas

    consulta = db.query(PontoTuristico).options(
        selectinload(PontoTuristico.avaliacoes).selectinload(Avaliacao.usuario)
    )

    usuario = obter_usuario_opcional(credenciais, db)
    if incluir_pendentes and (usuario is None or usuario.tipo != TipoUsuario.ADMIN):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Apenas administradores podem listar pontos pendentes.",
        )

    if not incluir_pendentes:
        consulta = consulta.filter(PontoTuristico.status == StatusPonto.APROVADO)
    if cidade:
        consulta = consulta.filter(PontoTuristico.cidade.ilike(f"%{cidade}%"))
    if categoria:
        consulta = consulta.filter(PontoTuristico.categoria.ilike(f"%{categoria}%"))
    if busca:
        termo = f"%{busca}%"
        consulta = consulta.filter(
            or_(
                PontoTuristico.nome.ilike(termo),
                PontoTuristico.categoria.ilike(termo),
                PontoTuristico.cidade.ilike(termo),
                PontoTuristico.bairro.ilike(termo),
            )
        )

    pontos = consulta.order_by(PontoTuristico.nome.asc()).all()
    salvos_ids: set[int] = set()
    if usuario is not None:
        salvos_ids = {
            ponto_id
            for (ponto_id,) in db.query(PontoSalvo.ponto_id)
            .filter(PontoSalvo.usuario_id == usuario.id)
            .all()
        }

    respostas = [montar_ponto_response(ponto, ponto.id in salvos_ids) for ponto in pontos]
    if ordenar in ("avaliacao_desc", "nota_desc"):
        respostas.sort(key=lambda ponto: (ponto.media_avaliacoes, ponto.total_avaliacoes), reverse=True)
    elif ordenar in ("avaliacao_asc", "nota_asc"):
        respostas.sort(key=lambda ponto: (ponto.media_avaliacoes, ponto.total_avaliacoes))
    return respostas


@router.get("/salvos/me", response_model=list[PontoResponse])
def listar_pontos_salvos(
    db: Session = Depends(get_db),
    usuario: Usuario = Depends(obter_usuario_atual),
) -> list[PontoResponse]:
    if using_mongodb():
        return [montar_ponto_response(ponto, salvo=True) for ponto in db.listar_pontos_salvos(usuario.id)]

    salvos = (
        db.query(PontoSalvo)
        .join(PontoSalvo.ponto)
        .options(
            selectinload(PontoSalvo.ponto)
            .selectinload(PontoTuristico.avaliacoes)
            .selectinload(Avaliacao.usuario)
        )
        .filter(PontoSalvo.usuario_id == usuario.id, PontoTuristico.status == StatusPonto.APROVADO)
        .order_by(PontoSalvo.criado_em.desc())
        .all()
    )
    return [montar_ponto_response(salvo.ponto, salvo=True) for salvo in salvos]


@router.get("/{ponto_id}", response_model=PontoResponse)
def obter_ponto(
    ponto_id: int,
    db: Session = Depends(get_db),
    credenciais: HTTPAuthorizationCredentials | None = Depends(optional_bearer_scheme),
) -> PontoResponse:
    ponto = buscar_ponto_ou_404(db, ponto_id)
    usuario = obter_usuario_opcional(credenciais, db)
    pode_ver_pendente = (
        usuario is not None
        and (usuario.tipo == TipoUsuario.ADMIN or ponto.criado_por_id == usuario.id)
    )
    if ponto.status != StatusPonto.APROVADO and not pode_ver_pendente:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Ponto turistico nao encontrado.")
    esta_salvo = False
    if usuario is not None:
        if using_mongodb():
            esta_salvo = ponto.id in db.salvos_ids_usuario(usuario.id)
        else:
            esta_salvo = (
                db.query(PontoSalvo)
                .filter(PontoSalvo.usuario_id == usuario.id, PontoSalvo.ponto_id == ponto.id)
                .first()
                is not None
            )
    return montar_ponto_response(ponto, esta_salvo)


@router.post("", response_model=PontoResponse, status_code=status.HTTP_201_CREATED)
def cadastrar_ponto(
    dados: PontoCadastroInput,
    db: Session = Depends(get_db),
    usuario: Usuario = Depends(obter_usuario_atual),
) -> PontoResponse:
    dados_ponto = dados.model_dump()
    if not dados_ponto.get("imagem_url") and dados_ponto.get("imagens_urls"):
        dados_ponto["imagem_url"] = dados_ponto["imagens_urls"][0]

    if using_mongodb():
        ponto = db.criar_ponto(
            dados=dados_ponto,
            criado_por_id=usuario.id,
            status=StatusPonto.APROVADO if usuario.tipo == TipoUsuario.ADMIN else StatusPonto.PENDENTE,
        )
        return montar_ponto_response(ponto)

    dados_sql = {campo: valor for campo, valor in dados_ponto.items() if campo != "imagens_urls"}
    ponto = PontoTuristico(
        **dados_sql,
        criado_por_id=usuario.id,
        status=StatusPonto.APROVADO if usuario.tipo == TipoUsuario.ADMIN else StatusPonto.PENDENTE,
    )
    db.add(ponto)
    db.commit()
    db.refresh(ponto)
    return montar_ponto_response(ponto)


@router.post("/{ponto_id}/salvar", response_model=PontoResponse)
def salvar_ponto(
    ponto_id: int,
    db: Session = Depends(get_db),
    usuario: Usuario = Depends(obter_usuario_atual),
) -> PontoResponse:
    ponto = buscar_ponto_ou_404(db, ponto_id)
    if ponto.status != StatusPonto.APROVADO:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Apenas pontos aprovados podem ser salvos.",
        )

    ponto_salvo = (
        None
        if using_mongodb()
        else
        db.query(PontoSalvo)
        .filter(PontoSalvo.usuario_id == usuario.id, PontoSalvo.ponto_id == ponto.id)
        .first()
    )

    if using_mongodb():
        db.salvar_ponto(usuario.id, ponto.id)
        return montar_ponto_response(ponto, salvo=True)

    if ponto_salvo is None:
        db.add(PontoSalvo(usuario_id=usuario.id, ponto_id=ponto.id))
        db.commit()
        db.refresh(ponto)

    return montar_ponto_response(ponto, salvo=True)


@router.post("/imagens", status_code=status.HTTP_201_CREATED)
async def enviar_imagens_ponto(
    request: Request,
    _: Usuario = Depends(obter_usuario_atual),
):
    form = await request.form()
    imagens = [arquivo for arquivo in form.getlist("imagens") if isinstance(arquivo, UploadFile)]
    if not imagens:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Envie pelo menos uma imagem.",
        )
    if len(imagens) > 8:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Envie no maximo 8 imagens por ponto.",
        )

    UPLOAD_DIR.mkdir(exist_ok=True)
    urls: list[str] = []
    for imagem in imagens:
        extensao = Path(imagem.filename or "").suffix.lower()
        if extensao not in EXTENSOES_IMAGEM or not (imagem.content_type or "").startswith("image/"):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Envie apenas imagens JPG, PNG, WEBP ou GIF.",
            )

        conteudo = await imagem.read()
        if len(conteudo) > TAMANHO_MAXIMO_IMAGEM:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Cada imagem deve ter no maximo 5 MB.",
            )

        nome_arquivo = f"{uuid4().hex}{extensao}"
        caminho = UPLOAD_DIR / nome_arquivo
        caminho.write_bytes(conteudo)
        urls.append(f"/uploads/{nome_arquivo}")

    return {"imagens_urls": urls}


@router.delete("/{ponto_id}/salvar", status_code=status.HTTP_204_NO_CONTENT)
def remover_ponto_salvo(
    ponto_id: int,
    db: Session = Depends(get_db),
    usuario: Usuario = Depends(obter_usuario_atual),
):
    if using_mongodb():
        db.remover_ponto_salvo(usuario.id, ponto_id)
        return None

    ponto_salvo = (
        db.query(PontoSalvo)
        .filter(PontoSalvo.usuario_id == usuario.id, PontoSalvo.ponto_id == ponto_id)
        .first()
    )
    if ponto_salvo is not None:
        db.delete(ponto_salvo)
        db.commit()


@router.patch("/{ponto_id}", response_model=PontoResponse)
def atualizar_ponto(
    ponto_id: int,
    dados: PontoAtualizacaoInput,
    db: Session = Depends(get_db),
    usuario: Usuario = Depends(obter_usuario_atual),
) -> PontoResponse:
    ponto = buscar_ponto_ou_404(db, ponto_id)
    atualizacoes = dados.model_dump(exclude_unset=True)
    if not atualizacoes.get("imagem_url") and atualizacoes.get("imagens_urls"):
        atualizacoes["imagem_url"] = atualizacoes["imagens_urls"][0]
    if "status" in atualizacoes and usuario.tipo != TipoUsuario.ADMIN:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Apenas administradores alteram status.")

    if using_mongodb():
        if usuario.tipo != TipoUsuario.ADMIN:
            if ponto.status != StatusPonto.APROVADO and ponto.criado_por_id != usuario.id:
                raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Voce nao pode editar este ponto.")
            return montar_ponto_response(db.solicitar_edicao_ponto(ponto_id, atualizacoes, usuario.id))
        return montar_ponto_response(db.atualizar_ponto(ponto_id, atualizacoes))

    if usuario.tipo != TipoUsuario.ADMIN and ponto.criado_por_id != usuario.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Voce nao pode editar este ponto.")

    atualizacoes.pop("imagens_urls", None)
    for campo, valor in atualizacoes.items():
        setattr(ponto, campo, valor)

    db.commit()
    db.refresh(ponto)
    return montar_ponto_response(ponto)


@router.patch("/{ponto_id}/aprovar", response_model=PontoResponse)
def aprovar_ponto(
    ponto_id: int,
    db: Session = Depends(get_db),
    _: Usuario = Depends(exigir_admin),
) -> PontoResponse:
    ponto = buscar_ponto_ou_404(db, ponto_id)
    if using_mongodb():
        return montar_ponto_response(db.atualizar_ponto(ponto_id, {"status": StatusPonto.APROVADO}))

    ponto.status = StatusPonto.APROVADO
    db.commit()
    db.refresh(ponto)
    return montar_ponto_response(ponto)


@router.post("/{ponto_id}/avaliacoes", response_model=AvaliacaoResponse, status_code=status.HTTP_201_CREATED)
def avaliar_ponto(
    ponto_id: int,
    dados: AvaliacaoInput,
    db: Session = Depends(get_db),
    usuario: Usuario = Depends(obter_usuario_atual),
) -> Avaliacao:
    ponto = buscar_ponto_ou_404(db, ponto_id)
    if ponto.status != StatusPonto.APROVADO:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Este ponto ainda nao pode ser avaliado.")

    if using_mongodb():
        return db.salvar_avaliacao(usuario.id, ponto.id, dados.nota, dados.comentario)

    avaliacao = (
        db.query(Avaliacao)
        .filter(Avaliacao.usuario_id == usuario.id, Avaliacao.ponto_id == ponto.id)
        .first()
    )
    if avaliacao is None:
        avaliacao = Avaliacao(usuario_id=usuario.id, ponto_id=ponto.id, nota=dados.nota, comentario=dados.comentario)
        db.add(avaliacao)
    else:
        avaliacao.nota = dados.nota
        avaliacao.comentario = dados.comentario

    db.commit()
    db.refresh(avaliacao)
    return avaliacao

@router.patch("/{ponto_id}/rejeitar", response_model=PontoResponse)
def rejeitar_ponto(
    ponto_id: int,
    db: Session = Depends(get_db),
    _: Usuario = Depends(exigir_admin),
) -> PontoResponse:
    ponto = buscar_ponto_ou_404(db, ponto_id)
    if using_mongodb():
        return montar_ponto_response(db.atualizar_ponto(ponto_id, {"status": StatusPonto.REJEITADO}))

    ponto.status = StatusPonto.REJEITADO
    db.commit()
    db.refresh(ponto)
    return montar_ponto_response(ponto)

@router.delete("/{ponto_id}/avaliacoes/{avaliacao_id}", status_code=status.HTTP_204_NO_CONTENT)
def apagar_avaliacao(
    ponto_id: int,
    avaliacao_id: int,
    db: Session = Depends(get_db),
    usuario: Usuario = Depends(obter_usuario_atual),
):
    if using_mongodb():
        usuario_id = None if usuario.tipo == TipoUsuario.ADMIN else usuario.id
        if not db.apagar_avaliacao(ponto_id, avaliacao_id, usuario_id):
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND if usuario.tipo == TipoUsuario.ADMIN else status.HTTP_403_FORBIDDEN,
                detail="Avaliacao nao encontrada." if usuario.tipo == TipoUsuario.ADMIN else "Voce nao pode apagar esta avaliacao.",
            )
        return None

    avaliacao = (
        db.query(Avaliacao)
        .filter(Avaliacao.id == avaliacao_id, Avaliacao.ponto_id == ponto_id)
        .first()
    )
    if avaliacao is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Avaliacao nao encontrada.",
        )
    if usuario.tipo != TipoUsuario.ADMIN and avaliacao.usuario_id != usuario.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Voce nao pode apagar esta avaliacao.",
        )
    db.delete(avaliacao)
    db.commit()
