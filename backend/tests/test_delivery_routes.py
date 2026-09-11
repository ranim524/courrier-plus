from unittest.mock import patch

from app.core.config import get_settings
from app.models.enums import DeliveryFailureReason
from app.repositories import delivery_agent_repository, delivery_provider_repository, delivery_repository
from app.services import delivery_service
from tests.conftest import sample_letter_form


def _create_sent_letter(client, db_session):
    letter_id = client.post("/api/letters", data=sample_letter_form()).json()["id"]
    payment = client.post("/api/payments/create", json={"letter_id": letter_id}).json()
    client.post("/api/payments/mock/confirm", json={"transaction_id": payment["transaction_id"], "outcome": "success"})
    order = delivery_repository.get_by_letter_id(db_session, letter_id)
    return letter_id, order


def _create_agent_via_api(client, auth_headers, db_session):
    provider = delivery_provider_repository.get_by_code(db_session, "courrier_plus_internal")
    response = client.post(
        "/api/admin/delivery-agents",
        headers=auth_headers,
        json={"provider_id": str(provider.id), "first_name": "Mohamed", "last_name": "Ben Ali", "phone": "+21600000000"},
    )
    assert response.status_code == 201
    return response.json()["id"]


def _advance_to_out_for_delivery(client, auth_headers, delivery_id, agent_id):
    client.post(f"/api/admin/deliveries/{delivery_id}/assign", headers=auth_headers, json={"agent_id": agent_id})
    client.post(f"/api/admin/deliveries/{delivery_id}/pickup", headers=auth_headers)
    client.post(f"/api/admin/deliveries/{delivery_id}/in-transit", headers=auth_headers)
    client.post(f"/api/admin/deliveries/{delivery_id}/out-for-delivery", headers=auth_headers)


def _deposit_with_known_token(client, auth_headers, delivery_id, raw_token="test-confirmation-token-123"):
    with patch("app.services.delivery_service.generate_secure_token", return_value=raw_token):
        response = client.post(f"/api/admin/deliveries/{delivery_id}/deposit", headers=auth_headers)
    assert response.status_code == 200
    return raw_token


# ---------------------------------------------------------------------------
# The mandatory critical email test -- no delivery email before DEPOSITED,
# exactly one confirmation-request to the recipient on deposit, and exactly
# one delivery-confirmed email to the sender once the recipient confirms --
# never before, never duplicated.
# ---------------------------------------------------------------------------


def test_no_delivery_email_before_deposited_then_exactly_one_on_recipient_confirm(client, db_session, auth_headers):
    letter_id, order = _create_sent_letter(client, db_session)
    agent_id = _create_agent_via_api(client, auth_headers, db_session)

    client.post(f"/api/admin/deliveries/{order.id}/assign", headers=auth_headers, json={"agent_id": agent_id})
    client.post(f"/api/admin/deliveries/{order.id}/pickup", headers=auth_headers)
    client.post(f"/api/admin/deliveries/{order.id}/in-transit", headers=auth_headers)

    emails = client.get(f"/api/admin/letters/{letter_id}/emails", headers=auth_headers).json()
    assert not any("DELIVERY_CONFIRM" in e["email_type"] for e in emails)

    client.post(f"/api/admin/deliveries/{order.id}/out-for-delivery", headers=auth_headers)
    emails = client.get(f"/api/admin/letters/{letter_id}/emails", headers=auth_headers).json()
    assert not any("DELIVERY_CONFIRM" in e["email_type"] for e in emails)

    # Deposited: recipient gets exactly one confirmation REQUEST (not yet a
    # "delivered" confirmation) -- the sender gets nothing at this point.
    raw_token = _deposit_with_known_token(client, auth_headers, order.id)
    emails = client.get(f"/api/admin/letters/{letter_id}/emails", headers=auth_headers).json()
    assert len([e for e in emails if e["email_type"] == "DELIVERY_CONFIRMATION_REQUEST"]) == 1
    assert not any(e["email_type"] in ("DELIVERY_CONFIRMED_RECIPIENT", "DELIVERY_CONFIRMED_SENDER") for e in emails)

    delivery = client.get(f"/api/admin/deliveries/{order.id}", headers=auth_headers).json()
    assert delivery["status"] == "DEPOSITED"

    # Recipient clicks the confirmation link -- only now is the sender notified.
    confirm = client.post(f"/api/delivery-confirmation/{raw_token}/confirm")
    assert confirm.status_code == 200
    assert confirm.json()["confirmed"] is True

    delivery = client.get(f"/api/admin/deliveries/{order.id}", headers=auth_headers).json()
    assert delivery["status"] == "DELIVERED"

    emails = client.get(f"/api/admin/letters/{letter_id}/emails", headers=auth_headers).json()
    assert len([e for e in emails if e["email_type"] == "DELIVERY_CONFIRMED_SENDER"]) == 1
    # The recipient already acted -- no redundant second email to them.
    assert not any(e["email_type"] == "DELIVERY_CONFIRMED_RECIPIENT" for e in emails)

    # The confirmation token is single-use: reusing it must not resend anything.
    confirm_again = client.post(f"/api/delivery-confirmation/{raw_token}/confirm")
    assert confirm_again.status_code == 404

    emails_after = client.get(f"/api/admin/letters/{letter_id}/emails", headers=auth_headers).json()
    assert len([e for e in emails_after if e["email_type"] == "DELIVERY_CONFIRMED_SENDER"]) == 1


