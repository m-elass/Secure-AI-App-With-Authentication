"""
Helpers compartidos por todos los generadores.

NOVEDADES v3 (subáreas):
─────────────────────────
- pick_fragment ahora acepta `area` además de `source_hint`. Esto permite
  filtrar el corpus por sub-bloque dentro de una asignatura.
  Ejemplo: pick_fragment("biochem", area="metabolismo") → solo fragmentos
  cuyo campo `area == "metabolismo"`.
"""
import json
import os
import random
import statistics
from pathlib import Path
from typing import Dict, Any, List, Optional, Callable

from openai import OpenAI
from dotenv import load_dotenv

load_dotenv()

_client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))


# ──────────────────────────────────────────────────────────────────────────────
# CORPUS LOADER
# ──────────────────────────────────────────────────────────────────────────────

_CORPUS_CACHE: Dict[str, List[Dict[str, Any]]] = {}

_MATERIALS_DIR = Path(__file__).resolve().parent.parent.parent / "materials"


def load_corpus(subject: str) -> List[Dict[str, Any]]:
    """Carga (con caché) el corpus de una asignatura."""
    if subject in _CORPUS_CACHE:
        return _CORPUS_CACHE[subject]

    path = _MATERIALS_DIR / f"{subject}_corpus.json"
    if not path.exists():
        print(f"[generators] AVISO: no encuentro corpus en {path}. "
              f"Ejecuta `python scripts/ingest_pdfs.py` para generarlo.")
        _CORPUS_CACHE[subject] = []
        return []

    try:
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)
    except Exception as e:
        print(f"[generators] ERROR cargando corpus {path}: {e}")
        _CORPUS_CACHE[subject] = []
        return []

    fragments = data.get("fragments", [])

    # Resumen de áreas si las hay
    areas = set(fr.get("area") for fr in fragments if fr.get("area"))
    area_info = f" · áreas: {sorted(areas)}" if areas else ""
    print(f"[generators] Corpus {subject!r}: {len(fragments)} fragmentos cargados{area_info}.")
    _CORPUS_CACHE[subject] = fragments
    return fragments


def pick_fragment(
    subject: str,
    source_hint: Optional[str] = None,
    area: Optional[str] = None,
) -> Optional[Dict[str, Any]]:
    """Selecciona un fragmento aleatorio del corpus.

    Args:
        subject: asignatura (clave del corpus).
        source_hint: substring que debe aparecer en `source` (nombre del PDF).
        area: si se pasa, restringe a fragmentos con ese campo `area`.

    El filtro es: PRIMERO se filtra por `area` (si se pasa), DESPUÉS por
    `source_hint` (si se pasa). Si después de filtrar no queda nada, hace
    fallback progresivo: prueba sin source_hint, y si tampoco hay, devuelve
    aleatorio del corpus entero.
    """
    corpus = load_corpus(subject)
    if not corpus:
        return None

    # 1) Filtro por área
    if area:
        filtered = [f for f in corpus if f.get("area") == area]
        if not filtered:
            # área pedida no tiene contenido — caemos al corpus entero
            print(f"[pick_fragment] área {area!r} sin fragmentos en {subject!r}, "
                  f"uso corpus completo")
            filtered = corpus
    else:
        filtered = corpus

    # 2) Filtro por source_hint
    if source_hint:
        narrowed = [f for f in filtered if source_hint.lower() in f["source"].lower()]
        if narrowed:
            return random.choice(narrowed)
        # source_hint sin matches: nos quedamos con el filtro de área únicamente.

    return random.choice(filtered)


# ──────────────────────────────────────────────────────────────────────────────
# VALIDADOR ANTI-LONGITUD
# ──────────────────────────────────────────────────────────────────────────────

LENGTH_ABS_DIFF_LIMIT = 12
LENGTH_RATIO_VS_RANGE = 1.35


