from enum import Enum

from sqlalchemy import Enum as SQLEnum
from sqlalchemy import ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


class TipoUsuario(str, Enum):
    ADMIN = "admin"
    COMUM = "comum"


class TipoTelefone(str, Enum):
    CELULAR = "celular"
    RESIDENCIAL = "residencial"
    COMERCIAL = "comercial"


class Usuario(Base):
    __tablename__ = "usuarios"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    nome: Mapped[str] = mapped_column(String(100), nullable=False)
    email: Mapped[str] = mapped_column(String(255), unique=True, index=True, nullable=False)
    senha_hash: Mapped[str] = mapped_column(String(255), nullable=False)
    tipo: Mapped[TipoUsuario] = mapped_column(
        SQLEnum(TipoUsuario), default=TipoUsuario.COMUM, nullable=False
    )

    telefones: Mapped[list["TelefoneUsuario"]] = relationship(
        back_populates="usuario", cascade="all, delete-orphan"
    )
    pontos_salvos = relationship(
        "PontoSalvo", back_populates="usuario", cascade="all, delete-orphan"
    )


class TelefoneUsuario(Base):
    __tablename__ = "usuarios_telefones"

    id: Mapped[int] = mapped_column(primary_key=True)
    usuario_id: Mapped[int] = mapped_column(ForeignKey("usuarios.id"), nullable=False)
    tipo: Mapped[TipoTelefone] = mapped_column(SQLEnum(TipoTelefone), nullable=False)
    numero: Mapped[str] = mapped_column(String(20), nullable=False)

    usuario: Mapped[Usuario] = relationship(back_populates="telefones")