def test_force_confirm_delivery_idempotent_no_duplicate_proof(client, db_session, auth_headers):
    letter_id, order = _create_sent_letter(client, db_session)
    agent_id = _create_agent_via_api(client, auth_headers, db_session)
    _advance_to_out_for_delivery(client, auth_headers, order.id, agent_id)
    client.post(f"/api/admin/deliveries/{order.id}/deposit", headers=auth_headers)

    first = client.post(f"/api/admin/deliveries/{order.id}/force-confirm", headers=auth_headers, json={}).json()
    second = client.post(f"/api/admin/deliveries/{order.id}/force-confirm", headers=auth_headers, json={}).json()
    assert first["delivered_at"] == second["delivered_at"]

    events = client.get(f"/api/admin/letters/{letter_id}/events", headers=auth_headers).json()
    delivered_events = [e for e in events if e["event_type"] == "DELIVERY_DELIVERED"]
    assert len(delivered_events) == 1


def test_force_confirm_after_recipient_already_confirmed_is_a_no_op(client, db_session, auth_headers):
    """Admin fallback must never duplicate the sender email if the recipient
    happened to confirm in the meantime."""
    letter_id, order = _create_sent_letter(client, db_session)
    agent_id = _create_agent_via_api(client, auth_headers, db_session)
    _advance_to_out_for_delivery(client, auth_headers, order.id, agent_id)
    raw_token = _deposit_with_known_token(client, auth_headers, order.id)

    client.post(f"/api/delivery-confirmation/{raw_token}/confirm")
    client.post(f"/api/admin/deliveries/{order.id}/force-confirm", headers=auth_headers, json={})

    emails = client.get(f"/api/admin/letters/{letter_id}/emails", headers=auth_headers).json()
    assert len([e for e in emails if e["email_type"] == "DELIVERY_CONFIRMED_SENDER"]) == 1


# ---------------------------------------------------------------------------
# Public delivery-confirmation link (recipient-facing, no content exposed)
# ---------------------------------------------------------------------------


def test_confirmation_view_shows_no_letter_content(client, db_session, auth_headers):
    letter_id, order = _create_sent_letter(client, db_session)
    agent_id = _create_agent_via_api(client, auth_headers, db_session)
    _advance_to_out_for_delivery(client, auth_headers, order.id, agent_id)
    raw_token = _deposit_with_known_token(client, auth_headers, order.id)

    response = client.get(f"/api/delivery-confirmation/{raw_token}")
    assert response.status_code == 200
    body = response.json()
    assert body["reference"]
    assert body["confirmed"] is False
    # No message/subject/PDF access -- only enough to recognize the letter.
    assert "message" not in body
    assert "subject" not in body


def test_confirmation_view_invalid_token_returns_404(client):
    response = client.get("/api/delivery-confirmation/not-a-real-token")
    assert response.status_code == 404


def test_confirmation_before_deposited_returns_404(client, db_session):
    _, order = _create_sent_letter(client, db_session)
    response = client.get(f"/api/delivery-confirmation/{order.tracking_number}")
    assert response.status_code == 404


# ---------------------------------------------------------------------------
# External carrier webhook
# ---------------------------------------------------------------------------


