"""
Telnyx Custom Functions Bridge
Handles webhook calls from Telnyx AI Assistant for custom business logic
Reuses existing function implementations from agent.py
"""
import json
import logging
from typing import Dict, Any
from fastapi import Request, HTTPException
from datetime import datetime, timedelta
import re

from microsoft_graph_client import MicrosoftGraphClient

logger = logging.getLogger(__name__)

# Initialize Microsoft Graph client for meeting scheduling
ms_graph_client = MicrosoftGraphClient()

async def handle_transfer_function(request: Request) -> Dict[str, Any]:
    """
    Handle transfer_call function from Telnyx AI Assistant
    Reuses the transfer logic from the original TDXSDRBot
    """
    try:
        payload = await request.json()
        
        # Extract parameters from Telnyx AI Assistant
        phone_number = payload.get("phone_number")
        reason = payload.get("reason", "Solicitud de transferencia del cliente")
        
        # Default transfer number for TDX
        default_transfer_number = "+573153041548"  # TDX main sales line
        
        # Use provided number or default
        transfer_number = phone_number if phone_number else default_transfer_number
        
        # Validate Colombian phone number format
        if not is_valid_colombian_number(transfer_number):
            return {
                "success": False,
                "message": "El número proporcionado no es válido. Te voy a transferir con nuestro equipo principal.",
                "action": "transfer_to_default",
                "transfer_number": default_transfer_number
            }
        
        logger.info(f"Processing transfer request to {transfer_number}, reason: {reason}")
        
        # Return instructions for Telnyx AI Assistant
        return {
            "success": True,
            "message": f"Perfecto, te voy a transferir ahora con un especialista. En un momento te atenderán al {transfer_number}. ¡Que tengas un excelente día!",
            "action": "transfer",
            "transfer_number": transfer_number,
            "reason": reason
        }
        
    except Exception as e:
        logger.error(f"Error handling transfer function: {str(e)}")
        return {
            "success": False,
            "message": "Disculpa, tengo un problema técnico. Permíteme transferirte directamente con nuestro equipo.",
            "action": "transfer_to_default", 
            "transfer_number": "+573153041548"
        }

async def handle_schedule_function(request: Request) -> Dict[str, Any]:
    """
    Handle schedule_meeting function from Telnyx AI Assistant
    Reuses the Microsoft Graph integration from the original implementation
    """
    try:
        payload = await request.json()
        
        # Extract meeting parameters
        email = payload.get("email", "").strip()
        date = payload.get("date", "").strip()
        time = payload.get("time", "").strip()
        duration_minutes = payload.get("duration_minutes", 30)
        attendee_name = payload.get("attendee_name", "Prospecto")
        company_name = payload.get("company_name", "")
        
        # Validate required parameters
        if not email:
            return {
                "success": False,
                "message": "Necesito tu email para enviarte la invitación de la reunión. ¿Podrías proporcionármelo?",
                "action": "request_email"
            }
        
        if not is_valid_email(email):
            return {
                "success": False,
                "message": "El email que proporcionaste no parece válido. ¿Podrías verificarlo?",
                "action": "request_valid_email"
            }
        
        if not date or not time:
            return {
                "success": False,
                "message": "Necesito que me confirmes la fecha y hora para la reunión. ¿Qué día y a qué hora te conviene?",
                "action": "request_datetime"
            }
        
        # Parse and validate date/time
        meeting_datetime = parse_datetime(date, time)
        if not meeting_datetime:
            return {
                "success": False,
                "message": "No pude entender la fecha y hora. ¿Podrías decirme algo como 'mañana a las 2 de la tarde' o 'el viernes a las 10 de la mañana'?",
                "action": "request_clear_datetime"
            }
        
        # Check if the datetime is in the future
        if meeting_datetime <= datetime.now():
            return {
                "success": False,
                "message": "La fecha y hora que mencionaste ya pasó. ¿Podrías darme una fecha futura?",
                "action": "request_future_datetime"
            }
        
        # Create meeting using Microsoft Graph
        meeting_result = await create_teams_meeting(
            email=email,
            meeting_datetime=meeting_datetime,
            duration_minutes=duration_minutes,
            attendee_name=attendee_name,
            company_name=company_name
        )
        
        if meeting_result["success"]:
            formatted_datetime = meeting_datetime.strftime("%A %d de %B a las %I:%M %p")
            
            return {
                "success": True,
                "message": f"¡Perfecto! He programado tu reunión para el {formatted_datetime}. Te envié la invitación a {email} con todos los detalles y el link de Teams. ¡Nos vemos pronto!",
                "action": "meeting_scheduled",
                "meeting_link": meeting_result.get("meeting_link"),
                "meeting_id": meeting_result.get("meeting_id"),
                "datetime": meeting_datetime.isoformat()
            }
        else:
            return {
                "success": False,
                "message": "Tengo un problema técnico para programar la reunión en este momento. ¿Te parece si te transfiero con nuestro equipo para que te ayuden directamente?",
                "action": "offer_transfer",
                "error": meeting_result.get("error")
            }
        
    except Exception as e:
        logger.error(f"Error handling schedule function: {str(e)}")
        return {
            "success": False,
            "message": "Disculpa, tengo un problema técnico. ¿Te parece si te transfiero con nuestro equipo para que te ayuden a programar la reunión?",
            "action": "offer_transfer_on_error"
        }

