"""Document Ingestion Routes"""
import logging
from fastapi import APIRouter, UploadFile, File, HTTPException, Form
from typing import Optional
import json

from app.models.schemas import IngestResponse
from app.services.document_processor import DocumentProcessor
from app.services.rag_retriever import RAGRetriever

logger = logging.getLogger(__name__)
router = APIRouter()

doc_processor = DocumentProcessor()
rag_retriever = RAGRetriever()

ALLOWED_TYPES = {
    "application/pdf": "pdf",
    "image/jpeg": "image",
    "image/png": "image",
    "image/webp": "image",
    "text/plain": "text",
}


@router.post("/ingest/file", response_model=IngestResponse)
async def ingest_file(
    file: UploadFile = File(...),
    metadata: Optional[str] = Form(default="{}"),
):
    """Upload and process PDF, image, or text file"""
    content_type = file.content_type
    if content_type not in ALLOWED_TYPES:
        raise HTTPException(
            status_code=400,
            detail=f"Unsupported file type: {content_type}. Supported: {list(ALLOWED_TYPES.keys())}",
        )

    meta = json.loads(metadata) if metadata else {}
    file_bytes = await file.read()
    file_type = ALLOWED_TYPES[content_type]

    # Process based on type
    if file_type == "pdf":
        chunks = await doc_processor.process_pdf(file_bytes, file.filename)
    elif file_type == "image":
        chunks = await doc_processor.process_image(file_bytes, file.filename)
    else:
        text = file_bytes.decode("utf-8", errors="ignore")
        chunks = await doc_processor.process_text(text, {**meta, "source": file.filename})

    # Store in vector DB
    count = await rag_retriever.add_documents(chunks)
    modalities = list(set(c.get("modality", "text") for c in chunks))

    return IngestResponse(
        document_id=chunks[0]["id"] if chunks else "none",
        chunks_created=count,
        modalities_detected=modalities,
        status="success",
    )


@router.post("/ingest/text", response_model=IngestResponse)
async def ingest_text(payload: dict):
    """Ingest raw text content"""
    text = payload.get("content", "")
    metadata = payload.get("metadata", {})

    if not text:
        raise HTTPException(status_code=400, detail="Content is required")

    chunks = await doc_processor.process_text(text, metadata)
    count = await rag_retriever.add_documents(chunks)

    return IngestResponse(
        document_id=chunks[0]["id"] if chunks else "none",
        chunks_created=count,
        modalities_detected=["text"],
        status="success",
    )
