import sqlite3
import os
import base64
from datetime import datetime
from typing import List, Dict, Optional, Tuple
import json

class ChatDatabase:
    def __init__(self, db_path: str = "chat_history.db"):
        """Inicializa la base de datos de chat"""
        self.db_path = db_path
        self.init_database()
    
    def init_database(self):
        """Crea las tablas necesarias si no existen"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            
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
            
            conn.commit()
    
    def create_new_session(self, session_name: str) -> int:
        """Crea una nueva sesión de chat y retorna su ID"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute(
                "INSERT INTO chat_sessions (session_name) VALUES (?)",
                (session_name,)
            )
            conn.commit()
            return cursor.lastrowid
    
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
            return cursor.lastrowid
    
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
            
            sessions = []
            for row in cursor.fetchall():
                sessions.append({
                    'id': row[0],
                    'name': row[1],
                    'created_at': row[2],
                    'last_updated': row[3],
                    'message_count': row[4]
                })
            
            return sessions
    
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
            
            messages = []
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
            
            return messages
    
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
                return True
        except Exception as e:
            print(f"Error eliminando sesión: {e}")
            return False
    
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
            return None
    
    def save_image_to_db(self, session_id: int, image_path: str, user_name: str, emotion: str) -> int:
        """Guarda una imagen en la base de datos"""
        try:
            with open(image_path, 'rb') as f:
                image_data = f.read()
            
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
            return -1
    
    def get_image_data(self, message_id: int) -> Optional[bytes]:
        """Obtiene los datos de una imagen específica"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute('''
                SELECT image_data FROM chat_messages 
                WHERE id = ? AND message_type = 'image'
            ''', (message_id,))
            
            row = cursor.fetchone()
            return row[0] if row else None 