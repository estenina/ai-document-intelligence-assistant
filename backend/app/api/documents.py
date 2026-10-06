from pathlib import Path
from uuid import uuid4

from fastapi import APIRouter, File, HTTPException, UploadFile, status

from app.models.extraction import ExtractionRequest, ExtractionResponse
from app.models.question import QuestionRequest, QuestionResponse
from app.models.search import MultiDocumentQuestionRequest, MultiDocumentQuestionResponse
from app.services import document_store
from app.services.ai_service import (
    USE_MOCK_AI,
    answer_document_question,
    extract_document_data,
    summarize_document,
)
from app.services.document_service import extract_document_text
from app.services.search_service import answer_multi_document_question


router = APIRouter(
    prefix="/documents",
    tags=["Documents"],
)

UPLOAD_DIRECTORY = Path("uploads")
UPLOAD_DIRECTORY.mkdir(exist_ok=True)

ALLOWED_EXTENSIONS = {".pdf", ".docx", ".txt"}
MAX_FILE_SIZE = 10 * 1024 * 1024
MAX_SUMMARY_CHARACTERS = 30_000
MAX_EXTRACTION_CHARACTERS = 50_000
MAX_QUESTION_CONTEXT_CHARACTERS = 50_000


def find_uploaded_document(document_id: str) -> Path:
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

    return matching_files[0]


def read_uploaded_document(file_path: Path) -> str:
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

    return document_text


@router.post(
    "/upload",
    status_code=status.HTTP_201_CREATED,
)
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

    try:
        file_path.write_bytes(file_content)
    except OSError as error:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Unable to save the uploaded document.",
        ) from error

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

    metadata = document_store.save_document_metadata(
        UPLOAD_DIRECTORY,
        document_id=document_id,
        original_filename=original_filename,
        stored_filename=stored_filename,
    )

    return {
        "document_id": document_id,
        "original_filename": original_filename,
        "stored_filename": stored_filename,
        "uploaded_at": metadata["uploaded_at"],
        "message": "Document uploaded and processed successfully.",
        "text_preview": extracted_text[:500],
    }


@router.get("")
async def list_documents() -> list[dict[str, str]]:
    all_metadata = document_store.load_all_metadata(UPLOAD_DIRECTORY)

    return sorted(
        (
            {
                "document_id": entry["document_id"],
                "original_filename": entry["original_filename"],
                "stored_filename": entry["stored_filename"],
                "uploaded_at": entry["uploaded_at"],
            }
            for entry in all_metadata.values()
            if (UPLOAD_DIRECTORY / entry["stored_filename"]).exists()
        ),
        key=lambda item: item["uploaded_at"],
        reverse=True,
    )


@router.post("/search", response_model=MultiDocumentQuestionResponse)
async def search_documents(
    request: MultiDocumentQuestionRequest,
) -> MultiDocumentQuestionResponse:
    all_metadata = document_store.load_all_metadata(UPLOAD_DIRECTORY)

    if request.document_ids:
        missing_ids = [
            document_id
            for document_id in request.document_ids
            if document_id not in all_metadata
        ]

        if missing_ids:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Document(s) not found: {', '.join(missing_ids)}",
            )

        selected_metadata = [
            all_metadata[document_id] for document_id in request.document_ids
        ]
    else:
        selected_metadata = list(all_metadata.values())

    if not selected_metadata:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No documents have been uploaded yet.",
        )

    documents: list[tuple[str, str, Path, str]] = []

    for entry in selected_metadata:
        file_path = UPLOAD_DIRECTORY / entry["stored_filename"]

        if not file_path.exists():
            continue

        document_text = read_uploaded_document(file_path)

        documents.append(
            (
                entry["document_id"],
                entry["original_filename"],
                file_path,
                document_text,
            )
        )

    if not documents:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="None of the requested documents could be read.",
        )

    try:
        result = answer_multi_document_question(
            question=request.question,
            documents=documents,
        )
    except ValueError as error:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(error),
        ) from error
    except Exception as error:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=f"AI multi-document search failed: {error}",
        ) from error

    return MultiDocumentQuestionResponse(
        question=request.question,
        documents_searched=len(documents),
        result=result,
        mock_mode=USE_MOCK_AI,
    )


@router.post("/{document_id}/summarize")
async def summarize_uploaded_document(
    document_id: str,
) -> dict[str, str]:
    file_path = find_uploaded_document(document_id)
    document_text = read_uploaded_document(file_path)

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


@router.post(
    "/{document_id}/extract",
    response_model=ExtractionResponse,
)
async def extract_uploaded_document(
    document_id: str,
    request: ExtractionRequest,
) -> ExtractionResponse:
    file_path = find_uploaded_document(document_id)
    document_text = read_uploaded_document(file_path)

    text_for_extraction = document_text[:MAX_EXTRACTION_CHARACTERS]

    try:
        extraction = extract_document_data(
            document_text=text_for_extraction,
            extraction_instructions=request.extraction_instructions,
        )
    except ValueError as error:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(error),
        ) from error
    except Exception as error:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=f"AI structured extraction failed: {error}",
        ) from error

    if len(document_text) > MAX_EXTRACTION_CHARACTERS:
        extraction.warnings.append(
            "The document was truncated before AI extraction because it "
            "exceeded the current processing limit."
        )

    return ExtractionResponse(
        document_id=document_id,
        stored_filename=file_path.name,
        extraction=extraction,
        mock_mode=USE_MOCK_AI,
    )


@router.post(
    "/{document_id}/questions",
    response_model=QuestionResponse,
)
async def ask_document_question(
    document_id: str,
    request: QuestionRequest,
) -> QuestionResponse:
    file_path = find_uploaded_document(document_id)
    document_text = read_uploaded_document(file_path)

    document_context = document_text[
        :MAX_QUESTION_CONTEXT_CHARACTERS
    ]

    try:
        result = answer_document_question(
            document_text=document_context,
            question=request.question,
        )
    except ValueError as error:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(error),
        ) from error
    except Exception as error:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=f"AI document question failed: {error}",
        ) from error

    if len(document_text) > MAX_QUESTION_CONTEXT_CHARACTERS:
        result.answer += (
            " The document exceeded the current processing limit, so only "
            "the first part of the document was analyzed."
        )

    return QuestionResponse(
        document_id=document_id,
        stored_filename=file_path.name,
        question=request.question,
        result=result,
        mock_mode=USE_MOCK_AI,
    )