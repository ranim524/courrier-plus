from unittest.mock import patch

from app.models.enums import EmailStatus
from tests.conftest import sample_letter_form


def test_email_mock_mode_records_sent_status(client, auth_headers):
    letter_id = client.post("/api/letters", data=sample_letter_form()).json()["id"]
    payment = client.post("/api/payments/create", json={"letter_id": letter_id}).json()
    client.post(
        "/api/payments/mock/confirm", json={"transaction_id": payment["transaction_id"], "outcome": "success"}
    )

    emails = client.get(f"/api/admin/letters/{letter_id}/emails", headers=auth_headers).json()
    assert len(emails) >= 2
    assert all(e["status"] == "SENT" for e in emails)


def test_resend_failure_is_handled_gracefully(client, db_session, auth_headers):
    letter_id = client.post("/api/letters", data=sample_letter_form()).json()["id"]

    with (
        patch("app.services.email_service.settings.is_email_mock_mode", False),
        patch("resend.Emails.send", side_effect=RuntimeError("Resend API unreachable")),
    ):
        from app.services import email_service

        event = email_service.send_letter_opened(db_session, letter_id, "sender@example.com", "Ahmed", "TN-2026-0000001", "10/01/2026 10:00")
        db_session.commit()

    assert event.status == EmailStatus.FAILED
    assert "Resend API unreachable" in event.error_message

    # The failure must not have crashed anything else in the request lifecycle.
    letter = client.get(f"/api/admin/letters/{letter_id}", headers=auth_headers)
    assert letter.status_code == 200
