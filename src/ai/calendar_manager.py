"""
Calendar Manager para TDX WhatsApp Bot
Maneja disponibilidad de horarios y opciones de agendamiento
"""

import logging
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional
from dataclasses import dataclass

logger = logging.getLogger("calendar_manager")

@dataclass
class TimeSlot:
    """Slot de tiempo disponible"""
    datetime: datetime
    formatted_date: str
    formatted_time: str
    day_name: str
    option_number: int

class CalendarManager:
    """Gestor de calendario para mostrar opciones de agendamiento"""
    
    def __init__(self):
        # Horarios disponibles durante la semana (9:00 - 17:00)
        self.available_hours = [9, 10, 11, 14, 15, 16, 17]  # Excluye hora de almuerzo 12-13
        
        # Días laborales (Lunes=0, Viernes=4)
        self.work_days = [0, 1, 2, 3, 4]  # Lunes a Viernes
        
        # Horarios ya ocupados (simulado - en producción vendría de calendario real)
        self.blocked_slots = set()
        
    def get_next_available_slots(self, num_options: int = 3, start_date: datetime = None) -> List[TimeSlot]:
        """Obtener próximos slots disponibles"""
        try:
            if start_date is None:
                start_date = datetime.now()
            
            # Comenzar desde mañana si es muy tarde hoy
            if start_date.hour >= 16:
                start_date = start_date.replace(hour=9, minute=0, second=0, microsecond=0) + timedelta(days=1)
            else:
                start_date = start_date.replace(minute=0, second=0, microsecond=0)
            
            available_slots = []
            current_date = start_date
            max_days_ahead = 14  # Buscar hasta 2 semanas adelante
            days_checked = 0
            
            while len(available_slots) < num_options and days_checked < max_days_ahead:
                # Solo días laborales
                if current_date.weekday() in self.work_days:
                    for hour in self.available_hours:
                        slot_datetime = current_date.replace(hour=hour, minute=0)
                        
                        # Verificar que no esté en el pasado
                        if slot_datetime <= datetime.now():
                            continue
                        
                        # Verificar que no esté bloqueado
                        if self._is_slot_blocked(slot_datetime):
                            continue
                        
                        # Crear slot disponible
                        time_slot = TimeSlot(
                            datetime=slot_datetime,
                            formatted_date=self._format_date(slot_datetime),
                            formatted_time=self._format_time(slot_datetime),
                            day_name=self._get_day_name(slot_datetime),
                            option_number=len(available_slots) + 1
                        )
                        
                        available_slots.append(time_slot)
                        
                        if len(available_slots) >= num_options:
                            break
                
                current_date += timedelta(days=1)
                days_checked += 1
            
            return available_slots
            
        except Exception as e:
            logger.error(f"Error getting available slots: {e}")
            return self._generate_fallback_slots()
    
    def _is_slot_blocked(self, slot_datetime: datetime) -> bool:
        """Verificar si un slot está bloqueado"""
        # En producción, esto consultaría el calendario real
        # Por ahora, simulamos algunos slots ocupados
        slot_key = slot_datetime.strftime('%Y-%m-%d_%H')
        return slot_key in self.blocked_slots
    
    def _format_date(self, dt: datetime) -> str:
        """Formatear fecha legible"""
        today = datetime.now().date()
        tomorrow = today + timedelta(days=1)
        
        if dt.date() == today:
            return "Hoy"
        elif dt.date() == tomorrow:
            return "Mañana"
        else:
            months = ['Enero', 'Febrero', 'Marzo', 'Abril', 'Mayo', 'Junio',
                     'Julio', 'Agosto', 'Septiembre', 'Octubre', 'Noviembre', 'Diciembre']
            return f"{dt.day} de {months[dt.month-1]}"
    
    def _format_time(self, dt: datetime) -> str:
        """Formatear hora legible"""
        if dt.hour < 12:
            return f"{dt.hour}:00 AM"
        elif dt.hour == 12:
            return "12:00 PM"
        else:
            return f"{dt.hour - 12}:00 PM"
    
    def _get_day_name(self, dt: datetime) -> str:
        """Obtener nombre del día"""
        days = ['Lunes', 'Martes', 'Miércoles', 'Jueves', 'Viernes', 'Sábado', 'Domingo']
        return days[dt.weekday()]
    
    def _generate_fallback_slots(self) -> List[TimeSlot]:
        """Generar slots de respaldo si hay error"""
        try:
            base_time = datetime.now().replace(hour=10, minute=0, second=0, microsecond=0)
            if base_time <= datetime.now():
                base_time += timedelta(days=1)
            
            fallback_slots = []
            for i in range(3):
                slot_time = base_time + timedelta(days=i)
                # Ajustar si cae en fin de semana
                while slot_time.weekday() > 4:  # Sábado o Domingo
                    slot_time += timedelta(days=1)
                
                time_slot = TimeSlot(
                    datetime=slot_time,
                    formatted_date=self._format_date(slot_time),
                    formatted_time=self._format_time(slot_time),
                    day_name=self._get_day_name(slot_time),
                    option_number=i + 1
                )
                fallback_slots.append(time_slot)
            
            return fallback_slots
            
        except Exception as e:
            logger.error(f"Error generating fallback slots: {e}")
            return []
    
    def reserve_slot(self, slot_datetime: datetime, client_info: Dict[str, Any]) -> bool:
        """Reservar un slot específico"""
        try:
            slot_key = slot_datetime.strftime('%Y-%m-%d_%H')
            
            # En producción, esto guardaría en el calendario real
            self.blocked_slots.add(slot_key)
            
            logger.info(f"Slot reservado: {slot_datetime} para {client_info.get('name', 'Cliente')}")
            return True
            
        except Exception as e:
            logger.error(f"Error reserving slot: {e}")
            return False
    
    def format_options_message(self, slots: List[TimeSlot], client_name: str, service: str = "automatización") -> str:
        """Formatear mensaje con opciones de agendamiento"""
        try:
            if not slots:
                return f"Lo siento {client_name}, no hay horarios disponibles en este momento. Te contactaremos para coordinar."
            
            message = f"¡Perfecto {client_name}! 🗓️\n\n"
            message += f"Tengo estos horarios disponibles para tu demo de {service}:\n\n"
            
            for slot in slots:
                message += f"*Opción {slot.option_number}:* {slot.day_name} {slot.formatted_date} a las {slot.formatted_time}\n"
            
            message += f"\n¿Cuál opción prefieres? Solo responde con el número (1, 2 o 3) 😊"
            
            return message
            
        except Exception as e:
            logger.error(f"Error formatting options message: {e}")
            return f"{client_name}, tengo horarios disponibles. Te contactaré para coordinar la agenda."
    
    def parse_time_selection(self, user_message: str, available_slots: List[TimeSlot]) -> Optional[TimeSlot]:
        """Parsear selección del usuario"""
        try:
            message_lower = user_message.lower().strip()
            
            # Buscar números en el mensaje
            import re
            numbers = re.findall(r'\b([123])\b', message_lower)
            
            if numbers:
                selected_number = int(numbers[0])
                if 1 <= selected_number <= len(available_slots):
                    return available_slots[selected_number - 1]
            
            # Buscar palabras clave
            if 'primera' in message_lower or 'primero' in message_lower or '1' in message_lower:
                return available_slots[0] if available_slots else None
            elif 'segunda' in message_lower or 'segundo' in message_lower or '2' in message_lower:
                return available_slots[1] if len(available_slots) > 1 else None
            elif 'tercera' in message_lower or 'tercero' in message_lower or '3' in message_lower:
                return available_slots[2] if len(available_slots) > 2 else None
            
            return None
            
        except Exception as e:
            logger.error(f"Error parsing time selection: {e}")
            return None
    
    def format_confirmation_message(self, slot: TimeSlot, client_info: Dict[str, Any]) -> str:
        """Formatear mensaje de confirmación"""
        try:
            client_name = client_info.get('name', 'Cliente')
            client_email = client_info.get('email', '')
            service = client_info.get('service_interest', 'automatización')
            
            message = f"¡Excelente {client_name}! ✅\n\n"
            message += f"*Demo agendada:*\n"
            message += f"📅 {slot.day_name} {slot.formatted_date}\n"
            message += f"🕐 {slot.formatted_time}\n"
            message += f"💼 Tema: {service}\n\n"
            
            if client_email:
                message += f"Te enviaré la invitación a {client_email}\n\n"
            
            message += "Nos vemos pronto. ¡Gracias por tu interés en TDX! 🚀"
            
            return message
            
        except Exception as e:
            logger.error(f"Error formatting confirmation message: {e}")
            return f"¡Perfecto! Tu reunión está agendada. Te contactaremos pronto."

# Instancia global
calendar_manager = CalendarManager()