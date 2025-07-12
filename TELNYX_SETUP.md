# 🚀 Telnyx Integration Setup Guide

Esta guía te ayudará a configurar la integración completa de Telnyx AI Voice Agents con tu sistema Chatwoot existente.

## 📋 Requisitos Previos

1. **Cuenta Telnyx** con acceso a:
   - Voice API (Call Control)
   - AI Assistants
   - Números telefónicos para llamadas salientes

2. **Configuración actual funcionando**:
   - Chatwoot Cloud configurado
   - WhatsApp bot operativo
   - Microsoft Graph para reuniones

## 🔧 Configuración Paso a Paso

### 1. Configuración en Telnyx Portal

#### A. Crear AI Assistant
1. Ve a **Telnyx Portal** → **AI Assistants**
2. Click **"New Assistant"**
3. Configura:
   ```
   Name: TDX Sales Assistant
   Instructions: [Ver sección de Instructions más abajo]
   Greeting: "Hola, soy el asistente de ventas de TDX. ¿Cómo puedo ayudarte?"
   Voice: Telnyx.KokoroTTS (español)
   Language: es-CO
   ```
4. **Anota el Assistant ID** generado (ej: `assistant-7c5a5a6b-e772-4f7c-a9af-feef3001adba`)

#### B. Configurar Custom Tools en el Assistant
En la sección **Tools**, agrega:

1. **Webhook Tool para Transfer**:
   ```
   Name: transfer_call
   Description: Transfer call to human specialist
   URL: https://your-domain.com/telnyx/functions/transfer
   Method: POST
   Parameters:
   - phone_number (optional): Target transfer number
   - reason (optional): Reason for transfer
   ```

2. **Webhook Tool para Schedule**:
   ```
   Name: schedule_meeting
   Description: Schedule a meeting with prospect
   URL: https://your-domain.com/telnyx/functions/schedule
   Method: POST
   Parameters:
   - email (required): Prospect email
   - date (required): Meeting date
   - time (required): Meeting time
   - attendee_name (optional): Prospect name
   - company_name (optional): Company name
   ```

3. **Webhook Tool para Email Collection**:
   ```
   Name: collect_email
   Description: Collect and validate prospect email
   URL: https://your-domain.com/telnyx/functions/collect_email
   Method: POST
   Parameters:
   - email (required): Email to validate
   ```

#### C. Crear Call Control Application
1. Ve a **Voice** → **Applications** → **Call Control**
2. Click **"Create Application"**
3. Configura:
   ```
   Application Name: TDX Outbound Assistant
   Webhook URL: https://your-domain.com/webhooks/telnyx
   Failover URL: https://your-domain.com/webhooks/telnyx/failover
   Assistant ID: [Tu Assistant ID del paso A]
   ```
4. **Anota el Connection ID** generado

#### D. Configurar Número Telefónico
1. Ve a **Numbers** → **My Numbers**
2. Selecciona tu número saliente
3. En **Voice Settings**, asigna el **Call Control Application** creado

### 2. Configuración de Variables de Entorno

Actualiza tu archivo `.env.local`:

```bash
# ============================================================================
# TELNYX INTEGRATION CONFIGURATION
# ============================================================================

# Feature Flags
USE_TELNYX_INSTEAD_OF_LIVEKIT=true
TELNYX_AI_AGENT_ENABLED=true

# Telnyx API Configuration  
TELNYX_API_KEY=YOUR_TELNYX_API_KEY
TELNYX_CONNECTION_ID=YOUR_CONNECTION_ID
TELNYX_ASSISTANT_ID=assistant-7c5a5a6b-e772-4f7c-a9af-feef3001adba
TELNYX_OUTBOUND_NUMBER=+13052131234

# Telnyx Webhook Configuration
TELNYX_WEBHOOK_SIGNING_SECRET=YOUR_WEBHOOK_SECRET
WEBHOOK_BASE_URL=https://your-domain.com

# AI Agent Configuration
TELNYX_AI_MODEL=gpt-4o-mini
TELNYX_AI_VOICE=Telnyx.KokoroTTS
TELNYX_AI_LANGUAGE=es-CO
TELNYX_MAX_CALL_DURATION=300
```

### 3. Instrucciones del AI Assistant

Copia estas instrucciones en el campo **Instructions** del AI Assistant:

