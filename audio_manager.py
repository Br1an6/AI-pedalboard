from pedalboard import (
    Pedalboard, Chorus, Compressor, Delay, Distortion, Gain, 
    HighpassFilter, LadderFilter, Limiter, LowpassFilter, 
    NoiseGate, Phaser, Reverb
)
from pedalboard.io import AudioStream
import logging

class AudioManager:
    def __init__(self):
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
        return AudioStream.input_device_names

    def list_output_devices(self):
        return AudioStream.output_device_names

    def build_pedalboard(self, config_list):
        """
        Converts a list of dicts (from AI) into a Pedalboard object.
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
        if self.stream:
            self.stream.__exit__(None, None, None)
            self.stream = None

    def update_plugins(self, config_list):
        if self.stream:
            new_board = self.build_pedalboard(config_list)
            self.stream.plugins = new_board
        else:
            self.logger.warning("Attempted to update plugins but stream is not running.")
    
    def is_active(self):
        return self.stream is not None
