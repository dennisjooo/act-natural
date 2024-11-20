import json
import os
import random
import time
import threading
from concurrent.futures import ThreadPoolExecutor
from dataclasses import dataclass
from enum import Enum
from langchain_groq import ChatGroq
from typing import Dict, Tuple, Optional, List, Any
from queue import Queue

from .prompts import (
    ORCHESTRATOR_FLOW_PROMPT,
    CHARACTER_THOUGHT_PROMPT
)

class SpeakerType(Enum):
    """Types of speakers in the conversation system."""
    USER = "user"
    CHARACTER = "character" 
    ALL = "all"

@dataclass
class ConversationEvent:
    """Represents a single conversation interaction between characters.
    
    Attributes:
        speaker (str): The name of the character speaking
        target (str): The name of the character being spoken to 
        message (str): The content of the message
        timestamp (float): Unix timestamp of when the message was sent
    """
    speaker: str
    target: str 
    message: str
    timestamp: float = time.time()

class ConversationFlow:
    """Handles the logic for determining conversation flow and turn-taking.
    
    Manages conversation dynamics including idle time thresholds, initiation chances,
    and response probabilities between characters and users.
    """
    
    def __init__(self, characters: Dict[str, Any]):
        """Initialize the ConversationFlow manager.
        
        Args:
            characters: Dictionary mapping character names to Character objects
        """
        self.characters = characters
        self.last_user_interaction: float = time.time()
        
        # Configuration constants
        self.IDLE_TIME_THRESHOLD = 45  # seconds before characters initiate
        self.INITIATION_CHANCE = 0.2   # 20% chance to initiate
        self.USER_RESPONSE_CHANCE = 0.9  # 90% chance to wait for user after question
        self.DIRECT_RESPONSE_CHANCE = 0.9  # 90% chance to respond when directly addressed
        
    def should_initiate_conversation(self) -> bool:
        """Determine if a character should initiate a new conversation thread.
        
        Returns:
            bool: True if conditions are met for character initiation
        """
        time_since_user = time.time() - self.last_user_interaction
        return (
            time_since_user > self.IDLE_TIME_THRESHOLD and
            random.random() < self.INITIATION_CHANCE
        )
    
    def get_next_speaker(self, last_event: Optional[ConversationEvent], 
                        active_characters: List[str]) -> Tuple[str, str, str]:
        """Determine who should speak next based on conversation context.
        
        Args:
            last_event: The most recent conversation event, if any
            active_characters: List of characters eligible to speak
            
        Returns:
            Tuple[str, str, str]: (next_speaker, target, reasoning)
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
            Tuple[str, str, str]: (initial_speaker, target, reasoning)
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
            self._is_question(last_event.message) and 
            random.random() < self.USER_RESPONSE_CHANCE):
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
                random.random() < self.DIRECT_RESPONSE_CHANCE)

    def _get_default_next_speaker(self, last_event: ConversationEvent, 
                                active_characters: List[str]) -> Tuple[str, str, str]:
        """Get default next speaker when no special conditions apply.
        
        Args:
            last_event: The most recent conversation event
            active_characters: List of characters eligible to speak
            
        Returns:
            Tuple[str, str, str]: (next_speaker, target, reasoning)
        """
        if not active_characters:
            return "user", "ALL", "Waiting for user input"
            
        if self.should_initiate_conversation():
            speaker = random.choice(active_characters)
            target = "User" if random.random() < 0.6 else random.choice(list(self.characters.keys()))
            return speaker, target, "Initiating new conversation thread"
            
        return "user", last_event.speaker, "Continuing conversation"

    def _is_question(self, message: str) -> bool:
        """Check if a message is a question.
        
        Args:
            message: The message content to check
            
        Returns:
            bool: True if the message appears to be a question
        """
        question_indicators = [
            "?", "what", "how", "why", "where", "when", "who", "which",
            "could you", "would you", "will you", "can you", "do you"
        ]
        message_lower = message.lower()
        return any(indicator in message_lower for indicator in question_indicators)

class Orchestrator:
    """Manages conversation flow and character interactions.
    
    Coordinates character responses, maintains conversation history, and manages
    background thought generation for characters.
    """
    
    # Constants moved to class level
    MAX_HISTORY_LENGTH = 10
    THOUGHT_QUEUE_MULTIPLIER = 2
    
    def __init__(self, characters: Dict[str, Any], narrator: Any) -> None:
        """Initialize the Orchestrator.
        
        Args:
            characters: Dictionary mapping character names to Character objects
            narrator: Narrator instance for scene management
        """
        self.characters = characters
        self.narrator = narrator
        self.llm = self._initialize_llm()
        self.chain = ORCHESTRATOR_FLOW_PROMPT | self.llm
        self.conversation_history: List[ConversationEvent] = []
        
        # Initialize conversation flow manager
        self.flow_manager = ConversationFlow(characters)
        
        # Initialize thread pool and thought queue
        self.executor = ThreadPoolExecutor(max_workers=len(characters))
        self.thoughts_queue: Queue = Queue()
        self._start_thoughts_thread()
    
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
            List[str]: List of character names who are eligible to speak
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
                max_queue_size = len(self.characters) * self.THOUGHT_QUEUE_MULTIPLIER
                current_size = self.thoughts_queue.qsize()
                
                # Check if we need more thoughts
                if current_size < max_queue_size:
                    # Count thoughts per character in queue
                    char_thought_counts = {char_name: 0 for char_name in self.characters}
                    
                    # Count existing thoughts
                    for _ in range(current_size):
                        char_name, thought = self.thoughts_queue.get()
                        char_thought_counts[char_name] += 1
                        self.thoughts_queue.put((char_name, thought))
                    
                    # Generate thoughts for characters with fewer thoughts
                    for char_name, count in char_thought_counts.items():
                        if count < self.THOUGHT_QUEUE_MULTIPLIER:
                            char = self.characters[char_name]
                            thought = self._generate_hidden_thought(char)
                            if thought:
                                self.thoughts_queue.put((char_name, thought))
                            
                time.sleep(1)
            except Exception as e:
                print(f"Error preloading thoughts: {e}")
                time.sleep(5)
    
    def _generate_hidden_thought(self, character: Any) -> Optional[str]:
        """Generate a hidden thought for a character.
        
        Args:
            character: Character instance to generate thought for
            
        Returns:
            Optional[str]: Generated thought string or None if generation fails
        """
        try:
            chain = CHARACTER_THOUGHT_PROMPT | self.llm
            recent_history = self._format_recent_history(2)
            
            response = chain.invoke({
                "name": character.config.name,
                "personality": self._format_character_traits(character),
                "motive": character.config.hidden_motive,
                "scene": self.narrator.current_scene,
                "history": recent_history
            }).content.strip()
            return response
        except Exception as e:
            print(f"Error generating thought: {e}")
            return None
    
    def _format_character_traits(self, character: Any) -> str:
        """Format character traits for prompts.
        
        Args:
            character: Character instance to format traits for
            
        Returns:
            str: Formatted string of character traits and values
        """
        return ", ".join([
            f"{k}: {v:.1f}" 
            for k, v in character.config.personality.items()
        ])
    
    def _format_recent_history(self, count: int = 3) -> str:
        """Format recent conversation history.
        
        Args:
            count: Number of recent events to include
            
        Returns:
            str: Formatted string of recent conversation events
        """
        recent = self.conversation_history[-count:] if self.conversation_history else []
        return "\n".join([
            f"{event.speaker} to {event.target}: {event.message}"
            for event in recent
        ])
    
    def _get_flow_response(self, last_speaker: str, last_message: str, history: str) -> str:
        """Get the next interaction flow from the LLM.
        
        Args:
            last_speaker: Name of the most recent speaker
            last_message: Content of the most recent message
            history: Formatted conversation history
            
        Returns:
            str: LLM response string determining next interaction
        """
        response = self.chain.invoke({
            "scene": self.narrator.current_scene,
            "characters": self.format_characters_info(),
            "last_speaker": last_speaker,
            "last_message": last_message,
            "history": history
        }).content.strip()
        
        return self._clean_json_response(response)
    
    def _clean_json_response(self, response: str) -> str:
        """Clean LLM response to ensure valid JSON.
        
        Args:
            response: Raw LLM response string
            
        Returns:
            str: Cleaned JSON string
            
        Raises:
            Exception: If JSON cleaning/parsing fails
        """
        try:
            # Remove any markdown code blocks
            response = response.strip()
            if response.startswith('```json'):
                response = response.split('```json')[1]
            if response.startswith('```'):
                response = response.split('```')[1]
            if response.endswith('```'):
                response = response.rsplit('```', 1)[0]
            
            # Clean up common JSON formatting issues
            response = response.strip()
            response = response.replace('\n', ' ')
            response = response.replace('\\n', ' ')
            response = response.replace('\\', '')
            
            # Remove any trailing commas before closing braces/brackets
            response = response.replace(',}', '}')
            response = response.replace(',]', ']')
            
            # Validate JSON structure
            json.loads(response)  # Test if it's valid JSON
            return response
            
        except Exception as e:
            print(f"Error cleaning JSON response: {e}")
            print(f"Original response: {response}")
            raise
    
    def _parse_flow_response(self, response: str) -> Dict[str, str]:
        """Parse the LLM's flow response into structured data.
        
        Args:
            response: JSON response string from LLM
            
        Returns:
            Dict[str, str]: Dictionary containing parsed response data
            
        Raises:
            ValueError: If response is missing required keys
        """
        try:
            result = json.loads(response)
            required_keys = {"next_speaker", "target", "reasoning"}
            if not all(key in result for key in required_keys):
                raise ValueError("Missing required keys in response")
            return result
        except (json.JSONDecodeError, ValueError) as e:
            print(f"Error parsing flow response: {e}")
            raise
    
    def _update_conversation_history(self, speaker: str, target: str, message: str) -> None:
        """Update the conversation history with new event.
        
        Args:
            speaker: Name of the speaking character
            target: Name of the character being spoken to
            message: Content of the message
        """
        self.conversation_history.append(ConversationEvent(
            speaker=speaker,
            target=target,
            message=message
        ))
        
        # Keep only recent history
        if len(self.conversation_history) > self.MAX_HISTORY_LENGTH:
            self.conversation_history = self.conversation_history[-self.MAX_HISTORY_LENGTH:]
    
    def _process_character_response(self, char_name: str, message: str, target: str) -> None:
        """Process a character's response in the thread pool.
        
        Args:
            char_name: Name of the character responding
            message: Message being responded to
            target: Target of the response
        """
        try:
            # Check recent responses for similar topics
            recent_events = self.conversation_history[-3:] if self.conversation_history else []
            similar_topics = any(
                event.speaker != char_name and
                self._check_similar_topics(message, event.message)
                for event in recent_events
            )
            
            # If similar topics found, add context to encourage a different perspective
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
            print(f"Error processing character response: {e}")
    
    def _check_similar_topics(self, msg1: str, msg2: str) -> bool:
        """Check if two messages discuss similar topics.
        
        Args:
            msg1: First message to compare
            msg2: Second message to compare
            
        Returns:
            bool: True if messages contain similar topics
        """
        # Add keywords for different topics your characters might discuss
        topic_keywords = {
            "mystery": ["journal", "key", "symbols", "passage", "chamber", "secret"],
            "investigation": ["found", "discovered", "search", "look", "examine"],
            "speculation": ["think", "believe", "suspect", "perhaps", "maybe"],
            # Add more topic categories as needed
        }
        
        msg1_lower = msg1.lower()
        msg2_lower = msg2.lower()
        
        for keywords in topic_keywords.values():
            # If both messages contain keywords from the same topic
            if (any(word in msg1_lower for word in keywords) and 
                any(word in msg2_lower for word in keywords)):
                return True
        
        return False
    
    def _get_fallback_interaction(self, last_speaker: str) -> Tuple[str, str, str]:
        """Provide fallback interaction if normal flow fails.
        
        Args:
            last_speaker: Name of the most recent speaker
            
        Returns:
            Tuple[str, str, str]: Tuple of (next_speaker, target, reasoning)
        """
        if last_speaker.lower() == "user":
            # Ensure a character responds to the user
            char_name = next(iter(self.characters.keys()))
            return (
                char_name,
                "User",
                "Responding to user's message"
            )
        else:
            # Encourage user participation
            return (
                "user",
                next(iter(self.characters.keys())),
                "Awaiting user's response"
            )
    
    def format_characters_info(self) -> str:
        """Format character information for prompts.
        
        Returns:
            str: Formatted string containing all character information
        """
        return "\n".join(
            f"{name} - {self._format_character_traits(char)}"
            for name, char in self.characters.items()
        )
    
    def _is_question_to_user(self, message: str, target: str) -> bool:
        """Check if the message is a question or prompt directed at the user.
        
        Args:
            message: The message content to check
            target: The target of the message
            
        Returns:
            bool: True if the message appears to be a question for the user
        """
        # Check if message is directed at user
        if target.lower() != "user":
            return False
        
        # Common question indicators
        question_indicators = [
            "?", "what", "how", "why", "where", "when", "who", "which",
            "could you", "would you", "will you", "can you", "do you"
        ]
        
        message_lower = message.lower()
        return any(indicator in message_lower for indicator in question_indicators)
    
    def determine_next_interaction(self, last_speaker: str, last_message: str) -> Tuple[str, str, str]:
        """Determine the next interaction in the conversation flow.
        
        Args:
            last_speaker: Name of the most recent speaker
            last_message: Content of the most recent message
            
        Returns:
            Tuple[str, str, str]: Tuple of (next_speaker, target, reasoning)
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
            
            return next_speaker, target, reasoning
            
        except Exception as e:
            print(f"Error in orchestrator: {e}")
            return self._get_fallback_interaction(last_speaker)
    
    def get_initial_character_response(self) -> str:
        """Generate initial character response after scene is set.
        
        Returns:
            str: Initial character response
        """
        try:
            # Pick a random character to speak first
            initial_speaker = random.choice(list(self.characters.keys()))
            char = self.characters[initial_speaker]
            
            # Generate response to scene setup
            response = char.respond_to(
                "SCENE_START",  # Special signal
                "ALL",  # Speaking to everyone
                {"scene": self.narrator.current_scene}
            )
            
            # Update conversation history
            self._update_conversation_history(initial_speaker, "ALL", response)
            return response
            
        except Exception as e:
            print(f"Error generating initial response: {e}")
            return f"[{list(self.characters.keys())[0]}]: *looks around curiously*"