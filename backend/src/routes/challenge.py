from fastapi import APIRouter, Depends, HTTPException, Request
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session
from typing import Optional
import json

from ..ai_generator import generate_challenge_with_ai
from ..generators import SUPPORTED_SUBJECTS, SUBJECT_METADATA, is_supported, is_valid_area
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
    subject: Optional[str] = Field(default="per", description="per | biochem")
    # area solo aplica a asignaturas con subáreas (ej. biochem)
    area: Optional[str] = Field(default=None, description="metabolismo | genetica | null")

    class Config:
        json_schema_extra = {
            "example": {"difficulty": "easy", "subject": "biochem", "area": "metabolismo"}
        }


@router.get("/subjects")
async def list_subjects():
    """Lista las asignaturas disponibles con sus áreas y metadata."""
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

        # Validar área (None es válido siempre = "todas las áreas")
        area = (request.area or None)
        if area:
            area = area.lower().strip() or None
        if area and not is_valid_area(subject, area):
            raise HTTPException(
                status_code=400,
                detail=f"Área inválida {area!r} para asignatura {subject!r}.",
            )

        # Validar dificultad
        difficulty = (request.difficulty or "").lower().strip()
        if difficulty not in {"easy", "medium", "hard"}:
            raise HTTPException(
                status_code=400,
                detail=f"Dificultad inválida: {difficulty!r}",
            )

        # ── Cuota: desactivada en modo desarrollo (sin límite) ───────────────
        # Si quieres reactivar la cuota, descomenta este bloque:
        #
        # quota = get_challenge_quota(db, user_id)
        # if not quota:
        #     quota = create_challenge_quota(db, user_id)
        # quota = reset_quota_if_needed(db, quota)
        # if quota.quota_remaining <= 0:
        #     raise HTTPException(status_code=429, detail="Quota exhausted")
        # ─────────────────────────────────────────────────────────────────────

        # Generar
        challenge_data = generate_challenge_with_ai(
            difficulty, subject=subject, area=area
        )

        # El generador puede haber resuelto el área (por ejemplo cuando se pasa
        # None y elige aleatoriamente entre las áreas disponibles).
        resolved_area = challenge_data.pop("_area", area)

        # Persistir
        new_challenge = create_challenge(
            db=db,
            difficulty=difficulty,
            subject=subject,
            area=resolved_area,
            created_by=user_id,
            title=challenge_data["title"],
            options=json.dumps(challenge_data["options"]),
            correct_answer_id=challenge_data["correct_answer_id"],
            explanation=challenge_data["explanation"],
        )

        # ── Cuota: descomenta también esto si reactivas el límite ────────────
        # quota.quota_remaining -= 1
        # db.commit()
        # ─────────────────────────────────────────────────────────────────────

        return {
            "id": new_challenge.id,
            "difficulty": difficulty,
            "subject": subject,
            "area": resolved_area,
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
    area: Optional[str] = None,
):
    """Historial del usuario. Acepta ?subject=...&area=... para filtrar."""
    user_details = authenticate_and_get_user_details(request)
    user_id = user_details.get("user_id")

    if subject is not None:
        subject = subject.lower().strip() or None
        if subject and not is_supported(subject):
            raise HTTPException(
                status_code=400, detail=f"Asignatura no soportada: {subject!r}")

    if area is not None:
        area = area.lower().strip() or None
        if area and subject and not is_valid_area(subject, area):
            raise HTTPException(
                status_code=400,
                detail=f"Área {area!r} no válida para {subject!r}")

    rows = get_user_challenges(db, user_id, subject=subject, area=area)
    return {
        "challenges": [
            {
                "id": c.id,
                "difficulty": c.difficulty,
                "subject": c.subject,
                "area": c.area,
                "title": c.title,
                "options": json.loads(c.options),
                "correct_answer_id": c.correct_answer_id,
                "explanation": c.explanation,
                "timestamp": c.date_created.isoformat(),
            }
            for c in rows
        ]
    }