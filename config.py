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

    # Debug mode
    DEBUG = os.getenv('FLASK_DEBUG', '1') == '1'

    # Calendly scheduling
    CALENDLY_URL = os.getenv('CALENDLY_URL', '')  # e.g., https://calendly.com/instructor-name/30min
