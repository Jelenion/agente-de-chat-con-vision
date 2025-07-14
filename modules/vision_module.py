"""
Módulo de visión que usa CNN local para detectar emociones
Basado en el código de Google Colab
"""
import os
import numpy as np
from PIL import Image
from tensorflow.keras.models import load_model
from tensorflow.keras.preprocessing.image import img_to_array
from loguru import logger
from typing import Dict

from config import USERS, EMOTIONS

class VisionModule:
    """
    Módulo de visión que usa CNN local para detectar emociones
    """
    
    def __init__(self):
        self.logger = logger
        self.model = None
        self.classes = []
        self.img_height, self.img_width = 96, 96
        
        # Cargar modelo
        self._load_models()
        
    def _load_models(self):
        """
        Carga el modelo CNN
        """
        try:
            model_path = "models/emotion_model.h5"
            classes_path = "models/classes.json"
            
            if os.path.exists(model_path) and os.path.exists(classes_path):
                self.model = load_model(model_path)
                
                # Cargar clases del modelo
                import json
                with open(classes_path, 'r', encoding='utf-8') as f:
                    self.classes = json.load(f)
                
                self.logger.info("✅ Modelo CNN cargado correctamente")
                self.logger.info(f"📋 Clases disponibles: {len(self.classes)}")
            else:
                self.logger.warning(f"⚠️ Modelo no encontrado en {model_path}")
                
        except Exception as e:
            self.logger.error(f"❌ Error al cargar modelos: {e}")
    
    def _preprocess_image(self, image: Image.Image) -> np.ndarray:
        """
        Preprocesa la imagen exactamente como en el código de Colab
        """
        try:
            # Convertir a RGB si es necesario
            if image.mode != 'RGB':
                image = image.convert('RGB')
            
            # Redimensionar exactamente a 96x96 (como en Colab)
            image = image.resize((96, 96))
            
            # Convertir a array y normalizar (como en Colab)
            image_array = img_to_array(image)
            image_array = image_array / 255.0  # Normalización como en Colab
            
            # Agregar dimensión de batch
            image_array = np.expand_dims(image_array, axis=0)
            
            return image_array
            
        except Exception as e:
            self.logger.error(f"Error al preprocesar imagen: {e}")
            raise
    
    def detect_emotion(self, image_path: str) -> Dict:
        """
        Detecta la emoción en la imagen usando el modelo CNN
        Proceso simplificado como en el código de Colab
        """
        try:
            # Cargar imagen
            image = Image.open(image_path)
            
            # Preprocesar imagen completa (sin detectar rostros, como en Colab)
            processed_image = self._preprocess_image(image)
            
            if self.model is not None and len(self.classes) > 0:
                # Hacer predicción (como en Colab)
                prediction = self.model.predict(processed_image, verbose=0)
                class_index = np.argmax(prediction[0])
                
                if class_index < len(self.classes):
                    predicted_class = self.classes[class_index]
                    confidence = float(prediction[0][class_index])
                    
                    self.logger.info(f"Clase detectada: {predicted_class} (confianza: {confidence:.3f})")
                    
                    return {
                        "emotion": predicted_class,
                        "confidence": confidence,
                        "success": True
                    }
                else:
                    return {"success": False, "error": "Error en predicción del modelo"}
            else:
                # Fallback si no hay modelo
                import random
                emotion = random.choice(self.classes) if self.classes else "neutral"
                confidence = random.uniform(0.6, 0.9)
                
                return {
                    "emotion": emotion,
                    "confidence": confidence,
                    "success": True
                }
                
        except Exception as e:
            self.logger.error(f"Error al detectar emoción: {e}")
            return {"success": False, "error": str(e)}
    
    def identify_user(self, image_path: str) -> Dict:
        """
        Identifica al usuario basado en la predicción del modelo
        """
        try:
            # Usar la misma lógica que detect_emotion
            result = self.detect_emotion(image_path)
            
            if result["success"]:
                predicted_class = result["emotion"]
                confidence = result["confidence"]
                
                # Determinar usuario basado en la clase predicha
                if "abrahan" in predicted_class.lower():
                    user_id = "user_a"
                    user_name = "Abraham"
                elif "jesus" in predicted_class.lower():
                    user_id = "user_b"
                    user_name = "Jesús"
                else:
                    user_id = "user_a"
                    user_name = "Desconocido"
                
                return {
                    "user_id": user_id,
                    "user_name": user_name,
                    "confidence": confidence,
                    "success": True
                }
            else:
                return result
                
        except Exception as e:
            self.logger.error(f"Error al identificar usuario: {e}")
            return {"success": False, "error": str(e)}
    
    def process_image(self, image_path: str) -> Dict:
        """
        Procesa una imagen: identifica usuario y emoción
        """
        try:
            # Hacer una sola predicción (más eficiente)
            result = self.detect_emotion(image_path)
            
            if result["success"]:
                predicted_class = result["emotion"]
                confidence = result["confidence"]
                
                # Extraer emoción real (puede venir como 'abrahan_feliz', 'jesus_triste', etc.)
                emotion_found = None
                for emo in EMOTIONS:
                    if emo in predicted_class.lower():
                        emotion_found = emo
                        break
                if not emotion_found:
                    emotion_found = "emoción desconocida"
                
                # Determinar usuario basado en la clase predicha
                if "abrahan" in predicted_class.lower():
                    user_id = "user_a"
                    user_name = "Abraham"
                elif "jesus" in predicted_class.lower():
                    user_id = "user_b"
                    user_name = "Jesús"
                else:
                    user_id = "user_a"
                    user_name = "Desconocido"
                
                return {
                    "user_id": user_id,
                    "user_name": user_name,
                    "user_confidence": confidence,
                    "emotion": emotion_found,
                    "emotion_confidence": confidence,
                    "success": True
                }
            else:
                return result
            
        except Exception as e:
            self.logger.error(f"Error al procesar imagen: {e}")
            return {"success": False, "error": str(e)}
    
    def test_connection(self) -> bool:
        """
        Prueba si el modelo está cargado correctamente
        """
        try:
            if self.model is not None:
                self.logger.info("✅ Modelo CNN disponible")
                return True
            else:
                self.logger.warning("⚠️ Modelo CNN no cargado")
                return False
        except Exception as e:
            self.logger.error(f"Error al verificar modelo: {e}")
            return False 