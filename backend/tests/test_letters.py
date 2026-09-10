from tests.conftest import make_pdf_file, sample_letter_form


def test_create_letter_with_message_succeeds(client):
    response = client.post("/api/letters", data=sample_letter_form())
    assert response.status_code == 201
    body = response.json()
    assert body["status"] == "DRAFT"
    assert body["reference"] is None
    assert body["content_type"] == "TEXT_MESSAGE"
    # A text message is priced as a single-page-equivalent letter.
    assert body["page_count"] == 1
    assert body["total_amount"] == 3.75


def test_create_letter_with_pdf_succeeds(client):
    form = sample_letter_form()
    form.pop("message")
    filename, filedata, content_type = make_pdf_file(page_count=1)
    response = client.post("/api/letters", data=form, files={"document": (filename, filedata, content_type)})
    assert response.status_code == 201
    body = response.json()
    assert body["content_type"] == "PDF_UPLOAD"
    assert body["document"]["sha256"]
    assert body["page_count"] == 1
    assert body["total_amount"] == 3.75


def test_create_letter_price_reflects_pdf_page_count(client):
    form = sample_letter_form()
    form.pop("message")
    filename, filedata, content_type = make_pdf_file(page_count=5)
    response = client.post("/api/letters", data=form, files={"document": (filename, filedata, content_type)})
    assert response.status_code == 201
    body = response.json()
    assert body["page_count"] == 5
    assert body["estimated_weight_g"] == 25
    assert body["weight_bracket"] == "20-100g"
    assert body["total_amount"] == 4.2


def test_create_letter_with_acknowledgment_of_receipt_adds_fee(client):
    form = sample_letter_form()
    form.pop("message")
    form["acknowledgment_of_receipt"] = "true"
    filename, filedata, content_type = make_pdf_file(page_count=20)
    response = client.post("/api/letters", data=form, files={"document": (filename, filedata, content_type)})
    assert response.status_code == 201
    body = response.json()
    assert body["acknowledgment_of_receipt"] is True
    assert body["acknowledgment_fee"] == 2.5
    assert body["total_amount"] == 6.7


def test_create_letter_rejects_pdf_over_400_pages(client):
    form = sample_letter_form()
    form.pop("message")
    filename, filedata, content_type = make_pdf_file(page_count=401)
    response = client.post("/api/letters", data=form, files={"document": (filename, filedata, content_type)})
    assert response.status_code == 422
    assert "400 pages" in response.json()["detail"]


def test_create_letter_ignores_client_supplied_price_fields(client):
    """The frontend can never dictate the price -- there is no price/total_amount
    Form field on the endpoint, so anything sent under those names is simply
    ignored, and the backend-computed total_amount always wins."""
    form = sample_letter_form()
    form.pop("message")
    form["total_amount"] = "0.001"
    form["price"] = "0.001"
    filename, filedata, content_type = make_pdf_file(page_count=1)
    response = client.post("/api/letters", data=form, files={"document": (filename, filedata, content_type)})
    assert response.status_code == 201
    assert response.json()["total_amount"] == 3.75


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
