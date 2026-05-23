"""
Helpers compartidos por todos los generadores (PER, biochem, futuros).

Funcionalidad común:
─────────────────────
1. Carga del corpus de fragmentos (PDFs ya procesados por scripts/ingest_pdfs.py)
2. Selección de un fragmento aleatorio, opcionalmente filtrado por tema/PDF
3. Validador anti-longitud (que la respuesta correcta no destaque por extensión)
4. Wrapper de llamada a OpenAI con reintentos para regeneración
5. Esquema canónico del challenge: title / options[4] / correct_answer_id / explanation
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

# Ruta absoluta a la carpeta materials/, calculada desde la posición de
# este archivo (backend/src/generators/_common.py → backend/materials/)
_MATERIALS_DIR = Path(__file__).resolve().parent.parent.parent / "materials"


def load_corpus(subject: str) -> List[Dict[str, Any]]:
    """Carga (con caché) el corpus de fragmentos de una asignatura.

    Devuelve [] si no se encuentra el corpus; el generador caerá a sus
    ejemplos few-shot pero seguirá funcionando.
    """
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
    print(f"[generators] Corpus {subject!r}: {len(fragments)} fragmentos cargados.")
    _CORPUS_CACHE[subject] = fragments
    return fragments


def pick_fragment(
    subject: str,
    source_hint: Optional[str] = None,
) -> Optional[Dict[str, Any]]:
    """Selecciona un fragmento aleatorio del corpus.

    Si se pasa source_hint, prioriza fragmentos cuyo `source` (nombre del
    PDF original) contenga esa cadena. Útil para forzar un tema concreto:
    pick_fragment("biochem", source_hint="Tema_15")  → solo transcripción.
    """
    corpus = load_corpus(subject)
    if not corpus:
        return None

    if source_hint:
        candidates = [f for f in corpus if source_hint.lower() in f["source"].lower()]
        if candidates:
            return random.choice(candidates)
        # Si el hint no matchea nada, caemos a aleatorio general.

    return random.choice(corpus)


# ──────────────────────────────────────────────────────────────────────────────
# VALIDADOR Y REGENERADOR
# ──────────────────────────────────────────────────────────────────────────────

# Umbrales del validador anti-longitud:
#
# La intuición: una respuesta correcta "delata" cuando, leyendo solo las 4
# opciones, una destaca a simple vista por ser MUY distinta en longitud
# respecto al resto. Para detectarlo robustamente miramos:
#
#  1) Que la diferencia ABSOLUTA en palabras entre la correcta y la media
#     de las otras sea grande (>= ABS_DIFF), Y
#  2) Que la correcta esté fuera del rango [min(otras)*X, max(otras)/X]
#     definido por las propias distractoras (RATIO_VS_RANGE).
#
# Esto evita falsos positivos cuando todas las opciones son cortas
# (3-4-5-6 palabras: el ratio sube pero la diferencia absoluta es pequeña)
# y también cuando todas son largas y la correcta solo lleva un par
# de palabras extra.
LENGTH_ABS_DIFF_LIMIT = 12    # 12+ palabras de diferencia con la media
LENGTH_RATIO_VS_RANGE = 1.35  # 35% por encima del MAX o por debajo del MIN


def _length_check(challenge: Dict[str, Any]) -> Optional[str]:
    """Devuelve None si pasa, o una explicación del problema."""
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

    # ── Caso A: la correcta es notablemente más larga ──
    if abs_diff >= LENGTH_ABS_DIFF_LIMIT and \
       correct_len >= others_max * LENGTH_RATIO_VS_RANGE:
        return (f"la opción correcta tiene {correct_len} palabras frente a "
                f"{word_counts} (media de las otras: {others_mean:.0f}). "
                f"Se delata por ser claramente la más larga.")

    # ── Caso B: la correcta es notablemente más corta ──
    if -abs_diff >= LENGTH_ABS_DIFF_LIMIT and \
       correct_len > 0 and \
       others_min >= correct_len * LENGTH_RATIO_VS_RANGE:
        return (f"la opción correcta tiene solo {correct_len} palabras frente a "
                f"{word_counts} (media de las otras: {others_mean:.0f}). "
                f"Se delata por ser claramente la más corta.")

    # ── Caso C: cualquier opción individual descuadra demasiado (no solo la
    #             correcta). Si una opción es 3× más larga que cualquier
    #             otra, la pregunta está mal formada aunque la "rara" no
    #             sea la correcta — porque hace evidente cuál descartar
    #             primero. ──
    overall_max = max(word_counts)
    overall_min = min(word_counts) or 1
    if overall_max >= overall_min * 3 and overall_max - overall_min >= LENGTH_ABS_DIFF_LIMIT:
        return (f"las opciones tienen longitudes muy desiguales: {word_counts}. "
                f"Iguálalas para que ninguna destaque.")

    return None


def _schema_check(challenge: Dict[str, Any]) -> Optional[str]:
    """Validación estructural del JSON devuelto por el modelo."""
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
    """Llama a OpenAI con response_format json_object y devuelve el dict parseado.

    Lanza excepción si falla el parseo o la llamada.
    """
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


# Cuántas veces como máximo regeneramos si la longitud se delata.
# Cada reintento añade un mensaje al modelo explicándole qué falló.
MAX_REGEN_ATTEMPTS = 2


def generate_with_validation(
    build_messages: Callable[[], List[Dict[str, str]]],
    fallback: Dict[str, Any],
    model: str = "gpt-4o-mini",
    temperature: float = 0.55,
) -> Dict[str, Any]:
    """Bucle de generación + validación + regeneración.

    Args:
        build_messages: callable que devuelve la lista de mensajes
                        (incluyendo system + few-shot + petición). Se llama
                        cada vez que regeneramos para permitir variar el
                        contexto.
        fallback: challenge a devolver si TODO falla.

    Política:
        1. Generar.
        2. Validar esquema. Si falla → reintento con mensaje correctivo.
        3. Validar longitud. Si falla → reintento explicando el problema.
        4. Si tras MAX_REGEN_ATTEMPTS sigue fallando, devolver fallback.
    """
    messages = build_messages()
    last_error = None

    for attempt in range(1 + MAX_REGEN_ATTEMPTS):
        try:
            challenge = call_openai(messages, model=model, temperature=temperature)
        except Exception as e:
            print(f"[generate] intento {attempt+1}: error llamando a OpenAI: {e}")
            # En errores de red/API NO regeneramos: caemos al fallback
            # para no encadenar fallos.
            return fallback

        # 1) Esquema
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

        # 2) Longitud
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
                        f"(diferencia máxima de ~10 palabras entre la más corta y la más larga). "
                        f"Puedes acortar la correcta o alargar los distractores con razonamiento "
                        f"plausible. Mantén la rigurosidad técnica."
                    )},
                ]
                continue
            break

        # Todo OK
        return challenge

    print(f"[generate] tras {1 + MAX_REGEN_ATTEMPTS} intentos sigue fallando "
          f"({last_error!r}). Devolviendo fallback.")
    return fallback


# ──────────────────────────────────────────────────────────────────────────────
# UTILIDADES PARA CONSTRUIR PROMPTS
# ──────────────────────────────────────────────────────────────────────────────

# Esta sección de reglas la comparten TODOS los generadores: redacción
# anti-longitud, formato JSON, etc. Cada asignatura añade encima sus
# reglas propias de contenido.

COMMON_RULES = """\
═══════════════════════════════════════════════════════════════════════════════
REGLAS COMUNES DE CALIDAD (OBLIGATORIAS PARA TODAS LAS PREGUNTAS)
═══════════════════════════════════════════════════════════════════════════════

