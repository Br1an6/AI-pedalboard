import tkinter as tk
from tkinter import ttk, scrolledtext, messagebox
import threading
import logging
import json
import uuid

from ai_assistant import AIAssistant
from audio_manager import AudioManager

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

class DragDropListbox(tk.Listbox):
    """
    A Listbox that supports internal drag-and-drop reordering and updates the main App model.
    """
    def __init__(self, master, app_instance, **kw):
        super().__init__(master, **kw)
        self.app = app_instance
        self.bind('<Button-1>', self.on_click)
        self.bind('<B1-Motion>', self.on_drag)
        self.bind('<ButtonRelease-1>', self.on_drop)
        self._drag_data = {"item_index": None}

    def on_click(self, event):
        # Prevent default selection clearing for a moment to track index
        index = self.nearest(event.y)
        if index >= 0:
            self._drag_data["item_index"] = index
            self.selection_clear(0, tk.END)
            self.selection_set(index)
            # Generate event so the main app shows params
            self.event_generate("<<ListboxSelect>>")

    def on_drag(self, event):
        # We could implement a visual "ghost" item here, but for simplicity
        # we just rely on the cursor.
        pass

    def on_drop(self, event):
        old_index = self._drag_data["item_index"]
        new_index = self.nearest(event.y)
        
        # If valid move
        if old_index is not None and new_index >= 0 and old_index != new_index:
            if old_index < len(self.app.current_config):
                # Move item in data model
                item = self.app.current_config.pop(old_index)
                self.app.current_config.insert(new_index, item)
                
                # Update UI and Audio
                self.app.refresh_lists()
                self.selection_set(new_index)
                self.app.on_select_active(None)
                self.app.update_audio_engine()

