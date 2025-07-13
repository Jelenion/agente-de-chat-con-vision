#!/usr/bin/env python3
"""
Interfaz Tkinter simplificada para el Agente de Visión
"""
import tkinter as tk
from tkinter import ttk, filedialog, scrolledtext
from PIL import Image, ImageTk
import sys
import os
from datetime import datetime

# Agregar el directorio actual al path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from modules.vision_module import VisionModule
from modules.llm_module import LLMModule
from config import EMOTIONS, USERS

class VisionAgentChat:
    def __init__(self, root):
        self.root = root
        self.root.title("Agente de Visión - Chat")
        self.root.geometry("800x600")
        self.root.configure(bg='#f0f0f0')
        
        # Inicializar módulos
        self.vision_module = VisionModule()
        self.llm_module = LLMModule()
        
        # Variables
        self.current_image_path = None
        self.current_emotion = "neutral"
        self.current_user = "user_a"
        self.conversation_history = []
        
        # Crear interfaz
        self.create_widgets()
        
        # Iniciar conversación
        self.start_conversation()
    
    def create_widgets(self):
        """Crear todos los widgets de la interfaz"""
        # Frame principal
        main_frame = ttk.Frame(self.root, padding="10")
        main_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        # Configurar grid
        self.root.columnconfigure(0, weight=1)
        self.root.rowconfigure(0, weight=1)
        main_frame.columnconfigure(1, weight=1)
        main_frame.rowconfigure(1, weight=1)
        
        # Panel izquierdo (imagen y controles)
        left_panel = ttk.Frame(main_frame)
        left_panel.grid(row=0, column=0, rowspan=2, sticky=(tk.W, tk.E, tk.N, tk.S), padx=(0, 10))
        
        # Área de imagen
        self.image_label = tk.Label(left_panel, text="Sin imagen", 
                                   width=35, height=20, 
                                   relief="solid", borderwidth=2,
                                   bg="white", anchor="center")
        self.image_label.grid(row=0, column=0, pady=(0, 10), padx=5)
        
        # Botón para seleccionar imagen
        self.select_btn = ttk.Button(left_panel, text="Seleccionar Imagen", 
                                   command=self.select_image)
        self.select_btn.grid(row=1, column=0, pady=(0, 10))
        
        # Información de emoción
        emotion_frame = ttk.LabelFrame(left_panel, text="Emoción Detectada", padding="5")
        emotion_frame.grid(row=2, column=0, pady=(0, 10))
        
        self.emotion_label = ttk.Label(emotion_frame, text="Neutral", 
                                     font=("Arial", 12, "bold"))
        self.emotion_label.grid(row=0, column=0)
        
        # Información del usuario detectado
        user_frame = ttk.LabelFrame(left_panel, text="Usuario Detectado", padding="5")
        user_frame.grid(row=3, column=0, pady=(0, 10))
        
        self.user_label = ttk.Label(user_frame, text="Sin usuario", 
                                   font=("Arial", 10, "bold"))
        self.user_label.grid(row=0, column=0)
        
        # Panel derecho (chat)
        right_panel = ttk.Frame(main_frame)
        right_panel.grid(row=0, column=1, sticky=(tk.W, tk.E, tk.N, tk.S))
        right_panel.columnconfigure(0, weight=1)
        right_panel.rowconfigure(0, weight=1)
        
        # Área de chat
        chat_frame = ttk.LabelFrame(right_panel, text="Conversación", padding="5")
        chat_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        chat_frame.columnconfigure(0, weight=1)
        chat_frame.rowconfigure(0, weight=1)
        
        # Chat display
        self.chat_display = scrolledtext.ScrolledText(chat_frame, 
                                                    wrap=tk.WORD, 
                                                    height=20,
                                                    font=("Arial", 10))
        self.chat_display.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S), pady=(0, 10))
        
        # Frame para entrada de texto
        input_frame = ttk.Frame(chat_frame)
        input_frame.grid(row=1, column=0, sticky=(tk.W, tk.E))
        input_frame.columnconfigure(0, weight=1)
        
        # Campo de texto
        self.text_input = ttk.Entry(input_frame, font=("Arial", 10))
        self.text_input.grid(row=0, column=0, sticky=(tk.W, tk.E), padx=(0, 5))
        self.text_input.bind('<Return>', self.send_message)
        
        # Botón enviar
        self.send_btn = ttk.Button(input_frame, text="Enviar", command=self.send_message)
        self.send_btn.grid(row=0, column=1)
        
        # Botón limpiar chat
        clear_btn = ttk.Button(chat_frame, text="Limpiar Chat", command=self.clear_chat)
        clear_btn.grid(row=2, column=0, pady=(5, 0))
    
    def select_image(self):
        """Seleccionar imagen y detectar emoción"""
        file_path = filedialog.askopenfilename(
            title="Seleccionar imagen",
            filetypes=[
                ("Imágenes", "*.jpg *.jpeg *.png *.bmp *.gif"),
                ("Todos los archivos", "*.*")
            ]
        )
        
        if file_path:
            self.current_image_path = file_path
            self.display_image(file_path)
            self.detect_emotion(file_path)
    
    def display_image(self, image_path):
        """Mostrar imagen en el label"""
        try:
            # Cargar imagen
            image = Image.open(image_path)
            
            # Convertir a RGB si es necesario
            if image.mode != 'RGB':
                image = image.convert('RGB')
            
            # Calcular dimensiones para mantener proporción
            max_width = 250
            max_height = 250
            
            # Obtener dimensiones originales
            width, height = image.size
            
            # Calcular factor de escala
            scale = min(max_width/width, max_height/height)
            
            # Calcular nuevas dimensiones
            new_width = int(width * scale)
            new_height = int(height * scale)
            
            # Redimensionar imagen
            image = image.resize((new_width, new_height), Image.Resampling.LANCZOS)
            
            # Convertir a PhotoImage
            photo = ImageTk.PhotoImage(image)
            
            # Actualizar label
            self.image_label.configure(image=photo, text="")
            self.image_label.image = photo  # Mantener referencia
            
        except Exception as e:
            self.image_label.configure(image="", text=f"Error: {str(e)}")
            print(f"Error al mostrar imagen: {e}")
    
    def detect_emotion(self, image_path):
        """Detectar emoción y usuario en la imagen"""
        try:
            # Procesar imagen completa (usuario + emoción)
            result = self.vision_module.process_image(image_path)
            
            if result["success"]:
                # Extraer información del usuario y emoción
                detected_user = result["user_name"]
                detected_emotion = result["emotion"]
                user_confidence = result["user_confidence"]
                emotion_confidence = result["emotion_confidence"]
                
                # Actualizar variables
                self.current_user = result["user_id"]
                self.current_emotion = detected_emotion
                
                # Actualizar interfaz
                self.user_label.configure(text=f"{detected_user}")
                self.emotion_label.configure(text=f"{detected_emotion.title()}")
                
                # Agregar al chat
                timestamp = datetime.now().strftime("%H:%M")
                self.add_to_chat(f"[{timestamp}] 👤 Usuario detectado: {detected_user}", "system")
                self.add_to_chat(f"[{timestamp}] 📷 Emoción detectada: {detected_emotion.title()}", "system")
                
                # Generar respuesta automática del modelo
                self.generate_model_response()
            else:
                error_msg = result.get('error', 'Error desconocido')
                self.add_to_chat(f"❌ Error al procesar imagen: {error_msg}", "error")
                
                # Si el modelo no existe, sugerir entrenarlo
                if "Modelo no encontrado" in error_msg:
                    self.add_to_chat("💡 Sugerencia: Ejecuta 'python train_cnn_model.py' para entrenar el modelo", "system")
                
        except Exception as e:
            self.add_to_chat(f"❌ Error inesperado: {str(e)}", "error")
            import traceback
            print(f"Error completo: {traceback.format_exc()}")
    
    def start_conversation(self):
        """Iniciar la conversación con el modelo"""
        welcome_message = "¡Hola! Soy tu agente de visión. Puedo detectar emociones en imágenes y mantener conversaciones inteligentes. ¿En qué puedo ayudarte hoy?"
        
        self.add_to_chat(welcome_message, "assistant")
        
        # Generar primera respuesta del modelo
        self.generate_model_response()
    
    def generate_model_response(self):
        """Generar respuesta automática del modelo"""
        try:
            # Crear contexto para el modelo
            context = f"El usuario está en estado emocional: {self.current_emotion}"
            
            response = self.llm_module.generate_response(
                user_id=self.current_user,
                emotion=self.current_emotion,
                message=context,
                conversation_history=self.conversation_history
            )
            
            if response["success"]:
                self.add_to_chat(response["response"], "assistant")
                
                # Agregar a historial
                self.conversation_history.append({
                    "user_message": context,
                    "assistant_response": response["response"],
                    "emotion": self.current_emotion,
                    "timestamp": datetime.now()
                })
            else:
                self.add_to_chat(f"❌ Error del modelo: {response.get('error', 'Error desconocido')}", "error")
                
        except Exception as e:
            self.add_to_chat(f"❌ Error: {str(e)}", "error")
    
    def send_message(self, event=None):
        """Enviar mensaje de texto"""
        message = self.text_input.get().strip()
        
        if message:
            # Agregar mensaje del usuario
            timestamp = datetime.now().strftime("%H:%M")
            self.add_to_chat(f"[{timestamp}] Tú: {message}", "user")
            
            # Limpiar campo de texto
            self.text_input.delete(0, tk.END)
            
            # Generar respuesta del modelo
            try:
                response = self.llm_module.generate_response(
                    user_id=self.current_user,
                    emotion=self.current_emotion,
                    message=message,
                    conversation_history=self.conversation_history
                )
                
                if response["success"]:
                    self.add_to_chat(response["response"], "assistant")
                    
                    # Agregar a historial
                    self.conversation_history.append({
                        "user_message": message,
                        "assistant_response": response["response"],
                        "emotion": self.current_emotion,
                        "timestamp": datetime.now()
                    })
                else:
                    self.add_to_chat(f"❌ Error del modelo: {response.get('error', 'Error desconocido')}", "error")
                    
            except Exception as e:
                self.add_to_chat(f"❌ Error: {str(e)}", "error")
    
    def add_to_chat(self, message, sender):
        """Agregar mensaje al chat"""
        try:
            # Habilitar el widget para edición
            self.chat_display.config(state='normal')
            
            # Insertar mensaje
            self.chat_display.insert(tk.END, f"{message}\n\n")
            
            # Desplazar al final
            self.chat_display.see(tk.END)
            
            # Deshabilitar edición
            self.chat_display.config(state='disabled')
            
            # Forzar actualización de la interfaz
            self.root.update_idletasks()
            
        except Exception as e:
            print(f"Error al agregar mensaje al chat: {e}")
    

    
    def clear_chat(self):
        """Limpiar chat"""
        try:
            # Habilitar edición
            self.chat_display.config(state='normal')
            
            # Limpiar contenido
            self.chat_display.delete(1.0, tk.END)
            
            # Limpiar historial
            self.conversation_history = []
            
            # Deshabilitar edición
            self.chat_display.config(state='disabled')
            
            # Reiniciar conversación
            self.start_conversation()
            
        except Exception as e:
            print(f"Error al limpiar chat: {e}")

def main():
    """Función principal"""
    root = tk.Tk()
    app = VisionAgentChat(root)
    root.mainloop()

if __name__ == "__main__":
    main() 