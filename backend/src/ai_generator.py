"""
Dispatcher de generación de preguntas tipo test.

El cuerpo real vive en backend/src/generators/. Este módulo mantiene la
firma pública generate_challenge_with_ai(difficulty, subject) para que
el resto del backend no necesite cambios al añadir nuevas asignaturas.

Compatibilidad hacia atrás:
    generate_challenge_with_ai("easy")  → equivale a subject="per"
"""
from typing import Dict, Any

from .generators import get_generator, is_supported, SUPPORTED_SUBJECTS


DEFAULT_SUBJECT = "per"


def generate_challenge_with_ai(
    difficulty: str,
    subject: str = DEFAULT_SUBJECT,
) -> Dict[str, Any]:
    """Genera una pregunta para la asignatura y dificultad dadas.

    Args:
        difficulty: "easy" | "medium" | "hard".
        subject: "per" | "biochem" (por defecto "per" para compatibilidad).

    Returns:
        dict con title, options[4], correct_answer_id, explanation.
        Si la asignatura no es válida, devuelve el fallback de PER.
    """
    if not is_supported(subject):
        print(f"[ai_generator] Asignatura no soportada: {subject!r}; "
              f"uso {DEFAULT_SUBJECT}.")
        subject = DEFAULT_SUBJECT

    gen = get_generator(subject)
    return gen(difficulty)