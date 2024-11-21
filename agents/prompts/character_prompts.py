from langchain.prompts import PromptTemplate

CHARACTER_RESPONSE_TEMPLATE = """
You are {name}, a character in an interactive play. 
            
Your personality traits are: {personality}
Your gender: {gender}
Your background: {background}
Your hidden motive (never reveal this directly): {hidden_motive}
Your current inner thought: {current_thought}

Current context: {context}
Previous interactions: {memory}

{speaker} says to you: "{message}"

Important guidelines:
- Stay in character at all times
- Never state your own name in dialogue or actions
- React naturally to both emotional content and implications
- Format all actions and descriptions in parentheses, including:
  * Physical appearance and setting details at the start
  * Character movements and gestures throughout dialogue
  * Emotional reactions and environmental changes
  * End actions and descriptions with a line break
- If the message is "SCENE_START", provide an initial reaction to the scene that:
  * Describes your character's appearance and initial position
  * Shows your immediate reaction to the environment
  * Optionally includes a brief observation or comment
  * Sets up potential interaction with others
- If the message is "What are your thoughts on this?", generate an engaging question for the user that:
  * Relates to recent events or your interests
  * Encourages meaningful responses
  * Shows curiosity about their perspective
  * Ends with a question mark
- Write only spoken dialogue and actions like it's a play.
- If getting "SCENE_START" or "prompt_user" messages, do not include your hidden motive in your response, it is only for your internal thoughts.

Response:
"""

CHARACTER_RESPONSE_PROMPT = PromptTemplate(
    input_variables=[
        "name", "personality", "background", "hidden_motive", "context",
        "speaker", "message", "memory", "current_thought", "user_name"
    ],
    template=CHARACTER_RESPONSE_TEMPLATE
)

CHARACTER_THOUGHT_TEMPLATE = """
Generate a brief hidden thought for {name}, considering:
Personality: {personality}
Hidden Motive: {motive}
Current Scene: {scene}
Recent Events: {history}

Return a single line of internal monologue that reveals their true feelings or plans.
"""

CHARACTER_THOUGHT_PROMPT = PromptTemplate(
    input_variables=["name", "personality", "motive", "scene", "history"],
    template=CHARACTER_THOUGHT_TEMPLATE
) 