import os

from dotenv import load_dotenv
from openai import OpenAI


load_dotenv()

USE_MOCK_AI = os.getenv("USE_MOCK_AI", "true").lower() == "true"
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
        model="gpt-4.1-mini",
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
        raise RuntimeError("The AI model returned an empty summary.")

    return summary