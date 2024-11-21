from collections import deque
from typing import Union, List
from langchain_core.messages import HumanMessage, AIMessage, trim_messages

from ..schema import MemoryEvent

class MemoryManager:
    """Manages a character's memory of recent conversations and interactions."""
    
    def __init__(self, max_memories: int = 10) -> None:
        """Initialize the MemoryManager.
        
        Args:
            max_memories: Maximum number of memories to store. Defaults to 10.
        """
        self.memories: deque[MemoryEvent] = deque(maxlen=max_memories)
        self.message_history: List[Union[HumanMessage, AIMessage]] = []
    
    def add_memory(self, event: MemoryEvent) -> None:
        """Add a new memory event to the memory store."""
        self.memories.append(event)
        self.message_history.extend([
            HumanMessage(content=event.message),
            AIMessage(content=event.response)
        ])
        # Keep message history in sync with deque size
        self.message_history = trim_messages(
            self.message_history,
            max_tokens=self.memories.maxlen * 2,  # *2 because each exchange has 2 messages
            token_counter=len,  # Simple message counting
            strategy="last",
            start_on="human"
        )
    
    def get_recent_memories(self, count: int = 3, as_messages: bool = False) -> Union[str, dict]:
        """Get a representation of the most recent memories.
        
        Args:
            count: Number of recent memories to retrieve. Defaults to 3.
            as_messages: Whether to return as langchain messages. Defaults to False.
            
        Returns:
            Either a string of formatted memories or dict with message history.
        """
        if as_messages:
            return {"chat_history": self.message_history[-count*2:]}  # *2 for message pairs
            
        recent = list(self.memories)[-count:]
        return "\n".join(str(memory) for memory in recent)