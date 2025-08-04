#!/bin/bash
# Simple TTS workaround using direct ElevenLabs API

API_KEY="${ELEVENLABS_API_KEY:-your_api_key_here}"
TEXT="${1:-Hello, this is a test message.}"
VOICE_ID="${2:-21m00Tcm4TlvDq8ikWAM}"  # Rachel voice by default

# Generate audio
curl -s -X POST "https://api.elevenlabs.io/v1/text-to-speech/$VOICE_ID" \
  -H "xi-api-key: $API_KEY" \
  -H "Content-Type: application/json" \
  -d "{\"text\": \"$TEXT\", \"model_id\": \"eleven_monolingual_v1\"}" \
  -o /tmp/tts_output.mp3

# Check if ffmpeg is available for adding silence padding
if command -v ffmpeg &> /dev/null; then
    # Add 0.5 seconds of silence at the end and ensure proper audio format
    ffmpeg -i /tmp/tts_output.mp3 \
           -af "apad=pad_dur=0.5" \
           -c:a libmp3lame -b:a 128k \
           -loglevel error \
           /tmp/tts_output_padded.mp3
    
    # Play with a small delay to ensure buffer is ready
    sleep 0.1
    afplay /tmp/tts_output_padded.mp3
    
    # Wait for playback to fully complete
    sleep 0.5
else
    # Fallback: play without padding but add delays
    sleep 0.1
    afplay /tmp/tts_output.mp3
    sleep 0.5
fi

# Clean up
rm -f /tmp/tts_output.mp3 /tmp/tts_output_padded.mp3