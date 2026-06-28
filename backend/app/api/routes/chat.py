"""Chat API Routes"""

import logging
import uuid

from app.models.schemas import ChatRequest, ChatResponse
from app.services.evaluation_service import EvaluationService
from app.services.llm_service import LLMService
from app.services.rag_retriever import RAGRetriever
from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import StreamingResponse

logger = logging.getLogger(__name__)
router = APIRouter()

# Service singletons (in prod, use DI container)
rag_retriever = RAGRetriever()
llm_service = LLMService()
eval_service = EvaluationService()


@router.post("/chat", response_model=ChatResponse)
async def chat(request: ChatRequest):
    """
    Main chat endpoint with RAG retrieval and evaluation
    """
    conversation_id = request.conversation_id or str(uuid.uuid4())

    try:
        # Retrieve relevant context
        contexts, raw_texts = [], []
        if request.use_rag:
            contexts, raw_texts = await rag_retriever.retrieve(
                query=request.message,
                top_k=request.top_k,
            )

        # Generate response
        answer, tokens_used, start_time = await llm_service.generate(
            question=request.message,
            contexts=raw_texts,
            history=request.history,
            image_base64=request.image_base64,
        )

        # Evaluate response
        evaluation = await eval_service.evaluate(
            question=request.message,
            answer=answer,
            contexts=raw_texts,
            start_time=start_time,
            tokens_used=tokens_used,
        )

        model_settings = __import__("app.core.config", fromlist=["settings"]).settings
        model_used = (
            f"groq/{model_settings.GROQ_MODEL}"
            if model_settings.GROQ_API_KEY
            else f"openai/{model_settings.OPENAI_MODEL}"
        )

        return ChatResponse(
            response=answer,
            conversation_id=conversation_id,
            retrieved_contexts=contexts,
            evaluation=evaluation,
            model_used=model_used,
            cached=False,
        )

    except Exception as e:
        logger.error(f"Chat error: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/chat/stream")
async def chat_stream(request: ChatRequest):
    """Server-sent events streaming endpoint"""
    _, raw_texts = await rag_retriever.retrieve(query=request.message)

    async def event_generator():
        async for token in llm_service.stream_generate(
            question=request.message,
            contexts=raw_texts,
            history=request.history,
        ):
            yield f"data: {token}\n\n"
        yield "data: [DONE]\n\n"

    return StreamingResponse(event_generator(), media_type="text/event-stream")
