# Multimodal RAG Chatbot

Production-grade RAG system with multimodal support, RAGAS evaluation, and Kubernetes deployment.

## Tech Stack

| Layer         | Technology                                         |
| ------------- | -------------------------------------------------- |
| LLM           | GPT-4o (OpenAI)                                    |
| Embeddings    | text-embedding-3-small                             |
| Vector DB     | ChromaDB                                           |
| Cache         | Redis                                              |
| Backend       | FastAPI + Python 3.11                              |
| Frontend      | React 18 + Vite                                    |
| Evaluation    | RAGAS (Faithfulness, Relevancy, Precision, Recall) |
| Container     | Docker (multi-stage builds)                        |
| Orchestration | Kubernetes + HPA                                   |

## Architecture

```
┌──────────────┐     ┌──────────────────────────────────────────┐
│   Browser    │────▶│  Nginx (Frontend)                        │
└──────────────┘     │  React SPA + EvalPanel                   │
                     └──────────────┬───────────────────────────┘
                                    │ /api/*
                     ┌──────────────▼───────────────────────────┐
                     │  FastAPI Backend                          │
                     │  ├── /chat       (RAG + GPT-4o)          │
                     │  ├── /ingest     (PDF/Image/Text)        │
                     │  ├── /evaluate   (RAGAS metrics)         │
                     │  └── /health                             │
                     └──────────┬────────────────┬──────────────┘
                                │                │
              ┌─────────────────▼──┐   ┌─────────▼────────────┐
              │  ChromaDB           │   │  Redis Cache          │
              │  (Vector Store)     │   │  (Embedding cache)    │
              └────────────────────┘   └──────────────────────┘
```

## Quick Start (Docker Compose)

```bash
# 1. Clone and setup
git clone <repo>
cd multimodal-rag
cp .env.example .env
# Edit .env and set OPENAI_API_KEY

# 2. Run everything
docker compose up --build -d

# 3. Open browser
open http://localhost:3000
```

## Local Development

```bash
# Backend
cd backend
pip install -r requirements.txt
uvicorn app.main:app --reload --port 8000

# Frontend (separate terminal)
cd frontend
npm install
npm run dev
```

## Kubernetes Deployment

### Prerequisites

```bash
# Install kubectl
# Install Docker
# Have access to a K8s cluster (minikube / GKE / EKS / AKS)

# For local: minikube start --memory=4096 --cpus=4
```

### Step 1 — Build & Push Images

```bash
# Set your registry (DockerHub example)
export REGISTRY=yourdockerhubuser

# Build images
./scripts/deploy.sh build $REGISTRY

# Login and push
docker login
./scripts/deploy.sh push $REGISTRY
```

### Step 2 — Configure Secrets

```bash
# Set your OpenAI API key
kubectl create secret generic rag-secrets \
  --from-literal=OPENAI_API_KEY=sk-your-key \
  -n rag-system \
  --dry-run=client -o yaml | kubectl apply -f -
```

### Step 3 — Deploy

```bash
./scripts/deploy.sh k8s $REGISTRY

# Or manually:
kubectl apply -f k8s/
```

### Step 4 — Access

```bash
# Port-forward for local testing
kubectl port-forward service/rag-frontend-service 8080:80 -n rag-system
kubectl port-forward service/rag-backend-service 8000:8000 -n rag-system

# Or get LoadBalancer IP
kubectl get ingress -n rag-system
```

### Useful Commands

```bash
# Check pod status
kubectl get pods -n rag-system

# View backend logs
kubectl logs -l app=rag-backend -n rag-system -f

# Check HPA scaling
kubectl get hpa -n rag-system

# Scale manually
kubectl scale deployment rag-backend --replicas=4 -n rag-system

# Rollback
./scripts/deploy.sh rollback
```

## Evaluation Metrics (RAGAS)

| Metric                | Description                           | Range |
| --------------------- | ------------------------------------- | ----- |
| **Faithfulness**      | Are claims grounded in context?       | 0–1   |
| **Answer Relevancy**  | Does the answer address the question? | 0–1   |
| **Context Precision** | Are retrieved docs relevant?          | 0–1   |
| **Context Recall**    | Does context cover the answer?        | 0–1   |
| **Overall Score**     | Weighted average                      | 0–1   |

Grades: A (≥85%) · B (≥70%) · C (≥55%) · D (<55%)

## Supported Document Types

| Type                 | Processing                                                    |
| -------------------- | ------------------------------------------------------------- |
| PDF                  | Text extraction (PyMuPDF) + image description (GPT-4o Vision) |
| Image (JPG/PNG/WebP) | OCR (Tesseract) + visual description (GPT-4o Vision)          |
| Plain Text           | Chunked and embedded directly                                 |

## Retrieval Strategy

- **Dense retrieval**: cosine similarity via ChromaDB
- **MMR re-ranking**: Maximal Marginal Relevance for diversity
- **Redis caching**: embedding cache to reduce API costs
- **Hybrid chunking**: 512 tokens with 50-token overlap

## API Reference

```
POST /api/v1/chat           - Chat with RAG
POST /api/v1/ingest/file    - Upload document
POST /api/v1/ingest/text    - Ingest plain text
POST /api/v1/evaluate       - Standalone evaluation
GET  /api/v1/health         - Health check
GET  /api/v1/metrics        - System metrics
```

## Environment Variables

See `.env.example` for full reference.

## Resume Talking Points

- **Multimodal RAG**: text, PDF, and image ingestion with GPT-4o Vision
- **Production architecture**: FastAPI + ChromaDB + Redis on Kubernetes
- **Real-time evaluation**: RAGAS faithfulness/relevancy/precision/recall per response
- **Auto-scaling**: HPA scales backend pods 2→8 based on CPU/memory
- **Optimized retrieval**: MMR re-ranking + Redis embedding cache
- **Zero-downtime deploys**: Rolling update strategy with startup/liveness/readiness probes
- **Multi-stage Docker**: minimized image sizes (~200MB backend, ~50MB frontend)

## Architecture

![Architecture](docs/images/architecture.svg)
