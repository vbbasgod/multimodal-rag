"""Embedding Service with Redis Caching and optional local provider"""

import hashlib
import json
import logging
from typing import List, Optional

import redis.asyncio as redis
from app.core.config import settings
from openai import AsyncOpenAI

logger = logging.getLogger(__name__)


class EmbeddingService:
    def __init__(self):
        # Provider selection: 'openai' (default) or 'local'
        self.provider = getattr(settings, "EMBEDDING_PROVIDER", "openai")

        if self.provider == "local":
            # Lazy import and load local sentence-transformers model
            try:
                from sentence_transformers import SentenceTransformer

                self._local_model = SentenceTransformer(settings.EMBEDDING_MODEL)
            except Exception as e:
                logger.error("Failed to load local embedding model: %s", e)
                raise
            self.client = None
        else:
            api_key = settings.GROQ_API_KEY or settings.OPENAI_API_KEY
            base_url = settings.GROQ_BASE_URL if settings.GROQ_API_KEY else None
            self.client = AsyncOpenAI(api_key=api_key, base_url=base_url)

        self.redis_client: Optional[redis.Redis] = None
        self._connect_redis()

    def _connect_redis(self):
        try:
            self.redis_client = redis.from_url(
                settings.REDIS_URL, encoding="utf-8", decode_responses=True
            )
        except Exception as e:
            logger.warning(f"Redis connection failed: {e}. Caching disabled.")

    def _cache_key(self, text: str) -> str:
        return f"embedding:{hashlib.sha256(text.encode()).hexdigest()}"

    async def embed_text(self, text: str) -> List[float]:
        """Get embedding with Redis cache"""
        cache_key = self._cache_key(text)

        # Try cache
        if self.redis_client:
            try:
                cached = await self.redis_client.get(cache_key)
                if cached:
                    return json.loads(cached)
            except Exception:
                pass

        # Generate embedding
        if self.provider == "local":
            emb = self._local_model.encode(text)
            embedding = emb.tolist() if hasattr(emb, "tolist") else list(emb)
        else:
            response = await self.client.embeddings.create(
                model=settings.EMBEDDING_MODEL,
                input=text,
            )
            embedding = response.data[0].embedding

        # Store in cache
        if self.redis_client:
            try:
                await self.redis_client.setex(
                    cache_key, settings.CACHE_TTL, json.dumps(embedding)
                )
            except Exception:
                pass

        return embedding

    async def embed_batch(self, texts: List[str]) -> List[List[float]]:
        """Batch embed texts"""
        # Check cache for each
        embeddings = []
        uncached_indices = []
        uncached_texts = []

        for i, text in enumerate(texts):
            cache_key = self._cache_key(text)
            cached = None
            if self.redis_client:
                try:
                    cached = await self.redis_client.get(cache_key)
                except Exception:
                    pass

            if cached:
                embeddings.append((i, json.loads(cached)))
            else:
                uncached_indices.append(i)
                uncached_texts.append(text)
                embeddings.append((i, None))

        # Batch API call for uncached
        if uncached_texts:
            if self.provider == "local":
                embs = self._local_model.encode(uncached_texts)
                # embs is numpy array or list of arrays
                embs_list = [
                    e.tolist() if hasattr(e, "tolist") else list(e) for e in embs
                ]
            else:
                response = await self.client.embeddings.create(
                    model=settings.EMBEDDING_MODEL,
                    input=uncached_texts,
                )
                embs_list = [d.embedding for d in response.data]

            for idx, emb in zip(uncached_indices, embs_list):
                embeddings[idx] = (idx, emb)

        # Return in original order
        return [emb for _, emb in sorted(embeddings, key=lambda x: x[0])]
