"""
Unit tests for TextProcessor
"""
import unittest
from utils.text_processor import TextProcessor


class TestTextProcessor(unittest.TestCase):
    """Test cases for TextProcessor class"""
    
    def test_clean_text(self):
        """Test text cleaning functionality"""
        # Test basic cleaning
        result = TextProcessor.clean_text("  Hello   world  ")
        self.assertEqual(result, "Hello world")
        
        # Test empty text
        result = TextProcessor.clean_text("")
        self.assertEqual(result, "")
        
        # Test None
        result = TextProcessor.clean_text(None)
        self.assertEqual(result, "")
    
    def test_expand_abbreviations(self):
        """Test abbreviation expansion"""
        result = TextProcessor.expand_abbreviations("Dr. Smith")
        self.assertEqual(result, "Doctor Smith")
        
        result = TextProcessor.expand_abbreviations("Mr. and Mrs. Jones")
        self.assertEqual(result, "Mister and Missus Jones")
        
        result = TextProcessor.expand_abbreviations("e.g. example")
        self.assertEqual(result, "for example example")
    
    def test_validate_text(self):
        """Test text validation"""
        # Valid text
        is_valid, msg = TextProcessor.validate_text("Hello world")
        self.assertTrue(is_valid)
        self.assertIsNone(msg)
        
        # Empty text
        is_valid, msg = TextProcessor.validate_text("")
        self.assertFalse(is_valid)
        self.assertIsNotNone(msg)
        
        # Too short
        is_valid, msg = TextProcessor.validate_text("Hi")
        self.assertFalse(is_valid)
        self.assertIsNotNone(msg)
        
        # Too long
        long_text = "a" * 501
        is_valid, msg = TextProcessor.validate_text(long_text, max_length=500)
        self.assertFalse(is_valid)
        self.assertIsNotNone(msg)
    
    def test_preprocess_for_tts(self):
        """Test complete preprocessing pipeline"""
        result = TextProcessor.preprocess_for_tts("  Dr. Smith said hello  ")
        self.assertEqual(result, "Doctor Smith said hello")
        
        # Test truncation
        long_text = "a" * 600
        result = TextProcessor.preprocess_for_tts(long_text, max_length=500)
        self.assertEqual(len(result), 500)
    
    def test_estimate_duration(self):
        """Test duration estimation"""
        text = "This is a test sentence with ten words here."
        duration = TextProcessor.estimate_duration(text, words_per_minute=150)
        self.assertIsInstance(duration, float)
        self.assertGreater(duration, 0)


if __name__ == '__main__':
    unittest.main()