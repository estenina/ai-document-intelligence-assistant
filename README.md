# AI Document Intelligence Assistant

An AI-assisted document-processing application built with Python and FastAPI.

The application allows users to upload documents, validate files, extract document content, and generate summaries through a REST API. The project demonstrates backend API development, document-processing workflows, file validation, error handling, and integration with generative AI services.

## Project Status

This project is currently an MVP and is under active development.

### Implemented

- FastAPI backend
- Document upload endpoint
- File type validation
- File size validation
- Support for PDF, DOCX, and TXT files
- Maximum upload size of 10 MB
- Structured API responses
- Error handling
- Interactive Swagger API documentation
- Mock summarization mode for local development
- Environment-based configuration

### In Progress

- OpenAI API integration
- Document text extraction improvements
- AI-generated document summaries
- Additional automated tests
- Angular frontend
- Deployment to a cloud platform

## Why I Built This Project

Many organizations work with large numbers of documents that must be reviewed, summarized, and categorized manually.

This project explores how generative AI can improve document-processing workflows by helping users:

- Upload business documents
- Extract useful text
- Generate concise summaries
- Identify important information
- Reduce repetitive manual review
- Build a foundation for intelligent document search

## Technologies

### Backend

- Python
- FastAPI
- Uvicorn
- Pydantic
- REST APIs

### Document Processing

- PDF documents
- Microsoft Word documents
- Plain-text files
- File validation and content extraction

### AI

- OpenAI API
- Prompt engineering
- Generative AI
- Mock AI responses for development without API usage

### Development Tools

- Visual Studio Code
- Git and GitHub
- Swagger / OpenAPI
- Environment variables

## API Endpoints

### Upload a Document

```http
POST /documents/upload
