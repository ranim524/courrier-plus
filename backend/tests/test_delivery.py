import pytest

from app.core.exceptions import ConflictError
from app.models.enums import DeliveryFailureReason, DeliveryStatus, LetterStatus
from app.repositories import delivery_repository
from app.services import delivery_service
from tests.conftest import sample_letter_form


def _create_sent_letter(client, db_session):
    """Creates and pays a letter, which auto-creates its DeliveryOrder
    (READY_FOR_DISPATCH) via the payment_service integration."""
    letter_id = client.post("/api/letters", data=sample_letter_form()).json()["id"]
    payment = client.post("/api/payments/create", json={"letter_id": letter_id}).json()
    client.post("/api/payments/mock/confirm", json={"transaction_id": payment["transaction_id"], "outcome": "success"})
    order = delivery_repository.get_by_letter_id(db_session, letter_id)
    return letter_id, order


def _create_agent(db_session):
    from app.models.delivery import DeliveryAgent
    from app.repositories import delivery_agent_repository, delivery_provider_repository

    provider = delivery_provider_repository.get_by_code(db_session, "courrier_plus_internal")
    agent = DeliveryAgent(
        provider_id=provider.id, first_name="Mohamed", last_name="Ben Ali", phone="+21600000000"
    )
    agent = delivery_agent_repository.create(db_session, agent)
    db_session.commit()
    return agent


class FakeAdmin:
    """Lightweight stand-in for the Admin ORM object -- delivery_service only
    ever reads .email off it."""

    email = "admin@courrierplus.tn"


def test_delivery_order_auto_created_on_payment(client, db_session):
    letter_id, order = _create_sent_letter(client, db_session)
    assert order is not None
    assert order.status == DeliveryStatus.READY_FOR_DISPATCH
    assert order.tracking_number.startswith("CP-")


def test_tracking_number_is_unique_and_not_the_db_id(client, db_session):
    _, order1 = _create_sent_letter(client, db_session)
    _, order2 = _create_sent_letter(client, db_session)
    assert order1.tracking_number != order2.tracking_number
    assert str(order1.id) != order1.tracking_number


def test_full_delivery_workflow(client, db_session):
    letter_id, order = _create_sent_letter(client, db_session)
    agent = _create_agent(db_session)
    admin = FakeAdmin()

    order = delivery_service.assign_courier(db_session, order.id, agent.id, admin)
    assert order.status == DeliveryStatus.ASSIGNED
    assert order.courier_id == agent.id
    assert order.assigned_at is not None

    order = delivery_service.mark_picked_up(db_session, order.id, admin)
    assert order.status == DeliveryStatus.PICKED_UP
    assert order.picked_up_at is not None

    order = delivery_service.mark_in_transit(db_session, order.id, admin)
    assert order.status == DeliveryStatus.IN_TRANSIT

    order = delivery_service.mark_out_for_delivery(db_session, order.id, admin)
    assert order.status == DeliveryStatus.OUT_FOR_DELIVERY

    order = delivery_service.mark_deposited(db_session, order.id, admin)
    assert order.status == DeliveryStatus.DEPOSITED
    assert order.deposited_at is not None
    assert order.confirmation_token_hash is not None
    assert order.proof is None  # not delivered yet -- only deposited

    order = delivery_service.force_confirm_delivery(db_session, order.id, admin)
    assert order.status == DeliveryStatus.DELIVERED
    assert order.delivered_at is not None
    assert order.confirmation_token_hash is None  # single-use, invalidated
    assert order.proof is not None
    assert "admin@courrierplus.tn" in order.proof.delivered_by


def test_invalid_transition_is_rejected(client, db_session):
    letter_id, order = _create_sent_letter(client, db_session)
    admin = FakeAdmin()
    # Cannot force-confirm straight from READY_FOR_DISPATCH -- DEPOSITED first.
    with pytest.raises(ConflictError):
        delivery_service.force_confirm_delivery(db_session, order.id, admin)


def test_deposited_required_before_delivered(client, db_session):
    letter_id, order = _create_sent_letter(client, db_session)
    agent = _create_agent(db_session)
    admin = FakeAdmin()

    delivery_service.assign_courier(db_session, order.id, agent.id, admin)
    delivery_service.mark_picked_up(db_session, order.id, admin)
    delivery_service.mark_in_transit(db_session, order.id, admin)
    order = delivery_service.mark_out_for_delivery(db_session, order.id, admin)

    with pytest.raises(ConflictError):
        delivery_service.force_confirm_delivery(db_session, order.id, admin)


