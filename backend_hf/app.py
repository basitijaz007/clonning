import os
import torch
import gradio as gr
from TTS.api import TTS
import tempfile

# Force CPU if needed, but HF Spaces (Free) provides 16GB RAM and CPU
device = "cuda" if torch.cuda.is_available() else "cpu"
print(f"Using device: {device}")

# Agree to Coqui ToS automatically (Required for non-interactive environments like HF)
os.environ["COQUI_TOS_AGREED"] = "1"

# Load model
print("Loading XTTS-v2...")
tts = TTS("tts_models/multilingual/multi-dataset/xtts_v2").to(device)
# Note: In some versions you might need: tts = TTS("model_path", agree_to_tos=True)
# But environment variable is the most reliable way.
print("Model loaded!")

def predict(text, audio_file, language):
    if not text or not audio_file:
        return None, "Please provide both text and a reference audio file."
    
    # Create a temporary file for the output
    with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as temp_wav:
        output_path = temp_wav.name
    
    try:
        tts.tts_to_file(
            text=text,
            speaker_wav=audio_file,
            language=language,
            file_path=output_path
        )
        return output_path, None
    except Exception as e:
        return None, str(e)

# Gradio Interface
iface = gr.Interface(
    fn=predict,
    inputs=[
        gr.Textbox(label="Text to Speak", placeholder="Enter text here..."),
        gr.Audio(label="Reference Audio (Voice to Clone)", type="filepath"),
        gr.Dropdown(
            label="Language", 
            choices=["en", "es", "fr", "de", "it", "pt", "pl", "tr", "ru", "nl", "cs", "ar", "zh-cn", "ja", "hu", "ko"],
            value="en"
        )
    ],
    outputs=[
        gr.Audio(label="Cloned Voice Output"),
        gr.Textbox(label="Error Log")
    ],
    title="XTTS-v2 Voice Cloner",
    description="Clone any voice for free! Powered by Coqui XTTS-v2."
)

if __name__ == "__main__":
    iface.launch()
