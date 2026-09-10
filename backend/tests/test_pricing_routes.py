from tests.conftest import make_pdf_file


def test_calculate_endpoint_returns_breakdown(client):
    response = client.post("/api/pricing/calculate", json={"page_count": 20, "acknowledgment_of_receipt": True})
    assert response.status_code == 200
    body = response.json()
    assert body["page_count"] == 20
    assert body["estimated_weight_g"] == 100
    assert body["weight_bracket"] == "20-100g"
    assert body["base_postage"] == "1.200"
    assert body["registered_fee"] == "3.000"
    assert body["acknowledgment_fee"] == "2.500"
    assert body["total"] == "6.700"
    assert body["currency"] == "TND"


def test_calculate_endpoint_rejects_over_400_pages(client):
    response = client.post("/api/pricing/calculate", json={"page_count": 401, "acknowledgment_of_receipt": False})
    assert response.status_code == 422


def test_preview_endpoint_counts_pages_from_uploaded_pdf(client):
    filename, filedata, content_type = make_pdf_file(page_count=21)
    response = client.post(
        "/api/pricing/preview",
        data={"acknowledgment_of_receipt": "true"},
        files={"document": (filename, filedata, content_type)},
    )
    assert response.status_code == 200
    body = response.json()
    assert body["page_count"] == 21
    assert body["estimated_weight_g"] == 105
    assert body["weight_bracket"] == "100-250g"
    assert body["total"] == "7.000"


def test_preview_endpoint_without_document_defaults_to_one_page(client):
    response = client.post("/api/pricing/preview", data={"acknowledgment_of_receipt": "false"})
    assert response.status_code == 200
    body = response.json()
    assert body["page_count"] == 1
    assert body["total"] == "3.750"


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
