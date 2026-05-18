import os
import json
import random

from openai import OpenAI
from typing import Dict, Any, List
from dotenv import load_dotenv

load_dotenv()

client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))


# ──────────────────────────────────────────────────────────────────────────────
# CATÁLOGO TEMÁTICO BASADO EN EL TEMARIO REAL DE PER (URJC)
# Este catálogo se usa para forzar variedad: en cada llamada se selecciona
# un tema concreto y un subtema, evitando la repetición típica de prompts
# abiertos como "genera una pregunta easy".
# ──────────────────────────────────────────────────────────────────────────────

TOPIC_CATALOG = {
    "easy": {
        "POO_BASICA": [
            "diferencia entre clase y objeto (instancia)",
            "propósito del constructor __init__",
            "qué es self y cómo se usa",
            "diferencia entre atributo y método",
            "diferencia entre función y método",
            "creación de una instancia: sintaxis correcta",
            "acceso a atributos mediante notación de punto",
            "encapsulación: atributos y métodos",
        ],
        "PYTHON_FUNDAMENTOS": [
            "tipos de datos básicos (int, str, float, bool, list, dict)",
            "diferencia entre lista y tupla (mutable vs inmutable)",
            "diferencia entre diccionario y lista",
            "operaciones con listas: append, insert, remove",
            "indexación y slicing de cadenas",
            "estructuras de control: if/elif/else",
            "bucles for y while",
            "f-strings y formato de cadenas",
        ],
        "HTTP_BASICO": [
            "qué es un verbo HTTP y cuáles existen",
            "diferencia conceptual entre GET y POST",
            "qué es una URL y sus partes (protocolo, dominio, ruta, query)",
            "código de estado 200, 404, 500",
            "qué es HTTPS frente a HTTP",
            "qué es una cabecera HTTP",
        ],
        "JSON_BASICO": [
            "qué es JSON y para qué sirve",
            "estructura de un objeto JSON (clave-valor)",
            "diferencia entre JSON y diccionario Python",
            "importación del módulo json",
        ],
    },
    "medium": {
        "POO_INTERMEDIA": [
            "herencia simple: cómo declarar una clase hija",
            "uso de super().__init__() para invocar al constructor del padre",
            "sobreescritura de métodos (overriding) y polimorfismo básico",
            "métodos dunder (__str__, __len__, __repr__, __eq__)",
            "paso de objetos por referencia frente a inmutables por valor",
            "identidad vs igualdad (is vs ==)",
            "atributos de clase vs atributos de instancia",
            "qué imprime este código: trazar una herencia con override",
            "interpretación de un constructor con valores por defecto",
        ],
        "HTTP_INTERMEDIO": [
            "qué verbos se usan para crear, leer, actualizar y borrar (CRUD vs REST)",
            "cabecera Content-Type: text/html vs application/json",
            "diferencia entre cabecera de petición y cabecera de respuesta",
            "idempotencia: por qué GET es idempotente y POST no",
            "dónde viaja la query en un GET y en un POST",
            "qué información va en el path y qué información va en la query",
            "qué es una API REST y cómo se relaciona con los verbos HTTP",
            "interpretación de una traza HTTP: identificar verbo, recurso y cabeceras",
        ],
        "JSON_INTERMEDIO": [
            "diferencia entre json.loads y json.load",
            "diferencia entre json.dumps y json.dump",
            "serializar (dumps) vs deserializar (loads)",
            "lectura de un JSON desde un fichero con open() y json.load",
            "escritura de un diccionario a fichero JSON",
            "tipos de Python que NO son serializables por defecto (set, datetime)",
            "navegación por un JSON anidado en Python",
        ],
        "SOCKETS_INTERMEDIO": [
            "qué hace socket.socket(AF_INET, SOCK_STREAM)",
            "rol del bind, listen y accept en un servidor",
            "rol del connect en un cliente",
            "qué representa la IP 127.0.0.1 (localhost)",
            "qué representa la IP 0.0.0.0 como dirección de bind",
            "diferencia entre puerto de escucha del servidor y puerto asignado al cliente",
            "orden correcto de cierre de un socket cliente/servidor",
        ],
        "TESTS_UNITTEST": [
            "estructura mínima de una clase de test con unittest.TestCase",
            "assertEqual, assertTrue, assertFalse, assertIn",
            "diferencia entre assertIs y assertEqual",
            "uso de assertRaises para verificar excepciones",
        ],
    },
    "hard": {
        "POO_AVANZADA": [
            "MRO y herencia múltiple en Python",
            "composición frente a herencia: cuándo usar cada una",
            "diferencia entre @classmethod, @staticmethod y método de instancia",
            "encapsulación con _ y __ (name mangling)",
            "trazar la salida de un código con override + super() en cadena",
            "detectar errores en código OOP: falta de super().__init__, firma incompatible, self ausente",
            "polimorfismo a través de duck typing en Python",
        ],
        "HTTP_AVANZADO": [
            "diferencia entre PUT y PATCH para actualizar recursos",
            "auditar una traza HTTP y detectar si la cabecera es de envío o de respuesta",
            "interpretación de un curl: identificar verbo, recurso, parámetros y cabeceras",
            "REST vs SOAP: características que definen una API RESTful",
            "qué verbos HTTP son válidos en REST (PUT, GET, POST, DELETE, PATCH) y cuáles NO (CREATE, READ, MODIFY, EXECUTE)",
            "cuándo el servidor debe responder con application/json frente a text/html",
        ],
        "SERVIDOR_HTTP_PYTHON": [
            "implementación de do_GET en BaseHTTPRequestHandler",
            "implementación de do_POST: lectura de Content-Length y rfile.read",
            "uso de send_response, send_header, end_headers",
            "ruteo según self.path en do_GET",
            "parseo de datos POST con urllib.parse o split manual",
            "devolver JSON desde do_GET: cabecera y serialización",
        ],
        "REDES_AVANZADO": [
            "diferencia entre IP pública y privada",
            "rol del puerto en una conexión TCP",
            "qué representa una IP dinámica frente a una estática",
            "concurrencia básica: un puerto de escucha + un socket por cliente",
        ],
        "PRACTICAS_REALES": [
            "código espagueti vs refactorización a OOP: detectar problemas de mantenibilidad",
            "interpretar un fragmento de código mixto (HTTP + JSON + OOP) y responder qué hace",
            "completar un test unitario que verifique la inicialización de una clase",
        ],
    },
}


