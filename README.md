# TDX AI Voice & WhatsApp Bot Service

Sistema integrado de agentes de IA para llamadas de voz y WhatsApp con integración completa a Chatwoot Cloud y Microsoft Graph.

## 📁 Estructura del Proyecto

### `/src` - Código Fuente Principal

#### `/src/core` - Componentes Centrales
- **`startup.py`** - Script de inicialización que arranca webhook receiver y voice agent en paralelo

#### `/src/webhooks` - Manejadores de Webhooks
- **`receiver.py`** - Receptor principal de webhooks de Chatwoot
  - Procesa eventos `contact_created` de landing pages
  - Integra llamadas Telnyx con fallback automático a WhatsApp
  - Maneja webhooks de WhatsApp y Telnyx
  - Endpoints de health check y métricas
- **`whatsapp_handler.py`** - Handler específico para webhooks de WhatsApp
  - Procesa mensajes entrantes de WhatsApp
  - Maneja bots activos por conversación
  - Validaciones de seguridad (pendiente completar)

#### `/src/agents` - Agentes de IA
*Directorio preparado para agentes de IA - actualmente vacío*

#### `/src/ai` - Componentes de Inteligencia Artificial
- **`bant_scorer.py`** - Sistema de calificación BANT (Budget, Authority, Need, Timeline)
  - Evalúa leads en base a presupuesto, autoridad, necesidad y tiempo
  - Mapeo por industria y posición
  - Scoring hasta 100 puntos (60+ = calificado)

- **`conversation_guard.py`** - Protección contra loops conversacionales
  - Detecta patrones repetitivos
  - Previene respuestas cíclicas
  - Manejo de conversaciones bloqueadas

- **`intent_classifier.py`** - Clasificador de intenciones
  - Clasifica mensajes en categorías (consulta, queja, etc.)
  - Machine Learning con TF-IDF + Logistic Regression
  - Detección rápida de off-topic

- **`micro_value_injector.py`** - Inyector de micro-valor
  - Genera respuestas cortas con valor específico
  - Sin mencionar precios directamente
  - Contexto por servicio TDX

- **`minimal_slot_manager.py`** - Manejo de slots conversacionales
  - Recolección progresiva de información
  - Gestión de datos de contacto
  - Validación de completitud de datos

- **`service_mapper.py`** - Mapeador de servicios TDX
  - Mapea keywords a servicios específicos
  - Detección de industria y contexto
  - Confidence scoring por servicio

- **`stt_handler.py`** - Speech-to-Text con Whisper
  - Procesamiento de mensajes de audio
  - Integración con OpenAI Whisper
  - Manejo de errores y timeouts

#### `/src/integrations` - Integraciones Externas

##### `/src/integrations/chatwoot`
- **`chatwoot_summary_integration.py`** - Integración completa con Chatwoot Cloud
  - Envío de resúmenes a conversations
  - Creación automática de conversaciones
  - Manejo de custom attributes
  - Reintentos automáticos

##### `/src/integrations/microsoft`
- **`microsoft_graph_client.py`** - Cliente de Microsoft Graph API
  - Integración con Outlook Calendar
  - Autenticación con Client Credentials
  - Operaciones de calendario y reuniones
  - Integración con Business Hours Validator

##### `/src/integrations/validators`
- **`business_hours.py`** - Validador de horarios comerciales
  - Horarios Colombia: Lunes-Viernes 8AM-4PM
  - Validación de días festivos colombianos
  - Generación de slots disponibles
  - Formateo de fechas en español

##### `/src/integrations` (raíz)
- **`whatsapp_client.py`** - Cliente WhatsApp para Chatwoot
  - Envío de mensajes vía Chatwoot API
  - Manejo de conversaciones activas
  - Typing indicators y estados
  - Rate limiting y retries

#### `/src/data` - Archivos de Datos
- **`cases.json`** - Casos de ejemplo y datos de entrenamiento

### `/config` - Configuración
- **`requirements.txt`** - Dependencias Python del proyecto
- **`render.yaml`** - Configuración para deploy en Render.com
- **`Dockerfile`** - Configuración de contenedor Docker

### `/scripts` - Scripts de Utilidad
*Directorio preparado para scripts auxiliares - actualmente vacío*

## 🚀 Funcionalidades Principales

### Voice System (Telnyx Integration)
- **Llamadas salientes automáticas** desde webhooks de Chatwoot
- **Fallback automático a WhatsApp** si llamada falla o no contesta
- **AI Assistant integrado** con funciones personalizadas
- **Gestión de transferencias** y programación de reuniones

### WhatsApp Bot System
- **Procesamiento inteligente** de mensajes entrantes
- **Clasificación de intenciones** con ML
- **Recolección progresiva de datos** (slot-filling)
- **Calificación automática BANT** de leads
- **Protección anti-loops** conversacionales
- **Integración completa con Chatwoot**

