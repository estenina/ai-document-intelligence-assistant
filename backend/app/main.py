from fastapi import FastAPI

from app.api.documents import router as documents_router


app = FastAPI(
    title="AI Document Intelligence Assistant",
    description="Upload and analyze documents using AI.",
    version="1.0.0",
)

app.include_router(documents_router)


@app.get("/")
def home() -> dict[str, str]:
    return {
        "message": "AI Document Assistant API is running",
    }


@app.get("/health")
def health() -> dict[str, str]:
    return {
        "status": "healthy",
    }