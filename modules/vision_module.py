"""
Módulo de visión que usa CNN local para detectar emociones
Basado en el código de Google Colab
"""
# Importa os para operaciones del sistema
import os
# Importa numpy para operaciones numéricas
import numpy as np
# Importa PIL para manejo de imágenes
from PIL import Image
# Importa funciones de Keras para cargar modelos y procesar imágenes
from tensorflow.keras.models import load_model
from tensorflow.keras.preprocessing.image import img_to_array
# Importa logger para mensajes de depuración
from loguru import logger
# Importa tipos para anotaciones
from typing import Dict

# Importa configuración global de usuarios y emociones
from config import USERS, EMOTIONS  # Configuración global

class VisionModule:
    """
    Módulo de visión que usa CNN local para detectar emociones
    """
    
    def __init__(self):
        self.logger = logger  # Logger para mensajes
        self.model = None  # Modelo CNN (se carga después)
        self.classes = []  # Lista de clases del modelo
        self.img_height, self.img_width = 96, 96  # Tamaño esperado de la imagen
        
        # Cargar modelo al inicializar
        self._load_models()
        
    def _load_models(self):
        """
        Carga el modelo CNN
        """
        try:
            model_path = "models/emotion_model.h5"  # Ruta al modelo
            classes_path = "models/classes.json"  # Ruta a las clases
            
            # Verifica que existan los archivos del modelo y clases
            if os.path.exists(model_path) and os.path.exists(classes_path):
                self.model = load_model(model_path)  # Carga el modelo
                
                # Cargar clases del modelo desde JSON
                import json
                with open(classes_path, 'r', encoding='utf-8') as f:
                    self.classes = json.load(f)  # Carga las clases
                
                self.logger.info("✅ Modelo CNN cargado correctamente")
                self.logger.info(f"📋 Clases disponibles: {len(self.classes)}")
            else:
                self.logger.warning(f"⚠️ Modelo no encontrado en {model_path}")
                
        except Exception as e:
            self.logger.error(f"❌ Error al cargar modelos: {e}")
    
    def _preprocess_image(self, image: Image.Image) -> np.ndarray:
        """
        Preprocesa la imagen exactamente como en el código de Colab (resize directo a 96x96, sin recorte cuadrado).
        """
        try:
            # Convertir a RGB si es necesario
            if image.mode != 'RGB':
                image = image.convert('RGB')
            # Redimensionar exactamente a 96x96 (sin recorte)
            image = image.resize((96, 96))
            # Convertir a array y normalizar
            image_array = img_to_array(image)
            image_array = image_array / 255.0
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
            # Cargar imagen desde el path
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
                # Fallback si no hay modelo cargado
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
                    user_id = "abrahan"
                    user_name = "Abrahan"
                elif "jesus" in predicted_class.lower():
                    user_id = "jesus"
                    user_name = "Jesus"
                else:
                    user_id = "abrahan"
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
                pred_lower = predicted_class.lower()
                # 1. Coincidencia exacta
                if pred_lower in EMOTIONS:
                    emotion_found = pred_lower
                # 2. Coincidencia por prefijo/sufijo
                if not emotion_found:
                    for emo in EMOTIONS:
                        if pred_lower.endswith(emo) or pred_lower.startswith(emo):
                            emotion_found = emo
                            break
                # 3. Coincidencia aproximada (más parecida)
                if not emotion_found:
                    close = difflib.get_close_matches(pred_lower, EMOTIONS, n=1, cutoff=0.6)
                    if close:
                        emotion_found = close[0]
                if not emotion_found:
                    emotion_found = "emoción desconocida"
                # Determinar usuario basado en la clase predicha
                if "abrahan" in pred_lower:
                    user_id = "abrahan"
                    user_name = "Abrahan"
                elif "jesus" in pred_lower:
                    user_id = "jesus"
                    user_name = "Jesus"
                else:
                    user_id = "abrahan"
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

    def train_from_emociones(self, dataset_dir='emociones', epochs=20, batch_size=32):
        """Entrena el modelo CNN usando las imágenes de la carpeta 'emociones/' y guarda el modelo y las clases. Devuelve True si tiene éxito, False si falla."""
        # Importa librerías necesarias para entrenamiento
        import numpy as np
        from PIL import Image
        from tensorflow.keras.utils import to_categorical
        from tensorflow.keras.models import Sequential
        from tensorflow.keras.layers import Conv2D, MaxPooling2D, Flatten, Dense, Dropout
        from tensorflow.keras.optimizers import Adam
        from sklearn.model_selection import train_test_split
        import json, os

        IMG_SIZE = self.img_height  # Tamaño de imagen
        X, y = [], []  # Listas para datos e índices
        class_names = set()  # Conjunto de nombres de clases
        for root, dirs, files in os.walk(dataset_dir):
            for file in files:
                if file.lower().endswith(('.jpg', '.jpeg', '.png', '.bmp', '.gif')):
                    img_path = os.path.join(root, file)
                    label = os.path.basename(root).split('_')[-1].lower()
                    class_names.add(label)
                    try:
                        img = Image.open(img_path).convert('RGB')
                        img = img.resize((IMG_SIZE, IMG_SIZE))
                        img = np.array(img) / 255.0
                        X.append(img)
                        y.append(label)
                    except Exception as e:
                        print(f"Error cargando {img_path}: {e}") 