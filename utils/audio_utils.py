"""
Audio Utilities
Helper functions for audio file manipulation
"""
import soundfile as sf
import numpy as np
from pathlib import Path
import logging

logger = logging.getLogger(__name__)

class AudioUtils:
    """Audio processing utilities"""
    
    @staticmethod
    def get_audio_info(file_path):
        """
        Get information about an audio file
        
        Args:
            file_path: Path to audio file
            
        Returns:
            Dictionary with audio information
        """
        try:
            file_path = Path(file_path)
            
            if not file_path.exists():
                return None
            
            info = sf.info(str(file_path))
            
            return {
                'duration': info.duration,
                'sample_rate': info.samplerate,
                'channels': info.channels,
                'format': info.format,
                'subtype': info.subtype,
                'size_bytes': file_path.stat().st_size
            }
            
        except Exception as e:
            logger.error(f"Error getting audio info: {e}")
            return None
    
    @staticmethod
    def normalize_audio(audio_array, target_level=-20.0):
        """
        Normalize audio to target dB level
        
        Args:
            audio_array: Audio data as numpy array
            target_level: Target level in dB
            
        Returns:
            Normalized audio array
        """
        try:
            # Calculate current RMS
            rms = np.sqrt(np.mean(audio_array**2))
            
            # Calculate scaling factor
            current_db = 20 * np.log10(rms) if rms > 0 else -np.inf
            scale = 10**((target_level - current_db) / 20)
            
            # Apply normalization
            normalized = audio_array * scale
            
            # Clip to prevent distortion
            normalized = np.clip(normalized, -1.0, 1.0)
            
            return normalized
            
        except Exception as e:
            logger.error(f"Error normalizing audio: {e}")
            return audio_array
    
    @staticmethod
    def convert_sample_rate(audio_array, orig_sr, target_sr):
        """
        Convert audio to different sample rate
        
        Args:
            audio_array: Audio data
            orig_sr: Original sample rate
            target_sr: Target sample rate
            
        Returns:
            Resampled audio array
        """
        try:
            import librosa
            
            if orig_sr == target_sr:
                return audio_array
            
            resampled = librosa.resample(
                audio_array,
                orig_sr=orig_sr,
                target_sr=target_sr
            )
            
            return resampled
            
        except Exception as e:
            logger.error(f"Error resampling audio: {e}")
            return audio_array
    
    @staticmethod
    def trim_silence(audio_array, sample_rate, threshold_db=-40):
        """
        Trim silence from beginning and end of audio
        
        Args:
            audio_array: Audio data
            sample_rate: Sample rate
            threshold_db: Silence threshold in dB
            
        Returns:
            Trimmed audio array
        """
        try:
            import librosa
            
            trimmed, _ = librosa.effects.trim(
                audio_array,
                top_db=-threshold_db
            )
            
            return trimmed
            
        except Exception as e:
            logger.error(f"Error trimming silence: {e}")
            return audio_array
    
    @staticmethod
    def add_fade(audio_array, sample_rate, fade_in_duration=0.1, fade_out_duration=0.1):
        """
        Add fade in/out to audio
        
        Args:
            audio_array: Audio data
            sample_rate: Sample rate
            fade_in_duration: Fade in duration in seconds
            fade_out_duration: Fade out duration in seconds
            
        Returns:
            Audio with fades applied
        """
        try:
            audio_copy = audio_array.copy()
            
            # Fade in
            fade_in_samples = int(fade_in_duration * sample_rate)
            fade_in_samples = min(fade_in_samples, len(audio_copy) // 2)
            
            for i in range(fade_in_samples):
                audio_copy[i] *= (i / fade_in_samples)
            
            # Fade out
            fade_out_samples = int(fade_out_duration * sample_rate)
            fade_out_samples = min(fade_out_samples, len(audio_copy) // 2)
            
            start_idx = len(audio_copy) - fade_out_samples
            for i in range(fade_out_samples):
                audio_copy[start_idx + i] *= (1.0 - (i / fade_out_samples))
            
            return audio_copy
            
        except Exception as e:
            logger.error(f"Error adding fade: {e}")
            return audio_array