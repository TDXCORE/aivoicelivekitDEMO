"""
Integración para enviar resumen de conversación del bot a Chatwoot Cloud
Utiliza custom_attributes para almacenar el resumen ya que no hay API específica para Contact Notes
"""

import os
import json
import requests
from datetime import datetime
from typing import Dict, Any, Optional
import logging
import time

# Configuración de logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class ChatwootSummaryIntegration:
    def __init__(self):
        self.account_id = os.getenv('VITE_CHATWOOT_ACCOUNT_ID', '126521')
        self.api_token = os.getenv('VITE_CHATWOOT_API_TOKEN', 'PNwLGXoDiJ22QKd4AzX9Xxof')
        self.inbox_id = os.getenv('VITE_CHATWOOT_INBOX_ID', '69704')  # ID numérico, no identifier
        self.base_url = "https://app.chatwoot.com/api/v1"
        
        self.headers = {
            'Content-Type': 'application/json',
            'api_access_token': self.api_token
        }
    
    def find_contact_by_phone(self, phone_number: str) -> Optional[Dict[str, Any]]:
        """
        Busca un contacto por número de teléfono
        """
        try:
            # Limpiar número de teléfono
            clean_phone = phone_number.replace('+', '').replace('-', '').replace(' ', '')
            
            # Buscar contacto
            url = f"{self.base_url}/accounts/{self.account_id}/contacts/search"
            params = {'q': phone_number}
            
            response = requests.get(url, headers=self.headers, params=params)
            
            if response.status_code == 200:
                contacts = response.json().get('payload', [])
                
                # Buscar contacto exacto por teléfono
                for contact in contacts:
                    if contact.get('phone_number'):
                        contact_phone = contact['phone_number'].replace('+', '').replace('-', '').replace(' ', '')
                        if contact_phone == clean_phone:
                            return contact
                            
                return contacts[0] if contacts else None
            else:
                logger.error(f"Error buscando contacto: {response.status_code} - {response.text}")
                return None
                
        except Exception as e:
            logger.error(f"Error en find_contact_by_phone: {str(e)}")
            return None
    
    def get_contact_inbox_source_id(self, contact_id: int) -> Optional[str]:
        """
        Obtiene el source_id del contact_inbox para crear conversaciones
        """
        try:
            url = f"{self.base_url}/accounts/{self.account_id}/contacts/{contact_id}/contactable_inboxes"
            response = requests.get(url, headers=self.headers)
            
            if response.status_code == 200:
                inboxes = response.json().get('payload', [])
                
                # Buscar el inbox que coincida con nuestro inbox_id
                for inbox in inboxes:
                    if str(inbox.get('inbox_id')) == str(self.inbox_id):
                        source_id = inbox.get('source_id')
                        if source_id:
                            logger.info(f"✅ Source ID encontrado: {source_id} para contacto {contact_id}")
                            return source_id
                
                # Si no encuentra el inbox específico, usar el primero disponible
                if inboxes:
                    source_id = inboxes[0].get('source_id')
                    logger.warning(f"⚠️ Usando primer source_id disponible: {source_id}")
                    return source_id
                    
                logger.error(f"No se encontraron inboxes para contacto {contact_id}")
                return None
                
            else:
                logger.error(f"Error obteniendo contactable inboxes: {response.status_code} - {response.text}")
                return None
                
        except Exception as e:
            logger.error(f"Error en get_contact_inbox_source_id: {str(e)}")
            return None
    
    def ensure_contact_inbox_association(self, contact_id: int) -> bool:
        """
        Verifica y crea la asociación entre contacto e inbox si no existe
        """
        try:
            # Primero verificar si ya existe la asociación
            source_id = self.get_contact_inbox_source_id(contact_id)
            if source_id:
                return True
            
            # Si no existe, intentar crear la asociación
            # Nota: Esto puede requerir permisos específicos según la configuración de Chatwoot
            logger.warning(f"Contacto {contact_id} no está asociado al inbox {self.inbox_id}")
            
            # Para API channels, la asociación se puede crear automáticamente
            # al crear la primera conversación
            return False
            
        except Exception as e:
            logger.error(f"Error en ensure_contact_inbox_association: {str(e)}")
            return False
    
    def update_contact_with_summary(self, contact_id: int, conversation_summary: str, 
                                   call_duration: Optional[str] = None,
                                   call_outcome: Optional[str] = None) -> bool:
        """
        Actualiza un contacto con el resumen de conversación usando custom_attributes
        """
        try:
            # Preparar datos del resumen
            timestamp = datetime.now().isoformat()
            
            custom_attributes = {
                'last_bot_conversation_summary': conversation_summary,
                'last_bot_call_date': timestamp,
                'bot_interaction_status': 'completed'
            }
            
            # Agregar información adicional si está disponible
            if call_duration:
                custom_attributes['last_call_duration'] = call_duration
            if call_outcome:
                custom_attributes['last_call_outcome'] = call_outcome
            
            # Actualizar contacto
            url = f"{self.base_url}/accounts/{self.account_id}/contacts/{contact_id}"
            payload = {
                'custom_attributes': custom_attributes
            }
            
            response = requests.put(url, headers=self.headers, json=payload)
            
            if response.status_code == 200:
                logger.info(f"✅ Resumen actualizado para contacto {contact_id}")
                return True
            else:
                logger.error(f"Error actualizando contacto: {response.status_code} - {response.text}")
                return False
                
        except Exception as e:
            logger.error(f"Error en update_contact_with_summary: {str(e)}")
            return False
    
    def create_conversation_with_summary(self, contact_id: int, conversation_summary: str) -> bool:
        """
        Crea una nueva conversación con el resumen como mensaje usando source_id válido
        """
        try:
            # 1. Obtener source_id válido
            source_id = self.get_contact_inbox_source_id(contact_id)
            
            if not source_id:
                # Intentar crear asociación o usar phone como source_id para API channels
                logger.warning(f"No se pudo obtener source_id para contacto {contact_id}, usando timestamp")
                source_id = f"bot-summary-{int(datetime.now().timestamp())}"
            
            # 2. Crear conversación con source_id válido
            conversation_payload = {
                'source_id': source_id,
                'inbox_id': int(self.inbox_id),
                'contact_id': contact_id,
                'status': 'resolved'
            }
            
            conv_url = f"{self.base_url}/accounts/{self.account_id}/conversations"
            logger.info(f"Creando conversación con payload: {conversation_payload}")
            
            conv_response = requests.post(conv_url, headers=self.headers, json=conversation_payload)
            
            if conv_response.status_code != 200:
                logger.error(f"Error creando conversación: {conv_response.status_code} - {conv_response.text}")
                return False
            
            conversation = conv_response.json()
            conversation_id = conversation.get('id')
            logger.info(f"Conversación creada exitosamente: ID {conversation_id}")
            
            # 3. Enviar mensaje con resumen
            message_content = f"""📋 **Resumen de Conversación Bot TDX**

📅 **Fecha:** {datetime.now().strftime('%d/%m/%Y %H:%M')}
🤖 **Agente:** Mati (Bot de Voz)

**Resumen de la Conversación:**
{conversation_summary}

---
*Generado automáticamente por el sistema de bot de voz TDX*"""

            message_payload = {
                'content': message_content,
                'message_type': 'outgoing',
                'private': False
            }
            
            msg_url = f"{self.base_url}/accounts/{self.account_id}/conversations/{conversation_id}/messages"
            msg_response = requests.post(msg_url, headers=self.headers, json=message_payload)
            
            if msg_response.status_code == 200:
                logger.info(f"✅ Conversación con resumen creada para contacto {contact_id}")
                return True
            else:
                logger.error(f"Error enviando mensaje: {msg_response.status_code} - {msg_response.text}")
                return False
                
        except Exception as e:
            logger.error(f"Error en create_conversation_with_summary: {str(e)}")
            return False
    
    def create_conversation_with_retry(self, contact_id: int, conversation_summary: str, max_retries: int = 3) -> bool:
        """
        Crea conversación con reintentos y diferentes estrategias
        """
        for attempt in range(max_retries):
            try:
                logger.info(f"Intento {attempt + 1}/{max_retries} de crear conversación")
                
                if self.create_conversation_with_summary(contact_id, conversation_summary):
                    return True
                
                # Esperar antes del siguiente intento
                if attempt < max_retries - 1:
                    wait_time = (attempt + 1) * 2  # Backoff exponencial
                    logger.info(f"Esperando {wait_time}s antes del siguiente intento...")
                    time.sleep(wait_time)
                    
            except Exception as e:
                logger.error(f"Error en intento {attempt + 1}: {str(e)}")
                if attempt < max_retries - 1:
                    time.sleep((attempt + 1) * 2)
        
        return False
    
    def send_conversation_summary_hybrid(self, phone_number: str, conversation_summary: str,
                                        call_duration: Optional[str] = None,
                                        call_outcome: Optional[str] = None) -> bool:
        """
        Método híbrido que intenta crear conversación y usa custom_attributes como respaldo
        """
        try:
            # 1. Buscar contacto
            contact = self.find_contact_by_phone(phone_number)
            
            if not contact:
                logger.error(f"No se encontró contacto con teléfono: {phone_number}")
                return False
            
            contact_id = contact['id']
            logger.info(f"Contacto encontrado: {contact['name']} (ID: {contact_id})")
            
            # 2. Intentar crear conversación primero (más visible)
            logger.info(f"Intentando crear conversación para resumen...")
            
            if self.create_conversation_with_retry(contact_id, conversation_summary):
                logger.info(f"✅ Resumen enviado exitosamente vía conversación")
                return True
            
            # 3. Si falla, usar custom_attributes como respaldo
            logger.warning(f"Conversación falló, intentando custom_attributes como respaldo...")
            
            if self.update_contact_with_summary(contact_id, conversation_summary, call_duration, call_outcome):
                logger.info(f"✅ Resumen enviado exitosamente vía custom_attributes")
                return True
            
            logger.error(f"❌ Todos los métodos fallaron para enviar resumen")
            return False
                
        except Exception as e:
            logger.error(f"Error en send_conversation_summary_hybrid: {str(e)}")
            return False
    
    def send_conversation_summary(self, phone_number: str, conversation_summary: str,
                                 call_duration: Optional[str] = None,
                                 call_outcome: Optional[str] = None,
                                 method: str = 'hybrid') -> bool:
        """
        Función principal para enviar resumen de conversación
        
        Args:
            phone_number: Número de teléfono del contacto
            conversation_summary: Resumen de la conversación
            call_duration: Duración de la llamada (opcional)
            call_outcome: Resultado de la llamada (opcional)
            method: 'custom_attributes', 'conversation' o 'hybrid' (método a usar)
        """
        try:
            # 1. Buscar contacto
            contact = self.find_contact_by_phone(phone_number)
            
            if not contact:
                logger.error(f"No se encontró contacto con teléfono: {phone_number}")
                return False
            
            contact_id = contact['id']
            logger.info(f"Contacto encontrado: {contact['name']} (ID: {contact_id})")
            
            # 2. Enviar resumen según método elegido
            if method == 'hybrid':
                return self.send_conversation_summary_hybrid(
                    phone_number, conversation_summary, call_duration, call_outcome
                )
            elif method == 'custom_attributes':
                return self.update_contact_with_summary(
                    contact_id, conversation_summary, call_duration, call_outcome
                )
            elif method == 'conversation':
                return self.create_conversation_with_retry(contact_id, conversation_summary)
            else:
                logger.error(f"Método no válido: {method}")
                return False
                
        except Exception as e:
            logger.error(f"Error en send_conversation_summary: {str(e)}")
            return False


