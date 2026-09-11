from app.repositories import delivery_provider_repository, delivery_repository
from app.services import delivery_service
from tests.conftest import sample_letter_form


class FakeAdmin:
    """Lightweight stand-in for the Admin ORM object -- delivery_service only
    ever reads .email off it."""

    email = "admin@courrierplus.tn"


def test_full_happy_path(client, db_session, auth_headers):
    # 1. Sender creates letter with the paid acknowledgment of receipt, so
    # this path exercises the RECEIVED status via physical confirmation.
    form = sample_letter_form()
    form["acknowledgment_of_receipt"] = "true"
    create_response = client.post("/api/letters", data=form)
    assert create_response.status_code == 201
    letter_id = create_response.json()["id"]

    # 2. Mock payment succeeds
    payment = client.post("/api/payments/create", json={"letter_id": letter_id}).json()
    confirm = client.post(
        "/api/payments/mock/confirm", json={"transaction_id": payment["transaction_id"], "outcome": "success"}
    ).json()
    assert confirm["status"] == "PAID"

    # 3 & 4. Letter becomes PAID then SENT, reference generated, delivery order auto-created
    letter = client.get(f"/api/admin/letters/{letter_id}", headers=auth_headers).json()
    assert letter["status"] == "SENT"
    reference = letter["reference"]
    assert reference

    # 5. Only the sender's payment-confirmation email is sent -- the
    # recipient gets nothing at this point (no digital access anymore).
    emails = client.get(f"/api/admin/letters/{letter_id}/emails", headers=auth_headers).json()
    assert any(e["email_type"] == "PAYMENT_CONFIRMATION" and e["status"] == "SENT" for e in emails)
    assert not any(e["recipient"] == form["recipient_email"] for e in emails)

    # 6. Admin runs the physical delivery through to confirmation
    order = delivery_repository.get_by_letter_id(db_session, letter_id)
    provider = delivery_provider_repository.get_by_code(db_session, "courrier_plus_internal")
    from app.models.delivery import DeliveryAgent
    from app.repositories import delivery_agent_repository

    agent = delivery_agent_repository.create(
        db_session,
        DeliveryAgent(provider_id=provider.id, first_name="Mohamed", last_name="Ben Ali", phone="+21600000000"),
    )
    db_session.commit()
    admin = FakeAdmin()

    delivery_service.assign_courier(db_session, order.id, agent.id, admin)
    delivery_service.mark_picked_up(db_session, order.id, admin)
    delivery_service.mark_in_transit(db_session, order.id, admin)
    delivery_service.mark_out_for_delivery(db_session, order.id, admin)
    delivery_service.mark_deposited(db_session, order.id, admin)
    delivery_service.force_confirm_delivery(db_session, order.id, admin)

    # 7. Letter reaches RECEIVED (acknowledgment of receipt was requested) --
    # only once the physical letter was actually confirmed delivered.
    letter = client.get(f"/api/admin/letters/{letter_id}", headers=auth_headers).json()
    assert letter["status"] == "RECEIVED"

    # 8. Recipient got exactly one confirmation-request email when deposited;
    # sender got exactly one delivery-confirmed email once the admin
    # force-confirmed (the recipient never gets a second email).
    emails = client.get(f"/api/admin/letters/{letter_id}/emails", headers=auth_headers).json()
    assert sum(1 for e in emails if e["email_type"] == "DELIVERY_CONFIRMATION_REQUEST") == 1
    assert sum(1 for e in emails if e["email_type"] == "DELIVERY_CONFIRMED_SENDER") == 1
    assert not any(e["email_type"] == "DELIVERY_CONFIRMED_RECIPIENT" for e in emails)

    # Final tracking view reflects the whole lifecycle
    tracking = client.get(f"/api/track/{reference}").json()
    assert tracking["status"] == "RECEIVED"
    assert tracking["delivery"]["status"] == "DELIVERED"