def _length_check(challenge: Dict[str, Any]) -> Optional[str]:
    options = challenge.get("options", [])
    if len(options) != 4:
        return f"se esperaban 4 opciones, hay {len(options)}"

    correct_id = challenge.get("correct_answer_id")
    if not isinstance(correct_id, int) or not (0 <= correct_id <= 3):
        return f"correct_answer_id inválido: {correct_id}"

    word_counts = [len(opt.split()) for opt in options]
    correct_len = word_counts[correct_id]
    others = [w for i, w in enumerate(word_counts) if i != correct_id]
    if not others:
        return None

    others_mean = statistics.mean(others)
    others_max = max(others)
    others_min = min(others)
    abs_diff = correct_len - others_mean

    if abs_diff >= LENGTH_ABS_DIFF_LIMIT and \
       correct_len >= others_max * LENGTH_RATIO_VS_RANGE:
        return (f"la opción correcta tiene {correct_len} palabras frente a "
                f"{word_counts} (media de las otras: {others_mean:.0f}). "
                f"Se delata por ser claramente la más larga.")

    if -abs_diff >= LENGTH_ABS_DIFF_LIMIT and \
       correct_len > 0 and \
       others_min >= correct_len * LENGTH_RATIO_VS_RANGE:
        return (f"la opción correcta tiene solo {correct_len} palabras frente a "
                f"{word_counts} (media de las otras: {others_mean:.0f}). "
                f"Se delata por ser claramente la más corta.")

    overall_max = max(word_counts)
    overall_min = min(word_counts) or 1
    if overall_max >= overall_min * 3 and overall_max - overall_min >= LENGTH_ABS_DIFF_LIMIT:
        return (f"las opciones tienen longitudes muy desiguales: {word_counts}. "
                f"Iguálalas para que ninguna destaque.")

    return None


def _schema_check(challenge: Dict[str, Any]) -> Optional[str]:
    required = ["title", "options", "correct_answer_id", "explanation"]
    for f in required:
        if f not in challenge:
            return f"falta campo {f!r}"
    if not isinstance(challenge["title"], str) or not challenge["title"].strip():
        return "title vacío o no es string"
    if not isinstance(challenge["options"], list) or len(challenge["options"]) != 4:
        return "options debe ser lista de 4 strings"
    if not all(isinstance(o, str) and o.strip() for o in challenge["options"]):
        return "alguna opción está vacía o no es string"
    if not isinstance(challenge["correct_answer_id"], int) or not (0 <= challenge["correct_answer_id"] <= 3):
        return f"correct_answer_id fuera de [0,3]: {challenge['correct_answer_id']}"
    if not isinstance(challenge["explanation"], str) or len(challenge["explanation"]) < 30:
        return "explanation vacío o demasiado corto"
    return None


def call_openai(
    messages: List[Dict[str, str]],
    model: str = "gpt-4o-mini",
    temperature: float = 0.55,
    max_tokens: int = 1200,
) -> Dict[str, Any]:
    response = _client.chat.completions.create(
        model=model,
        messages=messages,
        response_format={"type": "json_object"},
        temperature=temperature,
        presence_penalty=0.4,
        frequency_penalty=0.3,
        max_tokens=max_tokens,
    )
    content = response.choices[0].message.content
    return json.loads(content)


MAX_REGEN_ATTEMPTS = 2


def generate_with_validation(
    build_messages: Callable[[], List[Dict[str, str]]],
    fallback: Dict[str, Any],
    model: str = "gpt-4o-mini",
    temperature: float = 0.55,
) -> Dict[str, Any]:
    messages = build_messages()
    last_error = None

    for attempt in range(1 + MAX_REGEN_ATTEMPTS):
        try:
            challenge = call_openai(messages, model=model, temperature=temperature)
        except Exception as e:
            print(f"[generate] intento {attempt+1}: error llamando a OpenAI: {e}")
            return fallback

        schema_err = _schema_check(challenge)
        if schema_err:
            print(f"[generate] intento {attempt+1}: esquema inválido ({schema_err})")
            last_error = schema_err
            if attempt < MAX_REGEN_ATTEMPTS:
                messages = messages + [
                    {"role": "assistant", "content": json.dumps(challenge, ensure_ascii=False)},
                    {"role": "user", "content": (
                        f"El JSON anterior no es válido: {schema_err}. "
                        f"Regenera la pregunta cumpliendo el formato exacto requerido."
                    )},
                ]
                continue
            break

        length_err = _length_check(challenge)
        if length_err:
            print(f"[generate] intento {attempt+1}: {length_err}")
            last_error = length_err
            if attempt < MAX_REGEN_ATTEMPTS:
                messages = messages + [
                    {"role": "assistant", "content": json.dumps(challenge, ensure_ascii=False)},
                    {"role": "user", "content": (
                        f"PROBLEMA con la pregunta anterior: {length_err}. "
                        f"Esto hace que se delate cuál es la correcta a simple vista. "
                        f"Regenera la pregunta IGUALANDO la longitud de las 4 opciones "
                        f"(diferencia máxima de ~10 palabras). "
                        f"Puedes acortar la correcta o alargar los distractores. "
                        f"Mantén la rigurosidad técnica."
                    )},
                ]
                continue
            break

        return challenge

    print(f"[generate] tras {1 + MAX_REGEN_ATTEMPTS} intentos sigue fallando "
          f"({last_error!r}). Devolviendo fallback.")
    return fallback


