import streamlit as st

def initialize_scenario(scene_description: str = None) -> None:
    """Initialize a new scenario with either random or custom scene description.
    
    Args:
        scene_description: Optional custom scenario description. If None, generates random.
    """
    try:
        st.session_state.started = True
        st.session_state.info_saved = False
        st.session_state.messages = []
        
        play_manager = st.session_state.play_manager
        play_manager.user_name = st.session_state.user_name
        play_manager.user_description = st.session_state.user_description
        
        # For custom scenarios, append to user description
        if scene_description:
            play_manager.user_description += f"\n\nDesired scenario: {scene_description}"
            
        # Generate the scenario
        generated_scene = play_manager.generate_scenario()
        st.session_state.scene_description = generated_scene
        
        # Start the play with initial responses
        initial_response = play_manager.start_play(
            generated_scene,
            num_characters=st.session_state.num_characters,
            user_name=st.session_state.user_name,
            user_description=st.session_state.user_description
        )
        st.session_state.messages.append(("assistant", initial_response))
        
        # Get initial character response
        initial_char_response = play_manager.orchestrator.get_initial_character_response()
        st.session_state.messages.append(("assistant", initial_char_response))
        
    except Exception as e:
        st.error(f"Error generating scenario: {str(e)}")
        st.session_state.error_log.append(str(e))
        st.session_state.started = False

def generate_random_scenario():
    """Callback function for random scenario generation."""
    initialize_scenario()

def handle_custom_form_submit(custom_scenario: str, form_placeholder) -> None:
    """Handle the submission of custom scenario form.
    
    Args:
        custom_scenario: The user-provided scenario description
        form_placeholder: Streamlit container to clear after submission
    """
    if custom_scenario:
        st.session_state.show_custom_form = False
        form_placeholder.empty()
        initialize_scenario(custom_scenario)

def start_custom_scenario():
    """Callback function for custom scenario initialization.
    
    Side Effects:
        Sets show_custom_form session state to True to display custom scenario form
    """
    st.session_state.show_custom_form = True

def display_scenario_buttons() -> None:
    """Display and handle scenario generation buttons.
    
    Creates a two-column layout with buttons for:
    - Generating a random scenario
    - Opening the custom scenario input form
    
    Side Effects:
        Displays two buttons in the Streamlit UI that trigger respective callback functions
        when clicked
    """
    # Main content
    col1, col2 = st.columns(2)
    
    with col1:
        st.button(
            "Generate Random Scenario",
            on_click=generate_random_scenario,
            key="random_scenario",
            use_container_width=True
        )
    
    with col2:
        st.button(
            "Input Custom Scenario",
            on_click=start_custom_scenario,
            key="custom_scenario",
            use_container_width=True
        )

def display_custom_form() -> None:
    """Display the custom scenario form in a container at the bottom.
    
    Creates a form with:
    - Text area for scenario description
    - Start button to submit form
    - Cancel button to close form
    
    Side Effects:
        - Displays form in Streamlit UI
        - On submit: Handles custom scenario submission
        - On cancel: Hides form and clears placeholder
    """
    form_placeholder = st.empty()
    
    with form_placeholder.container():
        with st.form("custom_scenario_form"):
            custom_scenario = st.text_area(
                "Describe your scenario",
                placeholder="Describe the setting, situation, and atmosphere you'd like to play in...",
                height=150,
                label_visibility="collapsed"
            )
            
            col1, col2 = st.columns([1, 1])
            with col1:
                submit_button = st.form_submit_button("Start", use_container_width=True)
            with col2:
                cancel_button = st.form_submit_button("Cancel", use_container_width=True)
            
            if cancel_button:
                st.session_state.show_custom_form = False
                form_placeholder.empty()
            
            if submit_button:
                handle_custom_form_submit(custom_scenario, form_placeholder)