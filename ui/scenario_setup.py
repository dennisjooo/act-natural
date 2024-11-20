import streamlit as st

def generate_random_scenario():
    """Callback function for random scenario generation.
    
    Generates a random interactive play scenario and initializes the play session.
    Sets up session state variables and generates initial responses from the play
    manager and characters.
    
    Handles any errors during generation by logging them and resetting the started state.
    
    Side Effects:
        - Sets multiple st.session_state variables including:
            started, info_saved, messages, scene_description
        - Displays error message if generation fails
        - Appends errors to error_log if they occur
    """
    try:
        # Set started flag first
        st.session_state.started = True
        st.session_state.info_saved = False
        st.session_state.messages = []
        
        # Generate the scenario
        scene_description = st.session_state.play_manager.generate_scenario()
        st.session_state.scene_description = scene_description
        
        # Start the play with initial responses
        initial_response = st.session_state.play_manager.start_play(
            scene_description, 
            num_characters=st.session_state.num_characters,
            user_name=st.session_state.user_name,
            user_description=st.session_state.user_description
        )
        st.session_state.messages.append(("assistant", initial_response))
        
        # Get initial character response
        initial_char_response = st.session_state.play_manager.orchestrator.get_initial_character_response()
        st.session_state.messages.append(("assistant", initial_char_response))
        
    except Exception as e:
        st.error(f"Error generating scenario: {str(e)}")
        st.session_state.error_log.append(str(e))
        st.session_state.started = False

def start_custom_scenario():
    """Callback function for custom scenario initialization.
    
    Prepares the session state for a custom scenario input by the user.
    Resets relevant session variables to their initial states.
    
    Side Effects:
        Sets the following st.session_state variables:
        - started: True to indicate play has begun
        - custom_input: True to indicate custom scenario mode
        - info_saved: False to reset saved state
        - messages: Empty list to store new messages
    """
    st.session_state.started = True
    st.session_state.custom_input = True
    st.session_state.info_saved = False
    st.session_state.messages = []

def display_scenario_buttons() -> None:
    """Display and handle scenario generation buttons.
    
    Creates a two-column layout with buttons for generating either a random
    scenario or starting a custom scenario input.
    
    Returns:
        None
        
    Side Effects:
        Displays two buttons in the Streamlit interface that trigger either
        generate_random_scenario() or start_custom_scenario() when clicked.
    """
    col1, col2 = st.columns(2)
    
    with col1:
        st.button(
            "Generate Random Scenario",
            on_click=generate_random_scenario,
            key="random_scenario"
        )
    
    with col2:
        st.button(
            "Input Custom Scenario",
            on_click=start_custom_scenario,
            key="custom_scenario"
        )