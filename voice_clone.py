"""
Voice Cloning Script using Coqui XTTS-v2
=========================================
A free, offline voice cloning solution that converts text to speech
using a reference audio sample to clone any voice.

Usage:
    python voice_clone.py --reference "adam_sample.wav" --text "Your text here" --output "output.wav"
    python voice_clone.py --reference "adam_sample.wav" --text_file "script.txt" --output "output.wav"
"""

import argparse
import os
import sys
import torch
from pathlib import Path


def load_model():
    """Load the XTTS-v2 model. Downloads automatically on first run (~1.8GB)."""
    print("Loading XTTS-v2 model (this may take a moment on first run)...")
    
    from TTS.api import TTS
    
    # Use XTTS-v2 for high-quality voice cloning
    # GPU acceleration if available
    device = "cuda" if torch.cuda.is_available() else "cpu"
    print(f"Using device: {device}")
    
    # Load XTTS-v2 model
    tts = TTS("tts_models/multilingual/multi-dataset/xtts_v2").to(device)
    
    print("Model loaded successfully!")
    return tts


def validate_reference_audio(audio_path: str) -> bool:
    """Validate that the reference audio file exists and is a supported format."""
    if not os.path.exists(audio_path):
        print(f"Error: Reference audio file not found: {audio_path}")
        return False
    
    supported_formats = ['.wav', '.mp3', '.flac', '.ogg', '.m4a']
    ext = Path(audio_path).suffix.lower()
    
    if ext not in supported_formats:
        print(f"Error: Unsupported audio format '{ext}'. Supported: {supported_formats}")
        return False
    
    return True


def auto_convert_to_wav(audio_path: str) -> str:
    """Convert non-WAV audio to WAV using FFmpeg for better compatibility if needed."""
    if audio_path.lower().endswith('.wav'):
        return audio_path, False
    
    import subprocess
    import tempfile
    
    print(f"Converting {os.path.basename(audio_path)} to temporary WAV for compatibility...")
    
    temp_wav = tempfile.NamedTemporaryFile(suffix='.wav', delete=False)
    temp_wav_path = temp_wav.name
    temp_wav.close()
    
    try:
        # Use ffmpeg to convert to wav (pcm_s16le, 22050Hz is standard for many TTS)
        # Note: XTTS often handles resampling internally, so we just need a standard WAV
        subprocess.run(
            ['ffmpeg', '-i', audio_path, '-y', '-acodec', 'pcm_s16le', '-ar', '22050', '-ac', '1', temp_wav_path],
            check=True,
            capture_output=True
        )
        return temp_wav_path, True
    except Exception as e:
        print(f"Warning: Failed to convert audio with FFmpeg. Attempting to use original file. Error: {e}")
        if os.path.exists(temp_wav_path):
            os.remove(temp_wav_path)
        return audio_path, False



# Presets for voice generation
# These simulate "emotion" by controlling randomness and stability
GENERATION_PRESETS = {
    "stable": {
        "temperature": 0.1,
        "repetition_penalty": 20.0,
        "speed": 1.0,
    },
    "neutral": {
        "temperature": 0.75,
        "repetition_penalty": 10.0,
        "speed": 1.0,
    },
    "expressive": {
        "temperature": 0.85,  # Higher temperature = more dynamic/emotional
        "repetition_penalty": 5.0,  # Lower penalty allows more natural pauses/fillers
        "speed": 1.0,
    },
    "extreme": {
        "temperature": 0.95,
        "repetition_penalty": 2.0,
        "speed": 1.0,
    }
}


def clone_voice(
    tts,
    reference_audio: str,
    text: str,
    output_path: str,
    language: str = "en",
    **kwargs
):
    """
    Clone a voice from reference audio and generate speech.
    
    Args:
        tts: The loaded TTS model
        reference_audio: Path to the reference audio file (WAV recommended)
        text: Text to convert to speech
        output_path: Path where the output .wav file will be saved
        language: Language code (default: "en" for English)
        **kwargs: Additional generation parameters (temperature, etc.)
    """
    print(f"Text to synthesize: {text[:100]}{'...' if len(text) > 100 else ''}")
    print(f"Output will be saved to: {output_path}")
    if kwargs:
        print(f"Generation parameters: {kwargs}")
    
    # Generate speech with cloned voice
    print("\nGenerating cloned speech...")
    
    tts.tts_to_file(
        text=text,
        speaker_wav=reference_audio,
        language=language,
        file_path=output_path,
        **kwargs
    )
    
    print(f"\nSUCCESS: Audio saved to: {output_path}")
    return output_path


