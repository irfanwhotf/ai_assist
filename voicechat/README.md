# Optimized Voice Chat

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

## Requirements

- Python 3.8+
- PyTorch (with CUDA support recommended)
- Google Generative AI Python SDK
- Other dependencies listed in `requirements.txt`

## Setup

1. Install the required dependencies:
   ```
   pip install -r requirements.txt
   ```

2. Copy the `.env.template` file to `.env` and add your Gemini API key:
   ```
   cp .env.template .env
   ```

3. Edit the `.env` file to add your API key:
   ```
   GEMINI_API_KEY=your_api_key_here
   ```

4. Customize TTS settings in the `.env` file (optional):
   ```
   DEFAULT_VOICE=nova
   DEFAULT_EMOTION=neutral
   DEFAULT_SPEED=1.25
   ```

## Usage

Run the voice chat application:
```
python voice_chat.py
```

### Commands

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
