"""
Dispatcher de generación de preguntas tipo test.

El cuerpo real vive en backend/src/generators/. Este módulo mantiene una
firma estable para el resto del backend.
"""
from typing import Dict, Any, Optional

from .generators import generate, is_supported, is_valid_area


DEFAULT_SUBJECT = "per"


def generate_challenge_with_ai(
    difficulty: str,
    subject: str = DEFAULT_SUBJECT,
    area: Optional[str] = None,
) -> Dict[str, Any]:
    """Genera una pregunta para la asignatura/área y dificultad dadas.

    Args:
        difficulty: "easy" | "medium" | "hard".
        subject: "per" | "biochem".
        area: para asignaturas con áreas (ej. biochem → "metabolismo" | "genetica" | None).

    Returns:
        dict con title, options[4], correct_answer_id, explanation.
        Si la asignatura tiene áreas, también incluye `_area` con el área final usada.
    """
    if not is_supported(subject):
        print(f"[ai_generator] Asignatura no soportada: {subject!r}; "
              f"uso {DEFAULT_SUBJECT}.")
        subject = DEFAULT_SUBJECT

    if not is_valid_area(subject, area):
        print(f"[ai_generator] Área no válida para {subject}: {area!r}; "
              f"se ignora.")
        area = None

    return generate(subject=subject, difficulty=difficulty, area=area)