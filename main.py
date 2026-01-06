import tkinter as tk
from tkinter import ttk, scrolledtext, messagebox
import threading
import logging
import json

from ai_assistant import AIAssistant
from audio_manager import AudioManager

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

class PedalboardApp:
    def __init__(self, root):
        """
        Initialize the PedalboardApp.

        Args:
            root (tk.Tk): The root Tkinter window.
        """
        self.root = root
        self.root.title("AI Pedalboard")
        self.root.geometry("600x700")

        self.ai = AIAssistant()
        self.audio = AudioManager()
        self.current_config = []

        self.setup_ui()
        self.log("Application started.")
        self.check_ollama_status()

    def setup_ui(self):
        """
        Set up the User Interface components (Frames, Labels, Buttons, etc.).
        """
        # --- Audio Device Section ---
        device_frame = ttk.LabelFrame(self.root, text="Audio Devices", padding="10")
        device_frame.pack(fill="x", padx=10, pady=5)

        ttk.Label(device_frame, text="Input Device:").grid(row=0, column=0, sticky="w")
        self.input_device_combo = ttk.Combobox(device_frame, state="readonly", width=40)
        self.input_device_combo.grid(row=0, column=1, padx=5, pady=5)

        ttk.Label(device_frame, text="Output Device:").grid(row=1, column=0, sticky="w")
        self.output_device_combo = ttk.Combobox(device_frame, state="readonly", width=40)
        self.output_device_combo.grid(row=1, column=1, padx=5, pady=5)
        
        refresh_btn = ttk.Button(device_frame, text="Refresh Devices", command=self.refresh_devices)
        refresh_btn.grid(row=2, column=1, sticky="e", pady=5)

        # --- AI Tone Section ---
        ai_frame = ttk.LabelFrame(self.root, text="AI Tone Generator", padding="10")
        ai_frame.pack(fill="x", padx=10, pady=5)

        ttk.Label(ai_frame, text="Describe your tone:").pack(anchor="w")
        self.prompt_entry = ttk.Entry(ai_frame, width=50)
        self.prompt_entry.pack(fill="x", pady=5)
        self.prompt_entry.bind("<Return>", lambda event: self.generate_tone())

        self.generate_btn = ttk.Button(ai_frame, text="Generate Tone", command=self.generate_tone)
        self.generate_btn.pack(anchor="e", pady=5)
        
        self.ollama_status_lbl = ttk.Label(ai_frame, text="Checking Ollama...", foreground="gray")
        self.ollama_status_lbl.pack(anchor="w")

        # --- Connection Settings ---
        conn_frame = ttk.LabelFrame(self.root, text="Ollama Settings", padding="10")
        conn_frame.pack(fill="x", padx=10, pady=5)

        ttk.Label(conn_frame, text="API URL:").grid(row=0, column=0, sticky="w")
        self.url_entry = ttk.Entry(conn_frame, width=40)
        self.url_entry.insert(0, self.ai.url)
        self.url_entry.grid(row=0, column=1, padx=5, pady=5)
        
        update_url_btn = ttk.Button(conn_frame, text="Update URL", command=self.update_ollama_url)
        update_url_btn.grid(row=0, column=2, padx=5)

        # --- Stream Control Section ---
        control_frame = ttk.Frame(self.root, padding="10")
        control_frame.pack(fill="x", padx=10)

        self.start_btn = ttk.Button(control_frame, text="Start Processing", command=self.toggle_stream)
        self.start_btn.pack(side="left", fill="x", expand=True, padx=5)

        # --- Log/Status Area ---
        log_frame = ttk.LabelFrame(self.root, text="Status / Logs", padding="10")
        log_frame.pack(fill="both", expand=True, padx=10, pady=5)

        self.log_area = scrolledtext.ScrolledText(log_frame, height=10, state="disabled")
        self.log_area.pack(fill="both", expand=True)

        # Initial data fetch
        self.refresh_devices()

    def log(self, message):
        """
        Log a message to the UI log area and the standard logger.

        Args:
            message (str): The message to log.
        """
        self.log_area.config(state="normal")
        self.log_area.insert(tk.END, message + "\n")
        self.log_area.see(tk.END)
        self.log_area.config(state="disabled")
        logging.info(message)

    def check_ollama_status(self):
        """
        Checks the status of the Ollama service in a separate thread and updates the UI.
        """
        def _check():
            if self.ai.is_running():
                self.root.after(0, lambda: self.ollama_status_lbl.config(text="Ollama: Connected", foreground="green"))
            else:
                self.root.after(0, lambda: self.ollama_status_lbl.config(text="Ollama: Not Running (Start 'ollama serve')", foreground="red"))
        
        threading.Thread(target=_check, daemon=True).start()

    def refresh_devices(self):
        """
        Refreshes the list of available input and output audio devices.
        Updates the Comboboxes in the UI.
        """
        try:
            inputs = self.audio.list_input_devices()
            outputs = self.audio.list_output_devices()
            
            self.input_device_combo['values'] = inputs
            self.output_device_combo['values'] = outputs
            
            if inputs: self.input_device_combo.current(0)
            if outputs: self.output_device_combo.current(0)
            
            self.log("Audio devices refreshed.")
        except Exception as e:
            self.log(f"Error listing devices: {e}")

    def update_ollama_url(self):
        """
        Updates the Ollama API URL from the UI entry field.
        """
        new_url = self.url_entry.get().strip()
        if new_url:
            self.ai.set_url(new_url)
            self.log(f"Ollama URL updated to: {new_url}")
            # Trigger a status check immediately
            self.check_ollama_status()
        else:
            messagebox.showwarning("Invalid URL", "Please enter a valid URL.")

    def generate_tone(self):
        """
        Initiates the tone generation process using the AI assistant.
        Runs in a separate thread to prevent UI freezing.
        """
        prompt = self.prompt_entry.get()
        if not prompt:
            messagebox.showwarning("Input Required", "Please describe the tone you want.")
            return

        self.generate_btn.config(state="disabled", text="Generating...")
        self.log(f"Asking AI for: '{prompt}'...")

        def _worker():
            config = self.ai.generate_pedal_config(prompt)
            self.root.after(0, self.apply_generated_config, config)

        threading.Thread(target=_worker, daemon=True).start()

    def apply_generated_config(self, config):
        """
        Applies the generated pedalboard configuration.

        Args:
            config (list): The list of pedal configurations generated by the AI.
        """
        self.generate_btn.config(state="normal", text="Generate Tone")
        if not config:
            self.log("AI returned empty or invalid config.")
            return

        self.current_config = config
        self.log(f"AI suggested: {json.dumps(config, indent=2)}")
        
        # If stream is running, update immediately
        if self.audio.is_active():
            self.audio.update_plugins(config)
            self.log("Updated active pedalboard.")
        else:
            self.log("Config saved. Start stream to hear it.")

    def toggle_stream(self):
        """
        Toggles the audio processing stream on or off.
        Starts or stops the stream based on the current state.
        """
        if self.audio.is_active():
            # Stop
            self.audio.stop_stream()
            self.start_btn.config(text="Stop Processing")
            self.log("Stream stopped.")
        else:
            # Start
            in_dev = self.input_device_combo.get()
            out_dev = self.output_device_combo.get()
            
            if not in_dev or not out_dev:
                messagebox.showerror("Error", "Please select input and output devices.")
                return

            self.log(f"Starting stream on {in_dev} -> {out_dev}...")
            success, msg = self.audio.start_stream(in_dev, out_dev, self.current_config)
            
            if success:
                self.start_btn.config(text="Stop Processing")
                self.log("Stream started successfully!")
            else:
                self.log(f"Error starting stream: {msg}")
                messagebox.showerror("Audio Error", msg)

if __name__ == "__main__":
    root = tk.Tk()
    app = PedalboardApp(root)
    root.mainloop()
