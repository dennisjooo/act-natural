import re
import time
import streamlit as st
from dotenv import load_dotenv
from play_manager import PlayManager
from typing import List, Tuple, Generator, Optional

load_dotenv()

def extract_character_name(message: str) -> Optional[str]:
    """Extract character name from message if it starts with [Character Name]:
    
    Args:
        message: The message text to extract character name from
        
    Returns:
        The extracted character name if found, None otherwise
    """
    match = re.match(r'\[(.*?)\]:', message)
    if match:
        return match.group(1)
    return None

def get_avatar_emoji(character_name: Optional[str]) -> str:
    """Return an emoji avatar based on character name or stored emoji
    
    Args:
        character_name: Name of the character to get avatar for
        
    Returns:
        An emoji string representing the character's avatar
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
    """Display message with character-specific styling in markdown format
    
    Args:
        role: The role of the message sender (user/assistant)
        content: The message content to display
    """
    character_name = extract_character_name(content)
    
    if character_name:
        # Remove the character name prefix and any emoji from the message
        message_content = content.split(":", 1)[1].strip()
        
        with st.chat_message(role, avatar=get_avatar_emoji(character_name)):
            # Format the message in markdown with emoji and line break
            formatted_message = f"**{character_name}**<br>{message_content}"
            st.markdown(formatted_message, unsafe_allow_html=True)
    else:
        # Handle user messages
        with st.chat_message(role, avatar="🧑" if role == "user" else "🤖"):
            st.markdown(content)

def init_session_state() -> None:
    """Initialize session state variables"""
    if 'play_manager' not in st.session_state:
        st.session_state.play_manager = PlayManager()
    if 'messages' not in st.session_state:
        st.session_state.messages = []
    if 'started' not in st.session_state:
        st.session_state.started = False
    if 'error_log' not in st.session_state:
        st.session_state.error_log = []

def process_responses(responses: List[str]) -> Generator[Tuple[str, str], None, None]:
    """Process responses and yield messages to add
    
    Args:
        responses: List of response strings to process
        
    Yields:
        Tuples of (role, content) for each processed message
    """
    for response in responses:
        if response.startswith("PAUSE:"):
            time.sleep(float(response.split(":")[1]))
            continue
        yield ("assistant", response)

def main() -> None:
    """Main application entry point"""
    st.title("Interactive Play Generator")
    
    # Add custom CSS
    st.markdown("""
        <style>
        .stChatMessage {
            margin-bottom: 1rem;
        }
        .stChatMessage .content p {
            margin-bottom: 0.2rem;
        }
        </style>
    """, unsafe_allow_html=True)
    
    # Initialize session state
    init_session_state()
    
    if not st.session_state.started:
        st.write("Welcome to the Interactive Play Generator! Let's create a scene together.")
        
        col1, col2 = st.columns(2)
        with col1:
            if st.button("Generate Random Scenario"):
                try:
                    scene_description = st.session_state.play_manager.generate_scenario()
                    st.session_state.messages = []
                    initial_response = st.session_state.play_manager.start_play(scene_description, num_characters=4)
                    st.session_state.messages.append(("assistant", initial_response))
                    st.session_state.started = True
                    st.rerun()
                except Exception as e:
                    st.error(f"Error generating scenario: {str(e)}")
                    st.session_state.error_log.append(str(e))
        with col2:
            if st.button("Input Custom Scenario"):
                st.session_state.custom_input = True
                st.session_state.started = True
        
        if getattr(st.session_state, 'custom_input', False):
            scene_description = st.text_area("Describe the scene and situation for your play:")
            if st.button("Start Play"):
                if scene_description:
                    st.session_state.messages = []
                    initial_response = st.session_state.play_manager.start_play(scene_description)
                    st.session_state.messages.append(("assistant", initial_response))
                    st.session_state.custom_input = False
                    st.rerun()
    
    else:
        # Display message history
        for role, content in st.session_state.messages:
            display_message(role, content)
        
        # Chat input
        if prompt := st.chat_input("Your response"):
            # Display user message
            display_message("user", prompt)
            st.session_state.messages.append(("user", prompt))
            
            # Create a container for new messages
            message_container = st.container()
            
            # Process and display responses as they come in
            responses = st.session_state.play_manager.process_input(prompt)
            
            for role, content in process_responses(responses):
                with message_container:
                    display_message(role, content)
                st.session_state.messages.append((role, content))
                # Small delay for visual feedback
                time.sleep(0.1)
            
            # Rerun after all messages are processed
            st.rerun()
        
        # Add a reset button
        if st.sidebar.button("Reset Play"):
            st.session_state.play_manager.cleanup()
            st.session_state.clear()
            st.rerun()

    # Add debug information in sidebar if there are errors
    if st.session_state.error_log:
        with st.sidebar.expander("Debug Information"):
            for error in st.session_state.error_log:
                st.write(error)

if __name__ == "__main__":
    main()