from fastapi import Request, HTTPException
import os
import logging
from typing import Dict, Any, Set
from datetime import datetime, timedelta
import json

logger = logging.getLogger("whatsapp-security")

class WhatsAppWebhookSecurity:
    def __init__(self):
        self.webhook_token = os.getenv('CHATWOOT_WEBHOOK_TOKEN')
        self.allowed_ips = os.getenv('CHATWOOT_ALLOWED_IPS', '').split(',')
        
        # Deduplicación de mensajes (Chatwoot reenvía hasta 3 veces)
        self.processed_messages: Set[str] = set()
        self.message_cleanup_interval = timedelta(hours=1)
        self.last_cleanup = datetime.now()
        
        # Rate limiting por IP
        self.ip_requests: Dict[str, list] = {}
        self.max_requests_per_minute = 60
        
        # Validar configuración
        if not self.webhook_token:
            logger.error("CHATWOOT_WEBHOOK_TOKEN not configured")
            raise ValueError("WhatsApp webhook token not configured")
    
    def cleanup_old_messages(self):
        """Limpiar mensajes antiguos para evitar memory leak"""
        now = datetime.now()
        if now - self.last_cleanup > self.message_cleanup_interval:
            # En production usar Redis/DB para persistencia
            self.processed_messages.clear()
            self.last_cleanup = now
            logger.info("Cleaned up old processed messages")
    
    def is_duplicate_message(self, webhook_data: Dict[str, Any]) -> bool:
        """Prevenir duplicados por message_id"""
        message_id = webhook_data.get('id')
        conversation_id = webhook_data.get('conversation', {}).get('id')
        
        if not message_id or not conversation_id:
            return False
        
        # Crear clave única
        message_key = f"{conversation_id}:{message_id}"
        
        # Verificar si ya fue procesado
        if message_key in self.processed_messages:
            logger.info(f"Duplicate message detected: {message_key}")
            return True
        
        # Marcar como procesado
        self.processed_messages.add(message_key)
        self.cleanup_old_messages()
        
        return False
    
    def check_rate_limit(self, client_ip: str) -> bool:
        """Rate limiting por IP (60 req/min)"""
        now = datetime.now()
        minute_ago = now - timedelta(minutes=1)
        
        # Limpiar requests antiguos
        if client_ip in self.ip_requests:
            self.ip_requests[client_ip] = [
                req_time for req_time in self.ip_requests[client_ip] 
                if req_time > minute_ago
            ]
        else:
            self.ip_requests[client_ip] = []
        
        # Verificar límite
        if len(self.ip_requests[client_ip]) >= self.max_requests_per_minute:
            logger.warning(f"Rate limit exceeded for IP: {client_ip}")
            return False
        
        # Registrar request
        self.ip_requests[client_ip].append(now)
        return True
    
    async def validate_webhook(self, request: Request) -> Dict[str, Any]:
        """Validación completa con deduplicación"""
        
        # 1. Rate limiting por IP
        client_ip = request.client.host
        if not self.check_rate_limit(client_ip):
            logger.warning(f"Rate limit exceeded for IP: {client_ip}")
            raise HTTPException(status_code=429, detail="Rate limit exceeded")
        
        # 2. Token validation
        token = request.path_params.get('token')
        if not token or token != self.webhook_token:
            logger.warning(f"Invalid webhook token from IP: {client_ip}")
            raise HTTPException(status_code=401, detail="Invalid token")
        
        # 3. IP whitelist (opcional)
        if self.allowed_ips and self.allowed_ips[0] and self.allowed_ips[0].strip():
            if client_ip not in self.allowed_ips:
                logger.warning(f"IP not allowed: {client_ip}")
                raise HTTPException(status_code=403, detail="IP not allowed")
        
        # 4. Content type validation
        content_type = request.headers.get('content-type', '')
        if 'application/json' not in content_type:
            logger.warning(f"Invalid content type: {content_type}")
            raise HTTPException(status_code=400, detail="Invalid content type")
        
        # 5. Parse and validate payload
        try:
            webhook_data = await request.json()
            if not isinstance(webhook_data, dict) or 'event' not in webhook_data:
                logger.warning(f"Invalid payload structure from IP: {client_ip}")
                raise HTTPException(status_code=400, detail="Invalid payload structure")
        except json.JSONDecodeError as e:
            logger.error(f"JSON parsing error from IP {client_ip}: {e}")
            raise HTTPException(status_code=400, detail="Invalid JSON payload")
        except Exception as e:
            logger.error(f"Payload parsing error from IP {client_ip}: {e}")
            raise HTTPException(status_code=400, detail="Payload parsing error")
        
        # 6. Deduplicación CRÍTICA
        if self.is_duplicate_message(webhook_data):
            # Retornar 200 para evitar reintentos de Chatwoot
            raise HTTPException(status_code=200, detail="Duplicate message ignored")
        
        return webhook_data
    
    def is_processable_message(self, webhook_data: Dict[str, Any]) -> tuple[bool, str]:
        """Verificar si el mensaje debe ser procesado"""
        
        # Solo message_created
        if webhook_data.get('event') != 'message_created':
            return False, 'not message_created event'
        
        # Solo mensajes incoming del cliente
        if webhook_data.get('message_type') != 'incoming':
            return False, 'not incoming message'
        
        # Prevenir loops del bot
        sender = webhook_data.get('sender', {})
        if sender.get('type') == 'agent_bot':
            return False, 'bot message loop prevention'
        
        # Verificar por ID del bot
        bot_id = os.getenv('CHATWOOT_BOT_AGENT_ID')
        if bot_id and str(sender.get('id')) == str(bot_id):
            return False, 'bot ID loop prevention'
        
        # Solo conversaciones en pending (bot activo)
        conversation = webhook_data.get('conversation', {})
        if conversation.get('status') != 'pending':
            return False, f"conversation not pending (status: {conversation.get('status')})"
        
        # Verificar que el mensaje tiene contenido
        content = webhook_data.get('content', '').strip()
        if not content:
            return False, 'empty message content'
        
        return True, 'processable'
    
    def extract_conversation_data(self, webhook_data: Dict[str, Any]) -> Dict[str, Any]:
        """Extraer datos relevantes del webhook"""
        conversation = webhook_data.get('conversation', {})
        contact = conversation.get('contact', {})
        
        return {
            'conversation_id': conversation.get('id'),
            'message_id': webhook_data.get('id'),
            'message_content': webhook_data.get('content', '').strip(),
            'contact': {
                'id': contact.get('id'),
                'name': contact.get('name', 'Cliente'),
                'email': contact.get('email'),
                'phone': contact.get('phone_number'),
                'company_name': contact.get('company_name', 'Su empresa')
            },
            'inbox_id': conversation.get('inbox_id'),
            'conversation_status': conversation.get('status'),
            'created_at': webhook_data.get('created_at'),
            'account_id': webhook_data.get('account', {}).get('id')
        }
    
    def log_security_event(self, event_type: str, details: Dict[str, Any]):
        """Log eventos de seguridad para monitoreo"""
        logger.info(f"Security event: {event_type}", extra={
            'event_type': event_type,
            'details': details,
            'timestamp': datetime.now().isoformat()
        })
    
    def validate_environment(self) -> bool:
        """Validar que todas las variables de entorno están configuradas"""
        required_vars = [
            'VITE_CHATWOOT_ACCOUNT_ID',
            'VITE_CHATWOOT_API_TOKEN',
            'CHATWOOT_WEBHOOK_TOKEN'
        ]
        
        missing_vars = []
        for var in required_vars:
            if not os.getenv(var):
                missing_vars.append(var)
        
        if missing_vars:
            logger.error(f"Missing required environment variables: {missing_vars}")
            return False
        
        logger.info("All required environment variables are configured")
        return True