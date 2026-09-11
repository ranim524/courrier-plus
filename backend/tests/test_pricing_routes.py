from tests.conftest import make_pdf_file


def test_calculate_endpoint_returns_breakdown(client):
    response = client.post(
        "/api/pricing/calculate", json={"page_count": 10, "acknowledgment_of_receipt": True}
    )
    assert response.status_code == 200
    body = response.json()
    assert body["page_count"] == 10
    assert body["sheet_count"] == 10
    assert body["printing_mode"] == "black_and_white"
    assert body["printing_sides"] == "single"
    assert body["paper_weight_g"] == "50.000"
    assert body["envelope_weight_g"] == "10.000"
    assert body["estimated_weight_g"] == "60.000"
    assert body["weight_bracket"] == "21-100g"
    assert body["printing_cost"] == "1.500"
    assert body["paper_cost"] == "0.500"
    assert body["envelope_cost"] == "0.500"
    assert body["postal_postage"] == "1.200"
    assert body["registered_mail_fee"] == "3.000"
    assert body["acknowledgment_fee"] == "2.500"
    assert body["delivery_fee"] == "0.000"
    assert body["service_fee"] == "1.000"
    assert body["total"] == "10.200"
    assert body["currency"] == "TND"


def test_calculate_endpoint_duplex(client):
    response = client.post(
        "/api/pricing/calculate",
        json={"page_count": 10, "printing_sides": "double", "acknowledgment_of_receipt": False},
    )
    assert response.status_code == 200
    body = response.json()
    assert body["sheet_count"] == 5
    assert body["total"] == "7.450"


def test_calculate_endpoint_rejects_excessive_weight(client):
    response = client.post("/api/pricing/calculate", json={"page_count": 399, "acknowledgment_of_receipt": False})
    assert response.status_code == 422


def test_calculate_endpoint_rejects_invalid_printing_mode(client):
    response = client.post("/api/pricing/calculate", json={"page_count": 1, "printing_mode": "sepia"})
    assert response.status_code == 422


def test_preview_endpoint_counts_pages_from_uploaded_pdf(client):
    filename, filedata, content_type = make_pdf_file(page_count=19)
    response = client.post(
        "/api/pricing/preview",
        data={"acknowledgment_of_receipt": "true"},
        files={"document": (filename, filedata, content_type)},
    )
    assert response.status_code == 200
    body = response.json()
    assert body["page_count"] == 19
    assert body["estimated_weight_g"] == "105.000"
    assert body["weight_bracket"] == "101-250g"


def test_preview_endpoint_without_document_defaults_to_one_page(client):
    response = client.post("/api/pricing/preview", data={"acknowledgment_of_receipt": "false"})
    assert response.status_code == 200
    body = response.json()
    assert body["page_count"] == 1
    assert body["total"] == "5.450"


def test_preview_endpoint_ignores_client_supplied_page_count(client):
    """Even if a malicious client tries to smuggle a page_count field, there is
    no such Form parameter on this endpoint, so it is silently dropped and the
    backend still counts the real PDF pages itself."""
    filename, filedata, content_type = make_pdf_file(page_count=5)
    response = client.post(
        "/api/pricing/preview",
        data={"acknowledgment_of_receipt": "false", "page_count": "1"},
        files={"document": (filename, filedata, content_type)},
    )
    assert response.status_code == 200
    assert response.json()["page_count"] == 5


def test_preview_endpoint_ignores_client_supplied_total(client):
    """There is no total/price Form field on this endpoint either -- anything
    sent under that name is simply dropped, never used to override the
    backend-computed total."""
    filename, filedata, content_type = make_pdf_file(page_count=1)
    response = client.post(
        "/api/pricing/preview",
        data={"acknowledgment_of_receipt": "false", "total": "0.001"},
        files={"document": (filename, filedata, content_type)},
    )
    assert response.status_code == 200
    assert response.json()["total"] == "5.450"
