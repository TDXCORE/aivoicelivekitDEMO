# 🚀 Guía de Deployment en Render - TDX SDR Bot

## Paso 1: Crear repositorio en GitHub

### Opción A: Nuevo repositorio (Recomendado)
1. Ir a [GitHub](https://github.com) → **New Repository**
2. Nombre: `tdx-sdr-bot`
3. Descripción: `AI-powered SDR bot for TDX with LiveKit and OpenAI Realtime API`
4. Visibilidad: **Private** (para proteger credenciales)
5. No inicializar con README (ya tenemos código)

### Opción B: Fork del repositorio existente
1. Hacer fork de `livekit-examples/outbound-caller-python`
2. Renombrar a `tdx-sdr-bot`

## Paso 2: Subir código a tu repositorio

```bash
# Cambiar remote al tu nuevo repositorio
git remote set-url origin https://github.com/TU-USUARIO/tdx-sdr-bot.git

# Push del código
git push -u origin main
```

## Paso 3: Configurar Render

### En Render Dashboard:

1. **New** → **Web Service**
2. **Connect a repository** → Seleccionar `TU-USUARIO/tdx-sdr-bot`

### Configuración del servicio:

```yaml
Name: tdx-sdr-bot
Environment: Docker
Region: Oregon (US West)
Branch: main
```

### Docker Settings:

```yaml
Dockerfile Path: ./Dockerfile
Build Context: . 
Docker Command: (dejar vacío)
```

### Advanced Settings:

```yaml
Plan: Starter ($7/mes)
Auto-Deploy: Yes
Health Check Path: /health (opcional)
```

## Paso 4: Variables de entorno

Agregar en **Environment**:

### 📡 LiveKit (OBLIGATORIAS)
```bash
LIVEKIT_URL=wss://tu-subdominio.livekit.cloud
LIVEKIT_API_KEY=LKSA_xxxxxxxxxx
LIVEKIT_API_SECRET=xxxxxxxxxxxxxx
```

### 🤖 OpenAI (OBLIGATORIA)
```bash
OPENAI_API_KEY=sk-xxxxxxxxxxxxxxxxx
```

### ☎️ SIP Telephony (OBLIGATORIAS)
```bash
SIP_OUTBOUND_TRUNK_ID=ST_62xof5EmFyRe
TDX_PHONE_NUMBER=+18632190153
SENIOR_SDR_PHONE=+1234567890
```

### 📅 MS Teams (OPCIONALES para testing)
```bash
MICROSOFT_GRAPH_CLIENT_ID=xxxxxxxxx
MICROSOFT_GRAPH_CLIENT_SECRET=xxxxxxxxx
MICROSOFT_GRAPH_TENANT_ID=xxxxxxxxx
```

### ⚙️ System (AUTO-CONFIGURADAS)
```bash
PYTHONUNBUFFERED=1
PORT=8000
```

## Paso 5: Deploy y verificación

1. **Deploy** automático se iniciará
2. **Verificar logs** en tiempo real
3. **Confirmar** que aparece: `"connecting to room"` 
4. **Test** con llamada al número TDX

## ⚠️ Troubleshooting común

### Error: "No module named 'sip_utils'"
- **Causa**: Build context incorrecto
- **Solución**: Build Context = `.` (raíz del repo)

### Error: "LIVEKIT_API_KEY not found"
- **Causa**: Variables de entorno no configuradas
- **Solución**: Verificar Environment variables en Render

### Error: "Port binding failed"
- **Causa**: Puerto incorrecto
- **Solución**: Render usa variable PORT automática

### Build timeout
- **Causa**: Dependencias pesadas
- **Solución**: Usar plan Standard temporalmente

## 📊 Monitoreo post-deployment

### Logs a verificar:
```bash
✅ "SIP Config initialized"
✅ "Teams integration ready" 
✅ "Agent ready for calls"
✅ "connecting to room {room_name}"
```

### Métricas importantes:
- **Memory usage**: < 512MB (Starter plan)
- **Response time**: < 500ms
- **Error rate**: < 1%

### Test calls:
1. **Inbound**: Llamar al número TDX
2. **Qualification**: Probar flujo BANT
3. **Transfer**: Verificar transferencia a senior SDR
4. **Teams**: Confirmar agendamiento de reuniones

## 🔒 Seguridad post-deployment

### IP Whitelisting en Twilio:
```bash
# Obtener IP de Render
curl https://tu-app.onrender.com/ip

# Agregar a Twilio IP Access Control List
```

### Monitoring de logs:
- No secrets en logs ✅
- Rate limiting configurado ✅
- Error handling robusto ✅

## 📈 Scaling considerations

### Para > 20 llamadas concurrentes:
1. Upgrade a **Standard plan** ($25/mes)
2. Configurar **Auto-scaling**
3. Usar **Redis** para session management
4. Implementar **Load balancing**

### Costo proyectado (100 calls/día):
- **Render Standard**: $25/mes
- **LiveKit**: ~$8/mes (270 minutos)
- **OpenAI Realtime**: ~$810/mes (270 minutos)
- **Total**: ~$843/mes

---

## ✅ Checklist final

- [ ] Repositorio GitHub creado y código subido
- [ ] Servicio Render configurado con Docker
- [ ] Variables de entorno configuradas
- [ ] Deploy exitoso sin errores
- [ ] Test call completado
- [ ] Logs mostrando funcionamiento correcto
- [ ] Documentación de credenciales guardada seguramente

**¡Tu TDX SDR Bot estará listo para recibir llamadas! 🎉**