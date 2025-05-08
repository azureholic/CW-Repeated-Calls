from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from . import settings

db_settings = settings.DatabaseSettings()

engine = create_engine(
    "postgresql+psycopg://{user}:{password}@{host}:{port}/{database}".format(
        user=db_settings.user,
        password=db_settings.password.get_secret_value(),
        host=db_settings.host,
        port=db_settings.port,
        database=db_settings.database,
    )
)
"""SQLAlchemy engine."""

session = sessionmaker(bind=engine, autocommit=False)
"""SQLAlchemy session."""
