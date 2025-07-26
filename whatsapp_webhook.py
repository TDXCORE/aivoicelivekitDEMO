from fastapi import Request, HTTPException
import logging
from typing import Dict, Any
import asyncio
from datetime import datetime

from whatsapp_bot import TDXWhatsAppBot
from whatsapp_security import WhatsAppWebhookSecurity
from whatsapp_metrics import whatsapp_metrics

logger = logging.getLogger("whatsapp-webhook")

class WhatsAppWebhookHandler:
    def __init__(self):
        self.security = WhatsAppWebhookSecurity()
        self.metrics = whatsapp_metrics
        self.active_bots: Dict[int, TDXWhatsAppBot] = {}
        
        # Validar configuración al inicializar
        if not self.security.validate_environment():
            raise ValueError("WhatsApp webhook handler: Environment not properly configured")
        
        logger.info("WhatsApp webhook handler initialized successfully")
    
    async def handle_webhook(self, request: Request) -> Dict[str, Any]:
        """Handler principal con todas las validaciones"""
        start_time = datetime.now()
        
        try:
            # 1. Validación de seguridad y deduplicación
            webhook_data = await self.security.validate_webhook(request)
            
            # 1.1. Manejo de mensajes duplicados
            if webhook_data is None:
                return {'status': 'ignored', 'reason': 'duplicate_message'}
            
            # 2. Verificar si el mensaje debe ser procesado
            processable, reason = self.security.is_processable_message(webhook_data)
            if not processable:
                logger.info(f"Message ignored: {reason} - Conversation ID: {webhook_data.get('conversation', {}).get('id')}")
                return {'status': 'ignored', 'reason': reason}
            
            # 3. Procesar mensaje con bot
            result = await self.process_customer_message(webhook_data, start_time)
            return result
            
        except HTTPException as e:
            # Errores de validación (401, 403, 429, etc.)
            logger.warning(f"Webhook validation failed: {e.status_code} - {e.detail}")
            raise e
        except Exception as e:
            logger.error(f"Unexpected webhook error: {e}")
            return {'status': 'error', 'message': str(e)}
    
    async def process_customer_message(self, webhook_data: Dict[str, Any], start_time: datetime) -> Dict[str, Any]:
        """Procesar mensaje del cliente"""
        conversation_id = None
        
        try:
            # Extraer datos del webhook usando security helper
            extracted_data = self.security.extract_conversation_data(webhook_data)
            
            conversation_id = extracted_data['conversation_id']
            message_content = extracted_data['message_content']
            contact = extracted_data['contact']
            
            logger.info(f"Processing WhatsApp message: conversation {conversation_id} from {contact['name']}")
            
            # Obtener o crear instancia del bot para esta conversación
            bot = await self.get_or_create_bot(conversation_id, contact)
            
            # Métricas: log mensaje del usuario
            await self.metrics.log_user_message(conversation_id, message_content)
            
            # Procesar mensaje y medir tiempo de respuesta
            response_start = datetime.now()
            response = await bot.process_message(message_content)
            response_time = (datetime.now() - response_start).total_seconds()
            
            # Métricas: log respuesta del bot
            if response:
                await self.metrics.log_bot_response(conversation_id, response, response_time)
                
                # Calcular tiempo total de procesamiento
                total_time = (datetime.now() - start_time).total_seconds()
                
                return {
                    'status': 'processed',
                    'conversation_id': conversation_id,
                    'response_sent': True,
                    'response_length': len(response),
                    'processing_time': round(total_time, 3),
                    'response_time': round(response_time, 3)
                }
            else:
                await self.metrics.log_error(conversation_id, 'response_generation_failed', 'Bot failed to generate response')
                return {
                    'status': 'processed',
                    'conversation_id': conversation_id,
                    'response_sent': False,
                    'error': 'Failed to generate response'
                }
                
        except Exception as e:
            logger.error(f"Error processing message: {e}")
            if conversation_id:
                await self.metrics.log_error(conversation_id, 'processing_error', str(e))
            return {'status': 'error', 'message': str(e)}
    
    async def get_or_create_bot(self, conversation_id: int, contact: Dict[str, Any]) -> TDXWhatsAppBot:
        """Obtener bot existente o crear nuevo"""
        
        if conversation_id not in self.active_bots:
            # Crear nuevo bot
            contact_name = contact.get('name', 'Cliente')
            company_name = contact.get('company_name', 'Su empresa')
            
            prospect_info = {
                'email': contact.get('email'),
                'phone': contact.get('phone'),
                'source': 'whatsapp',
                'chatwoot_id': contact.get('id'),
                'company_name': company_name,
                'contact_name': contact_name
            }
            
            bot = TDXWhatsAppBot(
                contact_name=contact_name,
                company_name=company_name,
                prospect_info=prospect_info,
                conversation_id=conversation_id
            )
            
            self.active_bots[conversation_id] = bot
            
            # Log métricas de nueva conversación
            await self.metrics.log_conversation_started(conversation_id, prospect_info)
            
            logger.info(f"Created new WhatsApp bot for conversation {conversation_id} - Contact: {contact_name}")
        
        return self.active_bots[conversation_id]
    
    async def cleanup_inactive_bots(self, max_inactive_hours: int = 24):
        """Limpiar bots inactivos para liberar memoria"""
        current_time = datetime.now()
        inactive_threshold = max_inactive_hours * 3600  # en segundos
        
        bots_to_remove = []
        
        for conversation_id, bot in self.active_bots.items():
            # Verificar última actividad del bot
            if hasattr(bot, 'conversation_log') and bot.conversation_log:
                last_activity = bot.conversation_log[-1].get('timestamp')
                if last_activity:
                    try:
                        last_activity_time = datetime.fromisoformat(last_activity)
                        time_diff = (current_time - last_activity_time).total_seconds()
                        
                        if time_diff > inactive_threshold:
                            bots_to_remove.append(conversation_id)
                            # Log fin de conversación por inactividad
                            await self.metrics.log_conversation_ended(conversation_id, "inactive_cleanup")
                    except:
                        # Si hay error parseando timestamp, considerar para limpieza
                        bots_to_remove.append(conversation_id)
        
        # Remover bots inactivos
        for conversation_id in bots_to_remove:
            del self.active_bots[conversation_id]
        
        if bots_to_remove:
            logger.info(f"Cleaned up {len(bots_to_remove)} inactive WhatsApp bots")
        
        return len(bots_to_remove)
    
    async def get_handler_stats(self) -> Dict[str, Any]:
        """Obtener estadísticas del handler"""
        return {
            'active_bots': len(self.active_bots),
            'conversations_by_status': {
                'active': len([
                    bot for bot in self.active_bots.values()
                    if hasattr(bot, 'awaiting_response_type') and bot.awaiting_response_type
                ]),
                'idle': len([
                    bot for bot in self.active_bots.values()
                    if not hasattr(bot, 'awaiting_response_type') or not bot.awaiting_response_type
                ])
            },
            'handler_uptime': (datetime.now() - datetime.now()).total_seconds(),  # Placeholder
            'total_processed_messages': sum([
                len(bot.conversation_log) for bot in self.active_bots.values()
                if hasattr(bot, 'conversation_log')
            ])
        }
    
    async def force_cleanup_conversation(self, conversation_id: int, reason: str = "manual_cleanup") -> bool:
        """Forzar limpieza de una conversación específica"""
        if conversation_id in self.active_bots:
            # Log fin de conversación
            await self.metrics.log_conversation_ended(conversation_id, reason)
            
            # Remover bot
            del self.active_bots[conversation_id]
            
            logger.info(f"Forced cleanup of conversation {conversation_id}: {reason}")
            return True
        
        return False
    
    async def get_conversation_status(self, conversation_id: int) -> Dict[str, Any]:
        """Obtener estado de una conversación"""
        if conversation_id not in self.active_bots:
            return {'status': 'not_found', 'active': False}
        
        bot = self.active_bots[conversation_id]
        
        return {
            'status': 'active',
            'active': True,
            'contact_name': bot.contact_name,
            'company_name': bot.company_name,
            'message_count': len(bot.conversation_log) if hasattr(bot, 'conversation_log') else 0,
            'awaiting_response': bot.awaiting_response_type if hasattr(bot, 'awaiting_response_type') else None,
            'session_start': bot.session_start_time.isoformat() if hasattr(bot, 'session_start_time') else None
        }

# Instancia global del handler
whatsapp_webhook_handler = WhatsAppWebhookHandler()