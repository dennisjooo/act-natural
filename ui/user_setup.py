import streamlit as st

def display_user_setup() -> bool:
    """Display user setup form and handle user information input.
    
    Displays a Streamlit form allowing users to input:
    - Their name (optional, defaults to 'Anonymous Player')
    - A description of themselves (optional, defaults to generic description)
    - Number of characters they want in their scene (2-6)
    
    The form saves the user's information to session state when submitted.
    
    Returns:
        bool: True if form was submitted and info saved, False otherwise
        
    Side Effects:
        When form is submitted, sets the following session state variables:
        - user_name: User's input name or default
        - user_description: User's input description or default
        - num_characters: Selected number of characters
        - info_saved: True to indicate setup is complete
    """
    st.write("Welcome to the Interactive Play Generator! Let's create a scene together.")
    
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
            st.session_state.user_name = user_name if user_name else "Anonymous Player"
            st.session_state.user_description = (
                user_description if user_description 
                else "A curious participant in this interactive story"
            )
            st.session_state.num_characters = num_characters
            st.success("Information saved!")
            st.session_state.info_saved = True
            return True
    
    return False