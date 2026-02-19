# groq_client.py - Conexión con la IA

from groq import Groq
from dotenv import load_dotenv
import os

load_dotenv()  # Lee las variables del archivo .env

cliente = Groq(api_key=os.getenv("GROQ_API_KEY"))

def obtener_respuesta(mensaje_usuario, nivel, historial):
    """
    Llama a la IA con el mensaje del usuario y el historial de conversación
    """
    from levels import LEVELS
    
    system_prompt = LEVELS[nivel]
    
    # Construye la lista de mensajes: historial + mensaje nuevo
    mensajes = [
        {"role": "system", "content": system_prompt},
        *historial,
        {"role": "user", "content": mensaje_usuario}
    ]
    
    respuesta = cliente.chat.completions.create(
        model="llama-3.1-8b-instant",  # Modelo gratis de Groq
        messages=mensajes,
        temperature=0.7,    # Creatividad moderada
        max_tokens=400      # Respuestas no muy largas
    )
    
    texto = respuesta.choices[0].message.content
    
    # Agrega el intercambio al historial
    historial.append({"role": "user", "content": mensaje_usuario})
    historial.append({"role": "assistant", "content": texto})
    
    return texto