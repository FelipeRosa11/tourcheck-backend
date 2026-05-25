from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session, selectinload

from app.database import get_db
from app.models.ponto import PontoTuristico, StatusPonto
from app.models.usuario import TipoUsuario, Usuario
from app.routers.pontos import montar_ponto_response
from app.schemas.ponto import PontoResponse
from app.schemas.usuario import PrimeiroAdminInput, UsuarioTipoInput
from app.security import exigir_admin


router = APIRouter(prefix="/admin/api", tags=["Administracao"])


def usuario_para_dict(usuario: Usuario) -> dict:
    return {
        "id": usuario.id,
        "nome": usuario.nome,
        "email": usuario.email,
        "tipo": usuario.tipo.value,
    }


@router.post("/primeiro-admin")
def criar_primeiro_admin(dados: PrimeiroAdminInput, db: Session = Depends(get_db)):
    admin_existente = db.query(Usuario).filter(Usuario.tipo == TipoUsuario.ADMIN).first()
    if admin_existente is not None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Ja existe um administrador cadastrado.",
        )

    usuario = db.query(Usuario).filter(Usuario.email == str(dados.email).lower()).first()
    if usuario is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Usuario nao encontrado.",
        )

    usuario.tipo = TipoUsuario.ADMIN
    db.commit()
    db.refresh(usuario)
    return usuario_para_dict(usuario)


@router.get("/pontos", response_model=list[PontoResponse])
def listar_pontos_admin(
    status_ponto: StatusPonto | None = None,
    db: Session = Depends(get_db),
    _: Usuario = Depends(exigir_admin),
) -> list[PontoResponse]:
    consulta = db.query(PontoTuristico).options(selectinload(PontoTuristico.avaliacoes))
    if status_ponto is not None:
        consulta = consulta.filter(PontoTuristico.status == status_ponto)

    pontos = consulta.order_by(PontoTuristico.criado_em.desc()).all()
    return [montar_ponto_response(ponto) for ponto in pontos]


@router.get("/usuarios")
def listar_usuarios_admin(
    db: Session = Depends(get_db),
    _: Usuario = Depends(exigir_admin),
):
    usuarios = db.query(Usuario).order_by(Usuario.nome.asc()).all()
    return [usuario_para_dict(usuario) for usuario in usuarios]


@router.patch("/usuarios/{usuario_id}/tipo")
def alterar_tipo_usuario(
    usuario_id: int,
    dados: UsuarioTipoInput,
    db: Session = Depends(get_db),
    admin: Usuario = Depends(exigir_admin),
):
    usuario = db.get(Usuario, usuario_id)
    if usuario is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Usuario nao encontrado.",
        )

    if usuario.id == admin.id and dados.tipo != TipoUsuario.ADMIN:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Voce nao pode remover o proprio acesso de administrador.",
        )

    usuario.tipo = dados.tipo
    db.commit()
    db.refresh(usuario)

    return usuario_para_dict(usuario)
