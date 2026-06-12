import os
from collections.abc import Generator

from sqlalchemy import create_engine
from sqlalchemy.orm import DeclarativeBase, Session, sessionmaker


DB_BACKEND = os.getenv("DB_BACKEND", "mongodb").lower()
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./tourcheck.db")
MONGODB_URL = os.getenv("MONGODB_URL", "mongodb://localhost:27017")
MONGODB_DATABASE = os.getenv("MONGODB_DATABASE", "tourcheck")

connect_args = {"check_same_thread": False} if DATABASE_URL.startswith("sqlite") else {}

engine = create_engine(DATABASE_URL, connect_args=connect_args)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


class Base(DeclarativeBase):
    pass


def using_mongodb() -> bool:
    return DB_BACKEND in {"mongo", "mongodb"}


def using_sqlalchemy() -> bool:
    return not using_mongodb()


def get_db() -> Generator[Session, None, None]:
    if using_mongodb():
        from app.mongo_database import mongo_db

        yield mongo_db
        return

    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def init_db() -> None:
    if using_mongodb():
        from app.mongo_database import mongo_db

        mongo_db.init_indexes()
        return

    import app.models.avaliacao  # noqa: F401
    import app.models.ponto  # noqa: F401
    import app.models.ponto_salvo  # noqa: F401
    import app.models.usuario  # noqa: F401

    Base.metadata.create_all(bind=engine)
