"""
Configuración centralizada del proyecto Agente de Visión
"""
# Importa el módulo os para operaciones del sistema
import os
# Importa Path para manejo de rutas
from pathlib import Path

# Rutas del proyecto
BASE_DIR = Path(__file__).parent  # Directorio base del proyecto
MODELS_DIR = BASE_DIR / "models"  # Carpeta de modelos

# Configuración de la CNN (Local)
MODEL_PATH = os.getenv("MODEL_PATH", "models/emotion_model.h5")  # Ruta al modelo CNN

# Configuración de Ollama
OLLAMA_BASE_URL = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")  # URL base de Ollama
OLLAMA_MODEL = os.getenv("OLLAMA_MODEL", "llama3:latest")  # Modelo por defecto de Ollama

# Configuración de usuarios
USERS = {
    "abrahan": {
        "name": "Abrahan",  # Nombre del usuario
        "prompt_template": "Eres un asistente amigable. Usuario: {user_name}. Responde cordialmente.",  # Plantilla de prompt
        "personality": "profesional"  # Personalidad del asistente
    },
    "jesus": {
        "name": "Jesus",  # Nombre del usuario
        "prompt_template": "Eres un asistente creativo. Usuario: {user_name}. Responde creativamente.",  # Plantilla de prompt
        "personality": "creativo"  # Personalidad del asistente
    }
}

# Configuración de emociones
EMOTIONS = [
    "cansado", "enojado", "feliz", "pensativo", "riendo", "sorprendido", "triste"  # Lista de emociones posibles
] 