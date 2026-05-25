from fastapi import APIRouter, Depends, HTTPException, Query, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
import jwt
from sqlalchemy import or_
from sqlalchemy.orm import Session, selectinload

from app.database import get_db
from app.models.avaliacao import Avaliacao
from app.models.ponto import PontoTuristico, StatusPonto
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


def montar_ponto_response(ponto: PontoTuristico) -> PontoResponse:
    notas = [avaliacao.nota for avaliacao in ponto.avaliacoes]
    media = round(sum(notas) / len(notas), 2) if notas else 0
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
            "imagem_url": ponto.imagem_url,
            "status": ponto.status,
            "criado_em": ponto.criado_em,
            "criado_por_id": ponto.criado_por_id,
            "media_avaliacoes": media,
            "total_avaliacoes": len(notas),
        }
    )


def buscar_ponto_ou_404(db: Session, ponto_id: int) -> PontoTuristico:
    ponto = (
        db.query(PontoTuristico)
        .options(selectinload(PontoTuristico.avaliacoes))
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
    return db.get(Usuario, usuario_id)


@router.get("", response_model=list[PontoResponse])
def listar_pontos(
    busca: str | None = Query(default=None, description="Busca por nome, categoria, cidade ou bairro"),
    cidade: str | None = None,
    categoria: str | None = None,
    incluir_pendentes: bool = False,
    db: Session = Depends(get_db),
    credenciais: HTTPAuthorizationCredentials | None = Depends(optional_bearer_scheme),
) -> list[PontoResponse]:
    consulta = db.query(PontoTuristico).options(selectinload(PontoTuristico.avaliacoes))

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
    return [montar_ponto_response(ponto) for ponto in pontos]


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
    return montar_ponto_response(ponto)


@router.post("", response_model=PontoResponse, status_code=status.HTTP_201_CREATED)
def cadastrar_ponto(
    dados: PontoCadastroInput,
    db: Session = Depends(get_db),
    usuario: Usuario = Depends(obter_usuario_atual),
) -> PontoResponse:
    ponto = PontoTuristico(
        **dados.model_dump(),
        criado_por_id=usuario.id,
        status=StatusPonto.APROVADO if usuario.tipo == TipoUsuario.ADMIN else StatusPonto.PENDENTE,
    )
    db.add(ponto)
    db.commit()
    db.refresh(ponto)
    return montar_ponto_response(ponto)


@router.patch("/{ponto_id}", response_model=PontoResponse)
def atualizar_ponto(
    ponto_id: int,
    dados: PontoAtualizacaoInput,
    db: Session = Depends(get_db),
    usuario: Usuario = Depends(obter_usuario_atual),
) -> PontoResponse:
    ponto = buscar_ponto_ou_404(db, ponto_id)
    if usuario.tipo != TipoUsuario.ADMIN and ponto.criado_por_id != usuario.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Voce nao pode editar este ponto.")

    atualizacoes = dados.model_dump(exclude_unset=True)
    if "status" in atualizacoes and usuario.tipo != TipoUsuario.ADMIN:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Apenas administradores alteram status.")

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
    ponto.status = StatusPonto.REJEITADO
    db.commit()
    db.refresh(ponto)
    return montar_ponto_response(ponto)

@router.delete("/{ponto_id}/avaliacoes/{avaliacao_id}", status_code=status.HTTP_204_NO_CONTENT)
def apagar_avaliacao(
    ponto_id: int,
    avaliacao_id: int,
    db: Session = Depends(get_db),
    _: Usuario = Depends(exigir_admin),
):
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
    db.delete(avaliacao)
    db.commit()