### Microsoft Graph Integration
- **Programación automática** de reuniones
- **Validación de horarios comerciales** colombianos
- **CC automático** a team members
- **Sincronización con Outlook Calendar**

### Chatwoot Cloud Integration
- **Recepción de webhooks** contact_created
- **Envío automático de resúmenes** conversacionales
- **Creación de conversaciones** proactivas
- **Gestión de multiple inboxes**
- **Custom attributes** para tracking

## 🛠️ Configuración

### Variables de Entorno Requeridas

#### Chatwoot
```env
VITE_CHATWOOT_ACCOUNT_ID=your_account_id
VITE_CHATWOOT_API_TOKEN=your_api_token
CHATWOOT_WHATSAPP_INBOX_ID=whatsapp_inbox_id
CHATWOOT_WEBHOOK_INBOX_ID=webhook_inbox_id
CHATWOOT_BOT_AGENT_ID=bot_agent_id
```

#### Telnyx (Voice)
```env
TELNYX_API_KEY=your_telnyx_api_key
TELNYX_CONNECTION_ID=your_connection_id
TELNYX_ASSISTANT_ID=your_assistant_id
TELNYX_OUTBOUND_NUMBER=your_phone_number
```

#### Microsoft Graph
```env
AZURE_CLIENT_ID=your_app_id
AZURE_CLIENT_SECRET=your_app_secret
AZURE_TENANT_ID=your_tenant_id
```

#### OpenAI (para STT)
```env
OPENAI_API_KEY=your_openai_key
```

### Feature Flags
```env
WHATSAPP_BOT_ENABLED=true
USE_TELNYX_INSTEAD_OF_LIVEKIT=true
WHATSAPP_FALLBACK_ENABLED=true
CREATE_WEBHOOK_CONVERSATIONS_ENABLED=true
```

## 📊 Endpoints Principales

### Health Checks
- `GET /` - Status general del servicio
- `GET /health` - Health check completo con configuración
- `GET /health/whatsapp` - Health check específico WhatsApp
- `GET /health/telnyx` - Health check específico Telnyx

### Webhooks
- `POST /webhooks/chatwoot/{token}` - Webhook principal Chatwoot
- `POST /webhooks/whatsapp/{token}` - Webhook WhatsApp
- `POST /webhooks/telnyx` - Webhook Telnyx Voice

### Funciones Telnyx AI
- `POST /telnyx/functions/transfer` - Transferencia de llamadas
- `POST /telnyx/functions/schedule` - Programar reuniones
- `POST /telnyx/functions/collect_email` - Recolectar emails

### Admin/Métricas
- `GET /admin/whatsapp/metrics` - Métricas WhatsApp
- `POST /admin/whatsapp/cleanup` - Limpieza de bots inactivos
- `GET /admin/whatsapp/conversations/{id}` - Estado conversación

## 🔧 Instalación y Ejecución

### Instalación
```bash
pip install -r config/requirements.txt
```

### Ejecución
```bash
# Opción 1: Servidor webhook standalone
python -m src.webhooks.receiver

# Opción 2: Con startup completo (voice + webhook)
python -m src.core.startup
```

### Docker
```bash
docker build -f config/Dockerfile -t tdx-ai-service .
docker run -p 8000:8000 tdx-ai-service
```

## 🏗️ Arquitectura

### Flujo Principal (Contact Created)
1. **Webhook recibido** desde Chatwoot landing page
2. **Validación** de origen y datos
3. **Llamada Telnyx** + **WhatsApp proactivo** (paralelo)
4. **Fallback automático** a WhatsApp si llamada falla
5. **Conversación automática** creada en Chatwoot

### Flujo WhatsApp Bot
1. **Mensaje recibido** vía webhook
2. **Clasificación de intención** (ML)
3. **Slot-filling progresivo** de datos
4. **Scoring BANT** automático
5. **Micro-valor** contextual inyectado
6. **Resumen enviado** a Chatwoot

### Integraciones Clave
- **Chatwoot Cloud**: CRM y comunicaciones
- **Telnyx**: Voice AI y telefonía
- **Microsoft Graph**: Calendar y reuniones
- **OpenAI**: Speech-to-Text processing

## 📈 Métricas y Monitoreo

- **Logs estructurados** por componente
- **Health checks** diferenciados
- **Métricas de conversación** (pendiente)
- **Performance tracking** (pendiente)
- **Error tracking** integrado

## 🔒 Seguridad

- **Token validation** en webhooks
- **Rate limiting** implementado
- **PII protection** en logs
- **Environment-based** configuration
- **Secure credential** management

---

**TDX AI Service - Transformación Digital Inteligente**