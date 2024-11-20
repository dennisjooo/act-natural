from dataclasses import dataclass
from typing import Dict

@dataclass
class CharacterConfig:
    """Configuration class for character attributes.
    
    Attributes:
        name: Character's name
        gender: Character's gender
        description: Character's physical description
        personality: Dictionary of personality traits and values
        background: Character's background story
        hidden_motive: Character's secret motivation
        emoji: Emoji representation of the character
        role_in_scene: Character's role in the scenario
        relation_to_user: Character's relation to the user
    """
    name: str
    gender: str
    description: str
    personality: Dict[str, float]
    background: str
    hidden_motive: str
    emoji: str = "👤"  # Default emoji if none is provided 
    role_in_scene: str = ""
    relation_to_user: str = ""