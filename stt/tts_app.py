#!/usr/bin/env python3
"""
Simple TTS - A standalone text-to-speech script using OpenAI.fm

Usage:
  python tts_app.py "Your text here" [voice] [emotion] [--volume VOLUME] [--save] [output_file]
  python tts_app.py --interactive

Examples:
  python tts_app.py "Hello world"                                # Just play audio with nova voice
  python tts_app.py "How are you today?" echo happy              # Specify different voice and emotion
  python tts_app.py "Volume control" --volume 0.8                # Control volume
  python tts_app.py "Save this" --save                           # Save to auto-named file
  python tts_app.py "Save as custom name" my_custom_file.mp3     # Save to specific file
  python tts_app.py "Full example" nova excited --volume 0.7 --save output.mp3

Available voices:
  alloy, echo, fable, onyx, nova (default), shimmer, ash, coral, sage

Available emotions/styles:
  happy, sad, excited, calm, angry, fearful, surprised, neutral,
  professional, friendly, enthusiastic, serious, whisper, shouting

Options:
  --volume, -v VALUE  Set playback volume (0.0 to 1.0, default: 1.0)
  --save, -s          Save audio to file (default: don't save)
  output_file         Specify output filename (implies --save)
"""

import sys
from stt import (
    generate_speech, save_audio, play_audio,
    SUPPORTED_VOICES, DEFAULT_VOICE,
    SUPPORTED_EMOTIONS, DEFAULT_EMOTION,
    DEFAULT_SPEED
)

def main():
    """Main function to handle command line arguments and generate speech"""
    # Print help if no arguments or help requested
    if len(sys.argv) == 1 or sys.argv[1] in ['-h', '--help', 'help']:
        print(__doc__)
        return

    # Check for interactive mode
    if sys.argv[1] == '--interactive':
        interactive_mode()
        return

    # Get text from command line
    text = sys.argv[1]

    # Parse arguments based on their validity
    args = sys.argv[2:]
    voice = DEFAULT_VOICE
    emotion = DEFAULT_EMOTION
    volume = 1.0  # Default volume
    speed = DEFAULT_SPEED  # Default speed (1.25x)
    save_to_file = False  # Default is not to save
    output_file = None

    # Process arguments
    i = 0
    while i < len(args):
        arg = args[i]

        # Check for volume flag
        if arg == '--volume' or arg == '-v':
            if i + 1 < len(args):
                try:
                    volume = float(args[i + 1])
                    volume = max(0.0, min(1.0, volume))  # Ensure it's in valid range
                    i += 2
                    continue
                except ValueError:
                    print(f"Invalid volume value: {args[i + 1]}, using default: {volume}")
                    i += 2
                    continue

        # Check for speed flag
        elif arg == '--speed' or arg == '-sp':
            if i + 1 < len(args):
                try:
                    speed = float(args[i + 1])
                    if speed <= 0:
                        print(f"Speed must be positive, using default: {speed}")
                        speed = DEFAULT_SPEED
                    i += 2
                    continue
                except ValueError:
                    print(f"Invalid speed value: {args[i + 1]}, using default: {speed}")
                    i += 2
                    continue

        # Check for save flag
        elif arg == '--save' or arg == '-s':
            save_to_file = True
            i += 1
            continue

        # Check for other arguments
        elif arg in SUPPORTED_VOICES and voice == DEFAULT_VOICE:
            voice = arg
        elif arg in SUPPORTED_EMOTIONS and emotion == DEFAULT_EMOTION:
            emotion = arg
        elif output_file is None and not arg in SUPPORTED_VOICES and not arg in SUPPORTED_EMOTIONS:
            output_file = arg
            save_to_file = True  # If output file is specified, we'll save

        i += 1

    # If saving is enabled but no output file was specified, generate one based on voice and emotion
    if save_to_file and output_file is None:
        output_file = f"{voice}_{emotion}_output.mp3"

    try:
        # Generate speech with emotion and speed
        audio_bytes = generate_speech(text, voice, emotion, speed)

        # Save audio to file only if requested
        if save_to_file and output_file:
            save_audio(audio_bytes, output_file)

        # Play the audio with specified volume
        play_audio(audio_bytes, volume)

    except Exception as e:
        print(f"Error: {e}")
        sys.exit(1)

def interactive_mode():
    """Run in interactive mode, allowing the user to test different voices and emotions"""
    print("=== Interactive TTS Mode ===")
    print("Type 'exit' or 'quit' to exit")
    print(f"Available voices: {', '.join(SUPPORTED_VOICES)}")
    print(f"Default voice: {DEFAULT_VOICE}")
    print(f"Available emotions: {', '.join(SUPPORTED_EMOTIONS)}")
    print(f"Default emotion: {DEFAULT_EMOTION}")
    print("Volume: 0.0 (silent) to 1.0 (maximum)")
    print("Speed: Default is 1.25x (1.0 is normal speed)")
    print("Save: yes/no to save audio files")
    print()

    # Default settings
    volume = 1.0
    speed = DEFAULT_SPEED
    save_to_file = False

    while True:
        # Get text input
        text = input("Enter text (or 'exit' to quit): ").strip()
        if text.lower() in ['exit', 'quit', '']:
            break

        # Get voice input
        voice_input = input(f"Enter voice [{DEFAULT_VOICE}]: ").strip()
        voice = voice_input if voice_input in SUPPORTED_VOICES else DEFAULT_VOICE

        # Get emotion input
        emotion_input = input(f"Enter emotion/style [{DEFAULT_EMOTION}]: ").strip()
        emotion = emotion_input if emotion_input in SUPPORTED_EMOTIONS else DEFAULT_EMOTION

        # Get volume input
        volume_input = input(f"Enter volume (0.0-1.0) [{volume}]: ").strip()
        try:
            if volume_input:
                volume = float(volume_input)
                volume = max(0.0, min(1.0, volume))  # Ensure it's in valid range
        except ValueError:
            print(f"Invalid volume, using {volume}")

        # Get speed input
        speed_input = input(f"Enter speed (e.g., 1.0=normal, 1.25=faster) [{speed}]: ").strip()
        try:
            if speed_input:
                speed = float(speed_input)
                if speed <= 0:
                    print(f"Speed must be positive, using {DEFAULT_SPEED}")
                    speed = DEFAULT_SPEED
        except ValueError:
            print(f"Invalid speed, using {speed}")

        # Ask if user wants to save the file
        save_input = input(f"Save audio file? (yes/no) [{save_to_file}]: ").strip().lower()
        if save_input in ['yes', 'y', 'true', '1']:
            save_to_file = True
        elif save_input in ['no', 'n', 'false', '0']:
            save_to_file = False

        try:
            # Generate speech with emotion and speed
            audio_bytes = generate_speech(text, voice, emotion, speed)

            # Save audio to file only if requested
            if save_to_file:
                output_file = f"{voice}_{emotion}_speed{speed}_output.mp3"
                save_audio(audio_bytes, output_file)

            # Play the audio with specified volume
            play_audio(audio_bytes, volume)

        except Exception as e:
            print(f"Error: {e}")

    print("Goodbye!")

if __name__ == "__main__":
    main()
