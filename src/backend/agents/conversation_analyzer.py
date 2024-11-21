class ConversationAnalyzer:
    """Analyzes conversation content and patterns.
    
    A utility class that provides methods for analyzing conversation messages
    to detect questions, similar topics, and other conversational patterns.
    """
    
    @staticmethod
    def is_question(message: str) -> bool:
        """Check if a message is a question.
        
        Analyzes a message to determine if it is phrased as a question by looking
        for common question indicators like question marks and interrogative words.

        Args:
            message (str): The message text to analyze

        Returns:
            bool: True if the message appears to be a question, False otherwise
        """
        question_indicators = [
            "?", "what", "how", "why", "where", "when", "who", "which",
            "could you", "would you", "will you", "can you", "do you"
        ]
        message_lower = message.lower()
        return any(indicator in message_lower for indicator in question_indicators)

    @staticmethod
    def check_similar_topics(msg1: str, msg2: str) -> bool:
        """Check if two messages discuss similar topics.
        
        Compares two messages to determine if they are discussing related topics
        by checking for shared keywords in predefined topic categories.

        Args:
            msg1 (str): First message to compare
            msg2 (str): Second message to compare

        Returns:
            bool: True if the messages appear to discuss similar topics, False otherwise
        """
        topic_keywords = {
            "mystery": ["journal", "key", "symbols", "passage", "chamber", "secret"],
            "investigation": ["found", "discovered", "search", "look", "examine"],
            "speculation": ["think", "believe", "suspect", "perhaps", "maybe"],
        }
        
        msg1_lower = msg1.lower()
        msg2_lower = msg2.lower()
        
        return any(
            any(word in msg1_lower for word in keywords) and 
            any(word in msg2_lower for word in keywords)
            for keywords in topic_keywords.values()
        )