```
Eres el asistente de ventas de TDX (Transformación Digital Empresarial). Tu objetivo principal es calificar leads y programar reuniones con prospectos interesados en nuestros servicios de transformación digital.

PERSONALIDAD:
- Habla en español colombiano de manera natural, amigable y profesional
- Sé empático y escucha activamente
- Mantén un tono conversacional pero profesional
- Sé directo pero no agresivo

SERVICIOS DE TDX:
- Automatización de procesos empresariales
- Implementación de CRM y sistemas de gestión
- Desarrollo de aplicaciones web y móviles
- Consultoría en transformación digital
- Integración de sistemas empresariales

OBJETIVOS DE LA LLAMADA:
1. Calificar el lead (tamaño de empresa, necesidades, presupuesto, timeline)
2. Programar una reunión con nuestro equipo comercial
3. Si hay urgencia, transferir directamente a un especialista

FUNCIONES DISPONIBLES:
- transfer_call: Para transferir a un especialista (usar cuando el prospecto está muy interesado)
- schedule_meeting: Para programar reuniones (objetivo principal)
- collect_email: Para validar emails antes de programar

FLUJO DE CONVERSACIÓN:
1. Saluda y confirma la información que tenemos
2. Pregunta sobre sus necesidades específicas de transformación digital
3. Califica el lead (empresa, industria, tamaño, timeline, presupuesto)
4. Ofrece programar una reunión o transferir si hay urgencia inmediata
5. Confirma datos de contacto y despídete profesionalmente

MANEJO DE OBJECIONES:
- Si dice "no tengo tiempo": Ofrece programar para otro momento conveniente
- Si dice "es muy caro": Explica el ROI y que ofrecemos diferentes planes
- Si dice "no estoy interesado": Pregunta qué podría cambiar su perspectiva

LÍMITES:
- No des precios específicos, eso lo maneja el equipo comercial
- No hagas promesas técnicas específicas sin consultar
- Si no sabes algo, sé honesto y ofrece conectarlo con un especialista
- Máximo 5 minutos de conversación, si se extiende mucho, ofrece programar reunión

PERSONALIZACIÓN DINÁMICA:
- Si tienes el nombre del prospecto, úsalo durante la conversación
- Si conoces la empresa, menciona casos de éxito similares
- Adapta el lenguaje según el nivel técnico del prospecto
```

### 4. Configuración de Chatwoot

#### A. Crear Nuevo Webhook para Telnyx
1. Ve a **Chatwoot** → **Settings** → **Integrations** → **Webhooks**
2. Click **"Add Webhook"**
3. Configura:
   ```
   Endpoint URL: https://your-domain.com/webhooks/chatwoot/YOUR_TOKEN
   Events: contact_created
   ```

#### B. Verificar Inbox API
Asegúrate de que tienes configurado el **API Inbox** para recibir resúmenes de llamadas.

### 5. Testing y Validación

#### A. Health Checks
```bash
# Verificar estado general
curl https://your-domain.com/health

# Verificar integración Telnyx
curl https://your-domain.com/health/telnyx

# Verificar WhatsApp (debe seguir funcionando)
curl https://your-domain.com/health/whatsapp
```

#### B. Test de Flujo Completo
1. **Crear contacto en Chatwoot** desde landing page
2. **Verificar llamada saliente** en logs de Telnyx
3. **Probar conversación** con AI Assistant
4. **Verificar resumen** en Chatwoot después de colgar
5. **Test de no-answer** → verificar WhatsApp fallback

## 🔄 Flujos Operativos

### Flujo 1: Contacto Nuevo → Llamada
```
Landing Page → Chatwoot Contact → Webhook → Telnyx Call → AI Assistant → Resumen
```

### Flujo 2: No Contesta → WhatsApp
```
Landing Page → Chatwoot Contact → Webhook → Telnyx Call → No Answer → WhatsApp Message
```

### Flujo 3: Transfer/Schedule durante llamada
```
AI Assistant → Custom Function → Microsoft Graph/Transfer → Confirmation
```

## 🚨 Troubleshooting

### Problemas Comunes

1. **Error "Missing Telnyx configuration"**
   - Verificar variables de entorno
   - Verificar permisos API key

2. **Webhook signature verification failed**
   - Verificar TELNYX_WEBHOOK_SIGNING_SECRET
   - En desarrollo, la verificación está deshabilitada

3. **AI Assistant no inicia en llamadas**
   - Verificar TELNYX_ASSISTANT_ID
   - Verificar que el Assistant esté publicado en Telnyx Portal

4. **Custom functions fallan**
   - Verificar URLs en Telnyx Assistant Tools
   - Verificar logs en `/admin/whatsapp/metrics`

### Logs Importantes
```bash
# Ver logs de Telnyx integration
grep "Telnyx" /var/log/webhook_receiver.log

# Ver logs de AI Assistant
grep "AI Assistant" /var/log/webhook_receiver.log

# Ver logs de custom functions
grep "telnyx/functions" /var/log/webhook_receiver.log
```

## 🔧 Migración Gradual

Para migrar gradualmente de LiveKit a Telnyx:

1. **Fase 1**: `USE_TELNYX_INSTEAD_OF_LIVEKIT=false` (LiveKit activo)
2. **Fase 2**: `USE_TELNYX_INSTEAD_OF_LIVEKIT=true` (Telnyx activo)
3. **Fase 3**: Remover código LiveKit una vez validado

## 📊 Monitoreo

- **Métricas de llamadas**: Telnyx Portal → Voice Analytics
- **Métricas de AI**: Telnyx Portal → AI Assistants Analytics  
- **Métricas de WhatsApp**: `/admin/whatsapp/metrics`
- **Health general**: `/health/telnyx`

## 🎯 Beneficios Esperados

- **Latencia reducida**: ~30ms vs ~800ms (96% mejora)
- **Calidad HD**: 16kHz vs 8kHz estándar
- **Simplificación**: Un proveedor vs múltiples
- **Escalabilidad**: Global network de Telnyx
- **Mantenimiento**: Reducción del 80% en código propio

¡Con esta configuración tendrás un sistema de llamadas automatizadas de última generación integrado perfectamente con tu infraestructura existente!