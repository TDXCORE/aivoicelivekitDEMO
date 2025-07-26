import aiohttp
import os
import logging
from typing import Optional, Dict, Any, List
from datetime import datetime, timedelta
import asyncio

logger = logging.getLogger("whatsapp-client")

class ChatwootWhatsAppClient:
    def __init__(self):
        self.account_id = os.getenv('VITE_CHATWOOT_ACCOUNT_ID')
        self.api_token = os.getenv('VITE_CHATWOOT_API_TOKEN')
        self.bot_agent_id = os.getenv('CHATWOOT_BOT_AGENT_ID')
        self.base_url = "https://app.chatwoot.com/api/v1"
        
        self.headers = {
            'Content-Type': 'application/json',
            'api_access_token': self.api_token
        }
        
        # Rate limiting optimizado para ventas agresivas (3s por usuario)
        self.user_rate_limits: Dict[str, datetime] = {}
        self.rate_limit_duration = int(os.getenv('WHATSAPP_RATE_LIMIT_SECONDS', '3'))
    
    async def check_rate_limit(self, user_id: str) -> bool:
        """Rate limiting: 1 mensaje cada 3s por usuario (optimizado para ventas agresivas)"""
        now = datetime.now()
        last_message = self.user_rate_limits.get(user_id)
        
        if last_message:
            time_diff = (now - last_message).total_seconds()
            if time_diff < self.rate_limit_duration:
                wait_time = self.rate_limit_duration - time_diff
                logger.info(f"Rate limiting user {user_id}: waiting {wait_time:.1f}s")
                await asyncio.sleep(wait_time)
        
        self.user_rate_limits[user_id] = now
        return True
    
    async def send_message_with_typing(self, conversation_id: int, content: str, user_id: str = None) -> Dict[str, Any]:
        """Enviar mensaje con typing indicator y rate limiting"""
        # Rate limiting por usuario
        if user_id:
            await self.check_rate_limit(user_id)
        
        try:
            # 1. Mostrar typing indicator si el mensaje es largo
            if len(content) > 50:
                await self.toggle_typing_status(conversation_id, True)
                await asyncio.sleep(0.5)  # Simular typing
            
            # 2. Enviar mensaje
            url = f"{self.base_url}/accounts/{self.account_id}/conversations/{conversation_id}/messages"
            
            payload = {
                'content': content,
                'message_type': 'outgoing',
                'private': False
            }
            
            # Usar session global si está disponible, sino crear temporal
            try:
                # Intentar usar session global
                import __main__
                if hasattr(__main__, 'http_session') and __main__.http_session:
                    session = __main__.http_session
                    async with session.post(url, headers=self.headers, json=payload) as response:
                        result = await response.json() if response.status == 200 else None
                else:
                    # Fallback a session temporal
                    async with aiohttp.ClientSession() as session:
                        async with session.post(url, headers=self.headers, json=payload) as response:
                            result = await response.json() if response.status == 200 else None
            except:
                # Fallback final a session temporal
                async with aiohttp.ClientSession() as session:
                    async with session.post(url, headers=self.headers, json=payload) as response:
                        result = await response.json() if response.status == 200 else None
                
            # 3. Quitar typing indicator
            if len(content) > 50:
                await self.toggle_typing_status(conversation_id, False)
            
            if result:
                logger.info(f"Message sent successfully to conversation {conversation_id}")
            else:
                logger.error(f"Failed to send message to conversation {conversation_id}")
                
            return result
                
        except Exception as e:
            logger.error(f"Error sending message: {e}")
            return None
    
    async def toggle_typing_status(self, conversation_id: int, typing: bool) -> bool:
        """Toggle typing indicator (no cuenta para cuota)"""
        url = f"{self.base_url}/accounts/{self.account_id}/conversations/{conversation_id}/toggle_typing_status"
        
        try:
            # Usar session global si está disponible
            try:
                import __main__
                if hasattr(__main__, 'http_session') and __main__.http_session:
                    session = __main__.http_session
                    async with session.post(url, headers=self.headers, json={'typing_status': typing}) as response:
                        return response.status == 200
                else:
                    async with aiohttp.ClientSession() as session:
                        async with session.post(url, headers=self.headers, json={'typing_status': typing}) as response:
                            return response.status == 200
            except:
                async with aiohttp.ClientSession() as session:
                    async with session.post(url, headers=self.headers, json={'typing_status': typing}) as response:
                        return response.status == 200
        except Exception as e:
            logger.error(f"Error toggling typing: {e}")
            return False
    
    async def get_conversation_details(self, conversation_id: int) -> Optional[Dict[str, Any]]:
        """Obtener detalles completos de conversación"""
        url = f"{self.base_url}/accounts/{self.account_id}/conversations/{conversation_id}"
        
        try:
            # Usar session global si está disponible
            try:
                import __main__
                if hasattr(__main__, 'http_session') and __main__.http_session:
                    session = __main__.http_session
                    async with session.get(url, headers=self.headers) as response:
                        if response.status == 200:
                            return await response.json()
                        return None
                else:
                    async with aiohttp.ClientSession() as session:
                        async with session.get(url, headers=self.headers) as response:
                            if response.status == 200:
                                return await response.json()
                            return None
            except:
                async with aiohttp.ClientSession() as session:
                    async with session.get(url, headers=self.headers) as response:
                        if response.status == 200:
                            return await response.json()
                        return None
        except Exception as e:
            logger.error(f"Error getting conversation details: {e}")
            return None
    
    async def handoff_to_human(self, conversation_id: int) -> bool:
        """Handoff mejorado: pending → open"""
        try:
            # 1. Verificar estado actual
            conversation = await self.get_conversation_details(conversation_id)
            if not conversation:
                logger.error(f"Could not get conversation details for {conversation_id}")
                return False
                
            current_status = conversation.get('status')
            logger.info(f"Current status for conversation {conversation_id}: {current_status}")
            
            if current_status == "pending":
                # 2. Cambiar a open usando toggle_status (sin payload)
                toggle_url = f"{self.base_url}/accounts/{self.account_id}/conversations/{conversation_id}/toggle_status"
                
                try:
                    import __main__
                    if hasattr(__main__, 'http_session') and __main__.http_session:
                        session = __main__.http_session
                        async with session.post(toggle_url, headers=self.headers, json={}) as response:
                            if response.status != 200:
                                logger.error(f"Toggle status failed: {response.status}")
                                return False
                    else:
                        async with aiohttp.ClientSession() as session:
                            async with session.post(toggle_url, headers=self.headers, json={}) as response:
                                if response.status != 200:
                                    logger.error(f"Toggle status failed: {response.status}")
                                    return False
                except:
                    async with aiohttp.ClientSession() as session:
                        async with session.post(toggle_url, headers=self.headers, json={}) as response:
                            if response.status != 200:
                                logger.error(f"Toggle status failed: {response.status}")
                                return False
                
                # 3. Verificar cambio exitoso
                await asyncio.sleep(0.5)  # Esperar propagación
                updated_conversation = await self.get_conversation_details(conversation_id)
                new_status = updated_conversation.get('status') if updated_conversation else None
                
                success = new_status == "open"
                logger.info(f"Handoff result: {current_status} → {new_status}, success: {success}")
                return success
            else:
                logger.warning(f"Conversation {conversation_id} is not in pending status (current: {current_status})")
                return False
            
        except Exception as e:
            logger.error(f"Error in handoff: {e}")
            return False
    
    async def return_to_bot_pending(self, conversation_id: int) -> bool:
        """Volver a pending - MÉTODO 1: PATCH directo"""
        url = f"{self.base_url}/accounts/{self.account_id}/conversations/{conversation_id}"
        payload = {"status": "pending"}
        
        try:
            # Usar session global si está disponible
            try:
                import __main__
                if hasattr(__main__, 'http_session') and __main__.http_session:
                    session = __main__.http_session
                    async with session.patch(url, headers=self.headers, json=payload) as response:
                        if response.status == 200:
                            # Verificar cambio
                            await asyncio.sleep(0.5)
                            conversation = await self.get_conversation_details(conversation_id)
                            return conversation.get('status') == 'pending' if conversation else False
                        return False
                else:
                    async with aiohttp.ClientSession() as session:
                        async with session.patch(url, headers=self.headers, json=payload) as response:
                            if response.status == 200:
                                await asyncio.sleep(0.5)
                                conversation = await self.get_conversation_details(conversation_id)
                                return conversation.get('status') == 'pending' if conversation else False
                            return False
            except:
                async with aiohttp.ClientSession() as session:
                    async with session.patch(url, headers=self.headers, json=payload) as response:
                        if response.status == 200:
                            await asyncio.sleep(0.5)
                            conversation = await self.get_conversation_details(conversation_id)
                            return conversation.get('status') == 'pending' if conversation else False
                        return False
                
        except Exception as e:
            logger.error(f"Error returning to pending via PATCH: {e}")
            return False
    
    async def return_to_bot_assignment(self, conversation_id: int) -> bool:
        """Volver a pending - MÉTODO 2: Reasignar bot"""
        url = f"{self.base_url}/accounts/{self.account_id}/conversations/{conversation_id}/assignments"
        payload = {"assignee_id": self.bot_agent_id}
        
        try:
            # Usar session global si está disponible
            try:
                import __main__
                if hasattr(__main__, 'http_session') and __main__.http_session:
                    session = __main__.http_session
                    async with session.post(url, headers=self.headers, json=payload) as response:
                        if response.status == 200:
                            await asyncio.sleep(0.5)
                            conversation = await self.get_conversation_details(conversation_id)
                            return conversation.get('status') == 'pending' if conversation else False
                        return False
                else:
                    async with aiohttp.ClientSession() as session:
                        async with session.post(url, headers=self.headers, json=payload) as response:
                            if response.status == 200:
                                await asyncio.sleep(0.5)
                                conversation = await self.get_conversation_details(conversation_id)
                                return conversation.get('status') == 'pending' if conversation else False
                            return False
            except:
                async with aiohttp.ClientSession() as session:
                    async with session.post(url, headers=self.headers, json=payload) as response:
                        if response.status == 200:
                            await asyncio.sleep(0.5)
                            conversation = await self.get_conversation_details(conversation_id)
                            return conversation.get('status') == 'pending' if conversation else False
                        return False
                
        except Exception as e:
            logger.error(f"Error returning to pending via assignment: {e}")
            return False
    
    async def return_to_bot(self, conversation_id: int) -> bool:
        """Volver al bot - probando ambos métodos"""
        logger.info(f"Attempting to return conversation {conversation_id} to bot")
        
        # Intentar método 1: PATCH
        success = await self.return_to_bot_pending(conversation_id)
        
        if not success:
            # Intentar método 2: Assignment
            logger.info("PATCH method failed, trying assignment method")
            success = await self.return_to_bot_assignment(conversation_id)
        
        if success:
            logger.info(f"Successfully returned conversation {conversation_id} to bot")
        else:
            logger.error(f"Failed to return conversation {conversation_id} to bot")
            
        return success