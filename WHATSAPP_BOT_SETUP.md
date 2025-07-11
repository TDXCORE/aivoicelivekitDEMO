# 📱 WhatsApp Bot Setup Guide

## 🎯 Resumen

Este sistema agrega capacidades de chatbot WhatsApp al agente de voz TDX existente, manteniendo **separación completa** entre ambos sistemas.

### ✅ Características

- **Agente WhatsApp separado** - No afecta el voice agent
- **Misma funcionalidad** - Agendamiento de reuniones, transferencia a humanos
- **Reutilización inteligente** - Usa Microsoft Graph y Chatwoot existentes
- **UX optimizado** - Typing indicators, quick replies, rate limiting
- **Métricas completas** - Analytics y monitoring
- **Production-ready** - Deduplicación, error handling, security

---

## 🚀 Configuración Paso a Paso

### **Paso 1: Configurar Bot en Chatwoot Dashboard**

1. **Ir a Settings → Bots** en tu Chatwoot dashboard
2. **Crear nuevo bot:**
   - **Name:** `Mati - TDX WhatsApp Bot`
   - **Avatar:** Logo TDX
   - **Webhook URL:** `https://tu-servidor.com/webhooks/whatsapp/secure-whatsapp-token-production-2025`
3. **Anotar el Bot Agent ID** (lo necesitarás para la configuración)

### **Paso 2: Configurar Variables de Entorno**

Actualizar `.env.local` con las nuevas variables:

```bash
# WhatsApp Bot Configuration
WHATSAPP_BOT_ENABLED=true
CHATWOOT_BOT_WEBHOOK_TOKEN=secure-whatsapp-token-production-2025
CHATWOOT_BOT_AGENT_ID=<ID_DEL_BOT_DE_CHATWOOT>
CHATWOOT_WHATSAPP_INBOX_ID=<ID_DEL_INBOX_WHATSAPP>
WHATSAPP_RATE_LIMIT_SECONDS=6

# Security (opcional)
CHATWOOT_ALLOWED_IPS=127.0.0.1,tu-ip-produccion
```

### **Paso 3: Conectar Bot al Inbox WhatsApp**

1. **Ir al inbox de WhatsApp** en Chatwoot
2. **En Bot Configuration** seleccionar el bot creado
3. **Guardar configuración**

### **Paso 4: Instalar Dependencias**

```bash
pip install -r requirements.txt
```

### **Paso 5: Iniciar el Servicio**

```bash
# Opción 1: Solo WhatsApp bot (recomendado para testing)
python start_whatsapp.py

# Opción 2: Servicio combinado (voice + WhatsApp)
python webhook_receiver.py
```

---

## 🔧 URLs y Endpoints

### **Endpoints Principales**
- **WhatsApp Webhook:** `/webhooks/whatsapp/<token>`
- **Voice Webhook:** `/webhooks/chatwoot/<token>` (sin cambios)
- **Health Check General:** `/health`
- **Health Check WhatsApp:** `/health/whatsapp`

### **Endpoints Admin**
- **Métricas:** `/admin/whatsapp/metrics`
- **Cleanup:** `/admin/whatsapp/cleanup` (POST)
- **Estado Conversación:** `/admin/whatsapp/conversations/{id}`

---

## 📊 Monitoreo y Métricas

### **Health Check**
```bash
curl http://localhost:8000/health/whatsapp
```

### **Métricas Diarias**
```bash
curl http://localhost:8000/admin/whatsapp/metrics
```

### **Ejemplo de Respuesta de Métricas**
```json
{
  "daily_summary": {
    "total_conversations": 25,
    "meetings_scheduled": 8,
    "human_handoffs": 3,
    "conversion_rate": 32.0,
    "avg_response_time": 1.2
  },
  "conversation_analytics": {
    "top_intents": [
      ["ai_solution_inquiry", 15],
      ["schedule_meeting", 8],
      ["pricing_inquiry", 5]
    ]
  }
}
```

---

## 🔒 Seguridad

