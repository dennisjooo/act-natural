import streamlit as st

def setup_page_config() -> None:
    """Setup page configuration including title, favicon, and layout settings.
    
    Configures the Streamlit page with:
    - Title: "Interactive Play Generator"
    - Favicon: Theater masks emoji
    - Layout: Wide mode for better content display
    - Sidebar: Auto-collapsed state
    
    Side Effects:
        Modifies the Streamlit page configuration using st.set_page_config()
    """
    st.set_page_config(
        page_title="Interactive Play Generator",
        page_icon="🎭",
        initial_sidebar_state="auto"
    ) 