import os
import json
import shutil
from config.settings import Config
from services.audio_service import AudioService
from services.transcription_service import TranscriptionService
from services.chunk_service import ChunkService


class YouTubeProcessor:

    def __init__(self, url, crop_time=None):
      
        self.url = url
        self.video_id = url.split("v=")[-1]
        self.crop_time = crop_time
        self.crop_duration_seconds = None
        
        if self.crop_time:
            self.crop_duration_seconds = AudioService.parse_time_string(self.crop_time)

        self.folder = os.path.join(Config.BASE_DIR, self.video_id)
        os.makedirs(self.folder, exist_ok=True)

        self.m4a = os.path.join(self.folder, "original.m4a")
        self.wav = os.path.join(self.folder, "original.wav")
        self.transcript_json = os.path.join(self.folder, "output_wav.json")
        self.chunks_wav = os.path.join(self.folder, "chunks_wav")
        self.chunks_txt = os.path.join(self.folder, "chunks_text")
        self.mapping_json = os.path.join(self.folder, "chunks_mapping.json")

    def run(self):
        crop_info = f" (cropping to {self.crop_time})" if self.crop_time else ""
        print(f"\n🎬 Processing {self.url}{crop_info}")

        # 1) Download audio
        if not os.path.exists(self.m4a):
            AudioService.download_youtube_audio(self.url, self.folder)
            print("✅ original.m4a done")
        else:
            print("⏭️  original.m4a exists → skip")

        # 2) Convert (with optional cropping)
        if not os.path.exists(self.wav):
            if self.crop_duration_seconds:
                print(f"✂️  Converting and cropping to {self.crop_duration_seconds}s...")
                AudioService.convert_m4a_to_wav(
                    self.m4a, 
                    self.wav, 
                    crop_duration=self.crop_duration_seconds
                )
            else:
                AudioService.convert_m4a_to_wav(self.m4a, self.wav)
            print("✅ WAV done")
        else:
            print("⏭️  WAV exists → skip")
        
        # 3) Transcribe
        if not os.path.exists(self.transcript_json):
            print("🎤 Transcribing audio...")
            data = TranscriptionService.transcribe(self.wav)
            with open(self.transcript_json, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=2)
            print("✅ Transcript done")
        else:
            print("⏭️  Transcript exists → skip")

        
        # 4) Chunk
        if not os.path.exists(self.chunks_wav):
            print("✂️  Chunking audio...")
            ChunkService.chunk_audio(
                self.wav,
                self.transcript_json,
                self.chunks_wav,
                self.chunks_txt
            )
            print("✅ Chunks done")
        else:
            print("⏭️  Chunks already exist → skip")
            

        print(f"✅ Finished → {self.folder}")