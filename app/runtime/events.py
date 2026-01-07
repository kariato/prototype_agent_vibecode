"""
app/runtime/events.py

Defines the structure for system events within the IDE.
Events are used to update the visual timeline and trigger frontend updates.
"""

from pydantic import BaseModel, Field
from datetime import datetime
from enum import Enum
from typing import Dict, Any, Optional

class EventImpact(str, Enum):
    INFO = "info"       # System messages, UI navigation
    MUTATION = "mutation" # File writes, state changes
    ERROR = "error"     # Process failures
    SYSTEM = "system"   # Initialization, recovery

class IDEEvent(BaseModel):
    """
    A single event in the IDE's lifecycle.
    """
    timestamp: float = Field(default_factory=lambda: datetime.now().timestamp())
    type: str
    impact: EventImpact = EventImpact.INFO
    session_id: str
    node_name: Optional[str] = None
    payload: Dict[str, Any] = Field(default_factory=dict)

def create_event(event_type: str, session_id: str, impact: EventImpact = EventImpact.INFO, node_name: str = None, payload: dict = None) -> dict:
    event = IDEEvent(
        type=event_type,
        session_id=session_id,
        impact=impact,
        node_name=node_name,
        payload=payload or {}
    )
    return event.model_dump()
