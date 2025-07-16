"""
Módulo LLM mejorado para integración local con Ollama (Llama3)
"""
# Importa requests para peticiones HTTP a la API de Ollama
import requests  # Para hacer peticiones HTTP a la API de Ollama
# Importa random para respuestas de fallback aleatorias
import random  # Para seleccionar respuestas de fallback aleatorias
# Importa tipos para anotaciones
from typing import Dict, List, Optional  # Tipos para anotaciones
# Importa logger para depuración
from loguru import logger  # Logger para depuración
# Importa configuración global
from config import OLLAMA_BASE_URL, OLLAMA_MODEL, USERS  # Configuración global

class LLMModule:
    """
    Módulo de LLM para chat continuo y robusto con Ollama local
    """

    def __init__(self):
        self.base_url = OLLAMA_BASE_URL  # URL base de la API de Ollama
        self.model = OLLAMA_MODEL  # Modelo por defecto
        self.logger = logger  # Logger para mensajes

    def _build_prompt(self, user_id: str, emotion: str, message: str, conversation_history: List[Dict]) -> str:
        """
        Construye un prompt tipo chat continuo, con contexto emocional solo si hay usuario y emoción.
        """
        # Si no hay usuario o emoción, prompt genérico
        if not user_id or not emotion:
            prompt = "Eres un asistente conversacional profesional.\nChat:\n"  # Prompt base
            for entry in conversation_history[-3:]:  # Últimos 3 turnos
                prompt += f"Usuario: {entry['user_message']}\n"  # Mensaje del usuario
                prompt += f"Asistente: {entry['assistant_response']}\n"  # Respuesta del asistente
            prompt += f"Usuario: {message}\nAsistente:"
            return prompt

        # Si hay usuario y emoción, prompt personalizado
        user_config = USERS[user_id]  # Configuración del usuario
        user_name = user_config["name"]  # Nombre del usuario
        prompt = (
            f"Eres un asistente conversacional empático y profesional.\n"
            f"Usuario: {user_name}\n"
            f"Emoción actual: {emotion}\n\n"
            f"Chat:\n"
        )
        for entry in conversation_history[-3:]:  # Últimos 3 turnos
            prompt += f"{user_name}: {entry['user_message']}\n"  # Mensaje del usuario
            prompt += f"Asistente: {entry['assistant_response']}\n"  # Respuesta del asistente
        prompt += f"{user_name}: {message}\nAsistente:"
        return prompt

    def _get_fallback_response(self, emotion: str, user_id: str) -> str:
        """
        Respuestas de fallback variadas según emoción.
        """
        user_name = USERS.get(user_id, {}).get("name", "Usuario")  # Nombre del usuario
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
        return random.choice(opciones)  # Selecciona una respuesta aleatoria

    def generate_response(self, user_id: str, emotion: str, message: str, conversation_history: Optional[List[Dict]] = None) -> Dict:
        """
        Genera una respuesta usando Ollama local (Llama3) con manejo robusto de errores y logs.
        """
        try:
            if conversation_history is None:
                conversation_history = []  # Si no hay historial, lo inicializa

            prompt = self._build_prompt(user_id, emotion, message, conversation_history)  # Construye el prompt

            payload = {
                "model": self.model,  # Modelo a usar
                "prompt": prompt,  # Prompt generado
                "stream": False,  # No streaming
                "options": {
                    "temperature": 0.7,  # Temperatura de muestreo
                    "top_p": 0.9,  # Top-p sampling
                    "max_tokens": 256,  # Máximo de tokens
                    "num_predict": 100,  # Tokens a predecir
                    "top_k": 40,  # Top-k sampling
                    "repeat_penalty": 1.1  # Penalización de repetición
                }
            }

            response = requests.post(
                f"{self.base_url}/api/generate",  # Endpoint de generación
                json=payload,  # Payload como JSON
                timeout=30  # Timeout de 30 segundos
            )

            self.logger.debug(f"Respuesta cruda de Ollama: {response.text}")  # Log de la respuesta

            if response.status_code == 200:
                try:
                    result = response.json()  # Intenta decodificar JSON
                except Exception as e:
                    self.logger.error(f"Respuesta no es JSON válido: {response.text}")  # Log de error
                    fallback_response = self._get_fallback_response(emotion, user_id)  # Respuesta de respaldo
                    return {
                        "success": True,
                        "error": f"Respuesta no es JSON válido: {e}",
                        "response": fallback_response,
                        "fallback": True
                    }
                respuesta = result.get("response", "").strip()  # Extrae la respuesta

                if not respuesta or not respuesta.strip():  # Si la respuesta está vacía
                    fallback_response = self._get_fallback_response(emotion, user_id)  # Respuesta de respaldo
                    return {
                        "response": fallback_response,
                        "success": True,
                        "model_used": self.model,
                        "fallback": True
                    }

                return {
                    "response": respuesta,  # Respuesta generada
                    "success": True,  # Éxito
                    "model_used": self.model  # Modelo usado
                }
            else:
                self.logger.error(f"Error en Ollama API: {response.status_code}")  # Log de error
                fallback_response = self._get_fallback_response(emotion, user_id)  # Respuesta de respaldo
                return {
                    "success": True,
                    "error": f"Ollama API error: {response.status_code}",
                    "response": fallback_response,
                    "fallback": True
                }

        except requests.Timeout:
            self.logger.error("Timeout al esperar respuesta del modelo LLM.")  # Log de timeout
            fallback_response = self._get_fallback_response(emotion, user_id)  # Respuesta de respaldo
            return {
                "success": True,
                "error": "Timeout del modelo LLM",
                "response": fallback_response,
                "fallback": True
            }
        except Exception as e:
            self.logger.error(f"Error al generar respuesta: {e}")  # Log de error general
            fallback_response = self._get_fallback_response(emotion, user_id)  # Respuesta de respaldo
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
            conversation_history = []  # Inicializa historial si no existe
        prompt = self._build_prompt(user_id, emotion, message, conversation_history)  # Construye el prompt
        payload = {
            "model": self.model,  # Modelo a usar
            "prompt": prompt,  # Prompt generado
            "stream": True,  # Activa streaming
            "options": {
                "temperature": 0.7,  # Temperatura de muestreo
                "top_p": 0.9,  # Top-p sampling
                "max_tokens": 256,  # Máximo de tokens
                "num_predict": 100,  # Tokens a predecir
                "top_k": 40,  # Top-k sampling
                "repeat_penalty": 1.1  # Penalización de repetición
            }
        }
        try:
            with requests.post(f"{self.base_url}/api/generate", json=payload, stream=True, timeout=60) as response:
                response.raise_for_status()  # Lanza excepción si hay error HTTP
                for line in response.iter_lines(decode_unicode=True):  # Itera por fragmentos
                    if line:
                        try:
                            data = line.strip()  # Limpia línea
                            if data.startswith('{'):
                                import json
                                obj = json.loads(data)  # Decodifica JSON
                                fragment = obj.get("response", "")  # Extrae fragmento
                                if fragment:
                                    yield fragment  # Devuelve fragmento
                        except Exception as e:
                            continue  # Ignora errores de fragmentos
        except Exception as e:
            self.logger.error(f"Error en streaming LLM: {e}")  # Log de error
            yield f"[Error en streaming: {e}]"  # Devuelve error como fragmento

    def test_connection(self) -> bool:
        """
        Prueba la conexión con Ollama local.
        """
        try:
            response = requests.get(f"{self.base_url}/api/tags", timeout=10)  # Prueba endpoint de modelos
            return response.status_code == 200  # True si responde correctamente
        except Exception as e:
            self.logger.error(f"Error al conectar con Ollama: {e}")  # Log de error
            return False  # Falla la conexión

    def get_available_models(self) -> List[str]:
        """
        Obtiene la lista de modelos disponibles en Ollama local.
        """
        try:
            response = requests.get(f"{self.base_url}/api/tags")  # Solicita modelos
            if response.status_code == 200:
                result = response.json()  # Decodifica JSON
                models = [model["name"] for model in result.get("models", [])]  # Extrae nombres
                return models  # Lista de nombres de modelos
            else:
                self.logger.error(f"Error al obtener modelos: {response.status_code}")  # Log de error
                return []  # Devuelve lista vacía
        except Exception as e:
            self.logger.error(f"Error al obtener modelos disponibles: {e}")  # Log de error
            return []  # Devuelve lista vacía

    def change_model(self, new_model: str) -> bool:
        """
        Cambia el modelo de Ollama local.
        """
        try:
            available_models = self.get_available_models()  # Modelos disponibles
            if new_model in available_models:
                self.model = new_model  # Cambia el modelo
                self.logger.info(f"Modelo cambiado a: {new_model}")  # Log de cambio
                return True  # Cambio exitoso
            else:
                self.logger.error(f"Modelo {new_model} no disponible")  # Log de error
                return False  # Modelo no disponible
        except Exception as e:
            self.logger.error(f"Error al cambiar modelo: {e}")  # Log de error
            return False  # Falla el cambio 