async def handle_collect_email_function(request: Request) -> Dict[str, Any]:
    """
    Handle collect_email function from Telnyx AI Assistant
    Simple email validation and collection
    """
    try:
        payload = await request.json()
        email = payload.get("email", "").strip()
        
        if not email:
            return {
                "success": False,
                "message": "No recibí tu email. ¿Podrías repetírmelo por favor?",
                "action": "request_email_again"
            }
        
        if not is_valid_email(email):
            return {
                "success": False,
                "message": "El email que proporcionaste no parece válido. ¿Podrías verificarlo? Por ejemplo: nombre@empresa.com",
                "action": "request_valid_email"
            }
        
        return {
            "success": True,
            "message": f"Perfecto, tengo tu email: {email}. Ya puedo enviarte información o programar una reunión.",
            "action": "email_collected",
            "email": email
        }
        
    except Exception as e:
        logger.error(f"Error handling collect email function: {str(e)}")
        return {
            "success": False,
            "message": "Tengo un problema técnico. ¿Podrías repetirme tu email?",
            "action": "technical_error"
        }

# Utility functions

def is_valid_colombian_number(phone_number: str) -> bool:
    """
    Validate Colombian phone number format
    """
    if not phone_number:
        return False
    
    # Remove spaces and special characters
    clean_number = re.sub(r'[^\d+]', '', phone_number)
    
    # Colombian mobile numbers: +57 3XX XXXXXXX or +57 3XXXXXXXXX  
    # Colombian landline: +57 X XXXXXXX or +57 XXXXXXXX
    colombian_pattern = r'^\+57[1-9]\d{7,9}$'
    
    return bool(re.match(colombian_pattern, clean_number))

def is_valid_email(email: str) -> bool:
    """
    Basic email validation
    """
    if not email:
        return False
    
    email_pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return bool(re.match(email_pattern, email))

def parse_datetime(date_str: str, time_str: str) -> datetime:
    """
    Parse date and time strings to datetime object
    Handles common Spanish date/time formats
    """
    try:
        # Combine date and time
        datetime_str = f"{date_str} {time_str}".lower()
        
        # Get current date for relative references
        now = datetime.now()
        
        # Handle relative dates
        if "mañana" in datetime_str:
            target_date = now + timedelta(days=1)
        elif "hoy" in datetime_str:
            target_date = now
        elif "pasado mañana" in datetime_str:
            target_date = now + timedelta(days=2)
        else:
            # Try to parse absolute date
            # This is a simplified version - in production, use more robust date parsing
            target_date = now + timedelta(days=1)  # Default to tomorrow
        
        # Extract time
        time_match = re.search(r'(\d{1,2}):?(\d{0,2})\s*(am|pm|de la mañana|de la tarde|de la noche)?', datetime_str)
        
        if time_match:
            hour = int(time_match.group(1))
            minute = int(time_match.group(2)) if time_match.group(2) else 0
            period = time_match.group(3) or ""
            
            # Convert to 24-hour format
            if "pm" in period or "de la tarde" in period or "de la noche" in period:
                if hour != 12:
                    hour += 12
            elif "am" in period or "de la mañana" in period:
                if hour == 12:
                    hour = 0
            
            return target_date.replace(hour=hour, minute=minute, second=0, microsecond=0)
        
        # Default time if no specific time found
        return target_date.replace(hour=14, minute=0, second=0, microsecond=0)  # 2 PM default
        
    except Exception as e:
        logger.error(f"Error parsing datetime: {str(e)}")
        return None

async def create_teams_meeting(email: str, meeting_datetime: datetime, duration_minutes: int, 
                             attendee_name: str, company_name: str) -> Dict[str, Any]:
    """
    Create a Teams meeting using Microsoft Graph
    Reuses the existing Microsoft Graph integration
    """
    try:
        # Build meeting details
        subject = f"Reunión TDX - {company_name}" if company_name else "Reunión TDX - Transformación Digital"
        
        body_content = f"""
Hola {attendee_name},

¡Gracias por tu interés en las soluciones de transformación digital de TDX!

En esta reunión conversaremos sobre:
• Tus necesidades específicas de transformación digital
• Nuestras soluciones y casos de éxito
• Cómo podemos ayudar a {company_name if company_name else 'tu empresa'} a crecer

Nos vemos en la reunión.

Saludos,
Equipo TDX
"""
        
        end_datetime = meeting_datetime + timedelta(minutes=duration_minutes)
        
        # Use the existing Microsoft Graph client
        result = await ms_graph_client.create_teams_meeting(
            subject=subject,
            start_datetime=meeting_datetime,
            end_datetime=end_datetime,
            attendee_email=email,
            body=body_content
        )
        
        return {
            "success": True,
            "meeting_link": result.get("onlineMeeting", {}).get("joinUrl"),
            "meeting_id": result.get("id")
        }
        
    except Exception as e:
        logger.error(f"Error creating Teams meeting: {str(e)}")
        return {
            "success": False,
            "error": str(e)
        }