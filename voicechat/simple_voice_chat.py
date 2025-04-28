#!/usr/bin/env python3
"""
Simple Voice Chat - A standalone script that doesn't rely on package imports

This script creates an interactive chatbot that:
1. Takes user input as text
2. Sends the input to Gemini 2.0 Flash API
3. Speaks the response using OpenAI.fm TTS
4. Maintains conversation history
"""

import os
import sys
import time
import asyncio
import requests
import io
import torch
import numpy as np
import warnings
from concurrent.futures import ThreadPoolExecutor
from dotenv import load_dotenv
import google.generativeai as genai
from colorama import init, Fore, Style
import sounddevice as sd
from scipy.io import wavfile

# Initialize colorama for colored terminal output
init()

# Check if CUDA is available
CUDA_AVAILABLE = torch.cuda.is_available()
if CUDA_AVAILABLE:
    print(f"CUDA is available. Using GPU: {torch.cuda.get_device_name(0)}")
else:
    print("CUDA is not available. Using CPU.")

# Define supported voices
SUPPORTED_VOICES = ["alloy", "echo", "fable", "onyx", "nova", "shimmer", "ash", "coral", "sage"]

# Define supported emotions/styles
SUPPORTED_EMOTIONS = [
    "happy", "sad", "excited", "calm", "angry", "fearful", "surprised", "neutral",
    "professional", "friendly", "enthusiastic", "serious", "whisper", "shouting"
]

# Default settings
DEFAULT_VOICE = "nova"  # Set nova as default voice
DEFAULT_EMOTION = "neutral"
DEFAULT_SPEED = 1.25    # Default speed multiplier (1.25x)

# API configuration for OpenAI.fm
PROVIDER_HEADERS = {
    "accept": "/",
    "accept-encoding": "gzip, deflate, br, zstd",
    "accept-language": "en-US,en;q=0.9",
    "dnt": "1",
    "origin": "https://www.openai.fm",
    "referer": "https://www.openai.fm/",
    "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/123.0.0.0 Safari/537.36"
}
PROVIDER_URL = "https://www.openai.fm/api/generate"

# Audio cache to reduce latency for repeated phrases
AUDIO_CACHE = {}
MAX_CACHE_SIZE = 50  # Maximum number of cached audio samples

# Load environment variables
load_dotenv()

# Configure Gemini API
GEMINI_API_KEY = os.getenv('GEMINI_API_KEY')
if not GEMINI_API_KEY:
    print(f"{Fore.RED}Error: GEMINI_API_KEY not found in environment variables{Style.RESET_ALL}")
    print("Please add your Gemini API key to the .env file")
    sys.exit(1)

# Configure TTS settings from environment or use defaults
TTS_VOICE = os.getenv('DEFAULT_VOICE', DEFAULT_VOICE)
TTS_EMOTION = os.getenv('DEFAULT_EMOTION', DEFAULT_EMOTION)
try:
    TTS_SPEED = float(os.getenv('DEFAULT_SPEED', DEFAULT_SPEED))
except (ValueError, TypeError):
    TTS_SPEED = DEFAULT_SPEED

# Configure Gemini API
genai.configure(api_key=GEMINI_API_KEY)

# Create a thread pool for concurrent processing
executor = ThreadPoolExecutor(max_workers=4)

def create_emotional_prompt(voice, emotion):
    """
    Create a detailed voice prompt with emotional cues

    Args:
        voice: The voice to use
        emotion: The emotion/style to apply

    Returns:
        A detailed prompt string
    """
    base_prompt = f"Voice: {voice}. "

    emotion_prompts = {
        "happy": "Speak with a cheerful, upbeat tone. Sound genuinely happy and optimistic.",
        "sad": "Speak with a somber, melancholic tone. Express sadness and heaviness in your voice.",
        "excited": "Speak with high energy and enthusiasm. Sound thrilled and eager.",
        "calm": "Speak with a soothing, peaceful tone. Maintain a tranquil and relaxed voice.",
        "angry": "Speak with intensity and force. Express controlled anger and frustration.",
        "fearful": "Speak with a trembling, uncertain voice. Express worry and anxiety.",
        "surprised": "Speak with astonishment. Express genuine shock and wonder.",
        "neutral": "Speak with a clear, balanced tone. Maintain a professional, unbiased voice.",
        "professional": "Speak with authority and clarity. Maintain a formal, business-like tone.",
        "friendly": "Speak warmly and invitingly. Sound approachable and kind.",
        "enthusiastic": "Speak with passion and energy. Show genuine interest and excitement.",
        "serious": "Speak with gravity and importance. Convey the weight of your message.",
        "whisper": "Speak in a hushed, quiet whisper. Keep your voice soft and intimate.",
        "shouting": "Project your voice loudly and clearly. Speak as if addressing a large crowd."
    }

    # Get the specific emotion prompt or use neutral if not found
    emotion_prompt = emotion_prompts.get(emotion, emotion_prompts["neutral"])

    # Combine base prompt with emotion prompt
    return base_prompt + emotion_prompt

