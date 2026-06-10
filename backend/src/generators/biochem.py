"""
Generador de preguntas para Bioquímica y Biología Molecular.

Cubre DOS subáreas con catálogos separados:

  • GENÉTICA MOLECULAR (Temas 14-18)
      14 Replicación, reparación y recombinación del DNA
      15 Transcripción
      16 Traducción
      17 Regulación génica
      18 Introducción a la Ingeniería Genética

  • METABOLISMO (Temas 10-13 + ciclo TCA + hidratos)
      Introducción al metabolismo (termodinámica, ATP, regulación)
      Metabolismo oxidativo (cadena respiratoria)
      Ciclo de Krebs / ácidos tricarboxílicos
      Metabolismo de hidratos de carbono (glucólisis, pentosas)
      Anabolismo de hidratos (gluconeogénesis, glucógeno)
      Catabolismo de lípidos (β-oxidación)
      Biosíntesis lipídica
      Metabolismo del nitrógeno (aminoácidos, urea)
      Integración del metabolismo

ESTILO: los few-shots están calcados del estilo de exámenes wooclap
del profesor, que se caracteriza por:
  - Enunciados breves y directos.
  - Mezcla de opciones de 1 palabra (nombres de moléculas) y opciones
    largas (~15-25 palabras) con estructura paralela.
  - Uso ocasional de "Todas son verdaderas" / "Todas son falsas"
    como opción real.
  - Preguntas en NEGATIVO ("¿Cuál NO clasificarías como...?").
  - Razonamientos experimentales ("Imagine una cepa que no puede
    sintetizar X, prediga...").
"""
import random
from typing import Dict, Any, List, Optional

from . import _common

SUBJECT = "biochem"
AREAS = ("metabolismo", "genetica")


# ──────────────────────────────────────────────────────────────────────────────
# Pistas por área y dificultad
# Cada lista es de source_hints (substrings del nombre del PDF). El generador
# elige uno al azar para sesgar la selección.
# ──────────────────────────────────────────────────────────────────────────────

DIFFICULTY_HINTS = {
    "genetica": {
        "easy":   [None, None, None, "Tema_14", "Tema_15", "Tema_16"],
        "medium": [None, None, "Tema_14", "Tema_15", "Tema_16", "Tema_17"],
        "hard":   [None, "Tema_14", "Tema_17", "Tema_18", "Tema_18"],
    },
    "metabolismo": {
        "easy": [
            None, None, None,
            "Introducción_al_Metabolismo",
            "Metabolismo_de_hidratos",
            "Metabolismo_Oxidativo",
            "Ciclo_de_los",
        ],
        "medium": [
            None, None,
            "Anabolismo_Hidratos",
            "Catabolismo_lipidos",
            "Metabolismo_Oxidativo",
            "Metabolismo_lipídico",
            "Metabolismo_de_hidratos",
            "Ciclo_de_los",
        ],
        "hard": [
            None,
            "Metabolismo_del_Nitrógeno",
            "Integración",
            "Anabolismo_Hidratos",
            "TEMA_11b",
            "Tema_13",
        ],
    },
}


# ──────────────────────────────────────────────────────────────────────────────
# FEW-SHOT EXAMPLES (GENÉTICA) — sin cambios respecto a versión anterior
# ──────────────────────────────────────────────────────────────────────────────

FEW_SHOTS_GENETICA = [
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
            "helicasa (desenrollado). D describe la topoisomerasa II o DNA girasa."
        ),
    },
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
            "B es la secuencia Shine-Dalgarno (mRNA, traducción). C y D pertenecen a "
            "promotores eucariotas."
        ),
    },
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
            "A confunde 'degenerado' con 'degradado'. B es falsa: el código NO es ambiguo. "
            "C es incorrecta: todos los codones tienen función asignada (aminoácido o STOP)."
        ),
    },
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
            "lactosa, esta se une al represor; el complejo represor-inductor pierde "
            "afinidad por el operador y los genes estructurales se transcriben.\n\n"
            "A describe el modelo REPRIMIBLE (como el operón triptófano). C es falsa. "
            "D invierte el mecanismo."
        ),
    },
]


# ──────────────────────────────────────────────────────────────────────────────
# FEW-SHOT EXAMPLES (METABOLISMO) — calcados del estilo wooclap del profe
#
# Diversificamos los patrones para enseñar al modelo el repertorio completo:
#  • Pregunta directa de identificación con opciones cortas (1-3 palabras)
#  • Pregunta NEGATIVA ("¿Cuál NO...?")
#  • Opciones largas con estructura paralela y cambios sutiles
#  • Uso de "Todas son verdaderas/falsas" como opción real
#  • Razonamiento experimental ("imagina una cepa...")
#
# correct_answer_id distribuido entre 0, 1, 2 y 3 para evitar sesgos.
# ──────────────────────────────────────────────────────────────────────────────

