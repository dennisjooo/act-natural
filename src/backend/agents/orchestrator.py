import logging
import os
import random
import time
import threading
from concurrent.futures import ThreadPoolExecutor
from langchain_groq import ChatGroq
from typing import Dict, Tuple, Optional, List, Any
from queue import Queue

from .conversation_analyzer import ConversationAnalyzer
from .prompts import ORCHESTRATOR_FLOW_PROMPT, CHARACTER_THOUGHT_PROMPT
from ..schema import ConversationEvent, FlowConfig, OrchestratorConfig

class ConversationFlow:
    """Handles the logic for determining conversation flow and turn-taking.
    
    This class manages the flow of conversation between characters and users,
    determining who should speak next based on conversation context and timing.
    
    Attributes:
        characters (Dict[str, Any]): Dictionary of character objects
        last_user_interaction (float): Timestamp of last user interaction
        config (FlowConfig): Configuration settings for conversation flow
        analyzer (ConversationAnalyzer): Utility for analyzing conversation content
    """
    
    def __init__(self, characters: Dict[str, Any], config: Optional[FlowConfig] = None):
        """Initialize the ConversationFlow manager.
        
        Args:
            characters: Dictionary mapping character names to character objects
            config: Optional configuration settings, uses defaults if not provided
        """
        self.characters = characters
        self.last_user_interaction: float = time.time()
        self.config = config or FlowConfig()
        self.analyzer = ConversationAnalyzer()
        
    def should_initiate_conversation(self) -> bool:
        """Determine if a character should initiate conversation.
        
        Returns:
            bool: True if enough idle time has passed and random chance succeeds
        """
        time_since_user = time.time() - self.last_user_interaction
        return (
            time_since_user > self.config.idle_time_threshold and
            random.random() < self.config.initiation_chance
        )
    
    def get_next_speaker(self, last_event: Optional[ConversationEvent], 
                        active_characters: List[str]) -> Tuple[str, str, str]:
        """Determine who should speak next in the conversation.
        
        Args:
            last_event: The most recent conversation event, if any
            active_characters: List of characters eligible to speak
            
        Returns:
            Tuple containing:
                - Name of next speaker
                - Name of target/recipient
                - Reasoning for the selection
        """
        if not last_event:
            return self._get_initial_speaker(active_characters)
            
        if self._should_wait_for_user_response(last_event):
            return "user", last_event.speaker, "Waiting for user's response"
            
        if self._should_handle_direct_address(last_event):
            return (last_event.target, last_event.speaker, "Responding to direct address")
            
        return self._get_default_next_speaker(last_event, active_characters)

    def _get_initial_speaker(self, active_characters: List[str]) -> Tuple[str, str, str]:
        """Select initial speaker when there's no conversation history.
        
        Args:
            active_characters: List of characters eligible to speak
            
        Returns:
            Tuple containing:
                - Name of initial speaker
                - Target audience ("ALL")
                - Reasoning for selection
        """
        if not active_characters:
            return "user", "ALL", "Waiting for initial user input"
        speaker = random.choice(active_characters)
        return speaker, "ALL", "Starting new conversation thread"

    def _should_wait_for_user_response(self, last_event: ConversationEvent) -> bool:
        """Determine if we should wait for user response.
        
        Args:
            last_event: The most recent conversation event
            
        Returns:
            bool: True if system should wait for user response
        """
        # Wait if the last message was a question to the user
        if (last_event.target.lower() == "user" and 
            self.analyzer.is_question(last_event.message) and 
            random.random() < self.config.user_response_chance):
            return True
        return False

    def _should_handle_direct_address(self, last_event: ConversationEvent) -> bool:
        """Determine if we should handle direct address.
        
        Args:
            last_event: The most recent conversation event
            
        Returns:
            bool: True if the last event was a direct address to a character
        """
        return (last_event.target in self.characters and 
                random.random() < self.config.direct_response_chance)

    def _get_default_next_speaker(self, last_event: ConversationEvent, 
                                active_characters: List[str]) -> Tuple[str, str, str]:
        """Get default next speaker when no special conditions apply.
        
        Args:
            last_event: The most recent conversation event
            active_characters: List of characters eligible to speak
            
        Returns:
            Tuple containing:
                - Name of next speaker
                - Target recipient
                - Reasoning for selection
        """
        if not active_characters:
            return "user", "ALL", "Waiting for user input"
            
        if self.should_initiate_conversation():
            speaker = random.choice(active_characters)
            target = "User" if random.random() < 0.6 else random.choice(list(self.characters.keys()))
            return speaker, target, "Initiating new conversation thread"
            
        return "user", last_event.speaker, "Continuing conversation"

