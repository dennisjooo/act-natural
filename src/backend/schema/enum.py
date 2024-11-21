from enum import Enum

class SpeakerType(Enum):
    """Types of speakers in the conversation system."""
    USER = "user"
    CHARACTER = "character" 
    ALL = "all"
    
class EventType(Enum):
    """Types of narrative events that can occur."""
    SCENE = 'scene'
    OBSERVATION = 'observation'