# ──────────────────────────────────────────────────────────────────────────────
# EJEMPLOS FEW-SHOT (estilo URJC / PER)
# Estos ejemplos están calcados del estilo y nivel de los exámenes reales
# y los simulacros que hemos revisado. Sirven para que el modelo aprenda
# qué se considera una "buena" pregunta de examen.
# ──────────────────────────────────────────────────────────────────────────────

FEW_SHOT_EXAMPLES = [
    # ── Ejemplo 1: OOP — relación clase / instancia (estilo examen parcial) ──
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
            "Coche es un objeto de tipo instancia, mientras que mi_coche es una clase.",
            "Se han creado tres objetos de la clase Coche en la memoria.",
            "Hay tres variables (mi_coche, otro_coche, nuevo_coche), pero solo apuntan a un único objeto.",
            "Se han creado dos objetos (instancias) diferentes de la clase Coche, y la variable otro_coche apunta al mismo objeto que mi_coche.",
        ],
        "correct_answer_id": 3,
        "explanation": (
            "La opción correcta es la D. Cada llamada a Coche() crea un nuevo objeto en memoria, "
            "por lo que mi_coche y nuevo_coche son objetos distintos (dos instancias). Sin embargo, "
            "la asignación otro_coche = mi_coche NO crea un nuevo objeto: simplemente hace que "
            "otro_coche referencie al mismo objeto que mi_coche. Una variable en Python no 'es' el "
            "objeto, sino que 'apunta' a él en memoria.\n\n"
            "Por qué fallan las demás: A confunde los roles (Coche es la clase, no la instancia). "
            "B ignora que otro_coche no crea un nuevo objeto. C es incorrecta porque nuevo_coche sí "
            "apunta a un objeto distinto."
        ),
    },
    # ── Ejemplo 2: HTTP — diferencia HTTP/HTTPS (estilo simulacro mayo 2024) ──
    # Aquí la respuesta correcta es la A (id=0) — distribuimos para que el
    # modelo no aprenda a poner siempre la correcta en la última posición.
    {
        "title": (
            "¿Cuál de las siguientes afirmaciones describe correctamente la "
            "diferencia entre los protocolos HTTP y HTTPS en una URL?"
        ),
        "options": [
            "HTTP transmite la información en texto plano, mientras que HTTPS la cifra mediante SSL/TLS para proteger la comunicación.",
            "HTTP y HTTPS son intercambiables y no afectan a la seguridad de la comunicación.",
            "HTTP cifra la información transmitida, mientras que HTTPS la transmite en texto plano.",
            "HTTP se utiliza para la transferencia de páginas web, mientras que HTTPS solo se utiliza entre servidores internos.",
        ],
        "correct_answer_id": 0,
        "explanation": (
            "La respuesta correcta es la A. HTTP transmite los datos sin cifrar, lo que permite "
            "que terceros (man-in-the-middle) puedan interceptarlos. HTTPS añade una capa de "
            "cifrado mediante SSL/TLS, protegiendo los datos entre cliente y servidor.\n\n"
            "Por qué fallan las demás: B es falsa porque la seguridad SÍ varía entre ambos "
            "protocolos. C invierte la realidad (es HTTPS el que cifra, no HTTP). D es una "
            "afirmación incorrecta sobre el uso: HTTPS se usa en cualquier comunicación web, no "
            "solo entre servidores internos."
        ),
    },
    # ── Ejemplo 3: HTTP — verbos REST (estilo simulacro abril 2024) ──
    {
        "title": (
            "En el contexto de una API REST (Transferencia de Estado Representacional), "
            "¿cuál de los siguientes es un verbo HTTP válido para realizar operaciones "
            "sobre recursos?"
        ),
        "options": [
            "CREATE",
            "READ",
            "MODIFY",
            "POST",
        ],
        "correct_answer_id": 3,
        "explanation": (
            "La respuesta correcta es la D, POST. Los verbos HTTP estándar utilizados en REST "
            "son: GET (leer), POST (crear), PUT (actualizar/reemplazar), PATCH (actualizar "
            "parcialmente) y DELETE (borrar). CREATE, READ y MODIFY NO son verbos HTTP: son "
            "conceptos del modelo CRUD que se IMPLEMENTAN con los verbos HTTP, pero no son "
            "verbos del protocolo.\n\n"
            "Por qué fallan las demás: CREATE, READ y MODIFY parecen plausibles porque "
            "describen acciones que se hacen en REST, pero el verbo real del protocolo es otro."
        ),
    },
    # ── Ejemplo 4: JSON — loads vs load (estilo simulacro abril 2024) ──
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
            "La variable producto es una cadena de texto que contiene el JSON original.",
            "La función json.loads() convierte el JSON en un objeto de tipo lista.",
            "La clave 'caracteristicas' del objeto producto contiene un diccionario anidado.",
            "El método loads() solo se puede usar si el JSON está almacenado en un archivo.",
        ],
        "correct_answer_id": 2,
        "explanation": (
            "La respuesta correcta es la C. json.loads() (con 's' final, de 'string') "
            "deserializa una cadena con formato JSON y la convierte en una estructura nativa "
            "de Python: el objeto JSON pasa a ser un dict y un objeto anidado también es un "
            "dict. Por tanto producto['caracteristicas'] es un diccionario.\n\n"
            "Por qué fallan las demás: A es falsa porque tras loads() ya tenemos un dict, no "
            "un string. B es falsa porque un objeto JSON {...} se convierte en dict, no en "
            "lista (las listas vendrían de [...]). D confunde loads() con load(): loads() lee "
            "de un string en memoria, mientras que load() lee de un fichero."
        ),
    },
    # ── Ejemplo 5: Sockets — interpretación de código (estilo simulacro abril 2024) ──
    {
        "title": (
            "Supón que estamos en el aula de laboratorio. Tu dirección IP es 255.25.78.125 "
            "y la de tu compañero es 255.25.78.178. Dado el siguiente código:\n\n"
            "import socket\n"
            "s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)\n"
            's.connect(("www.ucm.es", 80))\n\n'
            "¿Qué rol está desempeñando este socket en la arquitectura de red?"
        ),
        "options": [
            "Servidor, porque está aceptando los datos que le envía el cliente.",
            "Servidor, porque el método connect() detiene la ejecución hasta que un cliente solicita una conexión.",
            "Cliente, porque es el encargado de realizar una petición a un servidor remoto.",
            "Ambos, tanto el cliente como el servidor deben ejecutar accept() para poder hablar.",
        ],
        "correct_answer_id": 2,
        "explanation": (
            "La respuesta correcta es la C. El método connect() es propio del CLIENTE: "
            "indica que este socket se conecta activamente a un servidor remoto que ya está "
            "escuchando. El servidor, en cambio, utiliza bind() + listen() + accept().\n\n"
            "Por qué fallan las demás: A y B describen comportamientos del servidor "
            "(aceptar conexiones, esperar peticiones), no del cliente. D es incorrecta porque "
            "accept() es exclusivo del servidor."
        ),
    },
    # ── Ejemplo 6: POO — herencia con bug (estilo examen mayo 2025) ──
    # Nota didáctica: la respuesta correcta es la B (id=1) para que en el
    # conjunto de few-shot estén representadas las cuatro posiciones (0, 1, 2, 3)
    # y el modelo no aprenda un sesgo posicional.
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
            "Error de compilación porque el método hablar ya existe en la clase padre.",
            "Se imprimen ambas líneas: primero el sonido genérico y luego el ladrido.",
        ],
        "correct_answer_id": 1,
        "explanation": (
            "La respuesta correcta es la B. Al llamar a mi_mascota.hablar(), Python busca "
            "primero el método en la clase del objeto (Perro). Como lo encuentra allí, lo "
            "ejecuta directamente; esto se llama sobreescritura (override) y es la base del "
            "polimorfismo.\n\n"
            "Por qué fallan las demás: A sería el resultado si Perro no redefiniera hablar. "
            "C es falsa: redefinir un método heredado no produce ningún error en Python. D es "
            "falsa: solo se ejecuta el método de la subclase, salvo que se invoque "
            "explícitamente super().hablar()."
        ),
    },
]


