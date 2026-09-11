from unittest.mock import PropertyMock, patch

from app.models.enums import EmailStatus
from app.services.email_service import settings as email_settings
from tests.conftest import sample_letter_form


def test_email_mock_mode_records_sent_status(client, auth_headers):
    letter_id = client.post("/api/letters", data=sample_letter_form()).json()["id"]
    payment = client.post("/api/payments/create", json={"letter_id": letter_id}).json()
    client.post(
        "/api/payments/mock/confirm", json={"transaction_id": payment["transaction_id"], "outcome": "success"}
    )

    emails = client.get(f"/api/admin/letters/{letter_id}/emails", headers=auth_headers).json()
    assert len(emails) >= 1
    assert any(e["email_type"] == "PAYMENT_CONFIRMATION" for e in emails)
    assert all(e["status"] == "SENT" for e in emails)


def test_resend_failure_is_handled_gracefully(client, db_session, auth_headers):
    letter_id = client.post("/api/letters", data=sample_letter_form()).json()["id"]

    with (
        patch.object(type(email_settings), "is_email_mock_mode", new_callable=PropertyMock, return_value=False),
        patch("resend.Emails.send", side_effect=RuntimeError("Resend API unreachable")),
    ):
        from app.services import email_service

        event = email_service.send_delivery_confirmed_sender(
            db_session,
            letter_id,
            "sender@example.com",
            "Ahmed",
            "TN-2026-0000001",
            "CP-2026-0000001",
            "10/01/2026",
            "10:00",
            "http://localhost:5173/track/TN-2026-0000001",
        )
        db_session.commit()

    assert event.status == EmailStatus.FAILED
    assert "Resend API unreachable" in event.error_message

    # The failure must not have crashed anything else in the request lifecycle.
    letter = client.get(f"/api/admin/letters/{letter_id}", headers=auth_headers)
    assert letter.status_code == 200
