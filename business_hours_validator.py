"""
Business Hours Validator for TDX
Validates business hours, holidays, and provides scheduling alternatives for Colombia
"""

import os
import logging
from datetime import datetime, timedelta, time
from typing import List, Dict, Any, Optional, Tuple
import requests
from dataclasses import dataclass

logger = logging.getLogger("business_hours_validator")

@dataclass
class TimeSlot:
    """Represents a time slot for scheduling"""
    date: datetime
    time_str: str
    formatted: str
    available: bool = True

class BusinessHoursValidator:
    """Validates business hours and provides scheduling alternatives for Colombia"""
    
    def __init__(self):
        # Business hours: Monday-Friday 8:00AM - 4:00PM Colombia time
        self.start_hour = 8  # 8:00 AM
        self.end_hour = 16   # 4:00 PM (16:00)
        self.slot_duration_minutes = 30  # 30-minute slots
        self.timezone_name = "America/Bogota"
        
        # Cache for holidays to avoid repeated API calls
        self._holidays_cache = {}
        self._cache_expiry = None
        
        # Generate time slots for business hours
        self.business_time_slots = self._generate_business_time_slots()
        
    def _generate_business_time_slots(self) -> List[Tuple[int, str, str]]:
        """Generate all possible time slots during business hours"""
        slots = []
        
        for hour in range(self.start_hour, self.end_hour):
            for minute in [0, 30]:  # Every 30 minutes
                if hour == self.end_hour - 1 and minute == 30:
                    # Don't include 15:30 if end hour is 16:00
                    continue
                    
                time_24h = f"{hour:02d}:{minute:02d}"
                
                # Convert to 12-hour format for display
                time_obj = time(hour, minute)
                time_12h = time_obj.strftime("%I:%M %p")
                
                slots.append((hour * 100 + minute, time_24h, time_12h))
        
        return slots
    
    def _get_colombia_holidays(self, year: int) -> List[str]:
        """Get Colombian holidays for a specific year using a public API"""
        try:
            # Check cache first
            if (year in self._holidays_cache and 
                self._cache_expiry and 
                datetime.now() < self._cache_expiry):
                return self._holidays_cache[year]
            
            # Try public holidays API for Colombia
            url = f"https://date.nager.at/api/v3/PublicHolidays/{year}/CO"
            response = requests.get(url, timeout=10)
            
            if response.status_code == 200:
                holidays_data = response.json()
                holidays = [holiday['date'] for holiday in holidays_data]
                
                # Cache for 24 hours
                self._holidays_cache[year] = holidays
                self._cache_expiry = datetime.now() + timedelta(days=1)
                
                logger.info(f"Loaded {len(holidays)} Colombian holidays for {year}")
                return holidays
            else:
                logger.warning(f"Could not fetch holidays for {year}, using fallback")
                return self._get_fallback_holidays(year)
                
        except Exception as e:
            logger.error(f"Error fetching holidays: {e}")
            return self._get_fallback_holidays(year)
    
    def _get_fallback_holidays(self, year: int) -> List[str]:
        """Fallback holidays for Colombia (major fixed holidays)"""
        return [
            f"{year}-01-01",  # New Year's Day
            f"{year}-05-01",  # Labor Day
            f"{year}-07-20",  # Independence Day
            f"{year}-08-07",  # Battle of Boyacá
            f"{year}-12-08",  # Immaculate Conception
            f"{year}-12-25",  # Christmas Day
        ]
    
    def is_business_day(self, date: datetime) -> bool:
        """Check if a date is a business day (Monday-Friday, not a holiday)"""
        # Check if it's a weekend (Saturday=5, Sunday=6)
        if date.weekday() >= 5:
            return False
        
        # Check if it's a holiday
        date_str = date.strftime("%Y-%m-%d")
        holidays = self._get_colombia_holidays(date.year)
        
        if date_str in holidays:
            return False
            
        return True
    
    def is_business_hour(self, hour: int, minute: int = 0) -> bool:
        """Check if a specific time is within business hours"""
        time_minutes = hour * 60 + minute
        start_minutes = self.start_hour * 60
        end_minutes = self.end_hour * 60
        
        return start_minutes <= time_minutes < end_minutes
    
    def validate_requested_datetime(self, requested_date: str, requested_time: str) -> Dict[str, Any]:
        """Validate a client's requested date and time"""
        try:
            # Parse the requested date
            if isinstance(requested_date, str):
                # Try different date formats
                date_formats = ["%Y-%m-%d", "%d/%m/%Y", "%d-%m-%Y"]
                parsed_date = None
                
                for date_format in date_formats:
                    try:
                        parsed_date = datetime.strptime(requested_date, date_format)
                        break
                    except ValueError:
                        continue
                
                if not parsed_date:
                    return {
                        "valid": False,
                        "reason": "invalid_date_format",
                        "message": "Formato de fecha inválido. Use YYYY-MM-DD, DD/MM/YYYY o DD-MM-YYYY"
                    }
            else:
                parsed_date = requested_date
            
            # Parse the requested time
            if isinstance(requested_time, str):
                # Try different time formats
                time_formats = ["%H:%M", "%I:%M %p", "%H:%M:%S"]
                parsed_time = None
                
                for time_format in time_formats:
                    try:
                        time_obj = datetime.strptime(requested_time, time_format).time()
                        parsed_time = (time_obj.hour, time_obj.minute)
                        break
                    except ValueError:
                        continue
                
                if not parsed_time:
                    return {
                        "valid": False,
                        "reason": "invalid_time_format", 
                        "message": "Formato de hora inválido. Use HH:MM o HH:MM AM/PM"
                    }
            
            # Check if it's a business day
            if not self.is_business_day(parsed_date):
                return {
                    "valid": False,
                    "reason": "not_business_day",
                    "message": "No trabajamos fines de semana ni festivos. Disponible lunes a viernes."
                }
            
            # Check if it's within business hours
            hour, minute = parsed_time
            if not self.is_business_hour(hour, minute):
                return {
                    "valid": False,
                    "reason": "outside_business_hours",
                    "message": f"Horario fuera de atención. Disponible de 8:00 AM a 4:00 PM."
                }
            
            # Check if the datetime is in the future
            requested_datetime = datetime.combine(parsed_date.date(), time(hour, minute))
            if requested_datetime <= datetime.now():
                return {
                    "valid": False,
                    "reason": "past_datetime",
                    "message": "La fecha y hora deben ser futuras."
                }
            
            return {
                "valid": True,
                "datetime": requested_datetime,
                "formatted_date": parsed_date.strftime("%A, %d de %B"),
                "formatted_time": time(hour, minute).strftime("%I:%M %p")
            }
            
        except Exception as e:
            logger.error(f"Error validating datetime: {e}")
            return {
                "valid": False,
                "reason": "validation_error",
                "message": "Error validando fecha y hora. Intente con formato DD/MM/YYYY HH:MM"
            }
    
    def get_same_day_alternatives(self, requested_date: datetime, exclude_times: List[str] = None) -> List[TimeSlot]:
        """Get alternative time slots for the same day"""
        if exclude_times is None:
            exclude_times = []
        
        alternatives = []
        
        # Check if the requested date is a business day
        if not self.is_business_day(requested_date):
            return alternatives
        
        # Generate all time slots for the day
        for time_code, time_24h, time_12h in self.business_time_slots:
            if time_24h in exclude_times:
                continue
            
            slot_datetime = datetime.combine(
                requested_date.date(),
                datetime.strptime(time_24h, "%H:%M").time()
            )
            
            # Only include future slots
            if slot_datetime > datetime.now():
                alternatives.append(TimeSlot(
                    date=slot_datetime,
                    time_str=time_24h,
                    formatted=f"{requested_date.strftime('%A %d/%m')} a las {time_12h}",
                    available=True
                ))
        
        return alternatives[:6]  # Return max 6 alternatives
    
    def get_next_available_slots(self, days_ahead: int = 7, max_slots: int = 6) -> List[TimeSlot]:
        """Get next available slots within the specified days"""
        available_slots = []
        current_date = datetime.now() + timedelta(days=1)  # Start from tomorrow
        end_date = current_date + timedelta(days=days_ahead)
        
        while current_date <= end_date and len(available_slots) < max_slots:
            if self.is_business_day(current_date):
                # Get time slots for this day
                day_slots = self.get_same_day_alternatives(current_date)
                
                # Add up to remaining needed slots
                remaining_slots = max_slots - len(available_slots)
                available_slots.extend(day_slots[:remaining_slots])
            
            current_date += timedelta(days=1)
        
        return available_slots
    
    def format_slots_for_whatsapp(self, slots: List[TimeSlot], max_options: int = 3) -> str:
        """Format time slots for WhatsApp display"""
        if not slots:
            return "⚠️ No hay horarios disponibles en este momento."
        
        message = "📅 *Horarios disponibles:*\n\n"
        
        for i, slot in enumerate(slots[:max_options], 1):
            message += f"{i}. {slot.formatted}\n"
        
        message += f"\n¿Cuál opción te conviene mejor? Responde con el número (1, 2, etc.)"
        
        return message
    
    def get_business_hours_info(self) -> str:
        """Get business hours information for display"""
        return (
            "🕐 *Horario de atención:*\n"
            "📅 Lunes a Viernes\n"
            "⏰ 8:00 AM - 4:00 PM\n"
            "🇨🇴 Hora de Colombia\n\n"
            "❌ No trabajamos sábados, domingos ni festivos"
        )

# Global instance
business_hours = BusinessHoursValidator()