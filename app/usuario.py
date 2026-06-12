from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session, selectinload

from app.database import get_db
from app.models.usuario import TipoUsuario, Usuario
from app.schemas.usuario import CadastroInput, CadastroOutput, LoginInput, LoginOutput
from app.security import criar_token_acesso, exigir_admin, gerar_hash_senha, obter_usuario_atual, verificar_senha

router = APIRouter(prefix="/usuarios", tags=["Usuários"])


@router.post("/login", response_model=LoginOutput)
def login(dados: LoginInput, db: Session = Depends(get_db)):
    # ← bug corrigido: busca o usuário antes de verificar
    usuario = (
        db.query(Usuario)
        .options(selectinload(Usuario.telefones))
        .filter(Usuario.email == str(dados.email).lower())
        .first()
    )

    if not usuario or not verificar_senha(dados.senha, usuario.senha_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="E-mail ou senha incorretos.",
        )

    return LoginOutput(
        access_token=criar_token_acesso(usuario),
        token_type="bearer",
        tipo_usuario=usuario.tipo.value,
    )


@router.post("/cadastro", response_model=CadastroOutput, status_code=status.HTTP_201_CREATED)
def cadastrar(dados: CadastroInput, db: Session = Depends(get_db)):
    if db.query(Usuario).filter(Usuario.email == str(dados.email).lower()).first():
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="E-mail já cadastrado.",
        )

    novo_usuario = Usuario(
        nome=dados.nome,
        email=str(dados.email).lower(),
        senha_hash=gerar_hash_senha(dados.senha),
        tipo=TipoUsuario.COMUM,
    )

    db.add(novo_usuario)
    db.commit()
    db.refresh(novo_usuario)

    return CadastroOutput(
        usuario_id=novo_usuario.id,
        nome=novo_usuario.nome,
        email=novo_usuario.email,
    )


@router.get("/me")
def meu_perfil(usuario: Usuario = Depends(obter_usuario_atual)):
    return {
        "id": usuario.id,
        "nome": usuario.nome,
        "email": usuario.email,
        "tipo": usuario.tipo.value,
    }


@router.get("/")
def listar_usuarios(admin: Usuario = Depends(exigir_admin), db: Session = Depends(get_db)):
    return [
        {"id": u.id, "nome": u.nome, "email": u.email, "tipo": u.tipo.value}
        for u in db.query(Usuario).all()
    ]