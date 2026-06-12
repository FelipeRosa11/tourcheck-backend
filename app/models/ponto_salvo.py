from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


class PontoSalvo(Base):
    __tablename__ = "pontos_salvos"
    __table_args__ = (
        UniqueConstraint("usuario_id", "ponto_id", name="uq_ponto_salvo_usuario_ponto"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    usuario_id: Mapped[int] = mapped_column(ForeignKey("usuarios.id"), nullable=False)
    ponto_id: Mapped[int] = mapped_column(ForeignKey("pontos_turisticos.id"), nullable=False)
    criado_em: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)

    usuario = relationship("Usuario", back_populates="pontos_salvos")
    ponto = relationship("PontoTuristico", back_populates="salvos")
