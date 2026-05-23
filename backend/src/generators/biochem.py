"""
Generador de preguntas para Bioquímica y Biología Molecular (Tema 14-18).

Temario cubierto:
  Tema 14 — Replicación, reparación y recombinación del DNA
  Tema 15 — Transcripción
  Tema 16 — Traducción
  Tema 17 — Regulación génica
  Tema 18 — Introducción a la Ingeniería Genética
"""
import random
from typing import Dict, Any, List

from . import _common

SUBJECT = "biochem"


# Pistas por dificultad: forzamos coherencia entre nivel y tema.
# EASY → terminología y conceptos básicos (cualquier tema). MEDIUM →
# tema 15/16 (mecanismos). HARD → tema 17/18 (regulación, ingeniería).
DIFFICULTY_HINTS = {
    "easy":   [None, None, None, "Tema_14", "Tema_15", "Tema_16"],
    "medium": [None, None, "Tema_14", "Tema_15", "Tema_16", "Tema_17"],
    "hard":   [None, "Tema_14", "Tema_17", "Tema_18", "Tema_18"],
}


# ──────────────────────────────────────────────────────────────────────────────
# FEW-SHOT EXAMPLES (estilo universitario de Bioquímica)
# Diseñados con OPCIONES DE LONGITUDES SIMILARES para enseñar al modelo
# que la correcta no debe destacar por extensión.
# correct_answer_id distribuido entre 0,1,2,3.
# ──────────────────────────────────────────────────────────────────────────────

