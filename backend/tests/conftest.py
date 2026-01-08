import os

TEST_DB_PATH = os.path.join(os.path.dirname(__file__), 'test.db')
os.environ.setdefault("DATABASE_URL", f"sqlite:///{TEST_DB_PATH}")

if os.path.exists(TEST_DB_PATH):
    os.remove(TEST_DB_PATH)

from app import models
from app.database import engine, SessionLocal
import pytest

models.Base.metadata.create_all(bind=engine)


@pytest.fixture
def db_session():
    session = SessionLocal()
    try:
        yield session
    finally:
        session.rollback()
        session.close()