def validate_emotion(emotion):
    """
    Validate that the provided emotion is supported

    Args:
        emotion: The emotion to validate

    Returns:
        True if valid, raises ValueError if not
    """
    if emotion not in SUPPORTED_EMOTIONS:
        raise ValueError(f"Emotion '{emotion}' not supported. Supported emotions: {SUPPORTED_EMOTIONS}")
    return True

def generate_speech(text, voice=DEFAULT_VOICE, emotion=DEFAULT_EMOTION, speed=DEFAULT_SPEED):
    """
    Generate speech from text using OpenAI.fm API with optimized performance

    Args:
        text: Text to convert to speech
        voice: Voice to use for synthesis
        emotion: Emotion/style to apply to the voice
        speed: Speed multiplier for speech (e.g., 1.0 is normal, 1.25 is 25% faster)

    Returns:
        Audio content as bytes
    """
    # Create cache key
    cache_key = f"{text}_{voice}_{emotion}_{speed}"

    # Check if audio is in cache
    if cache_key in AUDIO_CACHE:
        print(f"Using cached audio for: {text[:30]}...")
        return AUDIO_CACHE[cache_key]

    # Validate voice
    if voice not in SUPPORTED_VOICES:
        raise ValueError(f"Voice '{voice}' not supported. Supported voices: {SUPPORTED_VOICES}")

    # Validate emotion
    validate_emotion(emotion)

    # Validate speed
    if speed <= 0:
        raise ValueError(f"Speed must be positive, got {speed}")

    print(f"Generating speech with voice: {voice}, emotion: {emotion}, speed: {speed}x")

    # Create detailed voice prompt with emotion and speed
    voice_prompt = create_emotional_prompt(voice, emotion)

    # Add speed instruction to the prompt if not at normal speed
    if speed != 1.0:
        if speed > 1.0:
            voice_prompt += f" Speak {int((speed-1.0)*100)}% faster than normal."
        else:
            voice_prompt += f" Speak {int((1.0-speed)*100)}% slower than normal."

    # Prepare payload with appropriate vibe
    payload = {
        "input": text,
        "prompt": voice_prompt,
        "voice": voice,
        "vibe": emotion if emotion != "neutral" else "null"
    }

    # Make API call
    try:
        response = requests.post(PROVIDER_URL, headers=PROVIDER_HEADERS, data=payload, timeout=30)
        response.raise_for_status()

        # Cache the audio
        if len(AUDIO_CACHE) >= MAX_CACHE_SIZE:
            # Remove oldest item if cache is full
            AUDIO_CACHE.pop(next(iter(AUDIO_CACHE)))

        AUDIO_CACHE[cache_key] = response.content

        # Return audio content
        return response.content

    except Exception as e:
        print(f"Error generating speech: {e}")
        raise

