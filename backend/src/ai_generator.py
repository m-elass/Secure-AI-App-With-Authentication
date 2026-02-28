import os
import json

from openai import OpenAI
from typing import Dict, Any
from dotenv import load_dotenv

load_dotenv()

client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

def generate_challenge_with_ai(difficulty: str) -> Dict[str, Any]:
    system_prompt = """Eres un creador de desafíos de programación de python experto.
    Tu objetivo es crear una pregunta sobre programación con múltiples respuestas.
    El usuario debe aprender programación en python.
    La pregunta debería ser conforme al nivel de dificultad seleccionado.
    Usa como fuente para las preguntas recursos del nivel de alumnos de primero de carrera en España.
    También puedes recurrir a webs como http://librosweb.es/libro/python/capitulo_5.html o libros como
    Python 3 Object-Oriented Programming - Second  Dusty Phillips(especialmente los capítulos 1, 2, 3, y 5);Programming Python, 4th Edition
    Ultimate Python Programming.
    Los títulos de las preguntas deben ser muy claros en cuanto a lo que se pregunta(nada de ambiguedad) y las respuestas relacionadas a este. No quiero que se repitan preguntas todo el rato, coherencia ante todo.
    quiero que todas las preguntas sean en Español.
    
    Para preguntas fáciles: centrate en lógica basica de python, la sintaxis, operadores y conceptos de programación básicos, así como de OOP.
    Para preguntas de dificultad media: sube la dificultad, yendo a resolucion lógica de problemas, estructura de datos y algoritmos,etc.
    Para preguntas difíciles: incluye temas avanzados, diseño, optimización de código, técnicas de optimización, desarrollo de porgramación orientada a objetos.
    
    Devuelve el desafío con la siguiente estructura de JSON:
    {
        "title": "El título de la pregunta",
        "options": ["Option 1", "Option 2", "Option 3", "Option 4"],
        "correct_answer_id": 0, // Index of the correct answer (0-3)
        "explanation": "Explicación detallada de porque la respuesta correcta esta bien y porque la incorrecta seleccionada está mal"
    }
    
    Asegúrate de que las opciones sean curiosas pero que sea muy claro que solo una respuesta es correcta. Asegúrate también de dar veredictictos correctos y no marcar como verdadero lo que en realidad es falso, no buscamos liar al usuario.
    """
    try:
        response = client.chat.completions.create(
            model="gpt-3.5-turbo-0125",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": f"Generate a {difficulty} difficulty coding challenge."}
            ],
            response_format={"type": "json_object"},
            temperature=0.7
        )

        content = response.choices[0].message.content
        challenge_data = json.loads(content)

        required_fields = ["title", "options", "correct_answer_id", "explanation"]
        for field in required_fields:
            if field not in challenge_data:
                raise ValueError(f"Missing required field: {field}")

        return challenge_data

    except Exception as e:
        print(e)
        return {
            "title": "Basic Python List Operation",
            "options": [
                "my_list.append(5)",
                "my_list.add(5)",
                "my_list.push(5)",
                "my_list.insert(5)",
            ],
            "correct_answer_id": 0,
            "explanation": "In Python, append() is the correct method to add an element to the end of a list."
        }