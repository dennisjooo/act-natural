from langchain.prompts import PromptTemplate

SCENARIO_GENERATION_TEMPLATE = """
Given a user with the following description:
User Name: {user_name}
User Description: {user_description}

Generate an interesting and dramatic scenario for an interactive play that would be engaging for this user. 
It needs to be captivating and should allow meaningful interaction with the user's character.

Return ONLY a JSON object in this exact format:
{{
    "setting": "description of the location",
    "situation": "description of what's happening",
    "atmosphere": "description of mood and environment",
    "character_context": "brief description of the types of characters that would be in this scenario",
    "user_role": "suggested role or position for the user character in this scenario"
}}
"""

SCENARIO_GENERATION_PROMPT = PromptTemplate(
    input_variables=["user_name", "user_description"],
    template=SCENARIO_GENERATION_TEMPLATE
)

CHARACTER_GENERATION_TEMPLATE = """Based on this scene description: {scene_description}

The user participating in this scene has the following profile:
Name: {user_name}
Description: {user_description}

Create exactly {num_characters} distinct characters that would make an interesting dynamic with this user.

Return ONLY a JSON object with this EXACT format (no additional text or formatting):
{{
    "characters": [
        {{
            "name": "string",
            "gender": "male/female/non-binary",
            "description": "physical appearance and notable features",
            "personality": {{"trait1": float_between_0_and_1, "trait2": float_between_0_and_1, 
            "trait3": float_between_0_and_1}},
            "background": "string",
            "hidden_motive": "string",
            "emoji": "🧔‍♂️",
            "role_in_scene": "character's current role or purpose in the scenario",
            "relation_to_user": "how this character relates to or views the user character"
        }}
    ]
}}

Rules:
- Each trait value must be a float between 0 and 1
- Gender must be exactly "male", "female", or "non-binary"
- Description should include physical appearance and distinguishing features
- Role in scene should explain why they are present in this scenario
- Relation to user should describe their initial attitude or connection to the user character
- No additional fields or text outside the JSON structure
- Exactly {num_characters} characters in the array
"""

CHARACTER_GENERATION_PROMPT = PromptTemplate(
    input_variables=["scene_description", "num_characters", "user_name", "user_description"],
    template=CHARACTER_GENERATION_TEMPLATE
) 