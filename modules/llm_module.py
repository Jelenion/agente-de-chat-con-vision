"""
Módulo 2: LLM - Integración con Ollama Local
"""
import requests
import json
from typing import Dict, List, Optional
from loguru import logger

from config import OLLAMA_BASE_URL, OLLAMA_MODEL, USERS


class LLMModule:
    """
    Módulo de LLM que se conecta con Ollama local
    """
    
    def __init__(self):
        self.base_url = OLLAMA_BASE_URL
        self.model = OLLAMA_MODEL
        self.logger = logger
        
    def _create_prompt(self, user_id: str, emotion: str, message: str, conversation_history: List[Dict]) -> str:
        """
        Crea el prompt personalizado basado en el usuario y su emoción
        """
        user_config = USERS[user_id]
        
        # Prompt base del usuario
        base_prompt = user_config["prompt_template"].format(user_name=user_config["name"])
        
        # Contexto emocional
        emotion_context = self._get_emotion_context(emotion)
        
        # Historial de conversación
        history_context = ""
        if conversation_history:
            history_context = "\n\nHistorial de conversación:\n"
            for entry in conversation_history[-5:]:  # Últimas 5 interacciones
                history_context += f"Usuario: {entry['user_message']}\n"
                history_context += f"Asistente: {entry['assistant_response']}\n"
        
        # Prompt final
        final_prompt = f"""{base_prompt}

{emotion_context}

{history_context}

Usuario (estado emocional: {emotion}): {message}

Asistente:"""
        
        return final_prompt
    
    def _get_emotion_context(self, emotion: str) -> str:
        """
        Proporciona contexto basado en la emoción detectada
        """
        emotion_contexts = {
            "feliz": "El usuario parece estar feliz. Mantén un tono positivo y alegre en tu respuesta.",
            "triste": "El usuario parece estar triste. Sé empático y ofrece apoyo emocional.",
            "enojado": "El usuario parece estar enojado. Mantén la calma y sé comprensivo.",
            "sorprendido": "El usuario parece estar sorprendido. Sé claro y explicativo en tu respuesta.",
            "neutral": "El usuario parece estar neutral. Mantén un tono equilibrado y profesional.",
            "asustado": "El usuario parece estar asustado. Sé tranquilizador y ofrecer seguridad.",
            "disgustado": "El usuario parece estar disgustado. Sé respetuoso y evita temas sensibles."
        }
        
        return emotion_contexts.get(emotion, "Mantén un tono apropiado y profesional.")
    
    def generate_response(self, user_id: str, emotion: str, message: str, conversation_history: List[Dict] = None) -> Dict:
        """
        Genera una respuesta usando el modelo de Ollama
        """
        try:
            if conversation_history is None:
                conversation_history = []
            
            # Crear prompt personalizado
            prompt = self._create_prompt(user_id, emotion, message, conversation_history)
            
            # Preparar payload para Ollama
            payload = {
                "model": self.model,
                "prompt": prompt,
                "stream": False,
                "options": {
                    "temperature": 0.7,
                    "top_p": 0.9,
                    "max_tokens": 500
                }
            }
            
            # Hacer request a Ollama
            response = requests.post(
                f"{self.base_url}/api/generate",
                json=payload,
                timeout=60
            )
            
            if response.status_code == 200:
                result = response.json()
                return {
                    "response": result.get("response", "").strip(),
                    "success": True,
                    "model_used": self.model
                }
            else:
                self.logger.error(f"Error en Ollama API: {response.status_code}")
                return {"success": False, "error": "Ollama API error"}
                
        except Exception as e:
            self.logger.error(f"Error al generar respuesta: {e}")
            return {"success": False, "error": str(e)}
    
    def get_available_models(self) -> List[str]:
        """
        Obtiene la lista de modelos disponibles en Ollama
        """
        try:
            response = requests.get(f"{self.base_url}/api/tags")
            
            if response.status_code == 200:
                result = response.json()
                models = [model["name"] for model in result.get("models", [])]
                return models
            else:
                self.logger.error(f"Error al obtener modelos: {response.status_code}")
                return []
                
        except Exception as e:
            self.logger.error(f"Error al obtener modelos disponibles: {e}")
            return []
    
    def test_connection(self) -> bool:
        """
        Prueba la conexión con Ollama
        """
        try:
            response = requests.get(f"{self.base_url}/api/tags", timeout=10)
            return response.status_code == 200
        except Exception as e:
            self.logger.error(f"Error al conectar con Ollama: {e}")
            return False
    
    def change_model(self, new_model: str) -> bool:
        """
        Cambia el modelo de Ollama
        """
        try:
            # Verificar si el modelo está disponible
            available_models = self.get_available_models()
            if new_model in available_models:
                self.model = new_model
                self.logger.info(f"Modelo cambiado a: {new_model}")
                return True
            else:
                self.logger.error(f"Modelo {new_model} no disponible")
                return False
        except Exception as e:
            self.logger.error(f"Error al cambiar modelo: {e}")
            return False 