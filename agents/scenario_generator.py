import logging
import random
from langchain_groq import ChatGroq

from agents.prompts import SCENARIO_GENERATION_PROMPT
from utils import clean_json_response

class ScenarioGenerator:
    """Generates interactive scenarios with rich descriptions and character contexts.
    
    This class handles the generation of detailed scenarios using an LLM, creating
    immersive settings, situations and atmospheres that provide engaging contexts
    for interactive play experiences.
    
    Attributes:
        llm (ChatGroq): Language model instance used for scenario generation
    """

    def __init__(self, llm: ChatGroq):
        """Initialize the scenario generator.
        
        Args:
            llm (ChatGroq): Language model instance to use for generation
        """
        self.llm = llm

    def generate_scenario(self, user_name: str, user_description: str) -> tuple[str, str, str]:
        """Generate a complete scenario with setting, situation and character context.
        
        Creates an immersive scenario description along with appropriate character context
        and a specific role for the user character.
        
        Args:
            user_name (str): Name of the user's character
            user_description (str): Description of the user's character
            
        Returns:
            tuple[str, str, str]: A tuple containing:
                - scenario_description: Complete scene description
                - character_context: Context about expected character types
                - user_role: The user's specific role in the scenario
                
        Note:
            Falls back to predefined scenarios if generation fails
        """
        try:
            chain = SCENARIO_GENERATION_PROMPT | self.llm
            response = chain.invoke({
                "user_name": user_name,
                "user_description": user_description
            }).content
            
            scenario_data = clean_json_response(response)
            if not scenario_data:
                logging.error("Failed to parse scenario data, using fallback scenario")
                return self.get_fallback_scenario()
            
            scenario_description = (
                f"{scenario_data['setting']}. "
                f"{scenario_data['situation']} "
                f"{scenario_data['atmosphere']}\n\n"
                f"Your role: {scenario_data['user_role']}"
            )
            
            return (
                scenario_description,
                scenario_data.get('character_context', ''),
                scenario_data.get('user_role', '')
            )
        except Exception as e:
            logging.error(f"Error generating scenario: {e}")
            return self.get_fallback_scenario()

    def get_fallback_scenario(self) -> tuple[str, str, str]:
        """Get a predefined fallback scenario when generation fails.
        
        Randomly selects from a set of predefined scenarios to ensure the
        application can continue even if scenario generation fails.
        
        Returns:
            tuple[str, str, str]: A tuple containing:
                - scenario_description: Complete scene description
                - character_context: Context about expected character types
                - user_role: The user's specific role in the scenario
        """
        scenarios = [
            ("A mysterious tavern on a stormy night. Travelers from different walks of life have sought shelter here, each carrying their own secrets and stories. The atmosphere is tense with unspoken tales and hidden agendas.",
             "Travelers, innkeeper, mysterious stranger",
             "A curious traveler seeking shelter from the storm"),
            
            ("An abandoned mansion during a masquerade ball. The guests are trapped inside by a mysterious force, and everyone seems to have a hidden agenda. The air is thick with intrigue and suspicion.",
             "Noble guests, servants, mysterious host",
             "An invited guest at the masquerade"),
            
            ("A futuristic space station at the edge of known space. The station's systems are malfunctioning, and the diverse crew members each seem to know more than they're letting on. The metallic corridors echo with whispered conspiracies.",
             "Station crew, engineers, security personnel",
             "A newly arrived passenger with vital information")
        ]
        
        return random.choice(scenarios)