# Función de conveniencia para uso directo
def send_bot_summary_to_chatwoot(phone_number: str, conversation_summary: str, 
                                call_duration: Optional[str] = None,
                                call_outcome: Optional[str] = None) -> bool:
    """
    Función simple para enviar resumen de conversación a Chatwoot
    
    Args:
        phone_number: Número de teléfono del contacto
        conversation_summary: Resumen de la conversación del bot
        call_duration: Duración de la llamada (opcional)
        call_outcome: Resultado de la llamada (opcional)
    
    Returns:
        bool: True si el envío fue exitoso, False en caso contrario
    """
    integration = ChatwootSummaryIntegration()
    return integration.send_conversation_summary(
        phone_number=phone_number,
        conversation_summary=conversation_summary,
        call_duration=call_duration,
        call_outcome=call_outcome,
        method='hybrid'  # Cambiado a hybrid para mejor robustez
    )


# Ejemplo de uso
if __name__ == "__main__":
    # Ejemplo de uso
    phone = "+573001234567"
    summary = """
    Cliente: Ana Ortiz
    Empresa: Ejemplo Corp
    
    Conversación:
    - Cliente interesado en soluciones de IA
    - Necesita automatización de procesos
    - Presupuesto: $5,000 - $10,000 USD
    - Próximo paso: Reunión técnica agendada para el 15/01/2024
    
    Outcome: Reunión agendada exitosamente
    """
    
    result = send_bot_summary_to_chatwoot(
        phone_number=phone,
        conversation_summary=summary,
        call_duration="8 minutos",
        call_outcome="Reunión agendada"
    )
    
    if result:
        print("✅ Resumen enviado exitosamente a Chatwoot")
    else:
        print("❌ Error enviando resumen a Chatwoot")