from pydantic import BaseModel, Field


class QuestionRequest(BaseModel):
    question: str = Field(
        min_length=2,
        max_length=1000,
        description="A question about the uploaded document.",
    )


class QuestionCitation(BaseModel):
    source_text: str = Field(
        description=(
            "A short exact passage from the document that supports the answer."
        )
    )


class DocumentQuestionResult(BaseModel):
    answer: str = Field(
        description="A factual answer based only on the uploaded document."
    )
    found_in_document: bool = Field(
        description=(
            "True when the document contains enough information to answer "
            "the question."
        )
    )
    citations: list[QuestionCitation] = Field(
        default_factory=list,
        description="Supporting passages copied from the document.",
    )


class QuestionResponse(BaseModel):
    document_id: str
    stored_filename: str
    question: str
    result: DocumentQuestionResult
    mock_mode: bool