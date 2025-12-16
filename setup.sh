#!/bin/bash

################################################################################
# Text-to-Speech Application - Automated Setup Script
# This script sets up the complete development environment
################################################################################

set -e  # Exit on error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Functions
print_header() {
    echo -e "${BLUE}========================================${NC}"
    echo -e "${BLUE}$1${NC}"
    echo -e "${BLUE}========================================${NC}"
}

print_success() {
    echo -e "${GREEN}✓ $1${NC}"
}

print_error() {
    echo -e "${RED}✗ $1${NC}"
}

print_warning() {
    echo -e "${YELLOW}⚠ $1${NC}"
}

print_info() {
    echo -e "  $1"
}

# Check if command exists
command_exists() {
    command -v "$1" >/dev/null 2>&1
}

# Main setup
main() {
    print_header "TTS Accessibility Platform - Setup"
    echo ""
    
    # Step 1: Check Python version
    print_info "Checking Python version..."
    if command_exists python3; then
        PYTHON_CMD=python3
    elif command_exists python; then
        PYTHON_CMD=python
    else
        print_error "Python not found. Please install Python 3.8 or higher."
        exit 1
    fi
    
    PYTHON_VERSION=$($PYTHON_CMD --version 2>&1 | awk '{print $2}')
    print_success "Python $PYTHON_VERSION found"
    
    # Check Python version is 3.8+
    PYTHON_MAJOR=$($PYTHON_CMD -c 'import sys; print(sys.version_info.major)')
    PYTHON_MINOR=$($PYTHON_CMD -c 'import sys; print(sys.version_info.minor)')
    
    if [ "$PYTHON_MAJOR" -lt 3 ] || { [ "$PYTHON_MAJOR" -eq 3 ] && [ "$PYTHON_MINOR" -lt 8 ]; }; then
        print_error "Python 3.8 or higher required (found $PYTHON_VERSION)"
        exit 1
    fi
    
    echo ""
    
    # Step 2: Create virtual environment
    print_info "Creating virtual environment..."
    if [ -d "venv" ]; then
        print_warning "Virtual environment already exists"
    else
        $PYTHON_CMD -m venv venv
        print_success "Virtual environment created"
    fi
    
    echo ""
    
    # Step 3: Activate virtual environment
    print_info "Activating virtual environment..."
    if [ -f "venv/bin/activate" ]; then
        source venv/bin/activate
        print_success "Virtual environment activated"
    elif [ -f "venv/Scripts/activate" ]; then
        source venv/Scripts/activate
        print_success "Virtual environment activated"
    else
        print_error "Could not find virtual environment activation script"
        exit 1
    fi
    
    echo ""
    
    # Step 4: Upgrade pip
    print_info "Upgrading pip..."
    pip install --upgrade pip --quiet
    print_success "pip upgraded"
    
    echo ""
    
    # Step 5: Install dependencies
    print_info "Installing dependencies (this may take a few minutes)..."
    if [ -f "requirements.txt" ]; then
        pip install -r requirements.txt --quiet
        print_success "Dependencies installed"
    else
        print_warning "requirements.txt not found, skipping dependency installation"
    fi
    
    echo ""
    
    # Step 6: Create directory structure
    print_info "Creating project directories..."
    
    DIRS=("models" "static/audio" "static/css" "static/js" "templates" "utils" "tests")
    
    for dir in "${DIRS[@]}"; do
        if [ ! -d "$dir" ]; then
            mkdir -p "$dir"
            print_success "Created $dir/"
        else
            print_info "$dir/ already exists"
        fi
    done
    
    echo ""
    
    # Step 7: Create .gitkeep files
    print_info "Creating placeholder files..."
    touch models/.gitkeep
    touch static/audio/.gitkeep
    print_success "Placeholder files created"
    
    echo ""
    
    # Step 8: Create .env file
    print_info "Creating environment file..."
    if [ ! -f ".env" ]; then
        if [ -f ".env.example" ]; then
            cp .env.example .env
            # Generate random secret key
            SECRET_KEY=$(python -c 'import secrets; print(secrets.token_hex(32))')
            if [[ "$OSTYPE" == "darwin"* ]]; then
                # macOS
                sed -i '' "s/your-secret-key-change-this-in-production/$SECRET_KEY/" .env
            else
                # Linux
                sed -i "s/your-secret-key-change-this-in-production/$SECRET_KEY/" .env
            fi
            print_success ".env file created with random SECRET_KEY"
        else
            cat > .env << EOF
FLASK_ENV=development
SECRET_KEY=$(python -c 'import secrets; print(secrets.token_hex(32))')
EOF
            print_success ".env file created"
        fi
    else
        print_info ".env file already exists"
    fi
    
    echo ""
    
    # Step 9: Create __init__.py files
    print_info "Creating Python package files..."
    touch utils/__init__.py
    touch tests/__init__.py
    print_success "Package files created"
    
    echo ""
    
    # Step 10: Verify installation
    print_info "Verifying installation..."
    
    VERIFY_FAILED=0
    
    # Check Flask
    if python -c "import flask" 2>/dev/null; then
        print_success "Flask installed"
    else
        print_error "Flask not installed"
        VERIFY_FAILED=1
    fi
    
    # Check PyTorch
    if python -c "import torch" 2>/dev/null; then
        print_success "PyTorch installed"
    else
        print_error "PyTorch not installed"
        VERIFY_FAILED=1
    fi
    
    # Check Transformers
    if python -c "import transformers" 2>/dev/null; then
        print_success "Transformers installed"
    else
        print_error "Transformers not installed"
        VERIFY_FAILED=1
    fi
    
    echo ""
    
    # Step 11: Check for required files
    print_info "Checking for required files..."
    
    FILES_MISSING=0
    REQUIRED_FILES=("app.py" "config.py" "requirements.txt")
    
    for file in "${REQUIRED_FILES[@]}"; do
        if [ -f "$file" ]; then
            print_success "$file exists"
        else
            print_warning "$file not found"
            FILES_MISSING=1
        fi
    done
    
    echo ""
    
    # Summary
    print_header "Setup Summary"
    echo ""
    
    if [ $VERIFY_FAILED -eq 0 ] && [ $FILES_MISSING -eq 0 ]; then
        print_success "Setup completed successfully!"
        echo ""
        print_info "Next steps:"
        echo ""
        echo "  1. Activate virtual environment:"
        echo "     source venv/bin/activate"
        echo ""
        echo "  2. Run the application:"
        echo "     python app.py"
        echo ""
        echo "  3. Open browser to:"
        echo "     http://localhost:5000"
        echo ""
        print_warning "Note: First run will download Bark model (~2GB, 2-5 minutes)"
        echo ""
    else
        print_warning "Setup completed with warnings"
        echo ""
        if [ $VERIFY_FAILED -eq 1 ]; then
            print_info "Some packages failed to install. Try:"
            echo "     pip install -r requirements.txt"
            echo ""
        fi
        if [ $FILES_MISSING -eq 1 ]; then
            print_info "Some application files are missing."
            print_info "Make sure to copy all project files to this directory."
            echo ""
        fi
    fi
    
    print_info "For troubleshooting, run:"
    echo "     python diagnose.py"
    echo ""
}

# Run main function
main