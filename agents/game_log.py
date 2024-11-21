import json
from datetime import datetime
from pathlib import Path
from typing import Dict, Any

class GameLog:
    """Manages logging of game events, character interactions, and hidden information.
    
    This class handles logging various aspects of gameplay including scene descriptions,
    character information, and timestamped events. All data is saved to a JSON file.
    
    Attributes:
        log_dir (Path): Directory where log files are stored
        log_file (Path): Path to the specific log file for this session
        game_log (Dict): Dictionary containing all logged data
    """
    
    def __init__(self, log_dir: str = "logs") -> None:
        """Initialize the game logger.
        
        Creates a new log file with a unique timestamp and initializes the basic
        log structure.
        
        Args:
            log_dir (str): Directory path where log files should be stored. Defaults to "logs".
        
        Side Effects:
            - Creates log directory if it doesn't exist
            - Creates new log file with timestamp
            - Initializes game_log dictionary structure
        """
        self.log_dir = Path(log_dir)
        self.log_dir.mkdir(exist_ok=True)
        
        # Create unique log file for this session
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        self.log_file = self.log_dir / f"game_log_{timestamp}.json"
        
        # Initialize log structure
        self.game_log = {
            "session_start": timestamp,
            "scene": None,
            "characters": {},
            "events": []
        }
        
    def set_scene(self, scene_description: str) -> None:
        """Log the initial scene description for the game session.
        
        Args:
            scene_description (str): The narrative description of the game scene
            
        Side Effects:
            Updates the scene field in game_log and saves to file
        """
        self.game_log["scene"] = scene_description
        self._save_log()
        
    def add_character(self, name: str, config: Dict[str, Any]) -> None:
        """Log detailed information about a character including their hidden motives.
        
        Args:
            name (str): The character's name
            config (Dict[str, Any]): Character configuration including description,
                                   personality, hidden motives, and background
                                   
        Side Effects:
            Adds character data to game_log and saves to file
        """
        self.game_log["characters"][name] = {
            "description": config.get("description"),
            "personality": config.get("personality"),
            "hidden_motive": config.get("hidden_motive"),
            "background": config.get("background"),
            "gender": config.get("gender"),
            "emoji": config.get("emoji"),
            "role_in_scene": config.get("role_in_scene"),
            "relation_to_user": config.get("relation_to_user")
        }
        self._save_log()
        
    def log_event(self, event_type: str, data: Dict[str, Any]) -> None:
        """Log a timestamped game event.
        
        Args:
            event_type (str): Category of event (e.g., "dialogue", "action")
            data (Dict[str, Any]): Event-specific data to be logged
            
        Side Effects:
            Appends event to game_log events list and saves to file
        """
        event_entry = {
            "timestamp": datetime.now().isoformat(),
            "type": event_type,
            **data
        }
        self.game_log["events"].append(event_entry)
        self._save_log()
        
    def _save_log(self) -> None:
        """Save the current game_log to the JSON file.
        
        Side Effects:
            Writes current game_log dictionary to log_file in JSON format
        """
        with open(self.log_file, 'w', encoding='utf-8') as f:
            json.dump(self.game_log, f, indent=2, ensure_ascii=False) 