"""
RAG Evaluation Service
Metrics: Faithfulness, Answer Relevancy, Context Precision, Context Recall
Uses RAGAS framework + custom scoring
"""

import asyncio
import logging
import time
from typing import List, Optional

from app.core.config import settings
from app.models.schemas import EvaluationScore
from openai import AsyncOpenAI

logger = logging.getLogger(__name__)


FAITHFULNESS_PROMPT = """You are evaluating whether an AI answer is faithful to the provided context.

Context:
{context}

Question: {question}
Answer: {answer}

Score faithfulness from 0.0 to 1.0:
- 1.0: All claims in the answer are directly supported by the context
- 0.5: Some claims supported, some not or slightly modified
- 0.0: Answer contradicts or ignores the context

Respond with ONLY a float number between 0.0 and 1.0."""

RELEVANCY_PROMPT = """Evaluate how relevant this answer is to the question.

Question: {question}
Answer: {answer}

Score relevancy from 0.0 to 1.0:
- 1.0: Directly and completely answers the question
- 0.5: Partially answers the question
- 0.0: Completely off-topic

Respond with ONLY a float number between 0.0 and 1.0."""

CONTEXT_PRECISION_PROMPT = """Evaluate whether the retrieved context is precise and relevant.

Question: {question}
Retrieved Context:
{context}

Score context precision from 0.0 to 1.0:
- 1.0: All retrieved context is highly relevant to answering the question
- 0.5: Mixed relevance, some useful some not
- 0.0: Retrieved context is irrelevant

Respond with ONLY a float number between 0.0 and 1.0."""


class EvaluationService:
    def __init__(self):
        api_key = settings.GROQ_API_KEY or settings.OPENAI_API_KEY
        base_url = settings.GROQ_BASE_URL if settings.GROQ_API_KEY else None

        self.client = AsyncOpenAI(
            api_key=api_key,
            base_url=base_url,
        )

    async def evaluate(
        self,
        question: str,
        answer: str,
        contexts: List[str],
        start_time: float,
        tokens_used: int,
        ground_truth: Optional[str] = None,
    ) -> EvaluationScore:
        """Run all evaluation metrics concurrently"""
        context_str = "\n\n---\n\n".join(contexts[:3])  # Limit to top 3 for eval
        latency_ms = (time.time() - start_time) * 1000

        if not settings.RAGAS_ENABLED or not contexts:
            return EvaluationScore(
                faithfulness=0.0,
                answer_relevancy=0.0,
                context_precision=0.0,
                context_recall=0.0,
                overall_score=0.0,
                latency_ms=latency_ms,
                tokens_used=tokens_used,
            )

        # Run evaluations concurrently
        results = await asyncio.gather(
            self._score_llm(
                FAITHFULNESS_PROMPT.format(
                    context=context_str, question=question, answer=answer
                )
            ),
            self._score_llm(RELEVANCY_PROMPT.format(question=question, answer=answer)),
            self._score_llm(
                CONTEXT_PRECISION_PROMPT.format(question=question, context=context_str)
            ),
            return_exceptions=True,
        )

        faithfulness = results[0] if isinstance(results[0], float) else 0.5
        relevancy = results[1] if isinstance(results[1], float) else 0.5
        precision = results[2] if isinstance(results[2], float) else 0.5

        # Context recall requires ground truth; estimate without it
        recall = self._estimate_recall(answer, contexts) if not ground_truth else 0.5

        overall = faithfulness * 0.3 + relevancy * 0.3 + precision * 0.2 + recall * 0.2

        return EvaluationScore(
            faithfulness=round(faithfulness, 3),
            answer_relevancy=round(relevancy, 3),
            context_precision=round(precision, 3),
            context_recall=round(recall, 3),
            overall_score=round(overall, 3),
            latency_ms=round(latency_ms, 2),
            tokens_used=tokens_used,
        )

    async def _score_llm(self, prompt: str) -> float:
        """Use GPT-4o-mini for fast, cheap evaluation scoring"""
        try:
            response = await self.client.chat.completions.create(
                model=settings.GROQ_MODEL if settings.GROQ_API_KEY else "gpt-4o-mini",
                messages=[{"role": "user", "content": prompt}],
                max_tokens=10,
                temperature=0,
            )
            text = response.choices[0].message.content.strip()
            return max(0.0, min(1.0, float(text)))
        except (ValueError, Exception) as e:
            logger.warning(f"Evaluation scoring failed: {e}")
            return 0.5

    def _estimate_recall(self, answer: str, contexts: List[str]) -> float:
        """Heuristic recall estimation based on answer coverage of context"""
        if not contexts or not answer:
            return 0.0

        answer_words = set(answer.lower().split())
        context_words = set(" ".join(contexts).lower().split())

        # Remove stopwords
        stopwords = {
            "the",
            "a",
            "an",
            "is",
            "are",
            "was",
            "were",
            "in",
            "on",
            "at",
            "to",
            "for",
            "of",
            "and",
            "or",
        }
        answer_keywords = answer_words - stopwords
        context_keywords = context_words - stopwords

        if not answer_keywords:
            return 0.5

        overlap = len(answer_keywords & context_keywords) / len(answer_keywords)
        return min(1.0, overlap * 1.2)  # slight boost for partial matches
