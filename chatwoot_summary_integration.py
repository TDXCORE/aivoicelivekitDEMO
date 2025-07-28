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
    def __init__(self, inbox_id=None):
        self.account_id = os.getenv('VITE_CHATWOOT_ACCOUNT_ID', '126521')
        self.api_token = os.getenv('VITE_CHATWOOT_API_TOKEN', 'PNwLGXoDiJ22QKd4AzX9Xxof')
        # Permitir override del inbox_id para diferentes casos de uso
        self.inbox_id = inbox_id or os.getenv('VITE_CHATWOOT_INBOX_ID', '69704')  # ID numérico, no identifier
        # Configuración específica para webhook conversations
        self.webhook_inbox_id = os.getenv('CHATWOOT_WEBHOOK_INBOX_ID', self.inbox_id)
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
            
            # 3. Enviar mensaje con resumen formateado
            formatted_summary = self.format_conversation_summary(conversation_summary)
            message_content = formatted_summary

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
    
    def extract_customer_profile(self, summary_data: Dict[str, Any]) -> Dict[str, str]:
        """
        Extrae el perfil del cliente de la conversación
        """
        try:
            conversation_log = summary_data.get('conversation_log', [])
            prospect_info = summary_data.get('prospect_info', {})
            
            # Obtener información básica del prospecto
            profile = {
                'industry': 'No especificada',
                'main_need': 'Consulta general',
                'urgency': 'Media',
                'budget': 'No mencionado',
                'company_size': 'No especificada'
            }
            
            # Analizar mensajes del usuario
            user_messages = [entry['content'].lower() for entry in conversation_log 
                           if entry.get('type') == 'user_message' and entry.get('content', '').strip()]
            
            all_user_text = ' '.join(user_messages)
            
            # Detectar industria
            if 'carro' in all_user_text or 'auto' in all_user_text or 'vehículo' in all_user_text:
                profile['industry'] = 'Automotriz'
            elif 'restaurante' in all_user_text or 'comida' in all_user_text:
                profile['industry'] = 'Restaurantes/Gastronomía'
            elif 'tienda' in all_user_text or 'retail' in all_user_text or 'venta' in all_user_text:
                profile['industry'] = 'Retail/Comercio'
            elif 'tecnología' in all_user_text or 'software' in all_user_text:
                profile['industry'] = 'Tecnología'
            elif 'salud' in all_user_text or 'médico' in all_user_text or 'clínica' in all_user_text:
                profile['industry'] = 'Salud'
            elif 'educación' in all_user_text or 'colegio' in all_user_text or 'universidad' in all_user_text:
                profile['industry'] = 'Educación'
            
            # Detectar necesidad principal
            if 'soporte' in all_user_text and 'nivel' in all_user_text:
                profile['main_need'] = 'Automatización de soporte técnico nivel 1'
            elif 'ventas' in all_user_text or 'vender' in all_user_text:
                profile['main_need'] = 'Automatización de procesos de ventas'
            elif 'atención' in all_user_text and 'cliente' in all_user_text:
                profile['main_need'] = 'Mejora en atención al cliente'
            elif 'bot' in all_user_text or 'chatbot' in all_user_text:
                profile['main_need'] = 'Implementación de chatbot'
            elif 'ia' in all_user_text or 'inteligencia artificial' in all_user_text:
                profile['main_need'] = 'Soluciones de inteligencia artificial'
            
            # Detectar urgencia
            if any(word in all_user_text for word in ['urgente', 'rápido', 'pronto', 'ya', 'inmediato']):
                profile['urgency'] = 'Alta'
            elif any(word in all_user_text for word in ['evaluar', 'analizar', 'futuro', 'próximo año']):
                profile['urgency'] = 'Baja'
            
            # Detectar presupuesto mencionado
            import re
            budget_pattern = r'(\$[\d,]+|[\d,]+\s*(?:pesos|dólares|usd|mil|millón))'
            budget_match = re.search(budget_pattern, all_user_text, re.IGNORECASE)
            if budget_match:
                profile['budget'] = budget_match.group(1)
            
            return profile
            
        except Exception as e:
            logger.error(f"Error extrayendo perfil: {str(e)}")
            return {
                'industry': 'No especificada',
                'main_need': 'Consulta general', 
                'urgency': 'Media',
                'budget': 'No mencionado',
                'company_size': 'No especificada'
            }
    
    def analyze_conversation_outcomes(self, summary_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Analiza los resultados y próximos pasos de la conversación
        """
        try:
            conversation_log = summary_data.get('conversation_log', [])
            all_content = ' '.join([entry.get('content', '') for entry in conversation_log]).lower()
            
            outcomes = {
                'outcome_type': 'Consulta completada',
                'meeting_scheduled': False,
                'transferred': False,
                'email_collected': False,
                'follow_up_required': False,
                'objections': [],
                'next_steps': [],
                'interest_level': 'Medio'
            }
            
            # Detectar si se agendó reunión
            if any(word in all_content for word in ['agendar', 'reunión', 'cita', 'meeting', 'programar']):
                outcomes['meeting_scheduled'] = True
                outcomes['outcome_type'] = 'Reunión agendada'
                
                # Buscar fechas específicas
                if any(day in all_content for day in ['lunes', 'martes', 'miércoles', 'jueves', 'viernes']):
                    outcomes['next_steps'].append('Reunión estratégica programada')
            
            # Detectar transferencia
            if any(word in all_content for word in ['transferir', 'ejecutivo', 'especialista', 'humano']):
                outcomes['transferred'] = True
                outcomes['outcome_type'] = 'Transferido a ejecutivo'
            
            # Detectar nivel de interés
            positive_words = ['interesado', 'me gusta', 'perfecto', 'excelente', 'sí']
            negative_words = ['no', 'no me interesa', 'muy caro', 'no tengo tiempo']
            
            positive_count = sum(1 for word in positive_words if word in all_content)
            negative_count = sum(1 for word in negative_words if word in all_content)
            
            if positive_count > negative_count + 1:
                outcomes['interest_level'] = 'Alto'
            elif negative_count > positive_count:
                outcomes['interest_level'] = 'Bajo'
            
            # Detectar objeciones
            if 'caro' in all_content or 'precio' in all_content:
                outcomes['objections'].append('Preocupación por precio')
            if 'tiempo' in all_content and 'no tengo' in all_content:
                outcomes['objections'].append('Falta de tiempo')
            if 'complejo' in all_content or 'complicado' in all_content:
                outcomes['objections'].append('Percepción de complejidad')
            
            # Determinar seguimiento requerido
            if not outcomes['meeting_scheduled'] and not outcomes['transferred']:
                outcomes['follow_up_required'] = True
                outcomes['next_steps'].append('Seguimiento requerido por equipo de ventas')
            
            return outcomes
            
        except Exception as e:
            logger.error(f"Error analizando outcomes: {str(e)}")
            return {
                'outcome_type': 'Consulta completada',
                'meeting_scheduled': False,
                'transferred': False,
                'interest_level': 'Medio',
                'next_steps': [],
                'objections': []
            }
    
    def format_conversation_summary(self, conversation_summary: str) -> str:
        """
        Convierte el JSON de conversación en un formato ejecutivo profesional
        """
        try:
            # Si es string JSON, parsearlo
            if isinstance(conversation_summary, str):
                if conversation_summary.strip().startswith('{'):
                    try:
                        summary_data = json.loads(conversation_summary)
                    except json.JSONDecodeError as e:
                        logger.error(f"Error parsing JSON: {e}")
                        return conversation_summary
                else:
                    # Si no es JSON, devolver como está
                    return conversation_summary
            else:
                summary_data = conversation_summary
            
            # Extraer información básica
            contact_name = summary_data.get('contact_name', 'Cliente')
            company_name = summary_data.get('company_name', 'N/A')
            call_direction = summary_data.get('call_direction', 'unknown')
            conversation_log = summary_data.get('conversation_log', [])
            prospect_info = summary_data.get('prospect_info', {})
            session_end_time = summary_data.get('session_end_time', '')
            total_turns = summary_data.get('total_turns', 0)
            
            # Extraer perfil del cliente y análisis
            customer_profile = self.extract_customer_profile(summary_data)
            outcomes = self.analyze_conversation_outcomes(summary_data)
            
            # Calcular duración estimada
            duration = "N/A"
            if conversation_log and len(conversation_log) > 0:
                try:
                    first_timestamp = conversation_log[0].get('timestamp', '')
                    last_timestamp = conversation_log[-1].get('timestamp', '') or session_end_time
                    
                    if first_timestamp and last_timestamp:
                        start_time = datetime.fromisoformat(first_timestamp.replace('Z', '+00:00'))
                        end_time = datetime.fromisoformat(last_timestamp.replace('Z', '+00:00'))
                        duration_mins = int((end_time - start_time).total_seconds() / 60)
                        duration = f"{duration_mins} minutos"
                except:
                    duration = "N/A"
            
            # Crear el formato ejecutivo profesional
            formatted_summary = f"""🎯 **RESUMEN EJECUTIVO - BOT TDX**

📊 **INFORMACIÓN DEL CONTACTO**
• **Cliente:** {contact_name}
• **Empresa:** {company_name}
• **Email:** {prospect_info.get('email', 'No disponible')}
• **Teléfono:** {prospect_info.get('phone', 'N/A')}
• **Fuente:** {prospect_info.get('source', 'N/A').replace('_', ' ').title()}
• **ID Chatwoot:** {prospect_info.get('chatwoot_id', 'N/A')}

👤 **PERFIL DEL CLIENTE**
• **Industria:** {customer_profile['industry']}
• **Necesidad principal:** {customer_profile['main_need']}
• **Urgencia:** {customer_profile['urgency']}
• **Presupuesto:** {customer_profile['budget']}
• **Nivel de interés:** {outcomes['interest_level']}

💬 **CONVERSACIÓN COMPLETA**"""
            
            # Procesar cada intercambio de la conversación
            for entry in conversation_log:
                entry_type = entry.get('type', '')
                content = entry.get('content', '').strip()
                timestamp = entry.get('timestamp', '')
                
                # Extraer solo la hora del timestamp
                if timestamp:
                    try:
                        dt = datetime.fromisoformat(timestamp.replace('Z', '+00:00'))
                        time_str = dt.strftime('%H:%M:%S')
                    except:
                        time_str = timestamp.split('T')[1][:8] if 'T' in timestamp else ''
                else:
                    time_str = ''
                
                # Solo mostrar mensajes con contenido
                if content and entry_type in ['user_message', 'assistant_message']:
                    if entry_type == 'user_message':
                        formatted_summary += f"\n[{time_str}] 👤 **{contact_name}:** {content}"
                    elif entry_type == 'assistant_message':
                        # Limpiar markdown del contenido del asistente
                        clean_content = content.replace('**', '').replace('*', '')
                        formatted_summary += f"\n[{time_str}] 🤖 **Mati:** {clean_content}"
            
            # Agregar análisis de la llamada
            formatted_summary += f"\n\n📈 **ANÁLISIS DE LA LLAMADA**"
            formatted_summary += f"\n• **Duración:** {duration}"
            formatted_summary += f"\n• **Total de intercambios:** {total_turns}"
            formatted_summary += f"\n• **Nivel de interés:** {outcomes['interest_level']}"
            
            if outcomes['objections']:
                objections_str = ', '.join(outcomes['objections'])
                formatted_summary += f"\n• **Objeciones identificadas:** {objections_str}"
            else:
                formatted_summary += f"\n• **Objeciones identificadas:** Ninguna"
            
            # Temas discutidos
            topics = [customer_profile['main_need']]
            if customer_profile['industry'] != 'No especificada':
                topics.append(f"Soluciones para {customer_profile['industry'].lower()}")
            topics_str = ', '.join(topics)
            formatted_summary += f"\n• **Temas discutidos:** {topics_str}"
            
            # Resultado y próximos pasos
            formatted_summary += f"\n\n🎯 **RESULTADO Y PRÓXIMOS PASOS**"
            formatted_summary += f"\n• **Outcome:** {outcomes['outcome_type']}"
            
            if outcomes['meeting_scheduled']:
                formatted_summary += f"\n• **Reunión agendada:** ✅ Sí"
            else:
                formatted_summary += f"\n• **Reunión agendada:** ❌ No"
            
            if outcomes['next_steps']:
                for step in outcomes['next_steps']:
                    formatted_summary += f"\n• **Acción requerida:** {step}"
            else:
                formatted_summary += f"\n• **Acción requerida:** Seguimiento estándar"
            
            # Notas especiales
            special_notes = []
            if outcomes['transferred']:
                special_notes.append("Cliente transferido a ejecutivo humano")
            if customer_profile['urgency'] == 'Alta':
                special_notes.append("URGENTE: Cliente requiere atención prioritaria")
            if outcomes['interest_level'] == 'Alto':
                special_notes.append("Cliente con alto nivel de interés - oportunidad caliente")
            
            if special_notes:
                notes_str = ' | '.join(special_notes)
                formatted_summary += f"\n• **Notas especiales:** {notes_str}"
            
            # Footer
            formatted_summary += f"\n\n---"
            formatted_summary += f"\n📅 **Generado:** {datetime.now().strftime('%d/%m/%Y %H:%M')}"
            formatted_summary += f"\n🤖 **Por:** Mati (Bot de Voz TDX)"
            
            return formatted_summary
            
        except Exception as e:
            logger.error(f"Error formateando resumen: {str(e)}")
            # Si hay error, devolver el resumen original
            return conversation_summary
    
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

    def format_webhook_contact_message(self, contact_data: Dict[str, Any]) -> str:
        """
        Crear mensaje inicial para contacto recibido por webhook
        """
        try:
            contact_name = contact_data.get('name', 'Cliente')
            phone = contact_data.get('phone', 'N/A')
            email = contact_data.get('email', 'No disponible')
            company_name = contact_data.get('company_name', 'No especificada')
            source = contact_data.get('source', 'webhook').replace('_', ' ').title()
            timestamp = datetime.now().strftime('%d/%m/%Y %H:%M')
            
            message = f"""🎯 **NUEVO CONTACTO - {source.upper()}**

📊 **INFORMACIÓN DEL CONTACTO**
• **Nombre:** {contact_name}
• **Teléfono:** {phone}
• **Email:** {email}
• **Empresa:** {company_name}
• **Fuente:** {source}
• **Recibido:** {timestamp}

🚀 **ACCIONES AUTOMÁTICAS INICIADAS**
• ✅ Llamada de voz programada con bot Mati
• ✅ Mensaje proactivo de WhatsApp enviado
• ✅ Conversación creada automáticamente en Chatwoot

📱 **ESTADO DEL PROCESO**
• **Bot de voz:** Intentando contactar al cliente
• **Fallback:** WhatsApp automático si no responde llamada
• **Seguimiento:** Requerido por equipo de ventas

💡 **PRÓXIMOS PASOS RECOMENDADOS**
• Monitorear respuesta del cliente en WhatsApp
• Preparar información adicional según interés mostrado
• Asignar agente humano si el bot requiere transferencia

---
📅 **Generado automáticamente:** {timestamp}
🤖 **Por:** Sistema de Webhook TDX"""

            return message
            
        except Exception as e:
            logger.error(f"Error formateando mensaje de webhook: {str(e)}")
            return f"Nuevo contacto recibido: {contact_data.get('name', 'N/A')} - {contact_data.get('phone', 'N/A')}"

    def create_conversation_for_webhook_contact(self, contact_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Crear conversación en Chatwoot para contacto recibido por webhook
        Usa el inbox específico configurado para webhooks
        """
        try:
            contact_id = contact_data.get('id')
            if not contact_id:
                logger.error("No se encontró ID del contacto en webhook data")
                return {"success": False, "error": "missing_contact_id"}

            logger.info(f"Creando conversación para contacto webhook: {contact_id}")
            
            # Usar inbox específico para webhooks
            target_inbox_id = self.webhook_inbox_id
            logger.info(f"Usando inbox {target_inbox_id} para conversación de webhook")
            
            # 1. Verificar/crear asociación contact-inbox
            source_id = self.get_contact_inbox_source_id_for_inbox(contact_id, target_inbox_id)
            
            if not source_id:
                logger.warning(f"No se pudo obtener source_id para contacto {contact_id} en inbox {target_inbox_id}")
                # Crear source_id temporal para API channels
                source_id = f"webhook-{contact_id}-{int(datetime.now().timestamp())}"
                logger.info(f"Usando source_id temporal: {source_id}")
            
            # 2. Crear conversación
            conversation_payload = {
                'source_id': source_id,
                'inbox_id': int(target_inbox_id),
                'contact_id': contact_id,
                'status': 'open',  # Mantener abierta para seguimiento
                'message': {
                    'content': self.format_webhook_contact_message(contact_data),
                    'message_type': 'outgoing',
                    'private': False
                }
            }
            
            conv_url = f"{self.base_url}/accounts/{self.account_id}/conversations"
            logger.info(f"Creando conversación webhook con payload: {conversation_payload}")
            
            response = requests.post(conv_url, headers=self.headers, json=conversation_payload)
            
            if response.status_code in [200, 201]:
                conversation = response.json()
                conversation_id = conversation.get('id')
                logger.info(f"✅ Conversación webhook creada exitosamente: ID {conversation_id}")
                
                return {
                    "success": True,
                    "conversation_id": conversation_id,
                    "contact_id": contact_id,
                    "inbox_id": target_inbox_id,
                    "source_id": source_id
                }
            else:
                logger.error(f"Error creando conversación webhook: {response.status_code} - {response.text}")
                return {
                    "success": False,
                    "error": f"api_error_{response.status_code}",
                    "details": response.text
                }
                
        except Exception as e:
            logger.error(f"Error en create_conversation_for_webhook_contact: {str(e)}")
            return {
                "success": False,
                "error": str(e)
            }

    def get_contact_inbox_source_id_for_inbox(self, contact_id: int, specific_inbox_id: str) -> Optional[str]:
        """
        Obtiene el source_id del contact_inbox para un inbox específico
        """
        try:
            url = f"{self.base_url}/accounts/{self.account_id}/contacts/{contact_id}/contactable_inboxes"
            response = requests.get(url, headers=self.headers)
            
            if response.status_code == 200:
                inboxes = response.json().get('payload', [])
                
                # Buscar el inbox específico
                for inbox in inboxes:
                    if str(inbox.get('inbox_id')) == str(specific_inbox_id):
                        source_id = inbox.get('source_id')
                        if source_id:
                            logger.info(f"✅ Source ID encontrado para inbox {specific_inbox_id}: {source_id}")
                            return source_id
                
                logger.warning(f"No se encontró source_id para inbox {specific_inbox_id} en contacto {contact_id}")
                return None
                
            else:
                logger.error(f"Error obteniendo contactable inboxes: {response.status_code} - {response.text}")
                return None
                
        except Exception as e:
            logger.error(f"Error en get_contact_inbox_source_id_for_inbox: {str(e)}")
            return None

    def create_webhook_conversation_with_retry(self, contact_data: Dict[str, Any], max_retries: int = 3) -> Dict[str, Any]:
        """
        Crear conversación para webhook con reintentos automáticos
        """
        for attempt in range(max_retries):
            try:
                logger.info(f"Intento {attempt + 1}/{max_retries} de crear conversación webhook")
                
                result = self.create_conversation_for_webhook_contact(contact_data)
                
                if result.get("success"):
                    logger.info(f"✅ Conversación webhook creada exitosamente en intento {attempt + 1}")
                    return result
                
                # Esperar antes del siguiente intento
                if attempt < max_retries - 1:
                    wait_time = (attempt + 1) * 2  # Backoff exponencial
                    logger.info(f"Esperando {wait_time}s antes del siguiente intento...")
                    time.sleep(wait_time)
                    
            except Exception as e:
                logger.error(f"Error en intento {attempt + 1}: {str(e)}")
                if attempt < max_retries - 1:
                    time.sleep((attempt + 1) * 2)
        
        logger.error("❌ Todos los intentos de crear conversación webhook fallaron")
        return {
            "success": False,
            "error": "max_retries_exceeded",
            "attempts": max_retries
        }


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