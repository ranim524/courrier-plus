from tests.conftest import sample_letter_form


def test_tracking_unknown_reference_returns_404(client):
    response = client.get("/api/track/TN-2026-9999999")
    assert response.status_code == 404


def test_tracking_returns_events_after_payment(client, auth_headers):
    letter_id = client.post("/api/letters", data=sample_letter_form()).json()["id"]
    payment = client.post("/api/payments/create", json={"letter_id": letter_id}).json()
    client.post(
        "/api/payments/mock/confirm", json={"transaction_id": payment["transaction_id"], "outcome": "success"}
    )

    letter = client.get(f"/api/admin/letters/{letter_id}", headers=auth_headers).json()
    reference = letter["reference"]
    assert reference is not None

    tracking = client.get(f"/api/track/{reference}")
    assert tracking.status_code == 200
    body = tracking.json()
    assert body["status"] == "SENT"
    event_types = [e["event_type"] for e in body["events"]]
    assert "LETTER_CREATED" in event_types
    assert "PAYMENT_SUCCEEDED" in event_types
    assert "LETTER_SENT" in event_types
