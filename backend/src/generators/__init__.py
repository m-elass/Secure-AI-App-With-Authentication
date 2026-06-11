"""
Paquete de generadores de preguntas por asignatura/área.

Uso:
    from backend.src.generators import generate
    challenge = generate(subject="per", difficulty="easy")
    challenge = generate(subject="biochem", difficulty="medium", area="metabolismo")
"""
from typing import Dict, Any, Optional

from . import per as _per
from . import biochem as _biochem


SUPPORTED_SUBJECTS = ["per", "biochem"]

# Áreas disponibles por asignatura (vacío = sin áreas, todo va junto)
SUBJECT_AREAS = {
    "per": [],
    "biochem": ["metabolismo", "genetica"],
}


SUBJECT_METADATA = {
    "per": {
        "id": "per",
        "name": "PER",
        "full_name": "Programación en Entornos de Red",
        "description": "Python OOP, HTTP, sockets, JSON",
        "accent": "violet",
        "areas": [],
    },
    "biochem": {
        "id": "biochem",
        "name": "Bioquímica",
        "full_name": "Bioquímica y Biología Molecular",
        "description": "Metabolismo y genética molecular",
        "accent": "emerald",
        "areas": [
            {"id": "metabolismo", "name": "Metabolismo",
             "description": "Glucólisis, Krebs, β-oxidación, ureogénesis, hormonas"},
            {"id": "genetica",    "name": "Genética",
             "description": "Replicación, transcripción, traducción, ingeniería"},
        ],
    },
}


def is_supported(subject: str) -> bool:
    return (subject or "").lower().strip() in SUPPORTED_SUBJECTS


def has_areas(subject: str) -> bool:
    return bool(SUBJECT_AREAS.get((subject or "").lower().strip(), []))


def is_valid_area(subject: str, area: Optional[str]) -> bool:
    """area=None es válido siempre (significa 'todas las áreas')."""
    if area is None or area == "":
        return True
    return area in SUBJECT_AREAS.get((subject or "").lower().strip(), [])


def generate(subject: str, difficulty: str, area: Optional[str] = None) -> Dict[str, Any]:
    """Despacha la generación a la asignatura correcta.

    Args:
        subject: "per" | "biochem"
        difficulty: "easy" | "medium" | "hard"
        area: solo aplicable a asignaturas con áreas (biochem). None = aleatorio
              entre las áreas disponibles.
    """
    subject = (subject or "").lower().strip()
    if subject == "per":
        return _per.generate(difficulty)
    elif subject == "biochem":
        return _biochem.generate(difficulty, area=area)
    else:
        raise ValueError(f"Asignatura desconocida: {subject!r}")