FEW_SHOTS_METABOLISMO = [
    # ── 1. Opciones cortas, oveja negra ──
    {
        "title": "¿Cuál de las siguientes moléculas se considera un segundo mensajero intracelular?",
        "options": [
            "Glucagón",
            "Adrenalina",
            "Diacilglicerol",
            "Insulina",
        ],
        "correct_answer_id": 2,
        "explanation": (
            "La respuesta correcta es la C. El diacilglicerol (DAG) es un segundo mensajero "
            "intracelular generado por la fosfolipasa C a partir del PIP2. Activa la "
            "proteína quinasa C dentro de la célula.\n\n"
            "Glucagón, adrenalina e insulina son hormonas (mensajeros primarios) que circulan "
            "por la sangre y se unen a receptores en la superficie celular o intracelulares. "
            "No son segundos mensajeros."
        ),
    },
    # ── 2. Opciones cortas, "Cuál NO..." ──
    {
        "title": "¿Cuál de las siguientes hormonas posee un receptor INTRACELULAR (no de membrana)?",
        "options": [
            "Adrenalina",
            "Glucagón",
            "Insulina",
            "Estradiol",
        ],
        "correct_answer_id": 3,
        "explanation": (
            "La respuesta correcta es la D. El estradiol, como el resto de hormonas esteroideas, "
            "es lipófilo y atraviesa la membrana plasmática para unirse a un receptor "
            "intracelular (nuclear) que actúa como factor de transcripción.\n\n"
            "Adrenalina y glucagón son hidrófilas y se unen a receptores de membrana acoplados "
            "a proteína G. La insulina también tiene receptor de membrana (tirosina quinasa). "
            "Solo las hormonas lipófilas (esteroideas, tiroideas) tienen receptores intracelulares."
        ),
    },
    # ── 3. Opciones largas con estructura paralela (estilo "cinética enzimática") ──
    {
        "title": "En una reacción catalizada enzimáticamente, en comparación con la misma reacción no catalizada:",
        "options": [
            "La diferencia de energía libre entre sustratos y productos se incrementa, acelerando así la reacción.",
            "La energía de activación necesaria para alcanzar el estado de transición se reduce, por lo que la reacción es más rápida.",
            "La energía libre necesaria para alcanzar el estado de transición se incrementa, lo que facilita la reacción.",
            "Se iguala la energía de activación con la energía libre de los sustratos produciendo que se favorezca la reacción.",
        ],
        "correct_answer_id": 1,
        "explanation": (
            "La respuesta correcta es la B. Las enzimas aceleran las reacciones reduciendo "
            "la energía de activación (Ea) — la barrera energética del estado de transición — "
            "sin alterar la termodinámica global del proceso.\n\n"
            "A es falsa: la enzima NO cambia el ΔG entre sustratos y productos, que es una "
            "propiedad termodinámica. C invierte el efecto (incrementar la Ea ralentizaría "
            "la reacción). D mezcla términos sin sentido fisicoquímico."
        ),
    },
    # ── 4. Razonamiento experimental ──
    {
        "title": (
            "Imagine una cepa de ratones que no puede sintetizar glucagón. "
            "¿Cuál sería la predicción más razonable para estos ratones mutantes en condiciones de ayuno?"
        ),
        "options": [
            "Tendrán hiperglucemia marcada por activación constante de la glucogenólisis hepática.",
            "Tendrán altas reservas de glucógeno en el hígado por falta de activación de la glucogenólisis.",
            "Su músculo esquelético ahorrará toda la energía disponible activando la gluconeogénesis.",
            "Las dos primeras opciones son correctas y describen el fenotipo simultáneamente.",
        ],
        "correct_answer_id": 1,
        "explanation": (
            "La respuesta correcta es la B. El glucagón activa la glucogenólisis hepática "
            "vía cascada PKA (fosforila y activa la glucógeno fosforilasa). Sin glucagón, esa "
            "vía está silenciada en ayuno y el glucógeno hepático no se moviliza, por lo que "
            "se acumula.\n\n"
            "A es falsa: sin glucagón la glucogenólisis está INHIBIDA, no activada, así que "
            "habría hipoglucemia. C es falsa: el músculo no realiza gluconeogénesis (le falta "
            "glucosa 6-fosfatasa) y además el glucagón apenas actúa sobre miocitos. D es falsa "
            "por las razones anteriores."
        ),
    },
    # ── 5. "Todas son verdaderas" como correcta (patrón del profe) ──
    # Nota: aquí "Todas son verdaderas" va en POSICIÓN 0 (no al final) para
    # equilibrar la distribución de correct_answer_id en el conjunto.
    {
        "title": "Respecto a los moduladores alostéricos en el control del metabolismo, ¿qué afirmación es correcta?",
        "options": [
            "Todas las afirmaciones siguientes son correctas y pueden darse simultáneamente.",
            "Regulan muchas enzimas situadas a la entrada de vías metabólicas (enzimas reguladoras).",
            "Permiten ajustar la actividad de algunas vías en función de la disponibilidad de energía.",
            "El producto final de una vía puede actuar como modulador alostérico negativo de su propia vía.",
        ],
        "correct_answer_id": 0,
        "explanation": (
            "La respuesta correcta es la A. Las tres afirmaciones B, C y D describen "
            "propiedades reales de la regulación alostérica:\n\n"
            "B es cierta: las enzimas alostéricas suelen catalizar pasos limitantes al inicio "
            "de las vías. C es cierta: ATP, ADP, NADH, etc. modulan enzimas clave según el "
            "estado energético. D es cierta: la retroinhibición por producto final es un "
            "mecanismo regulador clásico (feedback negativo). Como todas son correctas, la "
            "opción A es la respuesta."
        ),
    },
    # ── 6. Identificación clásica de enzima/función con opciones medias ──
    {
        "title": (
            "En la gluconeogénesis hepática, ¿qué papel desempeña la enzima "
            "fructosa 1,6-bisfosfatasa?"
        ),
        "options": [
            "Cataliza la hidrólisis de fructosa 1,6-bisfosfato a fructosa 6-fosfato, sorteando la PFK-1 glucolítica.",
            "Fosforila la fructosa 6-fosfato a fructosa 1,6-bisfosfato consumiendo un ATP en la primera etapa.",
            "Convierte el piruvato citosólico en oxalacetato dentro de la mitocondria como paso inicial.",
            "Transforma la glucosa 6-fosfato en glucosa libre en el retículo endoplásmico del hepatocito.",
        ],
        "correct_answer_id": 0,
        "explanation": (
            "La respuesta correcta es la A. La fructosa 1,6-bisfosfatasa es una de las tres "
            "enzimas exclusivas de la gluconeogénesis: hidroliza fructosa 1,6-bisfosfato a "
            "fructosa 6-fosfato, sorteando el paso irreversible que en la glucólisis cataliza "
            "la fosfofructoquinasa-1 (PFK-1).\n\n"
            "B describe la PFK-1 (glucólisis, sentido contrario). C describe la piruvato "
            "carboxilasa. D describe la glucosa 6-fosfatasa (paso final de gluconeogénesis)."
        ),
    },
    # ── 7. Ciclo de Krebs ──
    {
        "title": (
            "Por cada molécula de acetil-CoA que entra en el ciclo de los ácidos "
            "tricarboxílicos, ¿cuántos NADH se generan?"
        ),
        "options": [
            "Solo 1 NADH, en el paso catalizado por la malato deshidrogenasa.",
            "2 NADH, uno en isocitrato deshidrogenasa y otro en α-cetoglutarato deshidrogenasa.",
            "3 NADH, en isocitrato, α-cetoglutarato y malato deshidrogenasas.",
            "4 NADH, contando además la oxidación previa del piruvato a acetil-CoA.",
        ],
        "correct_answer_id": 2,
        "explanation": (
            "La respuesta correcta es la C. El balance del ciclo por cada acetil-CoA que entra "
            "es: 3 NADH (isocitrato deshidrogenasa, α-cetoglutarato deshidrogenasa y malato "
            "deshidrogenasa), 1 FADH₂ (succinato deshidrogenasa) y 1 GTP/ATP (succinil-CoA "
            "sintetasa). Se liberan también 2 CO₂.\n\n"
            "A y B subestiman el número de pasos redox del ciclo. D incluye el NADH del "
            "complejo PDH, que es PREVIO al ciclo (no forma parte de él)."
        ),
    },
    # ── 8. "Todas son falsas" como correcta ──
    {
        "title": (
            "Los moduladores alostéricos covalentes (como la fosforilación) actúan sobre las "
            "enzimas diana. ¿Cuál de las siguientes descripciones es correcta?"
        ),
        "options": [
            "Fosforilan la enzima provocando siempre un aumento de la transformación de sustrato en producto.",
            "Fosforilan la enzima provocando siempre una disminución de la transformación del sustrato en producto.",
            "Fosforilan la enzima provocando siempre una activación irreversible que no se revierte por fosfatasa.",
            "Todas las afirmaciones anteriores son falsas.",
        ],
        "correct_answer_id": 3,
        "explanation": (
            "La respuesta correcta es la D. La fosforilación puede activar O inhibir la enzima "
            "según cada caso concreto (la glucógeno fosforilasa se activa al fosforilarse, "
            "la glucógeno sintasa se inactiva). Por tanto NO es válido afirmar que 'siempre' "
            "aumenta o 'siempre' disminuye la actividad. Además, la fosforilación es reversible "
            "(las fosfatasas la revierten).\n\n"
            "A y B son falsas por su carácter absoluto. C es falsa porque la fosforilación es "
            "REVERSIBLE."
        ),
    },
]