# ──────────────────────────────────────────────────────────────────────────────
# SYSTEM PROMPT — Reescrito completamente.
# Se basa en:
#   - El temario REAL de la asignatura PER (URJC) — apuntes, PDFs, prácticas
#   - El estilo de las preguntas de los exámenes y simulacros reales
#   - El examen parcial del alumno
# Está en español, técnico, con reglas estrictas anti-repetición y anti-fallos
# de formato.
# ──────────────────────────────────────────────────────────────────────────────

SYSTEM_PROMPT = """Eres profesor de la asignatura "Programación en Entornos de Red" (PER) de la URJC \
y experto en diseñar preguntas tipo test para exámenes universitarios. Tu trabajo es generar \
UNA pregunta de examen en formato test multi-opción siguiendo EXACTAMENTE el estilo de los \
exámenes oficiales de la asignatura.

═══════════════════════════════════════════════════════════════════════════════
TEMARIO OFICIAL DE LA ASIGNATURA (NO te salgas de aquí)
═══════════════════════════════════════════════════════════════════════════════

BLOQUE 1 — Programación Orientada a Objetos en Python:
  • Clases vs objetos (instancias). Una clase es un molde; un objeto es una
    instancia concreta. Las variables NO son los objetos, los referencian.
  • Constructor __init__: inicializa el estado del objeto al crearlo.
  • self: referencia explícita a la instancia. Diferencia método vs función.
  • Atributo de instancia vs atributo de clase vs variable global.
  • Métodos dunder (__str__, __len__, __repr__, __eq__): Python los invoca
    automáticamente al usar funciones nativas (print, len, ==, etc.).
  • Herencia: clase hija(ClasePadre). Uso obligado de super().__init__(...)
    cuando la hija define su propio __init__.
  • Sobreescritura de métodos (override) y polimorfismo.
  • Paso de parámetros: los mutables (list, dict, set, objetos) se pasan por
    referencia; los inmutables (int, str, float, tuple, bool) "por valor"
    (realmente Python pasa todo por referencia, pero los inmutables no se
    modifican in-place).

BLOQUE 2 — Protocolo HTTP / HTTPS:
  • Verbos HTTP estándar: GET, POST, PUT, PATCH, DELETE, HEAD, OPTIONS,
    CONNECT, TRACE. NO existen verbos como CREATE, READ, MODIFY, EXECUTE,
    PUSH (esos son confusiones frecuentes con CRUD).
  • GET: idempotente, sin cuerpo, parámetros en la query (?clave=valor).
  • POST: NO idempotente, datos en el cuerpo (no visibles en la URL).
  • PUT vs PATCH: PUT reemplaza el recurso entero; PATCH lo actualiza
    parcialmente.
  • Partes de la URL: protocolo://subdominio.dominio.tld/ruta?query
  • Cabeceras: Content-Type, Host, User-Agent, Accept, Accept-Language.
    Content-Type: text/html para HTML, application/json para JSON.
  • Códigos de estado: 200 OK, 301/302 redirección, 404 no encontrado,
    500 error servidor.
  • Diferencia HTTP vs HTTPS: HTTPS añade cifrado SSL/TLS; en HTTP los datos
    viajan en texto plano y pueden ser interceptados.
  • REST: usa los verbos HTTP estándar; la información viaja como JSON o XML
    (no HTML). Las URLs representan información, no páginas.

BLOQUE 3 — JSON:
  • json.loads(string)  → dict (deserializar desde STRING)
  • json.load(fichero)  → dict (deserializar desde FICHERO)
  • json.dumps(dict)    → string JSON (serializar A STRING)
  • json.dump(dict, fichero) → escribe a fichero
  • Objeto JSON {...} → dict; array JSON [...] → list
  • Serializar = de Python a JSON; Deserializar = de JSON a Python.

BLOQUE 4 — Sockets:
  • socket.socket(socket.AF_INET, socket.SOCK_STREAM) → TCP/IP
  • Servidor: bind((ip, puerto)) → listen(n) → accept() (bloqueante).
  • Cliente: connect((ip, puerto)).
  • 127.0.0.1 = localhost (loopback, máquina propia).
  • 0.0.0.0 = bind a todas las interfaces (comodín).
  • El puerto de escucha del servidor (80, 8080, 20090…) es FIJO; el puerto
    del cliente es asignado dinámicamente por el SO.
  • Cierre: primero cliente.close(), luego servidor.close().

BLOQUE 5 — Servidor HTTP en Python:
  • from http.server import HTTPServer, BaseHTTPRequestHandler
  • do_GET(self) y do_POST(self) sobre self.path.
  • Patrón: send_response(200) → send_header(...) → end_headers().
  • Leer POST: content_length = int(self.headers['Content-Length']);
    post_data = self.rfile.read(content_length).decode('utf-8').
  • Devolver JSON: send_header('Content-type', 'application/json').

BLOQUE 6 — Tests unitarios con unittest:
  • class MiTest(unittest.TestCase): def test_xxx(self): ...
  • assertEqual(a, b), assertTrue(x), assertFalse(x), assertIs(a, b),
    assertIn(a, b), assertRaises(Excepcion, callable, *args).
  • Ejecución: python3 -m unittest fichero  o  if __name__ == "__main__": unittest.main()

═══════════════════════════════════════════════════════════════════════════════
NIVELES DE DIFICULTAD
═══════════════════════════════════════════════════════════════════════════════

EASY (fácil) — conceptos atómicos, una sola idea, respuesta directa:
  Ej. ¿Qué hace __init__? ¿Qué verbo HTTP es idempotente? ¿Qué es self?

MEDIUM (medio) — combinación de 1-2 conceptos, lectura de un fragmento de
código pequeño, interpretación de una traza HTTP, distinción loads/load,
herencia simple con super().
  Ej. ¿Qué imprime este código con herencia? ¿Dónde viaja la query en un POST?

HARD (difícil) — análisis de código con bugs sutiles, interpretación de un
fragmento que mezcla HTTP+JSON+OOP, distinción PUT/PATCH, detección de errores
en super(), elección entre verbos REST con varios distractores plausibles,
preguntas de marcar varias correctas reducidas a 4 opciones.
  Ej. ¿Cuál de estas opciones contiene SOLO verbos HTTP válidos? ¿Por qué
  falla este código de herencia?

═══════════════════════════════════════════════════════════════════════════════
REGLAS DE CALIDAD (OBLIGATORIAS)
═══════════════════════════════════════════════════════════════════════════════

1. IDIOMA: español neutro técnico. Misma terminología que los apuntes URJC
   (instancia, atributo, método, cabecera, idempotente, serializar, etc.).

2. TÍTULO ("title"): es el ENUNCIADO completo de la pregunta.
   - Puede contener un fragmento de código si la pregunta lo requiere.
   - Usa \\n para saltos de línea dentro del JSON.
   - Indenta el código con 4 espacios (NO tabs).
   - NO incluyas la respuesta en el enunciado.
   - NO empieces con "Pregunta:" ni con numeración tipo "1.".

3. OPCIONES ("options"): EXACTAMENTE 4 strings.
   - Mutuamente excluyentes (solo una correcta).
   - Longitud similar entre ellas (un distractor demasiado corto delata la
     respuesta).
   - Distractores PLAUSIBLES: errores frecuentes que cometería un estudiante
     de PER (confundir loads/load, confundir PUT/POST, olvidar super(),
     mezclar GET/POST en la URL, confundir cliente/servidor en sockets...).
   - NO uses "todas las anteriores" / "ninguna de las anteriores" salvo que
     pedagógicamente aporten.
   - NO empieces las opciones con letras (a), b), c)) — eso lo añade la UI.

4. RESPUESTA CORRECTA ("correct_answer_id"): entero 0, 1, 2 o 3.
   - DEBE ROTAR: NO siempre 0. Distribuye el correcto aleatoriamente entre
     las 4 posiciones.

5. EXPLICACIÓN ("explanation"): didáctica, exhaustiva, 4-8 frases.
   - Frase 1: "La respuesta correcta es la {LETRA}. ..." indicando POR QUÉ.
   - Resto: explica brevemente por qué cada distractor es incorrecto,
     mencionando el error conceptual que detectaría.
   - Si la pregunta es sobre código: traza la ejecución paso a paso.
   - Si es sobre HTTP/REST: cita el verbo o cabecera concreta.

6. ANTI-REPETICIÓN: NO uses siempre los mismos ejemplos. Varía:
   - Los nombres de clases (no siempre Coche, Persona, Animal: prueba con
     Libro, Empleado, Producto, Pedido, Cuenta, Cronometro, Factura, Tiempo,
     Rectangulo, Punto, Vehiculo, Mascota, Estudiante…).
   - Los dominios (no siempre coches: usa libros, bancos, animales,
     facturación, planetas, biblioteca, tienda online, geometría…).
   - Los verbos HTTP del ejemplo (no siempre GET/POST: incluye PUT, PATCH,
     DELETE, HEAD).
   - Los temas: si te piden EASY, no generes 3 veces seguidas la misma
     pregunta sobre __init__.

7. FORMATO DE SALIDA: JSON ESTRICTO, sin texto fuera, sin markdown:
{
  "title": "Enunciado completo (puede tener saltos de línea con \\n)",
  "options": ["...", "...", "...", "..."],
  "correct_answer_id": <0|1|2|3>,
  "explanation": "..."
}
"""


