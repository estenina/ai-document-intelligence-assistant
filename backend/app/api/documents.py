from pathlib import Path
from uuid import uuid4

from fastapi import APIRouter, File, HTTPException, UploadFile, status

from app.services.ai_service import summarize_document
from app.services.document_service import extract_document_text


router = APIRouter(
    prefix="/documents",
    tags=["Documents"],
)

UPLOAD_DIRECTORY = Path("uploads")
UPLOAD_DIRECTORY.mkdir(exist_ok=True)

ALLOWED_EXTENSIONS = {".pdf", ".docx", ".txt"}
MAX_FILE_SIZE = 10 * 1024 * 1024
MAX_SUMMARY_CHARACTERS = 30_000


@router.post("/upload", status_code=status.HTTP_201_CREATED)
async def upload_document(
    file: UploadFile = File(...),
) -> dict[str, str]:
    original_filename = file.filename or "unnamed-file"
    extension = Path(original_filename).suffix.lower()

    if extension not in ALLOWED_EXTENSIONS:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Only PDF, DOCX, and TXT files are supported.",
        )

    file_content = await file.read()

    if not file_content:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="The uploaded file is empty.",
        )

    if len(file_content) > MAX_FILE_SIZE:
        raise HTTPException(
            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            detail="The file must be 10 MB or smaller.",
        )

    document_id = str(uuid4())
    stored_filename = f"{document_id}{extension}"
    file_path = UPLOAD_DIRECTORY / stored_filename

    file_path.write_bytes(file_content)

    try:
        extracted_text = extract_document_text(file_path)
    except Exception as error:
        file_path.unlink(missing_ok=True)

        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=f"Unable to read the document: {error}",
        ) from error

    if not extracted_text.strip():
        file_path.unlink(missing_ok=True)

        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="No readable text was found in the document.",
        )

    return {
        "document_id": document_id,
        "original_filename": original_filename,
        "stored_filename": stored_filename,
        "message": "Document uploaded and processed successfully.",
        "text_preview": extracted_text[:500],
    }


@router.post("/{document_id}/summarize")
async def summarize_uploaded_document(
    document_id: str,
) -> dict[str, str]:
    matching_files = list(
        UPLOAD_DIRECTORY.glob(f"{document_id}.*")
    )

    if not matching_files:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Document was not found.",
        )

    if len(matching_files) > 1:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Multiple files were found for this document ID.",
        )

    file_path = matching_files[0]

    try:
        document_text = extract_document_text(file_path)
    except Exception as error:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=f"Unable to read the document: {error}",
        ) from error

    if not document_text.strip():
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="No readable text was found in the document.",
        )

    text_for_summary = document_text[:MAX_SUMMARY_CHARACTERS]

    try:
        summary = summarize_document(text_for_summary)
    except ValueError as error:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(error),
        ) from error
    except Exception as error:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=f"AI summary generation failed: {error}",
        ) from error

    return {
        "document_id": document_id,
        "stored_filename": file_path.name,
        "summary": summary,
    }