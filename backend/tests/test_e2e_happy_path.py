from app.services import access_service
from tests.conftest import sample_letter_form


def test_full_happy_path(client, db_session, auth_headers):
    # 1. Sender creates letter
    create_response = client.post("/api/letters", data=sample_letter_form())
    assert create_response.status_code == 201
    letter_id = create_response.json()["id"]

    # 2. Mock payment succeeds
    payment = client.post("/api/payments/create", json={"letter_id": letter_id}).json()
    confirm = client.post(
        "/api/payments/mock/confirm", json={"transaction_id": payment["transaction_id"], "outcome": "success"}
    ).json()
    assert confirm["status"] == "PAID"

    # 3 & 4. Letter becomes PAID then SENT, reference generated
    letter = client.get(f"/api/admin/letters/{letter_id}", headers=auth_headers).json()
    assert letter["status"] == "SENT"
    reference = letter["reference"]
    assert reference

    # 5. Resend email triggered (mock mode) — recorded as email_events
    emails = client.get(f"/api/admin/letters/{letter_id}/emails", headers=auth_headers).json()
    assert any(e["email_type"] == "PAYMENT_CONFIRMATION" and e["status"] == "SENT" for e in emails)
    assert any(e["email_type"] == "RECIPIENT_NOTIFICATION" and e["status"] == "SENT" for e in emails)

    # 6. Recipient accesses secure link
    raw_token = access_service.create_access_token(db_session, letter_id)
    db_session.commit()
    view = client.get(f"/api/access/{raw_token}")
    assert view.status_code == 200

    # 7. OPENED event recorded
    opened = client.post(f"/api/access/{raw_token}/open")
    assert opened.status_code == 200
    assert opened.json()["status"] == "OPENED"

    events = client.get(f"/api/admin/letters/{letter_id}/events", headers=auth_headers).json()
    assert any(e["event_type"] == "LETTER_OPENED" for e in events)

    # 8. Recipient confirms receipt
    received = client.post(f"/api/access/{raw_token}/receive")
    assert received.status_code == 200
    assert received.json()["status"] == "RECEIVED"

    # 9. RECEIVED event recorded
    events = client.get(f"/api/admin/letters/{letter_id}/events", headers=auth_headers).json()
    assert any(e["event_type"] == "RECEIPT_CONFIRMED" for e in events)

    # 10. Sender notification triggered for both opened and received
    emails = client.get(f"/api/admin/letters/{letter_id}/emails", headers=auth_headers).json()
    assert any(e["email_type"] == "LETTER_OPENED" for e in emails)
    assert any(e["email_type"] == "RECEIPT_CONFIRMED" for e in emails)

    # Final tracking view reflects the whole lifecycle
    tracking = client.get(f"/api/track/{reference}").json()
    assert tracking["status"] == "RECEIVED"
