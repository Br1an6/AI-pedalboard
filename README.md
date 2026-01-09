# AI-Powered Pedalboard

![version](https://img.shields.io/badge/version-0.0.2-blue)

An intelligent guitar effects processor that configures itself based on natural language descriptions of the desired tone. Powered by local LLM (Ollama).

## Web app
![alt tag](https://github.com/Br1an6/AI-pedalboard/blob/main/img/pedal.png)
![alt tag](https://github.com/Br1an6/AI-pedalboard/blob/main/img/pedal-detail.png)

## Desktop app
![alt tag](https://github.com/Br1an6/AI-pedalboard/blob/main/img/pedal-desktop-app.png)

## Features

- **Real-time Audio Processing:** Powered by Spotify's [pedalboard](https://github.com/spotify/pedalboard) library.
- **AI Tone Generation:** Uses a locally running [Ollama](https://ollama.com/) instance to interpret tone requests.
- **Configurable Endpoint:** Support for custom Ollama API URLs (defaults to `http://localhost:11434`).
- **Interactive Web Interface (Streamlit):**
    - **Drag-and-Drop:** Easily reorder effects or move them between active and unused pools.
    - **Toggle Switches:** Bypass individual effects without removing them from the chain.
    - **Real-time Controls:** Adjust parameters on the fly.
- **Desktop Interface (Tkinter):** A fully-featured desktop app with drag-and-drop support, effect parameter fine-tuning, and real-time audio control.
- **Device Selection:** Simple UI to select input (guitar interface) and output (speakers/headphones) devices.

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

## Quick Start (Automated)

We provide automation scripts to handle virtual environment creation and dependency installation.

### Using Make (Mac/Linux)

1.  **Install:**
    ```bash
    make install
    ```
2.  **Run Web Interface (Recommended):**
    ```bash
    make run-web
    ```
3.  **Run Desktop Interface:**
    ```bash
    make run-desktop
    ```

### Using Setup Script (Mac/Linux)

1.  **Make executable:**
    ```bash
    chmod +x setup.sh
    ```
2.  **Install:**
    ```bash
    ./setup.sh install
    ```
3.  **Run:**
    ```bash
    ./setup.sh web      # Streamlit
    # OR
    ./setup.sh desktop  # Tkinter
    ```

## Manual Installation

If you prefer to set up the environment manually:

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
4.  Run the application:
    *   **Web:** `streamlit run app.py`
    *   **Desktop:** `python main.py`

## Application Steps
1.  **Configuration:** Select your Input Device (e.g., audio interface) and Output Device. Ensure the Ollama URL is correct.
2.  **Tone Description:** Type a description of the tone you want (e.g., "80s rock solo").
3.  **Generate:** Click **Generate Tone**.
4.  **Process:** Click **Start Processing** to hear the result.
5.  **Adjust:**
    *   **Reorder:** Drag pedals to change the signal chain order.
    *   **Toggle:** Use the switches to enable/disable effects.
    *   **Tweaks:** Use sliders to fine-tune parameters.

## Recording (DAW Integration)

To record the output of this application into a DAW (like GarageBand, Logic Pro, Ableton, etc.), you need to route the audio using a virtual audio cable.

### macOS
1.  **Install BlackHole:**
    We recommend [BlackHole](https://github.com/ExistentialAudio/BlackHole) (a modern replacement for Soundflower).
    ```bash
    brew install blackhole-2ch
    ```
2.  **Configure AI Pedalboard:**
    - Set **Input Device** to your Guitar Interface.
    - Set **Output Device** to **BlackHole 2ch**.
3.  **Configure DAW (e.g., GarageBand):**
    - Set **Input Device** to **BlackHole 2ch**.
    - Set **Output Device** to your headphones/speakers (for monitoring).
    - **Important:** Enable "Input Monitoring" on your track to hear the wet signal.

### Windows
1.  **Install VB-CABLE:**
    Download and install [VB-CABLE Virtual Audio Device](https://vb-audio.com/Cable/).
2.  **Configure AI Pedalboard:**
    - Set **Output Device** to **CABLE Input**.
3.  **Configure DAW:**
    - Set **Input Device** to **CABLE Output**.

## 💡 Tips for Best Results

*   **Model Matters:** The quality of the output relies heavily on the "brain" behind it. If you have access to a larger or more capable LLM (like `llama3:70b` or `gemma3:27b`), you might get even more accurate and nuanced presets.
*   **Watch the Wet Effects:** Depending on your specific setup, the AI might get a little excited with spatial effects. If the reverb or chorus feels like "too much," just dial those back manually in the UI to taste.

## ⚠️ Important Notes
- **Set up your input/output devices first:** The tone generation only works after configuring your audio devices.
- **Audio Feedback:** The application bypasses standard feedback safety checks to allow more flexible device routing. **Please use headphones** or keep your volume low when starting the stream to avoid loud feedback loops between your microphone and speakers.
- **Latency:** As this is running in Python, you may experience slight audio delay (latency) depending on your hardware and OS configuration. For best results, use a dedicated ASIO driver (Windows) or a low-latency audio interface.

## License

GPL 3.0

[![ko-fi](https://ko-fi.com/img/githubbutton_sm.svg)](https://ko-fi.com/I3I81RWCLP)