# ──────────────────────────────────────────────────────────────────────────────
# SYSTEM PROMPTS POR ÁREA
# ──────────────────────────────────────────────────────────────────────────────

SYSTEM_PROMPT_GENETICA = """\
Eres profesor universitario de Bioquímica y Biología Molecular en una facultad \
de Ciencias de la Salud (URJC). Diseñas preguntas tipo test al estilo de los \
exámenes oficiales y de los cuestionarios wooclap usados en clase.

═══════════════════════════════════════════════════════════════════════════════
ÁREA: GENÉTICA MOLECULAR (Temas 14-18)
═══════════════════════════════════════════════════════════════════════════════

TEMA 14 — Replicación, reparación y recombinación del DNA
  Replicación semiconservativa, bidireccional, semidiscontinua. DNA
  polimerasas (I, III). Horquilla de replicación. Hebra conductora vs
  retardada. Fragmentos de Okazaki. Enzimas: helicasa, primasa,
  topoisomerasa II/DNA girasa, DNA ligasa, SSB. Recombinación homóloga.
  Reparación: escisión de base, escisión de nucleótidos, apareamientos
  erróneos (MutS/MutL/MutH), doble cadena. Telomerasa.

TEMA 15 — Transcripción
  RNA polimerasa procariota (α₂ββ'ω + σ). Promotores: caja Pribnow (-10),
  región -35. Iniciación, elongación, terminación. Eucariotas: tres RNA
  polimerasas. Factores generales (TBP, TFIID). Procesamiento del
  pre-mRNA: caperuza, poliA, splicing.

TEMA 16 — Traducción
  Código genético: 64 codones (61 + 3 STOP). Universal, no ambiguo,
  degenerado. tRNA, anticodón, aminoacil-tRNA sintetasas. Ribosoma 70S
  (30S + 50S); sitios A, P, E. Shine-Dalgarno. Factores IF, EF, RF.

TEMA 17 — Regulación génica
  Procariotas: operón. Inducible vs reprimible. Operón LAC (inducible
  negativo, lactosa = inductor). Operón TRP (reprimible negativo,
  triptófano = corepresor). Eucariotas: cromatina, metilación, TF
  basales y reguladores, enhancers, miRNA/siRNA.

TEMA 18 — Ingeniería Genética
  Enzimas de restricción tipo II (palíndromos). EcoRI, BamHI, HindIII.
  Vectores: plásmidos (pBR322), BACs, YACs. Características: ori,
  marcadores, sitios únicos. PCR (Mullis 1983): desnaturalización,
  alineamiento, extensión. Taq polimerasa. RT-PCR. CRISPR/Cas9.
"""