class ThoughtManager:
    """Manages background thought generation for characters.
    
    This class handles the asynchronous generation and queuing of character thoughts
    to provide more natural and dynamic character behaviors.
    
    Attributes:
        characters (Dict[str, Any]): Dictionary of character objects
        llm (ChatGroq): Language model for generating thoughts
        narrator (Any): Narrator object for scene context
        game_log (Any): Logger for game events
        config (OrchestratorConfig): Configuration settings
        thoughts_queue (Queue): Queue for storing generated thoughts
        thoughts_thread (threading.Thread): Background thread for thought generation
        conversation_history (List[ConversationEvent]): Recent conversation events
    """
    
    def __init__(self, characters: Dict[str, Any], llm: ChatGroq, 
                 narrator: Any, game_log: Any, config: OrchestratorConfig):
        """Initialize the ThoughtManager.
        
        Args:
            characters: Dictionary mapping character names to character objects
            llm: Language model for generating thoughts
            narrator: Narrator object for scene context
            game_log: Logger for game events
            config: Configuration settings for the orchestrator
        """
        self.characters = characters
        self.llm = llm
        self.narrator = narrator
        self.game_log = game_log
        self.config = config
        self.thoughts_queue: Queue = Queue()
        self.thoughts_thread = None
        self.conversation_history: List[ConversationEvent] = []
        self._start_thoughts_thread()

    def _start_thoughts_thread(self) -> None:
        """Start background thread for preloading character thoughts."""
        self.thoughts_thread = threading.Thread(
            target=self._preload_thoughts,
            daemon=True
        )
        self.thoughts_thread.start()

    def _preload_thoughts(self) -> None:
        """Continuously generate and queue character thoughts in background."""
        while True:
            try:
                max_queue_size = len(self.characters) * self.config.thought_queue_multiplier
                current_size = self.thoughts_queue.qsize()
                
                if current_size < max_queue_size:
                    char_thought_counts = {char_name: 0 for char_name in self.characters}
                    
                    # Count existing thoughts
                    for _ in range(current_size):
                        char_name, thought = self.thoughts_queue.get()
                        char_thought_counts[char_name] += 1
                        self.thoughts_queue.put((char_name, thought))
                    
                    # Generate thoughts for characters with fewer thoughts
                    for char_name, count in char_thought_counts.items():
                        if count < self.config.thought_queue_multiplier:
                            char = self.characters[char_name]
                            thought = self._generate_hidden_thought(char)
                            if thought:
                                self.thoughts_queue.put((char_name, thought))
                            
                time.sleep(1)
            except Exception as e:
                logging.error(f"Error preloading thoughts: {e}")
                time.sleep(5)

    def _generate_hidden_thought(self, character: Any) -> Optional[str]:
        """Generate a hidden thought for a character.
        
        Args:
            character: Character object to generate thought for
            
        Returns:
            str: Generated thought text, or None if generation fails
        """
        try:
            chain = CHARACTER_THOUGHT_PROMPT | self.llm
            
            # Format recent history
            recent_history = "\n".join([
                f"{event.speaker} to {event.target}: {event.message}"
                for event in self.conversation_history[-2:]  # Get last 2 messages
            ])

            response = chain.invoke({
                "name": character.config.name,
                "personality": self._format_character_traits(character),
                "motive": character.config.hidden_motive,
                "scene": self.narrator.current_scene,
                "history": recent_history  # Add this line
            }).content.strip()

            if response:
                self.game_log.log_event("hidden_thought", {
                    "character": character.config.name,
                    "thought": response
                })
            return response
            
        except Exception as e:
            logging.error(f"Error generating thought: {e}")
            return None

    def _format_character_traits(self, character: Any) -> str:
        """Format character traits for prompts.
        
        Args:
            character: Character object containing personality traits
            
        Returns:
            str: Formatted string of personality traits and values
        """
        return ", ".join([
            f"{k}: {v:.1f}" 
            for k, v in character.config.personality.items()
        ])

