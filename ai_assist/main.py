#!/usr/bin/env python3
"""
AI Voice Assistant - Main module

This module ties together the TTS, STT, and Gemini API modules to create a complete voice assistant.
"""

import os
import sys
import asyncio
from concurrent.futures import ThreadPoolExecutor
from dotenv import load_dotenv
from colorama import init, Fore, Style

# Import our modules
from .tts import speak, DEFAULT_VOICE, DEFAULT_EMOTION, DEFAULT_SPEED, SUPPORTED_VOICES, SUPPORTED_EMOTIONS
from .stt import listen_for_speech, initialize_whisper
from .gemini_api import GeminiAssistant

# Initialize colorama for colored terminal output
init()

# Load environment variables
load_dotenv()

# Configure TTS settings from environment or use defaults
TTS_VOICE = os.getenv('DEFAULT_VOICE', DEFAULT_VOICE)
TTS_EMOTION = os.getenv('DEFAULT_EMOTION', DEFAULT_EMOTION)
try:
    TTS_SPEED = float(os.getenv('DEFAULT_SPEED', DEFAULT_SPEED))
except (ValueError, TypeError):
    TTS_SPEED = DEFAULT_SPEED

# Create a thread pool for concurrent processing
executor = ThreadPoolExecutor(max_workers=4)

def print_system_info():
    """Print system information and settings"""
    print(f"{Fore.GREEN}=== AI Voice Assistant ===")
    print(f"Using voice: {TTS_VOICE}, emotion: {TTS_EMOTION}, speed: {TTS_SPEED}x")
    print(f"Press and hold Shift+Spacebar to record speech")
    print(f"Say 'exit' or 'quit' to end the chat")
    print(f"Say 'voice <name>' to change the voice")
    print(f"Say 'emotion <name>' to change the emotion")
    print(f"Say 'speed <value>' to change the speed{Style.RESET_ALL}")
    print()

async def run_async(func, *args, **kwargs):
    """Run a function asynchronously"""
    loop = asyncio.get_event_loop()
    return await loop.run_in_executor(
        executor,
        lambda: func(*args, **kwargs)
    )

async def voice_assistant():
    """Run the voice assistant"""
    # Declare globals that will be modified in this function
    global TTS_VOICE, TTS_EMOTION, TTS_SPEED
    
    # Initialize the whisper model
    await run_async(initialize_whisper)
    
    # Initialize the Gemini assistant
    gemini = GeminiAssistant()
    
    # Print system information
    print_system_info()
    
    # Initial greeting
    greeting = "Hello! I'm your voice assistant powered by Gemini. Press and hold Shift+Spacebar to speak."
    print(f"{Fore.YELLOW}Assistant: {greeting}{Style.RESET_ALL}")
    await run_async(speak, greeting, TTS_VOICE, TTS_EMOTION, TTS_SPEED)
    
    # Chat loop
    while True:
        # Listen for speech
        user_input = await run_async(listen_for_speech)
        
        # Print transcribed text
        print(f"{Fore.GREEN}You: {user_input}{Style.RESET_ALL}")
        
        # Check if the transcription is empty
        if not user_input.strip():
            print(f"{Fore.RED}No speech detected. Please try again.{Style.RESET_ALL}")
            continue
            
        # Check for exit command
        if any(exit_word in user_input.lower() for exit_word in ['exit', 'quit', 'bye']):
            farewell = "Goodbye! Have a great day!"
            print(f"{Fore.YELLOW}Assistant: {farewell}{Style.RESET_ALL}")
            await run_async(speak, farewell, TTS_VOICE, TTS_EMOTION, TTS_SPEED)
            break
            
        # Check for voice command
        if user_input.lower().startswith('voice '):
            voice_name = user_input.lower().split('voice ')[1].strip()
            if voice_name in SUPPORTED_VOICES:
                TTS_VOICE = voice_name
                print(f"{Fore.BLUE}Voice changed to: {TTS_VOICE}{Style.RESET_ALL}")
                await run_async(speak, f"Voice changed to {TTS_VOICE}", TTS_VOICE, TTS_EMOTION, TTS_SPEED)
            else:
                print(f"{Fore.RED}Unsupported voice: {voice_name}{Style.RESET_ALL}")
                await run_async(speak, f"Sorry, {voice_name} is not a supported voice", TTS_VOICE, TTS_EMOTION, TTS_SPEED)
            continue
            
        # Check for emotion command
        if user_input.lower().startswith('emotion '):
            emotion_name = user_input.lower().split('emotion ')[1].strip()
            if emotion_name in SUPPORTED_EMOTIONS:
                TTS_EMOTION = emotion_name
                print(f"{Fore.BLUE}Emotion changed to: {TTS_EMOTION}{Style.RESET_ALL}")
                await run_async(speak, f"Emotion changed to {TTS_EMOTION}", TTS_VOICE, TTS_EMOTION, TTS_SPEED)
            else:
                print(f"{Fore.RED}Unsupported emotion: {emotion_name}{Style.RESET_ALL}")
                await run_async(speak, f"Sorry, {emotion_name} is not a supported emotion", TTS_VOICE, TTS_EMOTION, TTS_SPEED)
            continue
            
        # Check for speed command
        if user_input.lower().startswith('speed '):
            try:
                speed_value = float(user_input.lower().split('speed ')[1].strip())
                if speed_value > 0:
                    TTS_SPEED = speed_value
                    print(f"{Fore.BLUE}Speed changed to: {TTS_SPEED}x{Style.RESET_ALL}")
                    await run_async(speak, f"Speed changed to {TTS_SPEED} times", TTS_VOICE, TTS_EMOTION, TTS_SPEED)
                else:
                    print(f"{Fore.RED}Speed must be positive{Style.RESET_ALL}")
                    await run_async(speak, "Speed must be a positive number", TTS_VOICE, TTS_EMOTION, TTS_SPEED)
            except ValueError:
                print(f"{Fore.RED}Invalid speed value{Style.RESET_ALL}")
                await run_async(speak, "Please provide a valid number for speed", TTS_VOICE, TTS_EMOTION, TTS_SPEED)
            continue
            
        # Get response from Gemini
        response_text = await run_async(gemini.get_response, user_input)
        
        # Print and speak the response
        print(f"{Fore.YELLOW}Assistant: {response_text}{Style.RESET_ALL}")
        await run_async(speak, response_text, TTS_VOICE, TTS_EMOTION, TTS_SPEED)

def main():
    """Main entry point"""
    try:
        # Run the async voice assistant
        asyncio.run(voice_assistant())
    except KeyboardInterrupt:
        print("\nExiting...")
    except Exception as e:
        print(f"{Fore.RED}Unexpected error: {e}{Style.RESET_ALL}")
    finally:
        # Clean up resources
        executor.shutdown(wait=False)

if __name__ == "__main__":
    main()
