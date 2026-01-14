from TTS.api import TTS
import torch

try:
    print("Loading XTTS model information...")
    # Using the same model path as voice_clone.py
    tts = TTS("tts_models/multilingual/multi-dataset/xtts_v2")
    print("\nSupported Languages:")
    print(tts.languages)
except Exception as e:
    print(f"Error: {e}")
