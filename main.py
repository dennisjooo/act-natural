import logging
import time
import streamlit as st
from dotenv import load_dotenv
from src.backend import PlayManager
from typing import List, Tuple, Generator

from src.frontend import *

load_dotenv()

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

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
    if 'info_saved' not in st.session_state:
        st.session_state.info_saved = False

def process_responses(responses: List[str]) -> Generator[Tuple[str, str], None, None]:
    """Process responses and yield messages to add"""
    for response in responses:
        if response.startswith("PAUSE:"):
            time.sleep(float(response.split(":")[1]))
            continue
        yield ("assistant", response)

def main() -> None:
    """Main application entry point"""
    setup_page_config()
    
    st.title("🎭 Act Natural")
    
    init_session_state()
    apply_custom_styles()
    
    if st.session_state.started and hasattr(st.session_state, 'play_manager'):
        display_sidebar()
    
    if not st.session_state.started:
        if display_user_setup() and st.session_state.get('info_saved', False):
            display_scenario_buttons()
    
    else:
        # Display message history
        for role, content in st.session_state.messages:
            display_message(role, content)
        
        # Chat input
        if prompt := st.chat_input("Your response"):
            display_message("user", prompt)
            st.session_state.messages.append(("user", prompt))
            
            message_container = st.container()
            responses = st.session_state.play_manager.process_input(prompt)
            
            for role, content in process_responses(responses):
                with message_container:
                    display_message(role, content)
                st.session_state.messages.append((role, content))
                time.sleep(0.1)
            
            st.rerun()
    
    # Display custom form at the end if needed
    if st.session_state.get('show_custom_form', False):
        display_custom_form()
    
    # Add debug information in sidebar if there are errors
    if st.session_state.error_log:
        with st.sidebar.expander("Debug Information"):
            for error in st.session_state.error_log:
                st.write(error)
                
if __name__ == "__main__":
    main()