SYSTEM_PROMPT_METABOLISMO = """\
Eres profesor universitario de Bioquímica y Biología Molecular en una facultad \
de Ciencias de la Salud (URJC). Diseñas preguntas tipo test al estilo de los \
exámenes oficiales y de los cuestionarios wooclap usados en clase.

═══════════════════════════════════════════════════════════════════════════════
ÁREA: METABOLISMO (Temas 10-13 + ciclo TCA y catabolismo de hidratos)
═══════════════════════════════════════════════════════════════════════════════

INTRODUCCIÓN AL METABOLISMO
  Metabolismo = suma de las reacciones catalizadas enzimáticamente en la
  célula. Funciones: obtener energía química (ATP), interconvertir nutrientes,
  ensamblar macromoléculas, sintetizar biomoléculas específicas.

  Clasificación metabólica: por fuente de carbono (autótrofos vs heterótrofos),
  por fuente de energía (fotótrofos vs quimiótrofos), por aceptor final de
  electrones (aerobios vs anaerobios; estrictos vs facultativos).

  Termodinámica: sistemas abiertos, entalpía (ΔH), entropía (ΔS), energía
  libre de Gibbs (ΔG = ΔH - TΔS). ΔG'º estándar bioquímico ≠ ΔG fisiológico.
  ΔG < 0 = espontáneo. Reacciones acopladas con ATP (ΔG'º hidrólisis ≈ -30 kJ/mol).

  Tipos de regulación enzimática:
    1) Regulación por compartimentación (orgánulos, transportadores).
    2) Regulación alostérica (efectores no covalentes; cooperatividad).
    3) Modulación covalente reversible (fosforilación/desfosforilación,
       acetilación, metilación). Ej: glucógeno fosforilasa activa al
       fosforilarse, glucógeno sintasa inactiva al fosforilarse.
    4) Regulación hormonal (cascadas).
    5) Cambios en la cantidad de enzima (síntesis/degradación).

  Hormonas: clasificación por hidrofobicidad. Hidrófilas (adrenalina,
  glucagón, insulina, péptidos) → receptores DE MEMBRANA. Lipófilas
  (esteroideas como estradiol, testosterona, cortisol; tiroideas) →
  receptores INTRACELULARES (nucleares).

  Segundos mensajeros: AMPc (PKA), GMPc (PKG), DAG (PKC), IP3 (libera
  Ca²⁺), Ca²⁺/calmodulina. Cascadas: receptor → proteína G → enzima
  efectora (adenilato ciclasa, fosfolipasa C) → segundo mensajero →
  proteína quinasa → enzima diana.

METABOLISMO DE HIDRATOS DE CARBONO (catabolismo)
  Digestión: glucosidasas en saliva y secreciones pancreáticas. Almidón
  (~150 g/día), sacarosa, lactosa, glucosa+fructosa.

  GLUCÓLISIS (10 reacciones, citosólica): glucosa → 2 piruvato + 2 ATP + 2 NADH.
  Reguladas: hexoquinasa (R1, inhibida por G6P), fosfofructoquinasa-1 PFK-1
  (R3, paso limitante; activada por AMP, fructosa 2,6-bisP; inhibida por
  ATP, citrato), piruvato quinasa (R10).

  Destinos del piruvato: descarboxilación oxidativa a acetil-CoA (PDH,
  aerobiosis), fermentación láctica (LDH, anaerobiosis), fermentación
  alcohólica (levaduras).

  Complejo piruvato deshidrogenasa (PDH): 3 enzimas (E1, E2, E3) y 5
  cofactores (TPP, ácido lipoico, CoA, FAD, NAD+). Regulación por
  fosforilación (PDH quinasa inactiva, PDH fosfatasa activa).

  RUTA DE LAS PENTOSAS FOSFATO: fase oxidativa (G6PDH → NADPH + ribulosa-5P
  + CO2) y fase no oxidativa (interconversión de azúcares: F6P, G3P).
  Función: NADPH para biosíntesis reductora y defensa antioxidante;
  ribosa-5P para nucleótidos.

CICLO DE LOS ÁCIDOS TRICARBOXÍLICOS (CICLO DE KREBS / TCA)
  Matriz mitocondrial. 8 reacciones. Por cada acetil-CoA: 3 NADH + 1 FADH₂
  + 1 GTP + 2 CO₂.
    1. Citrato sintasa (acetil-CoA + OAA → citrato)
    2. Aconitasa (citrato → isocitrato)
    3. Isocitrato deshidrogenasa (→ α-cetoglutarato + CO₂ + NADH)
    4. α-cetoglutarato deshidrogenasa (→ succinil-CoA + CO₂ + NADH)
    5. Succinil-CoA sintetasa (→ succinato + GTP)
    6. Succinato deshidrogenasa (→ fumarato + FADH₂) [complejo II de la
       cadena respiratoria]
    7. Fumarasa (fumarato → malato)
    8. Malato deshidrogenasa (malato → OAA + NADH)
  Reacciones anapleróticas para reponer intermediarios (piruvato
  carboxilasa: piruvato + CO₂ → OAA).

METABOLISMO OXIDATIVO (cadena respiratoria mitocondrial)
  Membrana mitocondrial interna. Complejos I, II, III, IV. Transportadores
  móviles: ubiquinona y citocromo c.
    Complejo I (NADH-UQ oxidorreductasa) — bombea 4 H⁺.
    Complejo II (succinato-UQ reductasa) — NO bombea protones.
    Complejo III (UQH₂-citocromo c reductasa) — bombea 4 H⁺.
    Complejo IV (citocromo c oxidasa) — reduce O₂ a H₂O; bombea 2 H⁺.
    ATP sintasa (complejo V) — fosforilación oxidativa.
  Hipótesis quimiosmótica de Mitchell. Control respiratorio (regulación
  por ADP). Inhibidores: rotenona (I), antimicina A (III), CN⁻/CO (IV),
  oligomicina (V), DNP (desacoplante).

ANABOLISMO DE HIDRATOS DE CARBONO
  GLUCONEOGÉNESIS: principalmente hepática (riñón ~10 %). Citosólica salvo
  la primera reacción mitocondrial. Tres pasos irreversibles glucolíticos
  sorteados con enzimas exclusivas:
    • Piruvato carboxilasa (mitocondria) + PEP carboxiquinasa (citosol):
      sortean la piruvato quinasa.
    • Fructosa 1,6-bisfosfatasa: sortea la PFK-1.
    • Glucosa 6-fosfatasa (RE): sortea la hexoquinasa.
  Precursores: lactato (ciclo de Cori), alanina (ciclo glucosa-alanina),
  glicerol, aminoácidos glucogénicos.

  METABOLISMO DEL GLUCÓGENO:
    Glucogénesis (citosólica): glucógeno sintasa (α-1→4), enzima
    ramificadora (α-1→6). Activada por insulina, inhibida por glucagón/
    adrenalina vía PKA.
    Glucogenólisis: glucógeno fosforilasa (α-1→4), enzima desramificadora.
    Activada por glucagón/adrenalina vía cascada PKA (fosforilación
    activadora), inhibida por insulina.
  Regulación recíproca: cuando glucagón está alto, fosforilasa ON y
  sintasa OFF; cuando insulina alta, al revés.

CATABOLISMO DE LÍPIDOS (β-oxidación)
  Movilización: lipasa hormono-sensible (TAG → glicerol + ác. grasos libres).
  Activación citosólica (acil-CoA sintetasa, gasta ATP→AMP+PPi).
  Transporte por carnitina al interior mitocondrial: CPT-I (regulada,
  inhibida por malonil-CoA) y CPT-II.
  β-oxidación (matriz mitocondrial): espiral de 4 reacciones por vuelta:
    1. Acil-CoA deshidrogenasa → FADH₂
    2. Enoil-CoA hidratasa
    3. β-hidroxiacil-CoA deshidrogenasa → NADH
    4. Tiolasa → libera 1 acetil-CoA, acorta 2C la cadena
  Ácidos grasos impares: última vuelta da propionil-CoA → succinil-CoA
  (vía B12 y biotina). Insaturados: enoil-CoA isomerasa.
  Cuerpos cetónicos (hígado): acetoacetato, β-hidroxibutirato, acetona.

METABOLISMO LIPÍDICO (biosíntesis)
  Síntesis de ácidos grasos: CITOSÓLICA. Sustratos: acetil-CoA + NADPH
  + ATP. El acetil-CoA sale de la mitocondria como CITRATO (lanzadera).
  Acetil-CoA carboxilasa (ACC, requiere biotina): acetil-CoA → malonil-CoA
  (paso limitante, regulado por citrato +, palmitoil-CoA −, insulina/
  glucagón).
  Ácido graso sintasa (FAS): complejo multienzimático con 7 actividades.
  Producto final: palmitato (C16). Elongación y desaturación en el RE.
  Triglicéridos: glicerol-3P + acil-CoA. Colesterol: HMG-CoA reductasa
  (diana de estatinas).

METABOLISMO DEL NITRÓGENO
  Aminoácidos esenciales (no se sintetizan) vs no esenciales.
  Catabolismo:
    • Transaminación (transaminasas, requieren PLP/vit B6): transfieren
      grupo amino a α-cetoglutarato → glutamato.
    • Desaminación oxidativa (glutamato deshidrogenasa): glutamato →
      α-cetoglutarato + NH₄⁺.
  Ciclo de la UREA (5 enzimas, hepático exclusivo):
    Mitocondria:
      1. Carbamoil-fosfato sintetasa I (CPS-I): NH₃ + CO₂ + 2 ATP →
         carbamoil-fosfato. Activador alostérico: N-acetilglutamato.
      2. Ornitina transcarbamilasa: ornitina + carbamoil-P → citrulina.
    Citosol:
      3. Argininosuccinato sintetasa: citrulina + aspartato → argininosuccinato.
      4. Argininosuccinato liasa: → arginina + fumarato.
      5. Arginasa: arginina → urea + ornitina (que vuelve a la mitocondria).
  Coste energético: 4 ATP por urea. Aminoácidos glucogénicos vs
  cetogénicos. Vitamina C: cofactor de hidroxilación (lisina/prolina
  del colágeno, neurotransmisores).

INTEGRACIÓN DEL METABOLISMO
  Acetil-CoA como encrucijada metabólica. Estado postprandial vs ayuno.
  Roles: hepatocito (productor de glucosa y cuerpos cetónicos),
  miocito (consumidor de glucosa y ácidos grasos), adipocito
  (almacén de TAG), neurona (consume glucosa preferentemente, cuerpos
  cetónicos en ayuno prolongado).
  Hormonas: insulina (anabólica, postprandial), glucagón, adrenalina,
  cortisol (catabólicas). Carga energética celular = (ATP + ½ADP) /
  (ATP+ADP+AMP). Patrones de combustible: ayuno corto (glucógeno),
  ayuno medio (gluconeogénesis), ayuno prolongado (cuerpos cetónicos).
"""


