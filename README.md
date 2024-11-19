# 🎭 act-natural

*Because teaching AI to act is exactly as chaotic as it sounds*

## What is this?

act-natural is an interactive theater experience where AI characters try (and sometimes hilariously fail) to act natural. Using Groq's LLMs and some questionable decision-making, we've created a space where:

- AI characters improvise scenes with hidden motives
- A narrator occasionally chimes in with dramatic flair
- You get to participate in whatever chaos unfolds

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