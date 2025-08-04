"""
BANT Scorer para TDX Core 2025 WhatsApp Agent
Sistema de calificación BANT (Budget, Authority, Need, Timeline)
"""

import logging
from typing import Dict, Any, Optional
from dataclasses import dataclass
from datetime import datetime

logger = logging.getLogger("bant_scorer")

@dataclass
class BANTScore:
    """Resultado de calificación BANT"""
    budget_score: int
    authority_score: int
    need_score: int
    timeline_score: int
    total_score: int
    qualified: bool
    recommendation: str
    details: Dict[str, str]

class BANTScorer:
    """Calificador BANT automático para leads WhatsApp"""
    
    def __init__(self):
        self.min_qualifying_score = 60
        
        # Mapeo de industrias a budget score
        self.industry_budget_map = {
            'fintech': 25,      # Alto presupuesto
            'startup': 20,      # Medio-alto
            'salud': 20,        # Medio-alto
            'ecommerce': 15,    # Medio
            'educacion': 15,    # Medio
            'inmobiliaria': 15, # Medio
            'restaurante': 10,  # Bajo
            'gimnasio': 10,     # Bajo
            'general': 15       # Default medio
        }
        
        # Mapeo de posiciones a authority score
        self.position_authority_map = {
            'ceo': 30,
            'founder': 30,
            'director': 25,
            'gerente': 20,
            'coordinador': 15,
            'jefe': 15,
            'supervisor': 10,
            'empleado': 5,
            'unknown': 15  # Default medio
        }
        
        # Mapeo de servicios a need score
        self.service_need_map = {
            'AI_VOICE': 25,           # Alto impacto
            'AI_CHATBOT': 25,         # Alto impacto
            'WEB_ECOMMERCE': 20,      # Medio-alto
            'MVP': 20,                # Medio-alto
            'AI_VIDEO': 15,           # Medio
            'WEB_BUSINESS': 15,       # Medio
            'AI_ASSISTANT_WHATSAPP': 15, # Medio
            'WEB_STARTER': 10,        # Bajo
            'SEO': 10,                # Bajo
            'AI_GENERAL': 15          # Default
        }
        
        # Keywords que indican urgencia
        self.urgency_keywords = {
            'high': ['urgente', 'ya', 'inmediato', 'rapidamente', 'pronto', 'ahora'],
            'medium': ['semana', 'mes', 'trimestre', 'necesito'],
            'low': ['futuro', 'eventualmente', 'considerando', 'evaluando']
        }
    
    def calculate_bant_score(self, prospect_info: Dict[str, Any], 
                           conversation_context: Optional[str] = None) -> BANTScore:
        """Calcular score BANT completo"""
        try:
            # 1. Budget Score (25 puntos max)
            budget_score = self._calculate_budget_score(prospect_info)
            
            # 2. Authority Score (30 puntos max)
            authority_score = self._calculate_authority_score(prospect_info)
            
            # 3. Need Score (25 puntos max)
            need_score = self._calculate_need_score(prospect_info, conversation_context)
            
            # 4. Timeline Score (20 puntos max)
            timeline_score = self._calculate_timeline_score(prospect_info, conversation_context)
            
            # Score total
            total_score = budget_score + authority_score + need_score + timeline_score
            
            # Calificación
            qualified = total_score >= self.min_qualifying_score
            recommendation = "schedule_meeting" if qualified else "nurture_lead"
            
            # Detalles para transparencia
            details = {
                'budget_reason': self._get_budget_reason(prospect_info),
                'authority_reason': self._get_authority_reason(prospect_info),
                'need_reason': self._get_need_reason(prospect_info),
                'timeline_reason': self._get_timeline_reason(prospect_info, conversation_context)
            }
            
            result = BANTScore(
                budget_score=budget_score,
                authority_score=authority_score,
                need_score=need_score,
                timeline_score=timeline_score,
                total_score=total_score,
                qualified=qualified,
                recommendation=recommendation,
                details=details
            )
            
            logger.info(f"BANT Score calculado: {total_score}/100 (B:{budget_score} A:{authority_score} N:{need_score} T:{timeline_score})")
            return result
            
        except Exception as e:
            logger.error(f"Error calculando BANT score: {e}")
            # Fallback score neutral
            return BANTScore(
                budget_score=15, authority_score=15, need_score=15, timeline_score=10,
                total_score=55, qualified=False, recommendation="nurture_lead",
                details={'error': str(e)}
            )
    
    def _calculate_budget_score(self, prospect_info: Dict[str, Any]) -> int:
        """Calcular score de presupuesto (Budget)"""
        industry = prospect_info.get('industry', 'general')
        company_name = prospect_info.get('company_name', '')
        
        # Score base por industria
        base_score = self.industry_budget_map.get(industry, 15)
        
        # Ajustes por señales de empresa
        if company_name:
            company_lower = company_name.lower()
            
            # Indicadores de empresa grande
            if any(indicator in company_lower for indicator in ['sas', 'sa', 'ltda', 'corp', 'inc']):
                base_score += 5
            
            # Indicadores de startup/tech
            if any(indicator in company_lower for indicator in ['tech', 'digital', 'software', 'ai']):
                base_score += 3
        
        return min(base_score, 25)  # Max 25 puntos
    
    def _calculate_authority_score(self, prospect_info: Dict[str, Any]) -> int:
        """Calcular score de autoridad (Authority)"""
        position = prospect_info.get('position', '').lower()
        
        # Mapeo directo por posición
        for key, score in self.position_authority_map.items():
            if key in position:
                return score
        
        # Si no hay posición explícita, inferir por contexto
        full_name = prospect_info.get('full_name', '').lower()
        company_name = prospect_info.get('company_name', '').lower()
        
        # Si el nombre está en el nombre de la empresa, probablemente es fundador/owner
        if full_name and company_name:
            name_parts = full_name.split()
            if any(part in company_name for part in name_parts if len(part) > 2):
                return 25  # Probable owner/founder
        
        return self.position_authority_map['unknown']
    
    def _calculate_need_score(self, prospect_info: Dict[str, Any], 
                            conversation_context: Optional[str] = None) -> int:
        """Calcular score de necesidad (Need)"""
        detected_service = prospect_info.get('detected_service')
        
        # Score base por servicio
        base_score = self.service_need_map.get(detected_service, 15)
        
        # Ajustes por contexto de conversación
        if conversation_context:
            context_lower = conversation_context.lower()
            
            # Indicadores de alta necesidad
            high_need_indicators = [
                'problema', 'dificultad', 'manual', 'lento', 'ineficiente',
                'necesito', 'urgente', 'ayuda', 'solución'
            ]
            
            need_mentions = sum(1 for indicator in high_need_indicators 
                              if indicator in context_lower)
            
            if need_mentions >= 2:
                base_score += 5
            elif need_mentions >= 1:
                base_score += 3
        
        return min(base_score, 25)  # Max 25 puntos
    
    def _calculate_timeline_score(self, prospect_info: Dict[str, Any], 
                                conversation_context: Optional[str] = None) -> int:
        """Calcular score de timeline (Timeline)"""
        if not conversation_context:
            return 10  # Default neutral
        
        context_lower = conversation_context.lower()
        
        # Detectar urgencia en el texto
        for urgency_level, keywords in self.urgency_keywords.items():
            if any(keyword in context_lower for keyword in keywords):
                if urgency_level == 'high':
                    return 20
                elif urgency_level == 'medium':
                    return 15
                elif urgency_level == 'low':
                    return 5
        
        return 10  # Default si no hay indicadores claros
    
    def _get_budget_reason(self, prospect_info: Dict[str, Any]) -> str:
        """Explicar razón del budget score"""
        industry = prospect_info.get('industry', 'general')
        company_name = prospect_info.get('company_name', '')
        
        base_reason = f"Industria {industry}"
        
        if company_name and any(indicator in company_name.lower() for indicator in ['sas', 'sa', 'ltda']):
            base_reason += " + empresa formal"
        
        return base_reason
    
    def _get_authority_reason(self, prospect_info: Dict[str, Any]) -> str:
        """Explicar razón del authority score"""
        position = prospect_info.get('position', '')
        
        if position:
            return f"Posición: {position}"
        
        # Inferencia por nombre en empresa
        full_name = prospect_info.get('full_name', '')
        company_name = prospect_info.get('company_name', '')
        
        if full_name and company_name:
            name_parts = full_name.lower().split()
            if any(part in company_name.lower() for part in name_parts if len(part) > 2):
                return "Probable fundador/owner (nombre en empresa)"
        
        return "Posición no especificada"
    
    def _get_need_reason(self, prospect_info: Dict[str, Any]) -> str:
        """Explicar razón del need score"""
        detected_service = prospect_info.get('detected_service', 'general')
        return f"Servicio: {detected_service}"
    
    def _get_timeline_reason(self, prospect_info: Dict[str, Any], 
                           conversation_context: Optional[str] = None) -> str:
        """Explicar razón del timeline score"""
        if not conversation_context:
            return "Timeline no especificado"
        
        context_lower = conversation_context.lower()
        
        for urgency_level, keywords in self.urgency_keywords.items():
            found_keywords = [kw for kw in keywords if kw in context_lower]
            if found_keywords:
                return f"Urgencia {urgency_level}: {found_keywords[0]}"
        
        return "Timeline neutral"
    
    def is_high_value_lead(self, bant_score: BANTScore) -> bool:
        """Determinar si es lead de alto valor"""
        return (bant_score.total_score >= 80 or 
                (bant_score.authority_score >= 25 and bant_score.need_score >= 20))
    
    def get_qualification_message(self, bant_score: BANTScore, contact_name: str) -> str:
        """Generar mensaje de calificación personalizado"""
        if bant_score.qualified:
            if self.is_high_value_lead(bant_score):
                return f"¡Perfecto {contact_name}! Perfil ideal. ¿Agendamos demo mañana?"
            else:
                return f"¡Excelente {contact_name}! ¿Agendamos reunión esta semana?"
        else:
            # Identificar área débil para nurturing
            weak_areas = []
            if bant_score.budget_score < 15:
                weak_areas.append("presupuesto")
            if bant_score.authority_score < 15:
                weak_areas.append("autoridad")
            if bant_score.need_score < 15:
                weak_areas.append("necesidad")
            
            return f"Entiendo {contact_name}. Te mantendré informado de soluciones que se ajusten mejor."

# Instancia global
bant_scorer = BANTScorer()