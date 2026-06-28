#!/usr/bin/env bash
# ═══════════════════════════════════════════════════════════
#  Multimodal RAG Chatbot - Full Deploy Script
#  Usage: ./scripts/deploy.sh [build|push|k8s|all] [registry]
# ═══════════════════════════════════════════════════════════
set -euo pipefail

# ── Config ───────────────────────────────────────────────────
REGISTRY="${2:-your-dockerhub-user}"  # e.g. myuser or ghcr.io/myorg
BACKEND_IMAGE="${REGISTRY}/multimodal-rag-backend"
FRONTEND_IMAGE="${REGISTRY}/multimodal-rag-frontend"
TAG="${TAG:-latest}"
NAMESPACE="rag-system"

RED='\033[0;31m'; GREEN='\033[0;32m'; YELLOW='\033[1;33m'; NC='\033[0m'

log()  { echo -e "${GREEN}[+]${NC} $1"; }
warn() { echo -e "${YELLOW}[!]${NC} $1"; }
err()  { echo -e "${RED}[✗]${NC} $1"; exit 1; }

# ── Commands ─────────────────────────────────────────────────
build_images() {
    log "Building backend image..."
    docker build -t "${BACKEND_IMAGE}:${TAG}" ./backend --target runtime

    log "Building frontend image..."
    docker build -t "${FRONTEND_IMAGE}:${TAG}" ./frontend \
        --build-arg VITE_API_URL=/api/v1

    log "Images built successfully."
    docker images | grep multimodal-rag
}

push_images() {
    log "Pushing images to registry: ${REGISTRY}..."
    docker push "${BACKEND_IMAGE}:${TAG}"
    docker push "${FRONTEND_IMAGE}:${TAG}"
    log "Push complete."
}

deploy_k8s() {
    log "Deploying to Kubernetes namespace: ${NAMESPACE}..."

    # Update image references in manifests
    sed -i "s|your-registry/multimodal-rag-backend:latest|${BACKEND_IMAGE}:${TAG}|g" k8s/03-backend-deployment.yaml
    sed -i "s|your-registry/multimodal-rag-frontend:latest|${FRONTEND_IMAGE}:${TAG}|g" k8s/04-frontend-deployment.yaml

    # Apply all manifests in order
    kubectl apply -f k8s/00-namespace.yaml
    kubectl apply -f k8s/01-secrets-configmap.yaml
    kubectl apply -f k8s/02-infra-deployments.yaml

    log "Waiting for ChromaDB to be ready..."
    kubectl rollout status deployment/chromadb -n ${NAMESPACE} --timeout=120s

    kubectl apply -f k8s/03-backend-deployment.yaml
    log "Waiting for backend to be ready..."
    kubectl rollout status deployment/rag-backend -n ${NAMESPACE} --timeout=180s

    kubectl apply -f k8s/04-frontend-deployment.yaml
    kubectl apply -f k8s/05-ingress.yaml

    log "Deployment complete! Status:"
    kubectl get pods -n ${NAMESPACE}
    kubectl get services -n ${NAMESPACE}
    kubectl get ingress -n ${NAMESPACE}
}

rollback() {
    warn "Rolling back backend..."
    kubectl rollout undo deployment/rag-backend -n ${NAMESPACE}
    warn "Rolling back frontend..."
    kubectl rollout undo deployment/rag-frontend -n ${NAMESPACE}
    log "Rollback complete."
}

status() {
    log "=== Cluster Status ==="
    kubectl get all -n ${NAMESPACE}
    echo ""
    log "=== Pod Logs (backend, last 20 lines) ==="
    kubectl logs -l app=rag-backend -n ${NAMESPACE} --tail=20 || true
}

# ── Entry Point ───────────────────────────────────────────────
CMD="${1:-help}"

case "$CMD" in
    build)   build_images ;;
    push)    push_images ;;
    k8s)     deploy_k8s ;;
    all)     build_images && push_images && deploy_k8s ;;
    rollback) rollback ;;
    status)  status ;;
    *)
        echo "Usage: $0 [build|push|k8s|all|rollback|status] [registry]"
        echo ""
        echo "  build    - Build Docker images"
        echo "  push     - Push images to registry"
        echo "  k8s      - Deploy to Kubernetes"
        echo "  all      - Build + Push + Deploy"
        echo "  rollback - Roll back last deployment"
        echo "  status   - Show cluster status"
        ;;
esac
