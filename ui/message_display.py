import streamlit as st
import re
from typing import Optional

def extract_character_name(message: str) -> Optional[str]:
    """Extract character name from message if it starts with [Character Name]:
    
    Args:
        message (str): The message to extract character name from
        
    Returns:
        Optional[str]: The extracted character name if found, None otherwise
    """
    match = re.match(r'\[(.*?)\]:', message)
    if match:
        return match.group(1)
    return None

def get_avatar_emoji(character_name: Optional[str]) -> str:
    """Return an emoji avatar based on character name or stored emoji.
    
    Args:
        character_name (Optional[str]): Name of the character to get avatar for
        
    Returns:
        str: An emoji character to use as the avatar
    
    The function checks for special cases like Narrator and user (None),
    then looks up character-specific emojis from the play manager if available.
    Falls back to a default avatar if no specific emoji is found.
    """
    if character_name == "Narrator":
        return "📜"
    elif not character_name:
        return "🧑"  # Default for user
    
    # Use character's assigned emoji if available
    if hasattr(st.session_state, 'play_manager') and character_name in st.session_state.play_manager.characters:
        char = st.session_state.play_manager.characters[character_name]
        if hasattr(char.config, 'emoji') and char.config.emoji:
            return char.config.emoji
    
    return "👤"

def display_message(role: str, content: str) -> None:
    """Display message with character-specific styling in markdown format.
    
    Args:
        role (str): The role of the message sender ('user' or 'assistant')
        content (str): The message content to display
        
    The function handles two types of messages:
    1. Character messages in format "[Character Name]: message"
    2. Regular messages from user or system
    
    Messages are displayed with appropriate avatars and formatting using
    Streamlit's chat message components.
    """
    character_name = extract_character_name(content)
    
    if character_name:
        message_content = content.split(":", 1)[1].strip()
        
        with st.chat_message(role, avatar=get_avatar_emoji(character_name)):
            formatted_message = f"**{character_name}**<br>{message_content}"
            st.markdown(formatted_message, unsafe_allow_html=True)
    else:
        with st.chat_message(role, avatar="🧑" if role == "user" else "🤖"):
            st.markdown(content)