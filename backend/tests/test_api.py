"""
Backend Test Suite
Run: pytest tests/ -v
"""
import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from fastapi.testclient import TestClient


# ── App import (mock external services before importing) ──────
@pytest.fixture(scope="session", autouse=True)
def mock_external_services():
    """Mock ChromaDB and Redis so tests run without infra"""
    with patch("app.core.database.chromadb") as mock_chroma, \
         patch("app.services.embedding_service.redis") as mock_redis:

        mock_collection = MagicMock()
        mock_collection.query.return_value = {
            "ids": [["doc1", "doc2"]],
            "documents": [["FastAPI is a web framework.", "It supports async."]],
            "metadatas": [[{"source": "test.txt"}, {"source": "test.txt"}]],
            "distances": [[0.1, 0.2]],
            "embeddings": [[[0.1] * 1536, [0.2] * 1536]],
        }
        mock_collection.add.return_value = None
        mock_collection.count.return_value = 2

        mock_client = MagicMock()
        mock_client.get_or_create_collection.return_value = mock_collection
        mock_client.heartbeat.return_value = True
        mock_chroma.HttpClient.return_value = mock_client

        yield


@pytest.fixture
def client():
    from app.main import app
    with TestClient(app) as c:
        yield c


# ── Health Tests ──────────────────────────────────────────────
class TestHealth:
    def test_health_returns_200(self, client):
        resp = client.get("/api/v1/health")
        assert resp.status_code == 200

    def test_health_has_status_field(self, client):
        resp = client.get("/api/v1/health")
        data = resp.json()
        assert "status" in data
        assert "version" in data
        assert "services" in data

    def test_metrics_endpoint(self, client):
        resp = client.get("/api/v1/metrics")
        assert resp.status_code == 200
        data = resp.json()
        assert "documents_indexed" in data


# ── Ingest Tests ──────────────────────────────────────────────
class TestIngest:
    @patch("app.api.routes.ingest.doc_processor")
    @patch("app.api.routes.ingest.rag_retriever")
    def test_ingest_text(self, mock_retriever, mock_processor, client):
        mock_processor.process_text = AsyncMock(return_value=[
            {"id": "abc123", "content": "test", "modality": "text", "metadata": {}}
        ])
        mock_retriever.add_documents = AsyncMock(return_value=1)

        resp = client.post("/api/v1/ingest/text", json={
            "content": "This is a test document about FastAPI.",
            "metadata": {"source": "test"}
        })
        assert resp.status_code == 200
        data = resp.json()
        assert data["chunks_created"] == 1
        assert data["status"] == "success"

    def test_ingest_text_empty_content(self, client):
        resp = client.post("/api/v1/ingest/text", json={"content": ""})
        assert resp.status_code == 422 or resp.status_code == 400


# ── Chat Tests ────────────────────────────────────────────────
class TestChat:
    @patch("app.api.routes.chat.rag_retriever")
    @patch("app.api.routes.chat.llm_service")
    @patch("app.api.routes.chat.eval_service")
    def test_chat_basic(self, mock_eval, mock_llm, mock_rag, client):
        from app.models.schemas import RetrievedContext, EvaluationScore

        mock_rag.retrieve = AsyncMock(return_value=(
            [RetrievedContext(
                document_id="doc1",
                content="FastAPI is a web framework.",
                score=0.95,
                metadata={},
                modality="text"
            )],
            ["FastAPI is a web framework."]
        ))
        mock_llm.generate = AsyncMock(return_value=(
            "FastAPI is a modern Python web framework.", 150, 1234567890.0
        ))
        mock_eval.evaluate = AsyncMock(return_value=EvaluationScore(
            faithfulness=0.9,
            answer_relevancy=0.85,
            context_precision=0.8,
            context_recall=0.75,
            overall_score=0.83,
            latency_ms=450.0,
            tokens_used=150
        ))

        resp = client.post("/api/v1/chat", json={
            "message": "What is FastAPI?",
            "use_rag": True,
            "history": []
        })
        assert resp.status_code == 200
        data = resp.json()
        assert "response" in data
        assert "evaluation" in data
        assert "conversation_id" in data
        assert data["evaluation"]["overall_score"] == 0.83

    def test_chat_missing_message(self, client):
        resp = client.post("/api/v1/chat", json={})
        assert resp.status_code == 422


# ── Evaluation Tests ──────────────────────────────────────────
class TestEvaluation:
    @patch("app.services.evaluation_service.AsyncOpenAI")
    def test_eval_score_clamped(self, mock_openai):
        """Scores must always be between 0 and 1"""
        from app.services.evaluation_service import EvaluationService
        svc = EvaluationService()

        # Test _estimate_recall stays within bounds
        recall = svc._estimate_recall(
            answer="FastAPI supports async and type hints.",
            contexts=["FastAPI is a web framework.", "It supports async operations."]
        )
        assert 0.0 <= recall <= 1.0

    def test_eval_empty_contexts(self):
        from app.services.evaluation_service import EvaluationService
        svc = EvaluationService()
        recall = svc._estimate_recall("some answer", [])
        assert recall == 0.0


# ── Schema Tests ──────────────────────────────────────────────
class TestSchemas:
    def test_chat_request_defaults(self):
        from app.models.schemas import ChatRequest
        req = ChatRequest(message="hello")
        assert req.use_rag is True
        assert req.top_k == 5
        assert req.history == []

    def test_eval_score_validation(self):
        from app.models.schemas import EvaluationScore
        score = EvaluationScore(
            faithfulness=0.9,
            answer_relevancy=0.8,
            context_precision=0.85,
            context_recall=0.75,
            overall_score=0.83,
            latency_ms=300.0,
            tokens_used=200
        )
        assert score.overall_score == 0.83