# ──────────────────────────────────────────────────────────────────────────────
# REGLAS DE ESTILO ESPECÍFICAS DE BIOQUÍMICA (se concatenan al system prompt)
# ──────────────────────────────────────────────────────────────────────────────

EXAM_STYLE_RULES = """\
═══════════════════════════════════════════════════════════════════════════════
ESTILO DE PREGUNTA (estilo wooclap del profesor)
═══════════════════════════════════════════════════════════════════════════════

VARIEDAD DE PATRONES (varía entre estos cinco patrones para no repetir formato):

1. IDENTIFICACIÓN DIRECTA con opciones cortas (1-3 palabras cada una):
   "¿Cuál de las siguientes hormonas tiene receptor intracelular?"
   → Adrenalina / Glucagón / Insulina / Estradiol

2. PREGUNTA EN NEGATIVO (oveja negra):
   "¿Cuál de las siguientes proteínas NO clasificarías como fibrosa?"
   → Elastina / Colágeno / Fibroína / Mioglobina

3. OPCIONES LARGAS con estructura paralela y cambios sutiles:
   Las cuatro opciones tienen una estructura sintáctica parecida; sólo
   cambian uno o dos términos clave (aumento/disminución; activa/inhibe).
   Ej: "La energía de activación se reduce..." vs "...se incrementa..."

4. USO de "Todas son verdaderas" o "Todas son falsas" como opción real:
   A veces la correcta es justamente "Todas son verdaderas" (cuando las 3
   anteriores son TODAS ciertas) o "Todas son falsas" (cuando las 3
   anteriores comparten un error sutil común). Útil para evaluar dominio
   integrado.

5. RAZONAMIENTO EXPERIMENTAL:
   "Imagine una cepa de ratones que no puede sintetizar X. Prediga..."
   El estudiante debe deducir las consecuencias en cascada.

REGLAS ADICIONALES:
   • Sin código (es bioquímica, no programación).
   • Lenguaje técnico universitario en español.
   • Distractores plausibles: SIEMPRE conceptos cercanos (otras enzimas
     de la misma vía, otras hormonas del mismo grupo, otras proteínas del
     mismo tipo).
   • Nunca opciones absurdas que se descarten sin pensar.
   • Si usas opciones cortas (1-2 palabras), TODAS las opciones deben ser
     igual de cortas. Si usas opciones largas, igual de largas.
"""


