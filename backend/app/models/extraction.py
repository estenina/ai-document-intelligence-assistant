from typing import Literal

from pydantic import BaseModel, Field


DocumentType = Literal[
    "invoice",
    "contract",
    "resume",
    "insurance_policy",
    "receipt",
    "report",
    "letter",
    "other",
]


class ExtractedField(BaseModel):
    name: str = Field(
        description="Normalized field name, such as invoice_number or due_date."
    )
    value: str | int | float | bool | None = Field(
        description="The extracted value, or null when unavailable."
    )
    source_text: str | None = Field(
        description="A short exact passage supporting the extracted value."
    )
    confidence: float = Field(
        ge=0,
        le=1,
        description="Confidence score between 0 and 1.",
    )


class ExtractedEntity(BaseModel):
    entity_type: Literal[
        "person",
        "organization",
        "date",
        "amount",
        "location",
        "identifier",
        "other",
    ]
    value: str
    source_text: str | None


class ActionItem(BaseModel):
    description: str
    owner: str | None
    due_date: str | None
    priority: Literal["low", "medium", "high"]


class DocumentExtraction(BaseModel):
    document_type: DocumentType
    title: str | None
    summary: str
    fields: list[ExtractedField]
    entities: list[ExtractedEntity]
    action_items: list[ActionItem]
    warnings: list[str]


class ExtractionRequest(BaseModel):
    extraction_instructions: str | None = Field(
        default=None,
        max_length=2000,
        description="Optional instructions describing what information to extract.",
    )


class ExtractionResponse(BaseModel):
    document_id: str
    stored_filename: str
    extraction: DocumentExtraction
    mock_mode: bool