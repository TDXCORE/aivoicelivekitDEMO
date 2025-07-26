# 🧪 GUÍA DE TESTING - HOMOLOGACIÓN DE BOTS TDX

## 🎯 **OBJETIVO DEL TESTING**

Validar que el chatbot de WhatsApp se comporta **exactamente igual** al bot de llamadas de voz, con las mismas funciones, personalidad y efectividad.

---

## ✅ **CHECKLIST DE VALIDACIÓN FUNCIONAL**

### **1. FUNCIÓN QUALIFY_PROSPECT ⭐ CRÍTICO**

**Test 1: Calificación BANT Básica**
```
Input: Presupuesto 100k+, Decision Maker, Urgencia Alta, Timeline Inmediato
Expected: Score 100, Qualified = true, Recomendación = schedule_meeting
```

**Test 2: Calificación BANT Límite**
```
Input: Presupuesto 10k-50k, Influencer, Urgencia Media, Timeline 6 meses
Expected: Score 60, Qualified = true, Recomendación = schedule_meeting
```

**Test 3: Calificación BANT Baja**
```
Input: Sin presupuesto, User, Urgencia Baja, Timeline 12+ meses
Expected: Score 0, Qualified = false, Recomendación = nurture_lead
```

### **2. KEYWORDS DE TRANSFERENCIA AUTOMÁTICA ⭐ CRÍTICO**

**Test Keywords:**
- "Quiero hablar con un ejecutivo" → Transferencia inmediata
- "Me conecta con un vendedor" → Transferencia inmediata  
- "Necesito un humano" → Transferencia inmediata
- "Transferir a especialista" → Transferencia inmediata

**Verificar:**
- [ ] No pregunta confirmación
- [ ] Transferencia inmediata
- [ ] Mensaje de transferencia apropiado
- [ ] Log de keyword detectada

### **3. PERSONALIDAD AGRESIVA DE VENTAS ⭐ CRÍTICO**

**Test Comportamiento:**
- [ ] Saludo entusiasmado y directo
- [ ] Máximo 3 intercambios antes de calificar/transferir
- [ ] Mensajes cortos (< 500 caracteres)
- [ ] Quick replies agresivos
- [ ] No explicaciones largas de servicios

### **4. FUNCIONES COMPARTIDAS (DEBEN SEGUIR FUNCIONANDO)**

**Test schedule_meeting_whatsapp:**
- [ ] Usa Microsoft Graph API correctamente
- [ ] Crea reunión con invitación de Teams
- [ ] Maneja emails del webhook y conversación
- [ ] Formato de respuesta correcto

**Test check_availability_whatsapp:**
- [ ] Consulta calendario via Microsoft Graph
- [ ] Ofrece exactamente 3 opciones
- [ ] Formato de fecha/hora correcto
- [ ] Fallback si API falla

**Test transfer_to_human_whatsapp:**
- [ ] Cambia estado en Chatwoot
- [ ] Crea resumen para agente humano
- [ ] Mensaje de transferencia apropiado

**Test collect_email_whatsapp:**
- [ ] Validación de formato de email
- [ ] Actualiza prospect_info
- [ ] Manejo de emails inválidos

---

## 🔄 **TESTING DEL FALLBACK TELNYX → WHATSAPP**

### **Configuración de Testing**
```bash
# Variables requeridas para testing
TELNYX_CALL_TIMEOUT_SECONDS=5  # Reducir para testing rápido
WHATSAPP_FALLBACK_ENABLED=true
CHATWOOT_WHATSAPP_INBOX_ID=your_inbox_id
```

### **Test Cases Fallback:**

**Test 1: Timeout de Llamada**
1. Crear contacto en Chatwoot desde landing page
2. Verificar que llamada Telnyx se inicia
3. Esperar 5 segundos (timeout)
4. Verificar que WhatsApp fallback se activa automáticamente
5. Verificar mensaje inicial en WhatsApp

**Test 2: Error de Llamada**
1. Configurar Telnyx con credenciales incorrectas
2. Crear contacto en Chatwoot
3. Verificar que WhatsApp fallback se activa inmediatamente
4. Verificar mensaje de error técnico apropiado

**Test 3: Fallback de Llamada No Contestada**
1. Crear contacto con número que no contesta
2. Verificar llamada Telnyx
3. Esperar timeout configurado
4. Verificar mensaje WhatsApp "Te llamé hace un momento"

