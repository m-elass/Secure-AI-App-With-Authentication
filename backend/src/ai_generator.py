import os
import json

from openai import OpenAI
from typing import Dict, Any
from dotenv import load_dotenv

load_dotenv()

client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

def generate_challenge_with_ai(difficulty: str) -> Dict[str, Any]:
    system_prompt = """Eres un Mentor Senior de Python y experto en pedagogía de programación. Tu objetivo es generar desafíos de código técnicos, precisos y educativos siguiendo estrictamente las enseñanzas de:
1. "Python 3 Object-Oriented Programming" (Dusty Phillips) - Especialmente conceptos de diseño de clases, herencia y polimorfismo (Caps 1, 2, 3, 5).
2. "Programming Python" (Mark Lutz) - Para aplicaciones de sistemas y herramientas avanzadas.
3. "Ultimate Python Programming" y "LibrosWeb (Cap. 5)" - Para fundamentos sólidos y estructuras de control.

REGLAS DE GENERACIÓN SEGÚN DIFICULTAD:
- EASY: Sintaxis básica, tipos de datos, bucles y condicionales (Basado en LibrosWeb).
- MEDIUM: Estructuras de datos avanzadas, funciones, manejo de excepciones y fundamentos de OOP (Objetos vs Clases, Herencia básica).
- HARD: OOP avanzado (MRO, Mixins, Composición), Decoradores, Context Managers, comandos complejos de Git (rebase, bisect, cherry-pick) y patrones de diseño.

CALIDAD DE LAS PREGUNTAS:
- Los títulos deben ser técnicos y profesionales.
- Las opciones incorrectas deben ser "distractores plausibles" (errores comunes que cometería un programador).
- La explicación DEBE ser exhaustiva: explica por qué la respuesta correcta es la única válida técnica y lógicamente, y menciona brevemente por qué las otras opciones fallan o son malas prácticas.

FORMATO DE SALIDA (JSON ESTRICTO):
{
    "title": "Título técnico de la pregunta",
    "options": ["Opción A", "Opción B", "Opción C", "Opción D"],
    "correct_answer_id": 0,
    "explanation": "Explicación detallada: La opción X es correcta porque... Mientras que las opciones Y y Z son incorrectas debido a..."
}
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