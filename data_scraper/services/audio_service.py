import os
import subprocess
from pytubefix import YouTube
from pytubefix.cli import on_progress


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
    def parse_time_string(time_str: str) -> int:
        time_str = time_str.strip()
        if ',' in time_str:
            parts = time_str.split(',')
            minutes = int(parts[0])
            seconds = int(parts[1]) if len(parts) > 1 else 0
            return minutes * 60 + seconds
        else:
            # Just minutes
            return int(time_str) * 60

    @staticmethod
    def crop_audio(input_file: str, output_file: str, duration_seconds: int) -> str:
        try:
            cmd = [
                'ffmpeg',
                '-i', input_file,
                '-t', str(duration_seconds),  # Crop to this duration
                '-acodec', 'copy',  # Copy audio codec (faster, no re-encoding)
                '-y',  # Overwrite output file
                output_file
            ]
            
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=300)
            
            if result.returncode != 0:
                raise Exception(f"FFmpeg crop error: {result.stderr}")
            
            print(f"✅ Audio cropped to {duration_seconds}s → {output_file}")
            return output_file
        except Exception as e:
            raise Exception(f"Cropping failed: {str(e)}")

    @staticmethod
    def convert_m4a_to_wav(input_file: str, output_file: str, crop_duration: int = None) -> str:
       
        try:
            cmd = [
                'ffmpeg',
                '-i', input_file,
                '-acodec', 'pcm_s16le',
                '-ac', '1',  # Convert to mono
                '-y',  # Overwrite output file
            ]
            
            # Add duration limit if specified
            if crop_duration:
                cmd.extend(['-t', str(crop_duration)])
            
            cmd.append(output_file)
            
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=300)
            
            if result.returncode != 0:
                raise Exception(f"FFmpeg error: {result.stderr}")
            
            duration_info = f" (cropped to {crop_duration}s)" if crop_duration else ""
            print(f"✅ WAV converted{duration_info} → {output_file}")
            return output_file
        except Exception as e:
            raise Exception(f"Conversion failed: {str(e)}")


if __name__ == "__main__":
    # Example usage with cropping
    url = "https://www.youtube.com/watch?v=dQw4w9WgXcQ"
    folder = "./test_audio"
    os.makedirs(folder, exist_ok=True)

    # Download
    m4a_path = AudioService.download_youtube_audio(url, folder)
    
    # Parse time and crop during conversion
    time_str = "2,25"  # 90 minutes 25 seconds
    duration_seconds = AudioService.parse_time_string(time_str)
    
    # Convert with cropping
    wav_path = os.path.join(folder, "audio.wav")
    AudioService.convert_m4a_to_wav(m4a_path, wav_path, crop_duration=duration_seconds)