# ──────────────────────────────────────────────────────────────────────────────
# Constructor de mensajes
# ──────────────────────────────────────────────────────────────────────────────

def _build_messages(difficulty: str, area: Optional[str]) -> List[Dict[str, str]]:
    diff = difficulty.lower()

    if area not in AREAS:
        area = random.choice(AREAS)

    hints = DIFFICULTY_HINTS.get(area, {}).get(diff, [None])
    hint = random.choice(hints) if hints else None

    fragment = _common.pick_fragment(SUBJECT, source_hint=hint, area=area)

    if area == "metabolismo":
        head = SYSTEM_PROMPT_METABOLISMO
        few_shots = FEW_SHOTS_METABOLISMO
    else:
        head = SYSTEM_PROMPT_GENETICA
        few_shots = FEW_SHOTS_GENETICA

    # Para metabolismo añadimos las reglas de estilo wooclap (5 patrones).
    # Para genética las reglas comunes son suficientes (ya están en _common).
    style = EXAM_STYLE_RULES if area == "metabolismo" else ""

    system_prompt = head + "\n" + style + _common.COMMON_RULES
    msgs: List[Dict[str, str]] = [{"role": "system", "content": system_prompt}]

    # 2 ejemplos al azar (de 8 si es metabolismo; de 4 si es genética).
    sample_size = min(2, len(few_shots))
    for ex in random.sample(few_shots, k=sample_size):
        msgs.append({"role": "user", "content": "Genera una pregunta de ejemplo."})
        msgs.append({"role": "assistant", "content": _dump_json(ex)})

    user_msg = (
        f"Genera UNA pregunta tipo test de dificultad **{diff.upper()}** del área "
        f"**{area.upper()}**.\n\n"
    )
    if fragment:
        user_msg += _common.build_context_block(fragment) + "\n\n"
    else:
        user_msg += (
            "(Aviso interno: no hay corpus cargado para esta área; basa la "
            "pregunta en el temario descrito en el system prompt.)\n\n"
        )

    # Para metabolismo, recordamos los 5 patrones para que el modelo varíe
    if area == "metabolismo":
        user_msg += (
            "VARÍA el patrón de pregunta entre los 5 disponibles: identificación "
            "con opciones cortas, pregunta en negativo, opciones largas paralelas, "
            "uso de 'Todas son verdaderas/falsas', o razonamiento experimental. "
            "No uses siempre el mismo patrón.\n\n"
        )

    user_msg += (
        "RECUERDA: las 4 opciones deben tener longitudes parecidas entre sí; la "
        "correcta NO puede destacar por ser visiblemente más larga ni más corta "
        "que las demás. Distribuye aleatoriamente la posición de la correcta "
        "entre 0, 1, 2 y 3. Devuelve solo el JSON con title/options/"
        "correct_answer_id/explanation."
    )
    msgs.append({"role": "user", "content": user_msg})
    return msgs