FEW_SHOT_EXAMPLES = [
    # ── correct_id = 2 — Tema 14 ──
    {
        "title": (
            "En la replicación del DNA en procariotas, ¿qué función específica "
            "desempeña la enzima DNA ligasa?"
        ),
        "options": [
            "Sintetizar los cebadores de RNA necesarios para que la DNA polimerasa III comience la elongación.",
            "Desenrollar la doble hélice por delante de la horquilla para facilitar el acceso de la polimerasa.",
            "Sellar las muescas formadas entre los fragmentos de Okazaki uniendo el extremo 3'-OH con el 5'-fosfato.",
            "Aliviar la tensión torsional generada en el DNA durante el avance de la horquilla de replicación.",
        ],
        "correct_answer_id": 2,
        "explanation": (
            "La respuesta correcta es la C. La DNA ligasa cataliza la formación del enlace "
            "fosfodiéster entre el extremo 3'-OH y el 5'-fosfato de fragmentos contiguos de "
            "DNA, sellando las muescas que quedan entre los fragmentos de Okazaki en la hebra "
            "retardada.\n\n"
            "A describe la primasa (RNA polimerasa que sintetiza cebadores). B describe la "
            "helicasa (desenrollado). D describe la topoisomerasa II o DNA girasa (alivio de "
            "tensión torsional). Son enzimas distintas con funciones complementarias."
        ),
    },
    # ── correct_id = 0 — Tema 15 ──
    {
        "title": (
            "En procariotas, la secuencia consenso TATAAT localizada aproximadamente "
            "en la posición -10 respecto al inicio de la transcripción recibe el nombre de:"
        ),
        "options": [
            "Caja de Pribnow, sitio reconocido por la holoenzima RNA polimerasa para iniciar la transcripción.",
            "Secuencia Shine-Dalgarno, sitio de unión del ribosoma para el inicio de la traducción del mRNA.",
            "Secuencia CAAT, elemento promotor habitual en genes eucariotas reconocido por factores específicos.",
            "Caja TATA eucariota, lugar de unión de la proteína TBP que recluta el complejo de transcripción.",
        ],
        "correct_answer_id": 0,
        "explanation": (
            "La respuesta correcta es la A. La caja de Pribnow (TATAAT, en -10) es un "
            "elemento clave del promotor procariota; junto con la región -35 (TTGACA), "
            "constituye el sitio que reconoce la holoenzima RNA polimerasa para iniciar la "
            "transcripción.\n\n"
            "B es la secuencia Shine-Dalgarno, pero pertenece al mRNA y se relaciona con la "
            "TRADUCCIÓN, no con la transcripción. C es un elemento de promotores EUCARIOTAS. "
            "D nombra la caja TATA eucariota: comparte secuencia parecida pero pertenece a "
            "otro contexto (eucariotas)."
        ),
    },
    # ── correct_id = 3 — Tema 16 ──
    {
        "title": (
            "El código genético se describe como «degenerado». ¿Qué significa "
            "exactamente esta propiedad?"
        ),
        "options": [
            "Que con el tiempo evolutivo el código sufre deterioro y aparecen lecturas alternativas erróneas.",
            "Que un mismo codón puede traducirse en aminoácidos distintos en función del contexto celular.",
            "Que existen codones sin asignación a ningún aminoácido y que no actúan como señal de parada.",
            "Que varios codones sinónimos pueden codificar el mismo aminoácido, ya que hay 61 codones para 20 aminoácidos.",
        ],
        "correct_answer_id": 3,
        "explanation": (
            "La respuesta correcta es la D. La degeneración del código genético significa "
            "que la mayoría de los 20 aminoácidos pueden ser codificados por más de un "
            "codón (codones sinónimos). De los 64 tripletes posibles, 61 codifican "
            "aminoácidos y 3 son codones de terminación.\n\n"
            "A confunde 'degenerado' con 'degradado'. B es falsa: el código NO es ambiguo "
            "— cada codón especifica un único aminoácido. C es incorrecta: todos los codones "
            "tienen función asignada (a un aminoácido o como STOP)."
        ),
    },
    # ── correct_id = 1 — Tema 17 ──
    {
        "title": (
            "En el operón lactosa de E. coli, ¿qué ocurre cuando hay lactosa "
            "disponible en el medio?"
        ),
        "options": [
            "La lactosa actúa como corepresor y refuerza la unión de la proteína represora al operador del operón.",
            "La lactosa actúa como inductor uniéndose al represor, lo cual impide que este se una al operador.",
            "La lactosa se une al promotor desplazando a la RNA polimerasa y bloqueando la transcripción del operón.",
            "La lactosa estimula la síntesis del represor activo, que se une al sitio operador inhibiendo la expresión.",
        ],
        "correct_answer_id": 1,
        "explanation": (
            "La respuesta correcta es la B. El operón lactosa es un sistema INDUCIBLE "
            "NEGATIVO: la proteína reguladora es un represor activo. En presencia de "
            "lactosa, esta actúa como inductor uniéndose al represor; el complejo "
            "represor-inductor pierde afinidad por el operador, queda libre, y los genes "
            "estructurales (lacZ, lacY, lacA) pueden transcribirse.\n\n"
            "A describe el modelo REPRIMIBLE (como el operón triptófano), no el inducible. "
            "C es falsa: la lactosa no interactúa con la RNA polimerasa. D invierte el "
            "mecanismo: la lactosa NO activa el represor, lo inactiva."
        ),
    },
    # ── correct_id = 0 — Tema 18 ──
    {
        "title": (
            "¿Qué característica esencial debe tener un vector de clonación para "
            "ser eficaz en la transferencia de DNA recombinante a una bacteria?"
        ),
        "options": [
            "Disponer de un origen de replicación funcional en la célula hospedadora, marcadores seleccionables y sitios de restricción únicos.",
            "Contener telómeros y un centrómero específicos de la cepa bacteriana receptora del vector recombinante.",
            "Llevar un promotor eucariota fuerte y al menos dos intrones en la región codificante del gen de interés.",
            "Estar formado exclusivamente por RNA monocatenario sintetizado por la enzima transcriptasa inversa.",
        ],
        "correct_answer_id": 0,
        "explanation": (
            "La respuesta correcta es la A. Un vector de clonación eficaz necesita tres "
            "cosas: (1) origen de replicación reconocible por la maquinaria del hospedador, "
            "para que se replique dentro de él; (2) marcadores seleccionables (típicamente "
            "genes de resistencia a antibióticos) para identificar las células que han "
            "incorporado el vector; y (3) sitios de restricción únicos donde insertar el "
            "fragmento de DNA de interés.\n\n"
            "B describe los YACs (cromosomas artificiales de levadura), no vectores "
            "bacterianos. C es propio de la expresión en sistemas eucariotas y los intrones "
            "no pertenecen al vector. D es incorrecta: los vectores estándar son DNA "
            "bicatenario, no RNA monocatenario."
        ),
    },
]


