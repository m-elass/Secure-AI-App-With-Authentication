"""
Paquete de generadores de preguntas por asignatura.

Uso:
    from backend.src.generators import get_generator
    challenge = get_generator("per")("easy")
    challenge = get_generator("biochem")("medium")
"""
from typing import Callable, Dict, Any

from . import per as _per
from . import biochem as _biochem


# Tabla de despacho: nombre canónico de la asignatura → función generadora.
_REGISTRY: Dict[str, Callable[[str], Dict[str, Any]]] = {
    "per": _per.generate,
    "biochem": _biochem.generate,
}

# Asignaturas soportadas, en orden de aparición en la UI.
SUPPORTED_SUBJECTS = ["per", "biochem"]

# Metadata para que el frontend pueda construir el selector dinámicamente.
# El backend puede exponerla en un endpoint /subjects si se desea.
SUBJECT_METADATA = {
    "per": {
        "id": "per",
        "name": "PER",
        "full_name": "Programación en Entornos de Red",
        "description": "Python OOP, HTTP, sockets, JSON",
        "accent": "violet",   # el frontend usa esto para el color de marca
    },
    "biochem": {
        "id": "biochem",
        "name": "Bioquímica",
        "full_name": "Bioquímica y Biología Molecular",
        "description": "Replicación, transcripción, traducción, regulación, ingeniería genética",
        "accent": "emerald",
    },
}


def get_generator(subject: str) -> Callable[[str], Dict[str, Any]]:
    """Devuelve la función generadora para una asignatura.

    Lanza ValueError si la asignatura no existe.
    """
    subject = (subject or "").lower().strip()
    if subject not in _REGISTRY:
        raise ValueError(
            f"Asignatura desconocida: {subject!r}. "
            f"Soportadas: {SUPPORTED_SUBJECTS}"
        )
    return _REGISTRY[subject]


def is_supported(subject: str) -> bool:
    return (subject or "").lower().strip() in _REGISTRY