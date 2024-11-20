import streamlit as st

def apply_custom_styles() -> None:
    """Apply custom CSS styles to the application.
    
    Applies custom styling to:
    - Chat messages: Adds bottom margin and adjusts paragraph spacing
    - Sidebar character descriptions: Sets smaller, muted text style
    
    Side Effects:
        Injects custom CSS into the Streamlit app using st.markdown()
    """
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