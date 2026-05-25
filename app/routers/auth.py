from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session, selectinload

from app.database import get_db
from app.models.usuario import TelefoneUsuario, TipoUsuario, Usuario
from app.schemas.usuario import (
    TokenResponse,
    UsuarioCadastroInput,
    UsuarioLoginInput,
    UsuarioResponse,
)
from app.security import criar_token_acesso, gerar_hash_senha, obter_usuario_atual, verificar_senha

router = APIRouter(prefix="/auth", tags=["Autenticacao"])


@router.post("/cadastro", response_model=UsuarioResponse, status_code=status.HTTP_201_CREATED)
def cadastrar_usuario(dados: UsuarioCadastroInput, db: Session = Depends(get_db)) -> Usuario:
    email = str(dados.email).lower()
    usuario_existente = db.query(Usuario).filter(Usuario.email == email).first()
    if usuario_existente:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Este e-mail ja esta cadastrado no sistema.",
        )

    usuario = Usuario(
        nome=dados.nome,
        email=email,
        senha_hash=gerar_hash_senha(dados.senha),
        tipo=TipoUsuario.ADMIN
        if db.query(Usuario).filter(Usuario.tipo == TipoUsuario.ADMIN).first() is None
        else TipoUsuario.COMUM,
    )
    usuario.telefones = [
        TelefoneUsuario(tipo=telefone.tipo, numero=telefone.numero)
        for telefone in dados.telefones
    ]

    db.add(usuario)
    db.commit()
    db.refresh(usuario)
    return usuario


@router.post("/login", response_model=TokenResponse)
def login(dados: UsuarioLoginInput, db: Session = Depends(get_db)) -> TokenResponse:
    usuario = (
        db.query(Usuario)
        .options(selectinload(Usuario.telefones))
        .filter(Usuario.email == str(dados.email).lower())
        .first()
    )
    if usuario is None or not verificar_senha(dados.senha, usuario.senha_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="E-mail ou senha invalidos.",
        )

    return TokenResponse(access_token=criar_token_acesso(usuario), usuario=usuario)


@router.get("/me", response_model=UsuarioResponse)
def obter_perfil(usuario: Usuario = Depends(obter_usuario_atual)) -> Usuario:
    return usuario
