from datetime import datetime, timedelta, timezone

from app.core.security import generate_secure_token, hash_token
from app.models.access_token import AccessToken
from app.services import access_service
from tests.conftest import sample_letter_form


def _create_paid_letter(client) -> str:
    letter_id = client.post("/api/letters", data=sample_letter_form()).json()["id"]
    payment = client.post("/api/payments/create", json={"letter_id": letter_id}).json()
    client.post("/api/payments/mock/confirm", json={"transaction_id": payment["transaction_id"], "outcome": "success"})
    return letter_id


def test_access_token_generation_is_random_and_url_safe():
    token_a = generate_secure_token()
    token_b = generate_secure_token()
    assert token_a != token_b
    assert len(token_a) > 30


def test_view_and_open_letter_with_valid_token(client, db_session):
    letter_id = _create_paid_letter(client)
    raw_token = access_service.create_access_token(db_session, letter_id)
    db_session.commit()

    view = client.get(f"/api/access/{raw_token}")
    assert view.status_code == 200
    assert view.json()["subject"] == "Contrat de travail"

    opened = client.post(f"/api/access/{raw_token}/open")
    assert opened.status_code == 200
    assert opened.json()["status"] == "OPENED"


def test_confirm_receipt_transitions_to_received(client, db_session):
    letter_id = _create_paid_letter(client)
    raw_token = access_service.create_access_token(db_session, letter_id)
    db_session.commit()

    client.post(f"/api/access/{raw_token}/open")
    receipt = client.post(f"/api/access/{raw_token}/receive")
    assert receipt.status_code == 200
    assert receipt.json()["status"] == "RECEIVED"


def test_invalid_token_returns_404(client):
    response = client.get("/api/access/not-a-real-token")
    assert response.status_code == 404


def test_expired_token_returns_410(client, db_session):
    letter_id = _create_paid_letter(client)
    raw_token = generate_secure_token()
    token = AccessToken(
        letter_id=letter_id,
        token_hash=hash_token(raw_token),
        expires_at=datetime.now(timezone.utc) - timedelta(days=1),
    )
    db_session.add(token)
    db_session.commit()

    response = client.get(f"/api/access/{raw_token}")
    assert response.status_code == 410


def test_revoked_token_returns_404(client, db_session):
    letter_id = _create_paid_letter(client)
    raw_token = generate_secure_token()
    token = AccessToken(
        letter_id=letter_id,
        token_hash=hash_token(raw_token),
        expires_at=datetime.now(timezone.utc) + timedelta(days=1),
        revoked_at=datetime.now(timezone.utc),
    )
    db_session.add(token)
    db_session.commit()

    response = client.get(f"/api/access/{raw_token}")
    assert response.status_code == 404


def test_confirm_receipt_before_opened_is_rejected_as_invalid_transition(client, db_session):
    letter_id = _create_paid_letter(client)
    raw_token = access_service.create_access_token(db_session, letter_id)
    db_session.commit()

    # Letter is SENT (not yet OPENED). RECEIVED is only reachable from OPENED.
    response = client.post(f"/api/access/{raw_token}/receive")
    assert response.status_code == 409