def test_webhook_deposits_delivery_with_valid_secret(client, db_session, auth_headers):
    letter_id, order = _create_sent_letter(client, db_session)
    agent_id = _create_agent_via_api(client, auth_headers, db_session)
    _advance_to_out_for_delivery(client, auth_headers, order.id, agent_id)

    with patch.object(get_settings(), "delivery_webhook_secret", "test-webhook-secret"):
        response = client.post(
            "/api/webhooks/delivery/deposited",
            json={"provider_code": "courrier_plus_internal", "tracking_number": order.tracking_number},
            headers={"X-Webhook-Secret": "test-webhook-secret"},
        )
    assert response.status_code == 200
    assert response.json()["status"] == "DEPOSITED"

    emails = client.get(f"/api/admin/letters/{letter_id}/emails", headers=auth_headers).json()
    assert len([e for e in emails if e["email_type"] == "DELIVERY_CONFIRMATION_REQUEST"]) == 1


def test_webhook_rejects_wrong_secret(client, db_session, auth_headers):
    letter_id, order = _create_sent_letter(client, db_session)
    agent_id = _create_agent_via_api(client, auth_headers, db_session)
    _advance_to_out_for_delivery(client, auth_headers, order.id, agent_id)

    with patch.object(get_settings(), "delivery_webhook_secret", "correct-secret"):
        response = client.post(
            "/api/webhooks/delivery/deposited",
            json={"provider_code": "courrier_plus_internal", "tracking_number": order.tracking_number},
            headers={"X-Webhook-Secret": "wrong-secret"},
        )
    assert response.status_code == 401


def test_webhook_rejects_when_no_secret_configured(client, db_session, auth_headers):
    letter_id, order = _create_sent_letter(client, db_session)
    agent_id = _create_agent_via_api(client, auth_headers, db_session)
    _advance_to_out_for_delivery(client, auth_headers, order.id, agent_id)

    with patch.object(get_settings(), "delivery_webhook_secret", ""):
        response = client.post(
            "/api/webhooks/delivery/deposited",
            json={"provider_code": "courrier_plus_internal", "tracking_number": order.tracking_number},
            headers={"X-Webhook-Secret": "anything"},
        )
    assert response.status_code == 401


def test_webhook_unknown_tracking_number_returns_404(client):
    with patch.object(get_settings(), "delivery_webhook_secret", "test-webhook-secret"):
        response = client.post(
            "/api/webhooks/delivery/deposited",
            json={"provider_code": "courrier_plus_internal", "tracking_number": "CP-2026-9999999"},
            headers={"X-Webhook-Secret": "test-webhook-secret"},
        )
    assert response.status_code == 404


# ---------------------------------------------------------------------------
# Authorization
# ---------------------------------------------------------------------------


def test_delivery_endpoints_require_admin_auth(client, db_session):
    _, order = _create_sent_letter(client, db_session)
    assert client.get("/api/admin/deliveries").status_code == 401
    assert client.get(f"/api/admin/deliveries/{order.id}").status_code == 401
    assert client.post(f"/api/admin/deliveries/{order.id}/pickup").status_code == 401
    assert client.post(f"/api/admin/deliveries/{order.id}/deposit").status_code == 401
    assert client.post(f"/api/admin/deliveries/{order.id}/force-confirm", json={}).status_code == 401


def test_recipient_and_sender_have_no_delivery_mutation_endpoint(client, db_session):
    """There is no public/sender/recipient-facing route that can change a
    delivery's status directly by id -- only /api/admin/deliveries/* (fully
    authenticated) and /api/delivery-confirmation/{token} (token-scoped to
    exactly one delivery, single-use). This test documents that guarantee
    structurally."""
    _, order = _create_sent_letter(client, db_session)
    assert client.post(f"/api/deliveries/{order.id}/confirm-delivery").status_code == 404


# ---------------------------------------------------------------------------
# List / detail / filters
# ---------------------------------------------------------------------------


def test_list_deliveries_and_filter_by_status(client, db_session, auth_headers):
    _create_sent_letter(client, db_session)
    response = client.get("/api/admin/deliveries", headers=auth_headers)
    assert response.status_code == 200
    body = response.json()
    assert body["total"] >= 1

    filtered = client.get("/api/admin/deliveries?status=READY_FOR_DISPATCH", headers=auth_headers)
    assert filtered.status_code == 200
    assert all(item["status"] == "READY_FOR_DISPATCH" for item in filtered.json()["items"])


