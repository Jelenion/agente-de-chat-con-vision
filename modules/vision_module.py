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
import difflib

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
        import numpy as np
        from PIL import Image
        from tensorflow.keras.utils import to_categorical
        from tensorflow.keras.models import Sequential
        from tensorflow.keras.layers import Conv2D, MaxPooling2D, Flatten, Dense, Dropout
        from tensorflow.keras.optimizers import Adam
        from sklearn.model_selection import train_test_split
        import json, os

        IMG_SIZE = self.img_height
        X, y = [], []
        class_names = set()
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

        class_names = sorted(list(class_names))
        if len(class_names) < 2 or len(X) < 10:
            print("Error: Se requieren al menos 2 clases y 10 imágenes para entrenar.")
            return False

        print(f"Clases detectadas: {class_names}")
        class_to_idx = {c: i for i, c in enumerate(class_names)}
        y_idx = [class_to_idx[label] for label in y]
        X = np.array(X, dtype=np.float32)
        y = to_categorical(y_idx, num_classes=len(class_names))

        try:
            X_train, X_test, y_train, y_test = train_test_split(
                X, y, test_size=0.15, random_state=42, stratify=y_idx
            )
            model = Sequential([
                Conv2D(32, (3,3), activation='relu', input_shape=(IMG_SIZE, IMG_SIZE, 3)),
                MaxPooling2D(2,2),
                Conv2D(64, (3,3), activation='relu'),
                MaxPooling2D(2,2),
                Flatten(),
                Dense(128, activation='relu'),
                Dropout(0.3),
                Dense(len(class_names), activation='softmax')
            ])
            model.compile(optimizer=Adam(learning_rate=0.001), loss='categorical_crossentropy', metrics=['accuracy'])
            print("Entrenando modelo...")
            history = model.fit(X_train, y_train, epochs=epochs, batch_size=batch_size, validation_data=(X_test, y_test))
            os.makedirs('models', exist_ok=True)
            model.save('models/emotion_model.h5')
            with open('models/classes.json', 'w', encoding='utf-8') as f:
                json.dump(class_names, f, ensure_ascii=False, indent=2)
            print("Modelo y clases guardados en 'models/'")
            self.model = model
            self.classes = class_names
            return True
        except Exception as e:
            print(f"Error durante el entrenamiento: {e}")
            return False 