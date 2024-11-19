from collections import deque
from dataclasses import dataclass
from typing import Optional

@dataclass
class MemoryEvent:
    """Represents a single memory event containing a conversation interaction.
    
    Attributes:
        speaker: The name of the character speaking
        message: The message that was spoken
        response: The response given to the message
        hidden_thought: Optional internal thought of the character
    """
    speaker: str
    message: str 
    response: str
    hidden_thought: Optional[str]

class MemoryManager:
    """Manages a character's memory of recent conversations and interactions.
    
    Maintains a fixed-size deque of MemoryEvent objects representing the most
    recent memories.
    """
    
    def __init__(self, max_memories: int = 10) -> None:
        """Initialize the MemoryManager.
        
        Args:
            max_memories: Maximum number of memories to store. Defaults to 10.
        """
        self.memories: deque[MemoryEvent] = deque(maxlen=max_memories)
    
    def add_memory(self, event: MemoryEvent) -> None:
        """Add a new memory event to the memory store.
        
        Args:
            event: The MemoryEvent to add
        """
        self.memories.append(event)
    
    def get_recent_memories(self, count: int = 3) -> str:
        """Get a string representation of the most recent memories.
        
        Args:
            count: Number of recent memories to retrieve. Defaults to 3.
            
        Returns:
            A string containing the formatted recent memories, one per line.
        """
        recent = list(self.memories)[-count:]
        return "\n".join(str(memory) for memory in recent)