import streamlit as st
import logging
import json
import threading
import uuid
from streamlit_sortables import sort_items

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
    .st-emotion-cache-1wbqy5l { 
        /* Streamlit Sortables Container Style Override if needed */
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

# --- Helpers ---
def render_param_widget(key, val, unique_key):
    """
    Returns an appropriate Streamlit widget for a given parameter based on its name.
    """
    label = key.replace("_", " ").title().replace(" Db", " (dB)").replace(" Hz", " (Hz)").replace(" Ms", " (ms)")
    
    try:
        val_float = float(val)
    except:
        return val # Not a number

    # Heuristics for ranges
    if any(x in key for x in ["mix", "depth", "feedback", "level", "damping", "dry_level", "wet_level"]):
        return st.slider(label, 0.0, 1.0, val_float, 0.01, key=unique_key)
    
    elif "db" in key:
        min_db = min(-60.0, val_float - 10)
        max_db = max(24.0, val_float + 10)
        return st.slider(label, min_db, max_db, val_float, 0.5, key=unique_key)
    
    elif "hz" in key:
        return st.number_input(label, 0.0, 20000.0, val_float, 10.0, key=unique_key)
    
    elif "ms" in key:
        return st.number_input(label, 0.0, 5000.0, val_float, 10.0, key=unique_key)
    
    else:
        return st.number_input(label, value=val_float, key=unique_key)

def ensure_metadata(pedal_list):
    """
    Ensures every pedal dict has a 'uuid' and 'active' status.
    """
    for p in pedal_list:
        if 'uuid' not in p:
            p['uuid'] = str(uuid.uuid4())[:8]
        if 'active' not in p:
            p['active'] = True
    return pedal_list

def get_pedal_label(p):
    return f"{p['plugin']}::{p['uuid']}"

def parse_pedal_label(label):
    parts = label.split("::")
    if len(parts) == 2:
        return parts[0], parts[1]
    return label, None

# --- Sidebar ---
st.sidebar.title("🎛 Settings")

# 1. Model & Connection
st.sidebar.subheader("🧠 AI Settings")
current_url = ai.url
new_url = st.sidebar.text_input("Ollama URL", value=current_url)
if new_url != ai.url:
    ai.set_url(new_url)

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
    st.sidebar.error("No models found. Check URL.")

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
# Prepare active config for streaming
active_stream_config = []
if "current_config" in st.session_state:
    active_stream_config = [p for p in st.session_state["current_config"] if p.get('active', True)]

if audio.is_active():
    st.sidebar.success("● Audio is Streaming")
    if st.sidebar.button("Stop Processing", type="primary"):
        audio.stop_stream()
        st.rerun()
else:
    st.sidebar.warning("○ Audio is Stopped")
    if st.sidebar.button("Start Processing"):
        success, msg = audio.start_stream(selected_input, selected_output, active_stream_config)
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
                st.session_state["current_config"] = ensure_metadata(config)
                st.session_state["unused_pedals"] = [] # Clear unused on new generation? Or keep? Let's clear to start fresh.
                st.success("Tone generated!")
                if audio.is_active():
                    audio.update_plugins(st.session_state["current_config"])
            else:
                st.error("AI failed to return a valid configuration.")

# --- Display Sections ---
tab1, tab2 = st.tabs(["🎛 Pedalboard", "📝 Raw AI Response"])

with tab1:
    # Initialize States
    if "current_config" not in st.session_state:
        st.session_state["current_config"] = []
    if "unused_pedals" not in st.session_state:
        st.session_state["unused_pedals"] = []

    ensure_metadata(st.session_state["current_config"])
    ensure_metadata(st.session_state["unused_pedals"])

    # 1. Add New Pedal Interface
    st.markdown("#### Add Pedal")
    col_add1, col_add2 = st.columns([3, 1])
    all_plugins = list(audio.plugin_map.keys())
    with col_add1:
        new_pedal_name = st.selectbox("Select Effect", all_plugins)
    with col_add2:
        if st.button("Add to Unused"):
            # Create default params
            # We instantiate momentarily to get default params? 
            # Or just empty params and let defaults handle it? 
            # To show sliders, we ideally want default values.
            # We can try to instantiate a dummy to get defaults.
            try:
                dummy = audio.plugin_map[new_pedal_name]()
                # Extract params? Pedalboard objects don't easily export dict params 
                # unless we access properties.
                # For simplicity, we start with empty params and let the UI/Audio engine handle defaults.
                # But to render widgets we need initial values.
                # Let's check if we can inspect `dummy`.
                # We'll use a basic heuristic: just empty dict. 
                # The render loop might need to handle missing params by not showing them 
                # or we just rely on the user adding them? 
                # Actually, `audio_manager` builds it fine.
                # But for the UI sliders, we need keys.
                # Let's just create a basic entry.
                new_p = {'plugin': new_pedal_name, 'params': {}, 'uuid': str(uuid.uuid4())[:8], 'active': True}
                st.session_state["unused_pedals"].append(new_p)
                st.rerun()
            except Exception as e:
                st.error(f"Error creating pedal: {e}")

    st.markdown("---")
    
    # 2. Sortable Lists (Drag and Drop)
    st.subheader("Organize Chain")
    st.info("Drag between 'Unused' and 'Active' to add/remove. Drag within 'Active' to reorder.")
    
    # Prepare lists for sortables
    active_labels = [get_pedal_label(p) for p in st.session_state["current_config"]]
    unused_labels = [get_pedal_label(p) for p in st.session_state["unused_pedals"]]
    
    # Render Sortable
    sortable_list = [
        {'header': 'Unused Effects', 'items': unused_labels},
        {'header': 'Active Chain', 'items': active_labels}
    ]
    sorted_data = sort_items(sortable_list, multi_containers=True)
    new_unused_labels = sorted_data[0]['items']
    new_active_labels = sorted_data[1]['items']
    
    # Check for changes
    if new_active_labels != active_labels or new_unused_labels != unused_labels:
        # Reconstruct lists based on UUIDs
        all_pool = st.session_state["current_config"] + st.session_state["unused_pedals"]
        pool_map = {get_pedal_label(p): p for p in all_pool}
        
        new_active_config = []
        for lbl in new_active_labels:
            if lbl in pool_map:
                new_active_config.append(pool_map[lbl])
        
        new_unused_config = []
        for lbl in new_unused_labels:
            if lbl in pool_map:
                new_unused_config.append(pool_map[lbl])
                
        st.session_state["current_config"] = new_active_config
        st.session_state["unused_pedals"] = new_unused_config
        
        # Trigger update if streaming
        if audio.is_active():
             # Filter only enabled pedals
            active_filtered = [p for p in new_active_config if p.get('active', True)]
            audio.update_plugins(active_filtered)
            
        st.rerun()

    # 3. Active Pedal Controls
    st.subheader("🎛 Active Chain Controls")
    
    config = st.session_state["current_config"]
    if not config:
        st.caption("No pedals in active chain.")
    
    config_changed = False
    
    # We display them in the order of the chain
    for i, item in enumerate(config):
        plugin_name = item.get('plugin', 'Unknown')
        params = item.get('params', {})
        is_active = item.get('active', True)
        uuid_str = item.get('uuid', '')
        
        # Visual indication of active status
        status_icon = "🟢" if is_active else "⚪"
        expander_title = f"{status_icon} {plugin_name} (Position {i+1})"
        
        with st.expander(expander_title, expanded=is_active):
            # On/Off Switch
            col_sw, col_params = st.columns([1, 4])
            with col_sw:
                new_active = st.toggle("Enabled", value=is_active, key=f"active_{uuid_str}")
                if new_active != is_active:
                    item['active'] = new_active
                    config_changed = True
            
            with col_params:
                # If we don't have params yet (newly added), try to populate default keys?
                # This is tricky without inspecting the class. 
                # For now, we only show what we have.
                if not params:
                    st.caption("Default parameters active.")
                
                new_params = {}
                for key, val in params.items():
                    unique_key = f"pedal_{uuid_str}_{key}"
                    new_val = render_param_widget(key, val, unique_key)
                    new_params[key] = new_val
                    if new_val != val:
                        config_changed = True
                item['params'] = new_params

    # Update audio if controls changed
    if config_changed:
        st.session_state["current_config"] = config
        if audio.is_active():
            active_filtered = [p for p in config if p.get('active', True)]
            audio.update_plugins(active_filtered)

with tab2:
    st.subheader("Last AI Interaction")
    if ai.last_raw_response:
        st.text_area("Raw Response:", value=ai.last_raw_response, height=300)
    else:
        st.write("No data yet.")
