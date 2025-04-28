"""
Gemini API module for the AI Assistant.

This module handles interaction with the Gemini API for generating responses
and incorporates Neura's personality and memory system.
"""

import os
import time
import sys
import re
import google.generativeai as genai
from colorama import Fore, Style

# Import personality module
from .personality import personalize_text, create_system_prompt, print_personality_loaded, update_user_name_from_memories
# Import memory module
from .memory import retrieve_memories, add_memory, format_memories_for_context, get_all_memories

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

            # Check if this is a memory command
            memory_command = self._check_memory_command(user_input)
            if memory_command:
                return memory_command

            # Get all memories to check for user name
            all_memories = get_all_memories()

            # Update user name from memories if possible
            update_user_name_from_memories(all_memories)

            # Retrieve relevant memories
            relevant_memories = retrieve_memories(user_input, k=3)

            # Format memories as context if any were found
            memory_context = ""
            if relevant_memories:
                memory_context = format_memories_for_context(relevant_memories)
                print(f"{Fore.BLUE}Found {len(relevant_memories)} relevant memories{Style.RESET_ALL}")

            # Prepare input with memory context if available
            if memory_context:
                enhanced_input = f"{memory_context}\n\nUser: {user_input}\n\nPlease use the memories above if they're relevant to the question."
            else:
                enhanced_input = user_input

            # Get response from Gemini
            response = self.chat.send_message(enhanced_input)

            # Calculate response time
            response_time = time.time() - start_time
            print(f"{Fore.BLUE}Response time: {response_time:.2f}s{Style.RESET_ALL}")

            # Get the raw response text
            raw_response = response.text

            # Check if we should remember something from this interaction
            self._check_for_memory(user_input, raw_response)

            # Personalize the response with Neura's personality
            personalized_response = personalize_text(raw_response)

            # Return the personalized response
            return personalized_response

        except Exception as e:
            error_msg = f"Error: {str(e)}"
            print(f"{Fore.RED}{error_msg}{Style.RESET_ALL}")
            return f"Oops, something went wrong on my end! Technical stuff: {str(e)}"

    def _check_memory_command(self, user_input):
        """
        Check if the user input is a memory command

        Args:
            user_input: User's input text

        Returns:
            Response text if it's a memory command, None otherwise
        """
        # Convert to lowercase for easier matching
        text = user_input.lower().strip()

        # Check for remember command
        if text.startswith("remember "):
            memory_content = user_input[9:].strip()  # Remove "remember " prefix
            if memory_content:
                # Check if this is a name-related memory
                name_indicators = ["my name is", "call me", "i am", "i'm", "name's"]
                is_name_memory = any(indicator in memory_content.lower() for indicator in name_indicators)

                # Add the memory
                success = add_memory(memory_content)

                # If it's a name memory, update the user name
                if success and is_name_memory:
                    # Get all memories to update the name
                    all_memories = get_all_memories()
                    name_updated = update_user_name_from_memories(all_memories)

                    if name_updated:
                        return f"I'll remember that your name is {memory_content.split()[-1]}!"

                if success:
                    return f"I'll remember that: {memory_content}"
                else:
                    return "I already have a similar memory stored!"
            else:
                return "What would you like me to remember?"

        # Check for memory listing command
        if any(cmd in text for cmd in ["list memories", "show memories", "what do you remember"]):
            # Get all memories instead of using retrieval
            all_memories = get_all_memories()
            if all_memories:
                response = "Here's what I remember:\n\n"
                for i, memory in enumerate(all_memories):
                    response += f"{i+1}. {memory['content']}\n"
                return response
            else:
                return "I don't have any memories stored yet. You can ask me to remember something by saying 'remember [information]'."

        # Check for name setting command
        if text.startswith("my name is ") or text.startswith("call me "):
            # Extract the name
            if text.startswith("my name is "):
                name = user_input[11:].strip()  # Remove "my name is " prefix
            else:  # call me
                name = user_input[8:].strip()  # Remove "call me " prefix

            # Add as a memory
            memory_content = f"My name is {name}"
            add_memory(memory_content)

            # Update the name
            all_memories = get_all_memories()
            update_user_name_from_memories(all_memories)

            return f"Great! I'll call you {name} from now on."

        # No memory command detected
        return None

    def _check_for_memory(self, user_input, response):
        """
        Check if we should extract and store a memory from this interaction

        Args:
            user_input: User's input text
            response: AI's response text
        """
        # Check if user asked to remember something indirectly
        remember_phrases = [
            "don't forget", "remember that", "keep in mind",
            "make a note", "important to know", "remember this"
        ]

        # Check user input for memory indicators
        if any(phrase in user_input.lower() for phrase in remember_phrases):
            # Extract the key information - use the whole input as memory
            add_memory(user_input)
            print(f"{Fore.GREEN}Automatically stored memory from user input{Style.RESET_ALL}")

        # Check for important information in the response that might be worth remembering
        # This is a simple heuristic - could be improved with more sophisticated extraction
        important_indicators = [
            "important to remember", "key point", "remember that",
            "don't forget", "make sure to remember"
        ]

        for indicator in important_indicators:
            if indicator in response.lower():
                # Find the sentence containing the indicator
                sentences = re.split(r'(?<=[.!?])\s+', response)
                for sentence in sentences:
                    if indicator in sentence.lower():
                        # Store this sentence as a memory
                        add_memory(sentence)
                        print(f"{Fore.GREEN}Automatically stored memory from response{Style.RESET_ALL}")
                        break
