from tests.conftest import make_pdf_file, sample_letter_form


def test_create_letter_with_message_succeeds(client):
    response = client.post("/api/letters", data=sample_letter_form())
    assert response.status_code == 201
    body = response.json()
    assert body["status"] == "DRAFT"
    assert body["reference"] is None
    assert body["content_type"] == "TEXT_MESSAGE"


def test_create_letter_with_pdf_succeeds(client):
    form = sample_letter_form()
    form.pop("message")
    filename, filedata, content_type = make_pdf_file()
    response = client.post("/api/letters", data=form, files={"document": (filename, filedata, content_type)})
    assert response.status_code == 201
    body = response.json()
    assert body["content_type"] == "PDF_UPLOAD"
    assert body["document"]["sha256"]


def test_create_letter_missing_required_field_fails(client):
    form = sample_letter_form()
    del form["subject"]
    response = client.post("/api/letters", data=form)
    assert response.status_code == 422


def test_create_letter_invalid_email_fails(client):
    form = sample_letter_form()
    form["sender_email"] = "not-an-email"
    response = client.post("/api/letters", data=form)
    assert response.status_code == 422


def test_create_letter_without_message_or_document_fails(client):
    form = sample_letter_form()
    del form["message"]
    response = client.post("/api/letters", data=form)
    assert response.status_code == 422


def test_create_letter_with_both_message_and_document_fails(client):
    form = sample_letter_form()
    filename, filedata, content_type = make_pdf_file()
    response = client.post("/api/letters", data=form, files={"document": (filename, filedata, content_type)})
    assert response.status_code == 422


def test_create_letter_invalid_pdf_content_fails(client):
    form = sample_letter_form()
    form.pop("message")
    response = client.post(
        "/api/letters",
        data=form,
        files={"document": ("document.pdf", b"not a real pdf", "application/pdf")},
    )
    assert response.status_code == 422


def test_create_letter_oversized_file_fails(client):
    from app.core.config import get_settings

    settings = get_settings()
    form = sample_letter_form()
    form.pop("message")
    oversized = b"%PDF-1.4\n" + b"0" * (settings.max_upload_size_bytes + 1)
    response = client.post(
        "/api/letters",
        data=form,
        files={"document": ("document.pdf", oversized, "application/pdf")},
    )
    assert response.status_code == 422


def test_create_letter_wrong_mime_type_fails(client):
    form = sample_letter_form()
    form.pop("message")
    response = client.post(
        "/api/letters",
        data=form,
        files={"document": ("document.pdf", b"%PDF-1.4\nsome content", "text/plain")},
    )
    assert response.status_code == 422
