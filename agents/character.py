import os
from langchain_groq import ChatGroq
from typing import Dict, Optional, Any
from queue import Empty

from .memory import MemoryManager, MemoryEvent
from .prompts import CHARACTER_RESPONSE_PROMPT
from .config import CharacterConfig

class Character:
    """A character in the interactive play that can engage in conversation.
    
    The character maintains memory of interactions, generates responses based on 
    personality and context, and has an emoji avatar representation.
    """
    
    def __init__(self, config: CharacterConfig) -> None:
        """Initialize a new character.
        
        Args:
            config: Configuration object containing character attributes
        """
        self.config = config
        self.memory = MemoryManager()
        self.thoughts_queue = None
        self.llm = self._initialize_llm()
        self.chain = CHARACTER_RESPONSE_PROMPT | self.llm
    
    @property
    def name(self) -> str:
        """Get the character's name."""
        return self.config.name
    
    @property
    def personality(self) -> Dict[str, float]:
        """Get the character's personality traits and values."""
        return self.config.personality
    
    @property
    def background(self) -> str:
        """Get the character's background story."""
        return self.config.background
    
    @property
    def hidden_motive(self) -> str:
        """Get the character's hidden motivation."""
        return self.config.hidden_motive
    
    @property
    def emoji(self) -> str:
        """Get the character's emoji representation."""
        if self.config.emoji:
            return self.config.emoji
        else:
            return "👤"
    
    def _initialize_llm(self) -> ChatGroq:
        """Initialize the language model for generating responses."""
        return ChatGroq(
            api_key=os.getenv("GROQ_API_KEY"),
            model_name="llama-3.1-8b-instant",
            temperature=0.25
        )
    
    def _format_personality(self) -> str:
        """Format personality traits into a readable string.
        
        Returns:
            A comma-separated string of traits and their values
        """
        return ", ".join(
            f"{k} ({v:.1f})" for k, v in self.personality.items()
        )
    
    def set_orchestrator(self, orchestrator: Any) -> None:
        """Set reference to orchestrator for accessing shared resources.
        
        Args:
            orchestrator: The orchestrator object managing the conversation
        """
        self.thoughts_queue = orchestrator.thoughts_queue
    
    def get_current_thought(self) -> Optional[str]:
        """Get a pre-generated thought if available.
        
        Returns:
            The current thought if available, None otherwise
        """
        if not self.thoughts_queue:
            return None
            
        try:
            char_name, thought = self.thoughts_queue.get_nowait()
            if char_name == self.name:
                return thought
            self.thoughts_queue.put((char_name, thought))
            return None
        except Empty:
            return None
    
    def _extract_response_text(self, response: Any) -> str:
        """Extract clean text from LLM response.
        
        Args:
            response: Raw response from the language model
            
        Returns:
            Cleaned response text as string
        """
        if hasattr(response, 'content'):
            return response.content.strip()
        if isinstance(response, dict):
            return response.get('text', str(response)).strip()
        return str(response).strip()
    
    def respond_to(self, message: str, speaker: str, context: Dict[str, str]) -> str:
        """Generate a response to a message.
        
        Args:
            message: The message to respond to
            speaker: The name of who sent the message
            context: Dictionary containing contextual information
            
        Returns:
            The character's response formatted with their name
        """
        hidden_thought = self.get_current_thought()
        
        try:
            response = self.chain.invoke({
                "name": self.name,
                "personality": self._format_personality(),
                "background": self.background,
                "hidden_motive": self.hidden_motive,
                "context": context.get("scene", ""),
                "speaker": speaker,
                "message": message,
                "memory": self.memory.get_recent_memories(),
                "current_thought": hidden_thought or "Just focusing on the current situation."
            })
            
            response_text = self._extract_response_text(response)
            
            self.memory.add_memory(MemoryEvent(
                speaker=speaker,
                message=message,
                response=response_text,
                hidden_thought=hidden_thought
            ))
            
            return f"[{self.name}]: {response_text}"
            
        except Exception as e:
            print(f"Error generating character response: {e}")
            return f"[{self.name}]: *looks uncertain*"
    
    def set_user_info(self, user_name: str, user_description: str) -> None:
        """Set information about the user for better interaction.
        
        Args:
            user_name: Name of the user
            user_description: Brief description of the user
        """
        self.user_name = user_name
        self.user_description = user_description