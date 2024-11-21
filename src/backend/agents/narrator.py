import logging
import os
from langchain_groq import ChatGroq
from typing import List, Optional

from .prompts import NARRATOR_OBSERVATION_PROMPT
from ..schema import SceneEvent, EventType


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
            model_name=os.getenv("ORCHESTRATOR_MODEL")
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
            logging.error(f"Error in narrator observation: {e}")
            return ""
    
    def get_observation(self) -> str:
        """Generate an observation based on the last interaction in the scene history.
        
        Returns:
            str: Observation string or empty if no observation is needed
        """
        if not self.scene_history:
            return ""
        
        # Get the last interaction event
        last_event = self.scene_history[-1]
        
        # Check if the last event was an observation
        if last_event.type == EventType.OBSERVATION:
            return ""
        
        # Attempt to split the description into speaker, listener, and message
        try:
            speaker, listener, message = last_event.description.split(" to ", 2)
        except ValueError:
            logging.error(f"Unexpected format in scene event description: {last_event.description}")
            return ""
        
        return self.observe_interaction(speaker, listener, message)