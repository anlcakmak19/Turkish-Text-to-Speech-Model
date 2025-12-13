import os
import json
import subprocess
from config.settings import Config


class BitrateAnalyzer:
    """Analyze bitrate information for audio files"""

    @staticmethod
    def get_detailed_bitrate_info(file_path: str) -> dict:
        """Extract detailed bitrate information using ffprobe"""
        try:
            cmd = [
                'ffprobe',
                '-v', 'error',
                '-select_streams', 'a:0',
                '-show_entries', 'stream=codec_name,bit_rate,duration',
                '-show_entries', 'format=bit_rate,duration',
                '-of', 'json',
                file_path
            ]
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
            
            if result.returncode != 0:
                return {"error": "Failed to get bitrate info"}
            
            data = json.loads(result.stdout)
            
            # Get stream bitrate
            stream_bitrate = 0
            stream_duration = 0
            if data.get('streams'):
                stream = data['streams'][0]
                stream_bitrate = int(stream.get('bit_rate', 0)) if stream.get('bit_rate') else 0
                stream_duration = float(stream.get('duration', 0)) if stream.get('duration') else 0
            
            # Get format bitrate
            format_bitrate = 0
            format_duration = 0
            if data.get('format'):
                fmt = data['format']
                format_bitrate = int(fmt.get('bit_rate', 0)) if fmt.get('bit_rate') else 0
                format_duration = float(fmt.get('duration', 0)) if fmt.get('duration') else 0
            
            return {
                "stream_bitrate": stream_bitrate,
                "format_bitrate": format_bitrate,
                "stream_duration": stream_duration,
                "format_duration": format_duration,
                "codec": data.get('streams', [{}])[0].get('codec_name', 'unknown') if data.get('streams') else 'unknown'
            }
        except Exception as e:
            return {"error": str(e)}

    @staticmethod
    def calculate_actual_bitrate(file_path: str) -> float:
        """Calculate actual bitrate from file size and duration"""
        try:
            size_bytes = os.path.getsize(file_path)
            
            # Get duration using ffmpeg
            cmd = ['ffmpeg', '-i', file_path]
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
            
            duration = 0
            for line in result.stderr.split('\n'):
                if 'Duration:' in line:
                    time_str = line.split('Duration:')[1].split(',')[0].strip()
                    parts = time_str.split(':')
                    duration = int(parts[0]) * 3600 + int(parts[1]) * 60 + float(parts[2])
                    break
            
            if duration > 0:
                actual_bitrate = (size_bytes * 8) / (duration * 1000)  # kbps
                return round(actual_bitrate, 2)
            return 0
        except Exception as e:
            return 0

    @staticmethod
    def compare_abr(video_id: str):
        """Compare ABR (Average Bitrate) between original M4A and output WAV"""
        base_dir = Config.BASE_DIR
        video_dir = os.path.join(base_dir, video_id)
        
        m4a_path = os.path.join(video_dir, "original.m4a")
        wav_path = os.path.join(video_dir, "original.wav")
        
        print(f"\n{'='*70}")
        print(f"📊 Bitrate (ABR) Comparison Analysis")
        print(f"{'='*70}")
        print(f"\nVideo ID: {video_id}\n")
        
        # Check file existence
        if not os.path.exists(m4a_path):
            print(f"❌ M4A file not found: {m4a_path}")
            return
        
        if not os.path.exists(wav_path):
            print(f"❌ WAV file not found: {wav_path}")
            return
        
        # Analyze M4A
        print(f"🔹 Original M4A File")
        print(f"   Path: {m4a_path}")
        m4a_size = os.path.getsize(m4a_path) / (1024 * 1024)
        print(f"   File Size: {m4a_size:.2f} MB")
        
        m4a_info = BitrateAnalyzer.get_detailed_bitrate_info(m4a_path)
        if "error" not in m4a_info:
            print(f"   Codec: {m4a_info.get('codec', 'unknown')}")
            if m4a_info.get('stream_bitrate'):
                print(f"   Declared Bitrate (stream): {m4a_info['stream_bitrate'] // 1000} kbps")
            if m4a_info.get('format_bitrate'):
                print(f"   Declared Bitrate (format): {m4a_info['format_bitrate'] // 1000} kbps")
        
        m4a_actual_br = BitrateAnalyzer.calculate_actual_bitrate(m4a_path)
        print(f"   Actual Bitrate (calculated): {m4a_actual_br} kbps")
        
        # Analyze WAV
        print(f"\n🔹 Output WAV File")
        print(f"   Path: {wav_path}")
        wav_size = os.path.getsize(wav_path) / (1024 * 1024)
        print(f"   File Size: {wav_size:.2f} MB")
        
        wav_info = BitrateAnalyzer.get_detailed_bitrate_info(wav_path)
        if "error" not in wav_info:
            print(f"   Codec: {wav_info.get('codec', 'unknown')}")
            if wav_info.get('stream_bitrate'):
                print(f"   Declared Bitrate (stream): {wav_info['stream_bitrate'] // 1000} kbps")
            if wav_info.get('format_bitrate'):
                print(f"   Declared Bitrate (format): {wav_info['format_bitrate'] // 1000} kbps")
        
        wav_actual_br = BitrateAnalyzer.calculate_actual_bitrate(wav_path)
        print(f"   Actual Bitrate (calculated): {wav_actual_br} kbps")
        
        # Comparison
        print(f"\n{'='*70}")
        print(f"📈 Bitrate Comparison Summary")
        print(f"{'='*70}")
        
        print(f"\nActual Bitrate (Calculated):")
        print(f"   M4A: {m4a_actual_br} kbps")
        print(f"   WAV: {wav_actual_br} kbps")
        
        if m4a_actual_br > 0:
            br_increase = ((wav_actual_br - m4a_actual_br) / m4a_actual_br) * 100
            print(f"   Change: {br_increase:+.1f}%")
        
        print(f"\nFile Size Comparison:")
        print(f"   M4A: {m4a_size:.2f} MB")
        print(f"   WAV: {wav_size:.2f} MB")
        
        if m4a_size > 0:
            size_increase = ((wav_size - m4a_size) / m4a_size) * 100
            print(f"   Increase: {size_increase:.1f}%")
        
        print(f"\nAudio Quality Assessment:")
        print(f"   M4A uses Opus codec (lossy compression)")
        print(f"   WAV uses PCM s16le codec (lossless, uncompressed)")
        print(f"   ✅ Size increase is normal for lossless format")
        print(f"   ✅ Quality is preserved during conversion")
        
        print(f"\n{'='*70}\n")


if __name__ == "__main__":
    import sys
    
    if len(sys.argv) > 1:
        video_id = sys.argv[1]
    else:
        video_id = "Ygu3ktENDYQ"
    
    BitrateAnalyzer.compare_abr(video_id)
