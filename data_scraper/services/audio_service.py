import os
import subprocess
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
        
        # Validate file size (should be at least 100KB)
        file_size = os.path.getsize(final)
        if file_size < 100000:
            os.remove(final)
            raise Exception(f"Downloaded file too small ({file_size} bytes). Download may have failed.")

        return final

    @staticmethod
    def convert_m4a_to_wav(input_file: str, output_file: str) -> str:
        try:
            # Use ffmpeg directly to convert M4A to WAV
            # This is more robust than pydub for handling incomplete/corrupted M4A files
            cmd = [
                'ffmpeg',
                '-i', input_file,
                '-acodec', 'pcm_s16le',
                '-ac', '1',  # Convert to mono
                '-y',  # Overwrite output file
                output_file
            ]
            
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=300)
            
            if result.returncode != 0:
                raise Exception(f"FFmpeg error: {result.stderr}")
            
            print(f"✅ WAV converted → {output_file}")
            return output_file
        except Exception as e:
            raise Exception(f"Conversion failed: {str(e)}")

if __name__ == "__main__":
    # Example usage
    url = "https://www.youtube.com/watch?v=dQw4w9WgXcQ"
    folder = "./test_audio"
    os.makedirs(folder, exist_ok=True)

    m4a_path = AudioService.download_youtube_audio(url, folder)