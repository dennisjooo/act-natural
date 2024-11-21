from dataclasses import dataclass
from typing import List

@dataclass
class PlayConfig:
    """Configuration class for interactive play settings and defaults.
    
    Attributes:
        default_num_characters: Default number of characters to include in a scene
        default_user_name: Default name for users who don't provide one
        default_user_description: Default description for users who don't provide one
        fallback_scenarios: List of pre-written scenario descriptions used when 
            custom scenarios are not provided
        max_memories: Maximum number of memories to keep
    """
    default_num_characters: int = 4
    default_user_name: str = "Anonymous Player"
    default_user_description: str = "A curious participant in this interactive story"
    max_memories: int = 10
    
    fallback_scenarios: List[str] = (
        "A mysterious tavern on a stormy night. Travelers from different walks of life have sought shelter here, each carrying their own secrets and stories. The atmosphere is tense with unspoken tales and hidden agendas.",
        "An abandoned mansion during a masquerade ball. The guests are trapped inside by a mysterious force, and everyone seems to have a hidden agenda. The air is thick with intrigue and suspicion.",
        "A futuristic space station at the edge of known space. The station's systems are malfunctioning, and the diverse crew members each seem to know more than they're letting on. The metallic corridors echo with whispered conspiracies."
    )