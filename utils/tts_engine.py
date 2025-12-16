"""
TTS Engine Module - Handles text-to-speech generation using Bark
"""
import torch
import scipy
import numpy as np
from transformers import AutoProcessor, BarkModel
from pathlib import Path
import logging
import tempfile
import os
try:
    from pydub import AudioSegment
    PYDUB_AVAILABLE = True
except ImportError:
    PYDUB_AVAILABLE = False

logger = logging.getLogger(__name__)

class TTSEngine:
    """
    Text-to-Speech Engine using Bark model
    Handles model loading, text preprocessing, and audio generation
    """
    
    def __init__(self, model_name="suno/bark-small", device=None, cache_dir=None):
        """
        Initialize TTS Engine
        
        Args:
            model_name: Hugging Face model identifier
            device: 'cuda' or 'cpu', auto-detected if None
            cache_dir: Directory to cache model files
        """
        self.model_name = model_name
        
        # Auto-detect device
        if device is None:
            self.device = "cuda" if torch.cuda.is_available() else "cpu"
        else:
            self.device = device
            
        logger.info(f"Initializing TTS Engine with device: {self.device}")
        
        self.cache_dir = cache_dir
        self.model = None
        self.processor = None
        self._load_model()
    
    def _load_model(self):
        """Load the TTS model and processor"""
        try:
            logger.info(f"Loading model: {self.model_name}")
            
            # Load processor (tokenizer)
            self.processor = AutoProcessor.from_pretrained(
                self.model_name,
                cache_dir=self.cache_dir
            )
            
            # Load model
            # Note: PyTorch 2.6+ fixes the security vulnerability, so we can use default loading
            self.model = BarkModel.from_pretrained(
                self.model_name,
                cache_dir=self.cache_dir
            )
            
            # Set pad_token_id if not already set (prevents warning)
            # Bark models typically use eos_token_id as pad_token_id (usually 10000)
            if hasattr(self.model, 'generation_config') and self.model.generation_config is not None:
                if not hasattr(self.model.generation_config, 'pad_token_id') or self.model.generation_config.pad_token_id is None:
                    # Try to use eos_token_id first, fallback to 10000 (common Bark default)
                    if hasattr(self.model.generation_config, 'eos_token_id') and self.model.generation_config.eos_token_id is not None:
                        self.model.generation_config.pad_token_id = self.model.generation_config.eos_token_id
                    else:
                        self.model.generation_config.pad_token_id = 10000
            
            # Move model to device
            self.model = self.model.to(self.device)
            
            # Set to evaluation mode
            self.model.eval()
            
            logger.info("Model loaded successfully")
            
        except Exception as e:
            logger.error(f"Error loading model: {e}")
            raise
    
    def preprocess_text(self, text, max_length=500):
        """
        Preprocess text for TTS generation
        
        Args:
            text: Input text string
            max_length: Maximum text length
            
        Returns:
            Preprocessed text
        """
        # Remove extra whitespace
        text = " ".join(text.split())
        
        # Truncate if too long
        if len(text) > max_length:
            text = text[:max_length]
            logger.warning(f"Text truncated to {max_length} characters")
        
        # Add period if missing (helps with prosody)
        if text and text[-1] not in '.!?':
            text += '.'
        
        return text
    
    def split_text(self, text, max_chunk_length=250):
        """
        Split long text into chunks (Bark has ~14 second limit per generation)
        
        Args:
            text: Input text
            max_chunk_length: Maximum characters per chunk
            
        Returns:
            List of text chunks
        """
        # Split by sentences
        sentences = text.replace('!', '.').replace('?', '.').split('.')
        sentences = [s.strip() + '.' for s in sentences if s.strip()]
        
        chunks = []
        current_chunk = ""
        
        for sentence in sentences:
            if len(current_chunk) + len(sentence) <= max_chunk_length:
                current_chunk += " " + sentence
            else:
                if current_chunk:
                    chunks.append(current_chunk.strip())
                current_chunk = sentence
        
        if current_chunk:
            chunks.append(current_chunk.strip())
        
        return chunks
    
    def generate_speech(self, text, voice_preset=None):
        """
        Generate speech from text
        
        Args:
            text: Input text string
            voice_preset: Optional voice preset (e.g., "v2/en_speaker_6")
            
        Returns:
            tuple: (audio_array, sample_rate)
        """
        try:
            # Preprocess text
            text = self.preprocess_text(text)
            
            # Check if text needs to be split
            if len(text) > 250:
                return self._generate_long_speech(text, voice_preset)
            
            # Prepare inputs
            inputs = self.processor(
                text,
                voice_preset=voice_preset,
                return_tensors="pt"
            )
            
            # Move inputs to device
            inputs = {k: v.to(self.device) for k, v in inputs.items()}
            
            # Generate speech
            # pad_token_id is handled in generation_config, so no need to pass it explicitly
            with torch.no_grad():
                speech_output = self.model.generate(**inputs)
            
            # Convert to numpy array
            audio_array = speech_output[0].cpu().numpy()
            
            # Ensure audio is 1D array (flatten if needed)
            if audio_array.ndim > 1:
                audio_array = audio_array.flatten()
            
            # Get sample rate
            sample_rate = self.model.generation_config.sample_rate
            
            logger.info(f"Generated audio: {len(audio_array)} samples at {sample_rate}Hz")
            
            return audio_array, sample_rate
            
        except Exception as e:
            logger.error(f"Error generating speech: {e}")
            raise
    
    def _generate_long_speech(self, text, voice_preset=None):
        """
        Generate speech for long text by splitting into chunks
        
        Args:
            text: Long input text
            voice_preset: Optional voice preset
            
        Returns:
            tuple: (concatenated_audio_array, sample_rate)
        """
        chunks = self.split_text(text)
        logger.info(f"Split text into {len(chunks)} chunks")
        
        audio_chunks = []
        sample_rate = None
        
        for i, chunk in enumerate(chunks):
            logger.info(f"Generating chunk {i+1}/{len(chunks)}")
            
            inputs = self.processor(
                chunk,
                voice_preset=voice_preset,
                return_tensors="pt"
            )
            
            inputs = {k: v.to(self.device) for k, v in inputs.items()}
            
            with torch.no_grad():
                speech_output = self.model.generate(**inputs)
            
            audio_chunk = speech_output[0].cpu().numpy()
            # Ensure audio is 1D array (flatten if needed)
            if audio_chunk.ndim > 1:
                audio_chunk = audio_chunk.flatten()
            audio_chunks.append(audio_chunk)
            
            if sample_rate is None:
                sample_rate = self.model.generation_config.sample_rate
        
        # Concatenate all chunks
        full_audio = np.concatenate(audio_chunks)
        
        logger.info(f"Concatenated {len(chunks)} chunks into full audio")
        
        return full_audio, sample_rate
    
    def save_audio(self, audio_array, sample_rate, output_path):
        """
        Save audio to file (supports WAV and MP3 formats)
        
        Args:
            audio_array: Audio data as numpy array
            sample_rate: Sample rate in Hz
            output_path: Output file path (extension determines format)
        """
        try:
            output_path = Path(output_path)
            output_path.parent.mkdir(parents=True, exist_ok=True)

            # Ensure sample rate is an int
            sample_rate = int(sample_rate)

            # Ensure audio is 1D array
            if audio_array.ndim > 1:
                audio_array = audio_array.flatten()
            
            # Get file extension
            file_ext = output_path.suffix.lower()
            
            # Bark returns float audio in range [-1, 1]; convert to int16 for broad player support
            if audio_array.dtype != np.int16:
                # Normalize to [-1, 1] if needed
                if audio_array.dtype in [np.float32, np.float64]:
                    clipped = np.clip(audio_array, -1.0, 1.0)
                    audio_array = (clipped * 32767.0).astype(np.int16)
                else:
                    # If already integer, just ensure it's int16
                    audio_array = audio_array.astype(np.int16)
            
            # Save based on format
            if file_ext == '.mp3':
                if not PYDUB_AVAILABLE:
                    logger.warning("pydub not available, falling back to WAV format")
                    # Fall back to WAV by changing extension
                    output_path = output_path.with_suffix('.wav')
                    file_ext = '.wav'
                else:
                    # Save as MP3 using pydub
                    # First, save as temporary WAV file
                    with tempfile.NamedTemporaryFile(suffix='.wav', delete=False) as temp_wav:
                        temp_wav_path = temp_wav.name
                        
                    try:
                        # Write WAV file first
                        scipy.io.wavfile.write(temp_wav_path, sample_rate, audio_array)
                        
                        # Convert WAV to MP3 using pydub (requires ffmpeg)
                        try:
                            audio_segment = AudioSegment.from_wav(temp_wav_path)
                            audio_segment.export(str(output_path), format="mp3", bitrate="192k")
                            logger.info(f"Audio saved as MP3 to: {output_path}")
                            return  # Successfully saved as MP3, exit early
                        except Exception as e:
                            logger.warning(f"MP3 conversion failed (ffmpeg may not be installed): {e}")
                            logger.warning(f"Falling back to WAV format. To enable MP3, install ffmpeg:")
                            logger.warning(f"  Windows: Download from https://ffmpeg.org/download.html and add to PATH")
                            logger.warning(f"  Linux: sudo apt-get install ffmpeg")
                            logger.warning(f"  Mac: brew install ffmpeg")
                            # Fall back to WAV by changing extension
                            output_path = output_path.with_suffix('.wav')
                            file_ext = '.wav'
                        
                    finally:
                        # Clean up temporary WAV file
                        if os.path.exists(temp_wav_path):
                            os.unlink(temp_wav_path)
            
            # Save as WAV (either requested format or fallback)
            scipy.io.wavfile.write(
                str(output_path),
                rate=sample_rate,
                data=audio_array
            )
            logger.info(f"Audio saved as WAV to: {output_path}")

        except Exception as e:
            logger.error(f"Error saving audio: {e}")
            raise
    
    def text_to_speech_file(self, text, output_path, voice_preset=None):
        """
        Complete pipeline: text to speech file
        
        Args:
            text: Input text
            output_path: Output file path
            voice_preset: Optional voice preset
            
        Returns:
            Path to generated audio file (may be different from input if format fallback occurred)
        """
        # Generate speech
        audio_array, sample_rate = self.generate_speech(text, voice_preset)
        
        # Save to file (may return different path if format fallback occurs)
        output_path = Path(output_path)
        actual_path = self.save_audio(audio_array, sample_rate, output_path)
        
        # Return the actual path that was used (in case it was changed due to fallback)
        return actual_path