# ──────────────────────────────────────────────────────────────────────────────
# REGLAS COMUNES DE CALIDAD
# ──────────────────────────────────────────────────────────────────────────────

COMMON_RULES = """\
═══════════════════════════════════════════════════════════════════════════════
REGLAS COMUNES DE CALIDAD (OBLIGATORIAS PARA TODAS LAS PREGUNTAS)
═══════════════════════════════════════════════════════════════════════════════

1. IDIOMA: español neutro técnico universitario. Misma terminología que los
   apuntes (no inventes sinónimos raros).

2. CLARIDAD DEL ENUNCIADO:
   - El enunciado debe ser autocontenido.
   - Una sola interrogación clara. No preguntas dobles.
   - NO empieces con "Pregunta:" ni numeración tipo "1.".

3. **PARIDAD DE LONGITUD ENTRE OPCIONES (CRÍTICO)**:
   - Las 4 opciones deben tener LONGITUDES SIMILARES (diferencia máxima
     ~10 palabras entre la más corta y la más larga).
   - La opción correcta NO PUEDE ser visiblemente más larga ni más corta
     que las demás. Esto delata la respuesta.
   - Estrategia: redacta primero las 3 distractoras y ajusta la correcta
     a su mismo tamaño.

4. DISTRACTORES PLAUSIBLES:
   - Cada distractor debe ser un error REAL que cometería un estudiante.
   - Los 4 deben sonar igual de creíbles leídos en frío.
   - NO uses "ninguna de las anteriores" / "todas las anteriores".
   - NO empieces las opciones con a)/b)/c)/d) — eso lo añade la UI.

5. ROTACIÓN DE POSICIÓN DE LA RESPUESTA CORRECTA:
   - correct_answer_id debe distribuirse entre 0, 1, 2 y 3.

6. EXPLICACIÓN (campo explanation): 4-8 frases, didáctica.
   - Frase 1: "La respuesta correcta es la {LETRA}. {breve razón}".
   - Después: por qué cada distractor es incorrecto.

7. FORMATO DE SALIDA (JSON ESTRICTO):
{
  "title": "Enunciado completo",
  "options": ["...", "...", "...", "..."],
  "correct_answer_id": <0|1|2|3>,
  "explanation": "..."
}
"""


def build_context_block(fragment: Dict[str, Any]) -> str:
    src = fragment.get("source", "?")
    page = fragment.get("page_start", "?")
    text = fragment.get("text", "")
    area = fragment.get("area")
    area_tag = f" · área: {area}" if area else ""
    return (
        "═══════════════════════════════════════════════════════════════════════\n"
        f"FRAGMENTO LITERAL DEL TEMARIO (fuente: {src}, pág./diapo. {page}{area_tag})\n"
        "═══════════════════════════════════════════════════════════════════════\n"
        f"{text}\n"
        "═══════════════════════════════════════════════════════════════════════\n\n"
        "INSTRUCCIÓN: la pregunta que generes debe versar ESTRICTAMENTE sobre el "
        "contenido del fragmento anterior. NO introduzcas conceptos ni datos "
        "que no aparezcan ahí. Si el fragmento es corto o muy concreto, formula "
        "una pregunta de comprensión profunda sobre lo poco que dice. NO te "
        "inventes información complementaria del dominio general."
    )