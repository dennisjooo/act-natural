import random
from typing import Generator, Dict
from agents.character import Character
from agents.narrator import Narrator

class ResponseProcessor:
    """Processes and formats character responses and generates narration.
    
    Handles formatting of character dialogue, adding appropriate punctuation,
    and occasionally generates narrative observations of interactions.
    
    Attributes:
        characters: Dictionary mapping character names to Character objects
        narrator: Narrator instance for generating scene descriptions
    """
    
    def __init__(self, characters: Dict[str, Character], narrator: Narrator) -> None:
        """Initialize the ResponseProcessor.
        
        Args:
            characters: Dictionary mapping character names to Character objects
            narrator: Narrator instance for generating scene descriptions
        """
        self.characters = characters
        self.narrator = narrator
        
    def process_response(self, speaker: str, target: str, response: str) -> Generator[str, None, None]:
        """Process a character's response and generate related content.
        
        Formats the response text and occasionally adds narrative observations.
        
        Args:
            speaker: Name of the character speaking
            target: Name of the character being spoken to
            response: The raw response text to process
            
        Yields:
            str: Formatted response text and optional narration with pause indicators
        """
        response = self._format_response(response)
        yield response
        yield "PAUSE:1"
        
        if random.random() < 0.15:
            narration = self._generate_narration(speaker, target, response)
            if narration:
                yield narration
                yield "PAUSE:0.5"
    
    def _format_response(self, response: str) -> str:
        """Format the response text with proper spacing and punctuation.
        
        Args:
            response: Raw response text to format
            
        Returns:
            str: Formatted response text with proper spacing and punctuation
        """
        response = response.replace('\n', ' ').strip()
        if not response.endswith(('.', '!', '?', '"')):
            response += '.'
        return response
    
    def _generate_narration(self, speaker: str, target: str, response: str) -> str:
        """Generate narrative observation of an interaction between characters.
        
        Args:
            speaker: Name of the character speaking
            target: Name of the character being spoken to
            response: The processed response text
            
        Returns:
            str: Formatted narration text, or empty string if no narration generated
        """
        narration = self.narrator.observe_interaction(speaker, target, response)
        if narration:
            narration = self._format_response(narration)
        return narration 