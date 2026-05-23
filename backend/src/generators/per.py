"""
Generador de preguntas para PER (Programación en Entornos de Red, URJC).

Estrategia: cada pregunta se construye sobre un FRAGMENTO LITERAL del
temario (extraído por scripts/ingest_pdfs.py). Esto garantiza que las
preguntas se mantengan dentro de lo que tus apuntes cubren realmente.

Si el corpus no está disponible, caemos a una estrategia "sin corpus"
basada solo en el system prompt y few-shots, igualmente válida.
"""
import random
from typing import Dict, Any, List, Optional

from . import _common

SUBJECT = "per"


# ──────────────────────────────────────────────────────────────────────────────
# Pistas por dificultad: cada dificultad se asocia a ciertos tipos de PDF
# de origen, para que el reparto temático sea coherente con el nivel.
# ──────────────────────────────────────────────────────────────────────────────

DIFFICULTY_HINTS = {
    "easy": [
        # Fundamentos: que vengan de los PDFs de teoría básica
        None, None, None,  # cualquier fragmento
        "JSON", "redes",
    ],
    "medium": [
        None, None,
        "HTTP", "Web", "JSON", "OOP", "Object_Oriented",
    ],
    "hard": [
        None,
        "HTTP", "sockets", "Web", "OOP", "Prácticas",
        "entornos_de_red",
    ],
}


# ──────────────────────────────────────────────────────────────────────────────
# FEW-SHOT EXAMPLES (estilo URJC / PER, calcados de exámenes reales)
# ──────────────────────────────────────────────────────────────────────────────
# Distribuimos correct_answer_id entre las 4 posiciones para no inducir sesgo.
# Cuidamos que las 4 opciones tengan longitudes parecidas.