# ──────────────────────────────────────────────────────────────────────────────
# SYSTEM PROMPT
# ──────────────────────────────────────────────────────────────────────────────

SYSTEM_PROMPT_HEAD = """\
Eres profesor universitario de Bioquímica y Biología Molecular y diseñador \
experto de preguntas tipo test para exámenes universitarios. Tu trabajo es \
generar UNA pregunta de examen siguiendo el estilo de un examen final de \
Bioquímica de grado en Ciencias de la Salud.

═══════════════════════════════════════════════════════════════════════════════
TEMARIO OFICIAL (Temas 14-18 de Bioquímica y Biología Molecular)
═══════════════════════════════════════════════════════════════════════════════

TEMA 14 — Replicación, reparación y recombinación del DNA
  Características de la replicación (semiconservativa, bidireccional,
  semidiscontinua). DNA polimerasas (I, III). Horquilla de replicación.
  Hebra conductora vs hebra retardada. Fragmentos de Okazaki. Enzimas:
  helicasa, primasa, topoisomerasa II/DNA girasa, DNA ligasa, proteínas
  de unión a ssDNA. Iniciación (DnaA en E. coli). Recombinación
  homóloga. Mutaciones espontáneas (desaminaciones, alineamiento
  incorrecto). Mecanismos de reparación: escisión de base, escisión de
  nucleótidos, reparación de apareamientos erróneos (MutS/MutL/MutH),
  reparación directa, reparación de rotura bicatenaria. Telomerasa y
  retrotranscriptasa.

TEMA 15 — Transcripción
  RNA polimerasa procariota (subunidades α₂ββ'ω + σ). Promotores en
  procariotas: caja de Pribnow (-10, TATAAT) y región -35 (TTGACA).
  Etapas: iniciación (formación de la burbuja de transcripción),
  elongación, terminación (rho-dependiente vs rho-independiente).
  Transcripción en eucariotas: tres RNA polimerasas (I, II, III).
  Factores de transcripción generales (TBP, TFIID, etc.). Cromatina,
  nucleosomas, factores de remodelación. Procesamiento del pre-mRNA:
  caperuza 5', poliadenilación 3', splicing.

TEMA 16 — Traducción
  Código genético: tripletes, 64 codones (61 codifican + 3 STOP: UAG,
  UAA, UGA). Propiedades: universal, sin solapamiento, no ambiguo,
  degenerado, unidireccional 5'→3'. Codón de iniciación AUG. tRNA:
  estructura en trébol, brazo aceptor (CCA), anticodón. Aminoacil-tRNA
  sintetasas (1 por aminoácido). Ribosoma procariota (70S = 30S + 50S);
  sitios A, P, E. Etapas: iniciación (Shine-Dalgarno, fMet-tRNA, IF1/2/3),
  elongación (EF-Tu, EF-G, peptidil transferasa), terminación (RF-1/2/3).
  Diferencias procariotas vs eucariotas en factores de iniciación.

TEMA 17 — Regulación génica
  PROCARIOTAS: control mayoritariamente transcripcional. Operón
  (genes agrupados bajo un único promotor). Operones inducibles vs
  reprimibles. Control negativo (represor) vs positivo (activador).
  Operón LACTOSA: inducible negativo. La lactosa es inductor, se une al
  represor y lo inactiva → genes estructurales se transcriben.
  Operón TRIPTÓFANO: reprimible negativo. El triptófano es corepresor,
  activa al represor → genes NO se transcriben.
  EUCARIOTAS: control en múltiples niveles. Remodelación de cromatina,
  metilación de DNA, modificación de histonas. Factores de transcripción
  basales, reguladores (activadores/represores), intensificadores
  (enhancers), aisladores. Procesamiento del mRNA, estabilidad,
  interferencia por RNA (miRNA, siRNA).

TEMA 18 — Introducción a la Ingeniería Genética
  DNA recombinante. Enzimas de restricción tipo II: reconocimiento de
  secuencias palindrómicas (4-8 nt), extremos cohesivos vs romos.
  Nomenclatura (EcoRI, BamHI, HindIII…). Vectores de clonación:
  plásmidos (pBR322), BACs, YACs. Características esenciales: ori,
  marcadores seleccionables, sitios de restricción únicos.
  Transformación, identificación de células transformantes.
  PCR (Mullis 1983): desnaturalización (95°C), alineamiento (~55°C),
  extensión (72°C) con Taq polimerasa. Limitaciones (sin corrección,
  <2kb). Aplicaciones (diagnóstico, forense, paternidad).
  RT-PCR (cDNA desde mRNA con retrotranscriptasa). CRISPR/Cas9: sgRNA
  + Cas9; edición genómica (knockout, knockin).
"""


