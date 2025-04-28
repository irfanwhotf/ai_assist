"""
Speech-to-Text (STT) package for handling text-to-speech conversion with emotional expression.
"""

from .core import generate_speech, save_audio, play_audio, SUPPORTED_VOICES, DEFAULT_VOICE, DEFAULT_SPEED
from .emotions import SUPPORTED_EMOTIONS, DEFAULT_EMOTION, create_emotional_prompt

__all__ = [
    'generate_speech',
    'save_audio',
    'play_audio',
    'SUPPORTED_VOICES',
    'DEFAULT_VOICE',
    'SUPPORTED_EMOTIONS',
    'DEFAULT_EMOTION',
    'DEFAULT_SPEED',
    'create_emotional_prompt'
]