FEW_SHOT_EXAMPLES = [
    # ── correct_id = 3 ──
    {
        "title": (
            "Analiza el siguiente fragmento de código en Python y selecciona la "
            "afirmación que describe correctamente la relación entre las variables "
            "y los objetos creados:\n\n"
            "class Coche:\n"
            "    pass\n\n"
            "mi_coche = Coche()\n"
            "otro_coche = mi_coche\n"
            "nuevo_coche = Coche()"
        ),
        "options": [
            "La clase Coche pasa a ser un objeto tras la asignación, mientras que mi_coche queda como referencia de tipo clase.",
            "Se crean tres objetos independientes de Coche que residen en posiciones distintas de memoria del intérprete.",
            "Existen tres variables nombradas (mi_coche, otro_coche, nuevo_coche), pero todas apuntan al mismo objeto en memoria.",
            "Se crean dos objetos distintos de Coche, y la variable otro_coche apunta al mismo objeto que mi_coche.",
        ],
        "correct_answer_id": 3,
        "explanation": (
            "La respuesta correcta es la D. Cada llamada Coche() crea un objeto nuevo, "
            "por lo que mi_coche y nuevo_coche son dos instancias distintas. La asignación "
            "otro_coche = mi_coche no crea un tercer objeto: solo añade una referencia al "
            "mismo que ya apuntaba mi_coche.\n\n"
            "A confunde los roles (Coche sigue siendo la clase). B ignora que = no crea "
            "objeto. C es falsa porque nuevo_coche apunta a un objeto distinto."
        ),
    },
    # ── correct_id = 0 ──
    {
        "title": (
            "¿Cuál de las siguientes afirmaciones describe correctamente la "
            "diferencia entre los protocolos HTTP y HTTPS en una URL?"
        ),
        "options": [
            "HTTP transmite la información en texto plano, mientras que HTTPS la cifra mediante SSL/TLS para proteger la comunicación.",
            "HTTP y HTTPS son intercambiables en una URL y no afectan a la seguridad real de la comunicación entre cliente y servidor.",
            "HTTP cifra la información transmitida mediante TLS, mientras que HTTPS la transmite en texto plano sin cifrado adicional.",
            "HTTP se utiliza para la transferencia de páginas web, mientras que HTTPS está limitado a la comunicación entre servidores internos.",
        ],
        "correct_answer_id": 0,
        "explanation": (
            "La respuesta correcta es la A. HTTP transmite los datos sin cifrar, lo que permite "
            "su interceptación. HTTPS añade cifrado SSL/TLS y protege la comunicación.\n\n"
            "B es falsa porque la seguridad SÍ varía. C invierte la realidad: el que cifra es "
            "HTTPS. D es incorrecta: HTTPS se usa en cualquier comunicación web, no solo "
            "entre servidores internos."
        ),
    },
    # ── correct_id = 1 ──
    {
        "title": (
            "Observa el siguiente código en Python y determina qué se imprimirá por "
            "pantalla al ejecutarlo:\n\n"
            "class Animal:\n"
            "    def hablar(self):\n"
            "        print(\"El animal hace un sonido\")\n\n"
            "class Perro(Animal):\n"
            "    def hablar(self):\n"
            "        print(\"El perro ladra: ¡Guau!\")\n\n"
            "mi_mascota = Perro()\n"
            "mi_mascota.hablar()"
        ),
        "options": [
            "El animal hace un sonido",
            "El perro ladra: ¡Guau!",
            "Error: el método hablar ya existe en la clase padre y no puede redefinirse.",
            "Se imprimen ambas líneas: primero el sonido genérico y después el ladrido.",
        ],
        "correct_answer_id": 1,
        "explanation": (
            "La respuesta correcta es la B. Al invocar mi_mascota.hablar(), Python busca el "
            "método primero en la clase del objeto (Perro). Como lo encuentra allí, lo "
            "ejecuta. Esto es la sobreescritura (override), base del polimorfismo.\n\n"
            "A sería el resultado si Perro NO redefiniera hablar. C es falsa: redefinir un "
            "método heredado es perfectamente válido en Python. D es falsa: solo se ejecuta "
            "el método de la subclase, salvo invocación explícita de super().hablar()."
        ),
    },
    # ── correct_id = 2 ──
    {
        "title": (
            "Considera el siguiente fragmento de código en Python:\n\n"
            "import json\n"
            "datos = '''\n"
            "{\n"
            '    "nombre": "Tablet A10",\n'
            '    "precio": 299.99,\n'
            '    "caracteristicas": {\n'
            '        "pantalla": "10 pulgadas",\n'
            '        "almacenamiento": "64GB"\n'
            "    }\n"
            "}\n"
            "'''\n"
            "producto = json.loads(datos)\n\n"
            "¿Cuál de las siguientes afirmaciones es correcta respecto al código anterior?"
        ),
        "options": [
            "La variable producto sigue siendo una cadena de texto que contiene el JSON original como string.",
            "La función json.loads() convierte el objeto JSON externo en una lista de pares clave-valor.",
            "La clave 'caracteristicas' del objeto producto contiene un diccionario anidado de Python.",
            "El método loads() solo se puede usar cuando el JSON está almacenado en un archivo del disco.",
        ],
        "correct_answer_id": 2,
        "explanation": (
            "La respuesta correcta es la C. json.loads() (con 's' final, de 'string') deserializa "
            "una cadena JSON y la convierte en estructuras nativas de Python: el objeto JSON "
            "externo es un dict y el objeto anidado también es un dict. Por tanto, "
            "producto['caracteristicas'] es un diccionario.\n\n"
            "A es falsa: tras loads() ya tenemos dict, no string. B confunde objeto JSON con "
            "array: los objetos {...} pasan a dict, los arrays [...] a list. D confunde "
            "loads() con load(): loads() opera sobre strings en memoria; load() lee de fichero."
        ),
    },
]


# ──────────────────────────────────────────────────────────────────────────────
# SYSTEM PROMPT
# ──────────────────────────────────────────────────────────────────────────────

