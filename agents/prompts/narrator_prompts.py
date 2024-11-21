from langchain.prompts import PromptTemplate

NARRATOR_OBSERVATION_TEMPLATE = """
As a subtle narrator in an interactive play, determine if this interaction needs atmospheric description
or context. Try and match the tone of the scene. Only provide narration if any of these conditions are met: 
1. There's a significant change in mood or atmosphere 
2. Important physical actions or movements occur 
3. Environmental changes need to be described 
4. Critical non-verbal cues need to be highlighted

Current scene: {current_scene} 
Interaction: {speaker} says to {listener}: "{message}"

If narration is needed, provide a brief, atmospheric description (2-3 sentences). 
If no narration is needed, respond with "SKIP". 

Response:
"""

NARRATOR_OBSERVATION_PROMPT = PromptTemplate(
    input_variables=["speaker", "listener", "message", "current_scene"],
    template=NARRATOR_OBSERVATION_TEMPLATE
) 