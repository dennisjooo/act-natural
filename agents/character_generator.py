import logging
from typing import Dict, Optional
from langchain_groq import ChatGroq

from agents.character import Character
from agents.prompts import CHARACTER_GENERATION_PROMPT
from config.character_config import CharacterConfig
from utils import clean_json_response

class CharacterGenerator:
    """Generates character sets for interactive scenarios.
    
    This class handles the generation of character sets using an LLM, creating
    detailed characters with personalities, backgrounds and motivations that fit
    the given scenario.
    
    Attributes:
        llm (ChatGroq): Language model instance used for character generation
    """

    def __init__(self, llm: ChatGroq):
        """Initialize the character generator.
        
        Args:
            llm (ChatGroq): Language model instance to use for generation
        """
        self.llm = llm

    def generate_characters(self, scene_description: str, character_context: str,
                            user_name: str, user_description: str, 
                            num_characters: int = 3) -> Dict[str, Character]:
        """Generate a set of characters for a given scene.
        
        Creates characters with personalities, backgrounds and motivations that fit
        the provided scenario description and context.
        
        Args:
            scene_description (str): Description of the scene/scenario
            character_context (str): Additional context about expected character types
            user_name (str): Name of the user's character
            user_description (str): Description of the user's character
            num_characters (int, optional): Number of characters to generate. Defaults to 3.
            
        Returns:
            Dict[str, Character]: Dictionary mapping character names to Character instances
            
        Note:
            Falls back to predefined characters if generation fails
        """
        try:
            full_description = scene_description
            if character_context:
                full_description = f"{scene_description}\n\nExpected characters: {character_context}"
            
            chain = CHARACTER_GENERATION_PROMPT | self.llm
            response = chain.invoke({
                "scene_description": full_description,
                "num_characters": num_characters,
                "user_name": user_name,
                "user_description": user_description
            }).content.strip()
            
            char_data = clean_json_response(response)
            if not char_data:
                logging.error("Failed to parse character data, using fallback characters")
                return self.generate_fallback_characters()
            
            characters = {}
            for char in char_data["characters"]:
                config = CharacterConfig(
                    name=char["name"],
                    gender=char.get("gender", "non-binary"),
                    description=char.get("description", ""),
                    personality=char["personality"],
                    background=char["background"],
                    hidden_motive=char["hidden_motive"],
                    emoji=char.get("emoji", "👤"),
                    role_in_scene=char.get("role_in_scene", "")
                )
                characters[char["name"]] = Character(config)
                logging.info(f"Generated character: {char['name']}, {char.get('emoji', '👤')}")
            
            return characters
                
        except Exception as e:
            logging.error(f"Error during character generation: {e}")
            return self.generate_fallback_characters()

    def generate_fallback_characters(self) -> Dict[str, Character]:
        """Generate a set of predefined fallback characters.
        
        Creates a default set of characters to use when dynamic generation fails.
        
        Returns:
            Dict[str, Character]: Dictionary mapping character names to Character instances
        """
        fallback_chars = {
            "Adventurer": CharacterConfig(
                name="Adventurer",
                gender="male",
                description="A rugged individual with weathered features and well-worn traveling clothes",
                personality={"bravery": 0.8, "curiosity": 0.9},
                background="A seasoned explorer seeking ancient treasures",
                hidden_motive="Searching for a legendary artifact that could save their homeland",
                emoji="🗺️"
            ),
            "Scholar": CharacterConfig(
                name="Scholar",
                gender="female",
                description="A sharp-eyed woman in scholarly robes with wire-rimmed spectacles",
                personality={"intelligence": 0.9, "caution": 0.7},
                background="A knowledgeable researcher of ancient ruins",
                hidden_motive="Secretly working for a mysterious organization",
                emoji="📚"
            ),
            "Guide": CharacterConfig(
                name="Guide",
                gender="non-binary",
                description="A mysterious figure in local garb with keen eyes and quiet demeanor",
                personality={"wisdom": 0.8, "mystery": 0.6},
                background="A local expert with deep knowledge of the area",
                hidden_motive="Protecting an ancient secret about the location",
                emoji="🧭"
            )
        }
        
        return {
            name: Character(config)
            for name, config in fallback_chars.items()
        } 