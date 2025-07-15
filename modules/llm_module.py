"""
Módulo LLM mejorado para integración local con Ollama (Llama3)
"""
import requests
import random
from typing import Dict, List, Optional
from loguru import logger
from config import OLLAMA_BASE_URL, OLLAMA_MODEL, USERS

class LLMModule:
    """
    Módulo de LLM para chat continuo y robusto con Ollama local
    """

    def __init__(self):
        self.base_url = OLLAMA_BASE_URL
        self.model = OLLAMA_MODEL
        self.logger = logger

    def _build_prompt(self, user_id: str, emotion: str, message: str, conversation_history: List[Dict]) -> str:
        """
        Construye un prompt tipo chat continuo, con contexto emocional solo si hay usuario y emoción.
        """
        # Si no hay usuario o emoción, prompt genérico
        if not user_id or not emotion:
            prompt = "Eres un asistente conversacional profesional.\nChat:\n"
            for entry in conversation_history[-3:]:
                prompt += f"Usuario: {entry['user_message']}\n"
                prompt += f"Asistente: {entry['assistant_response']}\n"
            prompt += f"Usuario: {message}\nAsistente:"
            return prompt

        # Si hay usuario y emoción, prompt personalizado
        user_config = USERS[user_id]
        user_name = user_config["name"]
        prompt = (
            f"Eres un asistente conversacional empático y profesional.\n"
            f"Usuario: {user_name}\n"
            f"Emoción actual: {emotion}\n\n"
            f"Chat:\n"
        )
        for entry in conversation_history[-3:]:
            prompt += f"{user_name}: {entry['user_message']}\n"
            prompt += f"Asistente: {entry['assistant_response']}\n"
        prompt += f"{user_name}: {message}\nAsistente:"
        return prompt

    def _get_fallback_response(self, emotion: str, user_id: str) -> str:
        """
        Respuestas de fallback variadas según emoción.
        """
        user_name = USERS.get(user_id, {}).get("name", "Usuario")
        fallback_responses = {
            "pensativo": [
                f"¿Quieres contarme en qué piensas, {user_name}?",
                f"Si necesitas hablar de tus pensamientos, aquí estoy.",
                f"¿Te gustaría compartir lo que te preocupa, {user_name}?"
            ],
            "feliz": [
                f"¡Me alegra verte feliz, {user_name}! ¿Qué te hace sentir así?",
                f"¡Qué bueno verte de buen ánimo, {user_name}!",
                f"¡Genial, {user_name}! ¿Quieres compartir tu alegría?"
            ],
            "triste": [
                f"Si quieres hablar de lo que te pone triste, aquí estoy, {user_name}.",
                f"¿Te gustaría compartir lo que te preocupa, {user_name}?",
                f"Recuerda que no estás solo, {user_name}."
            ],
            "enojado": [
                f"Entiendo que estés molesto, {user_name}. ¿Quieres desahogarte?",
                f"Si necesitas hablar de lo que te enoja, aquí estoy, {user_name}.",
                f"A veces expresar lo que sentimos ayuda, {user_name}."
            ],
            "cansado": [
                f"Si necesitas descansar, tómate tu tiempo, {user_name}.",
                f"¿Quieres hablar de lo que te cansa, {user_name}?",
                f"Recuerda cuidar de ti mismo, {user_name}."
            ],
            "riendo": [
                f"¡Me alegra verte riendo, {user_name}! ¿Qué te hace tan feliz?",
                f"¡Qué bueno verte de buen humor, {user_name}!",
                f"¡Sigue disfrutando, {user_name}!"
            ],
            "sorprendido": [
                f"¿Qué te ha sorprendido, {user_name}?",
                f"¡Vaya sorpresa, {user_name}! ¿Quieres contarme más?",
                f"Cuéntame qué te sorprendió, {user_name}."
            ]
        }
        opciones = fallback_responses.get(emotion, [f"¿En qué puedo ayudarte, {user_name}?"])
        return random.choice(opciones)

    def generate_response(self, user_id: str, emotion: str, message: str, conversation_history: Optional[List[Dict]] = None) -> Dict:
        """
        Genera una respuesta usando Ollama local (Llama3) con manejo robusto de errores y logs.
        """
        try:
            if conversation_history is None:
                conversation_history = []

            prompt = self._build_prompt(user_id, emotion, message, conversation_history)

            payload = {
                "model": self.model,
                "prompt": prompt,
                "stream": False,
                "options": {
                    "temperature": 0.7,
                    "top_p": 0.9,
                    "max_tokens": 80,
                    "num_predict": 100,
                    "top_k": 40,
                    "repeat_penalty": 1.1
                }
            }

            response = requests.post(
                f"{self.base_url}/api/generate",
                json=payload,
                timeout=30
            )

            self.logger.debug(f"Respuesta cruda de Ollama: {response.text}")

            if response.status_code == 200:
                try:
                    result = response.json()
                except Exception as e:
                    self.logger.error(f"Respuesta no es JSON válido: {response.text}")
                    fallback_response = self._get_fallback_response(emotion, user_id)
                    return {
                        "success": True,
                        "error": f"Respuesta no es JSON válido: {e}",
                        "response": fallback_response,
                        "fallback": True
                    }
                respuesta = result.get("response", "").strip()

                if not respuesta or not respuesta.strip():
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

    def generate_response_stream(self, user_id: str, emotion: str, message: str, conversation_history: Optional[List[Dict]] = None):
        """
        Genera una respuesta usando Ollama local (Llama3) en modo streaming (fragmentos).
        """
        if conversation_history is None:
            conversation_history = []
        prompt = self._build_prompt(user_id, emotion, message, conversation_history)
        payload = {
            "model": self.model,
            "prompt": prompt,
            "stream": True,
            "options": {
                "temperature": 0.7,
                "top_p": 0.9,
                "max_tokens": 80,
                "num_predict": 100,
                "top_k": 40,
                "repeat_penalty": 1.1
            }
        }
        try:
            with requests.post(f"{self.base_url}/api/generate", json=payload, stream=True, timeout=60) as response:
                response.raise_for_status()
                for line in response.iter_lines(decode_unicode=True):
                    if line:
                        try:
                            data = line.strip()
                            if data.startswith('{'):
                                import json
                                obj = json.loads(data)
                                fragment = obj.get("response", "")
                                if fragment:
                                    yield fragment
                        except Exception as e:
                            continue
        except Exception as e:
            self.logger.error(f"Error en streaming LLM: {e}")
            yield f"[Error en streaming: {e}]"

    def test_connection(self) -> bool:
        """
        Prueba la conexión con Ollama local.
        """
        try:
            response = requests.get(f"{self.base_url}/api/tags", timeout=10)
            return response.status_code == 200
        except Exception as e:
            self.logger.error(f"Error al conectar con Ollama: {e}")
            return False

    def get_available_models(self) -> List[str]:
        """
        Obtiene la lista de modelos disponibles en Ollama local.
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

    def change_model(self, new_model: str) -> bool:
        """
        Cambia el modelo de Ollama local.
        """
        try:
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