from fastapi.testclient import TestClient

from app.api.documents import UPLOAD_DIRECTORY
from app.main import app
from app.services import document_store


client = TestClient(app)


def _upload_txt(filename: str, content: bytes) -> str:
    response = client.post(
        "/documents/upload",
        files={"file": (filename, content, "text/plain")},
    )
    assert response.status_code == 201

    return response.json()["document_id"]


def _cleanup(document_id: str) -> None:
    metadata = document_store.get_document_metadata(UPLOAD_DIRECTORY, document_id)

    if metadata:
        (UPLOAD_DIRECTORY / metadata["stored_filename"]).unlink(missing_ok=True)

    document_store.delete_document_metadata(UPLOAD_DIRECTORY, document_id)


def test_search_across_multiple_documents() -> None:
    invoice_id = _upload_txt(
        "invoice.txt",
        b"Invoice Number: INV-3001\nVendor: Acme Corp\nTotal Amount: $500",
    )
    contract_id = _upload_txt(
        "contract.txt",
        b"This contract is between Acme Corp and Globex Inc, effective January 2026.",
    )

    try:
        response = client.post(
            "/documents/search",
            json={"question": "Which vendor is mentioned in the invoice?"},
        )

        assert response.status_code == 200

        data = response.json()

        assert data["mock_mode"] is True
        assert data["documents_searched"] == 2
        assert data["result"]["found_in_documents"] is True
        assert len(data["result"]["citations"]) > 0
        assert {citation["document_id"] for citation in data["result"]["citations"]} <= {
            invoice_id,
            contract_id,
        }
    finally:
        _cleanup(invoice_id)
        _cleanup(contract_id)


def test_search_restricted_to_specific_document() -> None:
    invoice_id = _upload_txt(
        "invoice-only.txt",
        b"Invoice Number: INV-4002\nTotal Amount: $75",
    )

    try:
        response = client.post(
            "/documents/search",
            json={
                "question": "What is the total amount?",
                "document_ids": [invoice_id],
            },
        )

        assert response.status_code == 200

        data = response.json()

        assert data["documents_searched"] == 1
    finally:
        _cleanup(invoice_id)


def test_search_with_unknown_document_id() -> None:
    response = client.post(
        "/documents/search",
        json={"question": "test", "document_ids": ["nonexistent-id"]},
    )

    assert response.status_code == 404


def test_list_documents_includes_uploaded_file() -> None:
    document_id = _upload_txt("sample.txt", b"Sample content for listing.")

    try:
        response = client.get("/documents")

        assert response.status_code == 200

        data = response.json()

        assert any(item["document_id"] == document_id for item in data)
    finally:
        _cleanup(document_id)
