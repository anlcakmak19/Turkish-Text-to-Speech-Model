import os
from pydub import AudioSegment
import pandas as pd
import math

base_dir = "data_scraper/Sıla_data"

success_count = 0
minor_count = 0
fail_count = 0
total_folders = 0

global_chunk_durations = []  # for overall avg/min/max
all_rounded_durations = []   # for per-second count DataFrame

def check_video_folder(folder_path):
    global success_count, minor_count, fail_count, total_folders
    global global_chunk_durations, all_rounded_durations

    original_path = os.path.join(folder_path, "original.wav")
    chunks_dir = os.path.join(folder_path, "chunks_wav")

    if not os.path.exists(original_path):
        print(f"⚠️ No original.wav found in {folder_path}")
        return
    if not os.path.isdir(chunks_dir):
        print(f"⚠️ No chunks_wav folder found in {folder_path}")
        return

    total_folders += 1

    # Load original
    original_audio = AudioSegment.from_wav(original_path)
    original_duration = len(original_audio) / 1000.0  # seconds

    # Process chunks
    chunk_files = [f for f in os.listdir(chunks_dir) if f.endswith(".wav")]
    if not chunk_files:
        print(f"⚠️ No .wav files found in {chunks_dir}")
        return

    chunk_files.sort()
    chunk_durations = []

    for fname in chunk_files:
        fpath = os.path.join(chunks_dir, fname)
        try:
            audio = AudioSegment.from_wav(fpath)
            dur = len(audio) / 1000.0
            chunk_durations.append(dur)
            global_chunk_durations.append(dur)
            all_rounded_durations.append(math.ceil(dur))  # round up to nearest second
        except Exception as e:
            print(f"❌ Error reading {fpath}: {e}")

    total_chunks_duration = sum(chunk_durations)
    avg_chunk = sum(chunk_durations) / len(chunk_durations)
    min_chunk = min(chunk_durations)
    max_chunk = max(chunk_durations)

    diff = abs(original_duration - total_chunks_duration)

    print(f"\n🎬 Folder: {os.path.basename(folder_path)}")
    print(f"🎧 Original: {original_duration:.2f}s | 🔹 Chunks total: {total_chunks_duration:.2f}s | Δ = {diff:.3f}s")
    print(f"📊 Chunk stats → avg: {avg_chunk:.2f}s | min: {min_chunk:.2f}s | max: {max_chunk:.2f}s | count: {len(chunk_durations)}")

    if diff < 0.1:
        print("✅ Perfect match")
        success_count += 1
    elif diff < 10.0:
        print("⚠️ Minor difference (within 5s tolerance)")
        minor_count += 1
    else:
        print("❌ Large mismatch — missing or overlapping chunks")
        fail_count += 1

# --- Run for all subfolders ---
for folder in sorted(os.listdir(base_dir)):
    folder_path = os.path.join(base_dir, folder)
    if os.path.isdir(folder_path):
        check_video_folder(folder_path)

# --- Final summary ---
print("\n" + "="*55)
print("📊 SUMMARY REPORT")
print(f"📁 Total folders checked: {total_folders}")
print(f"✅ Perfect matches: {success_count}")
print(f"⚠️ Minor differences (<5s): {minor_count}")
print(f"❌ Large mismatches (>5s): {fail_count}")

# --- Total duration of all chunks ---
total_chunks_duration_all = sum(global_chunk_durations)
print(f"\n⏱️ TOTAL DURATION OF ALL CHUNKS: {total_chunks_duration_all:.2f}s "
      f"({total_chunks_duration_all / 60:.2f} minutes | "
      f"{total_chunks_duration_all / 3600:.2f} hours)")


if global_chunk_durations:
    global_avg = sum(global_chunk_durations) / len(global_chunk_durations)
    global_min = min(global_chunk_durations)
    global_max = max(global_chunk_durations)
    print("\n🎧 GLOBAL CHUNK STATS")
    print(f"   Avg duration: {global_avg:.2f}s")
    print(f"   Min duration: {global_min:.2f}s")
    print(f"   Max duration: {global_max:.2f}s")
    print(f"   Total chunks: {len(global_chunk_durations)}")

# --- Create per-second chunk count DataFrame ---
df = pd.DataFrame(all_rounded_durations, columns=["duration_sec"])
df_count = df.value_counts().sort_index().reset_index()
df_count.columns = ["duration_sec", "count"]

# Save DataFrame to CSV
csv_path = os.path.join(base_dir, "chunks_per_second.csv")
df_count.to_csv(csv_path, index=False)
print(f"\n✅ Per-second chunk counts saved to: {csv_path}")
print(df_count.head(10))

print("="*55)