def _dump_json(obj: Dict[str, Any]) -> str:
    import json
    return json.dumps(obj, ensure_ascii=False)


FALLBACK_GENETICA = {
    "title": (
        "En la replicación semidiscontinua del DNA en procariotas, "
        "¿qué propiedad de la DNA polimerasa explica que la hebra retardada "
        "se sintetice en fragmentos (de Okazaki) en vez de continuamente "
        "como la hebra conductora?"
    ),
    "options": [
        "Que la DNA polimerasa solo es capaz de extender una cadena nueva en dirección 5' hacia 3'.",
        "Que la DNA polimerasa necesita primero degradar las histonas antes de polimerizar la hebra molde.",
        "Que la DNA polimerasa requiere ATP libre y no tolera la presencia de pirofosfato durante la elongación.",
        "Que la DNA polimerasa sintetiza simultáneamente las dos hebras en sentido contrario al avance de la horquilla.",
    ],
    "correct_answer_id": 0,
    "explanation": (
        "La respuesta correcta es la A. La DNA polimerasa solo añade nucleótidos al extremo "
        "3'-OH de la cadena en crecimiento, por lo que la síntesis siempre es 5'→3'. Como "
        "las dos hebras son antiparalelas, la conductora se sintetiza de manera continua y "
        "la retardada en fragmentos cortos (Okazaki) que luego se unen.\n\n"
        "B es falsa (las histonas son eucariotas). C invierte la realidad. D es errónea."
    ),
}

