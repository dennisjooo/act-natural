import json
import os
import random
import time
import threading
from dataclasses import dataclass
from concurrent.futures import ThreadPoolExecutor
from langchain_groq import ChatGroq
from typing import Dict, Tuple, Optional, List
from queue import Queue

from .prompts import (
    ORCHESTRATOR_FLOW_PROMPT,
    CHARACTER_THOUGHT_PROMPT
)

@dataclass
class ConversationEvent:
    """Represents a single conversation interaction between characters.
    
    Attributes:
        speaker: The name of the character speaking
        target: The name of the character being spoken to
        message: The content of the message
        timestamp: Unix timestamp of when the message was sent
    """
    speaker: str
    target: str 
    message: str
    timestamp: float = time.time()

class Orchestrator:
    """Manages conversation flow between characters and users.
    
    Handles character interactions, conversation history, and thought generation.
    Uses LLM to determine conversation flow and character responses.
    
    Attributes:
        characters: Dictionary mapping character names to Character objects
        narrator: Narrator instance for scene management
        conversation_history: List of recent ConversationEvents
        last_user_interaction: Timestamp of most recent user message
        thoughts_queue: Queue for preloaded character thoughts
    """
    
    def __init__(self, characters: Dict, narrator) -> None:
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
        self.last_user_interaction: float = time.time()
        
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
            model_name="gemma2-9b-it",
            temperature=0.25
        )
    
    def _should_initiate_conversation(self) -> bool:
        """Determine if characters should initiate conversation.
        
        Returns:
            bool: True if enough time has passed and random chance succeeds
        """
        time_since_user = time.time() - self.last_user_interaction
        return (
            time_since_user > 45 and  # Increased from 30 to 45 seconds
            random.random() < 0.2     # Reduced from 0.3 to 0.2 (20% chance)
        )
    
    def _get_active_characters(self, exclude: Optional[List[str]] = None) -> List[str]:
        """Get list of characters who haven't spoken recently.
        
        Args:
            exclude: Optional list of character names to exclude
            
        Returns:
            List of character names who are eligible to speak
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
                for char_name, char in self.characters.items():
                    if self.thoughts_queue.qsize() < len(self.characters) * 2:
                        thought = self._generate_hidden_thought(char)
                        if thought:
                            self.thoughts_queue.put((char_name, thought))
                time.sleep(1)
            except Exception as e:
                print(f"Error preloading thoughts: {e}")
                time.sleep(5)
    
    def _generate_hidden_thought(self, character) -> Optional[str]:
        """Generate a hidden thought for a character.
        
        Args:
            character: Character instance to generate thought for
            
        Returns:
            Generated thought string or None if generation fails
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
    
    def _format_character_traits(self, character) -> str:
        """Format character traits for prompts.
        
        Args:
            character: Character instance to format traits for
            
        Returns:
            Formatted string of character traits and values
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
            Formatted string of recent conversation events
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
            LLM response string determining next interaction
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
            Cleaned JSON string
            
        Raises:
            Exception if JSON cleaning/parsing fails
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
    
    def _parse_flow_response(self, response: str) -> Dict:
        """Parse the LLM's flow response into structured data.
        
        Args:
            response: JSON response string from LLM
            
        Returns:
            Dictionary containing parsed response data
            
        Raises:
            ValueError if response is missing required keys
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
        if len(self.conversation_history) > 10:
            self.conversation_history = self.conversation_history[-10:]
    
    def _process_character_response(self, char_name: str, message: str, target: str) -> None:
        """Process a character's response in the thread pool.
        
        Args:
            char_name: Name of the responding character
            message: Message being responded to
            target: Name of character being responded to
        """
        try:
            self.executor.submit(
                self.characters[char_name].respond_to,
                message,
                target,
                {"scene": self.narrator.current_scene}
            )
        except Exception as e:
            print(f"Error processing character response: {e}")
    
    def _get_fallback_interaction(self, last_speaker: str) -> Tuple[str, str, str]:
        """Provide fallback interaction if normal flow fails.
        
        Args:
            last_speaker: Name of the most recent speaker
            
        Returns:
            Tuple of (next_speaker, target, reasoning)
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
            Formatted string containing all character information
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
        """Determine the next interaction in the conversation flow."""
        try:
            if last_speaker == "User":
                self.last_user_interaction = time.time()
            
            # Check if the last message was a question to the user
            last_event = self.conversation_history[-1] if self.conversation_history else None
            if last_event and self._is_question_to_user(last_event.message, last_event.target):
                # Strongly prefer user response after being asked a question
                if random.random() < 0.9:  # 90% chance to wait for user
                    return "user", last_speaker, "Responding to direct question"
            
            # Rest of the existing conversation initiation logic
            if self._should_initiate_conversation():
                active_chars = self._get_active_characters()
                if active_chars:
                    initiator = random.choice(active_chars)
                    # Increase chance of targeting user when initiating
                    if random.random() < 0.6:  # 60% chance to target user
                        target = "User"
                    else:
                        target = random.choice([
                            name for name in self.characters.keys()
                            if name != initiator
                        ])
                    return (
                        initiator,
                        target,
                        "Initiating new conversation thread"
                    )
            
            # Normal flow determination with modified logic
            recent_history = self._format_recent_history()
            response = self._get_flow_response(last_speaker, last_message, recent_history)
            result = self._parse_flow_response(response)
            
            # If LLM suggests a character speak after a question to user,
            # override to prefer user response
            if (last_event and 
                self._is_question_to_user(last_event.message, last_event.target) and
                result["next_speaker"] != "user" and 
                random.random() < 0.8):  # 80% chance to override
                result["next_speaker"] = "user"
                result["target"] = last_speaker
                result["reasoning"] = "Waiting for user's response to question"
            
            # Rest of the existing logic...
            self._update_conversation_history(last_speaker, result["target"], last_message)
            
            if result["next_speaker"] in self.characters and result["next_speaker"] != "user":
                self._process_character_response(
                    result["next_speaker"],
                    last_message,
                    result["target"]
                )
            
            return result["next_speaker"], result["target"], result["reasoning"]
            
        except Exception as e:
            print(f"Error in orchestrator: {e}")
            return self._get_fallback_interaction(last_speaker)