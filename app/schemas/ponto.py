from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field

from app.models.ponto import StatusPonto


class PontoBase(BaseModel):
    nome: str = Field(..., min_length=3, max_length=120)
    descricao: str = Field(..., min_length=10)
    categoria: str = Field(..., min_length=2, max_length=60)
    cidade: str = Field(..., min_length=2, max_length=80)
    bairro: str | None = Field(default=None, max_length=80)
    endereco: str | None = Field(default=None, max_length=255)
    latitude: float | None = Field(default=None, ge=-90, le=90)
    longitude: float | None = Field(default=None, ge=-180, le=180)
    imagem_url: str | None = Field(default=None, max_length=500)


class PontoCadastroInput(PontoBase):
    pass


class PontoAtualizacaoInput(BaseModel):
    nome: str | None = Field(default=None, min_length=3, max_length=120)
    descricao: str | None = Field(default=None, min_length=10)
    categoria: str | None = Field(default=None, min_length=2, max_length=60)
    cidade: str | None = Field(default=None, min_length=2, max_length=80)
    bairro: str | None = Field(default=None, max_length=80)
    endereco: str | None = Field(default=None, max_length=255)
    latitude: float | None = Field(default=None, ge=-90, le=90)
    longitude: float | None = Field(default=None, ge=-180, le=180)
    imagem_url: str | None = Field(default=None, max_length=500)
    status: StatusPonto | None = None


class AvaliacaoInput(BaseModel):
    nota: int = Field(..., ge=1, le=5)
    comentario: str | None = Field(default=None, max_length=1000)


class AvaliacaoResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    usuario_id: int
    ponto_id: int
    nota: int
    comentario: str | None
    criado_em: datetime


class PontoResponse(PontoBase):
    model_config = ConfigDict(from_attributes=True)

    id: int
    status: StatusPonto
    criado_em: datetime
    criado_por_id: int | None
    media_avaliacoes: float = 0
    total_avaliacoes: int = 0
