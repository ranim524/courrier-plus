from tests.conftest import sample_letter_form


def _create_letter(client) -> str:
    response = client.post("/api/letters", data=sample_letter_form())
    return response.json()["id"]


def test_create_payment_succeeds(client):
    letter_id = _create_letter(client)
    response = client.post("/api/payments/create", json={"letter_id": letter_id})
    assert response.status_code == 201
    body = response.json()
    assert body["status"] == "PENDING"
    assert body["transaction_id"].startswith("mock_")


def test_confirm_payment_success_activates_letter(client, auth_headers):
    letter_id = _create_letter(client)
    payment = client.post("/api/payments/create", json={"letter_id": letter_id}).json()

    response = client.post(
        "/api/payments/mock/confirm", json={"transaction_id": payment["transaction_id"], "outcome": "success"}
    )
    assert response.status_code == 200
    assert response.json()["status"] == "PAID"

    letter = client.get(f"/api/admin/letters/{letter_id}", headers=auth_headers).json()
    assert letter["status"] == "SENT"
    assert letter["reference"] is not None
    assert letter["reference"].startswith("TN-")


def test_confirm_payment_failure_marks_letter_failed(client, auth_headers):
    letter_id = _create_letter(client)
    payment = client.post("/api/payments/create", json={"letter_id": letter_id}).json()

    response = client.post(
        "/api/payments/mock/confirm", json={"transaction_id": payment["transaction_id"], "outcome": "failure"}
    )
    assert response.status_code == 200
    assert response.json()["status"] == "FAILED"

    letter = client.get(f"/api/admin/letters/{letter_id}", headers=auth_headers).json()
    assert letter["status"] == "FAILED"


def test_duplicate_payment_confirmation_is_idempotent(client, auth_headers):
    letter_id = _create_letter(client)
    payment = client.post("/api/payments/create", json={"letter_id": letter_id}).json()

    first = client.post(
        "/api/payments/mock/confirm", json={"transaction_id": payment["transaction_id"], "outcome": "success"}
    ).json()
    second = client.post(
        "/api/payments/mock/confirm", json={"transaction_id": payment["transaction_id"], "outcome": "success"}
    ).json()

    assert first["id"] == second["id"]

    events = client.get(f"/api/admin/letters/{letter_id}/events", headers=auth_headers).json()
    sent_events = [e for e in events if e["event_type"] == "LETTER_SENT"]
    assert len(sent_events) == 1

    emails = client.get(f"/api/admin/letters/{letter_id}/emails", headers=auth_headers).json()
    recipient_emails = [e for e in emails if e["email_type"] == "RECIPIENT_NOTIFICATION"]
    assert len(recipient_emails) == 1


def test_confirm_unknown_transaction_returns_404(client):
    response = client.post("/api/payments/mock/confirm", json={"transaction_id": "does-not-exist", "outcome": "success"})
    assert response.status_code == 404
