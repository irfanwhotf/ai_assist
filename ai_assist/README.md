# AI Voice Assistant

A high-performance voice assistant that uses speech-to-text, Gemini AI, and text-to-speech for natural conversation.

## Features

- **Speech-to-Text**: Uses faster_whisper for efficient speech recognition
- **AI Responses**: Powered by Google's Gemini 2.0 Flash API
- **Text-to-Speech**: High-quality voice synthesis with OpenAI.fm
- **Low Latency**: Optimized for minimal response time
- **CUDA Acceleration**: Uses GPU when available for faster processing
- **Shift+Spacebar Recording**: Press and hold to speak, release to process
- **Customizable**: Change voice, emotion, and speech speed on the fly

## Setup

1. Install the required dependencies:
   ```
   pip install -r requirements.txt
   ```

2. Make sure you have a `.env` file with your Gemini API key:
   ```
   GEMINI_API_KEY=your_api_key_here
   ```

3. Run the voice assistant:
   ```
   python run.py
   ```

   Or use the batch file from the parent directory:
   ```
   run_ai_assistant.bat
   ```

## Usage

1. Press and hold **Shift+Spacebar** to record your speech
2. Release Spacebar to stop recording and process your speech
3. The assistant will respond with speech

### Voice Commands

- Say "voice [name]" to change the voice (e.g., "voice echo")
- Say "emotion [name]" to change the emotion (e.g., "emotion happy")
- Say "speed [value]" to change the speech speed (e.g., "speed 1.5")
- Say "my name is [name]" or "call me [name]" to set your name
- Say "remember [information]" to store a memory
- Say "list memories" to see what Neura remembers
- Say "exit" or "quit" to end the session

### Available Voices

- alloy
- echo
- fable
- onyx
- nova (default)
- shimmer
- ash
- coral
- sage

### Available Emotions

- happy
- sad
- excited
- calm
- angry
- fearful
- surprised
- neutral (default)
- professional
- friendly
- enthusiastic
- serious
- whisper
- shouting
