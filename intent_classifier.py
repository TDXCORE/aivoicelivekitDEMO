"""
Intent Classifier para TDX WhatsApp Bot
Clasifica intenciones Off-Topic y detecta servicios TDX específicos
"""

import logging
import re
from typing import Dict, Any, List, Optional
from dataclasses import dataclass

logger = logging.getLogger("intent_classifier")

@dataclass
class IntentResult:
    """Resultado de clasificación de intención"""
    category: str
    confidence: float
    detected_service: Optional[str] = None
    industry: Optional[str] = None
    signals: List[str] = None

class IntentClassifier:
    """Clasificador de intenciones Off-Topic y servicios TDX"""
    
    def __init__(self):
        self.off_topic_patterns = self._load_off_topic_patterns()
        self.service_keywords = self._load_service_keywords()
        self.industry_keywords = self._load_industry_keywords()
        
    def _load_off_topic_patterns(self) -> Dict[str, List[str]]:
        """Patrones para detectar conversaciones Off-Topic"""
        return {
            'emotional': [
                'triste', 'deprimido', 'depresion', 'ansiedad', 'solo', 'soledad',
                'problemas personales', 'crisis', 'ayuda emocional', 'psicolog',
                'novia', 'novio', 'pareja', 'relacion', 'familia', 'padres',
                'divorcio', 'separacion', 'hijos', 'muerte', 'enfermedad grave',
                'suicidio', 'autolesion', 'dolor', 'sufro', 'lloro'
            ],
            'harassment': [
                'linda', 'hermosa', 'bella', 'guapa', 'sexy', 'atractiva',
                'salir contigo', 'cita romantica', 'te amo', 'te quiero',
                'eres soltera', 'tienes novio', 'fotos personales', 'selfie',
                'whatsapp personal', 'numero personal', 'conocerte mejor',
                'encuentro personal', 'hotel', 'besos', 'abrazo'
            ],
            'small_talk': [
                'como estas', 'que tal', 'como vas', 'todo bien', 'como amaneciste',
                'buen dia', 'buenas tardes', 'buenas noches', 'que haces',
                'clima', 'calor', 'frio', 'lluvia', 'tiempo', 'covid',
                'futbol', 'deportes', 'musica', 'peliculas', 'fin de semana',
                'vacaciones', 'comida', 'almuerzo', 'desayuno', 'cena'
            ]
        }
    
    def _load_service_keywords(self) -> Dict[str, List[str]]:
        """Keywords para detectar servicios TDX específicos"""
        return {
            'AI_CHATBOT': [
                'chatbot', 'bot', 'multiagente', 'automatizar respuestas',
                'atencion cliente', 'servicio cliente', '24/7', 'chat automatico',
                'respuesta automatica', 'consultas automaticas', 'faq automatico',
                'conversacional', 'dialogo automatico'
            ],
            'AI_VOICE': [
                'voz', 'llamada', 'telefono', 'voice', 'llamar', 'marcador',
                'outbound', 'phone', 'vocal', 'speaking', 'telefonico',
                'llamadas automaticas', 'voice assistant', 'asistente voz',
                'ivr', 'call center'
            ],
            'AI_ASSISTANT_WHATSAPP': [
                'whatsapp', 'wa', 'mensajes whatsapp', 'chat whatsapp',
                'mensajeria', 'whatsapp business', 'wp', 'messaging',
                'automatizar whatsapp', 'bot whatsapp', 'respuestas whatsapp'
            ],
            'AI_VIDEO': [
                'avatar', 'video', 'onboarding', 'entrenamientos', 'capacitacion',
                'virtual assistant', 'personalized video', 'avatar digital',
                'entrenamiento virtual', 'induccion virtual', 'video personalizado',
                'avatar realista', 'persona virtual'
            ],
            'WEB_STARTER': [
                'pagina web', 'sitio web', 'website', 'vitrina digital',
                'landing page', 'presencia digital', 'web basica',
                'sitio internet', 'pagina internet', 'web simple'
            ],
            'WEB_BUSINESS': [
                'web profesional', 'negocio online', 'web empresarial',
                'sitio comercial', 'web corporativa', 'portal empresarial',
                'web avanzada', 'sitio profesional'
            ],
            'WEB_ECOMMERCE': [
                'ecommerce', 'tienda online', 'vender online', 'carrito compras',
                'commerce', 'ventas digitales', 'marketplace', 'shop online',
                'store online', 'catalogo online', 'venta internet'
            ],
            'MVP': [
                'mvp', 'prototipo', 'demo', 'startup', 'validacion idea',
                'producto minimo', 'poc', 'pilot', 'prueba concepto',
                'validar negocio', 'emprendimiento', 'idea negocio'
            ],
            'WHATSAPP_API': [
                'api whatsapp', 'integracion whatsapp', 'whatsapp oficial',
                'meta api', 'business api', 'whatsapp api business',
                'conectar whatsapp', 'integrar whatsapp'
            ],
            'SEO': [
                'seo', 'google', 'aparecer google', 'posicionamiento',
                'busqueda google', 'ranking google', 'optimizacion web',
                'analytics', 'google maps', 'busquedas', 'visibilidad web'
            ]
        }
    
    def _load_industry_keywords(self) -> Dict[str, List[str]]:
        """Keywords para detectar industria del cliente"""
        return {
            'salud': [
                'clinica', 'hospital', 'medico', 'doctor', 'paciente',
                'consulta medica', 'cita medica', 'eps', 'salud',
                'odontologia', 'veterinaria', 'farmacia', 'laboratorio'
            ],
            'ecommerce': [
                'tienda', 'venta', 'productos', 'catalogo', 'inventario',
                'pedidos', 'envios', 'domicilios', 'marketplace'
            ],
            'educacion': [
                'colegio', 'universidad', 'academia', 'curso', 'estudiante',
                'capacitacion', 'entrenamiento', 'educativo', 'aprendizaje'
            ],
            'restaurante': [
                'restaurante', 'comida', 'menu', 'delivery', 'domicilio',
                'cocina', 'chef', 'platos', 'gastronomia'
            ],
            'gimnasio': [
                'gimnasio', 'fitness', 'ejercicio', 'entrenamiento',
                'membresia', 'rutina', 'deporte', 'fisico'
            ],
            'inmobiliaria': [
                'inmobiliaria', 'propiedad', 'casa', 'apartamento',
                'arriendo', 'venta', 'finca raiz'
            ],
            'fintech': [
                'fintech', 'finanzas', 'banco', 'credito', 'prestamo',
                'inversion', 'pagos', 'billetera digital'
            ],
            'startup': [
                'startup', 'emprendimiento', 'innovacion', 'tecnologia',
                'disrupcion', 'escalabilidad'
            ]
        }
    
    def classify(self, text: str) -> IntentResult:
        """Clasificar intención del mensaje"""
        text_lower = text.lower()
        
        # 1. Verificar Off-Topic primero
        off_topic_result = self._check_off_topic(text_lower)
        if off_topic_result['is_off_topic']:
            return IntentResult(
                category=off_topic_result['category'],
                confidence=off_topic_result['confidence']
            )
        
        # 2. Detectar servicio TDX
        service_detection = self._detect_service(text_lower)
        
        # 3. Detectar industria
        industry_detection = self._detect_industry(text_lower)
        
        return IntentResult(
            category='tdx_service',
            confidence=service_detection['confidence'],
            detected_service=service_detection['service'],
            industry=industry_detection['industry'],
            signals=service_detection['signals']
        )
    
    def _check_off_topic(self, text: str) -> Dict[str, Any]:
        """Verificar si el mensaje es Off-Topic"""
        for category, patterns in self.off_topic_patterns.items():
            matches = 0
            for pattern in patterns:
                if pattern in text:
                    matches += 1
            
            if matches > 0:
                confidence = min(0.9, matches * 0.3)  # Max 0.9 confidence
                return {
                    'is_off_topic': True,
                    'category': category,
                    'confidence': confidence
                }
        
        return {'is_off_topic': False, 'category': None, 'confidence': 0.0}
    
    def _detect_service(self, text: str) -> Dict[str, Any]:
        """Detectar servicio TDX mencionado"""
        best_match = {'service': None, 'confidence': 0.0, 'signals': []}
        
        for service, keywords in self.service_keywords.items():
            matches = []
            for keyword in keywords:
                if keyword in text:
                    matches.append(keyword)
            
            if matches:
                confidence = min(0.95, len(matches) * 0.2)
                if confidence > best_match['confidence']:
                    best_match = {
                        'service': service,
                        'confidence': confidence,
                        'signals': matches
                    }
        
        return best_match
    
    def _detect_industry(self, text: str) -> Dict[str, Any]:
        """Detectar industria del cliente"""
        for industry, keywords in self.industry_keywords.items():
            for keyword in keywords:
                if keyword in text:
                    return {
                        'industry': industry,
                        'confidence': 0.8,
                        'keyword': keyword
                    }
        
        return {'industry': 'general', 'confidence': 0.5, 'keyword': None}
    
    def detect_price_inquiry(self, text: str) -> bool:
        """Detectar consultas sobre precios"""
        price_keywords = [
            'precio', 'costo', 'cuanto cuesta', 'valor', 'cotizar',
            'cotizacion', 'presupuesto', 'inversion', 'tarifa',
            'cuanto vale', 'que vale', 'cuanto es', 'precio de'
        ]
        
        text_lower = text.lower()
        return any(keyword in text_lower for keyword in price_keywords)

# Instancia global
intent_classifier = IntentClassifier()