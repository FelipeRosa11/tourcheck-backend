from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, Integer, String, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


class Avaliacao(Base):
    __tablename__ = "avaliacoes"
    __table_args__ = (
        UniqueConstraint("usuario_id", "ponto_id", name="uq_avaliacao_usuario_ponto"),
    )

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    usuario_id: Mapped[int] = mapped_column(ForeignKey("usuarios.id"), nullable=False)
    ponto_id: Mapped[int] = mapped_column(ForeignKey("pontos_turisticos.id"), nullable=False)
    nota: Mapped[int] = mapped_column(Integer, nullable=False)
    comentario: Mapped[str | None] = mapped_column(Text, nullable=True)
    criado_em: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)

    usuario = relationship("Usuario")
    ponto = relationship("PontoTuristico", back_populates="avaliacoes")
