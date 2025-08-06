"""
Test Storage Module
Provides temporary memory storage for testing the chatbot without affecting Chatwoot
"""

from datetime import datetime
from typing import List, Dict, Any, Optional
import json


class TestStorage:
    """
    Simple in-memory storage for testing purposes.
    Replaces Chatwoot storage during testing.
    """
    
    def __init__(self):
        self.messages: List[Dict[str, Any]] = []
        self.conversation_data: Dict[str, Any] = {}
        self.user_data: Dict[str, Any] = {}
        self.session_start: datetime = datetime.now()
        
    def save_message(self, message: str, sender: str = "bot", metadata: Optional[Dict] = None):
        """Save a message to the test conversation"""
        message_data = {
            'id': len(self.messages) + 1,
            'content': message,
            'sender': sender,
            'timestamp': datetime.now().isoformat(),
            'metadata': metadata or {}
        }
        self.messages.append(message_data)
        
    def save_user_message(self, message: str, metadata: Optional[Dict] = None):
        """Save a user message"""
        self.save_message(message, sender="user", metadata=metadata)
        
    def save_bot_message(self, message: str, metadata: Optional[Dict] = None):
        """Save a bot response"""
        self.save_message(message, sender="bot", metadata=metadata)
        
    def save_conversation_data(self, data: Dict[str, Any]):
        """Save conversation state data"""
        self.conversation_data.update(data)
        
    def save_user_data(self, data: Dict[str, Any]):
        """Save extracted user data"""
        self.user_data.update(data)
        
    def get_conversation(self) -> List[Dict[str, Any]]:
        """Get all messages in the conversation"""
        return self.messages.copy()
        
    def get_conversation_data(self) -> Dict[str, Any]:
        """Get conversation state data"""
        return self.conversation_data.copy()
        
    def get_user_data(self) -> Dict[str, Any]:
        """Get extracted user data"""
        return self.user_data.copy()
        
    def get_last_message(self) -> Optional[Dict[str, Any]]:
        """Get the last message"""
        return self.messages[-1] if self.messages else None
        
    def get_messages_by_sender(self, sender: str) -> List[Dict[str, Any]]:
        """Get all messages from a specific sender"""
        return [msg for msg in self.messages if msg['sender'] == sender]
        
    def clear(self):
        """Clear all stored data for a fresh test"""
        self.messages.clear()
        self.conversation_data.clear()
        self.user_data.clear()
        self.session_start = datetime.now()
        
    def export_conversation(self) -> Dict[str, Any]:
        """Export entire conversation for analysis"""
        return {
            'session_start': self.session_start.isoformat(),
            'session_duration': str(datetime.now() - self.session_start),
            'message_count': len(self.messages),
            'messages': self.messages,
            'conversation_data': self.conversation_data,
            'user_data': self.user_data
        }
        
    def get_stats(self) -> Dict[str, Any]:
        """Get conversation statistics"""
        user_messages = len(self.get_messages_by_sender("user"))
        bot_messages = len(self.get_messages_by_sender("bot"))
        
        return {
            'total_messages': len(self.messages),
            'user_messages': user_messages,
            'bot_messages': bot_messages,
            'session_duration': str(datetime.now() - self.session_start),
            'data_collected': len(self.user_data),
            'conversation_state': len(self.conversation_data)
        }
        
    def __repr__(self):
        return f"TestStorage(messages={len(self.messages)}, user_data={len(self.user_data)})"