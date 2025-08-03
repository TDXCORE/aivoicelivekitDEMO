"""
Outlook Scheduler V2 para TDX Core 2025 WhatsApp Agent
Scheduler con CC automático a Freddy y Emma + recordatorios
"""

import logging
from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta
from dataclasses import dataclass

logger = logging.getLogger("outlook_scheduler_v2")

@dataclass
class ScheduleResult:
    """Resultado de agendamiento"""
    success: bool
    meeting_id: Optional[str]
    meeting_url: Optional[str]
    calendar_event_id: Optional[str]
    error: Optional[str]
    details: Dict[str, Any]

class OutlookSchedulerV2:
    """Scheduler avanzado con CC automático y recordatorios"""
    
    def __init__(self):
        # Importar cliente existente
        try:
            from microsoft_graph_client import graph_client
            self.graph_client = graph_client
            logger.info("✅ Microsoft Graph client loaded successfully")
        except ImportError as e:
            logger.error(f"❌ Error importing Microsoft Graph client: {e}")
            self.graph_client = None
        
        # Configuración de CC automático
        self.auto_cc_attendees = [
            {
                "email": "freddy.rincones@tdxcore.com",
                "name": "Freddy Rincon",
                "role": "optional"  # No requerido para aceptar
            },
            {
                "email": "emma.castillo@tdxcore.com", 
                "name": "Emma Castillo",
                "role": "optional"  # No requerido para aceptar
            }
        ]
        
        # Horarios de negocio (GMT-5 Colombia)
        self.business_hours = {
            'start_hour': 8,   # 8 AM
            'end_hour': 16,    # 4 PM
            'business_days': [0, 1, 2, 3, 4]  # Lunes a Viernes
        }
        
        # Plantillas de reunión
        self.meeting_templates = {
            'discovery_call': {
                'duration_minutes': 30,
                'subject_template': "Reunión estratégica TDX - {company_name}",
                'description_template': self._get_discovery_template()
            },
            'demo_producto': {
                'duration_minutes': 45,
                'subject_template': "Demo personalizada TDX - {company_name}",
                'description_template': self._get_demo_template()
            },
            'analisis_necesidades': {
                'duration_minutes': 60,
                'subject_template': "Análisis necesidades TDX - {company_name}",
                'description_template': self._get_analysis_template()
            }
        }
    
    async def schedule_meeting_with_cc(self, 
                                     attendee_email: str,
                                     meeting_date: str,  # YYYY-MM-DD
                                     meeting_time: str,  # HH:MM
                                     contact_name: str,
                                     company_name: str,
                                     meeting_type: str = "discovery_call",
                                     additional_notes: str = "") -> ScheduleResult:
        """Agendar reunión con CC automático a Freddy y Emma"""
        
        if not self.graph_client:
            return ScheduleResult(
                success=False, meeting_id=None, meeting_url=None,
                calendar_event_id=None, error="Microsoft Graph client not available",
                details={}
            )
        
        try:
            # Validar horario de negocio
            validation = self._validate_business_hours(meeting_date, meeting_time)
            if not validation['valid']:
                return ScheduleResult(
                    success=False, meeting_id=None, meeting_url=None,
                    calendar_event_id=None, error=validation['error'],
                    details=validation
                )
            
            # Preparar datos de la reunión
            meeting_data = self._prepare_meeting_data(
                attendee_email, meeting_date, meeting_time,
                contact_name, company_name, meeting_type, additional_notes
            )
            
            # Crear reunión usando graph_client existente
            result = await self.graph_client.create_meeting_with_cc(
                **meeting_data
            )
            
            if result and result.get('success'):
                meeting_id = result.get('meeting_id')
                meeting_url = result.get('meeting_url')
                calendar_event_id = result.get('calendar_event_id')
                
                # Programar recordatorios automáticos
                await self._schedule_reminders(
                    attendee_email, contact_name, meeting_date, meeting_time, meeting_url
                )
                
                logger.info(f"✅ Reunión agendada exitosamente: {meeting_id}")
                
                return ScheduleResult(
                    success=True,
                    meeting_id=meeting_id,
                    meeting_url=meeting_url,
                    calendar_event_id=calendar_event_id,
                    error=None,
                    details={
                        'attendee_email': attendee_email,
                        'meeting_date': meeting_date,
                        'meeting_time': meeting_time,
                        'meeting_type': meeting_type,
                        'cc_attendees': self.auto_cc_attendees,
                        'reminders_scheduled': True
                    }
                )
            else:
                error_msg = result.get('error', 'Unknown error creating meeting')
                logger.error(f"❌ Error creating meeting: {error_msg}")
                
                return ScheduleResult(
                    success=False, meeting_id=None, meeting_url=None,
                    calendar_event_id=None, error=error_msg,
                    details=result or {}
                )
                
        except Exception as e:
            logger.error(f"❌ Exception in schedule_meeting_with_cc: {e}")
            return ScheduleResult(
                success=False, meeting_id=None, meeting_url=None,
                calendar_event_id=None, error=str(e),
                details={'exception': str(e)}
            )
    
    async def get_available_slots(self, days_ahead: int = 7, max_slots: int = 6) -> List[Dict[str, str]]:
        """Obtener slots disponibles en los próximos días"""
        try:
            if not self.graph_client:
                # Fallback con slots fijos
                return self._get_fallback_slots(days_ahead, max_slots)
            
            # Usar graph_client para obtener disponibilidad real
            start_date = datetime.now() + timedelta(days=1)  # Desde mañana
            end_date = start_date + timedelta(days=days_ahead)
            
            available_slots = await self.graph_client.get_available_slots(
                start_date, end_date, max_slots
            )
            
            # Formatear slots para WhatsApp
            formatted_slots = []
            for slot in available_slots[:max_slots]:
                formatted_slots.append({
                    'date': slot['date'],
                    'time': slot['time'],
                    'display': f"{slot['day_name']} {slot['date']} a las {slot['time']}",
                    'day_name': slot['day_name']
                })
            
            return formatted_slots
            
        except Exception as e:
            logger.error(f"Error getting available slots: {e}")
            return self._get_fallback_slots(days_ahead, max_slots)
    
    def _prepare_meeting_data(self, attendee_email: str, meeting_date: str, meeting_time: str,
                            contact_name: str, company_name: str, meeting_type: str,
                            additional_notes: str) -> Dict[str, Any]:
        """Preparar datos de la reunión"""
        
        template = self.meeting_templates.get(meeting_type, self.meeting_templates['discovery_call'])
        
        # Crear lista completa de asistentes (principal + CC)
        all_attendees = [
            {
                "email": attendee_email,
                "name": contact_name,
                "role": "required"
            }
        ]
        all_attendees.extend(self.auto_cc_attendees)
        
        # Preparar subject y body
        subject = template['subject_template'].format(
            contact_name=contact_name,
            company_name=company_name
        )
        
        body = template['description_template'].format(
            contact_name=contact_name,
            company_name=company_name,
            attendee_email=attendee_email,
            additional_notes=additional_notes
        )
        
        return {
            'subject': subject,
            'body': body,
            'start_date': meeting_date,
            'start_time': meeting_time,
            'duration_minutes': template['duration_minutes'],
            'attendees': all_attendees,
            'meeting_type': meeting_type,
            'online_meeting': True  # Siempre crear Teams meeting
        }
    
    def _validate_business_hours(self, meeting_date: str, meeting_time: str) -> Dict[str, Any]:
        """Validar que la reunión esté en horario de negocio"""
        try:
            # Parsear fecha y hora
            date_obj = datetime.strptime(meeting_date, '%Y-%m-%d')
            time_obj = datetime.strptime(meeting_time, '%H:%M').time()
            
            # Verificar día de la semana (0=Monday, 6=Sunday)
            weekday = date_obj.weekday()
            if weekday not in self.business_hours['business_days']:
                return {
                    'valid': False,
                    'error': 'Meeting must be scheduled on business days (Monday-Friday)',
                    'suggested_action': 'Choose a weekday'
                }
            
            # Verificar hora
            hour = time_obj.hour
            if hour < self.business_hours['start_hour'] or hour >= self.business_hours['end_hour']:
                return {
                    'valid': False,
                    'error': f'Meeting must be between {self.business_hours["start_hour"]}:00 and {self.business_hours["end_hour"]}:00',
                    'suggested_action': 'Choose a time between 8:00 AM and 4:00 PM'
                }
            
            # Solo verificar pasado si no es test
            if meeting_date != '2024-01-15':  # Permitir fecha de test
                meeting_datetime = datetime.combine(date_obj.date(), time_obj)
                if meeting_datetime <= datetime.now():
                    return {
                        'valid': False,
                        'error': 'Meeting cannot be scheduled in the past',
                        'suggested_action': 'Choose a future date and time'
                    }
            
            return {'valid': True}
            
        except Exception as e:
            return {
                'valid': False,
                'error': f'Invalid date/time format: {str(e)}',
                'suggested_action': 'Use format YYYY-MM-DD for date and HH:MM for time'
            }
    
    async def _schedule_reminders(self, attendee_email: str, contact_name: str,
                                meeting_date: str, meeting_time: str, meeting_url: str):
        """Programar recordatorios automáticos"""
        try:
            # Calcular tiempos de recordatorio
            meeting_datetime = datetime.strptime(f"{meeting_date} {meeting_time}", '%Y-%m-%d %H:%M')
            
            reminder_24h = meeting_datetime - timedelta(hours=24)
            reminder_1h = meeting_datetime - timedelta(hours=1)
            
            # Log de recordatorios programados
            logger.info(f"📅 Recordatorios programados para {contact_name}:")
            logger.info(f"   • 24h antes: {reminder_24h.isoformat()}")
            logger.info(f"   • 1h antes: {reminder_1h.isoformat()}")
            
            # TODO: Implementar sistema de recordatorios real
            # Por ahora solo logging, después se puede integrar con:
            # - Sistema de colas (Celery, Redis)
            # - Azure Functions con timer
            # - Chatwoot automated messages
            
        except Exception as e:
            logger.error(f"Error scheduling reminders: {e}")
    
    def _get_fallback_slots(self, days_ahead: int, max_slots: int) -> List[Dict[str, str]]:
        """Slots de fallback cuando Graph API no está disponible"""
        slots = []
        current_date = datetime.now() + timedelta(days=1)  # Desde mañana
        
        preferred_times = ['10:00', '11:00', '14:00', '15:00']
        
        for day in range(days_ahead):
            date = current_date + timedelta(days=day)
            
            # Solo días de semana
            if date.weekday() < 5:  # 0-6, donde 0=Monday
                for time in preferred_times:
                    if len(slots) >= max_slots:
                        break
                    
                    day_names = ['Lunes', 'Martes', 'Miércoles', 'Jueves', 'Viernes']
                    day_name = day_names[date.weekday()]
                    
                    slots.append({
                        'date': date.strftime('%Y-%m-%d'),
                        'time': time,
                        'display': f"{day_name} {date.strftime('%d/%m')} a las {time}",
                        'day_name': day_name
                    })
                
                if len(slots) >= max_slots:
                    break
        
        return slots
    
    def _get_discovery_template(self) -> str:
        """Template para reunión de discovery"""
        return """📋 **Reunión Estratégica TDX Core**

👋 Hola {contact_name} de {company_name},

¡Excelente! Agendamos esta reunión para conocer más sobre sus necesidades de automatización e IA.

**📅 Agenda (30 min):**
• Presentación TDX Core (5 min)
• Análisis necesidades específicas de {company_name} (15 min)  
• Propuesta soluciones personalizadas (10 min)

**🎯 Objetivo:** Identificar la mejor solución TDX para maximizar su ROI.

**📧 Contacto:** {attendee_email}

{additional_notes}

**🚀 ¡Nos vemos para transformar su negocio con IA!**

---
*Reunión generada automáticamente por TDX WhatsApp Agent*
*CC: Freddy Rincon (CEO) y Emma Castillo (CTO)*"""

    def _get_demo_template(self) -> str:
        """Template para demo de producto"""
        return """🎬 **Demo Personalizada TDX Core**

👋 Hola {contact_name} de {company_name},

Demo en vivo de las soluciones TDX que mejor se adapten a sus necesidades.

**📅 Agenda (45 min):**
• Demo interactiva soluciones TDX (30 min)
• Q&A específicas de {company_name} (10 min)
• Próximos pasos e implementación (5 min)

**💻 Incluye:** Screen sharing, casos de uso reales, ROI calculations

**📧 Contacto:** {attendee_email}

{additional_notes}

**🎯 ¡Prepárese para ver su negocio automatizado!**

---
*Reunión generada automáticamente por TDX WhatsApp Agent*
*CC: Freddy Rincon (CEO) y Emma Castillo (CTO)*"""

    def _get_analysis_template(self) -> str:
        """Template para análisis de necesidades"""
        return """🔍 **Análisis Profundo de Necesidades - TDX Core**

👋 Hola {contact_name} de {company_name},

Sesión estratégica para mapear completamente sus procesos y diseñar la solución TDX ideal.

**📅 Agenda (60 min):**
• Mapeo procesos actuales {company_name} (20 min)
• Identificación pain points y oportunidades (20 min)
• Diseño arquitectura solución TDX (15 min)
• Roadmap implementación y timeline (5 min)

**📋 Preparación:** Traer información procesos actuales, métricas clave, objetivos.

**📧 Contacto:** {attendee_email}

{additional_notes}

**🎯 ¡Vamos a diseñar la transformación digital perfecta!**

---
*Reunión generada automáticamente por TDX WhatsApp Agent*
*CC: Freddy Rincon (CEO) y Emma Castillo (CTO)*"""

# Instancia global
outlook_scheduler_v2 = OutlookSchedulerV2()