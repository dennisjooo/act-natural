import os
import random
from langchain_groq import ChatGroq
from typing import Dict, Optional, Generator

from .agents import Character, Narrator, Orchestrator, ResponseProcessor, GameLog
from .generator import ScenarioGenerator, CharacterGenerator
from .schema import PlayConfig

class PlayManager:
    """Manages the interactive play experience including characters, narration and orchestration.
    
    The PlayManager class is responsible for coordinating all aspects of the interactive play experience.
    It handles character generation, scenario creation, and processes user interactions with the play.
    
    Attributes:
        config (PlayConfig): Configuration settings for the play including defaults and parameters
        narrator (Narrator): Narrator instance that provides scene descriptions and observations
        characters (Dict[str, Character]): Dictionary mapping character names to Character instances
        user_name (str): Name used to identify the user in character interactions
        user_description (str): Description of the user's character/role for interactions
        orchestrator (Optional[Orchestrator]): Orchestrator instance managing character interactions
        llm (ChatGroq): Language model instance used for content generation
        response_processor (Optional[ResponseProcessor]): Processor for formatting character responses
        character_context (str): Additional context about expected characters in the scene
        user_role (str): The specific role/position assigned to the user in the scenario
        
    The PlayManager serves as the central coordinator, initializing and managing all the components
    needed for the interactive play experience. It handles:
    - Character generation and management
    - Scene/scenario creation
    - Processing user input and generating responses
    - Coordinating character interactions
    - Managing the flow of conversation
    """

    def __init__(self, config: Optional[PlayConfig] = None) -> None:
        """Initialize a new PlayManager instance.
        
        Creates a new PlayManager with the specified configuration. If no configuration is provided,
        uses default PlayConfig settings.
        
        Args:
            config (Optional[PlayConfig]): Configuration settings for the play. If None, uses defaults.
            
        The initialization process:
        1. Sets up basic configuration and state
        2. Creates the narrator instance
        3. Initializes empty character dictionary
        4. Sets default user information
        5. Creates language model instance
        6. Prepares for orchestrator and response processor
        """
        self.config = config or PlayConfig()
        self.narrator = Narrator()
        self.characters: Dict[str, Character] = {}
        self.user_name = self.config.default_user_name
        self.user_description = self.config.default_user_description
        self.orchestrator: Optional[Orchestrator] = None
        self.llm = self._initialize_llm()
        self.response_processor: Optional[ResponseProcessor] = None
        self.character_context: str = ""
        self.user_role: str = ""
        
        # Add game_log initialization
        self.game_log = GameLog()
        
        # Initialize generators
        self.character_generator = CharacterGenerator(self.llm)
        self.scenario_generator = ScenarioGenerator(self.llm)
    
    def _initialize_llm(self) -> ChatGroq:
        """Initialize and configure the language model instance.
        
        Creates a new ChatGroq instance with appropriate configuration settings from environment
        variables. Sets up the model with specified temperature for content generation.
        
        Returns:
            ChatGroq: Configured language model instance ready for use
            
        The method uses environment variables:
        - GROQ_API_KEY: API key for authentication
        - SCENARIO_MODEL: Name of the model to use
        """
        return ChatGroq(
            api_key=os.getenv("GROQ_API_KEY"),
            model_name=os.getenv("SCENARIO_MODEL"),
            temperature=0.5
        )
    
    def generate_characters(self, scene_description: str, num_characters: int = 3) -> None:
        """Generate character set based on the scene description.
        
        Creates a set of characters appropriate for the given scene, with personalities,
        backgrounds, and motivations that fit the scenario.
        
        Args:
            scene_description (str): Detailed description of the scene and situation
            num_characters (int): Number of characters to generate. Defaults to 3
            
        Side Effects:
            - Populates self.characters with generated Character instances
            - Prints status messages about character generation
            - Falls back to default characters if generation fails
            
        The generation process:
        1. Combines scene description with any existing character context
        2. Uses LLM to generate character details
        3. Creates CharacterConfig instances for each character
        4. Instantiates Character objects and adds them to self.characters
        """
        self.characters = self.character_generator.generate_characters(
            scene_description,
            self.character_context,
            self.user_name,
            self.user_description,
            num_characters
        )
    
    def generate_scenario(self) -> str:
        """Generate a random scenario for the interactive play.
        
        Creates a detailed scenario description including setting, situation, atmosphere,
        and the user's role within the scene.
        
        Returns:
            str: Complete scenario description combining all elements
            
        Side Effects:
            - Sets self.character_context with expected character types
            - Sets self.user_role with the user's assigned role
            
        The generation process:
        1. Uses LLM to generate scenario components
        2. Extracts and stores character context and user role
        3. Combines elements into cohesive description
        4. Falls back to predefined scenarios if generation fails
        """
        scenario_description, self.character_context, self.user_role = (
            self.scenario_generator.generate_scenario(self.user_name, self.user_description)
        )
        return scenario_description
    
    def start_play(self, scene_description: str, num_characters: Optional[int] = None, 
                   user_name: Optional[str] = None, user_description: Optional[str] = None) -> str:
        """Initialize and start the interactive play experience.
        
        Sets up all necessary components and begins the interactive play session
        with the specified scene and characters.
        
        Args:
            scene_description (str): Detailed description of the scene and situation
            num_characters (Optional[int]): Number of characters to generate
            user_name (Optional[str]): Name for the user's character
            user_description (Optional[str]): Description of the user's character
            
        Returns:
            str: Opening narration and ready message
            
        Side Effects:
            - Sets user information
            - Generates characters
            - Initializes orchestrator and response processor
            - Configures characters with user info and orchestrator
            
        The startup process:
        1. Sets user information
        2. Generates appropriate number of characters
        3. Creates orchestrator and response processor
        4. Configures all characters with necessary information
        5. Sets initial scene through narrator
        """
        # Set user info before any character generation or scenario creation
        self.user_name = user_name or self.config.default_user_name
        self.user_description = user_description or self.config.default_user_description
        num_characters = num_characters or self.config.default_num_characters
        
        if not scene_description:
            scene_description = input("Describe the scene and situation for the play: ")

        # Generate characters with updated user info
        self.generate_characters(scene_description, num_characters)
        self.orchestrator = Orchestrator(self.characters, self.narrator, self.game_log)
        
        # Log characters after generation
        for name, char in self.characters.items():
            self.game_log.add_character(name, char.config.__dict__)
        
        # Log the scene and narrator information
        self.game_log.log_event("narrator_setup", {
            "scene_description": scene_description,
            "narrator_type": type(self.narrator).__name__
        })
        self.game_log.set_scene(scene_description)
        
        self.response_processor = ResponseProcessor(self.characters, self.narrator)
        
        # Set user info for each character
        for char in self.characters.values():
            char.set_orchestrator(self.orchestrator)
            char.set_user_info(self.user_name, self.user_description)
        
        opening = self.narrator.set_scene(scene_description)
        
        # Log the narrator's opening statement
        self.game_log.log_event("narration", {
            "type": "opening",
            "content": opening
        })
        
        return f"{opening}\n\nThe scene is set. You may begin interacting..."
    
    def process_input(self, user_input: str) -> Generator[str, None, None]:
        """Process user input and generate character responses.
        
        Handles user input by determining appropriate character responses,
        processing those responses, and managing the flow of conversation.
        
        Args:
            user_input (str): The user's input text
            
        Yields:
            str: Character responses, reactions, and follow-up messages
            
        Raises:
            RuntimeError: If play hasn't been properly started
            
        The processing flow:
        1. Validates play state
        2. Formats user input
        3. Determines next speaker
        4. Generates primary response
        5. Processes reactions from other characters
        6. Updates conversation history
        """
        if not self.orchestrator or not self.response_processor:
            raise RuntimeError("Play must be started before processing input")
            
        # Ensure input is wrapped in quotes, but avoid double-wrapping
        cleaned_input = user_input.strip().strip("\"\'")
        formatted_input = f'"{cleaned_input}"'
        
        # Get next speaker and target
        next_speaker, target, _ = self.orchestrator.determine_next_interaction(
            "User", formatted_input
        )
        
        if next_speaker not in self.characters:
            next_speaker = random.choice(list(self.characters.keys()))
            target = "User"
        
        # Primary character response
        char_response = self.characters[next_speaker].respond_to(
            formatted_input,
            target,
            {"scene": self.narrator.current_scene}
        )
        
        # Process primary response
        yield from self.response_processor.process_response(next_speaker, target, char_response)
        
        # Update conversation history
        self.orchestrator._update_conversation_history(next_speaker, target, char_response)
        
        # Handle reactions
        yield from self._process_reactions(next_speaker, char_response)
        
        # If narrator provides any observations
        if narrator_observation := self.narrator.get_observation():
            self._log_narrator_event("observation", narrator_observation)
            yield narrator_observation
    
    def _process_reactions(self, primary_speaker: str, primary_response: str) -> Generator[str, None, None]:
        """Process reactions from other characters to maintain engagement.
        
        Generates and manages reactions from other characters to the primary speaker's
        response, ensuring ongoing engagement through varied interactions.
        
        Args:
            primary_speaker (str): Name of the character who gave initial response
            primary_response (str): Content of the initial response
            
        Yields:
            str: Character reactions, follow-up responses, and user prompts
            
        Side Effects:
            Updates conversation history in orchestrator
            
        The reaction process:
        1. Selects random subset of characters to react
        2. Generates and processes their reactions
        3. Occasionally generates follow-up interactions
        4. Ensures user engagement through character prompts
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
            
            if random.random() < 0.2:
                yield from self._process_followup(primary_speaker, char_name, reaction)
        
        # After all reactions, have a character prompt the user
        prompt_char = random.choice(list(self.characters.keys()))
        prompt_response = self.characters[prompt_char].respond_to(
            "prompt_user",  # Special signal
            "User",
            {"scene": self.narrator.current_scene}
        )
        
        yield prompt_response  # Make sure we're yielding the prompt
        self.orchestrator._update_conversation_history(prompt_char, "User", prompt_response)
        
    def _process_followup(self, speaker: str, target: str, 
                          previous_response: str) -> Generator[str, None, None]:
        """Process follow-up responses between characters.
        
        Generates and handles follow-up interactions between characters to create
        more natural conversation flow and deeper character interactions.
        
        Args:
            speaker (str): Name of the character speaking
            target (str): Name of the character being addressed
            previous_response (str): The response being followed up on
            
        Yields:
            str: Follow-up responses from characters
            
        Side Effects:
            Updates conversation history in orchestrator
            
        The follow-up process:
        1. Generates appropriate follow-up response
        2. Processes the response through response processor
        3. Updates conversation history
        """
        follow_up = self.characters[speaker].respond_to(
            previous_response,
            target,
            {"scene": self.narrator.current_scene}
        )
        
        yield from self.response_processor.process_response(speaker, target, follow_up)
        self.orchestrator._update_conversation_history(speaker, target, follow_up)
    
    def cleanup(self) -> None:
        """Clean up resources when shutting down the play manager.
        
        Performs necessary cleanup operations when the play session ends,
        ensuring proper resource management.
        
        Side Effects:
            Shuts down the orchestrator's thread pool executor if it exists
            
        The cleanup process:
        1. Checks for active orchestrator
        2. Shuts down thread pool executor if present
        3. Ensures proper resource release
        """
        if self.orchestrator:
            self.orchestrator.executor.shutdown()
    
    def _log_narrator_event(self, event_type: str, content: str) -> None:
        """Log narrator events to the game log.
        
        Args:
            event_type (str): Type of narrator event (e.g., 'scene_description', 'observation')
            content (str): The actual narration content
        """
        self.game_log.log_event("narration", {
            "type": event_type,
            "content": content
        })