def test_delivered_is_terminal_no_backward_transition(client, db_session):
    letter_id, order = _create_sent_letter(client, db_session)
    agent = _create_agent(db_session)
    admin = FakeAdmin()

    delivery_service.assign_courier(db_session, order.id, agent.id, admin)
    delivery_service.mark_picked_up(db_session, order.id, admin)
    delivery_service.mark_in_transit(db_session, order.id, admin)
    delivery_service.mark_out_for_delivery(db_session, order.id, admin)
    delivery_service.mark_deposited(db_session, order.id, admin)
    delivery_service.force_confirm_delivery(db_session, order.id, admin)

    with pytest.raises(ConflictError):
        delivery_service.mark_in_transit(db_session, order.id, admin)


def test_force_confirm_is_idempotent(client, db_session):
    letter_id, order = _create_sent_letter(client, db_session)
    agent = _create_agent(db_session)
    admin = FakeAdmin()

    delivery_service.assign_courier(db_session, order.id, agent.id, admin)
    delivery_service.mark_picked_up(db_session, order.id, admin)
    delivery_service.mark_in_transit(db_session, order.id, admin)
    delivery_service.mark_out_for_delivery(db_session, order.id, admin)
    delivery_service.mark_deposited(db_session, order.id, admin)

    first = delivery_service.force_confirm_delivery(db_session, order.id, admin)
    second = delivery_service.force_confirm_delivery(db_session, order.id, admin)
    assert first.delivered_at == second.delivered_at


def test_delivery_failure_and_retry(client, db_session):
    letter_id, order = _create_sent_letter(client, db_session)
    agent = _create_agent(db_session)
    admin = FakeAdmin()

    delivery_service.assign_courier(db_session, order.id, agent.id, admin)
    delivery_service.mark_picked_up(db_session, order.id, admin)
    delivery_service.mark_in_transit(db_session, order.id, admin)
    delivery_service.mark_out_for_delivery(db_session, order.id, admin)

    order = delivery_service.mark_failed(
        db_session, order.id, DeliveryFailureReason.RECIPIENT_UNAVAILABLE, admin, notes="Personne absente"
    )
    assert order.status == DeliveryStatus.DELIVERY_FAILED
    assert order.attempt_count == 1
    assert len(order.attempts) == 1
    assert order.attempts[0].reason == DeliveryFailureReason.RECIPIENT_UNAVAILABLE

    order = delivery_service.retry_delivery(db_session, order.id, admin)
    assert order.status == DeliveryStatus.OUT_FOR_DELIVERY

    delivery_service.mark_deposited(db_session, order.id, admin)
    order = delivery_service.force_confirm_delivery(db_session, order.id, admin)
    assert order.status == DeliveryStatus.DELIVERED


def test_return_to_sender(client, db_session):
    letter_id, order = _create_sent_letter(client, db_session)
    agent = _create_agent(db_session)
    admin = FakeAdmin()

    delivery_service.assign_courier(db_session, order.id, agent.id, admin)
    delivery_service.mark_picked_up(db_session, order.id, admin)
    delivery_service.mark_in_transit(db_session, order.id, admin)
    delivery_service.mark_out_for_delivery(db_session, order.id, admin)
    delivery_service.mark_failed(db_session, order.id, DeliveryFailureReason.INCORRECT_ADDRESS, admin)

    order = delivery_service.return_to_sender(db_session, order.id, admin)
    assert order.status == DeliveryStatus.RETURNED_TO_SENDER
    assert order.returned_at is not None


def test_cancel_delivery_from_early_status(client, db_session):
    letter_id, order = _create_sent_letter(client, db_session)
    admin = FakeAdmin()

    order = delivery_service.cancel_delivery(db_session, order.id, admin)
    assert order.status == DeliveryStatus.CANCELLED


def test_letter_status_updates_to_delivered(client, db_session, auth_headers):
    letter_id, order = _create_sent_letter(client, db_session)
    agent = _create_agent(db_session)
    admin = FakeAdmin()

    delivery_service.assign_courier(db_session, order.id, agent.id, admin)
    delivery_service.mark_picked_up(db_session, order.id, admin)
    delivery_service.mark_in_transit(db_session, order.id, admin)
    delivery_service.mark_out_for_delivery(db_session, order.id, admin)
    delivery_service.mark_deposited(db_session, order.id, admin)
    delivery_service.force_confirm_delivery(db_session, order.id, admin)

    letter = client.get(f"/api/admin/letters/{letter_id}", headers=auth_headers).json()
    assert letter["status"] == "DELIVERED"