def play_audio(audio_bytes, volume=1.0):
    """
    Play audio bytes directly using sounddevice

    This method avoids creating temporary files by playing audio directly from memory.
    Uses CUDA acceleration if available for faster processing.

    Args:
        audio_bytes: Audio data as bytes
        volume: Volume level (0.0 to 1.0, default is 1.0)
    """
    # Ensure volume is within valid range
    volume = max(0.0, min(1.0, volume))

    try:
        # Convert audio bytes to numpy array for processing
        audio_io = io.BytesIO(audio_bytes)

        try:
            # Try to read as WAV file first
            with warnings.catch_warnings():
                warnings.simplefilter("ignore")
                sample_rate, audio_data = wavfile.read(audio_io)
        except Exception:
            # If WAV reading fails, try to handle as MP3
            # Reset the file pointer
            audio_io.seek(0)

            # Save to a temporary file and use sounddevice directly
            import tempfile
            with tempfile.NamedTemporaryFile(suffix=".mp3", delete=False) as temp_file:
                temp_path = temp_file.name
                temp_file.write(audio_bytes)

            # Use a system command to play the audio
            import subprocess
            try:
                subprocess.run(["start", temp_path], shell=True, check=True)
                time.sleep(0.5)  # Give some time for the player to start
                print(f"Audio playback started via system player")
                return
            except Exception as e:
                print(f"Could not play audio via system player: {e}")
                raise

        # Convert to float32 for processing
        if audio_data.dtype != np.float32:
            audio_data = audio_data.astype(np.float32) / np.iinfo(audio_data.dtype).max

        # Apply volume adjustment
        audio_data = audio_data * volume

        # Use CUDA for processing if available
        if CUDA_AVAILABLE:
            # Move data to GPU for processing
            audio_tensor = torch.tensor(audio_data, device='cuda')

            # Apply any GPU-accelerated processing here
            # For example, you could apply filters, normalization, etc.

            # Move back to CPU for playback
            audio_data = audio_tensor.cpu().numpy()

        # Play the audio
        sd.play(audio_data, sample_rate)
        sd.wait()  # Wait until audio is finished playing

        print(f"Audio playback completed")

    except Exception as e:
        print(f"Could not play audio: {e}")

        # Fallback to saving a file if direct playback fails
        try:
            import tempfile
            with tempfile.NamedTemporaryFile(suffix=".mp3", delete=False) as temp_file:
                temp_path = temp_file.name
                temp_file.write(audio_bytes)

            # Use the appropriate command based on the operating system
            # Since we're on Windows, use the start command
            os.system(f'start {temp_path}')
            print("Audio opened in default player")
        except Exception as e2:
            print(f"Fallback also failed: {e2}")

# Initialize Gemini model with optimized settings
def initialize_model():
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

async def generate_speech_async(text, voice, emotion, speed):
    """Generate speech asynchronously"""
    loop = asyncio.get_event_loop()
    return await loop.run_in_executor(
        executor,
        lambda: generate_speech(text, voice, emotion, speed)
    )

async def play_audio_async(audio_bytes, volume=1.0):
    """Play audio asynchronously"""
    loop = asyncio.get_event_loop()
    await loop.run_in_executor(
        executor,
        lambda: play_audio(audio_bytes, volume)
    )

async def speak_async(text):
    """Generate speech and play it asynchronously"""
    print(f"{Fore.CYAN}Speaking...{Style.RESET_ALL}")

    # Generate speech with the configured settings
    audio_bytes = await generate_speech_async(text, TTS_VOICE, TTS_EMOTION, TTS_SPEED)

    # Play the audio
    await play_audio_async(audio_bytes)

async def get_gemini_response(chat, user_input):
    """Get response from Gemini asynchronously"""
    loop = asyncio.get_event_loop()
    return await loop.run_in_executor(
        executor,
        lambda: chat.send_message(user_input)
    )

def print_system_info():
    """Print system information and settings"""
    print(f"{Fore.GREEN}=== Optimized Voice Chat ===")
    print(f"Using voice: {TTS_VOICE}, emotion: {TTS_EMOTION}, speed: {TTS_SPEED}x")

    # Print CUDA information if available
    if CUDA_AVAILABLE:
        print(f"CUDA enabled: {torch.cuda.get_device_name(0)}")
        print(f"CUDA version: {torch.version.cuda}")
    else:
        print("CUDA not available, using CPU")

    print(f"Type 'exit' or 'quit' to end the chat")
    print(f"Type 'voice <name>' to change the voice")
    print(f"Type 'emotion <name>' to change the emotion")
    print(f"Type 'speed <value>' to change the speed{Style.RESET_ALL}")
    print()