def _build_user_message(difficulty: str) -> str:
    """
    Construye el mensaje de usuario inyectando un tema concreto del catálogo
    para forzar variedad y evitar la repetición típica de "genera una pregunta easy".
    """
    diff = difficulty.lower()
    if diff not in TOPIC_CATALOG:
        diff = "easy"

    # Elegimos un bloque y un subtema concreto al azar:
    bloque = random.choice(list(TOPIC_CATALOG[diff].keys()))
    subtema = random.choice(TOPIC_CATALOG[diff][bloque])

    # Variedad de "sabor" en el tipo de pregunta para reducir uniformidad:
    estilos = [
        "una pregunta conceptual pura, sin código",
        "una pregunta que incluya un fragmento de código corto (5-12 líneas) y "
        "pida interpretar qué hace, qué imprime o detectar un error",
        "una pregunta que muestre una traza, una URL, una cabecera HTTP o un JSON "
        "y pida identificar algún aspecto concreto",
    ]
    # Las preguntas de POO_AVANZADA y PRACTICAS_REALES casi siempre llevan código:
    if bloque in {"POO_AVANZADA", "PRACTICAS_REALES", "SERVIDOR_HTTP_PYTHON"}:
        estilo = estilos[1]
    elif bloque in {"HTTP_AVANZADO", "HTTP_INTERMEDIO", "SOCKETS_INTERMEDIO"}:
        estilo = random.choice([estilos[1], estilos[2]])
    else:
        estilo = random.choice(estilos)

    return (
        f"Genera UNA pregunta tipo test de dificultad **{diff.upper()}** sobre el bloque "
        f"**{bloque}**, centrada concretamente en: \"{subtema}\".\n\n"
        f"Estilo solicitado: {estilo}.\n\n"
        f"Reglas adicionales para esta generación:\n"
        f"- La respuesta correcta NO puede ser siempre la primera opción: "
        f"distribuye aleatoriamente entre las 4 posiciones.\n"
        f"- Usa nombres de clases / variables / dominios variados, NO recurras "
        f"siempre a Coche, Persona o Animal.\n"
        f"- Devuelve EXCLUSIVAMENTE el JSON con las claves "
        f"title, options, correct_answer_id, explanation. Sin markdown, sin "
        f"comentarios."
    )


