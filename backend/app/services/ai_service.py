import os

from dotenv import load_dotenv
from openai import OpenAI

from app.models.extraction import (
    ActionItem,
    DocumentExtraction,
    ExtractedEntity,
    ExtractedField,
)
from app.models.question import (
    DocumentQuestionResult,
    QuestionCitation,
)

load_dotenv()

USE_MOCK_AI = os.getenv("USE_MOCK_AI", "true").lower() == "true"
OPENAI_MODEL = os.getenv("OPENAI_MODEL", "gpt-4.1-mini")
api_key = os.getenv("OPENAI_API_KEY")


def create_mock_summary(document_text: str) -> str:
    cleaned_text = " ".join(document_text.split())

    if not cleaned_text:
        raise ValueError("Document text cannot be empty.")

    preview = cleaned_text[:700]

    return (
        "Mock AI Summary\n\n"
        "This document was successfully uploaded and processed by the "
        "AI Document Intelligence Assistant.\n\n"
        "Document preview:\n"
        f"{preview}\n\n"
        "This summary was generated in mock mode and did not call the OpenAI API."
    )


def create_mock_extraction(
    document_text: str,
) -> DocumentExtraction:
    cleaned_text = " ".join(document_text.split())

    if not cleaned_text:
        raise ValueError("Document text cannot be empty.")

    preview = cleaned_text[:300]

    return DocumentExtraction(
        document_type="other",
        title="Mock document extraction",
        summary=(
            "This is a mock structured extraction generated without calling "
            "the OpenAI API."
        ),
        fields=[
            ExtractedField(
                name="text_preview",
                value=preview,
                source_text=preview,
                confidence=1.0,
            )
        ],
        entities=[
            ExtractedEntity(
                entity_type="other",
                value="Mock extraction",
                source_text=preview,
            )
        ],
        action_items=[
            ActionItem(
                description="Disable mock mode to run real AI extraction.",
                owner=None,
                due_date=None,
                priority="low",
            )
        ],
        warnings=[
            "Mock mode is enabled. No OpenAI API request was made."
        ],
    )


def create_mock_question_answer(
    document_text: str,
    question: str,
) -> DocumentQuestionResult:
    cleaned_text = " ".join(document_text.split())
    cleaned_question = question.strip()

    if not cleaned_text:
        raise ValueError("Document text cannot be empty.")

    if not cleaned_question:
        raise ValueError("Question cannot be empty.")

    preview = cleaned_text[:500]

    return DocumentQuestionResult(
        answer=(
            "This is a mock answer. The uploaded document was successfully "
            "found and processed. Disable mock mode to receive an AI-generated "
            "answer based on the document."
        ),
        found_in_document=True,
        citations=[
            QuestionCitation(
                source_text=preview,
            )
        ],
    )


def summarize_document(document_text: str) -> str:
    if not document_text.strip():
        raise ValueError("Document text cannot be empty.")

    if USE_MOCK_AI:
        return create_mock_summary(document_text)

    if not api_key:
        raise RuntimeError(
            "OPENAI_API_KEY is missing. Add it to the backend/.env file."
        )

    client = OpenAI(api_key=api_key)

    response = client.responses.create(
        model=OPENAI_MODEL,
        instructions=(
            "You are a professional document analysis assistant. "
            "Create a clear, accurate, concise summary. "
            "Include the main purpose, important details, and key conclusions. "
            "Do not invent information."
        ),
        input=document_text,
    )

    summary = response.output_text.strip()

    if not summary:
        raise RuntimeError(
            "The AI model returned an empty summary."
        )

    return summary


def extract_document_data(
    document_text: str,
    extraction_instructions: str | None = None,
) -> DocumentExtraction:
    if not document_text.strip():
        raise ValueError("Document text cannot be empty.")

    if USE_MOCK_AI:
        return create_mock_extraction(document_text)

    if not api_key:
        raise RuntimeError(
            "OPENAI_API_KEY is missing. Add it to the backend/.env file."
        )

    client = OpenAI(api_key=api_key)

    instructions = extraction_instructions or (
        "Extract the most important business information from this document."
    )

    response = client.responses.parse(
        model=OPENAI_MODEL,
        instructions=(
            "You are an enterprise document intelligence system. "
            "Analyze only the supplied document. "
            "Determine its document type and title. "
            "Create a concise factual summary. "
            "Extract important fields, people, organizations, dates, amounts, "
            "identifiers, and action items. "
            "Include short supporting source text whenever possible. "
            "Do not invent missing information. "
            "Use null when information is unavailable. "
            "Add warnings when the document is incomplete or unclear."
        ),
        input=(
            f"User extraction instructions:\n{instructions}\n\n"
            f"Document text:\n{document_text}"
        ),
        text_format=DocumentExtraction,
    )

    extraction = response.output_parsed

    if extraction is None:
        raise RuntimeError(
            "The AI model returned no structured extraction result."
        )

    return extraction


def answer_document_question(
    document_text: str,
    question: str,
) -> DocumentQuestionResult:
    cleaned_text = document_text.strip()
    cleaned_question = question.strip()

    if not cleaned_text:
        raise ValueError("Document text cannot be empty.")

    if not cleaned_question:
        raise ValueError("Question cannot be empty.")

    if USE_MOCK_AI:
        return create_mock_question_answer(
            document_text=cleaned_text,
            question=cleaned_question,
        )

    if not api_key:
        raise RuntimeError(
            "OPENAI_API_KEY is missing. Add it to the backend/.env file."
        )

    client = OpenAI(api_key=api_key)

    response = client.responses.parse(
        model=OPENAI_MODEL,
        instructions=(
            "You are a document question-answering assistant. "
            "Answer the user's question using only the supplied document. "
            "Do not use outside knowledge. "
            "Do not guess or invent information. "
            "If the document contains enough information to answer the "
            "question, set found_in_document to true. "
            "Include one or more short exact passages from the document in "
            "the citations list. "
            "Each citation must directly support the answer. "
            "If the document does not contain enough information, set "
            "found_in_document to false. "
            "Clearly state that the answer was not found in the document and "
            "return an empty citations list."
        ),
        input=(
            f"Question:\n{cleaned_question}\n\n"
            f"Document text:\n{cleaned_text}"
        ),
        text_format=DocumentQuestionResult,
    )

    result = response.output_parsed

    if result is None:
        raise RuntimeError(
            "The AI model returned no document question result."
        )

    return result