"""
STT Handler para TDX WhatsApp Bot
Maneja transcripción de audio con OpenAI Whisper
"""

import logging
import asyncio
import os
import tempfile
from typing import Optional, Dict, Any
from datetime import datetime

logger = logging.getLogger("stt_handler")

class STTHandler:
    """Manejador de Speech-to-Text con Whisper"""
    
    def __init__(self, openai_client=None):
        self.openai_client = openai_client
        self.supported_formats = ['.mp3', '.mp4', '.mpeg', '.mpga', '.m4a', '.wav', '.webm', '.ogg']
        self.max_file_size = 25 * 1024 * 1024  # 25MB límite OpenAI
        self.temp_dir = tempfile.gettempdir()
        
        # Configuración de transcripción
        self.transcription_config = {
            'model': 'whisper-1',
            'language': 'es',  # Español
            'response_format': 'text',
            'temperature': 0.2  # Más determinístico
        }
        
        # Fallbacks para errores comunes
        self.fallback_responses = [
            "No pude procesar el audio. ¿Puedes escribir tu mensaje?",
            "Audio no claro. ¿Podrías repetir por escrito?",
            "Problema técnico audio. ¿Me escribes?"
        ]
    
    async def transcribe_audio(self, audio_file_path: str, 
                              user_id: Optional[str] = None) -> Dict[str, Any]:
        """Transcribir archivo de audio a texto"""
        try:
            # Verificar que el cliente OpenAI esté disponible
            if not self.openai_client:
                logger.error("OpenAI client no disponible para STT")
                return {
                    'success': False,
                    'text': self.fallback_responses[0],
                    'error': 'OpenAI client not available'
                }
            
            # Validar archivo
            validation_result = self._validate_audio_file(audio_file_path)
            if not validation_result['valid']:
                return {
                    'success': False,
                    'text': validation_result['fallback'],
                    'error': validation_result['error']
                }
            
            # Procesar transcripción
            start_time = datetime.now()
            
            with open(audio_file_path, "rb") as audio_file:
                transcript = await self.openai_client.audio.transcriptions.create(
                    file=audio_file,
                    **self.transcription_config
                )
            
            processing_time = (datetime.now() - start_time).total_seconds()
            
            # Limpiar y validar transcripción
            cleaned_text = self._clean_transcription(transcript.text if hasattr(transcript, 'text') else str(transcript))
            
            if not cleaned_text or len(cleaned_text.strip()) < 3:
                logger.warning(f"Transcripción muy corta: '{cleaned_text}'")
                return {
                    'success': False,
                    'text': "Audio no claro. ¿Podrías repetir por escrito?",
                    'error': 'Transcription too short'
                }
            
            # Log exitoso
            logger.info(f"STT exitoso: {len(cleaned_text)} chars, {processing_time:.2f}s, user: {user_id}")
            logger.debug(f"Transcripción: {cleaned_text[:100]}...")
            
            return {
                'success': True,
                'text': cleaned_text,
                'processing_time': processing_time,
                'char_count': len(cleaned_text),
                'user_id': user_id
            }
            
        except Exception as e:
            logger.error(f"Error en transcripción STT: {str(e)}")
            
            # Determinar tipo de error y fallback apropiado
            error_type = self._classify_error(str(e))
            fallback_text = self._get_error_fallback(error_type)
            
            return {
                'success': False,
                'text': fallback_text,
                'error': str(e),
                'error_type': error_type
            }
    
    def _validate_audio_file(self, file_path: str) -> Dict[str, Any]:
        """Validar archivo de audio antes de procesar"""
        try:
            # Verificar si el archivo existe
            if not os.path.exists(file_path):
                return {
                    'valid': False,
                    'error': 'File not found',
                    'fallback': "Archivo de audio no encontrado. ¿Puedes enviarlo de nuevo?"
                }
            
            # Verificar tamaño
            file_size = os.path.getsize(file_path)
            if file_size > self.max_file_size:
                return {
                    'valid': False,
                    'error': 'File too large',
                    'fallback': "Audio muy largo. ¿Puedes enviarlo más corto o escribir?"
                }
            
            if file_size < 100:  # Muy pequeño, probablemente corrupto
                return {
                    'valid': False,
                    'error': 'File too small',
                    'fallback': "Audio muy corto. ¿Puedes repetir?"
                }
            
            # Verificar extensión
            file_ext = os.path.splitext(file_path)[1].lower()
            if file_ext not in self.supported_formats:
                return {
                    'valid': False,
                    'error': 'Unsupported format',
                    'fallback': "Formato audio no soportado. ¿Puedes escribir tu mensaje?"
                }
            
            return {'valid': True}
            
        except Exception as e:
            logger.error(f"Error validando archivo audio: {e}")
            return {
                'valid': False,
                'error': str(e),
                'fallback': "Error procesando audio. ¿Puedes escribir?"
            }
    
    def _clean_transcription(self, text: str) -> str:
        """Limpiar y normalizar transcripción"""
        if not text:
            return ""
        
        # Limpiar espacios extra
        text = ' '.join(text.split())
        
        # Remover artefactos comunes de Whisper
        artifacts = [
            'gracias por ver este video',
            'suscríbete',
            'like',
            'comentar',
            'subtítulos creados por la comunidad',
            '♪♪♪',
            '[música]',
            '[aplausos]',
            '[risas]'
        ]
        
        text_lower = text.lower()
        for artifact in artifacts:
            if artifact in text_lower:
                # Remover artefacto manteniendo el resto
                text = text.replace(artifact, '').replace(artifact.upper(), '').replace(artifact.capitalize(), '')
        
        # Limpiar espacios extra después de remover artefactos
        text = ' '.join(text.split())
        
        return text.strip()
    
    def _classify_error(self, error_message: str) -> str:
        """Clasificar tipo de error para mejor fallback"""
        error_lower = error_message.lower()
        
        if 'timeout' in error_lower or 'timed out' in error_lower:
            return 'timeout'
        elif 'network' in error_lower or 'connection' in error_lower:
            return 'network'
        elif 'file' in error_lower and 'size' in error_lower:
            return 'file_size'
        elif 'format' in error_lower or 'codec' in error_lower:
            return 'format'
        elif 'quota' in error_lower or 'limit' in error_lower:
            return 'quota'
        else:
            return 'unknown'
    
    def _get_error_fallback(self, error_type: str) -> str:
        """Obtener mensaje de fallback según tipo de error"""
        fallbacks = {
            'timeout': "Audio muy largo. ¿Puedes escribir tu mensaje?",
            'network': "Problema de conexión. ¿Me escribes?",
            'file_size': "Audio muy pesado. ¿Mensaje más corto?",
            'format': "Formato no soportado. ¿Puedes escribir?",
            'quota': "Servicio ocupado. ¿Me escribes?",
            'unknown': "Error técnico audio. ¿Podrías escribir?"
        }
        
        return fallbacks.get(error_type, self.fallback_responses[0])
    
    async def health_check(self) -> Dict[str, Any]:
        """Verificar estado del servicio STT"""
        try:
            if not self.openai_client:
                return {
                    'status': 'error',
                    'message': 'OpenAI client not available',
                    'available': False
                }
            
            # Test básico (sin archivo real)
            return {
                'status': 'ok',
                'message': 'STT service available',
                'available': True,
                'supported_formats': self.supported_formats,
                'max_file_size_mb': self.max_file_size / (1024 * 1024)
            }
            
        except Exception as e:
            logger.error(f"STT health check failed: {e}")
            return {
                'status': 'error',
                'message': str(e),
                'available': False
            }
    
    def get_audio_info(self, file_path: str) -> Dict[str, Any]:
        """Obtener información del archivo de audio"""
        try:
            if not os.path.exists(file_path):
                return {'error': 'File not found'}
            
            file_size = os.path.getsize(file_path)
            file_ext = os.path.splitext(file_path)[1].lower()
            
            return {
                'file_path': file_path,
                'size_bytes': file_size,
                'size_mb': round(file_size / (1024 * 1024), 2),
                'format': file_ext,
                'supported': file_ext in self.supported_formats,
                'valid_size': file_size <= self.max_file_size,
                'created': datetime.fromtimestamp(os.path.getctime(file_path)).isoformat()
            }
            
        except Exception as e:
            return {'error': str(e)}
    
    def cleanup_temp_files(self, older_than_hours: int = 1):
        """Limpiar archivos temporales antiguos"""
        try:
            import glob
            from datetime import timedelta
            
            cutoff_time = datetime.now() - timedelta(hours=older_than_hours)
            pattern = os.path.join(self.temp_dir, "stt_*")
            
            cleaned_count = 0
            for file_path in glob.glob(pattern):
                try:
                    file_time = datetime.fromtimestamp(os.path.getctime(file_path))
                    if file_time < cutoff_time:
                        os.remove(file_path)
                        cleaned_count += 1
                except:
                    continue  # Ignorar errores individuales
            
            logger.info(f"Limpieza STT: {cleaned_count} archivos temporales eliminados")
            return cleaned_count
            
        except Exception as e:
            logger.error(f"Error limpiando archivos STT: {e}")
            return 0

# Función helper para crear instancia
def create_stt_handler(openai_client=None) -> STTHandler:
    """Crear instancia del handler STT"""
    return STTHandler(openai_client=openai_client)