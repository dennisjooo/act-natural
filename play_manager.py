import os
import random
from langchain_groq import ChatGroq
from typing import Dict, Optional, Generator

from agents.character import Character
from agents.narrator import Narrator
from agents.orchestrator import Orchestrator
from agents.prompts import (
    SCENARIO_GENERATION_PROMPT,
    CHARACTER_GENERATION_PROMPT
)
from config.character_config import CharacterConfig
from utils import clean_json_response
from config.play_config import PlayConfig
from agents.response_processor import ResponseProcessor

class PlayManager:
    """Manages the interactive play experience including characters, narration and orchestration.
    
    Handles character generation, scenario creation, and processing user interactions with the play.
    
    Attributes:
        config (PlayConfig): Configuration settings for the play
        narrator (Narrator): The Narrator instance that provides scene descriptions and observations
        characters (Dict[str, Character]): Dictionary mapping character names to Character instances
        user_name (str): Name used to identify the user in interactions
        user_description (str): Description of the user for character interactions
        orchestrator (Optional[Orchestrator]): Orchestrator instance that manages character interactions
        llm (ChatGroq): The language model used for generating content
        response_processor (Optional[ResponseProcessor]): Processor for formatting character responses
    """

    def __init__(self, config: Optional[PlayConfig] = None) -> None:
        """Initialize the PlayManager with optional configuration.
        
        Args:
            config (Optional[PlayConfig]): Configuration settings for the play. Defaults to None.
        """
        self.config = config or PlayConfig()
        self.narrator = Narrator()
        self.characters: Dict[str, Character] = {}
        self.user_name = self.config.default_user_name
        self.orchestrator: Optional[Orchestrator] = None
        self.llm = self._initialize_llm()
        self.response_processor: Optional[ResponseProcessor] = None
        
    def _initialize_llm(self) -> ChatGroq:
        """Initialize the language model with configuration.
        
        Returns:
            ChatGroq: Configured language model instance
        """
        return ChatGroq(
            api_key=os.getenv("GROQ_API_KEY"),
            model_name="gemma2-9b-it",
            temperature=0.5
        )
    
    def generate_characters(self, scene_description: str, num_characters: int = 3) -> None:
        """Generate characters based on the scene description.
        
        Args:
            scene_description (str): Description of the scene to base characters on
            num_characters (int): Number of characters to generate. Defaults to 3.
        """
        try:
            chain = CHARACTER_GENERATION_PROMPT | self.llm
            response = chain.invoke({
                "scene_description": scene_description,
                "num_characters": num_characters
            }).content.strip()
            
            # Use the new clean_json_response function
            char_data = clean_json_response(response)
            if not char_data:
                print("Failed to parse character data, using fallback characters")
                self.generate_fallback_characters()
                return
            
            # Create characters using CharacterConfig
            for char in char_data["characters"]:
                config = CharacterConfig(
                    name=char["name"],
                    gender=char.get("gender", "non-binary"),
                    personality=char["personality"],
                    background=char["background"],
                    hidden_motive=char["hidden_motive"],
                    emoji=char.get("emoji", "👤")
                )
                self.characters[char["name"]] = Character(config)
                print(f"Generated character: {char['name']}, {char.get('emoji', '👤')}")
                
        except Exception as e:
            print(f"Error during character generation: {e}")
            self.generate_fallback_characters()
    
    def generate_fallback_characters(self) -> None:
        """Create default characters if generation fails."""
        fallback_chars = {
            "Adventurer": CharacterConfig(
                name="Adventurer",
                gender="male",
                personality={"bravery": 0.8, "curiosity": 0.9},
                background="A seasoned explorer seeking ancient treasures",
                hidden_motive="Searching for a legendary artifact that could save their homeland"
            ),
            "Scholar": CharacterConfig(
                name="Scholar",
                gender="female",
                personality={"intelligence": 0.9, "caution": 0.7},
                background="A knowledgeable researcher of ancient ruins",
                hidden_motive="Secretly working for a mysterious organization"
            ),
            "Guide": CharacterConfig(
                name="Guide",
                gender="non-binary",
                personality={"wisdom": 0.8, "mystery": 0.6},
                background="A local expert with deep knowledge of the area",
                hidden_motive="Protecting an ancient secret about the location"
            )
        }
        
        self.characters = {
            name: Character(config)
            for name, config in fallback_chars.items()
        }
    
    def generate_scenario(self) -> str:
        """Generate a random scenario for the play.
        
        Returns:
            str: Generated scenario description
        """
        try:
            chain = SCENARIO_GENERATION_PROMPT | self.llm
            response = chain.invoke({}).content
            
            # Use the new clean_json_response function
            scenario_data = clean_json_response(response)
            if not scenario_data:
                print("Failed to parse scenario data, using fallback scenario")
                return self.get_fallback_scenario()
            
            return (
                f"{scenario_data['setting']}. "
                f"{scenario_data['situation']} "
                f"{scenario_data['atmosphere']}"
            )
        except Exception as e:
            print(f"Error generating scenario: {e}")
            return self.get_fallback_scenario()
    
    def get_fallback_scenario(self) -> str:
        """Get a pre-written fallback scenario if generation fails.
        
        Returns:
            str: Random pre-written scenario
        """
        fallback_scenarios = [
            "A mysterious tavern on a stormy night. Travelers from different walks of life have sought shelter here, each carrying their own secrets and stories. The atmosphere is tense with unspoken tales and hidden agendas.",
            "An abandoned mansion during a masquerade ball. The guests are trapped inside by a mysterious force, and everyone seems to have a hidden agenda. The air is thick with intrigue and suspicion.",
            "A futuristic space station at the edge of known space. The station's systems are malfunctioning, and the diverse crew members each seem to know more than they're letting on. The metallic corridors echo with whispered conspiracies."
        ]
        return random.choice(fallback_scenarios)
    
    def start_play(self, scene_description: str, num_characters: Optional[int] = None, 
                   user_name: Optional[str] = None, user_description: Optional[str] = None) -> str:
        """Start the interactive play with given scene and characters.
        
        Args:
            scene_description (str): Description of the scene and situation
            num_characters (Optional[int]): Number of characters to generate. Defaults to config value.
            user_name (Optional[str]): Name of the user. Defaults to config value.
            user_description (Optional[str]): Description of the user. Defaults to config value.
            
        Returns:
            str: Opening narration and ready message
        """
        num_characters = num_characters or self.config.default_num_characters
        self.user_name = user_name or self.config.default_user_name
        self.user_description = user_description or self.config.default_user_description
        
        if not scene_description:
            scene_description = input("Describe the scene and situation for the play: ")
        
        self.generate_characters(scene_description, num_characters)
        self.orchestrator = Orchestrator(self.characters, self.narrator)
        self.response_processor = ResponseProcessor(self.characters, self.narrator)
        
        for char in self.characters.values():
            char.set_orchestrator(self.orchestrator)
            char.set_user_info(self.user_name, self.user_description)
        
        opening = self.narrator.set_scene(scene_description)
        return f"{opening}\n\nThe scene is set. You may begin interacting..."
    
    def process_input(self, user_input: str) -> Generator[str, None, None]:
        """Process user input and generate character responses.
        
        Args:
            user_input (str): The user's input message
            
        Yields:
            str: Character responses and narration
            
        Raises:
            RuntimeError: If play hasn't been started
        """
        if not self.orchestrator or not self.response_processor:
            raise RuntimeError("Play must be started before processing input")
            
        formatted_input = f'"{user_input.strip("\"\'")}"'
        
        # Get next speaker
        next_speaker, target, _ = self.orchestrator.determine_next_interaction(
            "User", formatted_input
        )
        
        if next_speaker not in self.characters:
            return
            
        # Primary character response
        char_response = self.characters[next_speaker].respond_to(
            formatted_input,
            "User",
            {"scene": self.narrator.current_scene}
        )
        
        # Process primary response
        yield from self.response_processor.process_response(next_speaker, "User", char_response)
        
        # Update conversation history
        self.orchestrator._update_conversation_history(next_speaker, "User", char_response)
        
        # Handle reactions
        yield from self._process_reactions(next_speaker, char_response)
    
    def _process_reactions(self, primary_speaker: str, primary_response: str) -> Generator[str, None, None]:
        """Process reactions from other characters.
        
        Args:
            primary_speaker (str): Name of the character who spoke initially
            primary_response (str): The initial character's response
            
        Yields:
            str: Reaction responses from other characters
        """
        remaining_chars = [name for name in self.characters.keys() if name != primary_speaker]
        num_reactions = min(len(remaining_chars), random.randint(1, 2))
        
        for char_name in random.sample(remaining_chars, num_reactions):
            reaction = self.characters[char_name].respond_to(
                primary_response,
                primary_speaker,
                {"scene": self.narrator.current_scene}
            )
            
            yield from self.response_processor.process_response(char_name, primary_speaker, reaction)
            self.orchestrator._update_conversation_history(char_name, primary_speaker, reaction)
            
            # Handle follow-up
            if random.random() < 0.2:
                yield from self._process_followup(primary_speaker, char_name, reaction)
    
    def _process_followup(self, speaker: str, target: str, previous_response: str) -> Generator[str, None, None]:
        """Process follow-up responses between characters.
        
        Args:
            speaker (str): Name of the character speaking
            target (str): Name of the character being spoken to
            previous_response (str): The previous response being followed up on
            
        Yields:
            str: Follow-up responses
        """
        follow_up = self.characters[speaker].respond_to(
            previous_response,
            target,
            {"scene": self.narrator.current_scene}
        )
        
        yield from self.response_processor.process_response(speaker, target, follow_up)
        self.orchestrator._update_conversation_history(speaker, target, follow_up)
    
    def cleanup(self) -> None:
        """Clean up resources when shutting down."""
        if self.orchestrator:
            self.orchestrator.executor.shutdown()