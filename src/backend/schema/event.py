import time
from dataclasses import dataclass
from typing import Optional

from .enum import EventType

@dataclass
class SceneEvent:
    """Represents a narrative event in the scene history.
    
    Attributes:
        description: The narrative description of the event
        type: The type of event (scene or observation)
    """
    description: str
    type: EventType

@dataclass
class ConversationEvent:
    """Represents a single conversation interaction between characters.
    
    Attributes:
        speaker (str): The name of the character speaking
        target (str): The name of the character being spoken to 
        message (str): The content of the message
        timestamp (float): Unix timestamp of when the message was sent
    """
    speaker: str
    target: str 
    message: str
    timestamp: float = time.time()
    
@dataclass
class MemoryEvent:
    """Represents a single memory event containing a conversation interaction."""
    speaker: str
    message: str 
    response: str
    hidden_thought: Optional[str]
    
    def __str__(self) -> str:
        """String representation of the memory event."""
        return f"{self.speaker}: {self.message} -> {self.response}"