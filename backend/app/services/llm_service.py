"""LLM Generation Service with Multimodal Support"""

import base64
import logging
import time
from typing import AsyncGenerator, List, Optional, Tuple

from app.core.config import settings
from app.models.schemas import ChatMessage
from openai import AsyncOpenAI

logger = logging.getLogger(__name__)

SYSTEM_PROMPT = """You are a helpful AI assistant with access to a knowledge base.
Answer questions accurately based on the provided context.
If the context doesn't contain sufficient information, say so clearly.
When referencing images or visual content, describe what's relevant.
Be concise, accurate, and cite which parts of the context you're using."""


class LLMService:
    def __init__(self):
        api_key = settings.GROQ_API_KEY or settings.OPENAI_API_KEY
        base_url = settings.GROQ_BASE_URL if settings.GROQ_API_KEY else None

        self.client = AsyncOpenAI(
            api_key=api_key,
            base_url=base_url,
        )

    async def generate(
        self,
        question: str,
        contexts: List[str],
        history: List[ChatMessage],
        image_base64: Optional[str] = None,
    ) -> Tuple[str, int, float]:
        """
        Generate response using RAG context
        Returns: (answer, tokens_used, start_time)
        """
        start_time = time.time()

        # Build context string
        context_str = "\n\n".join(
            [f"[Context {i+1}]:\n{ctx}" for i, ctx in enumerate(contexts)]
        )

        # Build messages
        messages = [{"role": "system", "content": SYSTEM_PROMPT}]

        # Add conversation history (last 6 turns)
        for msg in history[-6:]:
            messages.append({"role": msg.role.value, "content": msg.content})

        # Build user message with optional image
        if image_base64:
            user_content = [
                {
                    "type": "text",
                    "text": f"Context from knowledge base:\n{context_str}\n\nQuestion: {question}",
                },
                {
                    "type": "image_url",
                    "image_url": {"url": f"data:image/jpeg;base64,{image_base64}"},
                },
            ]
            messages.append({"role": "user", "content": user_content})
        else:
            user_content = (
                f"Context from knowledge base:\n{context_str}\n\nQuestion: {question}"
            )
            messages.append({"role": "user", "content": user_content})

        response = await self.client.chat.completions.create(
            model=(
                settings.GROQ_MODEL if settings.GROQ_API_KEY else settings.OPENAI_MODEL
            ),
            messages=messages,
            max_tokens=settings.MAX_TOKENS,
            temperature=settings.TEMPERATURE,
        )

        answer = response.choices[0].message.content
        tokens_used = response.usage.total_tokens
        return answer, tokens_used, start_time

    async def stream_generate(
        self,
        question: str,
        contexts: List[str],
        history: List[ChatMessage],
    ) -> AsyncGenerator[str, None]:
        """Streaming generation for SSE"""
        context_str = "\n\n".join(
            [f"[Context {i+1}]:\n{ctx}" for i, ctx in enumerate(contexts)]
        )

        messages = [{"role": "system", "content": SYSTEM_PROMPT}]

        # Add conversation history (last 6 turns)
        for msg in history[-6:]:
            messages.append({"role": msg.role.value, "content": msg.content})

        messages.append(
            {
                "role": "user",
                "content": f"Context:\n{context_str}\n\nQuestion: {question}",
            }
        )

        async with self.client.chat.completions.create(
            model=(
                settings.GROQ_MODEL if settings.GROQ_API_KEY else settings.OPENAI_MODEL
            ),
            messages=messages,
            max_tokens=settings.MAX_TOKENS,
            temperature=settings.TEMPERATURE,
            stream=True,
        ) as stream:
            async for chunk in stream:
                if chunk.choices[0].delta.content:
                    yield chunk.choices[0].delta.content