class Orchestrator:
    """Manages conversation flow and character interactions.
    
    This class coordinates the overall flow of conversation, character responses,
    and thought generation in the interactive story.
    
    Attributes:
        config (OrchestratorConfig): Configuration settings
        characters (Dict[str, Any]): Dictionary of character objects
        narrator (Any): Narrator object for scene context
        game_log (Any): Logger for game events
        llm (ChatGroq): Language model for generating responses
        chain: Prompt chain for orchestrating flow
        conversation_history (List[ConversationEvent]): Recent conversation events
        flow_manager (ConversationFlow): Manager for conversation flow
        thought_manager (ThoughtManager): Manager for character thoughts
        executor (ThreadPoolExecutor): Thread pool for processing responses
    """
    
    def __init__(self, characters: Dict[str, Any], narrator: Any, game_log: Any,
                 config: Optional[OrchestratorConfig] = None) -> None:
        """Initialize the Orchestrator.
        
        Args:
            characters: Dictionary mapping character names to character objects
            narrator: Narrator object for scene context
            game_log: Logger for game events
            config: Optional configuration settings
        """
        self.config = config or OrchestratorConfig()
        self.characters = characters
        self.narrator = narrator
        self.game_log = game_log
        self.llm = self._initialize_llm()
        self.chain = ORCHESTRATOR_FLOW_PROMPT | self.llm
        self.conversation_history: List[ConversationEvent] = []
        
        self.flow_manager = ConversationFlow(characters)
        self.thought_manager = ThoughtManager(
            characters, self.llm, narrator, game_log, self.config
        )
        
        self.executor = ThreadPoolExecutor(max_workers=len(characters))

    def _initialize_llm(self) -> ChatGroq:
        """Initialize the language model.
        
        Returns:
            ChatGroq: Configured language model instance
        """
        return ChatGroq(
            api_key=os.getenv("GROQ_API_KEY"),
            model_name=os.getenv("ORCHESTRATOR_MODEL"),
            temperature=0.25
        )

    def _get_active_characters(self, exclude: Optional[List[str]] = None) -> List[str]:
        """Get list of characters who haven't spoken recently.
        
        Args:
            exclude: Optional list of character names to exclude
            
        Returns:
            List[str]: Names of characters eligible to speak
        """
        exclude = exclude or []
        recent_speakers = {
            event.speaker for event in self.conversation_history[-3:]
            if event.speaker in self.characters
        }
        return [
            name for name in self.characters.keys()
            if name not in recent_speakers and name not in exclude
        ]

    def _update_conversation_history(self, speaker: str, target: str, message: str) -> None:
        """Update the conversation history and log the interaction.
        
        Args:
            speaker: Name of speaking character
            target: Name of target/recipient
            message: Content of the message
        """
        event = ConversationEvent(
            speaker=speaker,
            target=target,
            message=message
        )
        self.conversation_history.append(event)
        
        if len(self.conversation_history) > self.config.max_history_length:
            self.conversation_history = self.conversation_history[-self.config.max_history_length:]
            
        # Update thought manager's conversation history
        self.thought_manager.conversation_history = self.conversation_history
            
        self.game_log.log_event("dialogue", {
            "speaker": speaker,
            "target": target,
            "message": message
        })

    def _process_character_response(self, char_name: str, message: str, target: str) -> None:
        """Process a character's response in the thread pool.
        
        Args:
            char_name: Name of responding character
            message: Message being responded to
            target: Target/recipient of the response
        """
        try:
            recent_events = self.conversation_history[-3:] if self.conversation_history else []
            similar_topics = any(
                event.speaker != char_name and
                ConversationAnalyzer.check_similar_topics(message, event.message)
                for event in recent_events
            )
            
            context = {
                "scene": self.narrator.current_scene,
                "avoid_similar_response": similar_topics
            }
            
            self.executor.submit(
                self.characters[char_name].respond_to,
                message,
                target,
                context
            )
        except Exception as e:
            logging.error(f"Error processing character response: {e}")

    def determine_next_interaction(self, last_speaker: str, last_message: str) -> Tuple[str, str, str]:
        """Determine and log the next interaction in the conversation flow.
        
        Args:
            last_speaker: Name of previous speaker
            last_message: Content of previous message
            
        Returns:
            Tuple containing:
                - Name of next speaker
                - Target recipient
                - Reasoning for selection
        """
        try:
            if last_speaker == "User":
                self.flow_manager.last_user_interaction = time.time()
            
            active_chars = self._get_active_characters()
            last_event = self.conversation_history[-1] if self.conversation_history else None
            
            next_speaker, target, reasoning = self.flow_manager.get_next_speaker(
                last_event, active_chars
            )
            
            self._update_conversation_history(last_speaker, target, last_message)
            
            if next_speaker in self.characters:
                self._process_character_response(next_speaker, last_message, target)
            
            self.game_log.log_event("flow_decision", {
                "last_speaker": last_speaker,
                "next_speaker": next_speaker,
                "target": target,
                "reasoning": reasoning
            })
            
            return next_speaker, target, reasoning
            
        except Exception as e:
            logging.error(f"Error in orchestrator: {e}")
            return self._get_fallback_interaction(last_speaker)

    def _get_fallback_interaction(self, last_speaker: str) -> Tuple[str, str, str]:
        """Provide fallback interaction if normal flow fails.
        
        Args:
            last_speaker: Name of previous speaker
            
        Returns:
            Tuple containing fallback speaker, target and reasoning
        """
        if last_speaker.lower() == "user":
            char_name = next(iter(self.characters.keys()))
            return (char_name, "User", "Responding to user's message")
        else:
            return ("user", next(iter(self.characters.keys())), "Awaiting user's response")

    def get_initial_character_response(self) -> str:
        """Generate initial character response after scene is set.
        
        Returns:
            str: Initial character response or fallback message
        """
        try:
            initial_speaker = random.choice(list(self.characters.keys()))
            char = self.characters[initial_speaker]
            
            response = char.respond_to(
                "SCENE_START",
                "ALL",
                {"scene": self.narrator.current_scene}
            )
            
            self._update_conversation_history(initial_speaker, "ALL", response)
            return response
            
        except Exception as e:
            logging.error(f"Error generating initial response: {e}")
            return f"[{list(self.characters.keys())[0]}]: *looks around curiously*"

    @property
    def thoughts_queue(self) -> Queue:
        """Access the thoughts queue from the ThoughtManager.
        
        Returns:
            Queue: Queue containing generated character thoughts
        """
        return self.thought_manager.thoughts_queue

    def get_next_thought(self) -> Optional[Tuple[str, str]]:
        """Get the next available thought from the queue.
        
        Returns:
            Optional[Tuple[str, str]]: Tuple of (character_name, thought) or None if queue is empty
        """
        try:
            if not self.thoughts_queue.empty():
                return self.thoughts_queue.get_nowait()
            return None
        except Exception as e:
            logging.error(f"Error getting next thought: {e}")
            return None