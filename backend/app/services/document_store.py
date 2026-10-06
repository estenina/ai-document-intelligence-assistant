import json
from datetime import datetime, timezone
from pathlib import Path
from typing import TypedDict


METADATA_FILENAME = "_metadata.json"


class DocumentMetadata(TypedDict):
    document_id: str
    original_filename: str
    stored_filename: str
    uploaded_at: str


def _metadata_path(upload_directory: Path) -> Path:
    return upload_directory / METADATA_FILENAME


def load_all_metadata(upload_directory: Path) -> dict[str, DocumentMetadata]:
    path = _metadata_path(upload_directory)

    if not path.exists():
        return {}

    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError):
        return {}


def _write_all_metadata(
    upload_directory: Path, all_metadata: dict[str, DocumentMetadata]
) -> None:
    _metadata_path(upload_directory).write_text(
        json.dumps(all_metadata, indent=2),
        encoding="utf-8",
    )


def save_document_metadata(
    upload_directory: Path,
    document_id: str,
    original_filename: str,
    stored_filename: str,
) -> DocumentMetadata:
    all_metadata = load_all_metadata(upload_directory)

    entry: DocumentMetadata = {
        "document_id": document_id,
        "original_filename": original_filename,
        "stored_filename": stored_filename,
        "uploaded_at": datetime.now(timezone.utc).isoformat(),
    }

    all_metadata[document_id] = entry
    _write_all_metadata(upload_directory, all_metadata)

    return entry


def get_document_metadata(
    upload_directory: Path, document_id: str
) -> DocumentMetadata | None:
    return load_all_metadata(upload_directory).get(document_id)


def delete_document_metadata(upload_directory: Path, document_id: str) -> None:
    all_metadata = load_all_metadata(upload_directory)

    if document_id in all_metadata:
        del all_metadata[document_id]
        _write_all_metadata(upload_directory, all_metadata)