### **Validaciones Implementadas**
- ✅ **Token-based authentication** (único método disponible en Chatwoot)
- ✅ **Rate limiting** por IP (60 req/min)
- ✅ **Deduplicación** de mensajes (Chatwoot reenvía hasta 3x)
- ✅ **IP whitelisting** (opcional)
- ✅ **Prevención de loops** del bot

### **WhatsApp Compliance**
- ✅ **Rate limiting** por usuario (6s entre mensajes)
- ✅ **Límite de caracteres** (1000 max)
- ✅ **No datos sensibles** en emojis
- ✅ **Typing indicators** para UX

---

## 🛠️ Troubleshooting

### **Problema: Bot no responde**
1. Verificar `WHATSAPP_BOT_ENABLED=true`
2. Verificar que el bot está conectado al inbox en Chatwoot
3. Verificar que la conversación está en estado `pending`
4. Revisar logs: `curl http://localhost:8000/health/whatsapp`

### **Problema: Error de configuración**
1. Verificar todas las variables de entorno
2. Verificar que el `CHATWOOT_BOT_AGENT_ID` corresponde al bot creado
3. Verificar que el `CHATWOOT_WHATSAPP_INBOX_ID` es correcto

### **Problema: Rate limiting**
1. Verificar que no hay múltiples instancias enviando mensajes
2. Ajustar `WHATSAPP_RATE_LIMIT_SECONDS` si es necesario
3. Revisar métricas de performance

### **Logs Importantes**
```bash
# Ver logs del servicio
tail -f /var/log/whatsapp-bot.log

# Ver health status
curl http://localhost:8000/health/whatsapp

# Limpiar bots inactivos
curl -X POST http://localhost:8000/admin/whatsapp/cleanup
```

---

## 📋 Checklist de Deployment

### **Pre-deployment**
- [ ] WhatsApp Business API configurado en Chatwoot
- [ ] Bot creado en Chatwoot dashboard
- [ ] Variables de entorno configuradas
- [ ] Dependencias instaladas
- [ ] Health check funciona en staging

### **Deployment**
- [ ] Servicio iniciado correctamente
- [ ] Webhook URL configurada en Chatwoot
- [ ] Bot conectado al inbox WhatsApp
- [ ] Test de mensaje funciona

### **Post-deployment**
- [ ] Métricas funcionando
- [ ] Logs sin errores
- [ ] Rate limiting funcionando
- [ ] Handoff a humano funciona
- [ ] Agendamiento de reuniones funciona

---

## 🔄 Integración con Sistema Existente

### **Reutilización de Componentes**
- **✅ `microsoft_graph_client.py`** - Agendamiento de reuniones
- **✅ `chatwoot_summary_integration.py`** - Resúmenes de conversación  
- **✅ Variables de entorno voice** - Mantenidas sin cambios
- **✅ `webhook_receiver.py`** - Extendido, no modificado

### **Separación Garantizada**
- **❌ `agent.py`** - Nunca tocado
- **❌ Sistema LiveKit** - Completamente separado
- **❌ Flujo de voz** - Sin modificaciones

---

## 📈 Métricas de Éxito

### **KPIs Principales**
- **Conversion Rate:** % de conversaciones que resultan en reunión agendada
- **Response Time:** Tiempo promedio de respuesta del bot
- **Handoff Rate:** % de conversaciones transferidas a humano
- **User Satisfaction:** Feedback positivo vs negativo

### **Alertas Recomendadas**
- Error rate > 5%
- Response time > 3 segundos
- Conversion rate < 20%
- Rate limiting triggered

---

## 🆘 Soporte

### **Información de Debug**
Incluir siempre en reportes de issues:
1. Output de `/health/whatsapp`
2. Variables de entorno (sin tokens)
3. Logs de error específicos
4. Conversation ID problemático
5. Timestamp del problema

### **Contacto**
Para soporte técnico, incluir toda la información de debug arriba.

---

**🎉 ¡El sistema WhatsApp está listo para producción!**