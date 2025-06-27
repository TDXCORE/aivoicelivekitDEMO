# Configuración Dispatch Rule para TDX SDR Bot

## Problema Identificado
El dispatch rule `SDR_43NLS8ztrysm` no tiene agente asignado, por eso las llamadas entrantes no son procesadas.

## Configuración Requerida en LiveKit Cloud

### 1. Dispatch Rule - SDR_43NLS8ztrysm
```
Rule name: twilio-calls
Configured trunks: ST_62xof5EmFyRe  
Destination room: call-{participant.identity}
Agents: tdx-sdr-bot  ← AGREGAR ESTO
Rule type: Individual
```

### 2. Verificar que el Worker esté usando el nombre correcto
En `agent.py` línea 267:
```python
cli.run_app(
    WorkerOptions(
        entrypoint_fnc=entrypoint,
        agent_name="tdx-sdr-bot",  ← Debe coincidir con dispatch rule
    )
)
```

### 3. Pasos para Corregir

1. **En LiveKit Cloud Dashboard:**
   - Ve a SIP → Dispatch rules
   - Edita el rule `SDR_43NLS8ztrysm`
   - En el campo "Agents" agrega: `tdx-sdr-bot`
   - Guarda los cambios

2. **Verificar Variables de Entorno en Render:**
   - LIVEKIT_URL: `wss://forceapp-jaadrt7a.livekit.cloud`
   - LIVEKIT_API_KEY: (tu clave)
   - LIVEKIT_API_SECRET: (tu secreto)
   - SIP_OUTBOUND_TRUNK_ID: `ST_G24Bo8JH4iy7`
   - OPENAI_API_KEY: (tu clave OpenAI)

3. **Reiniciar Worker en Render** después de cambios

### 4. Prueba Final
- Llamar a `+18632190153`
- El dispatch rule debería crear room `call-{phone_number}`
- El worker `tdx-sdr-bot` debería procesar automáticamente
- El bot debería contestar como SDR de TDX

## Diagnostic Commands
```bash
# Monitorear llamadas entrantes
python monitor_calls.py

# Verificar status del sistema
python check_worker_status.py
```