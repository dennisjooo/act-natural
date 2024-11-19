import os
from dataclasses import dataclass
from langchain_groq import ChatGroq
from typing import Dict, Optional, Any
from queue import Empty

from .memory import MemoryManager, MemoryEvent
from .prompts import CHARACTER_RESPONSE_PROMPT

@dataclass
class CharacterConfig:
    """Configuration for a character in the interactive play.
    
    Attributes:
        name: The character's name
        gender: The character's gender identity
        personality: Dictionary mapping personality traits to their strength values
        background: The character's backstory and history
        hidden_motive: The character's secret motivation
    """
    name: str
    gender: str
    personality: Dict[str, float]
    background: str
    hidden_motive: str

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
        self.emoji = self._get_trait_emoji()
    
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
    
    def _initialize_llm(self) -> ChatGroq:
        """Initialize the language model for generating responses."""
        return ChatGroq(
            api_key=os.getenv("GROQ_API_KEY"),
            model_name="llama-3.1-8b-instant"
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
    
    def _get_trait_emoji(self) -> str:
        """Get emoji based on dominant personality trait and gender.
        
        Returns:
            An emoji character representing the character
        """
        gender = self.config.gender.lower()
        
        # Create a mapping of common traits to emojis with gender variants
        trait_emoji_map = {
            "intelligence": {"male": "👨‍🎓", "female": "👩‍🎓", "non-binary": "🧑‍🎓"},
            "wisdom": {"male": "👨‍🏫", "female": "👩‍🏫", "non-binary": "🧑‍🏫"},
            "scholarly": {"male": "👨‍🎓", "female": "👩‍🎓", "non-binary": "🧑‍🎓"},
            "authority": {"male": "👨‍💼", "female": "👩‍💼", "non-binary": "🧑‍💼"},
            "leadership": {"male": "👨‍💼", "female": "👩‍💼", "non-binary": "🧑‍💼"},
            "commanding": {"male": "👨‍✈️", "female": "👩‍✈️", "non-binary": "🧑‍✈️"},
            "scientific": {"male": "👨‍🔬", "female": "👩‍🔬", "non-binary": "🧑‍🔬"},
            "medical": {"male": "👨‍⚕️", "female": "👩‍⚕️", "non-binary": "🧑‍⚕️"},
            "analytical": {"male": "🧔", "female": "👩", "non-binary": "🧑"},
            "military": {"male": "👨‍✈️", "female": "👩‍✈️", "non-binary": "🧑‍✈️"},
            "security": {"male": "👮‍♂️", "female": "👮‍♀️", "non-binary": "👮"},
            "tactical": {"male": "🧔", "female": "👩", "non-binary": "🧑"},
            "empathy": {"male": "👨‍⚕️", "female": "👩‍⚕️", "non-binary": "🧑‍⚕️"},
            "social": {"male": "🧔", "female": "👩", "non-binary": "🧑"},
            "friendly": {"male": "😊", "female": "😊", "non-binary": "😊"},
            "mysterious": {"male": "🕵️‍♂️", "female": "🕵️‍♀️", "non-binary": "🕵️"},
            "secretive": {"male": "🕵️‍♂️", "female": "🕵️‍♀️", "non-binary": "🕵️"},
            "deceptive": {"male": "🕵️‍♂️", "female": "🕵️‍♀️", "non-binary": "🕵️"},
            "adventurous": {"male": "🧗‍♂️", "female": "🧗‍♀️", "non-binary": "🧗"},
            "brave": {"male": "💂‍♂️", "female": "💂‍♀️", "non-binary": "💂"},
            "explorer": {"male": "👨‍🦱", "female": "👩‍🦱", "non-binary": "🧑"},
            "technical": {"male": "👨‍💻", "female": "👩‍💻", "non-binary": "🧑‍💻"},
            "engineering": {"male": "👨‍🔧", "female": "👩‍🔧", "non-binary": "🧑‍🔧"},
            "mechanical": {"male": "👨‍🔧", "female": "👩‍🔧", "non-binary": "🧑‍🔧"}
        }
        
        if self.personality:
            dominant_trait = max(self.personality.items(), key=lambda x: x[1])[0].lower()
            for trait_key, emoji_dict in trait_emoji_map.items():
                if trait_key in dominant_trait:
                    return emoji_dict.get(gender, emoji_dict["non-binary"])
        
        # Generic avatars based on gender
        generic_avatars = {
            "male": ["👨", "👨‍🦰", "👨‍🦱", "👨‍🦳", "🧔"],
            "female": ["👩", "👩‍🦰", "👩‍🦱", "👩‍🦳", "👱‍♀️"],
            "non-binary": ["🧑", "🧑‍🦰", "🧑‍🦱", "🧑‍🦳", "🧑‍🦲"]
        }
        return generic_avatars.get(gender, generic_avatars["non-binary"])[hash(self.name) % 5]
    
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