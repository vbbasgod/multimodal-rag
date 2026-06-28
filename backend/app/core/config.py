"""Application Configuration"""

from typing import List

from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    # App
    APP_NAME: str = "Multimodal RAG Chatbot"
    DEBUG: bool = False
    ALLOWED_ORIGINS: List[str] = ["http://localhost:3000", "http://localhost:80"]

    # LLM
    OPENAI_API_KEY: str = ""
    GROQ_API_KEY: str = ""
    OPENAI_MODEL: str = "gpt-4o"
    GROQ_MODEL: str = "gemma-3n-e4b-it"
    GROQ_BASE_URL: str = "https://api.groq.ai/v1"
    # Embeddings
    EMBEDDING_PROVIDER: str = "openai"  # 'openai' or 'local' or 'nomic'
    EMBEDDING_MODEL: str = "text-embedding-3-small"
    # When using local provider, a sentence-transformers model like 'all-MiniLM-L6-v2' is recommended

    # Vector DB (ChromaDB)
    CHROMA_HOST: str = "chromadb"
    CHROMA_PORT: int = 8000
    CHROMA_COLLECTION: str = "multimodal_rag"

    # Redis Cache
    REDIS_URL: str = "redis://redis:6379"
    CACHE_TTL: int = 3600

    # RAG
    TOP_K_RETRIEVAL: int = 5
    CHUNK_SIZE: int = 512
    CHUNK_OVERLAP: int = 50
    MAX_TOKENS: int = 2048
    TEMPERATURE: float = 0.1

    # Evaluation
    RAGAS_ENABLED: bool = True

    # Storage
    UPLOAD_DIR: str = "/app/uploads"
    MAX_FILE_SIZE_MB: int = 50

    class Config:
        env_file = ".env"
        case_sensitive = True


settings = Settings()
