"""
Test Integration Module
Wrapper around the existing WhatsApp agent for isolated testing
"""

import sys
import os
import logging
from datetime import datetime
from typing import Optional, Dict, Any

# Add the src directory to the Python path
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'src'))

from agents.whatsapp_agent import TDXWhatsAppAgentClean
from .test_storage import TestStorage

logger = logging.getLogger("test-integration")


class TestAgentWrapper:
    """
    Wrapper around the existing TDXWhatsAppAgentClean for testing purposes.
    Uses the exact same agent code but redirects Chatwoot calls to local storage.
    """
    
    def __init__(self, contact_name: str = "TestUser", company_name: str = "Test Company"):
        """Initialize the test wrapper with a fresh agent instance"""
        self.storage = TestStorage()
        self.test_session_id = f"test_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        
        # Create the same agent as production but for testing
        self.agent = TDXWhatsAppAgentClean(
            contact_name=contact_name,
            company_name=company_name,
            prospect_info={
                "name": contact_name,
                "company": company_name,
                "phone": "+1234567890",  # Test phone number
                "source": "test_interface"
            },
            conversation_id=999999  # Test conversation ID
        )
        
        # Store original methods before monkey patching
        self._original_send_to_chatwoot = self.agent._send_to_chatwoot
        
        # Monkey patch the Chatwoot send method to use our test storage
        self.agent._send_to_chatwoot = self._mock_chatwoot_send
        
        logger.info(f"🧪 Test Agent Wrapper initialized for {contact_name}")
        logger.info(f"🧪 Session ID: {self.test_session_id}")
        
    async def _mock_chatwoot_send(self, message: str) -> bool:
        """
        Mock the Chatwoot send method to save to test storage instead
        """
        try:
            # Save the bot message to our test storage
            self.storage.save_bot_message(message, metadata={
                'session_id': self.test_session_id,
                'agent_state': self.agent.collected_data.copy(),
                'timestamp': datetime.now().isoformat()
            })
            
            # Also save the collected data state
            self.storage.save_conversation_data(self.agent.collected_data)
            
            logger.info(f"📝 Test message saved: {message[:50]}...")
            return True
            
        except Exception as e:
            logger.error(f"❌ Error saving test message: {e}")
            return False
    
    async def send_message(self, user_message: str) -> Optional[str]:
        """
        Send a message to the agent and get response
        Exactly like production but saves to test storage
        """
        try:
            # Save user message to test storage
            self.storage.save_user_message(user_message, metadata={
                'session_id': self.test_session_id,
                'timestamp': datetime.now().isoformat()
            })
            
            logger.info(f"👤 User message: {user_message}")
            
            # Process message with the SAME agent as production
            response = await self.agent.process_message(user_message)
            
            if response:
                logger.info(f"🤖 Bot response: {response[:100]}...")
                
                # The response is already saved via our mocked _send_to_chatwoot method
                return response
            else:
                logger.warning("⚠️ No response generated")
                return None
                
        except Exception as e:
            logger.error(f"❌ Error processing message: {e}")
            return f"Error: {str(e)}"
    
    def reset_conversation(self):
        """
        Reset the conversation for a fresh test
        Creates a new agent instance to ensure clean state
        """
        # Store current session info
        old_session = self.test_session_id
        
        # Clear storage
        self.storage.clear()
        
        # Create new session with microseconds to ensure uniqueness
        import time
        self.test_session_id = f"test_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{int(time.time() * 1000) % 10000}"
        
        # Create fresh agent instance
        self.agent = TDXWhatsAppAgentClean(
            contact_name="TestUser",
            company_name="Test Company", 
            prospect_info={
                "name": "TestUser",
                "company": "Test Company",
                "phone": "+1234567890",
                "source": "test_interface"
            },
            conversation_id=999999
        )
        
        # Re-apply monkey patch
        self.agent._send_to_chatwoot = self._mock_chatwoot_send
        
        logger.info(f"🔄 Conversation reset - Old: {old_session}, New: {self.test_session_id}")
        
    def get_conversation_history(self) -> Dict[str, Any]:
        """Get the full conversation history and stats"""
        return {
            'session_id': self.test_session_id,
            'conversation': self.storage.get_conversation(),
            'agent_state': self.agent.collected_data.copy(),
            'stats': self.storage.get_stats(),
            'full_export': self.storage.export_conversation()
        }
    
    def get_agent_state(self) -> Dict[str, Any]:
        """Get current agent state for debugging"""
        return {
            'collected_data': self.agent.collected_data.copy(),
            'conversation_log_count': len(self.agent.conversation_log),
            'last_conversation_entries': self.agent.conversation_log[-3:] if self.agent.conversation_log else [],
            'contact_name': self.agent.contact_name,
            'company_name': self.agent.company_name,
            'conversation_id': self.agent.conversation_id
        }
    
    def get_test_summary(self) -> Dict[str, Any]:
        """Get a summary of the test session"""
        stats = self.storage.get_stats()
        state = self.get_agent_state()
        
        return {
            'session_id': self.test_session_id,
            'duration': stats['session_duration'],
            'message_count': stats['total_messages'],
            'user_messages': stats['user_messages'],
            'bot_messages': stats['bot_messages'],
            'data_collection_progress': {
                'email': bool(state['collected_data'].get('email')),
                'service_interest': bool(state['collected_data'].get('service_interest')),
                'budget_confirmed': state['collected_data'].get('budget_confirmed', False),
                'meeting_confirmed': state['collected_data'].get('meeting_confirmed', False)
            },
            'conversation_stage': self._determine_conversation_stage(state['collected_data'])
        }
    
    def _determine_conversation_stage(self, data: Dict[str, Any]) -> str:
        """Determine what stage of the conversation we're in"""
        if data.get('meeting_confirmed'):
            return "meeting_scheduled"
        elif data.get('calendar_options_shown'):
            return "calendar_selection"
        elif data.get('budget_confirmed'):
            return "budget_confirmed"
        elif data.get('service_interest'):
            return "service_identified"
        elif data.get('email'):
            return "contact_collection"
        else:
            return "initial_contact"
    
    def __repr__(self):
        return f"TestAgentWrapper(session={self.test_session_id}, messages={len(self.storage.messages)})"