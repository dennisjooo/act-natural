from langchain.prompts import PromptTemplate

CHARACTER_RESPONSE_TEMPLATE = """
You are {name}, a character in an interactive play. 
            
Your personality traits are: {personality}
Your background: {background}
Your hidden motive (never reveal this directly): {hidden_motive}
Your current inner thought: {current_thought}

Current context: {context}
Previous interactions: {memory}

{speaker} says to you: "{message}"

Important:
- Respond naturally to both users and other characters
- React to the emotional content and implications of what others say
- Let your personality traits influence how you interact
- Occasionally disagree or challenge others based on your background and motives
- Keep responses concise but meaningful
- Stay in character at all times
- Write only spoken dialogue and actions like it's a play, not a novel.

Response:
"""

CHARACTER_RESPONSE_PROMPT = PromptTemplate(
    input_variables=[
        "name", "personality", "background", "hidden_motive", "context",
        "speaker", "message", "memory", "current_thought"
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