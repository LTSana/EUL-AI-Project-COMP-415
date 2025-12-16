"""
Flask Text-to-Speech Application
Main application file with routes and API endpoints
"""
from flask import Flask, render_template, request, jsonify, send_file
from flask_cors import CORS
from pathlib import Path
import logging
import uuid
import os
from datetime import datetime

from config import get_config
from utils.tts_engine import TTSEngine
from utils.text_processor import TextProcessor

# Initialize Flask app
app = Flask(__name__)
app.config.from_object(get_config())

# Enable CORS for API endpoints
CORS(app)

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Initialize TTS Engine (lazy loading)
tts_engine = None

def get_tts_engine():
    """
    Get or initialize TTS Engine (singleton pattern)
    Lazy loading to avoid loading model on import
    """
    global tts_engine
    if tts_engine is None:
        logger.info("Initializing TTS Engine...")
        device = "cuda" if app.config['USE_GPU'] else "cpu"
        tts_engine = TTSEngine(
            model_name=app.config['MODEL_NAME'],
            device=device,
            cache_dir=app.config['MODEL_CACHE_DIR']
        )
        logger.info("TTS Engine initialized successfully")
    return tts_engine

# Ensure output directory exists
app.config['AUDIO_OUTPUT_DIR'].mkdir(parents=True, exist_ok=True)

# ==================== ROUTES ====================

@app.route('/')
def index():
    """Main page"""
    return render_template('index.html')

@app.route('/about')
def about():
    """About page"""
    return render_template('about.html')

@app.route('/health')
def health():
    """Health check endpoint"""
    return jsonify({
        'status': 'healthy',
        'model': app.config['MODEL_NAME'],
        'device': 'cuda' if app.config['USE_GPU'] else 'cpu'
    })

# ==================== API ENDPOINTS ====================

@app.route('/api/synthesize', methods=['POST'])
def synthesize():
    """
    Main TTS synthesis endpoint
    
    Request JSON:
        {
            "text": "Text to convert to speech",
            "voice_preset": "v2/en_speaker_6" (optional)
        }
    
    Returns:
        JSON with audio file URL or error message
    """
    try:
        # Get JSON data
        data = request.get_json()
        
        if not data or 'text' not in data:
            return jsonify({
                'success': False,
                'error': 'No text provided'
            }), 400
        
        text = data.get('text', '')
        voice_preset = data.get('voice_preset', None)
        
        # Validate text
        is_valid, error_msg = TextProcessor.validate_text(
            text,
            max_length=app.config['MAX_TEXT_LENGTH']
        )
        
        if not is_valid:
            return jsonify({
                'success': False,
                'error': error_msg
            }), 400
        
        # Preprocess text
        processed_text = TextProcessor.preprocess_for_tts(
            text,
            max_length=app.config['MAX_TEXT_LENGTH']
        )
        
        logger.info(f"Synthesizing text: {processed_text[:50]}...")
        
        # Generate unique filename
        audio_id = str(uuid.uuid4())
        requested_format = app.config['AUDIO_FORMAT']
        audio_filename = f"{audio_id}.{requested_format}"
        audio_path = app.config['AUDIO_OUTPUT_DIR'] / audio_filename
        
        # Get TTS engine and generate speech
        engine = get_tts_engine()
        actual_output_path = engine.text_to_speech_file(
            processed_text,
            audio_path,
            voice_preset=voice_preset
        )
        
        # Use actual output filename (in case format changed due to fallback)
        actual_filename = audio_filename
        
        # Estimate duration
        estimated_duration = TextProcessor.estimate_duration(processed_text)
        
        # Return success response
        return jsonify({
            'success': True,
            'audio_url': f'/audio/{actual_filename}',
            'audio_id': audio_id,
            'text': processed_text,
            'estimated_duration': estimated_duration,
            'timestamp': datetime.now().isoformat()
        })
        
    except Exception as e:
        logger.error(f"Error in synthesis: {e}", exc_info=True)
        return jsonify({
            'success': False,
            'error': f'Synthesis failed: {str(e)}'
        }), 500

