import os
from langchain_groq import ChatGroq
from typing import Dict, Optional, Any
from queue import Empty

from agents.memory import MemoryManager, MemoryEvent
from agents.prompts import CHARACTER_RESPONSE_PROMPT
from config.character_config import CharacterConfig

class Character:
    """A character in the interactive play that can engage in conversation.
    
    The character maintains memory of interactions, generates responses based on 
    personality and context, and has an emoji avatar representation.
    
    Attributes:
        config (CharacterConfig): Configuration object containing character attributes
        memory (MemoryManager): Manager for character's memory and interaction history
        thoughts_queue (Optional[Queue]): Queue for pre-generated character thoughts
        llm (ChatGroq): Language model for generating responses
        chain (Chain): Prompt chain for character responses
        user_name (str): Name of the user interacting with the character
        user_description (str): Description of the user
    """
    
    def __init__(self, config: CharacterConfig) -> None:
        """Initialize a new character.
        
        Args:
            config (CharacterConfig): Configuration object containing character attributes
                including name, personality traits, background story, and hidden motives
        """
        self.config = config
        self.memory = MemoryManager()
        self.thoughts_queue = None
        self.llm = self._initialize_llm()
        self.chain = CHARACTER_RESPONSE_PROMPT | self.llm
    
    @property
    def name(self) -> str:
        """Get the character's name.
        
        Returns:
            str: The character's configured name
        """
        return self.config.name
    
    @property
    def personality(self) -> Dict[str, float]:
        """Get the character's personality traits and values.
        
        Returns:
            Dict[str, float]: Dictionary mapping personality traits to their values
        """
        return self.config.personality
    
    @property
    def background(self) -> str:
        """Get the character's background story.
        
        Returns:
            str: The character's configured background story
        """
        return self.config.background
    
    @property
    def hidden_motive(self) -> str:
        """Get the character's hidden motivation.
        
        Returns:
            str: The character's configured hidden motive
        """
        return self.config.hidden_motive
    
    @property
    def emoji(self) -> str:
        """Get the character's emoji representation.
        
        Returns:
            str: The character's configured emoji or default avatar
        """
        if self.config.emoji:
            return self.config.emoji
        else:
            return "👤"
    
    def _initialize_llm(self) -> ChatGroq:
        """Initialize the language model for generating responses.
        
        Returns:
            ChatGroq: Configured language model instance
        """
        return ChatGroq(
            api_key=os.getenv("GROQ_API_KEY"),
            model_name="llama-3.1-8b-instant"
        )
    
    def _format_personality(self) -> str:
        """Format personality traits into a readable string.
        
        Returns:
            str: A comma-separated string of traits and their values
        """
        return ", ".join(
            f"{k} ({v:.1f})" for k, v in self.personality.items()
        )
    
    def set_orchestrator(self, orchestrator: Any) -> None:
        """Set reference to orchestrator for accessing shared resources.
        
        Args:
            orchestrator (Any): The orchestrator object managing the conversation
        """
        self.thoughts_queue = orchestrator.thoughts_queue
    
    def get_current_thought(self) -> Optional[str]:
        """Get a pre-generated thought if available.
        
        Returns:
            Optional[str]: The current thought if available for this character, None otherwise
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
            response (Any): Raw response from the language model
            
        Returns:
            str: Cleaned response text as string
        """
        if hasattr(response, 'content'):
            return response.content.strip()
        if isinstance(response, dict):
            return response.get('text', str(response)).strip()
        return str(response).strip()
    
    def respond_to(self, message: str, speaker: str, context: Dict[str, str]) -> str:
        """Generate a response to a message.
        
        Args:
            message (str): The message to respond to
            speaker (str): The name of who sent the message
            context (Dict[str, str]): Additional context like scene description
            
        Returns:
            str: Formatted response with character name prefix
            
        Raises:
            Exception: If response generation fails
        """
        hidden_thought = self.get_current_thought()
        
        try:
            # Add debug print
            if message == "prompt_user":
                print(f"Character {self.name} generating user prompt...")
            
            response = self.chain.invoke({
                "name": self.name,
                "personality": self._format_personality(),
                "background": self.background,
                "hidden_motive": self.hidden_motive,
                "context": context.get("scene", ""),
                "speaker": speaker,
                "message": "What are your thoughts on this?" if message == "prompt_user" else message,
                "memory": self.memory.get_recent_memories(),
                "current_thought": (
                    "I should engage the user in conversation" 
                    if message == "prompt_user" 
                    else (hidden_thought or "Just focusing on the current situation.")
                ),
                "user_name": getattr(self, 'user_name', 'User')
            })
            
            response_text = self._extract_response_text(response)
            
            # For user prompts, ensure it ends with a question
            if message == "prompt_user" and not any(response_text.rstrip().endswith(x) for x in ["?", "..."]):
                response_text = f"{response_text.rstrip()}"
            
            self.memory.add_memory(MemoryEvent(
                speaker=speaker,
                message=message,
                response=response_text,
                hidden_thought=hidden_thought
            ))
            
            return f"[{self.name}]: {response_text}"
            
        except Exception as e:
            print(f"Error generating character response: {e}")
            if message == "prompt_user":
                return f"[{self.name}]: What are your thoughts on this situation?"
            return f"[{self.name}]: *looks uncertain*"
    
    def set_user_info(self, user_name: str, user_description: str) -> None:
        """Set information about the user for better interaction.
        
        Args:
            user_name (str): Name of the user
            user_description (str): Brief description of the user
        """
        self.user_name = user_name
        self.user_description = user_description