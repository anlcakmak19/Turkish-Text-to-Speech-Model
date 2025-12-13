import os
import re

VIDEOS_DIR = "data_scraper/Sıla_data"
chunk_pattern = re.compile(r"chunk_(\d+)\.(txt|wav)$")

for folder in sorted(os.listdir(VIDEOS_DIR)):
    folder_path = os.path.join(VIDEOS_DIR, folder)
    if not os.path.isdir(folder_path):
        continue

    text_dir = os.path.join(folder_path, "chunks_text")
    wav_dir = os.path.join(folder_path, "chunks_wav")

    if not os.path.exists(text_dir) or not os.path.exists(wav_dir):
        print(f"❌ {folder}: Missing 'chunks_text' or 'chunks_wav'")
        continue

    # Collect chunk IDs
    text_chunks = set()
    for f in os.listdir(text_dir):
        m = chunk_pattern.match(f)
        if m and m.group(2) == "txt":
            text_chunks.add(int(m.group(1)))

    wav_chunks = set()
    for f in os.listdir(wav_dir):
        m = chunk_pattern.match(f)
        if m and m.group(2) == "wav":
            wav_chunks.add(int(m.group(1)))

    # Compare sets
    missing_txt = wav_chunks - text_chunks
    missing_wav = text_chunks - wav_chunks

    if not missing_txt and not missing_wav:
        print(f"✅ {folder}: All chunks match ({len(text_chunks)} total)")
    else:
        print(f"⚠️ {folder}: MISMATCH found")
        if missing_txt:
            print(f"   - Missing TXT for chunks: {sorted(missing_txt)}")
        if missing_wav:
            print(f"   - Missing WAV for chunks: {sorted(missing_wav)}")
