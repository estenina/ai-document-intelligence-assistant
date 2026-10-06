from pydantic import BaseModel, Field


class MultiDocumentQuestionRequest(BaseModel):
    question: str = Field(
        min_length=2,
        max_length=1000,
        description="A question to ask across one or more uploaded documents.",
    )
    document_ids: list[str] | None = Field(
        default=None,
        description=(
            "Restrict the search to these document IDs. "
            "Omit to search every uploaded document."
        ),
    )


class MultiDocumentCitation(BaseModel):
    document_id: str = Field(
        description="The ID of the document the supporting passage came from."
    )
    filename: str = Field(
        description="The original filename of the document the passage came from."
    )
    source_text: str = Field(
        description="A short exact passage that supports the answer."
    )


class MultiDocumentQuestionResult(BaseModel):
    answer: str = Field(
        description="A factual answer based only on the searched documents."
    )
    found_in_documents: bool = Field(
        description=(
            "True when at least one searched document contained enough "
            "information to answer the question."
        )
    )
    citations: list[MultiDocumentCitation] = Field(
        default_factory=list,
        description="Supporting passages, each tagged with its source document.",
    )


class MultiDocumentQuestionResponse(BaseModel):
    question: str
    documents_searched: int
    result: MultiDocumentQuestionResult
    mock_mode: bool
