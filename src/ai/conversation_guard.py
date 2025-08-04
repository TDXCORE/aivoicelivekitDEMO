"""
Conversation Guard para TDX WhatsApp Bot
Previene loops y aplica fallbacks ultra cortos
"""

import logging
import hashlib
from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta
from dataclasses import dataclass
from collections import defaultdict

logger = logging.getLogger("conversation_guard")

@dataclass
class ResponsePattern:
    """Patrón de respuesta detectado"""
    content: str
    hash: str
    count: int
    first_seen: datetime
    last_seen: datetime

class ConversationGuard:
    """Guardian de conversación anti-loops con fallbacks ultra cortos"""
    
    def __init__(self):
        self.max_repeats = 2  # Máximo 2 repeticiones antes de fallback
        self.pattern_history = {}  # {conversation_id: {hash: ResponsePattern}}
        self.fallback_responses = [
            "¿Agendamos 15 min?",
            "¿Mañana te conviene?", 
            "¿Tu disponibilidad?",
            "¿Cuándo hablamos?",
            "¿Esta semana?",
            "¿Te llamo?"
        ]
        
        # Patrones problemáticos comunes
        self.problem_patterns = [
            "no pude procesar",
            "error procesando",
            "intenta de nuevo",
            "puedes repetir",
            "problema técnico"
        ]
        
        # Respuestas de escape para situaciones críticas
        self.escape_responses = [
            "Mejor agendemos llamada rápida.",
            "Te contacto por teléfono.",
            "Un especialista te escribirá."
        ]
        
        # Límites temporales
        self.reset_after_minutes = 30  # Reset patrones después de 30 min
        self.max_conversation_length = 20  # Máximo 20 intercambios
        
    def check_for_loops(self, response: str, conversation_id: str, 
                       conversation_log: List[Dict[str, Any]]) -> str:
        """DESACTIVADO TEMPORALMENTE - Permitir flujo normal sin interferencia"""
        try:
            # DESACTIVADO: ConversationGuard está causando problemas
            # Simplemente devolver la respuesta original sin modificaciones
            logger.info(f"ConversationGuard DESACTIVADO para {conversation_id} - permitiendo flujo normal")
            return response
            
        except Exception as e:
            logger.error(f"Error en conversation guard: {e}")
            # En caso de error, devolver respuesta original
            return response
    
    def _generate_response_hash(self, response: str) -> str:
        """Generar hash normalizado de la respuesta"""
        # Normalizar: minúsculas, sin espacios extra, sin puntuación
        normalized = ''.join(c.lower() for c in response if c.isalnum() or c.isspace())
        normalized = ' '.join(normalized.split())
        
        # Generar hash corto
        return hashlib.md5(normalized.encode()).hexdigest()[:8]
    
    def _cleanup_old_patterns(self, patterns: Dict[str, ResponsePattern], now: datetime):
        """Limpiar patrones antiguos"""
        cutoff_time = now - timedelta(minutes=self.reset_after_minutes)
        
        # Remover patrones antiguos
        expired_hashes = [
            hash_key for hash_key, pattern in patterns.items()
            if pattern.last_seen < cutoff_time
        ]
        
        for hash_key in expired_hashes:
            del patterns[hash_key]
        
        if expired_hashes:
            logger.debug(f"Limpiados {len(expired_hashes)} patrones expirados")
    
    def _select_fallback(self, original_response: str, conversation_log: List[Dict[str, Any]], 
                        conversation_id: str) -> str:
        """Seleccionar fallback apropiado según contexto"""
        
        # Analizar contexto de la conversación
        has_service_info = any(
            'detected_service' in str(entry.get('content', ''))
            for entry in conversation_log[-5:]
        )
        
        has_contact_info = any(
            '@' in str(entry.get('content', '')) or 'nombre' in str(entry.get('content', ''))
            for entry in conversation_log[-5:]
        )
        
        # Seleccionar fallback según contexto
        if has_service_info and has_contact_info:
            # Tiene info suficiente, forzar agendamiento
            return "¿Agendamos llamada ahora?"
        elif has_service_info:
            # Tiene servicio, necesita datos
            return "¿Tu nombre y email?"
        else:
            # Conversación sin progreso
            import random
            return random.choice(self.fallback_responses)
    
    def _is_problematic_response(self, response: str) -> bool:
        """Verificar si la respuesta indica un problema"""
        response_lower = response.lower()
        
        return any(pattern in response_lower for pattern in self.problem_patterns)
    
    def _get_escape_response(self) -> str:
        """Obtener respuesta de escape para situaciones críticas"""
        import random
        return random.choice(self.escape_responses)
    
    def force_scheduling_fallback(self, conversation_id: str, reason: str = "conversation_stuck") -> str:
        """Forzar fallback de agendamiento"""
        logger.info(f"Forzando fallback agendamiento en {conversation_id}: {reason}")
        
        # Limpiar historial para reiniciar
        if conversation_id in self.pattern_history:
            del self.pattern_history[conversation_id]
        
        # Respuestas directas de agendamiento
        direct_scheduling = [
            "¿Mañana 10am disponible?",
            "¿Esta tarde te conviene?",
            "¿15 min ahora?"
        ]
        
        import random
        return random.choice(direct_scheduling)
    
    def get_conversation_stats(self, conversation_id: str) -> Dict[str, Any]:
        """Obtener estadísticas de la conversación"""
        if conversation_id not in self.pattern_history:
            return {
                'patterns_tracked': 0,
                'repeated_responses': 0,
                'status': 'healthy'
            }
        
        patterns = self.pattern_history[conversation_id]
        repeated_count = sum(1 for p in patterns.values() if p.count > 1)
        max_repeats = max((p.count for p in patterns.values()), default=1)
        
        status = 'healthy'
        if max_repeats > self.max_repeats:
            status = 'loop_detected'
        elif repeated_count > 3:
            status = 'repetitive'
        
        return {
            'patterns_tracked': len(patterns),
            'repeated_responses': repeated_count,
            'max_repeats': max_repeats,
            'status': status,
            'last_activity': max((p.last_seen for p in patterns.values()), default=datetime.now()).isoformat()
        }
    
    def reset_conversation(self, conversation_id: str):
        """Reset completo del historial de conversación"""
        if conversation_id in self.pattern_history:
            del self.pattern_history[conversation_id]
            logger.info(f"Reset conversation guard para {conversation_id}")
    
    def get_global_stats(self) -> Dict[str, Any]:
        """Estadísticas globales del guardian"""
        total_conversations = len(self.pattern_history)
        total_patterns = sum(len(patterns) for patterns in self.pattern_history.values())
        
        # Conversaciones con loops
        looped_conversations = sum(
            1 for patterns in self.pattern_history.values()
            if any(p.count > self.max_repeats for p in patterns.values())
        )
        
        return {
            'total_conversations': total_conversations,
            'total_patterns': total_patterns,
            'looped_conversations': looped_conversations,
            'loop_rate': round(looped_conversations / max(total_conversations, 1) * 100, 2),
            'avg_patterns_per_conversation': round(total_patterns / max(total_conversations, 1), 2)
        }
    
    def cleanup_inactive_conversations(self, hours: int = 24):
        """Limpiar conversaciones inactivas"""
        cutoff_time = datetime.now() - timedelta(hours=hours)
        
        inactive_conversations = []
        for conv_id, patterns in self.pattern_history.items():
            if not patterns:  # Vacío
                inactive_conversations.append(conv_id)
                continue
            
            last_activity = max(p.last_seen for p in patterns.values())
            if last_activity < cutoff_time:
                inactive_conversations.append(conv_id)
        
        # Remover conversaciones inactivas
        for conv_id in inactive_conversations:
            del self.pattern_history[conv_id]
        
        logger.info(f"Limpiadas {len(inactive_conversations)} conversaciones inactivas")
        return len(inactive_conversations)
    
    def _detect_scheduling_loop(self, response: str, conversation_log: List[Dict[str, Any]]) -> Optional[Dict[str, Any]]:
        """Detectar loops específicos de agendamiento"""
        try:
            # Obtener últimas respuestas del bot
            recent_bot_responses = [
                entry.get('content', '').lower() for entry in conversation_log[-6:]
                if entry.get('type') == 'assistant_message'
            ]
            
            # Obtener últimos mensajes del usuario
            recent_user_messages = [
                entry.get('content', '').lower() for entry in conversation_log[-6:]
                if entry.get('type') == 'user_message'
            ]
            
            current_response = response.lower()
            
            # CASO 1: Repetir "¿Qué día y hora te conviene?" después de que el usuario ya dio información
            if any('día y hora' in resp or 'cuándo' in resp for resp in recent_bot_responses[-2:]):
                # Verificar si el usuario ya dio información de tiempo
                time_info_given = any(
                    any(keyword in msg for keyword in ['mañana', 'tarde', 'pm', 'am', '3pm', '10', '11', '12', '1', '2', '3', '4', '5'])
                    for msg in recent_user_messages[-2:]
                )
                
                if time_info_given and ('día y hora' in current_response or 'cuándo' in current_response):
                    return {
                        'reason': 'Usuario ya proporcionó información de horario',
                        'fallback': '¡Perfecto! Te envío la invitación para mañana a las 3:00 PM. Solo necesito confirmar tu email.'
                    }
            
            # CASO ESPECÍFICO: Repetir pregunta por teléfono después de que el usuario ya lo proporcionó
            if ('teléfono' in current_response or 'telefono' in current_response) and any('teléfono' in resp or 'telefono' in resp for resp in recent_bot_responses[-2:]):
                # Verificar si el usuario ya dio un número de teléfono
                import re
                phone_given = any(
                    re.search(r'\b3\d{9}\b|\b\d{10}\b', msg) for msg in recent_user_messages[-3:]
                )
                
                if phone_given:
                    return {
                        'reason': 'Usuario ya proporcionó teléfono',
                        'fallback': '¡Perfecto! Ya tengo todos tus datos. Te contactaremos pronto para agendar la demo. ¡Gracias por tu interés!'
                    }
            
            # CASO ESPECÍFICO: Repetir pregunta general después de tener datos completos
            contact_questions = ['en qué puedo ayudarte', 'qué puedo hacer', 'cómo puedo ayudarte']
            if any(question in current_response.lower() for question in contact_questions):
                # Verificar si la conversación ya avanzó (tiene email, teléfono, servicio)
                conversation_advanced = any(
                    any(keyword in str(entry.get('content', '')) for keyword in ['email', '@', 'telefono', 'automatizacion', 'demo'])
                    for entry in conversation_log[-5:]
                )
                
                # Solo aplicar fallback si realmente hay datos COMPLETOS (incluyendo teléfono)
                has_phone = any(
                    any(keyword in str(entry.get('content', '')) for keyword in ['3', '31', 'telefono', 'teléfono'])
                    for entry in conversation_log[-5:]
                )
                
                if conversation_advanced and has_phone:
                    return {
                        'reason': 'Conversación ya avanzó con datos completos, no reiniciar',
                        'fallback': 'Perfecto. Ya tenemos todo listo. Te contactaremos pronto para coordinar la demo de automatización.'
                    }
            
            # CASO CRÍTICO: NO INTERFERIR cuando el bot está mostrando opciones de calendario
            if any(keyword in current_response.lower() for keyword in ['opción 1', 'opción 2', 'opción 3', 'horarios disponibles']):
                return {
                    'reason': 'Bot mostrando opciones de calendario - no interferir',
                    'fallback': None  # Permitir que el flujo normal continúe
                }
            
            # CASO 2: Repetir pregunta general sobre servicios después de que el usuario especificó
            service_keywords = ['automatización', 'automatizar', 'chatbot', 'finanzas', 'conciliación']
            service_mentioned = any(
                any(keyword in msg for keyword in service_keywords)
                for msg in recent_user_messages[-3:]
            )
            
            if service_mentioned:
                general_questions = ['qué puedo ayudarte', 'en qué podemos ayudarte', 'qué servicio']
                if any(question in current_response for question in general_questions):
                    return {
                        'reason': 'Usuario ya especificó servicio de interés',
                        'fallback': 'Perfecto, automatización financiera es exactamente nuestra especialidad. ¿Agendamos una demo?'
                    }
            
            # CASO 3: Bucle infinito en confirmación de agendamiento
            confirmation_responses = [resp for resp in recent_bot_responses if 'agend' in resp or 'reunión' in resp or 'llamada' in resp]
            if len(confirmation_responses) >= 2 and ('agend' in current_response or 'reunión' in current_response):
                # Verificar si el usuario está respondiendo a opciones de calendario
                user_selecting_option = any(
                    any(option in msg for option in ['1', '2', '3', 'primera', 'segunda', 'tercera'])
                    for msg in recent_user_messages[-2:]
                )
                
                # Verificar si ya tenemos datos completos (email, teléfono, nombre)
                has_complete_data = any(
                    all(keyword in str(entry.get('content', '')) for keyword in ['@', '3'])
                    for entry in conversation_log[-5:]
                )
                
                # Solo aplicar fallback si el usuario está seleccionando opciones Y tenemos datos completos
                if not user_selecting_option and has_complete_data:
                    return {
                        'reason': 'Bucle infinito en confirmaciones de agendamiento con datos completos',
                        'fallback': None  # Permitir que el flujo normal continúe
                    }
            
            # CASO 4: El usuario confirma pero el bot sigue preguntando lo mismo
            user_confirmations = [msg for msg in recent_user_messages[-2:] if any(
                conf in msg for conf in ['si', 'sí', 'yes', 'dale', 'ok', 'claro', 'perfecto', 'genial', 'agendemos']
            )]
            
            if user_confirmations and len(recent_bot_responses) >= 2:
                # Si el usuario confirmó y el bot repite la misma pregunta
                if recent_bot_responses[-1] == recent_bot_responses[-2]:
                    return {
                        'reason': 'Usuario confirmó pero bot repite pregunta',
                        'fallback': 'Excelente. Te envío los detalles por WhatsApp. ¿Cuál es tu email corporativo?'
                    }
            
            return None
            
        except Exception as e:
            logger.error(f"Error detecting scheduling loop: {e}")
            return None

# Instancia global
conversation_guard = ConversationGuard()
