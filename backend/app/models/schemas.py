"""Pydantic Models"""
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field
from enum import Enum


class MessageRole(str, Enum):
    USER = "user"
    ASSISTANT = "assistant"
    SYSTEM = "system"


class ChatMessage(BaseModel):
    role: MessageRole
    content: str
    image_url: Optional[str] = None


class ChatRequest(BaseModel):
    message: str
    conversation_id: Optional[str] = None
    history: List[ChatMessage] = []
    image_base64: Optional[str] = None
    use_rag: bool = True
    top_k: int = Field(default=5, ge=1, le=20)


class EvaluationScore(BaseModel):
    faithfulness: float = Field(ge=0, le=1)
    answer_relevancy: float = Field(ge=0, le=1)
    context_precision: float = Field(ge=0, le=1)
    context_recall: float = Field(ge=0, le=1)
    overall_score: float = Field(ge=0, le=1)
    latency_ms: float
    tokens_used: int


class RetrievedContext(BaseModel):
    document_id: str
    content: str
    score: float
    metadata: Dict[str, Any] = {}
    modality: str = "text"  # text | image | table


class ChatResponse(BaseModel):
    response: str
    conversation_id: str
    retrieved_contexts: List[RetrievedContext]
    evaluation: EvaluationScore
    model_used: str
    cached: bool = False


class IngestRequest(BaseModel):
    source_type: str  # url | text
    content: str
    metadata: Dict[str, Any] = {}


class IngestResponse(BaseModel):
    document_id: str
    chunks_created: int
    modalities_detected: List[str]
    status: str


class HealthResponse(BaseModel):
    status: str
    version: str
    services: Dict[str, str]
