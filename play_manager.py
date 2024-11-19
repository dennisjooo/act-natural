import os
import random
from langchain_groq import ChatGroq
from typing import Dict, Optional, Generator

from agents.character import Character, CharacterConfig
from agents.narrator import Narrator
from agents.orchestrator import Orchestrator
from agents.prompts import (
    SCENARIO_GENERATION_PROMPT,
    CHARACTER_GENERATION_PROMPT
)
from utils import clean_json_response

class PlayManager:
    """Manages the interactive play experience including characters, narration and orchestration.
    
    Handles character generation, scenario creation, and processing user interactions with the play.
    
    Attributes:
        narrator: The Narrator instance that provides scene descriptions and observations
        characters: Dictionary mapping character names to Character instances
        user_name: Name used to identify the user in interactions
        orchestrator: Optional Orchestrator instance that manages character interactions
        llm: The language model used for generating content
    """

    def __init__(self) -> None:
        """Initialize the PlayManager with default values."""
        self.narrator = Narrator()
        self.characters: Dict[str, Character] = {}
        self.user_name = "User"
        self.orchestrator: Optional[Orchestrator] = None
        self.llm = self._initialize_llm()
        
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
            scene_description: Description of the scene to base characters on
            num_characters: Number of characters to generate
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
                    hidden_motive=char["hidden_motive"]
                )
                self.characters[char["name"]] = Character(config)
                print(f"Generated character: {char['name']}")
                
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
    
    def start_play(self, scene_description: str = None, num_characters: int = 3) -> str:
        """Start the interactive play with given scene and characters.
        
        Args:
            scene_description: Description of the scene, prompts for input if None
            num_characters: Number of characters to generate
            
        Returns:
            str: Opening narration for the scene
        """
        if not scene_description:
            scene_description = input("Describe the scene and situation for the play: ")
        
        # Generate characters based on the scene
        self.generate_characters(scene_description, num_characters)
        
        # Initialize orchestrator with generated characters
        self.orchestrator = Orchestrator(self.characters, self.narrator)
        
        # Connect characters to orchestrator
        for char in self.characters.values():
            char.set_orchestrator(self.orchestrator)
        
        opening = self.narrator.set_scene(scene_description)
        return f"{opening}\n\nThe scene is set. You may begin interacting..."
    
    def process_input(self, user_input: str) -> Generator[str, None, None]:
        """Process user input and generate character responses.
        
        Args:
            user_input: The user's input message
            
        Yields:
            str: Generated responses including character dialogue and narration
        """
        user_input = user_input.strip('"')
        formatted_input = f'"{user_input}"'
        
        # Initial response to user
        next_speaker, target, reasoning = self.orchestrator.determine_next_interaction(
            "User", formatted_input
        )
        
        if next_speaker in self.characters:
            # Primary character responds to user
            char_response = self.characters[next_speaker].respond_to(
                formatted_input,
                "User",
                {"scene": self.narrator.current_scene}
            )
            
            # Ensure complete response
            char_response = char_response.replace('\n', ' ').strip()
            if not char_response.endswith(('.', '!', '?', '"')):
                char_response += '.'  # Add period if response seems incomplete
            
            # Update conversation history
            self.orchestrator._update_conversation_history(next_speaker, "User", char_response)
            
            # Possible narration
            if random.random() < 0.15:
                narration = self.narrator.observe_interaction(next_speaker, "User", char_response)
                if narration:
                    narration = narration.replace('\n', ' ').strip()
                    if not narration.endswith(('.', '!', '?')):
                        narration += '.'
                    yield narration
                    yield "PAUSE:0.5"
            
            yield char_response
            yield "PAUSE:1"
            
            # Process reactions
            remaining_chars = [name for name in self.characters.keys() if name != next_speaker]
            num_reactions = min(len(remaining_chars), random.randint(1, 2))
            reacting_chars = random.sample(remaining_chars, num_reactions)
            
            for char_name in reacting_chars:
                reaction = self.characters[char_name].respond_to(
                    char_response,
                    next_speaker,
                    {"scene": self.narrator.current_scene}
                )
                
                # Ensure complete reaction
                reaction = reaction.replace('\n', ' ').strip()
                if not reaction.endswith(('.', '!', '?', '"')):
                    reaction += '.'
                
                self.orchestrator._update_conversation_history(
                    char_name, next_speaker, reaction
                )
                
                # Add narration for dramatic reactions
                if random.random() < 0.2:
                    narration = self.narrator.observe_interaction(
                        char_name, next_speaker, reaction
                    )
                    if narration:
                        narration = narration.replace('\n', ' ').strip()
                        if not narration.endswith(('.', '!', '?')):
                            narration += '.'
                        yield "PAUSE:0.5"
                        yield narration
                
                yield "PAUSE:1"
                yield reaction
                
                # Handle follow-up response
                if random.random() < 0.2:
                    follow_up = self.characters[next_speaker].respond_to(
                        reaction,
                        char_name,
                        {"scene": self.narrator.current_scene}
                    )
                    
                    # Ensure complete follow-up
                    follow_up = follow_up.replace('\n', ' ').strip()
                    if not follow_up.endswith(('.', '!', '?', '"')):
                        follow_up += '.'
                    
                    self.orchestrator._update_conversation_history(
                        next_speaker, char_name, follow_up
                    )
                    
                    yield "PAUSE:1"
                    yield follow_up
    
    def cleanup(self) -> None:
        """Clean up resources when shutting down."""
        if self.orchestrator:
            self.orchestrator.executor.shutdown()