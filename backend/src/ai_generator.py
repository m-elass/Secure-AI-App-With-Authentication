"""
Generador de preguntas para PER (Programación en Entornos de Red, URJC).

PER no usa subáreas, pero la función generate() acepta `area` como
parámetro opcional (lo ignora) para mantener una firma uniforme con
el resto de generadores.
"""
import random
from typing import Dict, Any, List, Optional

from . import _common

SUBJECT = "per"


DIFFICULTY_HINTS = {
    "easy": [None, None, None, "JSON", "redes"],
    "medium": [None, None, "HTTP", "Web", "JSON", "OOP", "Object_Oriented"],
    "hard": [None, "HTTP", "sockets", "Web", "OOP", "Prácticas", "entornos_de_red"],
}


FEW_SHOT_EXAMPLES = [
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
            "por lo que mi_coche y nuevo_coche son dos instancias distintas. "
            "otro_coche = mi_coche no crea un tercer objeto: solo añade una referencia.\n\n"
            "A confunde los roles. B ignora que = no crea objeto. C es falsa."
        ),
    },
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
            "La respuesta correcta es la A. HTTP transmite los datos sin cifrar. HTTPS añade "
            "cifrado SSL/TLS y protege la comunicación.\n\n"
            "B es falsa. C invierte la realidad. D es incorrecta: HTTPS se usa en cualquier "
            "comunicación web."
        ),
    },
    {
        "title": (
            "Observa el siguiente código en Python y determina qué se imprimirá:\n\n"
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
            "La respuesta correcta es la B. Python busca el método primero en la clase del "
            "objeto (Perro). Como lo encuentra, lo ejecuta. Esto es sobreescritura (override).\n\n"
            "A sería el resultado si Perro NO redefiniera hablar. C es falsa: redefinir es "
            "válido en Python. D es falsa: solo se ejecuta el método de la subclase."
        ),
    },
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
            "¿Cuál de las siguientes afirmaciones es correcta?"
        ),
        "options": [
            "La variable producto sigue siendo una cadena de texto que contiene el JSON original como string.",
            "La función json.loads() convierte el objeto JSON externo en una lista de pares clave-valor.",
            "La clave 'caracteristicas' del objeto producto contiene un diccionario anidado de Python.",
            "El método loads() solo se puede usar cuando el JSON está almacenado en un archivo del disco.",
        ],
        "correct_answer_id": 2,
        "explanation": (
            "La respuesta correcta es la C. json.loads() deserializa una cadena JSON en "
            "estructuras nativas: el objeto JSON externo es un dict y el anidado también.\n\n"
            "A es falsa. B confunde objeto JSON con array. D confunde loads() con load()."
        ),
    },
]


SYSTEM_PROMPT_HEAD = """\
Eres profesor de la asignatura "Programación en Entornos de Red" (PER) de la \
URJC y experto en diseñar preguntas tipo test para exámenes universitarios.

═══════════════════════════════════════════════════════════════════════════════
TEMARIO OFICIAL DE PER
═══════════════════════════════════════════════════════════════════════════════

BLOQUE 1 — POO en Python: clases, __init__, self, métodos, herencia con
super(), sobreescritura, polimorfismo, paso por referencia vs inmutables.

BLOQUE 2 — HTTP / HTTPS: verbos estándar (GET, POST, PUT, PATCH, DELETE,
HEAD). NO existen verbos como CREATE/READ/MODIFY/EXECUTE/PUSH. Idempotencia.
URL, cabeceras (Content-Type, Host, User-Agent). Códigos de estado.
HTTP/HTTPS (SSL/TLS). REST: verbos HTTP + JSON.

BLOQUE 3 — JSON: loads/load (deserializar), dumps/dump (serializar).
Objeto {...}→dict, array [...]→list.

BLOQUE 4 — Sockets: socket.socket(AF_INET, SOCK_STREAM). Servidor: bind/
listen/accept. Cliente: connect. 127.0.0.1, 0.0.0.0. Puertos.

BLOQUE 5 — Servidor HTTP en Python: BaseHTTPRequestHandler, do_GET, do_POST.

BLOQUE 6 — unittest: TestCase, assertEqual, assertTrue, assertRaises.
"""


def _build_messages(difficulty: str, area: Optional[str] = None) -> List[Dict[str, str]]:
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

    user_msg = f"Genera UNA pregunta tipo test de dificultad **{diff.upper()}**.\n\n"
    if fragment:
        user_msg += _common.build_context_block(fragment) + "\n\n"
    else:
        user_msg += (
            "(Aviso interno: no hay corpus cargado; basa la pregunta en el "
            "temario descrito en el system prompt.)\n\n"
        )
    user_msg += (
        "RECUERDA: las 4 opciones deben tener longitudes parecidas. "
        "Distribuye la posición de la correcta entre 0, 1, 2 y 3. "
        "Devuelve solo el JSON."
    )
    msgs.append({"role": "user", "content": user_msg})
    return msgs


def _dump_json(obj):
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
        "La respuesta correcta es la B. libro2 = libro1 no crea un nuevo objeto: solo "
        "añade un segundo nombre que referencia al mismo objeto.\n\n"
        "A es falsa. C confunde asignación con herencia. D es falsa."
    ),
}


def generate(difficulty: str, area: Optional[str] = None) -> Dict[str, Any]:
    """Genera una pregunta de PER. El parámetro `area` se acepta por simetría
    con otros generadores pero PER no usa subáreas; se ignora."""
    return _common.generate_with_validation(
        build_messages=lambda: _build_messages(difficulty),
        fallback=FALLBACK,
    )