SYSTEM_PROMPT_HEAD = """\
Eres profesor de la asignatura "Programación en Entornos de Red" (PER) de la \
URJC y experto en diseñar preguntas tipo test para exámenes universitarios. \
Tu trabajo es generar UNA pregunta de examen siguiendo EXACTAMENTE el estilo \
de los exámenes oficiales.

═══════════════════════════════════════════════════════════════════════════════
TEMARIO OFICIAL DE LA ASIGNATURA (referencia, no agregues nada fuera de aquí)
═══════════════════════════════════════════════════════════════════════════════

BLOQUE 1 — Programación Orientada a Objetos en Python
  Clases vs objetos, __init__, self, atributos vs métodos, métodos dunder,
  herencia con super(), sobreescritura, polimorfismo, paso por referencia
  vs inmutables.

BLOQUE 2 — Protocolo HTTP / HTTPS
  Verbos HTTP estándar (GET, POST, PUT, PATCH, DELETE, HEAD; NO existen
  CREATE/READ/MODIFY/EXECUTE/PUSH). Idempotencia. Partes de la URL.
  Cabeceras (Content-Type, Host, User-Agent, Accept). Códigos de estado.
  Diferencia HTTP/HTTPS (SSL/TLS). REST: usa verbos HTTP, datos en JSON.

BLOQUE 3 — JSON
  loads/load (deserializar), dumps/dump (serializar). Objeto {...}→dict,
  array [...]→list.

BLOQUE 4 — Sockets en Python
  socket.socket(AF_INET, SOCK_STREAM). Servidor: bind/listen/accept.
  Cliente: connect. 127.0.0.1 (localhost), 0.0.0.0 (todas las interfaces).
  Puerto de escucha del servidor vs puerto asignado al cliente.

BLOQUE 5 — Servidor HTTP en Python
  BaseHTTPRequestHandler, do_GET, do_POST. send_response → send_header →
  end_headers. Lectura POST con Content-Length y rfile.read.

BLOQUE 6 — Tests unitarios con unittest
  TestCase, assertEqual, assertTrue, assertFalse, assertIs, assertIn,
  assertRaises.
"""


def _build_messages(difficulty: str) -> List[Dict[str, str]]:
    """Construye el conjunto de mensajes para una generación PER."""
    diff = difficulty.lower()
    if diff not in DIFFICULTY_HINTS:
        diff = "easy"

    # Elegimos un fragmento del corpus alineado con la dificultad
    hint = random.choice(DIFFICULTY_HINTS[diff])
    fragment = _common.pick_fragment(SUBJECT, source_hint=hint)

    system_prompt = SYSTEM_PROMPT_HEAD + "\n" + _common.COMMON_RULES

    msgs: List[Dict[str, str]] = [{"role": "system", "content": system_prompt}]

    # 2 ejemplos few-shot rotatorios
    for ex in random.sample(FEW_SHOT_EXAMPLES, k=2):
        msgs.append({"role": "user", "content": "Genera una pregunta de ejemplo."})
        msgs.append({"role": "assistant", "content": _dump_json(ex)})

    # Mensaje real de petición
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
        "Observa el siguiente código en Python y selecciona la afirmación correcta:\n\n"
        "class Libro:\n"
        "    def __init__(self, titulo):\n"
        "        self.titulo = titulo\n\n"
        'libro1 = Libro("1984")\n'
        "libro2 = libro1"
    ),
    "options": [
        "Se han creado dos objetos diferentes de la clase Libro almacenados en memoria distinta.",
        "Las variables libro1 y libro2 son dos nombres que referencian al mismo objeto en memoria.",
        "La variable libro2 es una nueva clase que hereda de la clase Libro original definida arriba.",
        "El código produce un error porque a Libro le falta un constructor explícito declarado.",
    ],
    "correct_answer_id": 1,
    "explanation": (
        "La respuesta correcta es la B. La asignación libro2 = libro1 no crea un nuevo "
        "objeto: solo añade un segundo nombre que referencia al mismo objeto que libro1.\n\n"
        "A es falsa: solo se ha llamado a Libro() una vez. C confunde asignación con "
        "herencia (que se haría con 'class libro2(Libro)'). D es falsa: __init__ está "
        "perfectamente definido."
    ),
}


def generate(difficulty: str) -> Dict[str, Any]:
    return _common.generate_with_validation(
        build_messages=lambda: _build_messages(difficulty),
        fallback=FALLBACK,
    )