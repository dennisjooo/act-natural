from dataclasses import dataclass
from typing import Dict

@dataclass
class CharacterConfig:
    """Configuration class for character attributes.
    
    Attributes:
        name: Character's name
        gender: Character's gender
        personality: Dictionary of personality traits and values
        background: Character's background story
        hidden_motive: Character's secret motivation
        emoji: Emoji representation of the character
    """
    name: str
    gender: str
    personality: Dict[str, float]
    background: str
    hidden_motive: str
    emoji: str = "👤"  # Default emoji if none is provided 