"""
Gemini API module for the AI Assistant.

This module handles interaction with the Gemini API for generating responses.
"""

import os
import time
import sys
import google.generativeai as genai
from colorama import Fore, Style

class GeminiAssistant:
    """Class to handle interaction with the Gemini API"""
    
    def __init__(self, api_key=None):
        """
        Initialize the Gemini Assistant
        
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
        
        # Create a chat session
        self.chat = self.model.start_chat(history=[])
        
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
        Get a response from Gemini
        
        Args:
            user_input: User's input text
            
        Returns:
            Response text from Gemini
        """
        try:
            print(f"{Fore.CYAN}Thinking...{Style.RESET_ALL}")
            start_time = time.time()
            
            # Get response
            response = self.chat.send_message(user_input)
            
            # Calculate response time
            response_time = time.time() - start_time
            print(f"{Fore.BLUE}Response time: {response_time:.2f}s{Style.RESET_ALL}")
            
            # Return response text
            return response.text
            
        except Exception as e:
            error_msg = f"Error: {str(e)}"
            print(f"{Fore.RED}{error_msg}{Style.RESET_ALL}")
            return f"I'm sorry, I encountered an error: {str(e)}"
