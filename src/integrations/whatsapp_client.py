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
    
    async def find_or_create_whatsapp_conversation(self, phone_number: str, contact_name: str = None) -> Optional[Dict[str, Any]]:
        """Encontrar conversación existente de WhatsApp o crear una nueva"""
        try:
            # 1. Buscar conversación existente por número de teléfono
            logger.info(f"Searching for existing WhatsApp conversation for {phone_number}")
            
            # Buscar contacto por teléfono
            search_url = f"{self.base_url}/accounts/{self.account_id}/contacts/search"
            search_params = {'q': phone_number}
            
            existing_contact = None
            try:
                import __main__
                if hasattr(__main__, 'http_session') and __main__.http_session:
                    session = __main__.http_session
                    async with session.get(search_url, headers=self.headers, params=search_params) as response:
                        if response.status == 200:
                            contacts_data = await response.json()
                            contacts = contacts_data.get('payload', [])
                            
                            # Buscar contacto exacto por teléfono
                            for contact in contacts:
                                if contact.get('phone_number'):
                                    clean_contact_phone = contact['phone_number'].replace('+', '').replace('-', '').replace(' ', '')
                                    clean_search_phone = phone_number.replace('+', '').replace('-', '').replace(' ', '')
                                    if clean_contact_phone == clean_search_phone:
                                        existing_contact = contact
                                        break
                else:
                    async with aiohttp.ClientSession() as session:
                        async with session.get(search_url, headers=self.headers, params=search_params) as response:
                            if response.status == 200:
                                contacts_data = await response.json()
                                contacts = contacts_data.get('payload', [])
                                
                                for contact in contacts:
                                    if contact.get('phone_number'):
                                        clean_contact_phone = contact['phone_number'].replace('+', '').replace('-', '').replace(' ', '')
                                        clean_search_phone = phone_number.replace('+', '').replace('-', '').replace(' ', '')
                                        if clean_contact_phone == clean_search_phone:
                                            existing_contact = contact
                                            break
            except Exception as e:
                logger.warning(f"Error searching for existing contact: {e}")
            
            # 2. Si hay contacto existente, buscar conversaciones activas
            if existing_contact:
                contact_id = existing_contact['id']
                logger.info(f"Found existing contact with ID: {contact_id}")
                
                # Buscar conversaciones del contacto
                conversations_url = f"{self.base_url}/accounts/{self.account_id}/conversations"
                conversations_params = {'contact_id': contact_id, 'status': 'pending'}
                
                try:
                    if hasattr(__main__, 'http_session') and __main__.http_session:
                        session = __main__.http_session
                        async with session.get(conversations_url, headers=self.headers, params=conversations_params) as response:
                            if response.status == 200:
                                conversations_data = await response.json()
                                conversations = conversations_data.get('data', {}).get('payload', [])
                                
                                # Buscar conversación de WhatsApp pendiente
                                for conv in conversations:
                                    if conv.get('inbox_id') == int(os.getenv('VITE_CHATWOOT_INBOX_ID', '0')):
                                        logger.info(f"Found existing WhatsApp conversation: {conv['id']}")
                                        return {
                                            'conversation_id': conv['id'],
                                            'contact_id': contact_id,
                                            'status': 'existing',
                                            'contact_name': existing_contact.get('name', contact_name)
                                        }
                    else:
                        async with aiohttp.ClientSession() as session:
                            async with session.get(conversations_url, headers=self.headers, params=conversations_params) as response:
                                if response.status == 200:
                                    conversations_data = await response.json()
                                    conversations = conversations_data.get('data', {}).get('payload', [])
                                    
                                    for conv in conversations:
                                        if conv.get('inbox_id') == int(os.getenv('VITE_CHATWOOT_INBOX_ID', '0')):
                                            logger.info(f"Found existing WhatsApp conversation: {conv['id']}")
                                            return {
                                                'conversation_id': conv['id'],
                                                'contact_id': contact_id,
                                                'status': 'existing',
                                                'contact_name': existing_contact.get('name', contact_name)
                                            }
                except Exception as e:
                    logger.warning(f"Error searching conversations: {e}")
            
            # 3. Si no hay conversación existente, crear una nueva
            logger.info(f"Creating new WhatsApp conversation for {phone_number}")
            
            # Crear o actualizar contacto
            if existing_contact:
                contact_id = existing_contact['id']
                contact_name_final = existing_contact.get('name') or contact_name or 'Lead WhatsApp'
            else:
                # Crear nuevo contacto
                create_contact_url = f"{self.base_url}/accounts/{self.account_id}/contacts"
                contact_payload = {
                    'name': contact_name or 'Lead WhatsApp',
                    'phone_number': phone_number,
                    'inbox_id': int(os.getenv('VITE_CHATWOOT_INBOX_ID', '0'))
                }
                
                try:
                    if hasattr(__main__, 'http_session') and __main__.http_session:
                        session = __main__.http_session
                        async with session.post(create_contact_url, headers=self.headers, json=contact_payload) as response:
                            if response.status == 200:
                                contact_data = await response.json()
                                contact_id = contact_data['payload']['contact']['id']
                                contact_name_final = contact_data['payload']['contact']['name']
                                logger.info(f"Created new contact with ID: {contact_id}")
                            else:
                                logger.error(f"Failed to create contact: {response.status}")
                                return None
                    else:
                        async with aiohttp.ClientSession() as session:
                            async with session.post(create_contact_url, headers=self.headers, json=contact_payload) as response:
                                if response.status == 200:
                                    contact_data = await response.json()
                                    contact_id = contact_data['payload']['contact']['id']
                                    contact_name_final = contact_data['payload']['contact']['name']
                                    logger.info(f"Created new contact with ID: {contact_id}")
                                else:
                                    logger.error(f"Failed to create contact: {response.status}")
                                    return None
                except Exception as e:
                    logger.error(f"Error creating contact: {e}")
                    return None
            
            # Crear nueva conversación
            create_conversation_url = f"{self.base_url}/accounts/{self.account_id}/conversations"
            conversation_payload = {
                'source_id': phone_number.replace('+', '').replace('-', '').replace(' ', ''),
                'inbox_id': int(os.getenv('VITE_CHATWOOT_INBOX_ID', '0')),
                'contact_id': contact_id,
                'status': 'pending'
            }
            
            try:
                if hasattr(__main__, 'http_session') and __main__.http_session:
                    session = __main__.http_session
                    async with session.post(create_conversation_url, headers=self.headers, json=conversation_payload) as response:
                        if response.status == 200:
                            conversation_data = await response.json()
                            conversation_id = conversation_data['id']
                            logger.info(f"Created new conversation with ID: {conversation_id}")
                            
                            return {
                                'conversation_id': conversation_id,
                                'contact_id': contact_id,
                                'status': 'created',
                                'contact_name': contact_name_final
                            }
                        else:
                            logger.error(f"Failed to create conversation: {response.status}")
                            return None
                else:
                    async with aiohttp.ClientSession() as session:
                        async with session.post(create_conversation_url, headers=self.headers, json=conversation_payload) as response:
                            if response.status == 200:
                                conversation_data = await response.json()
                                conversation_id = conversation_data['id']
                                logger.info(f"Created new conversation with ID: {conversation_id}")
                                
                                return {
                                    'conversation_id': conversation_id,
                                    'contact_id': contact_id,
                                    'status': 'created',
                                    'contact_name': contact_name_final
                                }
                            else:
                                logger.error(f"Failed to create conversation: {response.status}")
                                return None
            except Exception as e:
                logger.error(f"Error creating conversation: {e}")
                return None
                
        except Exception as e:
            logger.error(f"Error in find_or_create_whatsapp_conversation: {e}")
            return None
    
    async def send_proactive_greeting_message(self, phone_number: str, contact_name: str, contact_data: Dict[str, Any]) -> bool:
        """Enviar mensaje de saludo proactivo personalizado"""
        try:
            logger.info(f"🔍 CLIENT DEBUG - send_proactive_greeting_message called")
            logger.info(f"🔍 CLIENT DEBUG - Phone: {phone_number}, Name: {contact_name}")
            logger.info(f"🔍 CLIENT DEBUG - Contact data: {contact_data}")
            
            # Verificar configuración
            logger.info(f"🔍 CLIENT DEBUG - Account ID: {self.account_id}")
            logger.info(f"🔍 CLIENT DEBUG - API Token configured: {bool(self.api_token)}")
            logger.info(f"🔍 CLIENT DEBUG - WhatsApp Inbox ID: {os.getenv('VITE_CHATWOOT_INBOX_ID')}")
            
            # 1. Encontrar o crear conversación
            conversation_info = await self.find_or_create_whatsapp_conversation(phone_number, contact_name)
            
            if not conversation_info:
                logger.error(f"❌ Could not create/find conversation for {phone_number}")
                return False
            
            conversation_id = conversation_info['conversation_id']
            final_contact_name = conversation_info['contact_name']
            
            # 2. Generar mensaje personalizado basado en los datos del contacto
            company_name = contact_data.get('company_name', '')
            email = contact_data.get('email', '')
            source = contact_data.get('source', 'manual')
            
            # Mensaje personalizado según la fuente
            if source == 'landing_page':
                greeting_message = f"""👋 ¡Hola {final_contact_name}!
                
Soy Mati, asistente virtual de TDX. Vi que te registraste en nuestro sitio web mostrando interés en soluciones de inteligencia artificial.

🚀 Estamos aquí para ayudarte a transformar tu {f'empresa {company_name}' if company_name else 'negocio'} con IA.

¿Qué desafío tecnológico específico te gustaría resolver? 

📞 También intenté llamarte, pero prefiero asegurarme de que puedas contactarnos por el canal que más te convenga."""
            else:
                greeting_message = f"""👋 ¡Hola {final_contact_name}!

Soy Mati, asistente virtual de TDX. Te contacto por tu interés en nuestras soluciones de inteligencia artificial.

🚀 Ayudamos a empresas como{f' {company_name}' if company_name else ' la tuya'} a implementar IA para automatizar procesos y mejorar la eficiencia.

¿Qué área de tu negocio te gustaría optimizar con inteligencia artificial?"""
            
            # 3. Enviar el mensaje
            user_id = str(conversation_info['contact_id'])
            result = await self.send_message_with_typing(conversation_id, greeting_message, user_id)
            
            if result:
                logger.info(f"Proactive greeting sent successfully to {phone_number}")
                
                # 4. Marcar conversación como asignada al bot
                if self.bot_agent_id:
                    await self.return_to_bot_assignment(conversation_id)
                
                return True
            else:
                logger.error(f"Failed to send proactive greeting to {phone_number}")
                return False
                
        except Exception as e:
            logger.error(f"Error sending proactive greeting message: {e}")
            return False