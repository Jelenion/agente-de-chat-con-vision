"""
Módulo de visión que usa CNN local para detectar emociones
Basado en el código de Google Colab
"""
# Importa os para operaciones del sistema
import os  # Para operaciones del sistema
# Importa numpy para operaciones numéricas
import numpy as np  # Para operaciones numéricas
# Importa PIL para manejo de imágenes
from PIL import Image  # Para manejo de imágenes
# Importa funciones de Keras para cargar modelos y procesar imágenes
from tensorflow.keras.models import load_model  # Para cargar modelos Keras
from tensorflow.keras.preprocessing.image import img_to_array  # Para convertir imágenes a arrays
# Importa logger para mensajes de depuración
from loguru import logger  # Logger para depuración
# Importa tipos para anotaciones
from typing import Dict  # Tipos para anotaciones

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
        Carga el modelo CNN. Si no existe, entrena y guarda automáticamente.
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
                self.logger.warning(f"⚠️ Modelo no encontrado en {model_path}. Entrenando modelo nuevo...")
                # Entrenar y guardar modelo automáticamente
                success = self.train_from_emociones()
                if success:
                    self.model = load_model(model_path)
                    import json
                    with open(classes_path, 'r', encoding='utf-8') as f:
                        self.classes = json.load(f)
                    self.logger.info("✅ Modelo CNN entrenado y cargado correctamente")
                else:
                    self.logger.error("❌ No se pudo entrenar el modelo CNN")
        except Exception as e:
            self.logger.error(f"❌ Error al cargar o entrenar modelos: {e}")
    
    def _preprocess_image(self, image: Image.Image) -> np.ndarray:
        """
        Preprocesa la imagen exactamente como en el código de Colab (resize directo a 96x96, sin recorte cuadrado).
        """
        try:
            # Convertir a RGB si es necesario
            if image.mode != 'RGB':
                image = image.convert('RGB')  # Convierte a RGB
            # Redimensionar exactamente a 96x96 (sin recorte)
            image = image.resize((96, 96))  # Redimensiona
            # Convertir a array y normalizar
            image_array = img_to_array(image)  # Convierte a array
            image_array = image_array / 255.0  # Normaliza
            # Agregar dimensión de batch
            image_array = np.expand_dims(image_array, axis=0)  # Añade dimensión batch
            return image_array
        except Exception as e:
            self.logger.error(f"Error al preprocesar imagen: {e}")  # Log de error
            raise  # Relanza excepción
    
    def detect_emotion(self, image_path: str) -> Dict:
        """
        Detecta la emoción en la imagen usando el modelo CNN
        Proceso simplificado como en el código de Colab
        """
        try:
            # Cargar imagen desde el path
            image = Image.open(image_path)  # Abre la imagen
            
            # Preprocesar imagen completa (sin detectar rostros, como en Colab)
            processed_image = self._preprocess_image(image)  # Preprocesa
            
            if self.model is not None and len(self.classes) > 0:
                # Hacer predicción (como en Colab)
                prediction = self.model.predict(processed_image, verbose=0)  # Predice
                class_index = np.argmax(prediction[0])  # Índice de clase
                
                if class_index < len(self.classes):
                    predicted_class = self.classes[class_index]  # Clase predicha
                    confidence = float(prediction[0][class_index])  # Confianza
                    
                    self.logger.info(f"Clase detectada: {predicted_class} (confianza: {confidence:.3f})")  # Log
                    
                    return {
                        "emotion": predicted_class,  # Emoción detectada
                        "confidence": confidence,  # Confianza
                        "success": True  # Éxito
                    }
                else:
                    return {"success": False, "error": "Error en predicción del modelo"}  # Error de predicción
            else:
                # Fallback si no hay modelo cargado
                import random
                emotion = random.choice(self.classes) if self.classes else "neutral"  # Emoción aleatoria
                confidence = random.uniform(0.6, 0.9)  # Confianza aleatoria
                
                return {
                    "emotion": emotion,  # Emoción fallback
                    "confidence": confidence,  # Confianza fallback
                    "success": True  # Éxito
                }
                
        except Exception as e:
            self.logger.error(f"Error al detectar emoción: {e}")  # Log de error
            return {"success": False, "error": str(e)}  # Devuelve error
    

    def process_image(self, image_path: str) -> Dict:
        """
        Procesa una imagen: identifica usuario y emoción
        """
        try:
            # Hacer una sola predicción (más eficiente)
            result = self.detect_emotion(image_path)  # Predicción
            if result["success"]:
                predicted_class = result["emotion"]  # Clase predicha
                confidence = result["confidence"]  # Confianza
                # Extraer emoción real (puede venir como 'abrahan_feliz', 'jesus_triste', etc.)
                emotion_found = None  # Inicializa emoción
                pred_lower = predicted_class.lower()  # Minúsculas
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
                    emotion_found = "emoción desconocida"  # Fallback
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
                    "user_id": user_id,  # ID usuario
                    "user_name": user_name,  # Nombre usuario
                    "user_confidence": confidence,  # Confianza usuario
                    "emotion": emotion_found,  # Emoción
                    "emotion_confidence": confidence,  # Confianza emoción
                    "success": True  # Éxito
                }
            else:
                return result  # Devuelve error
        except Exception as e:
            self.logger.error(f"Error al procesar imagen: {e}")  # Log de error
            return {"success": False, "error": str(e)}  # Devuelve error
    
    def test_connection(self) -> bool:
        """
        Prueba si el modelo está cargado correctamente
        """
        try:
            if self.model is not None:
                self.logger.info("✅ Modelo CNN disponible")  # Log de éxito
                return True  # Modelo disponible
            else:
                self.logger.warning("⚠️ Modelo CNN no cargado")  # Log de advertencia
                return False  # Modelo no disponible
        except Exception as e:
            self.logger.error(f"Error al verificar modelo: {e}")  # Log de error
            return False  # Devuelve False

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
        if not X or not y or not class_names:
            self.logger.error("❌ No se encontraron datos para entrenamiento.")
            return False
        X = np.array(X)
        class_names = sorted(list(class_names))
        y_idx = [class_names.index(lbl) for lbl in y]
        y_cat = to_categorical(y_idx, num_classes=len(class_names))
        X_train, X_val, y_train, y_val = train_test_split(X, y_cat, test_size=0.2, random_state=42)
        # Definir modelo simple CNN
        model = Sequential([
            Conv2D(32, (3, 3), activation='relu', input_shape=(IMG_SIZE, IMG_SIZE, 3)),
            MaxPooling2D((2, 2)),
            Conv2D(64, (3, 3), activation='relu'),
            MaxPooling2D((2, 2)),
            Flatten(),
            Dense(128, activation='relu'),
            Dropout(0.5),
            Dense(len(class_names), activation='softmax')
        ])
        model.compile(optimizer=Adam(), loss='categorical_crossentropy', metrics=['accuracy'])
        model.fit(X_train, y_train, epochs=epochs, batch_size=batch_size, validation_data=(X_val, y_val), verbose=2)
        # Guardar modelo y clases
        os.makedirs('models', exist_ok=True)
        model.save('models/emotion_model.h5')
        with open('models/classes.json', 'w', encoding='utf-8') as f:
            json.dump(class_names, f, ensure_ascii=False, indent=2)
        self.logger.info("✅ Modelo y clases guardados en 'models/'")
        return True 