def test_admin_login_success(client, db_session):
    from app.services.admin_service import create_admin_if_not_exists

    create_admin_if_not_exists(db_session, "boss@courrierplus.tn", "StrongPass123!")
    db_session.commit()

    response = client.post("/api/admin/login", json={"email": "boss@courrierplus.tn", "password": "StrongPass123!"})
    assert response.status_code == 200
    assert response.json()["access_token"]


def test_admin_login_wrong_password_fails(client, db_session):
    from app.services.admin_service import create_admin_if_not_exists

    create_admin_if_not_exists(db_session, "boss2@courrierplus.tn", "StrongPass123!")
    db_session.commit()

    response = client.post("/api/admin/login", json={"email": "boss2@courrierplus.tn", "password": "WrongPassword"})
    assert response.status_code == 401


def test_admin_login_unknown_email_fails(client):
    response = client.post("/api/admin/login", json={"email": "ghost@courrierplus.tn", "password": "whatever"})
    assert response.status_code == 401


def test_dashboard_requires_authentication(client):
    response = client.get("/api/admin/dashboard")
    assert response.status_code == 401


def test_letters_list_requires_authentication(client):
    response = client.get("/api/admin/letters")
    assert response.status_code == 401


def test_dashboard_accessible_with_token(client, auth_headers):
    response = client.get("/api/admin/dashboard", headers=auth_headers)
    assert response.status_code == 200
    assert "total_letters" in response.json()


def test_viewing_letter_records_admin_viewed_event(client, auth_headers):
    from tests.conftest import sample_letter_form

    letter_id = client.post("/api/letters", data=sample_letter_form()).json()["id"]
    client.get(f"/api/admin/letters/{letter_id}", headers=auth_headers)

    events = client.get(f"/api/admin/letters/{letter_id}/events", headers=auth_headers).json()
    assert any(e["event_type"] == "ADMIN_VIEWED_LETTER" for e in events)


def test_invalid_token_rejected(client):
    response = client.get("/api/admin/dashboard", headers={"Authorization": "Bearer not-a-real-token"})
    assert response.status_code == 401


def test_change_password_allows_login_with_new_password(client, db_session):
    from app.services.admin_service import change_password, create_admin_if_not_exists

    create_admin_if_not_exists(db_session, "rotate@courrierplus.tn", "OldPassword123!")
    db_session.commit()

    change_password(db_session, "rotate@courrierplus.tn", "NewPassword456!")
    db_session.commit()

    old_login = client.post(
        "/api/admin/login", json={"email": "rotate@courrierplus.tn", "password": "OldPassword123!"}
    )
    assert old_login.status_code == 401

    new_login = client.post(
        "/api/admin/login", json={"email": "rotate@courrierplus.tn", "password": "NewPassword456!"}
    )
    assert new_login.status_code == 200


def test_change_password_rejects_unknown_email(db_session):
    from app.core.exceptions import NotFoundError
    from app.services.admin_service import change_password

    try:
        change_password(db_session, "ghost@courrierplus.tn", "SomePassword123!")
        assert False, "expected NotFoundError"
    except NotFoundError:
        pass


def test_change_password_rejects_short_password(client, db_session):
    from app.core.exceptions import ValidationAppError
    from app.services.admin_service import change_password, create_admin_if_not_exists

    create_admin_if_not_exists(db_session, "shortpw@courrierplus.tn", "OldPassword123!")
    db_session.commit()

    try:
        change_password(db_session, "shortpw@courrierplus.tn", "short")
        assert False, "expected ValidationAppError"
    except ValidationAppError:
        pass
