"""Evaluation Routes"""
from fastapi import APIRouter
from pydantic import BaseModel
from typing import List
from app.services.evaluation_service import EvaluationService
import time

router = APIRouter()
eval_service = EvaluationService()


class EvalRequest(BaseModel):
    question: str
    answer: str
    contexts: List[str]
    ground_truth: str = None


@router.post("/evaluate")
async def evaluate_response(request: EvalRequest):
    """Standalone evaluation endpoint"""
    score = await eval_service.evaluate(
        question=request.question,
        answer=request.answer,
        contexts=request.contexts,
        start_time=time.time(),
        tokens_used=0,
        ground_truth=request.ground_truth,
    )
    return score