def _validate_challenge(data: Dict[str, Any]) -> None:
    """Valida que el JSON cumpla EXACTAMENTE el formato esperado por la app."""
    required = ["title", "options", "correct_answer_id", "explanation"]
    for field in required:
        if field not in data:
            raise ValueError(f"Missing required field: {field}")

    if not isinstance(data["title"], str) or not data["title"].strip():
        raise ValueError("title must be a non-empty string")

    if not isinstance(data["options"], list) or len(data["options"]) != 4:
        raise ValueError("options must be a list of exactly 4 items")

    if not all(isinstance(o, str) and o.strip() for o in data["options"]):
        raise ValueError("each option must be a non-empty string")

    if not isinstance(data["correct_answer_id"], int) or not (0 <= data["correct_answer_id"] <= 3):
        raise ValueError("correct_answer_id must be int in [0, 3]")

    if not isinstance(data["explanation"], str) or len(data["explanation"]) < 20:
        raise ValueError("explanation must be a meaningful string")


def _build_messages(difficulty: str) -> List[Dict[str, str]]:
    """
    Construye el array de mensajes con system + ejemplos few-shot + petición.
    Los ejemplos se inyectan como turnos previos (assistant/user) para que
    el modelo aprenda el estilo.
    """
    msgs: List[Dict[str, str]] = [{"role": "system", "content": SYSTEM_PROMPT}]

    # 2 ejemplos few-shot rotatorios (no metemos los 6 cada vez para no gastar tokens):
    sample = random.sample(FEW_SHOT_EXAMPLES, k=2)
    for ex in sample:
        msgs.append({
            "role": "user",
            "content": "Genera una pregunta tipo test siguiendo el formato indicado.",
        })
        msgs.append({
            "role": "assistant",
            "content": json.dumps(ex, ensure_ascii=False),
        })

    # Petición real:
    msgs.append({"role": "user", "content": _build_user_message(difficulty)})
    return msgs