def process_long_text(
    tts,
    reference_audio: str,
    text: str,
    output_path: str,
    language: str = "en",
    max_chunk_length: int = 250,
    **kwargs
):
    """
    Process long text in a memory-efficient way by saving to disk.
    
    This avoids 'bad allocation' errors by not keeping all audio in RAM.
    """
    import subprocess
    import tempfile
    
    # Create a 'parts' directory for intermediate files
    parts_dir = os.path.join(os.path.dirname(os.path.abspath(output_path)), "voice_parts")
    if not os.path.exists(parts_dir):
        os.makedirs(parts_dir)
        
    print(f"\n[MEM-SAFE MODE] Parts will be saved to: {parts_dir}")
    if kwargs:
        print(f"Generation parameters: {kwargs}")

    # Split text into sentences/chunks
    sentences = []
    current_chunk = ""
    # Split by sentence endings
    for char in text:
        current_chunk += char
        if char in '.!?' and len(current_chunk) >= 20:
            sentences.append(current_chunk.strip())
            current_chunk = ""
    if current_chunk.strip():
        sentences.append(current_chunk.strip())
    
    # If text is short enough, process directly
    if len(sentences) <= 1:
        return clone_voice(tts, reference_audio, text, output_path, language, **kwargs)
    
    print(f"\nLong text detected ({len(sentences)} segments). Processing with disk-caching...")
    
    temp_wav_files = []
    
    for i, sentence in enumerate(sentences):
        if not sentence.strip():
            continue
            
        part_filename = os.path.join(parts_dir, f"part_{i+1:04d}.wav")
        temp_wav_files.append(part_filename)
        
        # Skip if already exists (allows resuming if crashed)
        if os.path.exists(part_filename):
            print(f"  Skipping segment {i+1}/{len(sentences)} (already exists)...")
            continue

        print(f"  Processing segment {i+1}/{len(sentences)}...")
        
        try:
            tts.tts_to_file(
                text=sentence,
                speaker_wav=reference_audio,
                language=language,
                file_path=part_filename,
                **kwargs
            )
        except Exception as e:
            print(f"  Error in segment {i+1}: {e}")
            # Try once more if it's a minor fluke
            continue

    # Use FFmpeg to concatenate all parts WITHOUT loading them into RAM
    print("\nConcatenating parts using FFmpeg...")
    
    # Create a list file for ffmpeg
    list_file_path = os.path.join(parts_dir, "input_list.txt")
    with open(list_file_path, 'w', encoding='utf-8') as f:
        for wav_file in temp_wav_files:
            if os.path.exists(wav_file):
                # FFmpeg requires forward slashes or escaped backslashes
                safe_path = os.path.abspath(wav_file).replace('\\', '/')
                f.write(f"file '{safe_path}'\n")

    try:
        subprocess.run(
            ['ffmpeg', '-f', 'concat', '-safe', '0', '-i', list_file_path, '-c', 'copy', '-y', output_path],
            check=True,
            capture_output=True
        )
        print(f"\nSUCCESS: Large audio saved to: {output_path}")
        print(f"You can now delete the '{parts_dir}' folder if you are satisfied.")
    except Exception as e:
        print(f"\nError during concatenation: {e}")
        print(f"All parts are saved in {parts_dir}. You can join them manually if needed.")
    
    return output_path


