from pathlib import Path
import os
import datetime

# --- Base Configuration ---
# All environments will inherit these settings
class Config:
    """Base configuration class with default settings."""

    # 1. Flask Core Settings
    # Use a strong, random key in production
    SECRET_KEY = os.environ.get('SECRET_KEY', 'default-dev-secret-key-please-change')
    
    # Static and Template folders (usually default but good to define)
    TEMPLATES_FOLDER = 'templates'
    STATIC_FOLDER = 'static'

    # 2. Text-to-Speech (Suno Bark) Settings
    MODEL_NAME = 'suno/bark'
    MODEL_CACHE_DIR = Path('./.model_cache') # Directory for huggingface model downloads
    
    # Hardware/Device Settings
    # Auto-detect CUDA availability for GPU usage
    USE_GPU = bool(os.environ.get('USE_GPU', 'False').lower() == 'true')
    
    # 3. Audio Output Settings
    AUDIO_OUTPUT_DIR = Path('./audio_output') # Directory to save generated audio files
    AUDIO_FORMAT = 'wav' # File format for output (e.g., 'wav', 'mp3')
    
    # Retention Policy (for cleanup_old_files)
    # 60 * 60 * 24 = 86400 seconds (1 day)
    # Set to a higher value or use an external scheduler in production
    AUDIO_RETENTION_TIME = int(os.environ.get('AUDIO_RETENTION_TIME_SECONDS', 86400)) # 1 day in seconds
    
    # 4. API & Text Processing Limits
    MAX_TEXT_LENGTH = int(os.environ.get('MAX_TEXT_LENGTH', 2000)) # Max characters for synthesis
    CORS_HEADERS = 'Content-Type'


# --- Development Configuration ---
class DevelopmentConfig(Config):
    """Development configuration: debugging enabled, less restrictive."""
    
    # 1. Flask Core Settings
    DEBUG = True
    TESTING = True # Enable testing mode
    ENV = 'development'

    # Shorter retention for easier development cleanup
    AUDIO_RETENTION_TIME = 3600 # 1 hour in seconds
    

# --- Production Configuration ---
class ProductionConfig(Config):
    """Production configuration: debugging disabled, robust security/performance."""
    
    # 1. Flask Core Settings
    DEBUG = False
    TESTING = False
    ENV = 'production'
    
    # Ensure a strong secret key is always set in the environment
    SECRET_KEY = os.environ.get('SECRET_KEY')
    
    # 2. API Limits (Potentially more restrictive in high-volume production)
    # MAX_TEXT_LENGTH = 1000 # Example: if you need stricter limits
    
    # 3. Retention Policy (Set longer or manage with a separate service)
    # AUDIO_RETENTION_TIME = 604800 # 7 days in seconds


# --- Helper Function ---
def get_config(env_name=None):
    """
    Returns the appropriate configuration class based on FLASK_ENV environment variable.
    """
    if env_name is None:
        env_name = os.environ.get('FLASK_ENV', 'development').lower()

    if env_name == 'production':
        return ProductionConfig
    elif env_name == 'development':
        return DevelopmentConfig
    else:
        # Default to DevelopmentConfig for unknown/unset envs
        return DevelopmentConfig

# Example usage in app.py: app.config.from_object(get_config())