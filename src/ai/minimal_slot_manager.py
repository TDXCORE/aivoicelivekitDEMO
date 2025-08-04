"""
Minimal Slot Manager para TDX WhatsApp Bot
Gestiona datos esenciales del prospect de forma inteligente
"""

import logging
import re
from typing import Dict, Any, List, Optional, Set
from datetime import datetime
from dataclasses import dataclass

logger = logging.getLogger("minimal_slot_manager")

@dataclass
class SlotStatus:
    """Estado de un slot de datos"""
    field: str
    value: Optional[str]
    confidence: float
    source: str  # 'user_input', 'extracted', 'inferred'
    timestamp: datetime
    validated: bool = False

class MinimalSlotManager:
    """Manager inteligente de slots que evita preguntas redundantes"""
    
    def __init__(self):
        # Slots esenciales para agendar reunión
        self.essential_slots = {
            'full_name': {
                'required': True,
                'patterns': [r'\bmi nombre es\b', r'\bsoy\b', r'\bme llamo\b'],
                'validation': self._validate_name,
                'question': "¿Tu nombre completo?"
            },
            'email': {
                'required': True,
                'patterns': [r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'],
                'validation': self._validate_email,
                'question': "¿Tu email?"
            },
            'company_name': {
                'required': True,
                'patterns': [r'\ben\b', r'\bempresa\b', r'\btrabajo en\b', r'\bsomos\b'],
                'validation': self._validate_company,
                'question': "¿Nombre de tu empresa?"
            }
        }
        
        # Slots opcionales que aportan valor
        self.optional_slots = {
            'position': {
                'required': False,
                'patterns': [r'\bsoy\b.*\b(director|gerente|ceo|founder)\b', r'\bcargo\b'],
                'validation': self._validate_position,
                'question': "¿Tu cargo?"
            },
            'industry': {
                'required': False,
                'patterns': [r'\bsector\b', r'\bindustria\b', r'\brubro\b'],
                'validation': self._validate_industry,
                'question': None  # Se infiere, no se pregunta directamente
            },
            'phone': {
                'required': False,
                'patterns': [r'\b\d{10,}\b', r'\bteléfono\b', r'\bcelular\b'],
                'validation': self._validate_phone,
                'question': None  # Viene del WhatsApp, no preguntar
            }
        }
        
        # Combinaciones de slots que optimizan preguntas
        self.slot_combinations = [
            (['full_name', 'email'], "¿Nombre y email?"),
            (['full_name', 'company_name'], "¿Tu nombre y empresa?"),
            (['email', 'company_name'], "¿Email y empresa?")
        ]
        
    def analyze_prospect_data(self, prospect_info: Dict[str, Any]) -> Dict[str, Any]:
        """Analizar datos del prospect y determinar qué falta"""
        
        current_slots = {}
        missing_essential = []
        missing_optional = []
        
        # Evaluar slots esenciales
        for slot_name, slot_config in self.essential_slots.items():
            value = prospect_info.get(slot_name)
            
            if value and self._is_valid_slot_value(value, slot_name):
                current_slots[slot_name] = SlotStatus(
                    field=slot_name,
                    value=value,
                    confidence=0.9,
                    source='user_input',
                    timestamp=datetime.now(),
                    validated=True
                )
            else:
                missing_essential.append(slot_name)
        
        # Evaluar slots opcionales
        for slot_name, slot_config in self.optional_slots.items():
            value = prospect_info.get(slot_name)
            
            if value and self._is_valid_slot_value(value, slot_name):
                current_slots[slot_name] = SlotStatus(
                    field=slot_name,
                    value=value,
                    confidence=0.8,
                    source='user_input',
                    timestamp=datetime.now(),
                    validated=True
                )
            else:
                missing_optional.append(slot_name)
        
        return {
            'current_slots': current_slots,
            'missing_essential': missing_essential,
            'missing_optional': missing_optional,
            'completion_rate': len(current_slots) / len(self.essential_slots) * 100,
            'ready_to_schedule': len(missing_essential) == 0
        }
    
    def extract_slots_from_message(self, message: str, current_prospect_info: Dict[str, Any]) -> Dict[str, Any]:
        """Extraer slots de un mensaje de usuario"""
        
        extracted_slots = {}
        message_lower = message.lower()
        
        # Buscar email (patrón más específico)
        email_match = re.search(r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b', message)
        if email_match and not current_prospect_info.get('email'):
            extracted_slots['email'] = email_match.group(0).lower()
        
        # Buscar nombre (patrones contextuales)
        name_patterns = [
            r'mi nombre es ([A-Za-zÀ-ÿ\s]+)',
            r'soy ([A-Za-zÀ-ÿ\s]+)',
            r'me llamo ([A-Za-zÀ-ÿ\s]+)',
            r'^([A-Za-zÀ-ÿ]+\s+[A-Za-zÀ-ÿ]+)$'  # Dos palabras al inicio
        ]
        
        for pattern in name_patterns:
            name_match = re.search(pattern, message, re.IGNORECASE)
            if name_match and not current_prospect_info.get('full_name'):
                potential_name = name_match.group(1).strip().title()
                if self._validate_name(potential_name):
                    extracted_slots['full_name'] = potential_name
                    break
        
        # Buscar empresa (patrones contextuales)
        company_patterns = [
            r'trabajo en ([A-Za-zÀ-ÿ\s]+)',
            r'empresa ([A-Za-zÀ-ÿ\s]+)',
            r'somos ([A-Za-zÀ-ÿ\s]+)',
            r'en ([A-Za-zÀ-ÿ\s]+\s+S\.?A\.?S?)',  # Sociedades
            r'de ([A-Za-zÀ-ÿ\s]+\s+(?:Ltda|SAS|SA))'
        ]
        
        for pattern in company_patterns:
            company_match = re.search(pattern, message, re.IGNORECASE)
            if company_match and not current_prospect_info.get('company_name'):
                potential_company = company_match.group(1).strip().title()
                if self._validate_company(potential_company):
                    extracted_slots['company_name'] = potential_company
                    break
        
        # Buscar cargo/posición
        position_patterns = [
            r'soy\s+(director|gerente|ceo|founder|jefe|coordinador)',
            r'cargo\s+(director|gerente|ceo|founder|jefe|coordinador)',
            r'(director|gerente|ceo|founder|jefe|coordinador)\s+de'
        ]
        
        for pattern in position_patterns:
            position_match = re.search(pattern, message_lower)
            if position_match and not current_prospect_info.get('position'):
                extracted_slots['position'] = position_match.group(1).title()
                break
        
        return extracted_slots
    
    def get_next_question(self, prospect_info: Dict[str, Any], conversation_context: List[Dict[str, Any]]) -> Optional[str]:
        """Determinar la próxima pregunta más eficiente"""
        
        analysis = self.analyze_prospect_data(prospect_info)
        missing_essential = analysis['missing_essential']
        
        if not missing_essential:
            return None  # Todos los datos esenciales están completos
        
        # Verificar si podemos preguntar múltiples slots a la vez
        optimal_question = self._find_optimal_question(missing_essential, conversation_context)
        if optimal_question:
            return optimal_question
        
        # Preguntar por el slot más crítico
        priority_order = ['email', 'full_name', 'company_name']
        
        for slot_name in priority_order:
            if slot_name in missing_essential:
                return self.essential_slots[slot_name]['question']
        
        # Fallback
        return missing_essential[0] if missing_essential else None
    
    def _find_optimal_question(self, missing_slots: List[str], conversation_context: List[Dict[str, Any]]) -> Optional[str]:
        """Encontrar la pregunta más eficiente que cubra múltiples slots"""
        
        # Evitar preguntar lo mismo que se preguntó recientemente
        recent_questions = [
            entry.get('content', '') for entry in conversation_context[-3:]
            if entry.get('type') == 'assistant_message'
        ]
        
        # Probar combinaciones en orden de eficiencia
        for slot_combination, question in self.slot_combinations:
            # Verificar si todos los slots de la combinación están faltando
            if all(slot in missing_slots for slot in slot_combination):
                # Verificar que no se haya preguntado recientemente
                if not any(question.lower() in recent.lower() for recent in recent_questions):
                    return question
        
        return None
    
    def _validate_name(self, name: str) -> bool:
        """Validar nombre completo"""
        if not name or len(name.strip()) < 3:
            return False
        
        # Debe tener al menos 2 palabras
        words = name.strip().split()
        if len(words) < 2:
            return False
        
        # Solo letras y espacios
        if not re.match(r'^[A-Za-zÀ-ÿ\s]+$', name):
            return False
        
        # No debe ser placeholder o genérico
        generic_names = ['cliente', 'usuario', 'persona', 'señor', 'señora', 'test', 'prueba']
        if any(generic in name.lower() for generic in generic_names):
            return False
        
        return True
    
    def _validate_email(self, email: str) -> bool:
        """Validar email"""
        if not email:
            return False
        
        # Patrón básico de email
        pattern = r'^[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}$'
        if not re.match(pattern, email):
            return False
        
        # Verificar dominios comunes válidos
        domain = email.split('@')[1].lower()
        
        # Rechazar dominios obviamente falsos
        invalid_domains = ['test.com', 'example.com', 'fake.com', 'temp.com']
        if domain in invalid_domains:
            return False
        
        return True
    
    def _validate_company(self, company: str) -> bool:
        """Validar nombre de empresa"""
        if not company or len(company.strip()) < 2:
            return False
        
        # No debe ser placeholder
        generic_companies = ['empresa', 'compañía', 'negocio', 'test', 'prueba', 'mi empresa']
        if company.lower().strip() in generic_companies:
            return False
        
        return True
    
    def _validate_position(self, position: str) -> bool:
        """Validar cargo/posición"""
        if not position or len(position.strip()) < 3:
            return False
        
        valid_positions = [
            'director', 'gerente', 'ceo', 'founder', 'presidente', 'jefe',
            'coordinador', 'manager', 'supervisor', 'líder', 'encargado'
        ]
        
        return any(pos in position.lower() for pos in valid_positions)
    
    def _validate_industry(self, industry: str) -> bool:
        """Validar industria"""
        if not industry:
            return False
        
        valid_industries = [
            'salud', 'educacion', 'tecnologia', 'retail', 'ecommerce',
            'fintech', 'inmobiliaria', 'restaurante', 'manufacturar'
        ]
        
        return any(ind in industry.lower() for ind in valid_industries)
    
    def _validate_phone(self, phone: str) -> bool:
        """Validar teléfono"""
        if not phone:
            return False
        
        # Remover espacios y caracteres especiales
        clean_phone = re.sub(r'[^\d]', '', phone)
        
        # Debe tener entre 10 y 15 dígitos
        return 10 <= len(clean_phone) <= 15
    
    def _is_valid_slot_value(self, value: Any, slot_name: str) -> bool:
        """Verificar si un valor de slot es válido"""
        if not value:
            return False
        
        if isinstance(value, str) and len(value.strip()) == 0:
            return False
        
        # Aplicar validación específica del slot
        if slot_name in self.essential_slots:
            validator = self.essential_slots[slot_name]['validation']
            return validator(str(value))
        elif slot_name in self.optional_slots:
            validator = self.optional_slots[slot_name]['validation']
            return validator(str(value))
        
        return True
    
    def get_completion_summary(self, prospect_info: Dict[str, Any]) -> Dict[str, Any]:
        """Obtener resumen de completitud de datos"""
        analysis = self.analyze_prospect_data(prospect_info)
        
        return {
            'essential_complete': len(analysis['missing_essential']) == 0,
            'completion_percentage': analysis['completion_rate'],
            'missing_fields': analysis['missing_essential'],
            'next_action': 'schedule' if analysis['ready_to_schedule'] else 'collect_data',
            'collected_fields': list(analysis['current_slots'].keys())
        }
    
    def format_collected_data(self, prospect_info: Dict[str, Any]) -> str:
        """Formatear datos recolectados para confirmación"""
        analysis = self.analyze_prospect_data(prospect_info)
        
        if not analysis['current_slots']:
            return "No hay datos recolectados aún."
        
        formatted_data = []
        for slot_name, slot_status in analysis['current_slots'].items():
            field_label = {
                'full_name': 'Nombre',
                'email': 'Email',
                'company_name': 'Empresa',
                'position': 'Cargo',
                'phone': 'Teléfono'
            }.get(slot_name, slot_name.title())
            
            formatted_data.append(f"• {field_label}: {slot_status.value}")
        
        return "\n".join(formatted_data)

# Instancia global
minimal_slot_manager = MinimalSlotManager()