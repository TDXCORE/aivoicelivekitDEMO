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

## Fase 6: Optimización de Conversación Fluida
### 6.1 Estado Actual Completado ✅
- [X] Bot funcional para inbound y outbound calls
- [X] Script SDR completo con Laura (prospección, BANT, agendamiento)
- [X] Configuración básica OpenAI Realtime API
- [X] Deploy productivo en Render

### 6.2 Problema Identificado 🔍
- **Latencia de Interrupción**: El bot se demora en responder cuando el usuario interrumpe
- **Causa**: Configuración básica sin optimización de turn detection
- **Impacto**: Conversación menos natural, frustración del usuario

### 6.3 Plan de Optimización (Step-by-Step)

#### **Opción 1: Semantic VAD Conservador** [SIGUIENTE]
- [ ] **Objetivo**: Reducir 30-40% latencia de interrupción
- [ ] **Riesgo**: Bajo (configuración estándar)
- [ ] **Implementación**:
  ```python
  turn_detection=openai.realtime.TurnDetection(
      type="semantic_vad",
      eagerness="medium",
      create_response=True,
      interrupt_response=True
  )
  ```
- [ ] **Pruebas**: Llamadas inbound y outbound
- [ ] **Validación**: Verificar que no se rompa funcionalidad existente

#### **Opción 2: Semantic VAD Agresivo** [FUTURO]
- [ ] **Objetivo**: Máxima reducción de latencia
- [ ] **Riesgo**: Medio (respuestas más rápidas pero posibles interrupciones)
- [ ] **Implementación**:
  ```python
  turn_detection=openai.realtime.TurnDetection(
      type="semantic_vad",
      eagerness="high",
      create_response=True,
      interrupt_response=True
  )
  ```
- [ ] **Condición**: Solo si Opción 1 funciona bien

#### **Opción 3: LiveKit Turn Detector Avanzado** [AVANZADO]
- [ ] **Objetivo**: Máximo control con modelo custom de 135M parámetros
- [ ] **Riesgo**: Alto (requiere import adicional)
- [ ] **Implementación**:
  ```python
  from livekit.plugins import turn_detector
  turn_detection=turn_detector.MultilingualModel(
      min_endpointing_delay=0.3,
      max_endpointing_delay=2.0
  )
  ```
- [ ] **Condición**: Solo si Opciones 1-2 no son suficientes

#### **Optimizaciones Adicionales de Bajo Riesgo**
- [ ] **Reducir tiempo inicialización**: `await asyncio.sleep(1)` en lugar de 2s
- [ ] **Optimizar voz para español**: `voice="echo"` en lugar de "alloy"
- [ ] **Ajustar temperature**: `temperature=0.8` para más naturalidad
- [ ] **Monitoreo**: Agregar métricas de latencia de respuesta

### 6.4 Metodología de Testing
- [ ] **Baseline**: Medir latencia actual de interrupción
- [ ] **A/B Testing**: Probar configuración antes/después
- [ ] **Casos de prueba**:
  - Interrupciones durante saludo inicial
  - Interrupciones durante preguntas BANT
  - Interrupciones durante propuesta de valor
  - Llamadas con ruido de fondo
- [ ] **Métricas**:
  - Tiempo de respuesta a interrupción (ms)
  - Tasa de interrupciones falsas
  - Calidad percibida de conversación
  - Funcionalidad SDR intacta

### 6.5 Rollback Plan
- [ ] **Git tags** antes de cada cambio
- [ ] **Configuración feature flag** para revertir rápidamente
- [ ] **Monitoreo continuo** de errores en producción
- [ ] **Testing pipeline** automatizado

### 6.6 Análisis de Costos y Rendimiento
- [ ] Monitorear uso de minutos LiveKit
- [ ] Calcular ancho de banda consumido
- [ ] Analizar costos Twilio Voice
- [ ] Proyecciones para 100 llamadas/día x 3min

### 6.7 Integraciones CRM (Post-Optimización)
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