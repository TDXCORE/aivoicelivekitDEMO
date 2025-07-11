import logging
from datetime import datetime, timedelta
from typing import Dict, Any, Optional, List
import json
import os

logger = logging.getLogger("whatsapp-metrics")

class WhatsAppMetrics:
    def __init__(self):
        # En production: usar Redis/InfluxDB/CloudWatch
        self.metrics = {
            'conversations': {},
            'daily_stats': {
                'messages_sent': 0,
                'messages_received': 0,
                'meetings_scheduled': 0,
                'human_handoffs': 0,
                'errors': 0,
                'unique_users': set()
            },
            'performance': {
                'avg_response_time': 0,
                'response_times': [],
                'error_rate': 0
            }
        }
        
        # Configuración
        self.retention_days = 7  # Mantener métricas por 7 días
        self.last_cleanup = datetime.now()
    
    async def log_conversation_started(self, conversation_id: int, contact_info: Dict[str, Any]):
        """Log inicio de conversación"""
        self.metrics['conversations'][conversation_id] = {
            'start_time': datetime.now().isoformat(),
            'contact_name': contact_info.get('name'),
            'company_name': contact_info.get('company'),
            'contact_email': contact_info.get('email'),
            'contact_phone': contact_info.get('phone'),
            'source': 'whatsapp',
            'status': 'active',
            'message_count': 0,
            'outcome': None,
            'session_duration': None,
            'bot_responses': 0,
            'user_messages': 0,
            'functions_called': [],
            'errors': []
        }
        
        # Agregar a usuarios únicos
        self.metrics['daily_stats']['unique_users'].add(
            contact_info.get('chatwoot_id', conversation_id)
        )
        
        logger.info(f"Started WhatsApp conversation: {conversation_id} for {contact_info.get('name')}")
    
    async def log_user_message(self, conversation_id: int, content: str):
        """Log mensaje del usuario"""
        self.metrics['daily_stats']['messages_received'] += 1
        
        if conversation_id in self.metrics['conversations']:
            self.metrics['conversations'][conversation_id]['message_count'] += 1
            self.metrics['conversations'][conversation_id]['user_messages'] += 1
            self.metrics['conversations'][conversation_id]['last_user_message'] = datetime.now().isoformat()
            
            # Analizar intent del mensaje
            intent = self.analyze_message_intent(content)
            if 'intents' not in self.metrics['conversations'][conversation_id]:
                self.metrics['conversations'][conversation_id]['intents'] = []
            self.metrics['conversations'][conversation_id]['intents'].append(intent)
    
    async def log_bot_response(self, conversation_id: int, content: str, response_time: float = 0):
        """Log respuesta del bot"""
        self.metrics['daily_stats']['messages_sent'] += 1
        
        if conversation_id in self.metrics['conversations']:
            self.metrics['conversations'][conversation_id]['bot_responses'] += 1
            self.metrics['conversations'][conversation_id]['last_bot_response'] = datetime.now().isoformat()
            
            # Métricas de performance
            if response_time > 0:
                self.metrics['performance']['response_times'].append(response_time)
                # Mantener solo últimas 100 mediciones
                if len(self.metrics['performance']['response_times']) > 100:
                    self.metrics['performance']['response_times'] = \
                        self.metrics['performance']['response_times'][-100:]
                
                # Calcular promedio
                avg_time = sum(self.metrics['performance']['response_times']) / \
                          len(self.metrics['performance']['response_times'])
                self.metrics['performance']['avg_response_time'] = round(avg_time, 2)
    
    async def log_function_called(self, conversation_id: int, function_name: str, success: bool):
        """Log llamada a función"""
        if conversation_id in self.metrics['conversations']:
            function_call = {
                'function': function_name,
                'timestamp': datetime.now().isoformat(),
                'success': success
            }
            self.metrics['conversations'][conversation_id]['functions_called'].append(function_call)
    
    async def log_meeting_scheduled(self, conversation_id: int, date: str, time: str):
        """Log reunión agendada"""
        self.metrics['daily_stats']['meetings_scheduled'] += 1
        
        if conversation_id in self.metrics['conversations']:
            self.metrics['conversations'][conversation_id]['outcome'] = 'meeting_scheduled'
            self.metrics['conversations'][conversation_id]['meeting_date'] = date
            self.metrics['conversations'][conversation_id]['meeting_time'] = time
            self.metrics['conversations'][conversation_id]['status'] = 'resolved'
            
            # Calcular duración de sesión
            start_time = datetime.fromisoformat(
                self.metrics['conversations'][conversation_id]['start_time']
            )
            duration = (datetime.now() - start_time).total_seconds()
            self.metrics['conversations'][conversation_id]['session_duration'] = duration
        
        await self.log_function_called(conversation_id, 'schedule_meeting_whatsapp', True)
        logger.info(f"Meeting scheduled via WhatsApp: {conversation_id} -> {date} {time}")
    
    async def log_human_handoff(self, conversation_id: int, reason: str):
        """Log transferencia a humano"""
        self.metrics['daily_stats']['human_handoffs'] += 1
        
        if conversation_id in self.metrics['conversations']:
            self.metrics['conversations'][conversation_id]['outcome'] = 'transferred_to_human'
            self.metrics['conversations'][conversation_id]['handoff_reason'] = reason
            self.metrics['conversations'][conversation_id]['status'] = 'transferred'
            
            # Calcular duración de sesión
            start_time = datetime.fromisoformat(
                self.metrics['conversations'][conversation_id]['start_time']
            )
            duration = (datetime.now() - start_time).total_seconds()
            self.metrics['conversations'][conversation_id]['session_duration'] = duration
        
        await self.log_function_called(conversation_id, 'transfer_to_human_whatsapp', True)
        logger.info(f"Human handoff: {conversation_id} -> {reason}")
    
    async def log_error(self, conversation_id: int, error_type: str, error_details: str = None):
        """Log errores"""
        self.metrics['daily_stats']['errors'] += 1
        
        error_entry = {
            'type': error_type,
            'details': error_details,
            'timestamp': datetime.now().isoformat()
        }
        
        if conversation_id in self.metrics['conversations']:
            if 'errors' not in self.metrics['conversations'][conversation_id]:
                self.metrics['conversations'][conversation_id]['errors'] = []
            self.metrics['conversations'][conversation_id]['errors'].append(error_entry)
        
        # Calcular error rate
        total_responses = self.metrics['daily_stats']['messages_sent']
        if total_responses > 0:
            self.metrics['performance']['error_rate'] = \
                (self.metrics['daily_stats']['errors'] / total_responses) * 100
        
        logger.error(f"WhatsApp bot error: {conversation_id} -> {error_type}: {error_details}")
    
    async def log_conversation_ended(self, conversation_id: int, reason: str = "user_ended"):
        """Log fin de conversación"""
        if conversation_id in self.metrics['conversations']:
            conv = self.metrics['conversations'][conversation_id]
            
            if conv['status'] == 'active':
                conv['status'] = 'ended'
                conv['end_reason'] = reason
                
                # Calcular duración final
                start_time = datetime.fromisoformat(conv['start_time'])
                duration = (datetime.now() - start_time).total_seconds()
                conv['session_duration'] = duration
                
                # Determinar outcome si no se estableció
                if not conv.get('outcome'):
                    if conv['message_count'] <= 2:
                        conv['outcome'] = 'abandoned_early'
                    elif conv['bot_responses'] >= 5:
                        conv['outcome'] = 'extended_conversation'
                    else:
                        conv['outcome'] = 'casual_inquiry'
        
        logger.info(f"Conversation ended: {conversation_id} -> {reason}")
    
    def analyze_message_intent(self, content: str) -> str:
        """Analizar intent básico del mensaje"""
        content_lower = content.lower()
        
        # Intents de negocio
        if any(word in content_lower for word in ['agendar', 'reunión', 'cita', 'meeting']):
            return 'schedule_meeting'
        elif any(word in content_lower for word in ['humano', 'persona', 'ejecutivo', 'agente']):
            return 'request_human'
        elif any(word in content_lower for word in ['precio', 'costo', 'cuanto', '$']):
            return 'pricing_inquiry'
        elif any(word in content_lower for word in ['ai', 'inteligencia artificial', 'automatización']):
            return 'ai_solution_inquiry'
        elif any(word in content_lower for word in ['soporte', 'ayuda', 'problema']):
            return 'support_request'
        elif any(word in content_lower for word in ['hola', 'buenos días', 'buenas tardes']):
            return 'greeting'
        elif any(word in content_lower for word in ['gracias', 'perfecto', 'excelente']):
            return 'positive_feedback'
        elif any(word in content_lower for word in ['no', 'no me interesa', 'cancelar']):
            return 'negative_response'
        else:
            return 'general_inquiry'
    
    async def get_daily_summary(self) -> Dict[str, Any]:
        """Obtener resumen diario"""
        active_conversations = len([
            conv for conv in self.metrics['conversations'].values() 
            if conv.get('status') == 'active'
        ])
        
        # Calcular conversion rate
        total_conversations = len(self.metrics['conversations'])
        meetings_scheduled = self.metrics['daily_stats']['meetings_scheduled']
        conversion_rate = (meetings_scheduled / total_conversations * 100) if total_conversations > 0 else 0
        
        # Calcular avg session duration
        completed_sessions = [
            conv for conv in self.metrics['conversations'].values()
            if conv.get('session_duration') is not None
        ]
        avg_session_duration = 0
        if completed_sessions:
            total_duration = sum(conv['session_duration'] for conv in completed_sessions)
            avg_session_duration = total_duration / len(completed_sessions)
        
        return {
            'date': datetime.now().strftime('%Y-%m-%d'),
            'total_conversations': total_conversations,
            'active_conversations': active_conversations,
            'unique_users': len(self.metrics['daily_stats']['unique_users']),
            'messages_sent': self.metrics['daily_stats']['messages_sent'],
            'messages_received': self.metrics['daily_stats']['messages_received'],
            'meetings_scheduled': meetings_scheduled,
            'human_handoffs': self.metrics['daily_stats']['human_handoffs'],
            'errors': self.metrics['daily_stats']['errors'],
            'conversion_rate': round(conversion_rate, 2),
            'avg_response_time': self.metrics['performance']['avg_response_time'],
            'error_rate': round(self.metrics['performance']['error_rate'], 2),
            'avg_session_duration': round(avg_session_duration, 2)
        }
    
    async def get_conversation_analytics(self) -> Dict[str, Any]:
        """Obtener analytics detallado de conversaciones"""
        conversations = list(self.metrics['conversations'].values())
        
        # Outcomes distribution
        outcomes = {}
        for conv in conversations:
            outcome = conv.get('outcome', 'unknown')
            outcomes[outcome] = outcomes.get(outcome, 0) + 1
        
        # Intent analysis
        all_intents = []
        for conv in conversations:
            all_intents.extend(conv.get('intents', []))
        
        intent_distribution = {}
        for intent in all_intents:
            intent_distribution[intent] = intent_distribution.get(intent, 0) + 1
        
        # Function usage
        function_usage = {}
        for conv in conversations:
            for func_call in conv.get('functions_called', []):
                func_name = func_call['function']
                if func_name not in function_usage:
                    function_usage[func_name] = {'total': 0, 'successful': 0}
                function_usage[func_name]['total'] += 1
                if func_call['success']:
                    function_usage[func_name]['successful'] += 1
        
        return {
            'total_conversations': len(conversations),
            'outcomes_distribution': outcomes,
            'intent_distribution': intent_distribution,
            'function_usage': function_usage,
            'top_intents': sorted(intent_distribution.items(), key=lambda x: x[1], reverse=True)[:5]
        }
    
    async def get_performance_metrics(self) -> Dict[str, Any]:
        """Obtener métricas de performance"""
        response_times = self.metrics['performance']['response_times']
        
        if not response_times:
            return {
                'avg_response_time': 0,
                'min_response_time': 0,
                'max_response_time': 0,
                'error_rate': 0,
                'total_responses': 0
            }
        
        return {
            'avg_response_time': self.metrics['performance']['avg_response_time'],
            'min_response_time': min(response_times),
            'max_response_time': max(response_times),
            'error_rate': self.metrics['performance']['error_rate'],
            'total_responses': self.metrics['daily_stats']['messages_sent'],
            'p95_response_time': self.calculate_percentile(response_times, 95),
            'p99_response_time': self.calculate_percentile(response_times, 99)
        }
    
    def calculate_percentile(self, data: List[float], percentile: int) -> float:
        """Calcular percentil de una lista"""
        if not data:
            return 0
        
        sorted_data = sorted(data)
        index = int((percentile / 100) * len(sorted_data))
        if index >= len(sorted_data):
            index = len(sorted_data) - 1
        
        return sorted_data[index]
    
    async def cleanup_old_metrics(self):
        """Limpiar métricas antiguas"""
        cutoff_date = datetime.now() - timedelta(days=self.retention_days)
        
        conversations_to_remove = []
        for conv_id, conv_data in self.metrics['conversations'].items():
            start_time = datetime.fromisoformat(conv_data['start_time'])
            if start_time < cutoff_date:
                conversations_to_remove.append(conv_id)
        
        for conv_id in conversations_to_remove:
            del self.metrics['conversations'][conv_id]
        
        if conversations_to_remove:
            logger.info(f"Cleaned up {len(conversations_to_remove)} old conversation metrics")
    
    async def export_metrics(self, format: str = 'json') -> str:
        """Exportar métricas para análisis externo"""
        if format == 'json':
            # Convertir sets a lists para JSON serialization
            export_data = {
                'daily_summary': await self.get_daily_summary(),
                'conversation_analytics': await self.get_conversation_analytics(),
                'performance_metrics': await self.get_performance_metrics(),
                'export_timestamp': datetime.now().isoformat()
            }
            return json.dumps(export_data, indent=2, default=str)
        else:
            return "Format not supported"

# Instancia global para reutilización
whatsapp_metrics = WhatsAppMetrics()