FALLBACK_METABOLISMO = {
    "title": "¿Cuál de las siguientes hormonas posee un receptor INTRACELULAR (no de membrana)?",
    "options": [
        "Adrenalina",
        "Glucagón",
        "Insulina",
        "Cortisol",
    ],
    "correct_answer_id": 3,
    "explanation": (
        "La respuesta correcta es la D. El cortisol es una hormona esteroidea, lipófila, "
        "que atraviesa la membrana plasmática y se une a un receptor intracelular "
        "(citoplasmático/nuclear) que actúa como factor de transcripción.\n\n"
        "Adrenalina y glucagón son hidrófilas y usan receptores de membrana acoplados a "
        "proteína G. La insulina también tiene receptor de membrana (con actividad "
        "tirosina quinasa). Solo las hormonas LIPÓFILAS (esteroideas, tiroideas) tienen "
        "receptores intracelulares."
    ),
}


def generate(difficulty: str, area: Optional[str] = None) -> Dict[str, Any]:
    """Genera una pregunta de bioquímica.

    Args:
        difficulty: "easy" | "medium" | "hard"
        area: "metabolismo" | "genetica" | None (None = aleatorio entre las dos)

    Returns:
        dict con title/options/correct_answer_id/explanation y un campo
        adicional `_area` indicando el área usada.
    """
    if area not in AREAS:
        chosen_area = random.choice(AREAS)
    else:
        chosen_area = area

    fallback = FALLBACK_METABOLISMO if chosen_area == "metabolismo" else FALLBACK_GENETICA

    challenge = _common.generate_with_validation(
        build_messages=lambda: _build_messages(difficulty, chosen_area),
        fallback=fallback,
    )
    challenge["_area"] = chosen_area
    return challenge