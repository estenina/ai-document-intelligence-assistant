import json
import math
import re
from dataclasses import dataclass
from pathlib import Path

from openai import OpenAI

from app.models.search import MultiDocumentCitation, MultiDocumentQuestionResult
from app.services import ai_service


CHUNK_SIZE = 1200
CHUNK_OVERLAP = 150
TOP_K_CHUNKS = 6
MAX_SEARCH_CONTEXT_CHARACTERS = 20_000
EMBEDDING_MODEL = "text-embedding-3-small"


@dataclass
class DocumentChunk:
    document_id: str
    filename: str
    text: str


def chunk_text(
    text: str,
    chunk_size: int = CHUNK_SIZE,
    overlap: int = CHUNK_OVERLAP,
) -> list[str]:
    cleaned = " ".join(text.split())

    if not cleaned:
        return []

    if len(cleaned) <= chunk_size:
        return [cleaned]

    chunks: list[str] = []
    start = 0

    while start < len(cleaned):
        end = min(start + chunk_size, len(cleaned))
        chunks.append(cleaned[start:end])

        if end == len(cleaned):
            break

        start = end - overlap

    return chunks


def _build_chunks(
    document_id: str, filename: str, text: str
) -> list[DocumentChunk]:
    return [
        DocumentChunk(document_id=document_id, filename=filename, text=chunk)
        for chunk in chunk_text(text)
    ]


_WORD_PATTERN = re.compile(r"[a-z0-9]+")


def _keyword_overlap_score(question: str, chunk_text_value: str) -> int:
    question_words = set(_WORD_PATTERN.findall(question.lower()))

    if not question_words:
        return 0

    chunk_words = _WORD_PATTERN.findall(chunk_text_value.lower())

    return sum(1 for word in chunk_words if word in question_words)


def _rank_chunks_by_keywords(
    question: str, chunks: list[DocumentChunk]
) -> list[DocumentChunk]:
    scored = [(chunk, _keyword_overlap_score(question, chunk.text)) for chunk in chunks]
    scored.sort(key=lambda pair: pair[1], reverse=True)

    ranked = [chunk for chunk, score in scored if score > 0]

    return ranked if ranked else [chunk for chunk, _ in scored]


def _cosine_similarity(a: list[float], b: list[float]) -> float:
    dot = sum(x * y for x, y in zip(a, b))
    norm_a = math.sqrt(sum(x * x for x in a))
    norm_b = math.sqrt(sum(y * y for y in b))

    if norm_a == 0 or norm_b == 0:
        return 0.0

    return dot / (norm_a * norm_b)


def _embedding_cache_path(file_path: Path) -> Path:
    return file_path.with_name(file_path.name + ".embeddings.json")


def _load_cached_embeddings(file_path: Path) -> dict | None:
    cache_path = _embedding_cache_path(file_path)

    if not cache_path.exists():
        return None

    try:
        cached = json.loads(cache_path.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError):
        return None

    if cached.get("source_mtime") != file_path.stat().st_mtime:
        return None

    return cached


def _save_cached_embeddings(
    file_path: Path, chunks: list[str], embeddings: list[list[float]]
) -> None:
    _embedding_cache_path(file_path).write_text(
        json.dumps(
            {
                "source_mtime": file_path.stat().st_mtime,
                "chunks": chunks,
                "embeddings": embeddings,
            }
        ),
        encoding="utf-8",
    )


def _get_chunk_embeddings(
    client: OpenAI, file_path: Path, chunks: list[str]
) -> list[list[float]]:
    if not chunks:
        return []

    cached = _load_cached_embeddings(file_path)

    if cached and cached.get("chunks") == chunks:
        return cached["embeddings"]

    response = client.embeddings.create(model=EMBEDDING_MODEL, input=chunks)
    embeddings = [item.embedding for item in response.data]

    _save_cached_embeddings(file_path, chunks, embeddings)

    return embeddings


