import os
import requests
from pytubefix import YouTube
from pytubefix.cli import on_progress
from config.settings import Config


class AudioService:

    @staticmethod
    def download_youtube_audio(url: str, output_folder: str) -> str:
        yt = YouTube(url, on_progress_callback=on_progress)
        best_audio = yt.streams.filter(only_audio=True).order_by("abr").last()

        temp = best_audio.download(output_path=output_folder)
        final = os.path.join(output_folder, "original.m4a")
        os.rename(temp, final)

        return final

    @staticmethod
    def convert_m4a_to_wav(input_file: str, output_file: str) -> str:
        with open(input_file, "rb") as f:
            response = requests.post(Config.CONVERT_URL, files={"file": f})

        if response.status_code != 200:
            raise Exception(f"Conversion failed: {response.status_code} {response.text}")

        with open(output_file, "wb") as wf:
            wf.write(response.content)

        print(f"✅ WAV converted → {output_file}")
        return output_file
