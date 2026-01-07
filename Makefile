# Makefile for AI Pedalboard

VENV_DIR = venv
PYTHON = $(VENV_DIR)/bin/python
PIP = $(VENV_DIR)/bin/pip
STREAMLIT = $(VENV_DIR)/bin/streamlit

.PHONY: install run-web run-desktop clean

# Default target
install:
	@echo "Creating virtual environment..."
	python3 -m venv $(VENV_DIR)
	@echo "Installing dependencies..."
	$(PIP) install --upgrade pip
	$(PIP) install -r requirements.txt
	@echo "Installation complete."

# Run Streamlit Web Interface
run-web:
	@if [ ! -d "$(VENV_DIR)" ]; then echo "Virtual environment not found. Running 'make install'..."; make install; fi
	$(STREAMLIT) run app.py

# Run Tkinter Desktop Application
run-desktop:
	@if [ ! -d "$(VENV_DIR)" ]; then echo "Virtual environment not found. Running 'make install'..."; make install; fi
	$(PYTHON) main.py

# Clean up virtual environment
clean:
	rm -rf $(VENV_DIR)
	rm -rf __pycache__
