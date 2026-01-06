# AI-Powered Pedalboard

An intelligent guitar effects processor that configures itself based on natural language descriptions of the desired tone.

![alt tag](https://github.com/Br1an6/AI-pedalboard/blob/main/img/pedal.png)

## Features

- **Real-time Audio Processing:** Powered by Spotify's `pedalboard` library.
- **AI Tone Generation:** Uses a locally running [Ollama](https://ollama.com/) instance to interpret tone requests (e.g., "I want a crunchy blues tone" or "Spacey ambient reverb").
- **Device Selection:** Simple UI to select input (guitar interface) and output (speakers/headphones) devices.
- **Live Updates:** Apply new effect chains without restarting the application.

## Prerequisites

1.  **Python 3.8+**
2.  **Ollama**:
    *   Install from [ollama.com](https://ollama.com).
    *   Pull a model (e.g., `llama3` or `mistral`):
        ```bash
        ollama pull llama3
        ```
    *   Ensure Ollama is running (`ollama serve`).

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

1.  Run the application:
    ```bash
    streamlit run app.py
    ```
    *This will open the interface in your default web browser.*

2.  **Sidebar:** Select your Input Device (e.g., audio interface) and Output Device.
3.  **Main Panel:** Type a description of the tone you want (e.g., "80s rock solo").
4.  Click **Generate Tone**.
5.  In the Sidebar, click **Start Processing** to hear the result.

## License

MIT
