"""
Configuración centralizada del proyecto Agente de Visión
"""
import os
from pathlib import Path

# Rutas del proyecto
BASE_DIR = Path(__file__).parent
MODELS_DIR = BASE_DIR / "models"

# Configuración de la CNN (Local)
MODEL_PATH = os.getenv("MODEL_PATH", "models/emotion_model.h5")

# Configuración de Ollama
OLLAMA_BASE_URL = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")
OLLAMA_MODEL = os.getenv("OLLAMA_MODEL", "llama3:latest")

# Configuración de usuarios
USERS = {
    "user_a": {
        "name": "Abrahan",
        "prompt_template": "Eres un asistente amigable y profesional. El usuario es {user_name}. Responde de manera cordial y útil.",
        "personality": "profesional"
    },
    "user_b": {
        "name": "Jesus", 
        "prompt_template": "Eres un asistente creativo y dinámico. El usuario es {user_name}. Responde de manera creativa y entusiasta.",
        "personality": "creativo"
    }
}

# Configuración de emociones
EMOTIONS = [
    "cansado", "enojado", "feliz", "pensativo", "riendo", "sorprendido", "triste"
] 