def generate_challenge_with_ai(difficulty: str) -> Dict[str, Any]:
    """
    Genera una pregunta tipo test con IA.
    El formato devuelto es EXACTAMENTE el mismo que el sistema anterior
    (title, options, correct_answer_id, explanation), por lo que es 100%
    compatible con el resto del backend y del frontend.
    """
    try:
        response = client.chat.completions.create(
            # Modelo mejor: gpt-4o-mini da resultados notablemente más coherentes
            # que gpt-3.5-turbo para preguntas con razonamiento técnico, y sigue
            # siendo barato. Si quieres mantener 3.5 cambia solo esta línea.
            model="gpt-4o-mini",
            messages=_build_messages(difficulty),
            response_format={"type": "json_object"},
            # Temperatura más baja → menos repetitivo en estructura, más fiel
            # al estilo few-shot. La variedad la introducimos vía catálogo de
            # temas y rotación de ejemplos, no vía aleatoriedad cruda.
            temperature=0.55,
            # Penalizaciones para evitar repetir vocabulario y abrirse a
            # nuevos ejemplos:
            presence_penalty=0.4,
            frequency_penalty=0.3,
            max_tokens=1200,
        )

        content = response.choices[0].message.content
        challenge_data = json.loads(content)
        _validate_challenge(challenge_data)
        return challenge_data

    except Exception as e:
        print(f"[ai_generator] Error generando pregunta: {e}")
        # Fallback de calidad — sigue siendo del temario real:
        return {
            "title": (
                "Observa el siguiente código en Python y selecciona la afirmación correcta:\n\n"
                "class Libro:\n"
                "    def __init__(self, titulo):\n"
                "        self.titulo = titulo\n\n"
                "libro1 = Libro(\"1984\")\n"
                "libro2 = libro1"
            ),
            "options": [
                "Se han creado dos objetos diferentes de la clase Libro en memoria.",
                "libro1 y libro2 son dos variables que referencian al mismo objeto en memoria.",
                "libro2 es una clase que hereda de Libro.",
                "El código produce un error porque falta un constructor explícito.",
            ],
            "correct_answer_id": 1,
            "explanation": (
                "La respuesta correcta es la B. En Python, la asignación libro2 = libro1 "
                "no crea un nuevo objeto: solo hace que libro2 referencie al mismo objeto "
                "que libro1. Por eso ambas variables apuntan a la misma instancia.\n\n"
                "A es incorrecta porque solo se ha llamado a Libro() una vez (un solo "
                "objeto). C confunde asignación de variables con herencia: para heredar "
                "haría falta 'class libro2(Libro):'. D es falsa: __init__ está definido "
                "correctamente."
            ),
        }