@app.route('/audio/<filename>')
def serve_audio(filename):
    """
    Serve generated audio files
    
    Args:
        filename: Audio file name
    """
    try:
        audio_path = app.config['AUDIO_OUTPUT_DIR'] / filename
        
        if not audio_path.exists():
            return jsonify({
                'success': False,
                'error': 'Audio file not found'
            }), 404
        
        # Check file size for debugging
        file_size = audio_path.stat().st_size
        logger.info(f"Serving audio file: {filename}, size: {file_size} bytes")
        
        # Determine MIME type based on file extension
        if filename.lower().endswith('.mp3'):
            mimetype = 'audio/mpeg'
        elif filename.lower().endswith('.wav'):
            mimetype = 'audio/wav'
        else:
            mimetype = 'audio/wav'  # default
        
        return send_file(
            audio_path,
            mimetype=mimetype,
            as_attachment=False,
            download_name=filename
        )
        
    except Exception as e:
        logger.error(f"Error serving audio: {e}")
        return jsonify({
            'success': False,
            'error': 'Failed to serve audio file'
        }), 500

@app.route('/api/voices', methods=['GET'])
def get_voices():
    """
    Get available voice presets
    
    Returns:
        JSON list of available voices
    """
    # Bark voice presets
    voices = [
        {'id': None, 'name': 'Default', 'language': 'en'},
        {'id': 'v2/en_speaker_0', 'name': 'Speaker 0 (Male)', 'language': 'en'},
        {'id': 'v2/en_speaker_1', 'name': 'Speaker 1 (Male)', 'language': 'en'},
        {'id': 'v2/en_speaker_2', 'name': 'Speaker 2 (Male)', 'language': 'en'},
        {'id': 'v2/en_speaker_3', 'name': 'Speaker 3 (Male)', 'language': 'en'},
        {'id': 'v2/en_speaker_4', 'name': 'Speaker 4 (Male)', 'language': 'en'},
        {'id': 'v2/en_speaker_5', 'name': 'Speaker 5 (Female)', 'language': 'en'},
        {'id': 'v2/en_speaker_6', 'name': 'Speaker 6 (Female)', 'language': 'en'},
        {'id': 'v2/en_speaker_7', 'name': 'Speaker 7 (Female)', 'language': 'en'},
        {'id': 'v2/en_speaker_8', 'name': 'Speaker 8 (Female)', 'language': 'en'},
        {'id': 'v2/en_speaker_9', 'name': 'Speaker 9 (Female)', 'language': 'en'},
    ]
    
    return jsonify({
        'success': True,
        'voices': voices
    })

@app.route('/api/test', methods=['GET'])
def test_tts():
    """
    Test endpoint to verify TTS is working
    Generates a simple test audio
    """
    try:
        test_text = "Hello! This is a test of the text to speech system."
        
        # Generate test audio
        audio_id = "test"
        audio_filename = f"{audio_id}.{app.config['AUDIO_FORMAT']}"
        audio_path = app.config['AUDIO_OUTPUT_DIR'] / audio_filename
        
        engine = get_tts_engine()
        engine.text_to_speech_file(test_text, audio_path)
        
        return jsonify({
            'success': True,
            'message': 'TTS test successful',
            'audio_url': f'/audio/{audio_filename}'
        })
        
    except Exception as e:
        logger.error(f"Test failed: {e}", exc_info=True)
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

# ==================== ERROR HANDLERS ====================

@app.errorhandler(404)
def not_found(e):
    """Handle 404 errors"""
    if request.path.startswith('/api/'):
        return jsonify({'success': False, 'error': 'Endpoint not found'}), 404
    return render_template('index.html'), 404

@app.errorhandler(500)
def internal_error(e):
    """Handle 500 errors"""
    logger.error(f"Internal error: {e}", exc_info=True)
    if request.path.startswith('/api/'):
        return jsonify({'success': False, 'error': 'Internal server error'}), 500
    return "Internal Server Error", 500

# ==================== CLEANUP TASK ====================

def cleanup_old_files():
    """
    Remove old audio files (should be run periodically)
    In production, use a scheduler like APScheduler
    """
    try:
        audio_dir = app.config['AUDIO_OUTPUT_DIR']
        retention_time = app.config['AUDIO_RETENTION_TIME']
        current_time = datetime.now().timestamp()
        
        for audio_file in audio_dir.glob('*.*'):
            # Only process audio files (wav, mp3, etc.)
            if audio_file.suffix.lower() not in ['.wav', '.mp3']:
                continue
            file_age = current_time - audio_file.stat().st_mtime
            if file_age > retention_time:
                audio_file.unlink()
                logger.info(f"Deleted old file: {audio_file.name}")
                
    except Exception as e:
        logger.error(f"Cleanup error: {e}")

# ==================== MAIN ====================

if __name__ == '__main__':
    # Note: In production, use a proper WSGI server like Gunicorn
    # gunicorn -w 4 -b 0.0.0.0:5000 app:app
    
    app.run(
        host='0.0.0.0',
        port=5000,
        debug=app.config['DEBUG']
    )