# 🚀 Deployment en Render - TDX Chatbot Testing

## 📋 Opciones de Deployment

### **OPCIÓN 1: Servicio Separado (RECOMENDADO)**
Deploy independiente solo para testing - Mayor control y seguridad

### **OPCIÓN 2: Servicio Integrado**
Agregar endpoints de testing al servicio de producción existente

---

## 🎯 OPCIÓN 1: Servicio Separado (RECOMENDADO)

### **1. Crear Nuevo Servicio en Render**

1. **Login en Render Dashboard**
   - Ir a [render.com](https://render.com)
   - Conectar con GitHub/GitLab

2. **Crear Web Service**
   - Click "New +" → "Web Service"
   - Conectar repositorio: `aivoicelivekitDEMO`
   - Branch: `main`

3. **Configuración del Servicio**
   ```
   Name: aivoicelivekitdemo-testing
   Environment: Python
   Build Command: (usar del render.yaml)
   Start Command: python main_test.py
   ```

### **2. Configurar Variables de Entorno**

#### **Variables Obligatorias**
```env
RENDER=production
TESTING_ENABLED=true
OPENAI_API_KEY=tu_openai_api_key
VITE_CHATWOOT_ACCOUNT_ID=tu_chatwoot_account_id
VITE_CHATWOOT_API_TOKEN=tu_chatwoot_api_token
```

#### **Variables Opcionales**
```env
VITE_CHATWOOT_INBOX_ID=tu_inbox_id
MICROSOFT_GRAPH_CLIENT_ID=tu_graph_client_id
MICROSOFT_GRAPH_CLIENT_SECRET=tu_graph_secret
MICROSOFT_GRAPH_TENANT_ID=tu_tenant_id
USER_EMAIL=ventas@tdxcore.com
```

### **3. Deployment Automático**

#### **Opción A: Usar render-testing.yaml**
```bash
# En Render Dashboard, usar archivo de configuración
Build Command: Usar render-testing.yaml
```

#### **Opción B: Configuración Manual**
```
Build Command:
pip install --upgrade pip
pip install -r requirements.txt
python -c "import testing; print('✅ Testing module verified')"

Start Command:
python main_test.py
```

### **4. URLs Resultantes**
```
Production: https://aivoicelivekitdemo.onrender.com
Testing:    https://aivoicelivekitdemo-testing.onrender.com
```

---

## 🔧 OPCIÓN 2: Servicio Integrado

### **1. Modificar Servicio Existente**

#### **Actualizar startup.py**
```python
# Agregar al final de startup.py
def start_testing_server():
    testing_enabled = os.getenv('TESTING_ENABLED', 'false').lower() == 'true'
    if testing_enabled:
        from main_test import app as test_app
        # Montar rutas de testing
        main_app.mount("/test", test_app)
```

#### **Agregar Variable de Entorno**
```env
TESTING_ENABLED=true
```

### **2. URLs Integradas**
```
Production: https://aivoicelivekitdemo.onrender.com/
Testing:    https://aivoicelivekitdemo.onrender.com/test/
API:        https://aivoicelivekitdemo.onrender.com/api/test/
```

---

## ⚙️ Configuración Avanzada

### **Health Checks**
```yaml
healthCheckPath: /api/test/health
```

### **Scaling Configuration**
```yaml
plan: starter  # Para testing básico
# plan: standard  # Para testing intensivo
```

### **Environment Detection**
El sistema detecta automáticamente el entorno:
```python
is_render = os.getenv("RENDER") == "production"
```

### **CORS Automático**
- **Desarrollo**: Permisivo (`allow_origins=["*"]`)
- **Producción**: Restringido a dominios Render

---

## 🔒 Configuración de Seguridad

### **Variables Sensibles**
```env
# Usar "Environment Variables" en Render Dashboard
OPENAI_API_KEY=secret
VITE_CHATWOOT_API_TOKEN=secret
MICROSOFT_GRAPH_CLIENT_SECRET=secret
```

### **CORS Producción**
```python
allowed_origins = [
    "https://aivoicelivekitdemo-testing.onrender.com",
    "https://*.onrender.com"
]
```

---

## 📊 Monitoreo y Logs

### **Health Checks Disponibles**
```
GET /api/test/health       - Health check básico
GET /api/test/status       - Estado detallado
GET /health               - Health check general
```

### **Logs en Tiempo Real**
```bash
# En Render Dashboard > Service > Logs
# Logs estructurados con timestamps
```

### **Métricas**
```
GET /api/test/debug/agent-state  - Estado del agente
GET /api/test/debug/export       - Exportar datos
```

---

## 🚀 Proceso de Deploy Paso a Paso

### **Deploy Rápido (5 minutos)**

1. **Fork/Clone Repository**
   ```bash
   git clone tu-repo
   cd aivoicelivekitDEMO
   ```

2. **Render Dashboard**
   - New Web Service
   - Connect Repository
   - Name: `aivoicelivekitdemo-testing`

3. **Configuración**
   - Build Command: `pip install -r requirements.txt`
   - Start Command: `python main_test.py`

4. **Environment Variables**
   - `RENDER=production`
   - `OPENAI_API_KEY=tu_key`
   - `VITE_CHATWOOT_ACCOUNT_ID=tu_account`

5. **Deploy**
   - Click "Create Web Service"
   - Esperar build completo
   - Verificar URL funcionando

### **Verificación Post-Deploy**

1. **Health Check**
   ```bash
   curl https://aivoicelivekitdemo-testing.onrender.com/api/test/health
   ```

2. **Frontend**
   ```
   https://aivoicelivekitdemo-testing.onrender.com/
   ```

3. **API Docs**
   ```
   https://aivoicelivekitdemo-testing.onrender.com/docs
   ```

---

## 🐛 Troubleshooting

### **Errores Comunes**

#### **"Module testing not found"**
```bash
# Verificar que testing/ esté en el repositorio
# Verificar buildCommand incluye verificación
```

#### **"Port already in use"**
```bash
# Verificar que RENDER=production esté configurado
# Render asigna puerto automáticamente
```

#### **"CORS Error"**
```bash
# Verificar CORS configuration en main_test.py
# Agregar dominio a allowed_origins si es necesario
```

#### **"OpenAI API Key not found"**
```bash
# Configurar OPENAI_API_KEY en Environment Variables
# Verificar que el key sea válido
```

### **Logs Útiles**
```bash
# Ver logs de startup
2024-XX-XX INFO: 🌍 Environment: Render Production
2024-XX-XX INFO: 🧪 Starting test server on 0.0.0.0:XXXX
2024-XX-XX INFO: 🔒 CORS configured for production
```

---

## 📈 Optimización

### **Performance**
- Plan Starter es suficiente para testing
- Auto-scaling basado en demanda
- Logs automáticos para debugging

### **Costo**
- Plan Starter: $7/mes
- Sleep automático si no hay uso
- Ideal para testing y desarrollo

### **Backup**
- Código en Git (backup automático)
- Logs en Render (7 días retención)
- Exportación de datos via API

---

## ✅ Checklist Final

- [ ] Servicio creado en Render
- [ ] Variables de entorno configuradas
- [ ] Build exitoso
- [ ] Health check funcionando
- [ ] Frontend accesible
- [ ] API endpoints respondiendo
- [ ] Logs visibles en dashboard
- [ ] CORS configurado correctamente
- [ ] Testing completo del chatbot

**🎉 ¡Listo para usar en producción!**