import os
import json
import shutil
from config.settings import Config
from services.audio_service import AudioService
from services.transcription_service import TranscriptionService
from services.chunk_service import ChunkService


class YouTubeProcessor:

    def __init__(self, url):
        self.url = url
        self.video_id = url.split("v=")[-1]

        self.folder = os.path.join(Config.BASE_DIR, self.video_id)
        os.makedirs(self.folder, exist_ok=True)

        self.m4a = os.path.join(self.folder, "original.m4a")
        self.wav = os.path.join(self.folder, "original.wav")
        self.transcript_json = os.path.join(self.folder, "output_wav.json")
        self.chunks_wav = os.path.join(self.folder, "chunks_wav")
        self.chunks_txt = os.path.join(self.folder, "chunks_text")
        self.mapping_json = os.path.join(self.folder, "chunks_mapping.json")

    def run(self):
        print(f"\n🎬 Processing {self.url}")

        # 1) Download audio
        if not os.path.exists(self.m4a):
            AudioService.download_youtube_audio(self.url, self.folder)
        else:
            print("🎬 original.m4a exists → skip")

        # 2) Convert
        if not os.path.exists(self.wav):
            AudioService.convert_m4a_to_wav(self.m4a, self.wav)
        else:
            print("WAV exists → skip")
        
        # 3) Transcribe
        if not os.path.exists(self.transcript_json):
            data = TranscriptionService.transcribe(self.wav)
            with open(self.transcript_json, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=2)
        else:
            print("Transcript exists → skip")

        
        # 4) Chunk
        if not os.path.exists(self.chunks_wav):
            ChunkService.chunk_audio(
                self.wav,
                self.transcript_json,
                self.chunks_wav,
                self.chunks_txt
            )
        else:
            print("✂️ Chunks already exist → skip")
            

        print(f"Finished → {self.folder}")