def _build_messages(difficulty: str) -> List[Dict[str, str]]:
    diff = difficulty.lower()
    if diff not in DIFFICULTY_HINTS:
        diff = "easy"

    hint = random.choice(DIFFICULTY_HINTS[diff])
    fragment = _common.pick_fragment(SUBJECT, source_hint=hint)

    system_prompt = SYSTEM_PROMPT_HEAD + "\n" + _common.COMMON_RULES

    msgs: List[Dict[str, str]] = [{"role": "system", "content": system_prompt}]

    for ex in random.sample(FEW_SHOT_EXAMPLES, k=2):
        msgs.append({"role": "user", "content": "Genera una pregunta de ejemplo."})
        msgs.append({"role": "assistant", "content": _dump_json(ex)})

    user_msg = (
        f"Genera UNA pregunta tipo test de dificultad **{diff.upper()}**.\n\n"
    )
    if fragment:
        user_msg += _common.build_context_block(fragment) + "\n\n"
    else:
        user_msg += (
            "(Aviso interno: no hay corpus cargado; basa la pregunta en el "
            "temario descrito en el system prompt.)\n\n"
        )
    user_msg += (
        "RECUERDA: las 4 opciones deben tener longitudes parecidas; la "
        "correcta NO puede ser visiblemente más larga ni más corta que las "
        "demás. Distribuye aleatoriamente la posición de la correcta entre "
        "0, 1, 2 y 3. Devuelve solo el JSON con title/options/"
        "correct_answer_id/explanation."
    )
    msgs.append({"role": "user", "content": user_msg})
    return msgs


def _dump_json(obj: Dict[str, Any]) -> str:
    import json
    return json.dumps(obj, ensure_ascii=False)


FALLBACK = {
    "title": (
        "En la replicación semidiscontinua del DNA en procariotas, "
        "¿qué propiedad de la DNA polimerasa explica que la hebra retardada "
        "se sintetice en fragmentos (fragmentos de Okazaki) en vez de "
        "continuamente como la hebra conductora?"
    ),
    "options": [
        "Que la DNA polimerasa solo es capaz de extender una cadena nueva en dirección 5' hacia 3'.",
        "Que la DNA polimerasa necesita primero degradar las histonas antes de polimerizar la hebra molde.",
        "Que la DNA polimerasa requiere ATP libre y no tolera la presencia de pirofosfato durante la elongación.",
        "Que la DNA polimerasa sintetiza simultáneamente las dos hebras en sentido contrario al avance de la horquilla.",
    ],
    "correct_answer_id": 0,
    "explanation": (
        "La respuesta correcta es la A. La DNA polimerasa solo cataliza la adición de "
        "nucleótidos al extremo 3'-OH de la cadena en crecimiento, por lo que la síntesis "
        "siempre ocurre en sentido 5'→3'. Como las dos hebras del DNA son antiparalelas, "
        "la conductora (que apunta en el sentido de avance de la horquilla) puede sintetizarse "
        "de manera continua, pero la retardada debe hacerse en fragmentos cortos (Okazaki) "
        "que luego se unen.\n\n"
        "B es falsa: las histonas son proteínas eucariotas y no participan en este proceso "
        "procariota. C invierte la realidad: la energía proviene de la hidrólisis del "
        "pirofosfato. D es errónea: la simultaneidad no implica continuidad."
    ),
}


def generate(difficulty: str) -> Dict[str, Any]:
    return _common.generate_with_validation(
        build_messages=lambda: _build_messages(difficulty),
        fallback=FALLBACK,
    )