import io
from collections.abc import Generator

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker

from app.core.config import get_settings
from app.core.database import Base, get_db
from app.main import app
from app.services.admin_service import create_admin_if_not_exists

settings = get_settings()

TEST_DATABASE_URL = settings.database_url.rsplit("/", 1)[0] + "/courrier_plus_test"

engine = create_engine(TEST_DATABASE_URL)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def _ensure_test_database() -> None:
    admin_engine = create_engine(settings.database_url.rsplit("/", 1)[0] + "/postgres", isolation_level="AUTOCOMMIT")
    with admin_engine.connect() as conn:
        exists = conn.execute(
            text("SELECT 1 FROM pg_database WHERE datname = 'courrier_plus_test'")
        ).first()
        if not exists:
            conn.execute(text("CREATE DATABASE courrier_plus_test OWNER courrier_plus"))
    admin_engine.dispose()


@pytest.fixture(scope="session", autouse=True)
def setup_database():
    _ensure_test_database()
    Base.metadata.create_all(bind=engine)
    yield
    Base.metadata.drop_all(bind=engine)


@pytest.fixture()
def db_session() -> Generator:
    connection = engine.connect()
    transaction = connection.begin()
    session = TestingSessionLocal(bind=connection)

    yield session

    session.close()
    transaction.rollback()
    connection.close()


@pytest.fixture()
def client(db_session) -> Generator[TestClient, None, None]:
    def override_get_db():
        yield db_session

    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app) as test_client:
        yield test_client
    app.dependency_overrides.clear()


@pytest.fixture()
def admin_token(client, db_session) -> str:
    create_admin_if_not_exists(db_session, "admin@test.com", "TestPassword123!")
    db_session.commit()
    response = client.post("/api/admin/login", json={"email": "admin@test.com", "password": "TestPassword123!"})
    return response.json()["access_token"]


@pytest.fixture()
def auth_headers(admin_token) -> dict:
    return {"Authorization": f"Bearer {admin_token}"}


def sample_letter_form() -> dict:
    return {
        "sender_first_name": "Ahmed",
        "sender_last_name": "Ben Ali",
        "sender_email": "ahmed@example.com",
        "recipient_first_name": "Sami",
        "recipient_last_name": "Trabelsi",
        "recipient_email": "sami@example.com",
        "subject": "Contrat de travail",
        "message": "Veuillez trouver ci-joint les termes du contrat.",
    }


def minimal_pdf_bytes() -> bytes:
    return b"%PDF-1.4\n%mock pdf content for tests\n%%EOF"


def make_pdf_file() -> tuple[str, io.BytesIO, str]:
    return ("document.pdf", io.BytesIO(minimal_pdf_bytes()), "application/pdf")
