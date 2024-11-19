import os
from dataclasses import dataclass
from enum import Enum
from langchain_groq import ChatGroq
from typing import List, Optional

from .prompts import NARRATOR_OBSERVATION_PROMPT

class EventType(Enum):
    """Types of narrative events that can occur."""
    SCENE = 'scene'
    OBSERVATION = 'observation'

@dataclass
class SceneEvent:
    """Represents a narrative event in the scene history.
    
    Attributes:
        description: The narrative description of the event
        type: The type of event (scene or observation)
    """
    description: str
    type: EventType

class Narrator:
    """Manages scene narration and observes character interactions.
    
    Maintains scene history and provides atmospheric narration when appropriate.
    """
    
    def __init__(self) -> None:
        """Initialize the Narrator."""
        self.scene_history: List[SceneEvent] = []
        self.current_scene: Optional[str] = None
        self.llm = self._initialize_llm()
        self.chain = NARRATOR_OBSERVATION_PROMPT | self.llm
    
    def _initialize_llm(self) -> ChatGroq:
        """Initialize the language model.
        
        Returns:
            ChatGroq: Configured language model instance
        """
        return ChatGroq(
            api_key=os.getenv("GROQ_API_KEY"),
            model_name="gemma2-9b-it"
        )

    def _format_narrator_message(self, message: str) -> str:
        """Format a message with narrator prefix.
        
        Args:
            message: The message to format
            
        Returns:
            str: The formatted narrator message
        """
        return f"[Narrator]: {message}"
    
    def _add_to_history(self, description: str, event_type: EventType) -> None:
        """Add an event to scene history.
        
        Args:
            description: The narrative description
            event_type: The type of event
        """
        self.scene_history.append(SceneEvent(description, event_type))
    
    def set_scene(self, scene_description: str) -> str:
        """Set the current scene and add it to history.
        
        Args:
            scene_description: Description of the scene to set
            
        Returns:
            str: Formatted narrator message with scene description
        """
        self.current_scene = scene_description
        self._add_to_history(scene_description, EventType.SCENE)
        return self._format_narrator_message(scene_description)
    
    def observe_interaction(self, speaker: str, listener: str, message: str) -> str:
        """Observe an interaction and provide narration if needed.
        
        Args:
            speaker: Name of the speaking character
            listener: Name of the listening character
            message: The spoken message
            
        Returns:
            str: Narration of the interaction if needed, empty string otherwise
        """
        if not self.current_scene:
            return ""
            
        try:
            observation = self.chain.invoke({
                "speaker": speaker,
                "listener": listener,
                "message": message,
                "current_scene": self.current_scene
            }).content.strip()
            
            if observation.upper() == "SKIP":
                return ""
            
            self._add_to_history(observation, EventType.OBSERVATION)
            return self._format_narrator_message(observation)
            
        except Exception as e:
            print(f"Error in narrator observation: {e}")
            return ""