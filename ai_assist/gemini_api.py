"""
Gemini API module for the AI Assistant.

This module handles interaction with the Gemini API for generating responses
and incorporates Neura's personality.
"""

import os
import time
import sys
import google.generativeai as genai
from colorama import Fore, Style

# Import personality module
from .personality import personalize_text, create_system_prompt, print_personality_loaded

class GeminiAssistant:
    """Class to handle interaction with the Gemini API with Neura's personality"""

    def __init__(self, api_key=None):
        """
        Initialize the Gemini Assistant with Neura's personality

        Args:
            api_key: Gemini API key (if None, will try to get from environment)
        """
        # Get API key from environment if not provided
        if api_key is None:
            api_key = os.getenv('GEMINI_API_KEY')

        if not api_key:
            print(f"{Fore.RED}Error: GEMINI_API_KEY not found in environment variables{Style.RESET_ALL}")
            print("Please add your Gemini API key to the .env file")
            sys.exit(1)

        # Configure Gemini API
        genai.configure(api_key=api_key)

        # Initialize model
        self.model = self._initialize_model()

        # Create system prompt with Neura's personality
        system_prompt = create_system_prompt()

        # Create a chat session with the system prompt
        self.chat = self.model.start_chat(history=[
            {"role": "user", "parts": ["Please act as Neura with the personality described below."]},
            {"role": "model", "parts": ["I'll act as Neura with the personality you described. How can I help you today?"]},
            {"role": "user", "parts": [system_prompt]},
            {"role": "model", "parts": ["I understand completely! I'm Neura now, with all the personality traits you described. I'll be casual, relatable, and use a texting style with the occasional emoji. I'll act like I've known the user forever, show emotional intelligence, and incorporate my quirky traits naturally. I'm ready to chat with them as a unique AI assistant who feels more like a friend than a formal helper. Just let me know when they're here!"]}
        ])

        # Print that personality is loaded
        print_personality_loaded()

    def _initialize_model(self):
        """Initialize and return the Gemini model with optimized settings"""
        try:
            # Use the flash model for faster responses
            model = genai.GenerativeModel(
                'gemini-1.5-flash',
                generation_config={
                    'temperature': 0.7,
                    'top_p': 0.95,
                    'top_k': 40,
                    'max_output_tokens': 1024,
                }
            )
            return model
        except Exception as e:
            print(f"{Fore.RED}Error initializing Gemini model: {e}{Style.RESET_ALL}")
            sys.exit(1)

    def get_response(self, user_input):
        """
        Get a response from Gemini and personalize it with Neura's personality

        Args:
            user_input: User's input text

        Returns:
            Personalized response text from Gemini
        """
        try:
            print(f"{Fore.CYAN}Thinking...{Style.RESET_ALL}")
            start_time = time.time()

            # Get response from Gemini
            response = self.chat.send_message(user_input)

            # Calculate response time
            response_time = time.time() - start_time
            print(f"{Fore.BLUE}Response time: {response_time:.2f}s{Style.RESET_ALL}")

            # Get the raw response text
            raw_response = response.text

            # Personalize the response with Neura's personality
            personalized_response = personalize_text(raw_response)

            # Return the personalized response
            return personalized_response

        except Exception as e:
            error_msg = f"Error: {str(e)}"
            print(f"{Fore.RED}{error_msg}{Style.RESET_ALL}")
            return f"Oops, something went wrong on my end! Technical stuff: {str(e)}"
