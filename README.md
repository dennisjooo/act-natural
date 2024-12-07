# 🎭 Act Natural

*Because teaching AI to act is exactly as chaotic as it sounds*

## What is this?

Act Natural is an interactive theatre experience where AI characters try (and sometimes hilariously fail) to act natural. Using Groq's LLMs and some questionable decision-making, we've created a space where:

- AI characters improvise scenes with hidden motives
- A narrator occasionally chimes in with dramatic flair
- You get to participate in whatever chaos unfolds

Basically I'm trying to figure out how to create an agentic system that orchestrates together to user inputs.
Making the agents "act in a play" is just a fun way to explore this and to kill time at work.

## Features

- 🎬 **Random Scenario Generation**: Get thrown into completely unexpected situations
- 🎭 **Dynamic Characters**: Each with their own personality traits, backgrounds, and secret agendas
- 📜 **Atmospheric Narration**: A narrator who tries their best to set the mood
- 🤔 **Hidden Thoughts**: Characters maintain internal monologues you'll never see (probably for the best)
- 🎯 **Hidden Motives**: Every character has a secret agenda (just like real theater!)

## Quick Start

1. Clone this repository

2. Install dependencies:

```bash
pip install -r requirements.txt
```

3. Set up your environment variables:

```bash
GROQ_API_KEY=your_api_key_here
CHARACTER_MODEL=your_character_model_here
ORCHESTRATOR_MODEL=your_orchestrator_model_here
SCENARIO_MODEL=your_scenario_model_here
```

4. Run the application:

```bash
streamlit run main.py
```

## How it Works

The system uses several key components (that occasionally cooperate):

- **Play Manager**: The director trying to keep everything from falling apart
- **Characters**: AI actors doing their best to stay in character
- **Narrator**: Adds dramatic flair when things get interesting
- **Orchestrator**: Makes sure characters actually talk to each other

## Technical Notes and Ideas

- Using Groq's LLMs (Gemma 2 9B for the characters and Llama 3.3 70B for scenario generation and orchestrator)
- Highly recommend using more powerful models for the orchestrator
- Langchain is used to manage the conversation history and to keep track of the characters' internal monologues
- Would be fun to add a vector database to keep track of the characters' memories, or even better, a graph database
- Also fun to add dice rolls and other randomness to the character's actions (ala D&D), that being said the current
  implementation is pretty janky and could use some work.