async def chat_with_gemini():
    """Run an interactive chat session with Gemini and TTS responses"""
    # Declare globals that will be modified in this function
    global TTS_VOICE, TTS_EMOTION, TTS_SPEED

    # Initialize the model
    model = initialize_model()

    # Create a chat session
    chat = model.start_chat(history=[])

    # Print system information
    print_system_info()

    # Initial greeting
    greeting = "Hello! I'm your voice assistant powered by Gemini. How can I help you today?"
    print(f"{Fore.YELLOW}Assistant: {greeting}{Style.RESET_ALL}")
    await speak_async(greeting)

    # Chat loop
    while True:
        # Get user input
        user_input = input(f"{Fore.GREEN}You: {Style.RESET_ALL}").strip()

        # Check for exit command
        if user_input.lower() in ['exit', 'quit', 'bye']:
            farewell = "Goodbye! Have a great day!"
            print(f"{Fore.YELLOW}Assistant: {farewell}{Style.RESET_ALL}")
            await speak_async(farewell)
            break

        # Check for voice change command
        if user_input.lower().startswith('voice '):
            voice_name = user_input[6:].strip()
            if voice_name in SUPPORTED_VOICES:
                TTS_VOICE = voice_name
                response = f"Voice changed to {voice_name}."
                print(f"{Fore.BLUE}System: {response}{Style.RESET_ALL}")
                await speak_async(response)
            else:
                response = f"Voice {voice_name} not found. Available voices: {', '.join(SUPPORTED_VOICES)}"
                print(f"{Fore.RED}System: {response}{Style.RESET_ALL}")
                await speak_async(response)
            continue

        # Check for emotion change command
        if user_input.lower().startswith('emotion '):
            emotion_name = user_input[8:].strip()
            if emotion_name in SUPPORTED_EMOTIONS:
                TTS_EMOTION = emotion_name
                response = f"Emotion changed to {emotion_name}."
                print(f"{Fore.BLUE}System: {response}{Style.RESET_ALL}")
                await speak_async(response)
            else:
                response = f"Emotion {emotion_name} not found. Available emotions: {', '.join(SUPPORTED_EMOTIONS)}"
                print(f"{Fore.RED}System: {response}{Style.RESET_ALL}")
                await speak_async(response)
            continue

        # Check for speed change command
        if user_input.lower().startswith('speed '):
            try:
                speed_value = float(user_input[6:].strip())
                if speed_value > 0:
                    TTS_SPEED = speed_value
                    response = f"Speed changed to {speed_value}x."
                    print(f"{Fore.BLUE}System: {response}{Style.RESET_ALL}")
                    await speak_async(response)
                else:
                    response = "Speed must be positive."
                    print(f"{Fore.RED}System: {response}{Style.RESET_ALL}")
                    await speak_async(response)
            except ValueError:
                response = "Invalid speed value. Please enter a number."
                print(f"{Fore.RED}System: {response}{Style.RESET_ALL}")
                await speak_async(response)
            continue

        # Skip empty inputs
        if not user_input:
            continue

        try:
            # Send the message to Gemini
            print(f"{Fore.CYAN}Thinking...{Style.RESET_ALL}")
            start_time = time.time()

            # Get response asynchronously
            response = await get_gemini_response(chat, user_input)

            # Calculate response time
            response_time = time.time() - start_time
            print(f"{Fore.BLUE}Response time: {response_time:.2f}s{Style.RESET_ALL}")

            # Get the response text
            response_text = response.text

            # Print and speak the response
            print(f"{Fore.YELLOW}Assistant: {response_text}{Style.RESET_ALL}")
            await speak_async(response_text)

        except Exception as e:
            error_msg = f"Error: {str(e)}"
            print(f"{Fore.RED}{error_msg}{Style.RESET_ALL}")
            await speak_async(f"I'm sorry, I encountered an error: {str(e)}")

def main():
    """Main entry point"""
    try:
        # Run the async chat function
        asyncio.run(chat_with_gemini())
    except KeyboardInterrupt:
        print("\nExiting...")
    except Exception as e:
        print(f"{Fore.RED}Unexpected error: {e}{Style.RESET_ALL}")
    finally:
        # Clean up resources
        executor.shutdown(wait=False)

if __name__ == "__main__":
    main()
