import os
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, DeclarativeBase
from dotenv import load_dotenv

load_dotenv()


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