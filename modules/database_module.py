# Módulo para manejar la base de datos de chat usando SQLite
import sqlite3  # Importa el módulo de SQLite para bases de datos locales
import os  # Para operaciones con el sistema de archivos
import base64  # Para codificar/decodificar datos binarios
from datetime import datetime  # Para manejar fechas y horas
from typing import List, Dict, Optional, Tuple  # Tipos para anotaciones
import json  # Para manejar datos en formato JSON

class ChatDatabase:
    def __init__(self, db_path: str = "chat_history.db"):
        """Inicializa la base de datos de chat"""
        self.db_path = db_path  # Ruta al archivo de la base de datos
        self.init_database()  # Crea las tablas si no existen
    
    def init_database(self):
        """Crea las tablas necesarias si no existen"""
        with sqlite3.connect(self.db_path) as conn:  # Abre conexión a la base de datos
            cursor = conn.cursor()  # Crea un cursor para ejecutar comandos SQL
            
            # Tabla para las sesiones de chat
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS chat_sessions (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    session_name TEXT NOT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    last_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            
            # Tabla para los mensajes del chat
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS chat_messages (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    session_id INTEGER NOT NULL,
                    message_type TEXT NOT NULL, -- 'user', 'assistant', 'image'
                    content TEXT NOT NULL,
                    user_name TEXT,
                    emotion TEXT,
                    image_data BLOB,
                    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (session_id) REFERENCES chat_sessions (id)
                )
            ''')
            
            conn.commit()  # Guarda los cambios
    
    def create_new_session(self, session_name: str) -> int:
        """Crea una nueva sesión de chat y retorna su ID"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute(
                "INSERT INTO chat_sessions (session_name) VALUES (?)",
                (session_name,)
            )
            conn.commit()
            return cursor.lastrowid  # Retorna el ID de la nueva sesión
    
    def save_message(self, session_id: int, message_type: str, content: str, 
                    user_name: Optional[str] = None, emotion: Optional[str] = None,
                    image_data: Optional[bytes] = None) -> int:
        """Guarda un mensaje en la base de datos"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute('''
                INSERT INTO chat_messages 
                (session_id, message_type, content, user_name, emotion, image_data)
                VALUES (?, ?, ?, ?, ?, ?)
            ''', (session_id, message_type, content, user_name, emotion, image_data))
            
            # Actualizar timestamp de la sesión
            cursor.execute(
                "UPDATE chat_sessions SET last_updated = CURRENT_TIMESTAMP WHERE id = ?",
                (session_id,)
            )
            
            conn.commit()
            return cursor.lastrowid  # Retorna el ID del mensaje guardado
    
    def get_all_sessions(self) -> List[Dict]:
        """Obtiene todas las sesiones de chat ordenadas por fecha de actualización"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute('''
                SELECT id, session_name, created_at, last_updated,
                       (SELECT COUNT(*) FROM chat_messages WHERE session_id = chat_sessions.id) as message_count
                FROM chat_sessions 
                ORDER BY last_updated DESC
            ''')
            
            sessions = []  # Lista para almacenar las sesiones
            for row in cursor.fetchall():
                sessions.append({
                    'id': row[0],
                    'name': row[1],
                    'created_at': row[2],
                    'last_updated': row[3],
                    'message_count': row[4]
                })
            
            return sessions  # Retorna la lista de sesiones
    
    def get_session_messages(self, session_id: int) -> List[Dict]:
        """Obtiene todos los mensajes de una sesión específica"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute('''
                SELECT id, message_type, content, user_name, emotion, image_data, timestamp
                FROM chat_messages 
                WHERE session_id = ?
                ORDER BY timestamp ASC
            ''', (session_id,))
            
            messages = []  # Lista para almacenar los mensajes
            for row in cursor.fetchall():
                message = {
                    'id': row[0],
                    'type': row[1],
                    'content': row[2],
                    'user_name': row[3],
                    'emotion': row[4],
                    'image_data': row[5],
                    'timestamp': row[6]
                }
                messages.append(message)
            
            return messages  # Retorna la lista de mensajes
    
    def delete_session(self, session_id: int) -> bool:
        """Elimina una sesión de chat y todos sus mensajes"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                # Eliminar mensajes primero (por la foreign key)
                cursor.execute("DELETE FROM chat_messages WHERE session_id = ?", (session_id,))
                # Eliminar la sesión
                cursor.execute("DELETE FROM chat_sessions WHERE id = ?", (session_id,))
                conn.commit()
                return True  # Éxito
        except Exception as e:
            print(f"Error eliminando sesión: {e}")
            return False  # Fallo
    
    def get_session_info(self, session_id: int) -> Optional[Dict]:
        """Obtiene información de una sesión específica"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute('''
                SELECT id, session_name, created_at, last_updated
                FROM chat_sessions 
                WHERE id = ?
            ''', (session_id,))
            
            row = cursor.fetchone()
            if row:
                return {
                    'id': row[0],
                    'name': row[1],
                    'created_at': row[2],
                    'last_updated': row[3]
                }
            return None  # Si no existe la sesión
    
    def save_image_to_db(self, session_id: int, image_path: str, user_name: str, emotion: str) -> int:
        """Guarda una imagen en la base de datos"""
        try:
            with open(image_path, 'rb') as f:
                image_data = f.read()  # Lee la imagen como binario
            
            return self.save_message(
                session_id=session_id,
                message_type='image',
                content=f"Imagen de {user_name} - Emoción: {emotion}",
                user_name=user_name,
                emotion=emotion,
                image_data=image_data
            )
        except Exception as e:
            print(f"Error guardando imagen: {e}")
            return -1  # Error
    
    def get_image_data(self, message_id: int) -> Optional[bytes]:
        """Obtiene los datos de una imagen específica"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute('''
                SELECT image_data FROM chat_messages 
                WHERE id = ? AND message_type = 'image'
            ''', (message_id,))
            
            row = cursor.fetchone()
            return row[0] if row else None  # Retorna los datos binarios de la imagen si existen 