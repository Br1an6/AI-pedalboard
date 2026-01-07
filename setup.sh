#!/bin/bash

# setup.sh - Helper script for AI Pedalboard

VENV_DIR="venv"

# Help function
show_help() {
    echo "Usage: ./setup.sh [option]"
    echo "Options:"
    echo "  install      Create venv and install dependencies"
    echo "  web          Run Streamlit Web Interface"
    echo "  desktop      Run Tkinter Desktop Application"
    echo "  clean        Remove virtual environment"
    echo "  help         Show this help message"
}

# Install function
install() {
    echo "Creating virtual environment..."
    python3 -m venv $VENV_DIR
    source $VENV_DIR/bin/activate
    echo "Installing dependencies..."
    pip install --upgrade pip
    pip install -r requirements.txt
    echo "Installation complete."
}

# Run Web function
run_web() {
    if [ ! -d "$VENV_DIR" ]; then
        echo "Virtual environment not found. Installing..."
        install
    fi
    source $VENV_DIR/bin/activate
    streamlit run app.py
}

# Run Desktop function
run_desktop() {
    if [ ! -d "$VENV_DIR" ]; then
        echo "Virtual environment not found. Installing..."
        install
    fi
    source $VENV_DIR/bin/activate
    python main.py
}

# Clean function
clean() {
    rm -rf $VENV_DIR
    rm -rf __pycache__
    echo "Cleaned up."
}

# Main logic
case "$1" in
    install)
        install
        ;;
    web)
        run_web
        ;;
    desktop)
        run_desktop
        ;;
    clean)
        clean
        ;;
    *)
        show_help
        ;;
esac
