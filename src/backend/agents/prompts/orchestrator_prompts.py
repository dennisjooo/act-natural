from langchain.prompts import PromptTemplate

ORCHESTRATOR_FLOW_TEMPLATE = """
As an orchestrator in an interactive play, manage the conversation flow naturally.

Current scene: {scene}
Available characters and their traits:
{characters}

Last speaker: {last_speaker}
Last message: "{last_message}"

Recent conversation history:
{history}

Important rules:
1. When the user speaks, at least one character should respond directly to them
2. Characters should actively engage with each other, not just with the user
3. Characters should react to each other's statements and emotions
4. If a character asks the user a question, set next_speaker as "user"
5. Characters should sometimes disagree or have conflicting viewpoints based on their personalities
6. Keep the conversation dynamic with a mix of user interaction and character-to-character dialogue

Return ONLY a JSON object in this exact format:
{{
    "next_speaker": "name",
    "target": "name",
    "reasoning": "brief explanation"
}}
"""

ORCHESTRATOR_FLOW_PROMPT = PromptTemplate(
    input_variables=["scene", "characters", "last_speaker", "last_message", "history"],
    template=ORCHESTRATOR_FLOW_TEMPLATE
) 