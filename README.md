# Optimized Voice Chat System

A high-performance chatbot that speaks its responses using text-to-speech technology with minimal latency.

## Features

- **Low Latency**: Optimized for fast response times
- **CUDA Acceleration**: Uses GPU acceleration when available
- **Direct Audio Playback**: Plays audio directly without creating temporary files
- **Audio Caching**: Caches audio for repeated phrases to reduce latency
- **Asynchronous Processing**: Uses async/await for concurrent operations
- **High-Quality TTS**: Uses OpenAI.fm for high-quality voice synthesis
- **Emotional Expression**: Supports various emotions and speaking styles
- **Customizable**: Easily change voice, emotion, and speech speed

## Quick Start

The easiest way to run the voice chat is to use the batch file:

```
run_voice_chat.bat
```

## Setup

1. Install the required dependencies:
   ```
   cd voicechat
   pip install -r requirements.txt
   ```

2. Add your Gemini API key to the `.env` file in the voicechat directory:
   ```
   GEMINI_API_KEY=your_actual_api_key
   ```

## Usage

During the chat session, you can use the following commands:

- `voice <name>` - Change the voice (e.g., `voice echo`)
- `emotion <name>` - Change the emotion (e.g., `emotion happy`)
- `speed <value>` - Change the speech speed (e.g., `speed 1.5`)
- `exit` or `quit` - End the chat session

## Available Voices

- alloy
- echo
- fable
- onyx
- nova (default)
- shimmer
- ash
- coral
- sage

## Available Emotions

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
