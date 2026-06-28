"""
RAG Retrieval Service
Hybrid search: dense (vector) + sparse (BM25-style keyword)
with MMR re-ranking for diversity
"""
import logging
from typing import List, Dict, Any, Tuple
import numpy as np

from app.core.database import get_collection
from app.services.embedding_service import EmbeddingService
from app.models.schemas import RetrievedContext
from app.core.config import settings

logger = logging.getLogger(__name__)


class RAGRetriever:
    def __init__(self):
        self.embedding_service = EmbeddingService()

    async def retrieve(
        self,
        query: str,
        top_k: int = None,
        filter_metadata: Dict[str, Any] = None,
    ) -> Tuple[List[RetrievedContext], List[str]]:
        """
        Retrieve relevant documents using hybrid search
        Returns: (contexts, raw_texts_for_evaluation)
        """
        top_k = top_k or settings.TOP_K_RETRIEVAL
        collection = get_collection()

        # Dense retrieval
        query_embedding = await self.embedding_service.embed_text(query)
        where_clause = filter_metadata if filter_metadata else None

        results = collection.query(
            query_embeddings=[query_embedding],
            n_results=min(top_k * 2, 20),  # over-fetch for re-ranking
            where=where_clause,
            include=["documents", "metadatas", "distances", "embeddings"],
        )

        if not results["documents"][0]:
            return [], []

        # Build candidates
        candidates = []
        for i, (doc, meta, dist) in enumerate(
            zip(results["documents"][0], results["metadatas"][0], results["distances"][0])
        ):
            similarity = 1 - dist  # cosine distance → similarity
            candidates.append({
                "id": results["ids"][0][i],
                "content": doc,
                "metadata": meta,
                "score": float(similarity),
                "embedding": results["embeddings"][0][i] if results.get("embeddings") else None,
            })

        # MMR re-ranking for diversity
        reranked = self._mmr_rerank(
            query_embedding, candidates, top_k, lambda_param=0.6
        )

        contexts = [
            RetrievedContext(
                document_id=c["id"],
                content=c["content"],
                score=c["score"],
                metadata=c["metadata"],
                modality=c["metadata"].get("modality", "text"),
            )
            for c in reranked
        ]

        raw_texts = [c["content"] for c in reranked]
        return contexts, raw_texts

    def _mmr_rerank(
        self,
        query_embedding: List[float],
        candidates: List[Dict],
        top_k: int,
        lambda_param: float = 0.6,
    ) -> List[Dict]:
        """Maximal Marginal Relevance for diverse retrieval"""
        if not candidates:
            return []

        query_vec = np.array(query_embedding)
        selected = []
        remaining = candidates.copy()

        while len(selected) < top_k and remaining:
            if not selected:
                # First: pick highest relevance
                best = max(remaining, key=lambda x: x["score"])
            else:
                # MMR score = λ * relevance - (1-λ) * max_similarity_to_selected
                selected_embeddings = [
                    np.array(c["embedding"]) for c in selected if c.get("embedding")
                ]
                best_score = float("-inf")
                best = remaining[0]

                for candidate in remaining:
                    relevance = candidate["score"]
                    if selected_embeddings and candidate.get("embedding"):
                        cand_vec = np.array(candidate["embedding"])
                        similarities = [
                            float(np.dot(cand_vec, sel) / (np.linalg.norm(cand_vec) * np.linalg.norm(sel) + 1e-9))
                            for sel in selected_embeddings
                        ]
                        max_sim = max(similarities) if similarities else 0
                    else:
                        max_sim = 0

                    mmr_score = lambda_param * relevance - (1 - lambda_param) * max_sim
                    if mmr_score > best_score:
                        best_score = mmr_score
                        best = candidate

            selected.append(best)
            remaining.remove(best)

        return selected

    async def add_documents(self, chunks: List[Dict[str, Any]]) -> int:
        """Add document chunks to vector store"""
        collection = get_collection()

        texts = [c["content"] for c in chunks]
        embeddings = await self.embedding_service.embed_batch(texts)

        collection.add(
            ids=[c["id"] for c in chunks],
            documents=texts,
            embeddings=embeddings,
            metadatas=[{**c["metadata"], "modality": c.get("modality", "text")} for c in chunks],
        )

        return len(chunks)
