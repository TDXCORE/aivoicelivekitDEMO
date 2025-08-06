# TDX Chatbot Test Interface

Sistema de testing completamente aislado para el chatbot TDX WhatsApp Agent.

## 🎯 Características

- **Mismo agente de producción**: Usa exactamente el mismo código que Chatwoot
- **Aislamiento total**: No afecta conversaciones reales ni datos de Chatwoot  
- **Reset completo**: Reinicia estado y memoria para pruebas frescas
- **UI estilo ChatGPT**: Interfaz moderna y responsive
- **Exportación de datos**: Descarga conversaciones para análisis
- **Métricas en tiempo real**: Monitoreo del estado del agente

## 🚀 Inicio Rápido

### 1. Ejecutar el servidor de testing
```bash
python main_test.py
```

### 2. Abrir la interfaz web
```
http://127.0.0.1:8001/
```

### 3. Comenzar a probar
- Envía mensajes al chatbot
- Observa las respuestas en tiempo real
- Usa el botón "Reset" para empezar una nueva prueba
- Exporta conversaciones para análisis

## 🔧 Endpoints de API

### Chat
```
POST /api/test/chat
{
    "message": "Hola, necesito ayuda con desarrollo de software"
}
```

### Reset
```
POST /api/test/reset
```

### Estado
```
GET /api/test/status
```

### Historial
```
GET /api/test/conversation
```

### Exportar
```
GET /api/test/debug/export
```

## 📁 Estructura de Archivos

```
testing/
├── __init__.py                 # Módulo Python
├── test_storage.py            # Almacenamiento temporal
├── test_integration.py        # Wrapper del agente existente
├── test_router.py             # Endpoints FastAPI
├── frontend/                  # Interfaz web
│   ├── index.html            # Página principal
│   ├── style.css             # Estilos ChatGPT
│   └── script.js             # Lógica frontend
└── README.md                 # Esta documentación

main_test.py                   # Servidor de testing
```

## 🔒 Garantías de Seguridad

### ✅ Lo que NO se afecta
- Código de producción (`src/`)
- Integración con Chatwoot
- Conversaciones reales
- Configuración existente
- Servidor de producción (puerto 8000)

### ✅ Lo que SÍ funciona igual
- Lógica del agente WhatsApp
- OpenAI function calling
- Microsoft Graph integration
- Validaciones de negocio
- Flujo de conversación completo

## 🧪 Casos de Prueba Recomendados

### 1. Flujo Completo
```
Usuario: "Hola, necesito desarrollo de software"
Bot: [Respuesta de bienvenida]
Usuario: "Quiero una aplicación móvil"
Bot: [Preguntas sobre el proyecto]
Usuario: "Mi email es test@example.com"
Bot: [Confirmación y siguiente paso]
```

### 2. Validación de Presupuesto
```
Usuario: "¿Cuánto cuesta?"
Bot: [Opciones de presupuesto]
Usuario: "Opción 2"
Bot: [Confirmación y calendario]
```

### 3. Programación de Reuniones
```
Usuario: "Quiero agendar una reunión"
Bot: [Opciones de calendario real]
Usuario: "Mañana a las 10 AM"
Bot: [Confirmación de reunión]
```

## 🐛 Debugging

### Ver logs del servidor
Los logs se guardan en `test_server.log`

### Estado detallado del agente
```
GET /api/test/debug/agent-state
```

### Exportar conversación completa
```
GET /api/test/debug/export
```

## 🔄 Reset y Limpieza

### Reset manual
- Botón "Reset" en la interfaz
- `POST /api/test/reset` via API

### Reset automático
- Cada vez que se inicia el servidor
- Nueva instancia del agente
- Memoria completamente limpia

## 📊 Métricas Disponibles

- Duración de sesión
- Número de mensajes (usuario/bot)
- Progreso de recolección de datos
- Etapa actual de conversación
- Estado del agente interno

## 🛠️ Desarrollo

### Modificar el agente
1. Edita `src/agents/whatsapp_agent.py`
2. Los cambios se reflejan automáticamente en testing
3. Reinicia el servidor si es necesario (`Ctrl+C` y `python main_test.py`)

### Agregar nuevas funciones
1. Las nuevas funciones de OpenAI funcionan automáticamente
2. Nuevas integraciones se ven reflejadas
3. Cambios en la lógica de negocio son inmediatos

## ❓ Solución de Problemas

### Error: "Test agent not initialized"
```bash
# Reiniciar el servidor
python main_test.py
```

### Error: "OpenAI API key not found"
```bash
# Verificar variables de entorno
echo $OPENAI_API_KEY
```

### Error: "Port already in use"
```bash
# El servidor usa puerto 8001 automáticamente
# Puerto 8000 es para producción
```

### Frontend no carga
```bash
# Verificar que los archivos estén en testing/frontend/
ls testing/frontend/
```

## 📞 Soporte

Para problemas con el sistema de testing:
1. Verificar logs en `test_server.log`
2. Comprobar endpoint `/api/test/health`
3. Reiniciar servidor si es necesario