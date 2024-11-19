from langchain.prompts import PromptTemplate

SCENARIO_GENERATION_TEMPLATE = """
Generate an interesting and dramatic scenario for an interactive play. It needs to be captivating and fun for the user.
Be free and creative, but make sure it's realistic and coherent.

Return ONLY a JSON object in this exact format:
{{
    "setting": "description of the location",
    "situation": "description of what's happening",
    "atmosphere": "description of mood and environment"
}}
"""

SCENARIO_GENERATION_PROMPT = PromptTemplate(
    input_variables=[],
    template=SCENARIO_GENERATION_TEMPLATE
)

CHARACTER_GENERATION_TEMPLATE = """Based on this scene description: {scene_description}
Create exactly {num_characters} distinct characters that would make an interesting dynamic.

Return ONLY a JSON object with this EXACT format (no additional text or formatting):
{{
    "characters": [
        {{
            "name": "string",
            "gender": "male/female/non-binary",
            "personality": {{"trait1": float_between_0_and_1, "trait2": float_between_0_and_1, 
            "trait3": float_between_0_and_1}},
            "background": "string",
            "hidden_motive": "string",
            "emoji": "🧔‍♂️"
        }}
    ]
}}

Rules:
- Each trait value must be a float between 0 and 1
- Gender must be exactly "male", "female", or "non-binary"
- No additional fields or text outside the JSON structure
- Exactly {num_characters} characters in the array
"""

CHARACTER_GENERATION_PROMPT = PromptTemplate(
    input_variables=["scene_description", "num_characters"],
    template=CHARACTER_GENERATION_TEMPLATE
) 