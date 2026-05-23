from datetime import datetime
from enum import Enum

from sqlalchemy import DateTime, Enum as SQLEnum
from sqlalchemy import Float, ForeignKey, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


class StatusPonto(str, Enum):
    PENDENTE = "pendente"
    APROVADO = "aprovado"
    REJEITADO = "rejeitado"


class PontoTuristico(Base):
    __tablename__ = "pontos_turisticos"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    nome: Mapped[str] = mapped_column(String(120), index=True, nullable=False)
    descricao: Mapped[str] = mapped_column(Text, nullable=False)
    categoria: Mapped[str] = mapped_column(String(60), index=True, nullable=False)
    cidade: Mapped[str] = mapped_column(String(80), index=True, nullable=False)
    bairro: Mapped[str | None] = mapped_column(String(80), nullable=True)
    endereco: Mapped[str | None] = mapped_column(String(255), nullable=True)
    latitude: Mapped[float | None] = mapped_column(Float, nullable=True)
    longitude: Mapped[float | None] = mapped_column(Float, nullable=True)
    imagem_url: Mapped[str | None] = mapped_column(String(500), nullable=True)
    status: Mapped[StatusPonto] = mapped_column(
        SQLEnum(StatusPonto), default=StatusPonto.APROVADO, nullable=False
    )
    criado_em: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)
    criado_por_id: Mapped[int | None] = mapped_column(ForeignKey("usuarios.id"), nullable=True)

    criado_por = relationship("Usuario")
    avaliacoes = relationship(
        "Avaliacao", back_populates="ponto", cascade="all, delete-orphan"
    )
