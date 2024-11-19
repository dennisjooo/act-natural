import json
import streamlit as st
from typing import Optional, Dict, Any

def clean_json_response(response_text: str) -> Optional[Dict[str, Any]]:
    """Clean and validate JSON response by handling common formatting issues.
    
    Args:
        response_text: Raw JSON string that may contain formatting issues
        
    Returns:
        Parsed JSON data as a dictionary if successful, None if parsing fails
        
    Example:
        >>> clean_json_response('{"key": "value"}')
        {'key': 'value'}
        >>> clean_json_response("{'key': 'value'}")
        {'key': 'value'}
        >>> clean_json_response("Invalid JSON")
        None
    """
    try:
        # First try direct JSON parsing
        return json.loads(response_text)
    except json.JSONDecodeError:
        try:
            # Try to clean up common JSON formatting issues
            # Remove any leading/trailing whitespace
            cleaned = response_text.strip()
            
            # Ensure proper quote usage
            cleaned = cleaned.replace('"', '"').replace('"', '"')
            
            # Replace any single quotes with double quotes for JSON compatibility
            cleaned = cleaned.replace("'", '"')
            
            # Try parsing again
            return json.loads(cleaned)
        except json.JSONDecodeError as e:
            st.error(f"Failed to parse character data: {str(e)}")
            st.code(response_text)  # Display the problematic response for debugging
            return None