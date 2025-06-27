# Plan de Trabajo: Agente de Voz SDR con LiveKit + OpenAI + Twilio

## Resumen Ejecutivo
Desarrollo de un agente de voz SDR inteligente para TDX (empresa de tecnología e IA) utilizando LiveKit Agents 1.0, OpenAI Realtime API y Twilio, con deploy en Render.

## Objetivos
- Crear un voice bot SDR que prospecte y califique clientes potenciales
- Integrar funcionalidades de agendamiento en MS Teams
- Implementar sistema de reenvío/forward de llamadas
- Deploy serverless en Render con costos optimizados
- Configuración completa de telefonía via Twilio

---

## Fase 1: Configuración del Entorno
### 1.1 Instalación de Herramientas
- [X] Instalar `livekit-agents-cli`
- [X] Configurar entorno de desarrollo local
- [X] Verificar conectividad con servicios externos

---

## Fase 2: Bootstrap del Agente
### 2.1 Generación del Template
- [X] Ejecutar comando bootstrap:
  ```bash
  ./lk app create --template outbound-caller-python tdx-sdr-bot
  ```
- [X] Revisar estructura generada:
  - agent.py ✅
  - requirements.txt ✅
  - taskfile.yaml ✅
  - README.md ✅

### 2.2 Configuración del Agente Principal
- [X] Personalizar `agent.py` con:
  - Nombre del agente: "TDXSDRBot" ✅
  - System prompt específico para SDR de empresa de tecnología/IA ✅
  - Configuración OpenAI Realtime API ✅
  - Lógica de prospección y calificación BANT ✅
  - Funciones: schedule_meeting, qualify_prospect, transfer_call ✅
  - Sistema de reenvío de llamadas ✅
  - Dependencias MS Teams agregadas ✅

### 2.3 Dockerización
- [X] Crear Dockerfile optimizado para Python 3.12-slim ✅
- [X] Configurar requirements.txt con dependencias:
  - livekit-agents[openai,deepgram,cartesia,silero,turn_detector] ✅
  - microsoft-graph-python-sdk (para MS Teams) ✅
  - requests (para APIs de CRM/calendario) ✅
  - python-dotenv, livekit-plugins-noise-cancellation ✅
- [X] Crear Procfile para Render ✅
- [X] Crear .env.example con variables de configuración ✅

---

## Fase 3: Deploy y Configuración
### 3.1 Variables de Entorno en Render
- [X] Configurar variables requeridas:
  - LIVEKIT_API_KEY, LIVEKIT_API_SECRET, LIVEKIT_WS_URL ✅
  - OPENAI_API_KEY ✅
  - MICROSOFT_GRAPH_CLIENT_ID, CLIENT_SECRET, TENANT_ID ✅
  - SIP_OUTBOUND_TRUNK_ID ✅
  - CRM_API_KEY, FORWARD_PHONE_NUMBER (opcionales) ✅
- [X] Crear render.yaml con configuración automatizada ✅
- [X] Crear .env.example con todas las variables ✅

### 3.2 Deploy Inicial
- [X] Crear documentación completa de deployment ✅
- [X] Configurar .gitignore para seguridad ✅
- [X] Crear módulo MS Teams integration ✅
- [X] Preparar archivos para Render (Procfile, Dockerfile) ✅
- [X] Deploy exitoso en Render con variables de entorno ✅
- [X] Corregir descarga de modelos turn-detector ✅

---

## Fase 4: Integración Telefónica
### 4.1 Configuración SIP
- [X] Verificar configuración de SIP Ingress en LiveKit ✅
- [X] Comprobar dispatch rules existentes ✅
- [X] Validar routing call-{participant.identity} ✅
- [X] Crear documentación completa SIP_CONFIGURATION.md ✅
- [X] Configurar Twilio webhook y TwiML ✅

### 4.2 Flujo de Llamada
- [X] Documentar flujo end-to-end con diagrama Mermaid ✅
  - Caller → Twilio PSTN → LiveKit SIP → Room → Bot ✅
- [X] Configurar identity="bot" para participante ✅
- [X] Crear utilidades SIP (sip_utils.py) ✅
- [X] Integrar SIP config en agent.py ✅

---

## Fase 5: Pruebas y Validación
### 5.1 Pruebas Inbound
- [ ] Realizar llamada de prueba desde móvil
- [ ] Verificar respuesta del SDR bot
- [ ] Validar script de prospección
- [ ] Confirmar calidad de audio y latencia

### 5.2 Pruebas de Funcionalidades SDR
- [ ] Probar calificación de leads (BANT)
- [ ] Validar agendamiento en MS Teams
- [ ] Verificar funcionalidad de reenvío de llamadas
- [ ] Testear manejo de objeciones

### 5.3 Pruebas Outbound (Opcional)
- [ ] Implementar funcionalidad de llamadas salientes
- [ ] Configurar CallServiceClient para prospección
- [ ] Probar dial_out con trunk ST_G24Bo8JH4iy7

### 5.4 Testing de Flujos de Conversación
- [ ] Probar diferentes escenarios de prospección
- [ ] Validar transición entre calificación y agendamiento
- [ ] Verificar comportamiento con diferentes tipos de leads

---

## Fase 6: Optimización y Monitoreo
### 6.1 Análisis de Costos
- [ ] Monitorear uso de minutos LiveKit
- [ ] Calcular ancho de banda consumido
- [ ] Analizar costos Twilio Voice
- [ ] Proyecciones para 100 llamadas/día x 3min

### 6.2 Optimizaciones SDR
- [ ] Implementar guardrails específicos para SDR (max_tokens, timeouts)
- [ ] Optimizar prompts para prospección efectiva
- [ ] Configurar métricas de conversión (leads calificados/llamadas)
- [ ] Implementar sistema de escalamiento a humanos

### 6.3 Integraciones CRM
- [ ] Conectar con CRM via webhooks para registro de leads
- [ ] Implementar logging de conversaciones
- [ ] Configurar notificaciones de reuniones agendadas

---

## Entregables
1. **Código base funcional** con main.py configurado para SDR
2. **Dockerfile y archivos de deploy** listos para Render  
3. **Documentación de configuración** con variables de entorno
4. **Integración MS Teams** para agendamiento de reuniones
5. **Sistema de reenvío** de llamadas configurado
6. **Guía de pruebas** para validación end-to-end
7. **Scripts de prospección** y manejo de objeciones
8. **Análisis de costos** y proyecciones de escalabilidad

## Cronograma Estimado
- **Fase 1-2**: 2-3 días (incluyendo integraciones SDR)
- **Fase 3-4**: 1-2 días  
- **Fase 5**: 2 días (testing extenso de funcionalidades SDR)
- **Fase 6**: 2-3 días (optimizaciones y CRM)

**Total estimado**: 7-10 días de desarrollo

## Criterios de Éxito
- ✅ SDR bot califica leads efectivamente usando metodología BANT
- ✅ Agendamiento automático en MS Teams funcional
- ✅ Sistema de reenvío de llamadas operativo
- ✅ Latencia < 2 segundos en respuestas
- ✅ Calidad de audio profesional
- ✅ Integración CRM para tracking de leads
- ✅ Métricas de conversión > 15% (leads calificados/llamadas)
- ✅ Deploy estable en producción