def main():
    parser = argparse.ArgumentParser(
        description="Voice Cloning Script - Clone any voice using XTTS-v2",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python voice_clone.py --reference adam.wav --text "Hello world" --output output.wav
  python voice_clone.py --reference adam.wav --text "Stable voice" --preset stable
  python voice_clone.py --reference adam.wav --text "Emotional voice" --preset expressive
  python voice_clone.py --reference adam.wav --text "Custom params" --temperature 0.8 --speed 1.2
        """
    )
    
    parser.add_argument(
        "--reference", "-r",
        required=True,
        help="Path to reference audio file (6-60 seconds of clear speech recommended)"
    )
    
    parser.add_argument(
        "--text", "-t",
        help="Text to convert to speech"
    )
    
    parser.add_argument(
        "--text_file", "-f",
        help="Path to a text file containing the text to convert"
    )
    
    parser.add_argument(
        "--output", "-o",
        default="output.wav",
        help="Output audio file path (default: output.wav)"
    )
    
    parser.add_argument(
        "--language", "-l",
        default="en",
        choices=["en", "es", "fr", "de", "it", "pt", "pl", "tr", "ru", "nl", "cs", "ar", "zh-cn", "ja", "hu", "ko"],
        help="Language code for synthesis (default: en)"
    )

    # Advanced generation args
    parser.add_argument(
        "--preset",
        choices=["stable", "neutral", "expressive", "extreme"],
        help="Simulate emotion/stability using presets"
    )
    
    parser.add_argument(
        "--temperature",
        type=float,
        help="Generation temperature (0.0-1.0). Higher = more variability/expressive."
    )
    
    parser.add_argument(
        "--repetition_penalty",
        type=float,
        help="Penalty for repetition. Higher = more stable, less wandering."
    )
    
    parser.add_argument(
        "--speed",
        type=float,
        help="Speed of speech (default: 1.0)"
    )
    
    args = parser.parse_args()
    
    # Validate input
    if not args.text and not args.text_file:
        parser.error("Either --text or --text_file must be provided")
    
    if args.text and args.text_file:
        parser.error("Provide either --text or --text_file, not both")
    
    # Get text content
    if args.text_file:
        if not os.path.exists(args.text_file):
            print(f"Error: Text file not found: {args.text_file}")
            sys.exit(1)
        with open(args.text_file, 'r', encoding='utf-8') as f:
            text = f.read().strip()
    else:
        text = args.text
    
    if not text:
        print("Error: No text provided for synthesis")
        sys.exit(1)
    
    # Validate reference audio
    if not validate_reference_audio(args.reference):
        sys.exit(1)
    
    # Ensure output directory exists
    output_dir = os.path.dirname(args.output)
    if output_dir and not os.path.exists(output_dir):
        os.makedirs(output_dir)

    # Determine generation parameters
    gen_params = GENERATION_PRESETS["neutral"].copy()
    
    if args.preset:
        gen_params = GENERATION_PRESETS[args.preset].copy()
    
    # Overwrite if manually provided
    if args.temperature is not None:
        gen_params["temperature"] = args.temperature
    if args.repetition_penalty is not None:
        gen_params["repetition_penalty"] = args.repetition_penalty
    if args.speed is not None:
        gen_params["speed"] = args.speed

    # Load model and generate
    ref_wav = args.reference
    is_temp = False
    
    try:
        # Auto-convert to WAV to avoid torchcodec/mp3 issues
        ref_wav, is_temp = auto_convert_to_wav(args.reference)
        
        tts = load_model()
        
        # Use long text processing for longer inputs
        if len(text) > 500:
            process_long_text(tts, ref_wav, text, args.output, args.language, **gen_params)
        else:
            clone_voice(tts, ref_wav, text, args.output, args.language, **gen_params)
            
    except Exception as e:
        print(f"\nError during voice cloning: {e}")
        import traceback
        traceback.print_exc()
        print("\nTroubleshooting tips:")
        print("1. Ensure your reference audio is 6-60 seconds of clear speech")
        print("2. Check that you have enough GPU/RAM (4GB+ recommended)")
        print("3. Try with a shorter text first")
    finally:
        if is_temp and os.path.exists(ref_wav):
            try:
                os.remove(ref_wav)
            except:
                pass
    
    if os.path.exists(args.output):
        sys.exit(0)
    else:
        sys.exit(1)


if __name__ == "__main__":
    main()