1. IDIOMA: español neutro técnico universitario. Misma terminología que los
   apuntes (no inventes sinónimos raros).

2. CLARIDAD DEL ENUNCIADO:
   - El enunciado debe ser autocontenido: leyéndolo solo (sin ver opciones)
     un estudiante debe entender qué se le pregunta exactamente.
   - Si la pregunta se refiere a un fragmento de código/secuencia/figura,
     inclúyelo dentro del enunciado.
   - Una sola interrogación clara. No preguntas dobles.
   - NO empieces con "Pregunta:" ni numeración tipo "1.".

3. **PARIDAD DE LONGITUD ENTRE OPCIONES (CRÍTICO)**:
   - Las 4 opciones deben tener LONGITUDES SIMILARES (mismo número de
     palabras aproximadamente; diferencia máxima ~10 palabras entre la
     más corta y la más larga).
   - La opción correcta NO PUEDE ser visiblemente más larga ni más corta
     que las demás. Esto delata la respuesta y arruina la pregunta.
   - Estrategia: redacta primero las 3 distractoras con un contenido
     técnico plausible, y luego ajusta la correcta a su mismo tamaño.

4. DISTRACTORES PLAUSIBLES (no absurdos):
   - Cada distractor debe ser un error REAL que cometería un estudiante:
     confundir conceptos parecidos, invertir una relación, mezclar
     términos relacionados.
   - Los 4 deben sonar igual de "creíbles" leídos en frío.
   - NO uses opciones tipo "ninguna de las anteriores" o "todas las
     anteriores" salvo que aporten pedagógicamente.
   - NO empieces las opciones con letras (a), b), c)) — eso lo añade la UI.

5. ROTACIÓN DE POSICIÓN DE LA RESPUESTA CORRECTA:
   - correct_answer_id debe distribuirse aleatoriamente entre 0, 1, 2 y 3.
   - NO uses siempre la última posición (un error frecuente).

6. EXPLICACIÓN PEDAGÓGICA (campo explanation):
   - 4-8 frases, didáctica.
   - Frase 1: "La respuesta correcta es la {LETRA}. {breve razón}".
   - Después: por qué cada distractor es incorrecto, citando el concepto
     que el estudiante podría haber confundido.
   - Si hay código o secuencia, traza qué ocurre paso a paso.

7. FORMATO DE SALIDA (JSON ESTRICTO, sin texto fuera, sin markdown):
{
  "title": "Enunciado completo (puede usar \\n para saltos de línea)",
  "options": ["...", "...", "...", "..."],
  "correct_answer_id": <0|1|2|3>,
  "explanation": "..."
}
"""


def build_context_block(fragment: Dict[str, Any]) -> str:
    """Convierte un fragmento del corpus en un bloque de contexto para el prompt."""
    src = fragment.get("source", "?")
    page = fragment.get("page_start", "?")
    text = fragment.get("text", "")
    return (
        "═══════════════════════════════════════════════════════════════════════\n"
        f"FRAGMENTO LITERAL DEL TEMARIO (fuente: {src}, pág./diapo. {page})\n"
        "═══════════════════════════════════════════════════════════════════════\n"
        f"{text}\n"
        "═══════════════════════════════════════════════════════════════════════\n\n"
        "INSTRUCCIÓN: la pregunta que generes debe versar ESTRICTAMENTE sobre el "
        "contenido del fragmento anterior. NO introduzcas conceptos ni datos "
        "que no aparezcan ahí. Si el fragmento es corto o muy concreto, formula "
        "una pregunta de comprensión profunda sobre lo poco que dice. NO te "
        "inventes información complementaria del dominio general."
    )