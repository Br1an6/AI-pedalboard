from pedalboard import (
    Pedalboard, Chorus, Compressor, Delay, Distortion, Gain, 
    HighpassFilter, LadderFilter, Limiter, LowpassFilter, 
    NoiseGate, Phaser, Reverb
)
from pedalboard.io import AudioStream
import logging

class AudioManager:
    def __init__(self):
        """
        Initialize the AudioManager.
        Sets up the plugin map and initializes the stream as None.
        """
        self.stream = None
        self.logger = logging.getLogger(__name__)
        
        # Mapping string names to classes
        self.plugin_map = {
            "Chorus": Chorus,
            "Compressor": Compressor,
            "Delay": Delay,
            "Distortion": Distortion,
            "Gain": Gain,
            "HighpassFilter": HighpassFilter,
            "LadderFilter": LadderFilter,
            "Limiter": Limiter,
            "LowpassFilter": LowpassFilter,
            "NoiseGate": NoiseGate,
            "Phaser": Phaser,
            "Reverb": Reverb,
        }

    def list_input_devices(self):
        """
        List available input device names.

        Returns:
            list: A list of strings representing input device names.
        """
        return AudioStream.input_device_names

    def list_output_devices(self):
        """
        List available output device names.

        Returns:
            list: A list of strings representing output device names.
        """
        return AudioStream.output_device_names

    def build_pedalboard(self, config_list):
        """
        Converts a list of dicts (from AI) into a Pedalboard object.

        Args:
            config_list (list): A list of dictionaries, each describing a plugin and its parameters.

        Returns:
            Pedalboard: A Pedalboard object containing the configured plugins.
        """
        plugins = []
        for item in config_list:
            name = item.get("plugin")
            params = item.get("params", {})
            
            plugin_class = self.plugin_map.get(name)
            if plugin_class:
                try:
                    # Instantiate plugin with parameters
                    # Note: We trust the AI to give valid kwargs. 
                    # In a production app, we should validate/sanitize these.
                    plugin = plugin_class(**params)
                    plugins.append(plugin)
                except Exception as e:
                    self.logger.error(f"Error creating plugin {name} with params {params}: {e}")
            else:
                self.logger.warning(f"Unknown plugin requested: {name}")
        
        return Pedalboard(plugins)

    def start_stream(self, input_device, output_device, initial_config=None):
        """
        Starts the audio stream.

        Args:
            input_device (str): The name of the input audio device.
            output_device (str): The name of the output audio device.
            initial_config (list, optional): Initial list of plugin configurations. Defaults to None.

        Returns:
            tuple: (bool, str) - (Success status, Message).
        """
        if self.stream:
            self.stop_stream()

        try:
            self.stream = AudioStream(
                input_device_name=input_device,
                output_device_name=output_device,
                allow_feedback=True
            )
            
            # Start the stream manually (enter context)
            self.stream.__enter__()
            
            if initial_config:
                self.stream.plugins = self.build_pedalboard(initial_config)
            
            return True, "Stream started."
        except Exception as e:
            self.logger.error(f"Failed to start stream: {e}")
            self.stream = None
            return False, str(e)

    def stop_stream(self):
        """
        Stops the current audio stream if it is running.
        """
        if self.stream:
            self.stream.__exit__(None, None, None)
            self.stream = None

    def update_plugins(self, config_list):
        """
        Updates the plugins in the active audio stream.

        Args:
            config_list (list): A new list of plugin configurations.
        """
        if self.stream:
            new_board = self.build_pedalboard(config_list)
            self.stream.plugins = new_board
        else:
            self.logger.warning("Attempted to update plugins but stream is not running.")
    
    def is_active(self):
        """
        Checks if the audio stream is currently active.

        Returns:
            bool: True if the stream is running, False otherwise.
        """
        return self.stream is not None
