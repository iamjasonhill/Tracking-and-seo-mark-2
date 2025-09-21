import os
import sys
from pathlib import Path
from typing import Generator

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import sessionmaker

os.environ["DATABASE_URL"] = "sqlite:///./test.db"

ROOT_DIR = Path(__file__).resolve().parents[1]
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from app.api.deps import get_db
from app.core.config import settings
from app.db.base_class import Base
from app.db.session import engine
from app.main import app as fastapi_app

import app.models.account  # noqa: F401
import app.models.search_data  # noqa: F401
import app.models.site  # noqa: F401
import app.models.sync_job  # noqa: F401
import app.models.user  # noqa: F401


TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False)


@pytest.fixture(scope="session")
def db_engine():
    Base.metadata.create_all(bind=engine)
    yield engine
    Base.metadata.drop_all(bind=engine)
    if settings.DATABASE_URL.startswith("sqlite"):
        db_file = settings.DATABASE_URL.replace("sqlite:///", "")
        if db_file:
            Path(db_file).unlink(missing_ok=True)


@pytest.fixture(scope="function")
def db_session(db_engine) -> Generator:
    connection = db_engine.connect()
    transaction = connection.begin()
    session = TestingSessionLocal(bind=connection)
    try:
        yield session
    finally:
        session.close()
        transaction.rollback()
        connection.close()


@pytest.fixture(scope="function")
def client(db_session):
    def _get_test_db():
        try:
            yield db_session
        finally:
            pass

    fastapi_app.dependency_overrides[get_db] = _get_test_db
    with TestClient(fastapi_app) as test_client:
        yield test_client
    fastapi_app.dependency_overrides.pop(get_db, None)
