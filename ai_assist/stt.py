"""
Speech-to-Text (STT) module for the AI Assistant.

This module handles speech recognition using faster_whisper.
It includes functionality to record audio when shift+spacebar is pressed.
"""

import time
import threading
import numpy as np
import pyaudio
import torch
from pynput import keyboard
from faster_whisper import WhisperModel
from colorama import Fore, Style

# Audio recording settings
RATE = 16000
CHUNK = 1024
FORMAT = pyaudio.paInt16
CHANNELS = 1

# Default whisper model
DEFAULT_WHISPER_MODEL = "small.en"  # Using small.en model for faster performance

# Check if CUDA is available
CUDA_AVAILABLE = torch.cuda.is_available()
DEVICE = "cuda" if CUDA_AVAILABLE else "cpu"
COMPUTE_TYPE = "float16" if CUDA_AVAILABLE else "int8"

# Initialize the WhisperModel
whisper_model = None

class AudioRecorder:
    """Class to handle audio recording with keyboard control"""

    def __init__(self):
        self.recording = False
        self.frames = []
        self.p = pyaudio.PyAudio()
        self.stream = None
        self.recording_thread = None
        self.keyboard_listener = None

    def on_press(self, key):
        """Handle key press events"""
        try:
            # Check if shift+spacebar is pressed
            if key == keyboard.Key.space and keyboard.Key.shift in self.currently_pressed:
                if not self.recording:
                    self.start_recording()
        except AttributeError:
            pass

    def on_release(self, key):
        """Handle key release events"""
        try:
            # Check if spacebar is released
            if key == keyboard.Key.space and self.recording:
                self.stop_recording()
        except AttributeError:
            pass

    def start_keyboard_listener(self):
        """Start listening for keyboard events"""
        self.currently_pressed = set()

        def on_press(key):
            self.currently_pressed.add(key)
            return self.on_press(key)

        def on_release(key):
            if key in self.currently_pressed:
                self.currently_pressed.remove(key)
            return self.on_release(key)

        self.keyboard_listener = keyboard.Listener(on_press=on_press, on_release=on_release)
        self.keyboard_listener.start()

    def stop_keyboard_listener(self):
        """Stop listening for keyboard events"""
        if self.keyboard_listener:
            self.keyboard_listener.stop()

    def start_recording(self):
        """Start recording audio"""
        self.recording = True
        self.frames = []

        print(f"{Fore.CYAN}Recording... (release spacebar to stop){Style.RESET_ALL}")

        # Open stream
        self.stream = self.p.open(format=FORMAT,
                                 channels=CHANNELS,
                                 rate=RATE,
                                 input=True,
                                 frames_per_buffer=CHUNK)

        # Start recording thread
        self.recording_thread = threading.Thread(target=self._record)
        self.recording_thread.start()

    def _record(self):
        """Record audio in a separate thread"""
        while self.recording:
            data = self.stream.read(CHUNK, exception_on_overflow=False)
            self.frames.append(data)

    def stop_recording(self):
        """Stop recording audio"""
        if not self.recording:
            return

        self.recording = False

        # Wait for recording thread to finish
        if self.recording_thread:
            self.recording_thread.join()

        # Stop and close the stream
        if self.stream:
            self.stream.stop_stream()
            self.stream.close()

        print(f"{Fore.CYAN}Recording finished{Style.RESET_ALL}")

    def get_audio_data(self):
        """Get the recorded audio data as numpy array"""
        if not self.frames:
            return None, RATE

        # Convert to numpy array
        audio_data = np.frombuffer(b''.join(self.frames), dtype=np.int16)

        return audio_data, RATE

    def cleanup(self):
        """Clean up resources"""
        self.stop_recording()
        self.stop_keyboard_listener()
        self.p.terminate()

def initialize_whisper(model_size=DEFAULT_WHISPER_MODEL):
    """Initialize the WhisperModel with the specified model size"""
    global whisper_model

    print(f"{Fore.CYAN}Initializing Whisper model ({model_size})...{Style.RESET_ALL}")
    try:
        # Initialize the model with CUDA if available
        whisper_model = WhisperModel(model_size, device=DEVICE, compute_type=COMPUTE_TYPE)
        print(f"{Fore.GREEN}Whisper model initialized successfully{Style.RESET_ALL}")
    except Exception as e:
        print(f"{Fore.RED}Error initializing Whisper model: {e}{Style.RESET_ALL}")
        raise

def post_process_transcription(text):
    """
    Post-process transcription to fix common misrecognitions

    Args:
        text: Transcribed text

    Returns:
        Processed text
    """
    # Common misrecognitions of "Neura"
    neura_variants = [
        "haikyura", "neuron", "nora", "nura", "neural", "nera",
        "noora", "nura", "norah", "nura", "nera", "nura", "nero"
    ]

    # Convert to lowercase for easier matching
    lower_text = text.lower()

    # Check for variants at the beginning of the text
    for variant in neura_variants:
        if lower_text.startswith(variant):
            # Replace with "Neura"
            return "Neura" + text[len(variant):]

    # Check for "list memories" variants
    list_memory_variants = [
        "list memory", "list the memories", "show memory",
        "show the memories", "show me the memories", "show me memory"
    ]

    for variant in list_memory_variants:
        if variant in lower_text:
            # Replace with "list memories"
            return "list memories"

    return text

def transcribe_audio(audio_data, sample_rate=RATE):
    """
    Transcribe audio using faster_whisper

    Args:
        audio_data: Audio data as numpy array
        sample_rate: Sample rate of the audio

    Returns:
        Transcribed text
    """
    if whisper_model is None:
        initialize_whisper()

    print(f"{Fore.CYAN}Transcribing...{Style.RESET_ALL}")
    start_time = time.time()

    # Normalize audio data to float32 in range [-1, 1]
    if audio_data.dtype != np.float32:
        audio_data = audio_data.astype(np.float32) / np.iinfo(np.int16).max

    # Transcribe audio
    segments, info = whisper_model.transcribe(audio_data, beam_size=5)

    # Extract text from segments
    text = " ".join(segment.text for segment in segments)

    # Post-process the transcription
    text = post_process_transcription(text)

    transcription_time = time.time() - start_time
    print(f"{Fore.BLUE}Transcription time: {transcription_time:.2f}s{Style.RESET_ALL}")

    return text

def listen_for_speech():
    """
    Record audio when shift+spacebar is pressed and transcribe it

    Returns:
        Transcribed text
    """
    recorder = AudioRecorder()

    try:
        # Start keyboard listener
        recorder.start_keyboard_listener()

        print(f"{Fore.GREEN}Press and hold Shift+Spacebar to record speech{Style.RESET_ALL}")

        # Wait for recording to complete
        while not recorder.frames:
            time.sleep(0.1)

        # Wait for recording to stop
        while recorder.recording:
            time.sleep(0.1)

        # Get audio data
        audio_data, sample_rate = recorder.get_audio_data()

        # Transcribe audio
        if audio_data is not None:
            return transcribe_audio(audio_data, sample_rate)
        else:
            return ""

    finally:
        # Clean up resources
        recorder.cleanup()
