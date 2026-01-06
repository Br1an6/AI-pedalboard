import requests
import json
import logging
import re

class AIAssistant:
    def __init__(self, model="gemma3:latest", url="http://localhost:11434"):
        """
        Initialize the AIAssistant.

        Args:
            model (str): The name of the Ollama model to use. Defaults to "gemma3:latest".
            url (str): The URL of the Ollama API. Defaults to "http://localhost:11434".
        """
        self.model = model
        self.url = url
        self.logger = logging.getLogger(__name__)
        self.last_raw_response = ""

    def is_running(self):
        """
        Checks if the Ollama service is running.

        Returns:
            bool: True if Ollama is reachable and returns status 200, False otherwise.
        """
        try:
            response = requests.get(self.url, timeout=2)
            # Ollama root usually returns "Ollama is running"
            return response.status_code == 200
        except requests.exceptions.RequestException:
            return False

    def get_available_models(self):
        """
        Fetches the list of available models from Ollama.

        Returns:
            list: A list of model names (strings) available in Ollama.
                  Returns an empty list if the request fails.
        """
        try:
            response = requests.get(f"{self.url}/api/tags", timeout=5)
            if response.status_code == 200:
                data = response.json()
                return [model["name"] for model in data.get("models", [])]
            return []
        except requests.exceptions.RequestException:
            return []

    def set_model(self, model_name):
        """
        Sets the model to be used for generation.

        Args:
            model_name (str): The name of the model to use.
        """
        self.model = model_name

    def set_url(self, url):
        """
        Sets the Ollama API URL.

        Args:
            url (str): The new URL for the Ollama API.
        """
        self.url = url

    def generate_pedal_config(self, user_prompt):
        """
        Asks Ollama to generate a pedalboard configuration.
        Uses /api/generate for maximum compatibility.

        Args:
            user_prompt (str): The user's description of the desired tone.

        Returns:
            list: A list of dictionaries representing the pedalboard configuration.
                  Returns an empty list if generation or parsing fails.
        """
        system_prompt = """
You are an expert audio engineer using the 'pedalboard' library. 
Convert the user's tone description into a JSON array of pedals.

Supported Plugins: 
- Chorus(rate_hz, depth, centre_delay_ms, feedback, mix)
- Compressor(threshold_db, ratio, attack_ms, release_ms)
- Delay(delay_seconds, feedback, mix)
- Distortion(drive_db)
- Gain(gain_db)
- HighpassFilter(cutoff_frequency_hz)
- Limiter(threshold_db, release_ms)
- LowpassFilter(cutoff_frequency_hz)
- NoiseGate(threshold_db, ratio, attack_ms, release_ms)
- Phaser(rate_hz, depth, centre_frequency_hz, feedback, mix)
- Reverb(room_size, damping, wet_level, dry_level)

Do NOT provide any explanations. 
Output ONLY the JSON array.

Example Response:
[
  {"plugin": "Compressor", "params": {"threshold_db": -20, "ratio": 4}},
  {"plugin": "Distortion", "params": {"drive_db": 30}}
]
"""

        payload = {
            "model": self.model,
            "prompt": f"{system_prompt}\n\nUser Request: {user_prompt}\nJSON Response:",
            "stream": False,
            # "format": "json"  <-- Removed to let the model generate text freely, regex will catch it
        }

        try:
            # Using /api/generate instead of /api/chat
            response = requests.post(f"{self.url}/api/generate", json=payload, timeout=30)
            response.raise_for_status()
            
            data = response.json()
            content = data.get("response", "")
            self.last_raw_response = content
            
            print(f"DEBUG: Ollama Raw Response:\n{content}\n")
            
            config = []
            try:
                config = json.loads(content)
            except json.JSONDecodeError:
                match = re.search(r'\[.*\]', content, re.DOTALL)
                if match:
                    try:
                        config = json.loads(match.group())
                    except:
                        return []
                else:
                    return []

            if isinstance(config, list):
                return config
            elif isinstance(config, dict) and "plugins" in config:
                return config["plugins"]
            return []

        except requests.exceptions.RequestException as e:
            self.logger.error(f"Error communicating with Ollama: {e}")
            return []