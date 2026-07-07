import os
import sys
from pathlib import Path
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, DeclarativeBase
from dotenv import load_dotenv

def _find_env():
    """Busca el archivo .env junto al ejecutable o en el directorio del proyecto."""
    if getattr(sys, 'frozen', False):
        # Ejecutable empaquetado (.exe)
        base = Path(sys.executable).parent
    else:
        # Modo de desarrollo normal
        base = Path(__file__).resolve().parent.parent.parent
    env_path = base / ".env"
    return str(env_path) if env_path.exists() else None

load_dotenv(_find_env())


class Base(DeclarativeBase):
    pass


class DatabaseConnection:
    """Singleton que gestiona la conexión a MySQL via SQLAlchemy."""

    _instance: "DatabaseConnection | None" = None

    def __new__(cls) -> "DatabaseConnection":
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialize()
        return cls._instance

    def _initialize(self) -> None:
        host     = os.getenv("DB_HOST", "localhost")
        port     = os.getenv("DB_PORT", "3306")
        user     = os.getenv("DB_USER", "root")
        password = os.getenv("DB_PASSWORD", "")
        name     = os.getenv("DB_NAME", "sistema_horarios")

        url = f"mysql+pymysql://{user}:{password}@{host}:{port}/{name}"
        self._engine  = create_engine(url, echo=False, pool_pre_ping=True)
        self._Session = sessionmaker(bind=self._engine)

    @property
    def engine(self):
        return self._engine

    def get_session(self):
        return self._Session()