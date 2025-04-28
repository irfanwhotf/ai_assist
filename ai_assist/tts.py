"""
Text-to-Speech (TTS) module for the AI Assistant.

This module handles text-to-speech conversion using OpenAI.fm API.
"""

import os
import io
import time
import warnings
import requests
import numpy as np
import torch
import sounddevice as sd
from scipy.io import wavfile
from colorama import Fore, Style

# Define supported voices
SUPPORTED_VOICES = ["alloy", "echo", "fable", "onyx", "nova", "shimmer", "ash", "coral", "sage"]

# Define supported emotions/styles
SUPPORTED_EMOTIONS = [
    "happy", "sad", "excited", "calm", "angry", "fearful", "surprised", "neutral",
    "professional", "friendly", "enthusiastic", "serious", "whisper", "shouting"
]

# Default settings
DEFAULT_VOICE = "nova"
DEFAULT_EMOTION = "neutral"
DEFAULT_SPEED = 1.25  # Default speed multiplier (1.25x)

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

# Check if CUDA is available
CUDA_AVAILABLE = torch.cuda.is_available()

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
    
    if emotion == "happy":
        return base_prompt + "Speak in a cheerful, upbeat, and joyful manner. Express happiness and positivity."
    elif emotion == "sad":
        return base_prompt + "Speak in a somber, melancholic tone. Express sadness and heaviness."
    elif emotion == "excited":
        return base_prompt + "Speak with high energy and enthusiasm. Express excitement and eagerness."
    elif emotion == "calm":
        return base_prompt + "Speak in a soothing, peaceful, and relaxed manner. Express tranquility."
    elif emotion == "angry":
        return base_prompt + "Speak with intensity and force. Express frustration and anger."
    elif emotion == "fearful":
        return base_prompt + "Speak with trepidation and uncertainty. Express worry and anxiety."
    elif emotion == "surprised":
        return base_prompt + "Speak with astonishment and wonder. Express shock and amazement."
    elif emotion == "professional":
        return base_prompt + "Speak in a formal, clear, and authoritative manner. Be concise and direct."
    elif emotion == "friendly":
        return base_prompt + "Speak in a warm, approachable, and conversational tone. Be personable."
    elif emotion == "enthusiastic":
        return base_prompt + "Speak with passion and energy. Show strong interest and excitement."
    elif emotion == "serious":
        return base_prompt + "Speak in a grave, no-nonsense manner. Be straightforward and solemn."
    elif emotion == "whisper":
        return base_prompt + "Speak in a hushed, quiet whisper. Be soft and intimate."
    elif emotion == "shouting":
        return base_prompt + "Speak loudly and forcefully, as if projecting to a large audience."
    else:  # neutral or any other value
        return base_prompt + "Speak in a balanced, neutral tone. Be clear and natural."

def validate_emotion(emotion):
    """
    Validate that the emotion is supported
    
    Args:
        emotion: The emotion to validate
        
    Raises:
        ValueError: If the emotion is not supported
    """
    if emotion not in SUPPORTED_EMOTIONS:
        raise ValueError(f"Emotion '{emotion}' not supported. Supported emotions: {SUPPORTED_EMOTIONS}")

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

def speak(text, voice=DEFAULT_VOICE, emotion=DEFAULT_EMOTION, speed=DEFAULT_SPEED, volume=1.0):
    """
    Generate speech and play it

    Args:
        text: Text to convert to speech
        voice: Voice to use for synthesis
        emotion: Emotion/style to apply to the voice
        speed: Speed multiplier for speech
        volume: Volume level (0.0 to 1.0)
    """
    print(f"{Fore.CYAN}Speaking...{Style.RESET_ALL}")
    
    # Generate speech
    audio_bytes = generate_speech(text, voice, emotion, speed)
    
    # Play the audio
    play_audio(audio_bytes, volume)