---

## 🌐 **ENDPOINTS DE TESTING**

### **Health Checks**
```bash
# Health check general
curl http://localhost:8000/health

# Health check WhatsApp específico
curl http://localhost:8000/health/whatsapp

# Health check Telnyx específico  
curl http://localhost:8000/health/telnyx
```

### **Métricas y Monitoreo**
```bash
# Métricas WhatsApp
curl http://localhost:8000/admin/whatsapp/metrics

# Estado de conversación específica
curl http://localhost:8000/admin/whatsapp/conversations/{conversation_id}

# Cleanup de bots inactivos
curl -X POST http://localhost:8000/admin/whatsapp/cleanup
```

---

## 📊 **MÉTRICAS DE ÉXITO**

### **KPIs Objetivo:**
- **Conversion Rate WhatsApp ≥ Conversion Rate Voice** (±5%)
- **Tiempo promedio conversación < 3 minutos**
- **Rate de transferencia similar** al bot de voz
- **Calificación BANT exitosa >80%** de casos
- **Fallback WhatsApp activation rate >95%** cuando voz falla

### **Métricas Técnicas:**
- **Response time < 3 segundos** promedio
- **Rate limiting respetado** (3s entre mensajes)
- **Error rate < 5%** en function calls
- **Syntax compilation success** 100%

---

## 🔧 **DEBUGGING Y TROUBLESHOOTING**

### **Logs Importantes**
```bash
# Logs de calificación
grep "qualifying WhatsApp prospect" /var/log/webhook_receiver.log

# Logs de transferencia automática
grep "AUTOMATIC TRANSFER triggered" /var/log/webhook_receiver.log

# Logs de fallback
grep "WhatsApp fallback" /var/log/webhook_receiver.log

# Logs de function calls
grep "WhatsApp bot calling function" /var/log/webhook_receiver.log
```

### **Problemas Comunes**

**Problema: qualify_prospect_whatsapp no se ejecuta**
- Verificar que está en tools list
- Verificar function call handling
- Verificar parámetros requeridos

**Problema: Keywords no disparan transferencia**
- Verificar check_automatic_transfer_keywords
- Verificar case sensitivity
- Verificar que la función se llama antes de generate_response

**Problema: Fallback no funciona**
- Verificar WHATSAPP_FALLBACK_ENABLED=true
- Verificar credenciales Chatwoot
- Verificar CHATWOOT_WHATSAPP_INBOX_ID

**Problema: Personalidad no es agresiva**
- Verificar system_prompt en build_conversation_context
- Verificar max_tokens en OpenAI call
- Verificar que no hay override en quick replies

---

## 🚀 **SECUENCIA DE TESTING RECOMENDADA**

### **Fase 1: Testing Básico (30 min)**
1. ✅ Compilation syntax check
2. ✅ Health checks endpoints
3. ✅ Función qualify_prospect con casos básicos
4. ✅ Keywords de transferencia automática

### **Fase 2: Testing Integración (45 min)**
5. ✅ Schedule meeting completo
6. ✅ Check availability
7. ✅ Collect email
8. ✅ Transfer to human

### **Fase 3: Testing Fallback (30 min)**
9. ✅ Telnyx timeout → WhatsApp
10. ✅ Telnyx error → WhatsApp
11. ✅ Conversación completa WhatsApp fallback

### **Fase 4: Testing Personalidad (45 min)**
12. ✅ Conversación agresiva completa
13. ✅ Flujo ultra-directo (máx 3 intercambios)
14. ✅ Comparación side-by-side con bot de voz

---

## 📋 **RESULTADO ESPERADO**

Al final del testing, deberías tener:

✅ **ChatBot WhatsApp funcionalmente idéntico al bot de voz**
✅ **Misma agresividad comercial y personalidad**
✅ **Todas las herramientas BANT implementadas**
✅ **Fallback automático Telnyx → WhatsApp funcionando**
✅ **Integración Chatwoot mantenida sin disrupciones**
✅ **Métricas y logging homologados**
✅ **Backward compatibility 100% garantizada**

🎯 **OBJETIVO FINAL ALCANZADO:** Sistema dual voz + WhatsApp con homologación completa y fallback inteligente.