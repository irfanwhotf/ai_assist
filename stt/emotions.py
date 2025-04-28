"""
Emotions module for the TTS system.

This module provides functionality for adding emotional expression to generated speech.
"""

# Define supported emotions/styles
SUPPORTED_EMOTIONS = [
    "happy", "sad", "excited", "calm", "angry", "fearful", "surprised", "neutral",
    "professional", "friendly", "enthusiastic", "serious", "whisper", "shouting"
]

# Default emotion
DEFAULT_EMOTION = "neutral"

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
