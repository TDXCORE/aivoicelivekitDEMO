#!/usr/bin/env python3
"""
Test simple de keywords sin dependencias externas
"""

def test_schedule_keywords():
    """Test simple de detección de keywords"""
    print("TESTING SCHEDULE KEYWORDS DETECTION")
    print("=" * 50)
    
    # Keywords para agendamiento (copiado del bot)
    SCHEDULE_KEYWORDS = [
        "agendar", "agenda", "agendo", "programar", "programa",
        "reunion", "cita", "meeting", "encuentro",
        "disponibilidad", "horario", "hora", "cuando",
        "reservar", "apartar", "calendario", "fecha"
    ]
    
    # Test messages
    test_messages = [
        "hola",
        "quiero agendar",
        "me gustaria programar una reunion", 
        "cuando tienes disponibilidad?",
        "necesito una cita",
        "quiero hablar con un ejecutivo",
        "agendar una reunion",
        "programar",
        "reunion manana"
    ]
    
    for message in test_messages:
        message_lower = message.lower()
        detected_keywords = []
        
        for keyword in SCHEDULE_KEYWORDS:
            if keyword in message_lower:
                detected_keywords.append(keyword)
        
        print(f"Message: '{message}'")
        if detected_keywords:
            print(f"   -> SCHEDULE DETECTED: {detected_keywords}")
        else:
            print(f"   -> No schedule keywords detected")
        print()

def test_transfer_keywords():
    """Test simple de detección de keywords de transferencia"""
    print("TESTING TRANSFER KEYWORDS DETECTION")
    print("=" * 50)
    
    # Keywords de transferencia (copiado del bot)
    TRANSFER_KEYWORDS = [
        "ejecutivo", "vendedor", "asesor", "consultor", "especialista",
        "hablar con alguien", "persona real", "humano", "representante", "agente",
        "gerente", "director", "supervisor", "jefe",
        "experto", "tecnico", "ingeniero",
        "quiero hablar con", "me conecta con", "transfiere", "transferir",
        "no quiero bot", "quiero persona", "alguien mas",
        "comunicar con", "conectar con", "pasar con"
    ]
    
    # Test messages
    test_messages = [
        "hola",
        "quiero agendar",
        "quiero hablar con un ejecutivo",
        "me conecta con un vendedor",
        "necesito un humano",
        "transferir a especialista",
        "hablar con alguien",
        "persona real"
    ]
    
    for message in test_messages:
        message_lower = message.lower()
        detected_keywords = []
        
        for keyword in TRANSFER_KEYWORDS:
            if keyword in message_lower:
                detected_keywords.append(keyword)
        
        print(f"Message: '{message}'")
        if detected_keywords:
            print(f"   -> TRANSFER DETECTED: {detected_keywords}")
        else:
            print(f"   -> No transfer keywords detected")
        print()

def main():
    """Función principal"""
    print("SIMPLE KEYWORD DETECTION TEST")
    print("=" * 50)
    print()
    
    test_schedule_keywords()
    print()
    test_transfer_keywords()
    
    print("TEST COMPLETED")
    print()
    print("EXPECTED BEHAVIOR:")
    print("- 'quiero agendar' should trigger SCHEDULE")
    print("- 'quiero hablar con un ejecutivo' should trigger TRANSFER")
    print("- 'me gustaria programar una reunion' should trigger SCHEDULE")
    print("- 'cuando tienes disponibilidad' should trigger SCHEDULE")

if __name__ == "__main__":
    main()