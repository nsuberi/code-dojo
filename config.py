"""Configuration settings for Code Dojo."""

import os
from dotenv import load_dotenv

load_dotenv()


class Config:
    """Application configuration."""

    SECRET_KEY = os.getenv('FLASK_SECRET_KEY', 'dev-secret-key-change-in-production')
    SQLALCHEMY_DATABASE_URI = os.getenv('DATABASE_URL', 'sqlite:///code_dojo.db')
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    ANTHROPIC_API_KEY = os.getenv('ANTHROPIC_API_KEY', '')

    # GitHub API
    # With token: 5000 req/hr, without: 60 req/hr
    GITHUB_API_BASE = 'https://api.github.com'
    GITHUB_TOKEN = os.getenv('GITHUB_TOKEN', None)

    # PR Validation Settings
    PR_BASE_VALIDATION_STRICT = True  # Enforce base repo must match starter repo
    PR_CACHE_DURATION = 3600  # Cache PR metadata for 1 hour (future enhancement)

    # Debug mode
    DEBUG = os.getenv('FLASK_DEBUG', '1') == '1'

    # Calendly scheduling
    CALENDLY_URL = os.getenv('CALENDLY_URL', '')  # e.g., https://calendly.com/instructor-name/30min

    # LangSmith configuration for tracing
    LANGCHAIN_TRACING_V2 = os.getenv('LANGCHAIN_TRACING_V2', 'true')
    LANGCHAIN_API_KEY = os.getenv('LANGSMITH_API_KEY', '')
    LANGCHAIN_PROJECT = os.getenv('LANGCHAIN_PROJECT', 'code-dojo')

    # OpenAI configuration for Whisper transcription
    OPENAI_API_KEY = os.getenv('OPENAI_API_KEY', os.getenv('OPENAPI_KEY', ''))

    # Architectural Analysis configuration
    ARCH_ANALYSIS_ENABLED = os.getenv('ARCH_ANALYSIS_ENABLED', 'true').lower() == 'true'
    ARCH_ANALYSIS_TIMEOUT = int(os.getenv('ARCH_ANALYSIS_TIMEOUT', '30'))  # seconds
    ARCH_SKIP_SMALL_PRS = os.getenv('ARCH_SKIP_SMALL_PRS', 'true').lower() == 'true'  # Skip if <5 files
    ARCH_DETAIL_LEVEL = os.getenv('ARCH_DETAIL_LEVEL', 'medium')  # basic/medium/deep
