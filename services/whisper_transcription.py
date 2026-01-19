"""Whisper transcription service for voice input."""

import os
from datetime import datetime
from openai import OpenAI
from langsmith import traceable
from config import Config
from models import db
from models.voice_input_metrics import VoiceInputMetrics

# Set up LangSmith environment variables
os.environ["LANGCHAIN_TRACING_V2"] = Config.LANGCHAIN_TRACING_V2
os.environ["LANGCHAIN_API_KEY"] = Config.LANGCHAIN_API_KEY
os.environ["LANGCHAIN_PROJECT"] = Config.LANGCHAIN_PROJECT


@traceable(name="whisper_transcribe", metadata={"feature": "voice_input"})
def transcribe_audio(audio_data, user_id=None, session_id=None):
    """
    Transcribe audio using OpenAI Whisper API.

    Args:
        audio_data: Audio file bytes or file-like object
        user_id: Optional user ID for metrics tracking
        session_id: Optional session ID for metrics tracking

    Returns:
        Dict with:
            - success: bool
            - transcription: str (if success)
            - duration_seconds: int (estimated from audio)
            - error: str (if not success)
    """
    api_key = Config.OPENAI_API_KEY

    if not api_key:
        return {
            'success': False,
            'error': "Voice transcription is not available. Please configure OPENAI_API_KEY."
        }

    try:
        client = OpenAI(api_key=api_key)

        # Create a temporary file-like object for the API
        # The audio_data should be bytes from the frontend
        response = client.audio.transcriptions.create(
            model="whisper-1",
            file=("audio.webm", audio_data, "audio/webm"),
            response_format="verbose_json"
        )

        transcription = response.text
        duration_seconds = int(response.duration) if hasattr(response, 'duration') else None

        # Track metrics if user_id provided
        if user_id:
            VoiceInputMetrics.record_acceptance(
                user_id=user_id,
                session_id=session_id,
                duration_seconds=duration_seconds
            )

        return {
            'success': True,
            'transcription': transcription,
            'duration_seconds': duration_seconds
        }

    except Exception as e:
        return {
            'success': False,
            'error': f"Error transcribing audio: {str(e)}"
        }


def record_voice_offer(user_id, session_id=None):
    """Record that voice input was offered to the user."""
    return VoiceInputMetrics.record_offer(user_id, session_id)


def record_voice_decline(user_id, session_id=None):
    """Record that user declined voice input."""
    return VoiceInputMetrics.record_decline(user_id, session_id)


def get_user_voice_stats(user_id):
    """Get voice input statistics for a user."""
    return VoiceInputMetrics.get_user_stats(user_id)


def get_global_skip_rate():
    """Get the global voice input skip rate."""
    return VoiceInputMetrics.get_skip_rate()
