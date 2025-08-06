"""
Test Router Module
FastAPI router for testing the WhatsApp agent without affecting Chatwoot
"""

import logging
from datetime import datetime
from typing import Dict, Any, Optional

from fastapi import APIRouter, HTTPException, Request
from fastapi.responses import JSONResponse
from pydantic import BaseModel

from .test_integration import TestAgentWrapper

logger = logging.getLogger("test-router")

# Initialize test router
test_router = APIRouter(prefix="/api/test", tags=["Testing"])

# Global test agent wrapper instance
test_agent: Optional[TestAgentWrapper] = None


# Pydantic models for request/response
class ChatMessage(BaseModel):
    message: str
    metadata: Optional[Dict[str, Any]] = None


class ChatResponse(BaseModel):
    success: bool
    response: Optional[str] = None
    error: Optional[str] = None
    session_id: str
    timestamp: str


class ResetResponse(BaseModel):
    success: bool
    message: str
    new_session_id: str
    timestamp: str


class ConversationHistoryResponse(BaseModel):
    success: bool
    session_id: str
    conversation: list
    agent_state: Dict[str, Any]
    stats: Dict[str, Any]


class StatusResponse(BaseModel):
    success: bool
    status: str
    session_id: Optional[str] = None
    agent_initialized: bool
    uptime: str
    test_summary: Optional[Dict[str, Any]] = None


# Initialize agent on startup
def initialize_test_agent():
    """Initialize the test agent wrapper"""
    global test_agent
    try:
        test_agent = TestAgentWrapper(
            contact_name="TestUser",
            company_name="Test Company"
        )
        logger.info("✅ Test agent initialized successfully")
    except Exception as e:
        logger.error(f"❌ Error initializing test agent: {e}")
        test_agent = None


# Initialize agent when module loads
initialize_test_agent()


@test_router.post("/chat", response_model=ChatResponse)
async def send_message(chat_message: ChatMessage):
    """
    Send a message to the test agent and get response
    """
    global test_agent
    
    try:
        # Ensure agent is initialized
        if not test_agent:
            initialize_test_agent()
            if not test_agent:
                raise HTTPException(status_code=500, detail="Test agent not initialized")
        
        logger.info(f"📨 Incoming test message: {chat_message.message[:50]}...")
        
        # Process message with the agent
        response = await test_agent.send_message(chat_message.message)
        
        if response:
            return ChatResponse(
                success=True,
                response=response,
                session_id=test_agent.test_session_id,
                timestamp=datetime.now().isoformat()
            )
        else:
            return ChatResponse(
                success=False,
                error="No response generated",
                session_id=test_agent.test_session_id,
                timestamp=datetime.now().isoformat()
            )
    
    except Exception as e:
        logger.error(f"❌ Error processing chat message: {e}")
        return ChatResponse(
            success=False,
            error=str(e),
            session_id=test_agent.test_session_id if test_agent else "unknown",
            timestamp=datetime.now().isoformat()
        )


@test_router.post("/reset", response_model=ResetResponse)
async def reset_conversation():
    """
    Reset the conversation for a fresh test
    """
    global test_agent
    
    try:
        # Ensure agent is initialized
        if not test_agent:
            initialize_test_agent()
            if not test_agent:
                raise HTTPException(status_code=500, detail="Test agent not initialized")
        
        old_session = test_agent.test_session_id
        test_agent.reset_conversation()
        new_session = test_agent.test_session_id
        
        logger.info(f"🔄 Conversation reset: {old_session} → {new_session}")
        
        return ResetResponse(
            success=True,
            message=f"Conversation reset successfully. New session: {new_session}",
            new_session_id=new_session,
            timestamp=datetime.now().isoformat()
        )
    
    except Exception as e:
        logger.error(f"❌ Error resetting conversation: {e}")
        return ResetResponse(
            success=False,
            message=f"Error resetting conversation: {str(e)}",
            new_session_id="unknown",
            timestamp=datetime.now().isoformat()
        )


@test_router.get("/conversation", response_model=ConversationHistoryResponse)
async def get_conversation_history():
    """
    Get the complete conversation history and agent state
    """
    global test_agent
    
    try:
        if not test_agent:
            raise HTTPException(status_code=404, detail="No active test session")
        
        history = test_agent.get_conversation_history()
        
        return ConversationHistoryResponse(
            success=True,
            session_id=history['session_id'],
            conversation=history['conversation'],
            agent_state=history['agent_state'],
            stats=history['stats']
        )
    
    except Exception as e:
        logger.error(f"❌ Error getting conversation history: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@test_router.get("/status", response_model=StatusResponse)
async def get_test_status():
    """
    Get the current status of the test environment
    """
    global test_agent
    
    try:
        is_initialized = test_agent is not None
        
        if is_initialized:
            summary = test_agent.get_test_summary()
            session_id = test_agent.test_session_id
            uptime = summary['duration']
        else:
            summary = None
            session_id = None
            uptime = "Not running"
        
        return StatusResponse(
            success=True,
            status="running" if is_initialized else "not_initialized",
            session_id=session_id,
            agent_initialized=is_initialized,
            uptime=uptime,
            test_summary=summary
        )
    
    except Exception as e:
        logger.error(f"❌ Error getting test status: {e}")
        return StatusResponse(
            success=False,
            status="error",
            agent_initialized=False,
            uptime="Error"
        )


@test_router.get("/debug/agent-state")
async def get_agent_debug_state():
    """
    Get detailed agent state for debugging purposes
    """
    global test_agent
    
    try:
        if not test_agent:
            raise HTTPException(status_code=404, detail="No active test session")
        
        state = test_agent.get_agent_state()
        
        return JSONResponse({
            "success": True,
            "session_id": test_agent.test_session_id,
            "agent_state": state,
            "storage_stats": test_agent.storage.get_stats(),
            "timestamp": datetime.now().isoformat()
        })
    
    except Exception as e:
        logger.error(f"❌ Error getting agent debug state: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@test_router.get("/debug/export")
async def export_conversation():
    """
    Export the complete conversation for analysis
    """
    global test_agent
    
    try:
        if not test_agent:
            raise HTTPException(status_code=404, detail="No active test session")
        
        export_data = test_agent.storage.export_conversation()
        export_data['agent_final_state'] = test_agent.get_agent_state()
        
        return JSONResponse(export_data)
    
    except Exception as e:
        logger.error(f"❌ Error exporting conversation: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@test_router.post("/init")
async def initialize_new_session():
    """
    Manually initialize a new test session
    """
    global test_agent
    
    try:
        initialize_test_agent()
        
        if test_agent:
            return JSONResponse({
                "success": True,
                "message": "Test agent initialized successfully",
                "session_id": test_agent.test_session_id,
                "timestamp": datetime.now().isoformat()
            })
        else:
            raise HTTPException(status_code=500, detail="Failed to initialize test agent")
    
    except Exception as e:
        logger.error(f"❌ Error initializing new session: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# Health check endpoint
@test_router.get("/health")
async def health_check():
    """
    Health check for the test router
    """
    return JSONResponse({
        "status": "healthy",
        "service": "TDX Chatbot Test API",
        "timestamp": datetime.now().isoformat(),
        "agent_ready": test_agent is not None
    })