"""
Service Mapper para TDX WhatsApp Bot
Mapea keywords en mensajes a servicios TDX específicos
"""

import logging
import re
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass

logger = logging.getLogger("service_mapper")

@dataclass
class ServiceMatch:
    """Resultado de detección de servicio"""
    service: str
    confidence: float
    matched_keywords: List[str]
    industry_hint: Optional[str] = None

class ServiceMapper:
    """Mapeador de keywords a servicios TDX Core"""
    
    def __init__(self):
        self.service_keywords = self._load_service_keywords()
        self.industry_keywords = self._load_industry_keywords()
        self.synonym_map = self._load_synonyms()
        
    def _load_service_keywords(self) -> Dict[str, Dict[str, List[str]]]:
        """Keywords organizados por servicio y nivel de especificidad"""
        return {
            'AI_GENERAL': {
                'high': [  # Alta especificidad - Consultas generales sobre IA
                    'inteligencia artificial', 'artificial intelligence', 'ia', 'ai',
                    'soluciones ia', 'servicios ia', 'tecnologia ia', 'ai solutions',
                    'que es ia', 'como funciona ia', 'usos ia'
                ],
                'medium': [  # Media especificidad
                    'inteligente', 'automatizacion', 'machine learning', 'ml',
                    'algoritmos', 'smart', 'artificial', 'automated'
                ],
                'low': [  # Baja especificidad
                    'tecnologia', 'innovation', 'digital', 'moderno'
                ]
            },
            'AI_CHATBOT': {
                'high': [  # Alta especificidad
                    'chatbot multiagente', 'bot conversacional', 'ai chatbot',
                    'chat inteligente', 'asistente virtual chat'
                ],
                'medium': [  # Media especificidad  
                    'chatbot', 'bot', 'chat automatico', 'respuestas automaticas',
                    'atencion automatizada', 'servicio cliente automatico'
                ],
                'low': [  # Baja especificidad
                    'automatizar', 'atencion', 'consultas', 'soporte',
                    '24/7', 'responder', 'atender'
                ]
            },
            'AI_VOICE': {
                'high': [
                    'ai voice', 'voice assistant', 'asistente voz', 'llamadas ia',
                    'bot telefonico', 'marcador automatico'
                ],
                'medium': [
                    'voz artificial', 'llamadas automaticas', 'voice bot',
                    'telefono automatico', 'outbound calls'
                ],
                'low': [
                    'voz', 'llamada', 'telefono', 'llamar', 'phone',
                    'telefonico', 'vocal'
                ]
            },
            'AI_ASSISTANT_WHATSAPP': {
                'high': [
                    'bot whatsapp', 'whatsapp bot', 'ai whatsapp assistant',
                    'automatizar whatsapp', 'whatsapp automatico'
                ],
                'medium': [
                    'whatsapp business', 'mensajes automaticos whatsapp',
                    'respuestas whatsapp', 'chat whatsapp'
                ],
                'low': [
                    'whatsapp', 'wa', 'mensajes', 'messaging',
                    'mensajeria'
                ]
            },
            'AI_VIDEO': {
                'high': [
                    'avatar digital', 'ai avatar', 'video personalizado ia',
                    'asistente video', 'avatar realista'
                ],
                'medium': [
                    'avatar', 'video avatar', 'persona virtual',
                    'video personalizado', 'onboarding video'
                ],
                'low': [
                    'video', 'onboarding', 'entrenamientos', 'capacitacion',
                    'entrenamiento virtual'
                ]
            },
            'WEB_STARTER': {
                'high': [
                    'web starter', 'pagina web basica', 'web simple',
                    'vitrina digital', 'landing page'
                ],
                'medium': [
                    'pagina web', 'sitio web', 'website', 'web',
                    'presencia digital'
                ],
                'low': [
                    'sitio', 'pagina', 'internet', 'online'
                ]
            },
            'WEB_BUSINESS': {
                'high': [
                    'web profesional', 'web business', 'web empresarial',
                    'sitio corporativo', 'web avanzada'
                ],
                'medium': [
                    'web comercial', 'negocio online', 'portal empresarial',
                    'web con chat'
                ],
                'low': [
                    'profesional', 'empresarial', 'corporativo', 'comercial'
                ]
            },
            'WEB_ECOMMERCE': {
                'high': [
                    'tienda online', 'ecommerce', 'shop online',
                    'marketplace', 'catalogo online'
                ],
                'medium': [
                    'venta online', 'store online', 'carrito compras',
                    'comercio electronico'
                ],
                'low': [
                    'vender', 'tienda', 'catalogo', 'productos',
                    'ventas', 'commerce'
                ]
            },
            'MVP': {
                'high': [
                    'mvp desarrollo', 'producto minimo viable', 'prototipo funcional',
                    'mvp 15 dias', 'demo producto'
                ],
                'medium': [
                    'mvp', 'prototipo', 'demo', 'poc',
                    'prueba concepto'
                ],
                'low': [
                    'startup', 'emprendimiento', 'validar', 'idea',
                    'nuevo producto'
                ]
            },
            'WHATSAPP_API': {
                'high': [
                    'whatsapp api', 'api whatsapp business', 'meta api',
                    'whatsapp oficial', 'business api'
                ],
                'medium': [
                    'integracion whatsapp', 'conectar whatsapp',
                    'api business', 'whatsapp integration'
                ],
                'low': [
                    'api', 'integracion', 'conectar', 'integration'
                ]
            },
            'SEO': {
                'high': [
                    'posicionamiento seo', 'optimizacion seo', 'seo google',
                    'aparecer google', 'ranking google'
                ],
                'medium': [
                    'seo', 'google', 'posicionamiento', 'optimizacion web',
                    'busqueda google'
                ],
                'low': [
                    'aparecer', 'busqueda', 'google maps', 'visibilidad',
                    'encontrar'
                ]
            }
        }
    
    def _load_industry_keywords(self) -> Dict[str, List[str]]:
        """Keywords para detectar industria"""
        return {
            'salud': [
                'clinica', 'hospital', 'medico', 'doctor', 'paciente',
                'consulta medica', 'cita medica', 'eps', 'salud',
                'odontologia', 'veterinaria', 'farmacia', 'laboratorio',
                'cirugia', 'tratamiento', 'diagnostico'
            ],
            'ecommerce': [
                'tienda', 'venta', 'productos', 'catalogo', 'inventario',
                'pedidos', 'envios', 'domicilios', 'marketplace',
                'retail', 'comercio', 'mercancia'
            ],
            'educacion': [
                'colegio', 'universidad', 'academia', 'curso', 'estudiante',
                'capacitacion', 'entrenamiento', 'educativo', 'aprendizaje',
                'instituto', 'escuela', 'formacion'
            ],
            'restaurante': [
                'restaurante', 'comida', 'menu', 'delivery', 'domicilio',
                'cocina', 'chef', 'platos', 'gastronomia',
                'bar', 'cafe', 'pizzeria'
            ],
            'gimnasio': [
                'gimnasio', 'fitness', 'ejercicio', 'entrenamiento',
                'membresia', 'rutina', 'deporte', 'fisico',
                'crossfit', 'yoga', 'pilates'
            ],
            'inmobiliaria': [
                'inmobiliaria', 'propiedad', 'casa', 'apartamento',
                'arriendo', 'venta', 'finca raiz', 'bienes raices',
                'lote', 'oficina', 'local'
            ],
            'fintech': [
                'fintech', 'finanzas', 'banco', 'credito', 'prestamo',
                'inversion', 'pagos', 'billetera digital',
                'cobranza', 'cartera'
            ],
            'startup': [
                'startup', 'emprendimiento', 'innovacion', 'tecnologia',
                'disrupcion', 'escalabilidad', 'inversionistas'
            ]
        }
    
    def _load_synonyms(self) -> Dict[str, str]:
        """Mapa de sinónimos para normalizar términos"""
        return {
            'chatbot': 'chatbot',
            'bot': 'chatbot', 
            'robot': 'chatbot',
            'asistente': 'chatbot',
            
            'web': 'website',
            'pagina': 'website',
            'sitio': 'website',
            
            'tienda': 'ecommerce',
            'shop': 'ecommerce',
            'store': 'ecommerce',
            
            'voz': 'voice',
            'telefono': 'voice',
            'llamada': 'voice'
        }
    
    def detect_service(self, text: str) -> Optional[ServiceMatch]:
        """Detectar servicio principal en el texto"""
        text_normalized = self._normalize_text(text)
        
        service_scores = {}
        all_matches = {}
        
        # Evaluar cada servicio
        for service, levels in self.service_keywords.items():
            total_score = 0
            matched_keywords = []
            
            # Puntuación por nivel de especificidad
            for level, keywords in levels.items():
                level_weight = {'high': 3, 'medium': 2, 'low': 1}[level]
                
                for keyword in keywords:
                    if keyword.lower() in text_normalized:
                        total_score += level_weight
                        matched_keywords.append(keyword)
            
            if total_score > 0:
                service_scores[service] = total_score
                all_matches[service] = matched_keywords
        
        # Retornar el servicio con mayor puntuación
        if service_scores:
            best_service = max(service_scores.items(), key=lambda x: x[1])
            service, score = best_service
            
            # Calcular confianza (normalizada)
            max_possible_score = 10  # Aproximado
            confidence = min(0.95, score / max_possible_score)
            
            # Detectar industria relacionada
            industry_hint = self._detect_industry_hint(text_normalized)
            
            return ServiceMatch(
                service=service,
                confidence=confidence,
                matched_keywords=all_matches[service],
                industry_hint=industry_hint
            )
        
        return None
    
    def detect_multiple_services(self, text: str) -> List[ServiceMatch]:
        """Detectar múltiples servicios mencionados"""
        text_normalized = self._normalize_text(text)
        matches = []
        
        for service, levels in self.service_keywords.items():
            total_score = 0
            matched_keywords = []
            
            for level, keywords in levels.items():
                level_weight = {'high': 3, 'medium': 2, 'low': 1}[level]
                
                for keyword in keywords:
                    if keyword.lower() in text_normalized:
                        total_score += level_weight
                        matched_keywords.append(keyword)
            
            if total_score > 0:
                confidence = min(0.95, total_score / 10)
                industry_hint = self._detect_industry_hint(text_normalized)
                
                matches.append(ServiceMatch(
                    service=service,
                    confidence=confidence,
                    matched_keywords=matched_keywords,
                    industry_hint=industry_hint
                ))
        
        # Ordenar por confianza descendente
        return sorted(matches, key=lambda x: x.confidence, reverse=True)
    
    def _normalize_text(self, text: str) -> str:
        """Normalizar texto para mejor detección"""
        # Convertir a minúsculas
        text = text.lower()
        
        # Aplicar sinónimos
        for original, normalized in self.synonym_map.items():
            text = text.replace(original, normalized)
        
        # Limpiar caracteres especiales
        text = re.sub(r'[^\w\s]', ' ', text)
        
        # Normalizar espacios
        text = re.sub(r'\s+', ' ', text).strip()
        
        return text
    
    def _detect_industry_hint(self, text: str) -> Optional[str]:
        """Detectar industria mencionada en el texto"""
        for industry, keywords in self.industry_keywords.items():
            for keyword in keywords:
                if keyword.lower() in text:
                    return industry
        return None
    
    def get_service_priority(self, services: List[str]) -> List[str]:
        """Ordenar servicios por prioridad de negocio"""
        priority_order = [
            'WEB_ECOMMERCE',    # Mayor valor
            'AI_VOICE',         # Alta conversión
            'AI_CHATBOT',       # Escalable
            'MVP',              # Urgente
            'WEB_BUSINESS',     # Profesional
            'AI_VIDEO',         # Innovador
            'WHATSAPP_API',     # Específico
            'WEB_STARTER',      # Básico
            'SEO'               # Complementario
        ]
        
        return sorted(services, key=lambda x: priority_order.index(x) 
                     if x in priority_order else len(priority_order))
    
    def is_service_combination_valid(self, services: List[str]) -> bool:
        """Verificar si la combinación de servicios es válida"""
        # Combinaciones incompatibles
        incompatible = [
            {'WEB_STARTER', 'WEB_BUSINESS', 'WEB_ECOMMERCE'},  # Solo un tipo de web
            {'AI_ASSISTANT_WHATSAPP', 'WHATSAPP_API'}  # Redundante
        ]
        
        services_set = set(services)
        
        for incompatible_set in incompatible:
            if len(services_set.intersection(incompatible_set)) > 1:
                return False
        
        return True

# Instancia global
service_mapper = ServiceMapper()