def test_search_deliveries_by_tracking_number(client, db_session, auth_headers):
    letter_id, order = _create_sent_letter(client, db_session)
    response = client.get(f"/api/admin/deliveries?search={order.tracking_number}", headers=auth_headers)
    assert response.status_code == 200
    body = response.json()
    assert any(item["tracking_number"] == order.tracking_number for item in body["items"])


def test_delivery_detail_includes_provider_and_attempts(client, db_session, auth_headers):
    letter_id, order = _create_sent_letter(client, db_session)
    response = client.get(f"/api/admin/deliveries/{order.id}", headers=auth_headers)
    assert response.status_code == 200
    body = response.json()
    assert body["provider"]["code"] == "courrier_plus_internal"
    assert body["attempts"] == []
    assert body["proof"] is None


def test_delivery_not_found_returns_404(client, auth_headers):
    import uuid

    response = client.get(f"/api/admin/deliveries/{uuid.uuid4()}", headers=auth_headers)
    assert response.status_code == 404


# ---------------------------------------------------------------------------
# Public tracking
# ---------------------------------------------------------------------------


def test_public_tracking_includes_delivery_view_without_courier_info(client, db_session, auth_headers):
    letter_id, order = _create_sent_letter(client, db_session)
    letter = client.get(f"/api/admin/letters/{letter_id}", headers=auth_headers).json()
    reference = letter["reference"]

    response = client.get(f"/api/track/{reference}")
    assert response.status_code == 200
    body = response.json()
    assert body["delivery"] is not None
    assert body["delivery"]["tracking_number"] == order.tracking_number
    assert body["delivery"]["status"] == "READY_FOR_DISPATCH"
    # No courier name/phone, no admin notes, no internal delivery UUID leaked.
    assert "courier" not in body["delivery"]
    assert "id" not in body["delivery"]


def test_delivery_agent_management(client, db_session, auth_headers):
    provider = delivery_provider_repository.get_by_code(db_session, "courrier_plus_internal")
    create_response = client.post(
        "/api/admin/delivery-agents",
        headers=auth_headers,
        json={"provider_id": str(provider.id), "first_name": "Sami", "last_name": "Trabelsi", "phone": "+21611111111"},
    )
    assert create_response.status_code == 201
    agent_id = create_response.json()["id"]

    list_response = client.get("/api/admin/delivery-agents", headers=auth_headers)
    assert any(a["id"] == agent_id for a in list_response.json())

    deactivate = client.patch(f"/api/admin/delivery-agents/{agent_id}", headers=auth_headers, json={"active": False})
    assert deactivate.status_code == 200
    assert deactivate.json()["active"] is False


def test_delivery_providers_list(client, auth_headers):
    response = client.get("/api/admin/delivery-providers", headers=auth_headers)
    assert response.status_code == 200
    codes = [p["code"] for p in response.json()]
    assert "courrier_plus_internal" in codes


def test_mark_failed_requires_reason(client, db_session, auth_headers):
    letter_id, order = _create_sent_letter(client, db_session)
    agent_id = _create_agent_via_api(client, auth_headers, db_session)
    client.post(f"/api/admin/deliveries/{order.id}/assign", headers=auth_headers, json={"agent_id": agent_id})
    client.post(f"/api/admin/deliveries/{order.id}/pickup", headers=auth_headers)
    client.post(f"/api/admin/deliveries/{order.id}/in-transit", headers=auth_headers)
    client.post(f"/api/admin/deliveries/{order.id}/out-for-delivery", headers=auth_headers)

    missing_reason = client.post(f"/api/admin/deliveries/{order.id}/fail", headers=auth_headers, json={})
    assert missing_reason.status_code == 422

    with_reason = client.post(
        f"/api/admin/deliveries/{order.id}/fail",
        headers=auth_headers,
        json={"reason": DeliveryFailureReason.RECIPIENT_UNAVAILABLE.value, "notes": "Absent"},
    )
    assert with_reason.status_code == 200
    assert with_reason.json()["status"] == "DELIVERY_FAILED"


def test_invalid_status_transition_via_api_returns_409(client, db_session, auth_headers):
    letter_id, order = _create_sent_letter(client, db_session)
    # Cannot force-confirm straight from READY_FOR_DISPATCH -- DEPOSITED first.
    response = client.post(f"/api/admin/deliveries/{order.id}/force-confirm", headers=auth_headers, json={})
    assert response.status_code == 409
