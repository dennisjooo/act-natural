import streamlit as st
from .message_display import get_avatar_emoji

def display_sidebar() -> None:
    """Display the sidebar with character information and scene context.
    
    Renders a Streamlit sidebar containing:
    - User information (name and description)
    - Scene context if available
    - List of characters with their details including:
        - Description
        - Background
        - Personality traits
        
    The sidebar uses expanders to organize character information and
    custom styling for readable formatting.
    
    Side Effects:
        Modifies the Streamlit sidebar by adding various UI elements
        including markdown text, expanders, and subheaders.
    """
    with st.sidebar:
        # Add Reset Play button at the top of sidebar
        if st.button("Reset Play"):
            st.session_state.play_manager.cleanup()
            st.session_state.clear()
            st.rerun()
            
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
            with st.expander(f"**{emoji} {char_name}**"):
                if hasattr(char.config, 'description'):
                    st.markdown(f"<small>**Description:** {char.config.description}</small>", 
                              unsafe_allow_html=True)
                if hasattr(char.config, 'background'):
                    st.markdown(f"<small>**Background:** {char.config.background}</small>", 
                              unsafe_allow_html=True)
                if hasattr(char.config, 'personality'):
                    st.markdown("<small>**Personality Traits:**</small>", unsafe_allow_html=True)
                    if isinstance(char.config.personality, dict):
                        for trait, value in char.config.personality.items():
                            formatted_trait = ' '.join(
                                word.capitalize() 
                                for word in trait.replace('_', ' ').split()
                            )
                            st.markdown(f"<small>• {formatted_trait}: {value}</small>", 
                                      unsafe_allow_html=True)