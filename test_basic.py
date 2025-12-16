"""
Simple test script to verify TTS functionality
Run this before starting the Flask app to ensure everything works
"""
import sys
from pathlib import Path

def test_imports():
    """Test that all required packages are installed"""
    print("🔍 Testing imports...")
    
    try:
        import flask
        print("   ✓ Flask installed")
    except ImportError:
        print("   ✗ Flask not found - run: pip install flask")
        return False
    
    try:
        import torch
        print(f"   ✓ PyTorch installed (version {torch.__version__})")
    except ImportError:
        print("   ✗ PyTorch not found - run: pip install torch")
        return False
    
    try:
        import transformers
        print(f"   ✓ Transformers installed (version {transformers.__version__})")
    except ImportError:
        print("   ✗ Transformers not found - run: pip install transformers")
        return False
    
    try:
        import scipy
        print("   ✓ SciPy installed")
    except ImportError:
        print("   ✗ SciPy not found - run: pip install scipy")
        return False
    
    try:
        import numpy
        print("   ✓ NumPy installed")
    except ImportError:
        print("   ✗ NumPy not found - run: pip install numpy")
        return False
    
    return True

def test_directories():
    """Test that required directories exist"""
    print("\n📁 Testing directories...")
    
    required_dirs = [
        'models',
        'static',
        'static/audio',
        'static/css',
        'static/js',
        'templates',
        'utils'
    ]
    
    all_exist = True
    for dir_path in required_dirs:
        path = Path(dir_path)
        if path.exists():
            print(f"   ✓ {dir_path}/ exists")
        else:
            print(f"   ✗ {dir_path}/ missing - creating...")
            path.mkdir(parents=True, exist_ok=True)
            all_exist = False
    
    return True  # We create them if missing

def test_files():
    """Test that required files exist"""
    print("\n📄 Testing files...")
    
    required_files = [
        'app.py',
        'config.py',
        'requirements.txt',
        'utils/tts_engine.py',
        'utils/text_processor.py',
        'templates/index.html',
        'static/css/style.css',
        'static/js/main.js'
    ]
    
    all_exist = True
    for file_path in required_files:
        path = Path(file_path)
        if path.exists():
            print(f"   ✓ {file_path} exists")
        else:
            print(f"   ✗ {file_path} missing!")
            all_exist = False
    
    return all_exist

def test_text_processor():
    """Test text processing utilities"""
    print("\n🔤 Testing text processor...")
    
    try:
        from utils.text_processor import TextProcessor
        
        # Test clean_text
        test_text = "  Hello   world!  "
        cleaned = TextProcessor.clean_text(test_text)
        assert cleaned == "Hello world!", f"Clean text failed: {cleaned}"
        print("   ✓ Text cleaning works")
        
        # Test validation
        is_valid, msg = TextProcessor.validate_text("Hello")
        assert is_valid, "Validation failed for valid text"
        print("   ✓ Text validation works")
        
        # Test empty validation
        is_valid, msg = TextProcessor.validate_text("")
        assert not is_valid, "Validation should fail for empty text"
        print("   ✓ Empty text validation works")
        
        return True
        
    except Exception as e:
        print(f"   ✗ Text processor test failed: {e}")
        return False

def test_tts_engine():
    """Test TTS engine initialization (without generating audio)"""
    print("\n🤖 Testing TTS engine initialization...")
    print("   (This will download the model if not cached - ~2GB)")
    print("   Press Ctrl+C to skip model download test")
    
    try:
        # Give user chance to skip
        input("   Press Enter to continue or Ctrl+C to skip... ")
        
        from utils.tts_engine import TTSEngine
        import torch
        
        device = "cpu"  # Use CPU for testing
        print(f"   Using device: {device}")
        
        print("   Loading model (this may take a few minutes)...")
        engine = TTSEngine(
            model_name="suno/bark-small",
            device=device
        )
        print("   ✓ TTS engine initialized successfully")
        
        # Test text preprocessing
        test_text = "Hello world"
        processed = engine.preprocess_text(test_text)
        print(f"   ✓ Text preprocessing works: '{processed}'")
        
        return True
        
    except KeyboardInterrupt:
        print("\n   ⊘ Skipped model download test")
        return True
    except Exception as e:
        print(f"   ✗ TTS engine test failed: {e}")
        return False

def test_config():
    """Test configuration"""
    print("\n⚙️  Testing configuration...")
    
    try:
        from config import get_config
        config = get_config()
        
        print(f"   Environment: {config.__name__}")
        print(f"   Model: {config.MODEL_NAME}")
        print(f"   Use GPU: {config.USE_GPU}")
        print(f"   Max text length: {config.MAX_TEXT_LENGTH}")
        print("   ✓ Configuration loaded")
        
        return True
        
    except Exception as e:
        print(f"   ✗ Configuration test failed: {e}")
        return False

def main():
    """Run all tests"""
    print("=" * 60)
    print("🧪 TTS Application - Pre-flight Checks")
    print("=" * 60)
    
    results = {
        "imports": test_imports(),
        "directories": test_directories(),
        "files": test_files(),
        "config": test_config(),
        "text_processor": test_text_processor(),
    }
    
    # Optional: TTS engine test (requires download)
    print("\n" + "=" * 60)
    print("Optional: Test TTS Engine (requires model download)")
    print("=" * 60)
    test_tts = input("Run TTS engine test? (y/n): ").lower().strip() == 'y'
    
    if test_tts:
        results["tts_engine"] = test_tts_engine()
    
    # Summary
    print("\n" + "=" * 60)
    print("📊 Test Summary")
    print("=" * 60)
    
    for test_name, passed in results.items():
        status = "✅ PASS" if passed else "❌ FAIL"
        print(f"   {test_name.upper()}: {status}")
    
    all_passed = all(results.values())
    
    print("\n" + "=" * 60)
    if all_passed:
        print("🎉 All tests passed! You're ready to run the application.")
        print("\nNext steps:")
        print("   1. Run: python app.py")
        print("   2. Open: http://localhost:5000")
    else:
        print("⚠️  Some tests failed. Please fix the issues above.")
        print("\nCommon fixes:")
        print("   - Install missing packages: pip install -r requirements.txt")
        print("   - Create missing files using the artifacts provided")
        print("   - Check file paths and names")
    print("=" * 60)
    
    return 0 if all_passed else 1

if __name__ == "__main__":
    try:
        sys.exit(main())
    except KeyboardInterrupt:
        print("\n\n⊘ Tests interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ Unexpected error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)