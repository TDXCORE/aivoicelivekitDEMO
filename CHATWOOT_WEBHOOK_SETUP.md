# 🔗 Configuración de Webhook Chatwoot → Agente de Voz

## 📋 Resumen
Esta guía te ayudará a configurar el webhook de Chatwoot para que dispare automáticamente llamadas salientes cuando se cree un nuevo contacto desde tu landing page.

## 🚀 Pasos de Configuración

### 1. Configurar Variables de Entorno

Agrega estas variables a tu archivo `.env.local`:

```bash
# Webhook Configuration
CHATWOOT_WEBHOOK_TOKEN="tu-token-seguro-aqui-cambiar"
WEBHOOK_PORT=8000
WEBHOOK_HOST=0.0.0.0

# Existing LiveKit variables (keep as they are)
LIVEKIT_URL=your_existing_url
LIVEKIT_API_KEY=your_existing_key
LIVEKIT_API_SECRET=your_existing_secret
```

### 2. Iniciar el Servidor de Webhooks

```bash
# Instalar dependencias nuevas
pip install -r requirements.txt

# Iniciar el webhook receiver
python webhook_receiver.py
```

El servidor estará disponible en: `http://localhost:8000`

### 3. Configurar Webhook en Chatwoot

#### Paso a Paso:

1. **Accede a tu panel de Chatwoot**
   - Inicia sesión en tu cuenta de Chatwoot
   - Ve a **Settings** (Configuración)

2. **Navegar a Webhooks**
   - En el menú lateral, busca **Integrations** 
   - Selecciona **Webhooks**
   - Haz clic en **Add new webhook**

3. **Configurar el Webhook**
   
   **Webhook URL:**
   ```
   https://tu-dominio.com/webhooks/chatwoot
   ```
   
   > ⚠️ **Importante**: Reemplaza `tu-dominio.com` con tu dominio real donde está desplegado el webhook receiver
   
   **Para desarrollo local con ngrok:**
   ```
   https://abc123.ngrok.io/webhooks/chatwoot
   ```

4. **Seleccionar Eventos**
   
   Marca **SOLO** este evento:
   - ✅ **Contact created (contact_created)**
   
   > 📝 **No marques otros eventos** para evitar llamadas no deseadas

5. **Configurar Headers de Autenticación**
   
   En la sección de Headers (si está disponible), agrega:
   ```
   Authorization: Bearer tu-token-seguro-aqui-cambiar
   ```
   
   > ⚠️ **Importante**: Usa el mismo token que configuraste en `CHATWOOT_WEBHOOK_TOKEN`

6. **Guardar Webhook**
   - Haz clic en **Save** o **Create Webhook**
   - Verifica que aparezca en la lista de webhooks activos

### 4. Configurar Landing Page para Enviar custom_attributes

Cuando crees contactos desde tu landing page, asegúrate de enviar:

```javascript
// Ejemplo para JavaScript/API
const contactData = {
  name: "Ana Ortiz",
  email: "ana@example.com", // Opcional
  phone_number: "+573001234567", // Requerido
  custom_attributes: {
    source: "landing_page"  // CRÍTICO: Debe ser exactamente "landing_page"
  }
};
```

```python
# Ejemplo para Python/API
import requests

contact_data = {
    "name": "Ana Ortiz",
    "email": "ana@example.com",  # Opcional
    "phone_number": "+573001234567",  # Requerido
    "custom_attributes": {
        "source": "landing_page"  # CRÍTICO
    }
}

response = requests.post(
    "https://app.chatwoot.com/api/v1/accounts/{account_id}/contacts",
    headers={"api_access_token": "tu_api_token"},
    json=contact_data
)
```

## 🔧 Configuración de Producción

### 1. Deploy del Webhook Receiver

**Opción A: Render/Railway/Vercel**
```bash
# En tu Dockerfile o startup script
python webhook_receiver.py
```

**Opción B: Usar Gunicorn (Recomendado)**
```bash
# Instalar gunicorn
pip install gunicorn

# Ejecutar en producción
gunicorn webhook_receiver:app -w 4 -k uvicorn.workers.UvicornWorker --bind 0.0.0.0:8000
```

### 2. Variables de Entorno en Producción

```bash
CHATWOOT_WEBHOOK_TOKEN="production-secure-token-123"
WEBHOOK_PORT=8000
WEBHOOK_HOST=0.0.0.0
```

### 3. Configurar HTTPS y Dominio

El webhook receiver debe estar disponible en una URL pública con HTTPS:
```
https://tu-app.render.com/webhooks/chatwoot
https://tu-app.railway.app/webhooks/chatwoot
https://tu-dominio.com/webhooks/chatwoot
```

## 🧪 Testear la Integración

### 1. Verificar que el Webhook Receiver está Funcionando

```bash
# Test de salud
curl https://tu-dominio.com/health

# Debería retornar:
{
  "status": "healthy",
  "timestamp": "2024-01-15T10:30:00"
}
```

### 2. Crear Contacto de Prueba

Desde Chatwoot o tu API, crea un contacto con:
- `custom_attributes.source = "landing_page"`
- `phone_number` válido
- `name` del contacto

### 3. Verificar Logs

```bash
# En tu servidor
tail -f webhook_receiver.log

# Deberías ver:
[INFO] Received webhook: contact_created
[INFO] Processing contact: Ana Ortiz (+573001234567)
[INFO] Has email: True
```

## 🚨 Troubleshooting

### Webhook No Se Dispara
1. ✅ Verificar que el evento `contact_created` esté marcado
2. ✅ Confirmar que la URL del webhook sea correcta y accesible
3. ✅ Verificar que `custom_attributes.source = "landing_page"`

### Error 401 - Unauthorized
1. ✅ Verificar que el token `CHATWOOT_WEBHOOK_TOKEN` sea correcto
2. ✅ Confirmar que el header `Authorization: Bearer TOKEN` esté configurado

### Llamada No Se Crea
1. ✅ Verificar que el `phone_number` esté en formato internacional (+573001234567)
2. ✅ Confirmar que las variables LiveKit estén configuradas correctamente
3. ✅ Verificar logs del agente de voz

### Webhook Receiver No Responde
1. ✅ Verificar que el puerto 8000 esté disponible
2. ✅ Confirmar que el servidor esté ejecutándose
3. ✅ Verificar firewall y configuración de red

## 📊 Monitoreo

### Endpoints de Monitoreo
- `GET /health` - Estado del servidor
- `GET /` - Información del servicio

### Logs Importantes
```bash
# Webhook recibido
[INFO] Received webhook: contact_created

# Contacto procesado
[INFO] Processing contact: Ana Ortiz (+573001234567)

# Llamada creada
[INFO] ✅ Dispatch creado desde webhook!
```

## 🔄 Flujo Completo

1. **Usuario llena formulario** en landing page
2. **Landing page crea contacto** en Chatwoot con `custom_attributes.source: "landing_page"`
3. **Chatwoot dispara webhook** `contact_created`
4. **Webhook receiver valida** y extrae datos del contacto
5. **Se crea llamada saliente** automáticamente
6. **Agente de voz llama** al cliente con personalización
7. **Agente agenda reunión** usando email del webhook (si está disponible)

## 📞 Soporte

Si tienes problemas con la configuración:
1. Verifica los logs del webhook receiver
2. Confirma que todas las variables de entorno estén configuradas
3. Testea la conectividad del webhook con herramientas como Postman

---

**¡La integración está lista!** 🎉

Cada nuevo contacto de tu landing page ahora disparará automáticamente una llamada personalizada del agente de voz TDX.