"""
Micro Value Injector para TDX WhatsApp Bot
Genera respuestas ultra cortas con micro-valor específico SIN PRECIOS
"""

import json
import logging
from typing import Dict, Optional, Any
from datetime import datetime

logger = logging.getLogger("micro_value_injector")

class MicroValueInjector:
    """Inyector de micro-valor ultra conciso SIN PRECIOS"""
    
    def __init__(self):
        self.responses = self._load_responses()
        self.price_response = "Precios en reunión según necesidades."
        
    def _load_responses(self) -> Dict[str, Dict[str, str]]:
        """Cargar respuestas ultra cortas por servicio e industria"""
        return {
            'AI_CHATBOT': {
                'general': "¡Perfecto! Reduce 70% tiempo. ¿Cuántos usuarios?",
                'salud': "¡Ideal! Agenda automático. ¿Cuántos pacientes?",
                'ecommerce': "¡Genial! 40% más ventas. ¿Cuántos productos?",
                'educacion': "¡Perfecto! Resuelve dudas 24/7. ¿Cuántos estudiantes?",
                'restaurante': "¡Ideal! Pedidos automáticos. ¿Cuántas mesas?",
                'inmobiliaria': "¡Genial! Califica leads automático. ¿Cuántas propiedades?"
            },
            'AI_VOICE': {
                'general': "¡Excelente! 60% mejor conversión. ¿Ventas?",
                'fintech': "¡Perfecto! Recupera 80% cartera. ¿Cuántos deudores?",
                'salud': "¡Ideal! Recordatorios automáticos. ¿Cuántos pacientes?",
                'ecommerce': "¡Genial! Ventas telefónicas 10x. ¿Cuántos leads?",
                'inmobiliaria': "¡Perfecto! Prospección automática. ¿Cuántos leads?"
            },
            'AI_ASSISTANT_WHATSAPP': {
                'general': "¡Genial! Automatiza WhatsApp 95%. ¿Para qué?",
                'ecommerce': "¡Perfecto! Tracking automático. ¿Cuántos pedidos?",
                'salud': "¡Ideal! Confirmaciones automáticas. ¿Cuántas citas?",
                'restaurante': "¡Genial! Delivery automático. ¿Cuántos pedidos?",
                'inmobiliaria': "¡Perfecto! Seguimiento leads automático. ¿Cuántos?"
            },
            'AI_VIDEO': {
                'general': "¡Genial! Avatares súper realistas. ¿Para qué?",
                'educacion': "¡Perfecto! Onboarding automático. ¿Cuántos empleados?",
                'salud': "¡Ideal! Explicaciones personalizadas. ¿Qué procedimientos?",
                'ecommerce': "¡Genial! Videos productos automáticos. ¿Cuántos?"
            },
            'WEB_STARTER': {
                'general': "¡Genial! Vitrina 24/7. ¿Qué negocio?",
                'restaurante': "¡Perfecto! Menú digital. ¿Sucursales?",
                'salud': "¡Ideal! Servicios online. ¿Especialidades?",
                'educacion': "¡Genial! Academia online. ¿Qué cursos?",
                'inmobiliaria': "¡Perfecto! Propiedades online. ¿Cuántas?"
            },
            'WEB_BUSINESS': {
                'general': "¡Excelente! Web + chat automático. ¿Qué vendes?",
                'salud': "¡Perfecto! Citas + chat. ¿Especialidades?",
                'educacion': "¡Ideal! Cursos + soporte. ¿Qué enseñas?",
                'inmobiliaria': "¡Genial! Leads automáticos. ¿Qué zona?"
            },
            'WEB_ECOMMERCE': {
                'general': "¡Excelente! Ventas 24/7 automáticas. ¿Cuántos productos?",
                'restaurante': "¡Perfecto! Delivery completo. ¿Qué cocinas?",
                'gimnasio': "¡Ideal! Membresías online. ¿Cuántos miembros?",
                'ecommerce': "¡Genial! Tienda completa. ¿Qué vendes?"
            },
            'MVP': {
                'general': "¡Genial! MVP en 15 días. ¿Qué idea?",
                'fintech': "¡Perfecto! Demo inversionistas. ¿Qué problema resuelves?",
                'startup': "¡Ideal! Validación rápida. ¿Cuál hipótesis?",
                'ecommerce': "¡Genial! Marketplace express. ¿Qué mercado?"
            },
            'WHATSAPP_API': {
                'general': "¡Excelente! API oficial Meta. ¿Para qué?",
                'ecommerce': "¡Perfecto! Tracking tiempo real. ¿Cuántos pedidos?",
                'salud': "¡Ideal! Recordatorios oficiales. ¿Cuántos pacientes?",
                'educacion': "¡Genial! Comunicación masiva. ¿Cuántos estudiantes?"
            },
            'SEO': {
                'general': "¡Genial! 10x más visibilidad. ¿Qué vendes?",
                'restaurante': "¡Perfecto! Google Maps automático. ¿Dónde están?",
                'salud': "¡Ideal! Pacientes por Google. ¿Qué especialidad?",
                'inmobiliaria': "¡Genial! Leads Google. ¿Qué zona?"
            }
        }
    
    def get_micro_value(self, service: str, industry: str = 'general', 
                       context: Optional[str] = None) -> str:
        """Obtener micro-valor ultra corto sin precios"""
        try:
            service_responses = self.responses.get(service, {})
            
            # Buscar respuesta específica por industria
            response = service_responses.get(industry)
            
            # Si no hay respuesta específica, usar general
            if not response:
                response = service_responses.get('general')
            
            # Fallback si no existe el servicio
            if not response:
                response = f"¡Perfecto! {service} ideal. ¿Para qué?"
            
            logger.info(f"Micro-valor generado: {service} + {industry} = {response}")
            return response
            
        except Exception as e:
            logger.error(f"Error generando micro-valor: {e}")
            return "¡Perfecto para tu caso! ¿Nombre y email?"
    
    def get_follow_up_question(self, service: str, industry: str = 'general') -> str:
        """Generar pregunta de seguimiento específica"""
        follow_ups = {
            'AI_CHATBOT': {
                'general': "¿Cuántos usuarios?",
                'salud': "¿Cuántos pacientes?",
                'ecommerce': "¿Cuántos productos?",
                'educacion': "¿Cuántos estudiantes?"
            },
            'AI_VOICE': {
                'general': "¿Ventas o soporte?",
                'fintech': "¿Cuántos deudores?",
                'ecommerce': "¿Cuántos leads?"
            },
            'WEB_STARTER': {
                'general': "¿Qué negocio?",
                'restaurante': "¿Sucursales?",
                'salud': "¿Especialidades?"
            }
        }
        
        service_questions = follow_ups.get(service, {})
        return service_questions.get(industry, service_questions.get('general', "¿Para qué?"))
    
    def get_price_response(self) -> str:
        """Respuesta estándar para consultas de precio"""
        return self.price_response
    
    def get_validation_response(self, emotion: str = 'positive') -> str:
        """Respuestas de validación emocional ultra cortas"""
        validations = {
            'positive': ["¡Perfecto!", "¡Genial!", "¡Exacto!", "¡Ideal!"],
            'understanding': ["Entiendo.", "Claro.", "Por supuesto."],
            'excitement': ["¡Excelente!", "¡Fantástico!", "¡Súper!"]
        }
        
        import random
        return random.choice(validations.get(emotion, validations['positive']))
    
    def get_urgency_response(self, urgency: str) -> str:
        """Respuesta según urgencia detectada"""
        urgency_responses = {
            'high': "¡Perfecto! ¿Mañana disponible?",
            'medium': "¡Genial! ¿Esta semana?",
            'low': "¡Ideal! ¿Cuándo empezamos?"
        }
        
        return urgency_responses.get(urgency, "¿Cuándo te conviene?")
    
    def format_roi_snippet(self, service: str, roi_metric: str) -> str:
        """Formatear snippet de ROI ultra corto"""
        roi_templates = {
            'AI_CHATBOT': f"Reduce {roi_metric} tiempo respuesta",
            'AI_VOICE': f"{roi_metric} mejor conversión",
            'WEB_STARTER': "Presencia digital 24/7",
            'WEB_ECOMMERCE': "Ventas automáticas 24/7",
            'MVP': f"{roi_metric} menos tiempo mercado"
        }
        
        return roi_templates.get(service, f"{roi_metric} mejora")
    
    def should_inject_value(self, conversation_log: list) -> bool:
        """Determinar si inyectar micro-valor basado en contexto"""
        # No inyectar si ya se inyectó en los últimos 3 mensajes
        recent_messages = conversation_log[-3:] if conversation_log else []
        
        for message in recent_messages:
            if message.get('type') == 'assistant_message':
                content = message.get('content', '')
                if any(indicator in content for indicator in ['¡Perfecto!', '¡Genial!', '¡Ideal!']):
                    return False
        
        return True

# Instancia global
micro_value_injector = MicroValueInjector()