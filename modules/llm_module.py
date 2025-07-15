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
        Crea el prompt personalizado optimizado para velocidad
        """
        user_config = USERS[user_id]
        
        # Prompt base del usuario (más conciso)
        base_prompt = user_config["prompt_template"].format(user_name=user_config["name"])
        
        # Contexto emocional (más corto)
        emotion_context = self._get_emotion_context(emotion)
        
        # Historial de conversación (limitado a 3 interacciones)
        history_context = ""
        if conversation_history:
            history_context = "\nContexto reciente:\n"
            for entry in conversation_history[-3:]:  # Solo últimas 3 interacciones
                history_context += f"U: {entry['user_message'][:100]}...\n"  # Limitar longitud
                history_context += f"A: {entry['assistant_response'][:100]}...\n"
        
        # Prompt final optimizado
        final_prompt = f"""{base_prompt}
{emotion_context}
{history_context}
Usuario ({emotion}): {message}
Asistente:"""
        
        return final_prompt
    
    def _get_emotion_context(self, emotion: str) -> str:
        """
        Proporciona contexto emocional optimizado para velocidad
        """
        emotion_contexts = {
            "feliz": "Usuario feliz. Responde con alegría.",
            "triste": "Usuario triste. Sé empático.",
            "enojado": "Usuario enojado. Mantén calma.",
            "sorprendido": "Usuario sorprendido. Sé claro.",
            "pensativo": "Usuario pensativo. Sé reflexivo.",
            "cansado": "Usuario cansado. Sé comprensivo.",
            "riendo": "Usuario riendo. Responde con humor.",
            "sorprendido": "Usuario sorprendido. Sé claro."
        }
        
        return emotion_contexts.get(emotion, "Responde apropiadamente.")
    
    def generate_response(self, user_id: str, emotion: str, message: str, conversation_history: List[Dict] = None) -> Dict:
        """
        Genera una respuesta usando el modelo de Ollama con optimizaciones para velocidad
        """
        try:
            if conversation_history is None:
                conversation_history = []
            
            # Crear prompt personalizado (más conciso)
            prompt = self._create_prompt(user_id, emotion, message, conversation_history)
            
            # Preparar payload optimizado para velocidad
            payload = {
                "model": self.model,
                "prompt": prompt,
                "stream": False,
                "options": {
                    "temperature": 0.5,  # Reducido para respuestas más rápidas
                    "top_p": 0.8,        # Reducido para mayor velocidad
                    "max_tokens": 200,    # Reducido para respuestas más cortas
                    "num_predict": 150,   # Limitar tokens de predicción
                    "top_k": 40,         # Reducir opciones de tokens
                    "repeat_penalty": 1.1 # Evitar repeticiones
                }
            }
            
            # Hacer request a Ollama con timeout optimizado
            response = requests.post(
                f"{self.base_url}/api/generate",
                json=payload,
                timeout=15  # Reducido a 15 segundos
            )
            
            if response.status_code == 200:
                result = response.json()
                respuesta = result.get("response", "").strip()
                
                if not respuesta:
                    # Respuesta de fallback rápida
                    fallback_response = self._get_fallback_response(emotion, user_id)
                    return {
                        "response": fallback_response,
                        "success": True,
                        "model_used": self.model,
                        "fallback": True
                    }
                
                return {
                    "response": respuesta,
                    "success": True,
                    "model_used": self.model
                }
            else:
                self.logger.error(f"Error en Ollama API: {response.status_code}")
                fallback_response = self._get_fallback_response(emotion, user_id)
                return {
                    "success": True, 
                    "error": f"Ollama API error: {response.status_code}", 
                    "response": fallback_response,
                    "fallback": True
                }
                
        except requests.Timeout:
            self.logger.error("Timeout al esperar respuesta del modelo LLM.")
            fallback_response = self._get_fallback_response(emotion, user_id)
            return {
                "success": True, 
                "error": "Timeout del modelo LLM", 
                "response": fallback_response,
                "fallback": True
            }
        except Exception as e:
            self.logger.error(f"Error al generar respuesta: {e}")
            fallback_response = self._get_fallback_response(emotion, user_id)
            return {
                "success": True, 
                "error": str(e), 
                "response": fallback_response,
                "fallback": True
            }
    
    def _get_fallback_response(self, emotion: str, user_id: str) -> str:
        """
        Genera respuestas de fallback rápidas cuando el modelo no responde
        """
        user_name = USERS.get(user_id, {}).get("name", "Usuario")
        
        fallback_responses = {
            "feliz": f"¡Hola {user_name}! Veo que estás feliz. ¿En qué puedo ayudarte hoy?",
            "triste": f"Hola {user_name}, veo que estás triste. ¿Te gustaría hablar sobre algo?",
            "enojado": f"Hola {user_name}, entiendo que estés molesto. ¿Qué puedo hacer para ayudarte?",
            "sorprendido": f"¡Hola {user_name}! Pareces sorprendido. ¿Qué te ha llamado la atención?",
            "pensativo": f"Hola {user_name}, veo que estás pensativo. ¿En qué estás reflexionando?",
            "cansado": f"Hola {user_name}, parece que estás cansado. ¿Necesitas descansar o hay algo en lo que pueda ayudarte?",
            "riendo": f"¡Hola {user_name}! Me alegra verte riendo. ¿Qué te hace tan feliz?"
        }
        
        return fallback_responses.get(emotion, f"¡Hola {user_name}! ¿En qué puedo ayudarte?")
    
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