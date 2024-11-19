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
    if 'user_name' not in st.session_state:
        st.session_state.user_name = "Anonymous Player"
    if 'user_description' not in st.session_state:
        st.session_state.user_description = "A curious participant in this interactive story"

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
    
    # Initialize session state
    init_session_state()
    
    # Add character tracker to sidebar when play has started
    if st.session_state.started and hasattr(st.session_state, 'play_manager'):
        with st.sidebar:
            st.subheader("Characters in Scene")
            
            # Display user first
            st.markdown(f"**{get_avatar_emoji(None)} {st.session_state.user_name}** (You)")
            st.markdown(f"<small>{st.session_state.user_description}</small>", unsafe_allow_html=True)
            
            st.markdown("---")
            
            # Display scene context if available
            if hasattr(st.session_state.play_manager, 'scene_description'):
                with st.expander("Scene Context"):
                    st.markdown(f"<small>{st.session_state.play_manager.scene_description}</small>", 
                              unsafe_allow_html=True)
            
            # Display all other characters
            for char_name, char in st.session_state.play_manager.characters.items():
                emoji = get_avatar_emoji(char_name)
                st.markdown(f"**{emoji} {char_name}**")
                with st.expander("Background"):
                    if hasattr(char.config, 'description'):
                        st.markdown(f"<small>**Description:** {char.config.description}</small>", 
                                  unsafe_allow_html=True)
                    if hasattr(char.config, 'background'):
                        st.markdown(f"<small>**Background:** {char.config.background}</small>", 
                                  unsafe_allow_html=True)
                    if hasattr(char.config, 'personality'):
                        st.markdown("<small>**Personality Traits:**</small>", unsafe_allow_html=True)
                        # Handle personality traits as a dictionary
                        if isinstance(char.config.personality, dict):
                            for trait, value in char.config.personality.items():
                                # Convert trait from snake_case or camelCase to Title Case
                                formatted_trait = ' '.join(
                                    word.capitalize() 
                                    for word in trait.replace('_', ' ').split()
                                )
                                st.markdown(f"<small>• {formatted_trait}: {value}</small>", 
                                          unsafe_allow_html=True)
    
    # Add custom CSS
    st.markdown("""
        <style>
        .stChatMessage {
            margin-bottom: 1rem;
        }
        .stChatMessage .content p {
            margin-bottom: 0.2rem;
        }
        /* Add styling for character descriptions in sidebar */
        .sidebar small {
            color: #666;
            font-size: 0.85em;
        }
        </style>
    """, unsafe_allow_html=True)
    
    # Move reset button to top of page
    if st.session_state.started:
        if st.button("Reset Play"):
            st.session_state.play_manager.cleanup()
            st.session_state.clear()
            st.rerun()
    
    if not st.session_state.started:
        st.write("Welcome to the Interactive Play Generator! Let's create a scene together.")
        
        # Add user information inputs
        with st.form("user_info"):
            st.write("Tell us about yourself:")
            user_name = st.text_input(
                "Your Name", 
                value=st.session_state.user_name,
                placeholder="Enter your name or leave blank for 'Anonymous Player'"
            ).strip()
            user_description = st.text_area(
                "Brief Description of Yourself", 
                value=st.session_state.user_description,
                placeholder="Tell us a bit about yourself, or leave blank for default description",
                help="This will help the characters interact with you more naturally"
            ).strip()
            num_characters = st.slider("Number of Characters", min_value=2, max_value=6, value=4,
                                     help="How many characters would you like in your scene?")
            submit_user_info = st.form_submit_button("Save")
            
            if submit_user_info:
                # Use defaults if fields are empty
                st.session_state.user_name = user_name if user_name else "Anonymous Player"
                st.session_state.user_description = (
                    user_description if user_description 
                    else "A curious participant in this interactive story"
                )
                st.session_state.num_characters = num_characters
                st.success("Information saved!")
        
        col1, col2 = st.columns(2)
        with col1:
            if st.button("Generate Random Scenario"):
                if not st.session_state.user_name or not st.session_state.user_description:
                    st.error("Please fill in your name and description first!")
                else:
                    try:
                        scene_description = st.session_state.play_manager.generate_scenario()
                        st.session_state.messages = []
                        initial_response = st.session_state.play_manager.start_play(
                            scene_description, 
                            num_characters=st.session_state.get('num_characters', 4),
                            user_name=st.session_state.user_name,
                            user_description=st.session_state.user_description
                        )
                        st.session_state.messages.append(("assistant", initial_response))
                        st.session_state.started = True
                        st.rerun()
                    except Exception as e:
                        st.error(f"Error generating scenario: {str(e)}")
                        st.session_state.error_log.append(str(e))
        with col2:
            if st.button("Input Custom Scenario"):
                if not st.session_state.user_name or not st.session_state.user_description:
                    st.error("Please fill in your name and description first!")
                else:
                    st.session_state.custom_input = True
                    st.session_state.started = True
        
        if getattr(st.session_state, 'custom_input', False):
            scene_description = st.text_area("Describe the scene and situation for your play:")
            if st.button("Start Play"):
                if scene_description:
                    st.session_state.messages = []
                    initial_response = st.session_state.play_manager.start_play(
                        scene_description,
                        num_characters=st.session_state.get('num_characters', 4),
                        user_name=st.session_state.user_name,
                        user_description=st.session_state.user_description
                    )
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
        
    # Add debug information in sidebar if there are errors
    if st.session_state.error_log:
        with st.sidebar.expander("Debug Information"):
            for error in st.session_state.error_log:
                st.write(error)

if __name__ == "__main__":
    main()