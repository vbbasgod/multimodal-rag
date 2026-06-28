"""Vector Store Initialization (ChromaDB) - Local Embedded Mode"""

import logging

import chromadb
from app.core.config import settings
from chromadb.config import Settings as ChromaSettings

logger = logging.getLogger(__name__)

_chroma_client = None
_collection = None


async def init_vector_store():
    global _chroma_client, _collection
    try:
        # Use local persistent storage instead of remote server
        _chroma_client = chromadb.PersistentClient(
            path="./chroma_data",
            settings=ChromaSettings(anonymized_telemetry=False),
        )
        _collection = _chroma_client.get_or_create_collection(
            name=settings.CHROMA_COLLECTION,
            metadata={"hnsw:space": "cosine"},
        )
        logger.info(
            f"Connected to ChromaDB locally. Collection: {settings.CHROMA_COLLECTION}"
        )
    except Exception as e:
        logger.error(f"Failed to initialize ChromaDB: {e}")
        raise


def get_collection():
    if _collection is None:
        raise RuntimeError("Vector store not initialized")
    return _collection


def get_client():
    if _chroma_client is None:
        raise RuntimeError("ChromaDB client not initialized")
    return _chroma_client
