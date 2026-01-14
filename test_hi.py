from TTS.api import TTS
import os

try:
    print("Loading XTTS...")
    tts = TTS("tts_models/multilingual/multi-dataset/xtts_v2")
    
    print("Testing Hindi generation...")
    # Using adam_sample.mp3 if exists, else create dummy
    ref = "adam_sample.mp3"
    if not os.path.exists(ref):
        print("Adam sample not found, skipping generation test")
    else:
        tts.tts_to_file(
            text="Namaste, kaise ho?",
            speaker_wav=ref,
            language="hi",
            file_path="test_hi.wav"
        )
        print("Success! Hindi is supported.")

except Exception as e:
    print(f"Failed: {e}")
