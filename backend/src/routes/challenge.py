from fastapi import APIRouter, Depends, HTTPException, Request
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session
from typing import Optional
import json
from datetime import datetime

from ..ai_generator import generate_challenge_with_ai
from ..generators import SUPPORTED_SUBJECTS, SUBJECT_METADATA, is_supported
from ..database.db import (
    get_challenge_quota,
    create_challenge,
    create_challenge_quota,
    reset_quota_if_needed,
    get_user_challenges,
)
from ..utils import authenticate_and_get_user_details
from ..database.models import get_db

router = APIRouter()


class ChallengeRequest(BaseModel):
    difficulty: str = Field(..., description="easy | medium | hard")
    # Compatible hacia atrás: si el cliente antiguo no envía subject,
    # asumimos PER. Los clientes nuevos enviarán "per" o "biochem".
    subject: Optional[str] = Field(default="per", description="per | biochem")

    class Config:
        json_schema_extra = {
            "example": {"difficulty": "easy", "subject": "per"}
        }


@router.get("/subjects")
async def list_subjects():
    """Lista las asignaturas disponibles y su metadata (para el selector del frontend)."""
    return {
        "subjects": [SUBJECT_METADATA[s] for s in SUPPORTED_SUBJECTS]
    }


@router.post("/generate-challenge")
async def generate_challenge(
    request: ChallengeRequest,
    request_obj: Request,
    db: Session = Depends(get_db),
):
    try:
        user_details = authenticate_and_get_user_details(request_obj)
        user_id = user_details.get("user_id")

        # Validar asignatura
        subject = (request.subject or "per").lower().strip()
        if not is_supported(subject):
            raise HTTPException(
                status_code=400,
                detail=f"Asignatura no soportada: {subject!r}. "
                       f"Soportadas: {SUPPORTED_SUBJECTS}",
            )

        # Validar dificultad
        difficulty = (request.difficulty or "").lower().strip()
        if difficulty not in {"easy", "medium", "hard"}:
            raise HTTPException(
                status_code=400,
                detail=f"Dificultad inválida: {difficulty!r}",
            )

        # Cuota
        #quota = get_challenge_quota(db, user_id)
        #if not quota:
        #    quota = create_challenge_quota(db, user_id)
        #quota = reset_quota_if_needed(db, quota)
        #if quota.quota_remaining <= 0:
        #    raise HTTPException(status_code=429, detail="Quota exhausted")

        # Generar
        challenge_data = generate_challenge_with_ai(difficulty, subject=subject)

        # Persistir
        new_challenge = create_challenge(
            db=db,
            difficulty=difficulty,
            subject=subject,
            created_by=user_id,
            title=challenge_data["title"],
            options=json.dumps(challenge_data["options"]),
            correct_answer_id=challenge_data["correct_answer_id"],
            explanation=challenge_data["explanation"],
        )

        #quota.quota_remaining -= 1
        #db.commit()

        return {
            "id": new_challenge.id,
            "difficulty": difficulty,
            "subject": subject,
            "title": new_challenge.title,
            "options": json.loads(new_challenge.options),
            "correct_answer_id": new_challenge.correct_answer_id,
            "explanation": new_challenge.explanation,
            "timestamp": new_challenge.date_created.isoformat(),
        }

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/my-history")
async def my_history(
    request: Request,
    db: Session = Depends(get_db),
    subject: Optional[str] = None,
):
    """Historial del usuario. Acepta ?subject=per|biochem para filtrar."""
    user_details = authenticate_and_get_user_details(request)
    user_id = user_details.get("user_id")

    # Validamos subject si se ha pasado
    if subject is not None:
        subject = subject.lower().strip() or None
        if subject and not is_supported(subject):
            raise HTTPException(
                status_code=400,
                detail=f"Asignatura no soportada: {subject!r}",
            )

    rows = get_user_challenges(db, user_id, subject=subject)
    return {
        "challenges": [
            {
                "id": c.id,
                "difficulty": c.difficulty,
                "subject": c.subject,
                "title": c.title,
                "options": json.loads(c.options),
                "correct_answer_id": c.correct_answer_id,
                "explanation": c.explanation,
                "timestamp": c.date_created.isoformat(),
            }
            for c in rows
        ]
    }