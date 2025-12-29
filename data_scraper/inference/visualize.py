import os
import subprocess
from pathlib import Path

# Get absolute paths based on script location
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
INPUT_FOLDER = os.path.join(SCRIPT_DIR, "inference_outputs")
OUTPUT_FOLDER = os.path.join(SCRIPT_DIR, "mp4_frequency_spectrum")

# Ensure output folder exists
os.makedirs(OUTPUT_FOLDER, exist_ok=True)

def generate_aurora_visualizer(input_path, output_path):
    """
    Creates a Frequency Spectrum visualizer by splitting audio into Bass/Mids/Treble:
    1. Bass Layer (Deep Orange) - Low frequencies (0-200 Hz)
    2. Mids Layer (Lime Green)  - Mid frequencies (200 Hz - 4 kHz)
    3. Treble Layer (Deep Sky Blue) - High frequencies (4+ kHz)
    """
    
    # --- FREQUENCY SPECTRUM FILTER ---
    # Split audio into three frequency bands and display with different colors
    filter_complex = (
        "[0:a]lowpass=f=200[bass];"
        "[0:a]highpass=f=200,lowpass=f=4000[mids];"
        "[0:a]highpass=f=4000[treble];"
        "[bass]volume=0.8[a1];"
        "[mids]volume=0.8[a2];"
        "[treble]volume=0.8[a3];"
        "[a1][a2][a3]amerge=inputs=3[merged];"
        "[merged]showwaves=s=1280x720:mode=cline:colors=0xFF4500|0x00FF00|0x00BFFF[v]"
    )
    
    cmd = [
        "ffmpeg", "-y",
        "-i", input_path,
        "-filter_complex", filter_complex,
        "-map", "[v]",       # Use our cool video
        "-map", "0:a",       # Use original audio
        "-c:v", "mpeg4",     # Use mpeg4 codec (available in all ffmpeg builds)
        "-q:v", "5",         # Quality (lower = better, 2-8 recommended)
        "-pix_fmt", "yuv420p",
        "-c:a", "aac",       # Use AAC for MP4 compatibility
        "-shortest",
        output_path
    ]

    try:
        print(f"🎵 Generating Frequency Spectrum: {os.path.basename(output_path)}...")
        subprocess.run(cmd, check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        print(f"✓ Completed: {os.path.basename(output_path)}\n")
    except subprocess.CalledProcessError as e:
        print(f"❌ Error processing {os.path.basename(input_path)}: {e.stderr.decode()}\n")

# --- RUN LOOP ---
print("=" * 60)
print("Starting Frequency Spectrum Batch Processing")
print("Bass (Orange) | Mids (Green) | Treble (Blue)")
print("=" * 60 + "\n")

total_files = 0
processed = 0

# Recursively search all subdirectories in inference_outputs
for wav_file in sorted(Path(INPUT_FOLDER).rglob("*.wav")):
    total_files += 1
    # Create output filename preserving the structure info
    out_filename = f"{wav_file.stem}_aurora.mp4"
    out_file = os.path.join(OUTPUT_FOLDER, out_filename)
    generate_aurora_visualizer(str(wav_file), out_file)
    processed += 1

print("=" * 60)
print(f"✨ Done! Processed {processed}/{total_files} files")
print(f"📂 Output folder: {OUTPUT_FOLDER}")
print("=" * 60)