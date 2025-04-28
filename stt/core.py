"""
Core TTS functionality module.

This module provides the basic text-to-speech conversion functionality.
"""

import requests
import io
import pygame
from .emotions import validate_emotion, create_emotional_prompt, DEFAULT_EMOTION

# Initialize pygame mixer for audio playback
pygame.mixer.init()

# Define supported voices
SUPPORTED_VOICES = ["alloy", "echo", "fable", "onyx", "nova", "shimmer", "ash", "coral", "sage"]

# Default voice and speed
DEFAULT_VOICE = "nova"
DEFAULT_SPEED = 1.25  # Default speed multiplier (1.25x)

# API configuration
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

def generate_speech(text, voice=DEFAULT_VOICE, emotion=DEFAULT_EMOTION, speed=DEFAULT_SPEED):
    """
    Generate speech from text using OpenAI.fm API

    Args:
        text: Text to convert to speech
        voice: Voice to use for synthesis
        emotion: Emotion/style to apply to the voice
        speed: Speed multiplier for speech (e.g., 1.0 is normal, 1.25 is 25% faster)

    Returns:
        Audio content as bytes
    """
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
        response = requests.post(PROVIDER_URL, headers=PROVIDER_HEADERS, data=payload, timeout=60)
        response.raise_for_status()

        # Return audio content
        return response.content

    except Exception as e:
        print(f"Error generating speech: {e}")
        raise

def save_audio(audio_bytes, output_file):
    """
    Save audio bytes to a file

    Args:
        audio_bytes: Audio data as bytes
        output_file: Path to save the audio file
    """
    with open(output_file, "wb") as f:
        f.write(audio_bytes)

    print(f"Audio saved to: {output_file}")

def play_audio(audio_bytes, volume=1.0, playback_speed=1.0):
    """
    Play audio bytes directly using pygame mixer

    Args:
        audio_bytes: Audio data as bytes
        volume: Volume level (0.0 to 1.0, default is 1.0)
        playback_speed: Speed multiplier for playback (1.0 is normal speed)
    """
    # Ensure volume is within valid range
    volume = max(0.0, min(1.0, volume))

    # Ensure playback_speed is positive
    if playback_speed <= 0:
        print(f"Invalid playback speed {playback_speed}, using 1.0")
        playback_speed = 1.0

    try:
        # Create a BytesIO object from the audio bytes
        audio_file = io.BytesIO(audio_bytes)

        # Load the audio file into pygame
        pygame.mixer.music.load(audio_file)

        # Set volume
        pygame.mixer.music.set_volume(volume)

        # Note: pygame.mixer doesn't support changing playback speed directly
        # The speed is controlled through the TTS generation prompt

        # Play the audio
        pygame.mixer.music.play()

        print(f"Playing audio at volume {int(volume * 100)}%...")

        # Wait for the audio to finish playing
        while pygame.mixer.music.get_busy():
            pygame.time.Clock().tick(10)

    except Exception as e:
        print(f"Could not play audio: {e}")

        # Fallback to saving a file if pygame playback fails
        try:
            import tempfile
            with tempfile.NamedTemporaryFile(suffix=".mp3", delete=False) as temp_file:
                temp_path = temp_file.name
                temp_file.write(audio_bytes)

            print(f"Fallback: Audio saved to temporary file: {temp_path}")
            print("Please open it manually")
        except:
            print("Could not save audio to temporary file")
