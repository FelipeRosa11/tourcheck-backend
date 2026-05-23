from pydantic import BaseModel, ConfigDict, EmailStr, Field

from app.models.usuario import TipoTelefone, TipoUsuario


class TelefoneInput(BaseModel):
    tipo: TipoTelefone
    numero: str = Field(..., min_length=8, max_length=20)


class TelefoneResponse(TelefoneInput):
    model_config = ConfigDict(from_attributes=True)

    id: int


class UsuarioCadastroInput(BaseModel):
    nome: str = Field(..., min_length=3, max_length=100)
    email: EmailStr
    senha: str = Field(..., min_length=6, max_length=128)
    telefones: list[TelefoneInput] = Field(default_factory=list)


class UsuarioLoginInput(BaseModel):
    email: EmailStr
    senha: str = Field(..., min_length=1)


class UsuarioResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    nome: str
    email: EmailStr
    tipo: TipoUsuario
    telefones: list[TelefoneResponse] = Field(default_factory=list)


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    usuario: UsuarioResponse
