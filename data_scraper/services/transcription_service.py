import os
import requests
from config.settings import Config


class TranscriptionService:

    @staticmethod
    def transcribe(file_path: str) -> dict:
        headers = {"xi-api-key": Config.XI_API_KEY}
        files = {
            "file": (os.path.basename(file_path), open(file_path, "rb"), "audio/wav")
        }
        data = {"model_id": "scribe_v1"}

        response = requests.post(Config.STT_URL, headers=headers, files=files, data=data, verify=False)
        return response.json()

    @staticmethod
    def save_full_text(transcript: dict, file_path: str):
        text = " ".join(w["text"] for w in transcript["segments"][0]["words"])
        with open(file_path, "w", encoding="utf-8") as f:
            f.write(text)
        return text
