# Agente de Visión - Chat con Base de Datos

Un agente conversacional inteligente que combina visión por computadora (CNN) y procesamiento de lenguaje natural (LLM) para crear un chat personalizado que detecta la identidad y emoción del usuario a partir de imágenes.

## 🚀 Características

### Visión por Computadora
- **Detección de Usuario**: Identifica automáticamente entre Abrahan y Jesus
- **Análisis de Emociones**: Detecta 7 emociones diferentes (cansado, enojado, feliz, pensativo, riendo, sorprendido, triste)
- **Procesamiento de Imágenes**: Redimensiona automáticamente a 96x96 píxeles para el análisis

### Procesamiento de Lenguaje Natural
- **Modelo Local**: Utiliza Llama3 a través de Ollama para respuestas locales
- **Contexto Emocional**: Adapta las respuestas según la emoción detectada
- **Historial de Conversación**: Mantiene contexto de conversaciones anteriores

### Base de Datos SQLite
- **Persistencia de Chat**: Guarda automáticamente todas las conversaciones
- **Gestión de Sesiones**: Múltiples sesiones de chat independientes
- **Almacenamiento de Imágenes**: Guarda las imágenes subidas junto con su análisis
- **Restauración Completa**: Carga conversaciones anteriores con todo el contexto

### Interfaz de Usuario
- **Tkinter GUI**: Interfaz gráfica intuitiva y moderna
- **Gestión de Sesiones**: Menú para crear, cargar y gestionar sesiones
- **Exportación**: Exporta chats a archivos de texto
- **Visualización**: Muestra imágenes, emociones y usuarios detectados

## 📁 Estructura del Proyecto

```
Agente de vision/
├── modules/
│   ├── __init__.py
│   ├── vision_module.py      # Módulo de visión por computadora
│   ├── llm_module.py         # Módulo de procesamiento de lenguaje
│   └── database_module.py    # Módulo de base de datos SQLite
├── models/
│   ├── cnn_model.h5          # Modelo CNN entrenado
│   └── classes.txt           # Clases de usuarios y emociones
├── emociones/                # Imágenes de entrenamiento
├── config.py                 # Configuración del proyecto
├── tk_chat.py               # Interfaz principal
├── test_database.py         # Script de prueba de BD
├── requirements.txt         # Dependencias
└── README.md               # Este archivo
```

## 🛠️ Instalación

### Prerrequisitos
- Python 3.8 o superior
- Ollama instalado con el modelo Llama3

### Instalación de Dependencias
```bash
pip install -r requirements.txt
```

### Configuración de Ollama
```bash
# Instalar Llama3
ollama pull llama3

# Verificar instalación
ollama list
```

## 🚀 Uso

### Ejecutar la Aplicación Principal
```bash
python tk_chat.py
```

### Probar la Base de Datos
```bash
python test_database.py
```

## 📊 Funcionalidades de Base de Datos

### Gestión de Sesiones
- **Nueva Sesión**: Crea automáticamente una nueva sesión al iniciar
- **Cargar Sesión**: Selecciona y carga conversaciones anteriores
- **Gestionar Sesiones**: Lista, elimina y organiza sesiones existentes

### Almacenamiento Automático
- **Mensajes de Usuario**: Se guardan automáticamente con timestamp
- **Respuestas del Asistente**: Se almacenan junto con el contexto
- **Imágenes**: Se guardan como BLOB con metadatos de análisis
- **Metadatos**: Usuario, emoción y timestamp de cada interacción

### Restauración de Conversaciones
- **Contexto Completo**: Restaura usuario, emoción y historial
- **Imágenes**: Recupera las imágenes subidas anteriormente
- **Continuidad**: Permite continuar conversaciones donde se quedaron

## 🎯 Flujo de Trabajo

1. **Inicio**: La aplicación crea automáticamente una nueva sesión
2. **Subir Imagen**: Selecciona una imagen para detectar usuario y emoción
3. **Chat**: Interactúa con el agente que adapta respuestas al contexto
4. **Guardado**: Todo se guarda automáticamente en la base de datos
5. **Restauración**: Puedes cargar sesiones anteriores en cualquier momento

## 🔧 Configuración

### Archivo config.py
```python
# Usuarios reconocidos
USERS = {
    "abrahan": "Abrahan",
    "jesus": "Jesus"
}

# Emociones detectadas
EMOTIONS = [
    "cansado", "enojado", "feliz", "pensativo", 
    "riendo", "sorprendido", "triste"
]
```

### Base de Datos
- **Archivo**: `chat_history.db` (se crea automáticamente)
- **Tablas**: 
  - `chat_sessions`: Información de sesiones
  - `chat_messages`: Mensajes, imágenes y metadatos

## 🧪 Pruebas

### Probar Base de Datos
```bash
python test_database.py
```

Este script prueba:
- Creación de sesiones
- Guardado de mensajes
- Almacenamiento de imágenes
- Consultas y recuperación de datos

## 📝 Notas Técnicas

### Modelo CNN
- **Arquitectura**: Red neuronal convolucional
- **Entrada**: Imágenes 96x96 píxeles
- **Salida**: 14 clases (2 usuarios × 7 emociones)
- **Entrenamiento**: Ver `train_cnn_model.py`

### LLM (Llama3)
- **Modelo**: Llama3 local via Ollama
- **Contexto**: Incluye usuario, emoción e historial (optimizado)
- **Timeout**: 15 segundos por respuesta
- **Fallback**: Respuestas automáticas si hay timeout o error
- **Optimizaciones**: Prompts concisos, parámetros optimizados para velocidad

### Base de Datos SQLite
- **Persistencia**: Archivo local `chat_history.db`
- **Transacciones**: Automáticas para integridad
- **Índices**: Optimizados para consultas frecuentes
- **Backup**: Copia manual del archivo .db

## 🐛 Solución de Problemas

### Error: "Modelo no encontrado"
```bash
python train_cnn_model.py
```

### Error: "Ollama no disponible"
```bash
# Instalar Ollama
curl -fsSL https://ollama.ai/install.sh | sh

# Instalar Llama3
ollama pull llama3

# Verificar que esté ejecutándose
ollama serve
```

### Error: "Timeout del modelo LLM"
- El sistema ahora usa respuestas de fallback automáticas
- Las respuestas son más rápidas (5-8 segundos promedio)
- Si persisten los timeouts, verifica que Ollama esté ejecutándose correctamente

### Error: "Base de datos corrupta"
- Eliminar `chat_history.db`
- La aplicación creará una nueva automáticamente

## 🤝 Contribuciones

1. Fork el proyecto
2. Crea una rama para tu feature
3. Commit tus cambios
4. Push a la rama
5. Abre un Pull Request

## 📄 Licencia

Este proyecto está bajo la Licencia MIT. Ver el archivo `LICENSE` para más detalles.

## 🙏 Agradecimientos

- **TensorFlow/Keras**: Para el modelo CNN
- **Ollama**: Para el modelo Llama3 local
- **PIL/Pillow**: Para procesamiento de imágenes
- **SQLite**: Para la base de datos local 