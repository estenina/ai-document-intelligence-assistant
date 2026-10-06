# AI Document Intelligence Assistant

A full-stack AI-powered document analysis application built with Angular, Python, FastAPI, and the OpenAI API.

The application allows users to upload documents, automatically generate AI-powered summaries, ask questions about document content, and receive grounded answers with supporting sources.

The project demonstrates full-stack application development, REST API design, document-processing workflows, generative AI integration, prompt engineering, file validation, error handling, and an interactive Angular user interface.

## Features

- Upload and analyze documents through a web interface
- Support for PDF, DOCX, and TXT files
- File type validation
- Maximum upload size of 10 MB
- Automatic document text extraction
- AI-generated document summaries
- Ask natural-language questions about uploaded documents
- Grounded AI answers based on document content
- Supporting source citations for AI responses
- Document-based answer verification
- Loading and error states
- REST API built with FastAPI
- Interactive Swagger / OpenAPI documentation
- Angular frontend
- OpenAI API integration
- Environment-based secret configuration

## How It Works

The application follows a simple full-stack AI workflow:

```text
Angular UI
    ↓
FastAPI REST API
    ↓
Document Processing
    ↓
Text Extraction
    ↓
OpenAI API
    ↓
AI Summary / Question Answering
    ↓
Grounded Response + Supporting Sources
    ↓
Angular UI
```

Users upload a document through the Angular interface. The FastAPI backend validates and stores the document, extracts its text, and sends relevant content to the AI service.

The application can then generate a summary or answer questions about the document while returning supporting source text when available.

## Why I Built This Project

Many organizations work with large volumes of documents that require manual review, summarization, and information extraction.

This project explores how generative AI can improve document-processing workflows by helping users:

- Quickly understand document content
- Generate concise summaries
- Ask questions using natural language
- Locate important information
- Verify AI answers against source content
- Reduce repetitive manual document review

It also gave me the opportunity to combine my software engineering experience with modern generative AI technologies and build an end-to-end AI application.

## Technologies

### Frontend

- Angular
- TypeScript
- HTML
- SCSS
- Angular HttpClient
- Angular Signals

### Backend

- Python
- FastAPI
- Uvicorn
- Pydantic
- REST APIs

### Document Processing

- PDF text extraction
- Microsoft Word (DOCX) processing
- Plain-text file processing
- File validation
- Document metadata management

### AI

- OpenAI API
- Generative AI
- Prompt engineering
- Document summarization
- Document question answering
- Grounded AI responses
- Supporting source citations

### Development Tools

- Visual Studio Code
- Git
- GitHub
- Swagger / OpenAPI
- Environment variables
- pytest

## Supported File Types

| File Type | Supported |
|---|---|
| PDF | Yes |
| DOCX | Yes |
| TXT | Yes |

Maximum file size: **10 MB**

## API Endpoints

### Upload a Document

```http
POST /documents/upload
```

Uploads, validates, stores, and extracts text from a document.

### List Documents

```http
GET /documents
```

Returns uploaded document metadata.

### Search Documents

```http
POST /documents/search
```

Searches stored document content.

### Generate Summary

```http
POST /documents/{document_id}/summarize
```

Generates an AI-powered summary of the selected document.

### Extract Document Content

```http
POST /documents/{document_id}/extract
```

Extracts structured information from document content.

### Ask a Question

```http
POST /documents/{document_id}/questions
```

Example request:

```json
{
  "question": "What is the main technical risk in this project?"
}
```

The API returns an AI-generated answer together with supporting source content when the answer can be grounded in the document.

## Running the Project Locally

### 1. Clone the Repository

```bash
git clone <repository-url>
cd ai-document-intelligence-assistant
```

### 2. Configure the Backend

Navigate to the backend:

```bash
cd backend
```

Create a Python virtual environment and install the dependencies:

```bash
python -m venv venv
```

Activate the virtual environment and run:

```bash
pip install -r requirements.txt
```

Create a `.env` file based on `.env.example`:

```env
OPENAI_API_KEY=your_openai_api_key_here
```

> Never commit your real API key to GitHub.

Start the FastAPI backend:

```bash
python -m uvicorn app.main:app --reload
```

The backend runs at:

```text
http://127.0.0.1:8000
```

Swagger API documentation is available at:

```text
http://127.0.0.1:8000/docs
```

### 3. Configure the Angular Frontend

Open another terminal and navigate to:

```bash
cd frontend
```

Install dependencies:

```bash
npm install
```

Start the Angular application:

```bash
npm start
```

The frontend runs at:

```text
http://localhost:4200
```

## Application Workflow

1. Select a PDF, DOCX, or TXT document.
2. Click **Upload & Analyze**.
3. The backend validates and processes the document.
4. AI automatically generates a document summary.
5. Enter a question in the **Ask AI** section.
6. The AI analyzes the document and returns an answer.
7. Supporting source text is displayed when the answer is found in the document.

## Security

Sensitive configuration such as the OpenAI API key is stored using environment variables.

The real `.env` file is excluded from Git through `.gitignore`.

The repository contains `.env.example` only as a configuration template.

## Testing

The backend includes automated tests for document search and processing functionality.

Additional validation has been performed for:

- Supported document uploads
- Invalid file types
- File size limits
- AI summarization
- Document question answering
- Supporting source citations
- API error handling

## Project Status

**MVP completed.**

The current version includes the FastAPI backend, Angular frontend, document processing, OpenAI integration, AI summarization, document question answering, and supporting source citations.

### Future Improvements

- Cloud deployment
- Persistent cloud document storage
- Improved semantic document search
- Vector embeddings and retrieval
- Authentication and user accounts
- Multi-document question answering
- Expanded automated test coverage

## Author

**Elena Stenina**

Senior Software Engineer exploring the intersection of enterprise application development and Generative AI.
