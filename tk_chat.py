#!/usr/bin/env python3
"""
Interfaz Tkinter simplificada para el Agente de Visión con Base de Datos
"""
import tkinter as tk
from tkinter import ttk, filedialog, scrolledtext, messagebox
from PIL import Image, ImageTk
import sys
import os
import tempfile
from datetime import datetime
import threading
import re
import time

# Agregar el directorio actual al path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from modules.vision_module import VisionModule
from modules.llm_module import LLMModule
from modules.database_module import ChatDatabase
from config import EMOTIONS, USERS

class VisionAgentChat:
    def __init__(self, root):
        self.root = root
        self.root.title("Agente de Visión - Chat con Base de Datos")
        self.root.geometry("1000x700")
        self.root.configure(bg='#f0f0f0')
        
        # Inicializar módulos
        self.vision_module = VisionModule()
        self.llm_module = LLMModule()
        self.database = ChatDatabase()
        
        # Variables
        self.current_image_path = None
        self.current_emotion = None
        self.current_user = None
        self.conversation_history = []
        self.current_session_id = None
        self.current_session_name = None
        
        # Crear interfaz
        self.create_widgets()
        self.create_menu()
        
        # Crear nueva sesión automáticamente
        self.create_new_session()
    
    def create_menu(self):
        """Crear menú principal"""
        menubar = tk.Menu(self.root)
        self.root.config(menu=menubar)
        
        # Menú Sesiones
        session_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="Sesiones", menu=session_menu)
        session_menu.add_command(label="Nueva Sesión", command=self.create_new_session)
        session_menu.add_command(label="Cargar Sesión", command=self.load_session_dialog)
        session_menu.add_command(label="Guardar Sesión Actual", command=self.save_current_session)
        session_menu.add_separator()
        session_menu.add_command(label="Gestionar Sesiones", command=self.manage_sessions)
        session_menu.add_separator()
        session_menu.add_command(label="Limpiar Base de Datos", command=self.limpiar_base_de_datos)
        
        # Menú Chat
        chat_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="Chat", menu=chat_menu)
        chat_menu.add_command(label="Limpiar Chat", command=self.clear_chat)
        chat_menu.add_command(label="Exportar Chat", command=self.export_chat)
    
    def create_widgets(self):
        """Crear todos los widgets de la interfaz (con tags de burbuja)."""
        # Frame principal
        main_frame = ttk.Frame(self.root, padding="10")
        main_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        self.root.columnconfigure(0, weight=1)
        self.root.rowconfigure(0, weight=1)
        main_frame.columnconfigure(0, weight=1)
        main_frame.rowconfigure(1, weight=1)

        # Panel izquierdo (solo info de sesión)
        left_panel = ttk.Frame(main_frame)
        left_panel.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S), padx=(0, 10))
        session_frame = ttk.LabelFrame(left_panel, text="Sesión Actual", padding="5")
        session_frame.grid(row=0, column=0, pady=(0, 10), sticky=(tk.W, tk.E))
        self.session_label = ttk.Label(session_frame, text="Nueva sesión", font=("Arial", 10, "bold"))
        self.session_label.grid(row=0, column=0)

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
        self.chat_display = scrolledtext.ScrolledText(chat_frame, wrap=tk.WORD, height=20, font=("Arial", 10))
        self.chat_display.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S), pady=(0, 10))
        # Definir tags de burbuja
        self.chat_display.tag_configure("user_bubble", background="#ffe0b2", foreground="#333", justify="right", lmargin1=60, lmargin2=60, rmargin=10, spacing3=5, font=("Arial", 10, "bold"))
        self.chat_display.tag_configure("assistant_bubble", background="#e1bee7", foreground="#222", justify="left", lmargin1=10, lmargin2=10, rmargin=60, spacing3=5, font=("Arial", 10))
        self.chat_display.tag_configure("system_bubble", background="#b3e5fc", foreground="#222", justify="center", lmargin1=40, lmargin2=40, rmargin=40, spacing3=5, font=("Arial", 10, "italic"))
        self.chat_display.tag_configure("default_bubble", background="#f0f0f0", foreground="#222", justify="left", lmargin1=10, lmargin2=10, rmargin=10, spacing3=5, font=("Arial", 10))

        # Frame para entrada de texto y botón seleccionar imagen
        input_frame = ttk.Frame(chat_frame)
        input_frame.grid(row=1, column=0, sticky=(tk.W, tk.E))
        input_frame.columnconfigure(0, weight=1)
        self.text_input = ttk.Entry(input_frame, font=("Arial", 10))
        self.text_input.grid(row=0, column=0, sticky=(tk.W, tk.E), padx=(0, 5))
        self.text_input.bind('<Return>', self.send_message)
        self.send_btn = ttk.Button(input_frame, text="Enviar", command=self.send_message)
        self.send_btn.grid(row=0, column=1, padx=(0, 5))
        self.select_btn = ttk.Button(input_frame, text="Seleccionar Imagen", command=self.select_image)
        self.select_btn.grid(row=0, column=2)

        # Frame para emoción y usuario detectados debajo del chat
        status_frame = ttk.Frame(right_panel)
        status_frame.grid(row=1, column=0, sticky=(tk.W, tk.E), pady=(10, 0))
        status_frame.columnconfigure(0, weight=1)
        self.emotion_label = ttk.Label(status_frame, text="Emoción: Neutral", font=("Arial", 12, "bold"))
        self.emotion_label.grid(row=0, column=0, sticky=(tk.W, tk.E), pady=(0, 2))
        self.user_label = ttk.Label(status_frame, text="Usuario: Sin usuario", font=("Arial", 10, "bold"))
        self.user_label.grid(row=1, column=0, sticky=(tk.W, tk.E))

    def create_new_session(self):
        """Crear una nueva sesión de chat"""
        session_name = f"Sesión {datetime.now().strftime('%Y-%m-%d %H:%M')}"
        self.current_session_id = self.database.create_new_session(session_name)
        self.current_session_name = session_name
        self.session_label.configure(text=session_name)
        
        # Limpiar chat y variables
        self.clear_chat()
        self.current_image_path = None
        self.current_emotion = None
        self.current_user = None
        self.conversation_history = []
        
        # Iniciar conversación
        self.start_conversation()
    
    def save_current_session(self):
        """Guardar la sesión actual en la base de datos"""
        if not self.current_session_id:
            messagebox.showwarning("Advertencia", "No hay sesión activa para guardar")
            return
        
        # La sesión se guarda automáticamente con cada mensaje
        messagebox.showinfo("Información", "La sesión se guarda automáticamente con cada mensaje")
    
    def load_session_dialog(self):
        """Mostrar diálogo para cargar una sesión"""
        sessions = self.database.get_all_sessions()
        
        if not sessions:
            messagebox.showinfo("Información", "No hay sesiones guardadas")
            return
        
        # Crear ventana de selección
        dialog = tk.Toplevel(self.root)
        dialog.title("Cargar Sesión")
        dialog.geometry("500x400")
        dialog.transient(self.root)
        dialog.grab_set()
        
        # Frame principal
        main_frame = ttk.Frame(dialog, padding="10")
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        # Lista de sesiones
        ttk.Label(main_frame, text="Selecciona una sesión para cargar:", 
                 font=("Arial", 12, "bold")).pack(pady=(0, 10))
        
        # Crear Treeview para mostrar sesiones
        columns = ('ID', 'Nombre', 'Creada', 'Actualizada', 'Mensajes')
        tree = ttk.Treeview(main_frame, columns=columns, show='headings', height=10)
        
        # Configurar columnas
        tree.heading('ID', text='ID')
        tree.heading('Nombre', text='Nombre')
        tree.heading('Creada', text='Creada')
        tree.heading('Actualizada', text='Actualizada')
        tree.heading('Mensajes', text='Mensajes')
        
        tree.column('ID', width=50)
        tree.column('Nombre', width=150)
        tree.column('Creada', width=120)
        tree.column('Actualizada', width=120)
        tree.column('Mensajes', width=80)
        
        # Insertar sesiones
        for session in sessions:
            tree.insert('', 'end', values=(
                session['id'],
                session['name'],
                session['created_at'][:19],  # Truncar timestamp
                session['last_updated'][:19],
                session['message_count']
            ))
        
        tree.pack(fill=tk.BOTH, expand=True, pady=(0, 10))
        
        # Botones
        button_frame = ttk.Frame(main_frame)
        button_frame.pack(fill=tk.X)
        
        def load_selected():
            selection = tree.selection()
            if selection:
                item = tree.item(selection[0])
                session_id = item['values'][0]
                self.load_session(session_id)
                dialog.destroy()
        
        def delete_selected():
            selection = tree.selection()
            if selection:
                item = tree.item(selection[0])
                session_id = item['values'][0]
                session_name = item['values'][1]
                
                if messagebox.askyesno("Confirmar", f"¿Eliminar la sesión '{session_name}'?"):
                    if self.database.delete_session(session_id):
                        tree.delete(selection[0])
                        messagebox.showinfo("Éxito", "Sesión eliminada")
                    else:
                        messagebox.showerror("Error", "No se pudo eliminar la sesión")
        
        ttk.Button(button_frame, text="Cargar", command=load_selected).pack(side=tk.LEFT, padx=(0, 5))
        ttk.Button(button_frame, text="Eliminar", command=delete_selected).pack(side=tk.LEFT, padx=(0, 5))
        ttk.Button(button_frame, text="Cancelar", command=dialog.destroy).pack(side=tk.RIGHT)
    
    def load_session(self, session_id):
        """Cargar una sesión específica"""
        # Obtener información de la sesión
        session_info = self.database.get_session_info(session_id)
        if not session_info:
            messagebox.showerror("Error", "No se pudo cargar la sesión")
            return
        # Obtener mensajes de la sesión
        messages = self.database.get_session_messages(session_id)
        # Actualizar variables
        self.current_session_id = session_id
        self.current_session_name = session_info['name']
        self.session_label.configure(text=self.current_session_name)
        # Limpiar chat actual
        self.chat_display.config(state='normal')
        self.chat_display.delete(1.0, tk.END)
        self.chat_display.config(state='disabled')
        # Cargar mensajes
        self.conversation_history = []
        for message in messages:
            if message['type'] == 'user':
                self.add_to_chat(f"Tú: {message['content']}", "user")
                self.conversation_history.append({
                    "user_message": message['content'],
                    "assistant_response": "",
                    "emotion": message.get('emotion'),
                    "timestamp": datetime.fromisoformat(message['timestamp'])
                })
            elif message['type'] == 'assistant':
                self.add_to_chat(message['content'], "assistant")
                if self.conversation_history:
                    self.conversation_history[-1]["assistant_response"] = message['content']
            elif message['type'] == 'image':
                # Si hay image_data, reconstruir imagen temporal
                if message.get('image_data'):
                    with tempfile.NamedTemporaryFile(delete=False, suffix='.jpg') as tmp_img:
                        tmp_img.write(message['image_data'])
                        tmp_img_path = tmp_img.name
                    self.add_image_to_chat(tmp_img_path, message.get('user_name'), message.get('emotion'))
                else:
                    self.add_to_chat("[Imagen no disponible en la base de datos]", "system")
                self.current_user = message.get('user_name')
                self.current_emotion = message.get('emotion')
                self.user_label.configure(text=message.get('user_name', ''))
                self.emotion_label.configure(text=message.get('emotion', '').title())
        messagebox.showinfo("Éxito", f"Sesión '{self.current_session_name}' cargada correctamente")

    def limpiar_base_de_datos(self):
        """Elimina todas las sesiones y mensajes de la base de datos."""
        import sqlite3
        from modules.database_module import ChatDatabase
        db = ChatDatabase()
        with sqlite3.connect(db.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("DELETE FROM chat_messages")
            cursor.execute("DELETE FROM chat_sessions")
            conn.commit()
        messagebox.showinfo("Limpieza", "La base de datos ha sido limpiada correctamente.")
    
    def manage_sessions(self):
        """Gestionar sesiones (alias para load_session_dialog)"""
        self.load_session_dialog()
    
    def export_chat(self):
        """Exportar el chat actual a un archivo de texto"""
        if not self.current_session_id:
            messagebox.showwarning("Advertencia", "No hay sesión activa para exportar")
            return
        
        file_path = filedialog.asksaveasfilename(
            title="Exportar chat",
            defaultextension=".txt",
            filetypes=[("Archivos de texto", "*.txt"), ("Todos los archivos", "*.*")]
        )
        
        if file_path:
            try:
                with open(file_path, 'w', encoding='utf-8') as f:
                    f.write(f"Chat - {self.current_session_name}\n")
                    f.write("=" * 50 + "\n\n")
                    
                    # Obtener mensajes de la sesión
                    messages = self.database.get_session_messages(self.current_session_id)
                    
                    for message in messages:
                        timestamp = message['timestamp'][:19]  # Truncar timestamp
                        if message['type'] == 'user':
                            f.write(f"[{timestamp}] Tú: {message['content']}\n\n")
                        elif message['type'] == 'assistant':
                            f.write(f"[{timestamp}] Asistente: {message['content']}\n\n")
                        elif message['type'] == 'image':
                            f.write(f"[{timestamp}] 📷 Imagen de {message['user_name']} - Emoción: {message['emotion']}\n\n")
                
                messagebox.showinfo("Éxito", f"Chat exportado a: {file_path}")
            except Exception as e:
                messagebox.showerror("Error", f"No se pudo exportar el chat: {str(e)}")
    
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
            self.detect_emotion(file_path)
            
            # Guardar imagen en la base de datos si hay sesión activa
            if self.current_session_id and self.current_user and self.current_emotion:
                self.database.save_image_to_db(
                    session_id=self.current_session_id,
                    image_path=file_path,
                    user_name=self.current_user,
                    emotion=self.current_emotion
                )
    
    def detect_emotion(self, image_path):
        """Detectar emoción y usuario en la imagen"""
        try:
            # Procesar imagen completa (usuario + emoción)
            result = self.vision_module.process_image(image_path)
            if result["success"]:
                detected_user = result["user_name"]
                detected_emotion = result["emotion"]
                user_confidence = result["user_confidence"]
                emotion_confidence = result["emotion_confidence"]
                self.current_user = result["user_id"]
                self.current_emotion = detected_emotion
                self.user_label.configure(text=f"{detected_user}")
                self.emotion_label.configure(text=f"{detected_emotion.title()}")
                # Mostrar imagen en el chat estilo ChatGPT
                self.add_image_to_chat(image_path, detected_user, detected_emotion)
                # Guardar imagen en la base de datos si hay sesión activa
                if self.current_session_id:
                    self.database.save_image_to_db(
                        session_id=self.current_session_id,
                        image_path=image_path,
                        user_name=detected_user,
                        emotion=detected_emotion
                    )
                # Generar respuesta automática del modelo
                self.generate_model_response()
            else:
                error_msg = result.get('error', 'Error desconocido')
                self.add_to_chat(f"❌ Error al procesar imagen: {error_msg}", "error")
                if "Modelo no encontrado" in error_msg:
                    self.add_to_chat("💡 Sugerencia: Ejecuta 'python train_cnn_model.py' para entrenar el modelo", "system")
        except Exception as e:
            self.add_to_chat(f"❌ Error inesperado: {str(e)}", "error")
            import traceback
            print(f"Error completo: {traceback.format_exc()}")
    
    def start_conversation(self):
        """Iniciar la conversación con saludo genérico (solo una vez)."""
        if not getattr(self, '_welcome_shown', False):
            welcome_message = "¡Hola! Soy tu agente conversacional. Puedes escribirme o subir una imagen para personalizar la conversación."
            self.add_to_chat(welcome_message, "assistant")
            self._welcome_shown = True
    
    def add_streaming_response(self, response_generator):
        """Agrega la respuesta del modelo al chat simulando escritura en vivo si es string."""
        import time
        self.chat_display.config(state='normal')
        pos = self.chat_display.index(tk.END)
        # Si response_generator es un string, simular streaming carácter por carácter
        if isinstance(response_generator, str):
            for char in response_generator:
                self.chat_display.insert(pos, char)
                self.chat_display.see(tk.END)
                self.chat_display.update_idletasks()
                time.sleep(0.015)  # retardo para simular escritura
            self.chat_display.insert(tk.END, "\n\n")
            self.chat_display.config(state='disabled')
            self.root.update_idletasks()
            return response_generator
        # Si es un generador real, usar lógica original
        full_text = ""
        buffer = ""
        last_shown = ""
        import re
        sentence_end = re.compile(r'([.!?\n])')
        for fragment in response_generator:
            full_text += fragment
            buffer += fragment
            sentences = []
            start = 0
            for match in sentence_end.finditer(buffer):
                end = match.end()
                sentences.append(buffer[start:end])
                start = end
            if sentences:
                to_show = "".join(sentences)
                self.chat_display.insert(pos, to_show)
                self.chat_display.see(tk.END)
                self.chat_display.update_idletasks()
                last_shown += to_show
                buffer = buffer[start:]
        if buffer:
            self.chat_display.insert(pos, buffer)
            self.chat_display.see(tk.END)
            self.chat_display.update_idletasks()
            last_shown += buffer
        self.chat_display.insert(tk.END, "\n\n")
        self.chat_display.config(state='disabled')
        self.root.update_idletasks()
        return full_text

    def generate_model_response(self):
        """Generar respuesta automática del modelo (respuesta simulando streaming)."""
        try:
            if not self.current_user or not self.current_emotion:
                return
            context = f"El usuario está en estado emocional: {self.current_emotion}"
            response = self.llm_module.generate_response(
                user_id=self.current_user,
                emotion=self.current_emotion,
                message=context,
                conversation_history=self.conversation_history
            )
            if response["success"]:
                # Simular streaming aunque la respuesta sea completa
                full_response = self.add_streaming_response(response["response"])
                if self.current_session_id:
                    self.database.save_message(
                        session_id=self.current_session_id,
                        message_type='assistant',
                        content=full_response,
                        user_name=self.current_user,
                        emotion=self.current_emotion
                    )
                self.conversation_history.append({
                    "user_message": context,
                    "assistant_response": full_response,
                    "emotion": self.current_emotion,
                    "timestamp": datetime.now()
                })
            else:
                self.add_to_chat(f"❌ Error del modelo: {response.get('error', 'Error desconocido')}", "error")
        except Exception as e:
            self.add_to_chat(f"❌ Error: {str(e)}", "error")
    
    def send_message(self, event=None):
        """Enviar mensaje de texto (respuesta simulando streaming)."""
        message = self.text_input.get().strip()
        if message:
            timestamp = datetime.now().strftime("%H:%M")
            self.add_to_chat(f"[{timestamp}] Tú: {message}", "user")
            if self.current_session_id:
                self.database.save_message(
                    session_id=self.current_session_id,
                    message_type='user',
                    content=message,
                    user_name=self.current_user,
                    emotion=self.current_emotion
                )
            self.text_input.delete(0, tk.END)
            try:
                response = self.llm_module.generate_response(
                    user_id=self.current_user if self.current_user else "",
                    emotion=self.current_emotion if self.current_emotion else "",
                    message=message,
                    conversation_history=self.conversation_history
                )
                if response["success"]:
                    # Simular streaming aunque la respuesta sea completa
                    full_response = self.add_streaming_response(response["response"])
                    if self.current_session_id:
                        self.database.save_message(
                            session_id=self.current_session_id,
                            message_type='assistant',
                            content=full_response,
                            user_name=self.current_user,
                            emotion=self.current_emotion
                        )
                    self.conversation_history.append({
                        "user_message": message,
                        "assistant_response": full_response,
                        "emotion": self.current_emotion,
                        "timestamp": datetime.now()
                    })
                else:
                    self.add_to_chat(f"❌ Error del modelo: {response.get('error', 'Error desconocido')}", "error")
            except Exception as e:
                self.add_to_chat(f"❌ Error: {str(e)}", "error")
    
    def add_to_chat(self, message, sender):
        """Agregar mensaje al chat con estilo burbuja y alineación."""
        try:
            self.chat_display.config(state='normal')
            # Definir estilos
            if sender == "user":
                tag = "user_bubble"
                icon = "\U0001F464 "  # emoji usuario
                align = "right"
            elif sender == "assistant":
                tag = "assistant_bubble"
                icon = "\U0001F916 "  # emoji robot
                align = "left"
            elif sender == "system":
                tag = "system_bubble"
                icon = "\U0001F4AC "  # emoji mensaje
                align = "center"
            else:
                tag = "default_bubble"
                icon = ""
                align = "left"
            # Insertar mensaje con icono y salto de línea
            if align == "right":
                self.chat_display.insert(tk.END, f"{icon}{message}\n", tag)
            elif align == "left":
                self.chat_display.insert(tk.END, f"{icon}{message}\n", tag)
            else:
                self.chat_display.insert(tk.END, f"{icon}{message}\n", tag)
            self.chat_display.insert(tk.END, "\n")
            self.chat_display.see(tk.END)
            self.chat_display.config(state='disabled')
            self.root.update_idletasks()
        except Exception as e:
            print(f"Error al agregar mensaje al chat: {e}")

    def add_image_to_chat(self, image_path, user=None, emotion=None):
        """Agregar una imagen como mensaje en el chat, estilo ChatGPT."""
        try:
            self.chat_display.config(state='normal')
            # Cargar y redimensionar imagen
            image = Image.open(image_path)
            max_width = 180
            max_height = 180
            width, height = image.size
            scale = min(max_width/width, max_height/height, 1.0)
            new_width = int(width * scale)
            new_height = int(height * scale)
            image = image.resize((new_width, new_height), Image.Resampling.LANCZOS)
            photo = ImageTk.PhotoImage(image)
            # Insertar imagen en el chat
            self.chat_display.image_create(tk.END, image=photo)
            # Guardar referencia para evitar garbage collection
            if not hasattr(self, '_chat_images_refs'):
                self._chat_images_refs = []
            self._chat_images_refs.append(photo)
            # Insertar info debajo
            info = ""
            if user or emotion:
                info = "\n"
                if user:
                    info += f"👤 {user}"
                if emotion:
                    info += f"  |  😃 {emotion.title()}"
            self.chat_display.insert(tk.END, f"{info}\n\n")
            self.chat_display.see(tk.END)
            self.chat_display.config(state='disabled')
            self.root.update_idletasks()
        except Exception as e:
            print(f"Error al mostrar imagen en el chat: {e}")
    
    def clear_chat(self):
        """Limpiar chat"""
        try:
            self.chat_display.config(state='normal')
            self.chat_display.delete(1.0, tk.END)
            self.conversation_history = []
            self.chat_display.config(state='disabled')
            self._welcome_shown = False
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