class PedalboardApp:
    def __init__(self, root):
        self.root = root
        self.root.title("AI Pedalboard - Desktop")
        self.root.geometry("1100x800")

        self.ai = AIAssistant()
        self.audio = AudioManager()
        
        # Data Model
        self.current_config = [] 
        self.unused_pedals = [] 
        
        self.setup_ui()
        self.log("Application started.")
        self.check_ollama_status()

    def setup_ui(self):
        # 1. Top Section: Device Config & AI Prompt
        top_frame = ttk.Frame(self.root, padding="10")
        top_frame.pack(fill="x")
        
        # Audio Devices
        dev_frame = ttk.LabelFrame(top_frame, text="Audio Devices", padding="5")
        dev_frame.pack(side="left", fill="both", expand=True, padx=5)
        
        ttk.Label(dev_frame, text="Input:").grid(row=0, column=0, sticky="w")
        self.input_combo = ttk.Combobox(dev_frame, state="readonly", width=25)
        self.input_combo.grid(row=0, column=1, padx=2)
        
        ttk.Label(dev_frame, text="Output:").grid(row=1, column=0, sticky="w")
        self.output_combo = ttk.Combobox(dev_frame, state="readonly", width=25)
        self.output_combo.grid(row=1, column=1, padx=2)
        
        ttk.Button(dev_frame, text="⟳", width=3, command=self.refresh_devices).grid(row=0, column=2, rowspan=2, padx=5)

        # AI Prompt
        ai_frame = ttk.LabelFrame(top_frame, text="AI Tone Generator", padding="5")
        ai_frame.pack(side="left", fill="both", expand=True, padx=5)
        
        self.prompt_entry = ttk.Entry(ai_frame)
        self.prompt_entry.pack(fill="x", pady=5)
        self.prompt_entry.bind("<Return>", lambda e: self.generate_tone())
        
        self.generate_btn = ttk.Button(ai_frame, text="Generate Tone", command=self.generate_tone)
        self.generate_btn.pack(anchor="e")

        # 2. Main Section: Lists and Controls
        mid_frame = ttk.Frame(self.root, padding="10")
        mid_frame.pack(fill="both", expand=True)

        # Left: Unused Pedals
        left_pane = ttk.LabelFrame(mid_frame, text="Unused Effects", padding="5")
        left_pane.pack(side="left", fill="both", expand=True, padx=5)
        
        self.unused_list = tk.Listbox(left_pane, selectmode=tk.SINGLE)
        self.unused_list.pack(fill="both", expand=True)
        ttk.Button(left_pane, text="Add to Chain ▶", command=self.move_to_active).pack(fill="x", pady=5)

        # Center: Active Chain (Drag & Drop)
        center_pane = ttk.LabelFrame(mid_frame, text="Active Chain (Drag to Reorder)", padding="5")
        center_pane.pack(side="left", fill="both", expand=True, padx=5)
        
        # Pass 'self' to DragDropListbox
        self.active_list = DragDropListbox(center_pane, app_instance=self, selectmode=tk.SINGLE)
        self.active_list.pack(fill="both", expand=True)
        # We also listen for standard selection to update the right panel
        self.active_list.bind("<<ListboxSelect>>", self.on_select_active)
        
        ttk.Button(center_pane, text="◀ Remove from Chain", command=self.move_to_unused).pack(fill="x", pady=5)

        # Right: Parameters
        right_pane = ttk.LabelFrame(mid_frame, text="Effect Parameters", padding="10")
        right_pane.pack(side="right", fill="both", expand=True, padx=5)
        
        # Container for dynamic sliders
        self.param_canvas = ttk.Frame(right_pane)
        self.param_canvas.pack(fill="both", expand=True)

        # 3. Bottom Section: Stream & Status
        btm_frame = ttk.Frame(self.root, padding="10")
        btm_frame.pack(fill="x")
        
        self.start_btn = ttk.Button(btm_frame, text="Start Processing", command=self.toggle_stream)
        self.start_btn.pack(side="left", padx=5)
        
        self.status_lbl = ttk.Label(btm_frame, text="Ready", relief="sunken", anchor="w")
        self.status_lbl.pack(side="left", fill="x", expand=True, padx=5)

        self.refresh_devices()

    # --- Actions ---

    def log(self, msg):
        logging.info(msg)
        self.status_lbl.config(text=msg)

    def check_ollama_status(self):
        def _check():
            if self.ai.is_running():
                self.root.after(0, lambda: self.root.title("AI Pedalboard - Connected"))
            else:
                self.root.after(0, lambda: self.root.title("AI Pedalboard - Offline"))
        threading.Thread(target=_check, daemon=True).start()

    def refresh_devices(self):
        inputs = self.audio.list_input_devices()
        outputs = self.audio.list_output_devices()
        self.input_combo['values'] = inputs
        self.output_combo['values'] = outputs
        if inputs: self.input_combo.current(0)
        if outputs: self.output_combo.current(0)

    def generate_tone(self):
        prompt = self.prompt_entry.get()
        if not prompt: return
        
        self.generate_btn.config(state="disabled", text="Thinking...")
        self.log(f"Generating tone for: {prompt}")
        
        def _thread():
            config = self.ai.generate_pedal_config(prompt)
            self.root.after(0, self.apply_ai_config, config)
            
        threading.Thread(target=_thread, daemon=True).start()

    def apply_ai_config(self, config):
        self.generate_btn.config(state="normal", text="Generate Tone")
        if not config:
            self.log("AI failed to generate config.")
            return

        # Ensure UUIDs and Status
        for p in config:
            if 'uuid' not in p: p['uuid'] = str(uuid.uuid4())[:8]
            if 'active' not in p: p['active'] = True
            
        self.current_config = config
        self.unused_pedals = [] # Clear unused on new generation
        
        self.refresh_lists()
        self.update_audio_engine()
        self.log("New tone applied.")

    def refresh_lists(self):
        # Unused List
        self.unused_list.delete(0, tk.END)
        for p in self.unused_pedals:
            self.unused_list.insert(tk.END, p.get('plugin', 'Unknown'))
            
        # Active List
        self.active_list.delete(0, tk.END)
        for i, p in enumerate(self.current_config):
            status = "🟢" if p.get('active', True) else "⚪"
            self.active_list.insert(tk.END, f"{status} {p.get('plugin', 'Unknown')}")

    def move_to_active(self):
        sel = self.unused_list.curselection()
        if not sel: return
        idx = sel[0]
        
        item = self.unused_pedals.pop(idx)
        # Add to active
        self.current_config.append(item)
        
        self.refresh_lists()
        self.update_audio_engine()

    def move_to_unused(self):
        sel = self.active_list.curselection()
        if not sel: return
        idx = sel[0]
        
        item = self.current_config.pop(idx)
        # Add to unused
        self.unused_pedals.append(item)
        
        self.refresh_lists()
        # Clear params if that one was selected
        for w in self.param_canvas.winfo_children(): w.destroy()
        self.update_audio_engine()

    def on_select_active(self, event):
        sel = self.active_list.curselection()
        if not sel: return
        idx = sel[0]
        if idx < len(self.current_config):
            self.show_params(self.current_config[idx], idx)

    def show_params(self, pedal, idx):
        # Clear current params
        for w in self.param_canvas.winfo_children():
            w.destroy()
            
        # Title
        tk.Label(self.param_canvas, text=f"{pedal['plugin']} Settings", font=("Arial", 12, "bold")).pack(pady=10)
        
        # Enable Switch
        is_on_var = tk.BooleanVar(value=pedal.get('active', True))
        def toggle_effect():
            pedal['active'] = is_on_var.get()
            self.refresh_lists() # Update icon
            self.active_list.selection_set(idx) # Restore selection
            self.update_audio_engine()

        tk.Checkbutton(self.param_canvas, text="Effect Active", variable=is_on_var, command=toggle_effect).pack(pady=5)
        
        # Params
        params = pedal.get('params', {})
        if not params:
            tk.Label(self.param_canvas, text="No adjustable parameters.").pack()
            
        for key, val in params.items():
            f = ttk.Frame(self.param_canvas)
            f.pack(fill="x", pady=2)
            
            # Label
            lbl = key.replace("_", " ").title()
            tk.Label(f, text=lbl, width=15, anchor="w").pack(side="left")
            
            # Slider Logic
            min_v, max_v = 0.0, 1.0
            if "hz" in key: max_v = 20000.0
            elif "ms" in key: max_v = 2000.0
            elif "db" in key: min_v, max_v = -60.0, 24.0
            
            # Helper to capture current key/pedal in closure
            def make_cb(k, p):
                return lambda v: self.on_param_change(k, v, p)

            var = tk.DoubleVar(value=float(val))
            s = ttk.Scale(f, from_=min_v, to=max_v, variable=var, command=make_cb(key, pedal))
            s.pack(side="right", fill="x", expand=True)

    def on_param_change(self, key, value, pedal):
        # Update model
        pedal['params'][key] = float(value)
        # Update audio
        self.update_audio_engine()

    def update_audio_engine(self):
        if self.audio.is_active():
            # Filter active pedals
            active_chain = [p for p in self.current_config if p.get('active', True)]
            self.audio.update_plugins(active_chain)

    def toggle_stream(self):
        if self.audio.is_active():
            self.audio.stop_stream()
            self.start_btn.config(text="Start Processing")
            self.log("Stream stopped.")
        else:
            in_d = self.input_combo.get()
            out_d = self.output_combo.get()
            if not in_d or not out_d: return
            
            active_chain = [p for p in self.current_config if p.get('active', True)]
            success, msg = self.audio.start_stream(in_d, out_d, active_chain)
            
            if success:
                self.start_btn.config(text="Stop Processing")
                self.log(f"Stream running: {in_d} -> {out_d}")
            else:
                messagebox.showerror("Error", msg)

if __name__ == "__main__":
    root = tk.Tk()
    app = PedalboardApp(root)
    root.mainloop()