def _rank_chunks_by_embedding(
    client: OpenAI,
    question: str,
    documents: list[tuple[str, str, Path, str]],
) -> list[DocumentChunk]:
    all_chunks: list[DocumentChunk] = []
    all_embeddings: list[list[float]] = []

    for document_id, filename, file_path, text in documents:
        chunks = chunk_text(text)

        if not chunks:
            continue

        embeddings = _get_chunk_embeddings(client, file_path, chunks)

        for chunk, embedding in zip(chunks, embeddings):
            all_chunks.append(
                DocumentChunk(document_id=document_id, filename=filename, text=chunk)
            )
            all_embeddings.append(embedding)

    if not all_chunks:
        return []

    question_embedding = (
        client.embeddings.create(model=EMBEDDING_MODEL, input=[question])
        .data[0]
        .embedding
    )

    scored = [
        (chunk, _cosine_similarity(question_embedding, embedding))
        for chunk, embedding in zip(all_chunks, all_embeddings)
    ]

    scored.sort(key=lambda pair: pair[1], reverse=True)

    return [chunk for chunk, _score in scored]


def _build_context(chunks: list[DocumentChunk]) -> str:
    context_parts: list[str] = []
    context_length = 0

    for index, chunk in enumerate(chunks):
        header = (
            f"[Source {index + 1} | document_id={chunk.document_id} "
            f"| filename={chunk.filename}]"
        )
        piece = f"{header}\n{chunk.text}"

        if context_length + len(piece) > MAX_SEARCH_CONTEXT_CHARACTERS:
            break

        context_parts.append(piece)
        context_length += len(piece)

    return "\n\n".join(context_parts)


def answer_multi_document_question(
    question: str,
    documents: list[tuple[str, str, Path, str]],
) -> MultiDocumentQuestionResult:
    """documents is a list of (document_id, filename, file_path, document_text)."""
    cleaned_question = question.strip()

    if not cleaned_question:
        raise ValueError("Question cannot be empty.")

    if not documents:
        raise ValueError("No documents are available to search.")

    if ai_service.USE_MOCK_AI:
        all_chunks = [
            chunk
            for document_id, filename, _file_path, text in documents
            for chunk in _build_chunks(document_id, filename, text)
        ]
        top_chunks = _rank_chunks_by_keywords(cleaned_question, all_chunks)[:TOP_K_CHUNKS]

        return MultiDocumentQuestionResult(
            answer=(
                "This is a mock multi-document answer. The question was matched "
                f"against {len(documents)} document(s) using keyword search. "
                "Disable mock mode to receive an AI-generated cross-document answer."
            ),
            found_in_documents=len(top_chunks) > 0,
            citations=[
                MultiDocumentCitation(
                    document_id=chunk.document_id,
                    filename=chunk.filename,
                    source_text=chunk.text[:300],
                )
                for chunk in top_chunks
            ],
        )

    if not ai_service.api_key:
        raise RuntimeError(
            "OPENAI_API_KEY is missing. Add it to the backend/.env file."
        )

    client = OpenAI(api_key=ai_service.api_key)

    top_chunks = _rank_chunks_by_embedding(client, cleaned_question, documents)[:TOP_K_CHUNKS]
    context = _build_context(top_chunks)

    response = client.responses.parse(
        model=ai_service.OPENAI_MODEL,
        instructions=(
            "You are a multi-document question-answering assistant. "
            "Answer the user's question using only the supplied document excerpts. "
            "Each excerpt is labeled with its document_id and filename. "
            "Do not use outside knowledge. Do not guess or invent information. "
            "If the excerpts contain enough information to answer, set "
            "found_in_documents to true and cite the supporting excerpts using "
            "their exact document_id and filename. "
            "If not, set found_in_documents to false, state that the answer was "
            "not found in the searched documents, and return an empty citations list."
        ),
        input=(
            f"Question:\n{cleaned_question}\n\n"
            f"Document excerpts:\n{context}"
        ),
        text_format=MultiDocumentQuestionResult,
    )

    result = response.output_parsed

    if result is None:
        raise RuntimeError("The AI model returned no multi-document result.")

    return result
