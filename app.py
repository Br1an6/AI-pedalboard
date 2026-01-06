import streamlit as st
import logging
import json
import threading

from ai_assistant import AIAssistant
from audio_manager import AudioManager

# Configure page
st.set_page_config(page_title="AI Pedalboard", page_icon="🎸", layout="wide")

# --- Custom CSS for Pedal Look ---
st.markdown("""
<style>
    div[data-testid="stExpander"] {
        background-color: #2b2b2b;
        border-radius: 10px;
        border: 2px solid #444;
    }
    .pedal-title {
        font-weight: bold;
        font-size: 1.2em;
        color: #f0f0f0;
        text-align: center;
        margin-bottom: 10px;
        border-bottom: 2px solid #666;
        padding-bottom: 5px;
    }
</style>
""", unsafe_allow_html=True)

# --- Resources (Cached) ---
@st.cache_resource
def get_audio_manager():
    return AudioManager()

@st.cache_resource
def get_ai_assistant():
    return AIAssistant()

audio = get_audio_manager()
ai = get_ai_assistant()

# --- Helper: Parameter Widgets ---
def render_param_widget(key, val, unique_key):
    """
    Returns an appropriate Streamlit widget for a given parameter based on its name.
    """
    label = key.replace("_", " ").title().replace(" Db", " (dB)").replace(" Hz", " (Hz)").replace(" Ms", " (ms)")
    
    # Heuristics for ranges
    try:
        val_float = float(val)
    except:
        # If not a number, return as is (text)
        return val

    if "mix" in key or "depth" in key or "feedback" in key or "level" in key or "damping" in key:
        # 0.0 to 1.0 range
        return st.slider(label, 0.0, 1.0, val_float, 0.01, key=unique_key)
    
    elif "db" in key:
        # Decibels (usually -60 to +24 or so)
        # Adjust min/max if the current value is outside standard bounds
        min_db = min(-60.0, val_float - 10)
        max_db = max(24.0, val_float + 10)
        return st.slider(label, min_db, max_db, val_float, 0.5, key=unique_key)
    
    elif "hz" in key:
        # Frequency
        return st.number_input(label, 0.0, 20000.0, val_float, 10.0, key=unique_key)
    
    elif "ms" in key:
        # Time
        return st.number_input(label, 0.0, 5000.0, val_float, 10.0, key=unique_key)
    
    else:
        # Generic fallback
        return st.number_input(label, value=val_float, key=unique_key)

# --- Sidebar ---
st.sidebar.title("🎛 Settings")

# 1. Model
st.sidebar.subheader("🧠 AI Model")
available_models = ai.get_available_models()
if available_models:
    default_idx = 0
    if ai.model in available_models:
        default_idx = available_models.index(ai.model)
    elif "gemma3:latest" in available_models:
        default_idx = available_models.index("gemma3:latest")
    
    selected_model = st.sidebar.selectbox("Select Model", available_models, index=default_idx)
    if selected_model != ai.model:
        ai.set_model(selected_model)
else:
    st.sidebar.error("No models found.")

st.sidebar.markdown("---")

# 2. Devices
st.sidebar.subheader("🔌 Audio Devices")
if st.sidebar.button("Refresh Devices"):
    st.rerun()

input_devices = audio.list_input_devices()
output_devices = audio.list_output_devices()

input_index = 0
output_index = 0

if "input_device" in st.session_state and st.session_state.input_device in input_devices:
    input_index = input_devices.index(st.session_state.input_device)
if "output_device" in st.session_state and st.session_state.output_device in output_devices:
    output_index = output_devices.index(st.session_state.output_device)

selected_input = st.sidebar.selectbox("Input", input_devices, index=input_index, key="input_device")
selected_output = st.sidebar.selectbox("Output", output_devices, index=output_index, key="output_device")

# 3. Stream Control
st.sidebar.markdown("---")
if audio.is_active():
    st.sidebar.success("● Audio is Streaming")
    if st.sidebar.button("Stop Processing", type="primary"):
        audio.stop_stream()
        st.rerun()
else:
    st.sidebar.warning("○ Audio is Stopped")
    if st.sidebar.button("Start Processing"):
        success, msg = audio.start_stream(selected_input, selected_output, st.session_state.get("current_config", []))
        if not success:
            st.error(f"Failed to start: {msg}")
        else:
            st.rerun()

# --- Main Area ---
st.title("🎸 AI Pedalboard")

if ai.is_running():
    st.caption(f"✅ AI Connected: {ai.model}")
else:
    st.error("❌ Ollama Local AI: Not Detected.")

st.markdown("### Describe your tone")
user_prompt = st.text_input("e.g., '80s hair metal solo', 'underwater ambient'", placeholder="Type description...")

if st.button("Generate Tone 🪄"):
    if not user_prompt:
        st.warning("Enter a description.")
    else:
        with st.spinner(f"Asking {ai.model}..."):
            config = ai.generate_pedal_config(user_prompt)
            if config:
                st.session_state["current_config"] = config
                st.success("Tone generated!")
                if audio.is_active():
                    audio.update_plugins(config)
            else:
                st.error("AI failed to return a valid configuration.")

# --- Display Sections ---
tab1, tab2 = st.tabs(["🎛 Pedalboard", "📝 Raw AI Response"])

with tab1:
    st.subheader("Current Pedal Chain")
    
    if "current_config" in st.session_state and st.session_state["current_config"]:
        config = st.session_state["current_config"]
        
        # Track if any value changed to update audio immediately
        config_changed = False
        
        cols_per_row = 4
        for i in range(0, len(config), cols_per_row):
            cols = st.columns(cols_per_row)
            for j in range(cols_per_row):
                if i + j < len(config):
                    idx = i + j
                    item = config[idx]
                    plugin_name = item.get('plugin', 'Unknown')
                    params = item.get('params', {})
                    
                    with cols[j]:
                        with st.container(border=True):
                            st.markdown(f"<div class='pedal-title'>{plugin_name}</div>", unsafe_allow_html=True)
                            
                            # Render interactive widgets for each param
                            new_params = {}
                            for key, val in params.items():
                                unique_key = f"pedal_{idx}_{key}"
                                new_val = render_param_widget(key, val, unique_key)
                                new_params[key] = new_val
                                
                                # Check for changes (rudimentary check)
                                if new_val != val:
                                    config_changed = True
                            
                            # Update config object in place
                            config[idx]['params'] = new_params

        # Apply updates if any slider moved
        if config_changed:
            st.session_state["current_config"] = config
            if audio.is_active():
                audio.update_plugins(config)
                # No toast here to avoid spamming while dragging
            
    else:
        st.info("No pedals configured. Start by generating a tone above!")

with tab2:
    st.subheader("Last AI Interaction")
    if ai.last_raw_response:
        st.text_area("Raw Response:", value=ai.last_raw_response, height=300)
        try:
            st.json(json.loads(ai.last_raw_response))
        except:
            st.info("Not valid JSON.")
    else:
        st.write("No data yet.")