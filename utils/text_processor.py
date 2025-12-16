"""
Text Processing Module - Handles text preprocessing and validation for TTS
"""
import re
import logging

logger = logging.getLogger(__name__)


class TextProcessor:
    """
    Text processing utilities for text-to-speech
    Handles cleaning, abbreviation expansion, validation, and preprocessing
    """
    
    # Minimum text length for validation (in characters)
    MIN_TEXT_LENGTH = 3
    
    # Default words per minute for duration estimation
    DEFAULT_WPM = 150
    
    # Common abbreviations mapping
    ABBREVIATIONS = {
        'Dr.': 'Doctor',
        'Mr.': 'Mister',
        'Mrs.': 'Missus',
        'Ms.': 'Miss',
        'Prof.': 'Professor',
        'e.g.': 'for example',
        'i.e.': 'that is',
        'etc.': 'etcetera',
        'vs.': 'versus',
        'v.': 'versus',
        'vs': 'versus',
        'v': 'versus',
        'approx.': 'approximately',
        'min.': 'minimum',
        'max.': 'maximum',
        'No.': 'Number',
        'no.': 'number',
        'St.': 'Street',
        'Ave.': 'Avenue',
        'Blvd.': 'Boulevard',
        'Rd.': 'Road',
        'Ltd.': 'Limited',
        'Inc.': 'Incorporated',
        'Corp.': 'Corporation',
        'Co.': 'Company',
        'Jan.': 'January',
        'Feb.': 'February',
        'Mar.': 'March',
        'Apr.': 'April',
        'Aug.': 'August',
        'Sep.': 'September',
        'Sept.': 'September',
        'Oct.': 'October',
        'Nov.': 'November',
        'Dec.': 'December',
    }
    
    @staticmethod
    def clean_text(text):
        """
        Clean text by removing extra whitespace
        
        Args:
            text: Input text string (can be None or empty)
            
        Returns:
            Cleaned text string
        """
        if text is None:
            return ""
        
        if not isinstance(text, str):
            text = str(text)
        
        # Remove extra whitespace (multiple spaces, tabs, newlines)
        # Replace any sequence of whitespace characters with a single space
        text = re.sub(r'\s+', ' ', text)
        
        # Strip leading and trailing whitespace
        text = text.strip()
        
        return text
    
    @staticmethod
    def expand_abbreviations(text):
        """
        Expand common abbreviations to improve TTS pronunciation
        
        Args:
            text: Input text string
            
        Returns:
            Text with abbreviations expanded
        """
        if not text:
            return text
        
        # Sort abbreviations by length (longest first) to avoid partial matches
        sorted_abbrevs = sorted(
            TextProcessor.ABBREVIATIONS.items(),
            key=lambda x: len(x[0]),
            reverse=True
        )
        
        # Replace abbreviations (case-sensitive)
        for abbrev, expansion in sorted_abbrevs:
            # Escape special regex characters in the abbreviation
            escaped_abbrev = re.escape(abbrev)
            
            # Pattern: word boundary or start of string, then abbreviation,
            # then word boundary or end of string (but handle period specially)
            # For abbreviations ending with period, we need to match the period
            # but ensure it's not part of a larger word
            if abbrev.endswith('.'):
                # Match abbreviation followed by word boundary or end of string
                # The period is part of the abbreviation, so we check for space/end after it
                pattern = r'(?<!\w)' + escaped_abbrev + r'(?!\w)'
            else:
                # Regular word boundary for abbreviations without period
                pattern = r'\b' + escaped_abbrev + r'\b'
            
            text = re.sub(pattern, expansion, text)
        
        return text
    
    @staticmethod
    def validate_text(text, max_length=2000, min_length=None):
        """
        Validate text for TTS processing
        
        Args:
            text: Input text to validate
            max_length: Maximum allowed text length
            min_length: Minimum required text length (defaults to MIN_TEXT_LENGTH)
            
        Returns:
            tuple: (is_valid: bool, error_message: str or None)
        """
        if min_length is None:
            min_length = TextProcessor.MIN_TEXT_LENGTH
        
        # Check if text is None or empty
        if not text:
            return False, "Text cannot be empty"
        
        # Convert to string if needed
        if not isinstance(text, str):
            text = str(text)
        
        # Clean text first to get accurate length
        cleaned_text = TextProcessor.clean_text(text)
        
        if not cleaned_text:
            return False, "Text cannot be empty"
        
        # Check minimum length
        if len(cleaned_text) < min_length:
            return False, f"Text is too short (minimum {min_length} characters)"
        
        # Check maximum length
        if len(cleaned_text) > max_length:
            return False, f"Text is too long (maximum {max_length} characters, got {len(cleaned_text)})"
        
        return True, None
    
    @staticmethod
    def preprocess_for_tts(text, max_length=2000):
        """
        Complete preprocessing pipeline for TTS
        
        Steps:
        1. Clean text (remove extra whitespace)
        2. Expand abbreviations
        3. Clean again (abbreviation expansion might add spaces)
        4. Truncate if necessary
        
        Args:
            text: Input text string
            max_length: Maximum text length (will truncate if exceeded)
            
        Returns:
            Preprocessed text string
        """
        if not text:
            return ""
        
        # Step 1: Clean text
        processed_text = TextProcessor.clean_text(text)
        
        # Step 2: Expand abbreviations
        processed_text = TextProcessor.expand_abbreviations(processed_text)
        
        # Step 3: Clean again after abbreviation expansion
        processed_text = TextProcessor.clean_text(processed_text)
        
        # Step 4: Truncate if too long
        if len(processed_text) > max_length:
            # Try to truncate at a word boundary
            truncated = processed_text[:max_length]
            # Find last space before max_length
            last_space = truncated.rfind(' ')
            if last_space > max_length * 0.8:  # Only use word boundary if it's reasonably close
                processed_text = truncated[:last_space]
            else:
                processed_text = truncated
            logger.warning(f"Text truncated to {len(processed_text)} characters")
        
        return processed_text
    
    @staticmethod
    def estimate_duration(text, words_per_minute=None):
        """
        Estimate audio duration based on text length
        
        Args:
            text: Input text string
            words_per_minute: Speaking rate (defaults to DEFAULT_WPM)
            
        Returns:
            Estimated duration in seconds (float)
        """
        if not text:
            return 0.0
        
        if words_per_minute is None:
            words_per_minute = TextProcessor.DEFAULT_WPM
        
        # Clean text first
        cleaned_text = TextProcessor.clean_text(text)
        
        if not cleaned_text:
            return 0.0
        
        # Count words (split by whitespace)
        words = cleaned_text.split()
        word_count = len(words)
        
        # Calculate duration: (word_count / words_per_minute) * 60 seconds
        duration_seconds = (word_count / words_per_minute) * 60
        
        return duration_seconds

