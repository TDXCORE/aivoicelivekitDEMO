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
        """Verificar loops y aplicar fallback si es necesario"""
        try:
            # Generar hash de la respuesta normalizada
            response_hash = self._generate_response_hash(response)
            
            # Inicializar historial si no existe
            if conversation_id not in self.pattern_history:
                self.pattern_history[conversation_id] = {}
            
            patterns = self.pattern_history[conversation_id]
            now = datetime.now()
            
            # Limpiar patrones antiguos
            self._cleanup_old_patterns(patterns, now)
            
            # Verificar si es respuesta repetida
            if response_hash in patterns:
                pattern = patterns[response_hash]
                pattern.count += 1
                pattern.last_seen = now
                
                # Si supera el límite, aplicar fallback
                if pattern.count > self.max_repeats:
                    logger.warning(f"Loop detectado en {conversation_id}: '{response[:50]}...' repetido {pattern.count} veces")
                    
                    # Determinar tipo de fallback necesario
                    fallback = self._select_fallback(response, conversation_log, conversation_id)
                    
                    # Reset el patrón para evitar loops infinitos
                    del patterns[response_hash]
                    
                    return fallback
            else:
                # Nueva respuesta, agregar al historial
                patterns[response_hash] = ResponsePattern(
                    content=response,
                    hash=response_hash,
                    count=1,
                    first_seen=now,
                    last_seen=now
                )
            
            # Verificar longitud de conversación
            if len(conversation_log) > self.max_conversation_length:
                logger.info(f"Conversación larga detectada ({len(conversation_log)} intercambios), forzando agendamiento")
                return "Conversación larga. ¿Agendamos llamada?"
            
            # Verificar patrones problemáticos
            if self._is_problematic_response(response):
                logger.warning(f"Respuesta problemática detectada: {response[:50]}...")
                return self._get_escape_response()
            
            return response
            
        except Exception as e:
            logger.error(f"Error en conversation guard: {e}")
            # En caso de error, aplicar fallback seguro
            return "Error técnico. ¿Agendamos llamada?"
    
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

# Instancia global
conversation_guard = ConversationGuard()