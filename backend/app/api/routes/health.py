"""Health Check Routes"""
from fastapi import APIRouter
from app.models.schemas import HealthResponse
from app.core.database import get_client
from app.core.config import settings

router = APIRouter()


@router.get("/health", response_model=HealthResponse)
async def health_check():
    services = {}

    # Check ChromaDB
    try:
        client = get_client()
        client.heartbeat()
        services["chromadb"] = "healthy"
    except Exception:
        services["chromadb"] = "unhealthy"

    services["api"] = "healthy"

    return HealthResponse(
        status="healthy" if all(v == "healthy" for v in services.values()) else "degraded",
        version="1.0.0",
        services=services,
    )


@router.get("/metrics")
async def get_metrics():
    """Prometheus-style metrics endpoint"""
    try:
        client = get_client()
        collection = client.get_collection(settings.CHROMA_COLLECTION)
        doc_count = collection.count()
    except Exception:
        doc_count = 0

    return {
        "documents_indexed": doc_count,
        "collection": settings.CHROMA_COLLECTION,
        "embedding_model": settings.EMBEDDING_MODEL,
        "llm_model": settings.OPENAI_MODEL,
    }
