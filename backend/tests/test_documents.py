from pathlib import Path

from fastapi.testclient import TestClient

from app.main import app
from app.api.documents import UPLOAD_DIRECTORY


client = TestClient(app)


def test_upload_txt_document() -> None:
    response = client.post(
        "/documents/upload",
        files={
            "file": (
                "sample.txt",
                b"Invoice Number: INV-1001\nTotal Amount: $2,000",
                "text/plain",
            )
        },
    )

    assert response.status_code == 201

    response_data = response.json()

    assert "document_id" in response_data
    assert response_data["original_filename"] == "sample.txt"
    assert response_data["stored_filename"].endswith(".txt")
    assert response_data["message"] == (
        "Document uploaded and processed successfully."
    )

    stored_file = UPLOAD_DIRECTORY / response_data["stored_filename"]
    stored_file.unlink(missing_ok=True)


def test_upload_unsupported_file() -> None:
    response = client.post(
        "/documents/upload",
        files={
            "file": (
                "sample.csv",
                b"name,value\ninvoice,1001",
                "text/csv",
            )
        },
    )

    assert response.status_code == 400
    assert response.json()["detail"] == (
        "Only PDF, DOCX, and TXT files are supported."
    )


def test_extract_unknown_document() -> None:
    response = client.post(
        "/documents/not-a-real-document/extract",
        json={
            "extraction_instructions": (
                "Extract important information."
            )
        },
    )

    assert response.status_code == 404
    assert response.json()["detail"] == "Document was not found."


def test_mock_document_extraction() -> None:
    document_id = "test-extraction-document"
    file_path = UPLOAD_DIRECTORY / f"{document_id}.txt"

    file_path.write_text(
        (
            "Invoice Number: INV-2026-1001\n"
            "Due Date: August 15, 2026\n"
            "Total Amount: $2,000"
        ),
        encoding="utf-8",
    )

    try:
        response = client.post(
            f"/documents/{document_id}/extract",
            json={
                "extraction_instructions": (
                    "Extract invoice details."
                )
            },
        )

        assert response.status_code == 200

        response_data = response.json()

        assert response_data["document_id"] == document_id
        assert response_data["mock_mode"] is True
        assert "extraction" in response_data
        assert response_data["extraction"]["document_type"] == "other"
        assert len(response_data["extraction"]["fields"]) > 0
        assert len(response_data["extraction"]["warnings"]) > 0
    finally:
        file_path.unlink(missing_ok=True)