# AI-Powered Pedalboard

![version](https://img.shields.io/badge/version-0.0.1-blue)

An intelligent guitar effects processor that configures itself based on natural language descriptions of the desired tone. Powered by local LLM (Ollama).

![alt tag](https://github.com/Br1an6/AI-pedalboard/blob/main/img/pedal.png)

## Features

- **Real-time Audio Processing:** Powered by Spotify's [pedalboard](https://github.com/spotify/pedalboard) library.
- **AI Tone Generation:** Uses a locally running [Ollama](https://ollama.com/) instance to interpret tone requests.
- **Configurable Endpoint:** Support for custom Ollama API URLs (defaults to `http://localhost:11434`).
- **Dual Interfaces:** Choose between a modern Streamlit web interface or a lightweight Tkinter desktop application.
- **Device Selection:** Simple UI to select input (guitar interface) and output (speakers/headphones) devices.
- **Live Updates:** Apply new effect chains and adjust parameters in real-time without restarting the application.

## Prerequisites

1.  **Python 3.8+**
2.  **Ollama**:
    *   Install from [ollama.com](https://ollama.com).
    *   Pull a model (e.g., `llama3` or `gemma3`):
        ```bash
        ollama pull llama3
        ```
    *   Ensure Ollama is running (`ollama serve`). If running on a different machine or port, you can configure the URL in the application.
3. **Tkinter**: (Optional) Required if you plan to run the desktop app (`main.py`).
    * **Linux (Ubuntu/Debian):**
        ```bash
        sudo apt-get install python3-tk
        ```
    * **macOS:**
        Usually included with the Python.org installer. If using Homebrew:
        ```bash
        brew install python-tk
        ```
    * **Windows:**
        Included with the standard Python installer. If you receive an error, rerun the Python installer, select **Modify**, and ensure **"tcl/tk and IDLE"** is checked.

## Installation

1.  Clone the repository.
2.  Create a virtual environment:
    ```bash
    python -m venv venv
    source venv/bin/activate  # On Windows: venv\Scripts\activate
    ```
3.  Install dependencies:
    ```bash
    pip install -r requirements.txt
    ```

## ⚠️ Important Notes
- **Set up your input/output devices first:** The tone generation only works after configuring your audio devices.
- **Audio Feedback:** The application bypasses standard feedback safety checks to allow more flexible device routing. **Please use headphones** or keep your volume low when starting the stream to avoid loud feedback loops between your microphone and speakers.
- **Latency:** As this is running in Python, you may experience slight audio delay (latency) depending on your hardware and OS configuration. For best results, use a dedicated ASIO driver (Windows) or a low-latency audio interface.

## Usage

### Option A: Streamlit Web Interface (Recommended)
1.  Run the application:
    ```bash
    streamlit run app.py
    ```
    *This will open the interface in your default web browser.*

### Option B: Tkinter Desktop Application
1.  Run the application:
    ```bash
    python main.py
    ```

    ![alt tag](https://github.com/Br1an6/AI-pedalboard/blob/main/img/pedal-app.png)

## Application Steps
1.  **Configuration:** Select your Input Device (e.g., audio interface) and Output Device. Ensure the Ollama URL is correct.
2.  **Tone Description:** Type a description of the tone you want (e.g., "80s rock solo").
3.  **Generate:** Click **Generate Tone**.
4.  **Process:** Click **Start Processing** to hear the result.
5.  **Adjust:** Use the generated sliders to fine-tune individual pedal parameters.

## TODO:
* Pedal board UI: drag drop, on off
* Update the system prompt

## License

MIT
