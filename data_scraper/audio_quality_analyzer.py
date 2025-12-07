import os
import json
import subprocess
from pathlib import Path
import numpy as np
from config.settings import Config


class AudioQualityAnalyzer:
    """Analyze and compare audio quality between M4A source and WAV conversion"""

    @staticmethod
    def get_audio_stats(file_path: str) -> dict:
        """Extract detailed audio statistics using ffprobe"""
        try:
            cmd = [
                'ffprobe',
                '-v', 'error',
                '-select_streams', 'a:0',
                '-show_entries', 'stream=codec_name,sample_rate,channels,bit_rate,duration',
                '-of', 'json',
                file_path
            ]
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
            
            if result.returncode != 0:
                return {"error": "Failed to get audio stats"}
            
            data = json.loads(result.stdout)
            if not data.get('streams'):
                return {"error": "No audio streams found"}
            
            stream = data['streams'][0]
            return {
                "codec": stream.get('codec_name', 'unknown'),
                "sample_rate": int(stream.get('sample_rate', 0)),
                "channels": int(stream.get('channels', 0)),
                "bit_rate": int(stream.get('bit_rate', 0)) if stream.get('bit_rate') else 0,
                "duration": float(stream.get('duration', 0))
            }
        except Exception as e:
            return {"error": str(e)}

    @staticmethod
    def get_file_size_info(file_path: str) -> dict:
        """Get file size and calculate bitrate"""
        try:
            size_bytes = os.path.getsize(file_path)
            size_mb = size_bytes / (1024 * 1024)
            
            # Get duration from ffmpeg (more reliable than ffprobe)
            cmd = [
                'ffmpeg',
                '-i', file_path
            ]
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
            
            # Parse duration from ffmpeg output
            duration = 0
            for line in result.stderr.split('\n'):
                if 'Duration:' in line:
                    # Format: Duration: HH:MM:SS.ms, ...
                    time_str = line.split('Duration:')[1].split(',')[0].strip()
                    parts = time_str.split(':')
                    duration = int(parts[0]) * 3600 + int(parts[1]) * 60 + float(parts[2])
                    break
            
            # Calculate actual bitrate
            if duration > 0:
                actual_bitrate = (size_bytes * 8) / (duration * 1000)  # kbps
            else:
                actual_bitrate = 0
            
            return {
                "size_bytes": size_bytes,
                "size_mb": round(size_mb, 2),
                "duration_seconds": round(duration, 2),
                "actual_bitrate_kbps": round(actual_bitrate, 0)
            }
        except Exception as e:
            return {"error": str(e)}

    @staticmethod
    def compare_audio_files(m4a_path: str, wav_path: str) -> dict:
        """Compare quality metrics between M4A source and WAV conversion"""
        
        print(f"\n📊 Audio Quality Analysis Report")
        print(f"{'='*70}")
        
        # Get M4A stats
        print(f"\n🔹 M4A Source File: {os.path.basename(m4a_path)}")
        m4a_stats = AudioQualityAnalyzer.get_audio_stats(m4a_path)
        m4a_size = AudioQualityAnalyzer.get_file_size_info(m4a_path)
        
        print(f"   Codec: {m4a_stats.get('codec', 'N/A')}")
        print(f"   Sample Rate: {m4a_stats.get('sample_rate', 0):,} Hz")
        print(f"   Channels: {m4a_stats.get('channels', 0)}")
        print(f"   Declared Bitrate: {m4a_stats.get('bit_rate', 0) // 1000} kbps")
        print(f"   File Size: {m4a_size.get('size_mb', 0)} MB")
        print(f"   Duration: {m4a_size.get('duration_seconds', 0)} seconds")
        print(f"   Actual Bitrate: {m4a_size.get('actual_bitrate_kbps', 0)} kbps")
        
        # Get WAV stats
        print(f"\n🔹 WAV Converted File: {os.path.basename(wav_path)}")
        wav_stats = AudioQualityAnalyzer.get_audio_stats(wav_path)
        wav_size = AudioQualityAnalyzer.get_file_size_info(wav_path)
        
        print(f"   Codec: {wav_stats.get('codec', 'N/A')}")
        print(f"   Sample Rate: {wav_stats.get('sample_rate', 0):,} Hz")
        print(f"   Channels: {wav_stats.get('channels', 0)}")
        print(f"   Declared Bitrate: {wav_stats.get('bit_rate', 0) // 1000} kbps")
        print(f"   File Size: {wav_size.get('size_mb', 0)} MB")
        print(f"   Duration: {wav_size.get('duration_seconds', 0)} seconds")
        print(f"   Actual Bitrate: {wav_size.get('actual_bitrate_kbps', 0)} kbps")
        
        # Quality comparison
        print(f"\n{'='*70}")
        print(f"📈 Quality Comparison & Conversion Success Metrics")
        print(f"{'='*70}")
        
        m4a_duration = m4a_size.get('duration_seconds', 0)
        wav_duration = wav_size.get('duration_seconds', 0)
        duration_diff = abs(m4a_duration - wav_duration)
        
        print(f"\n✓ Duration Match:")
        print(f"  M4A: {m4a_duration}s | WAV: {wav_duration}s")
        if m4a_duration > 0:
            print(f"  Difference: {duration_diff:.2f}s ({(duration_diff/m4a_duration*100):.1f}%)")
        else:
            print(f"  Difference: Unable to calculate (duration not detected)")
        
        # File size comparison
        size_bytes_m4a = m4a_size.get('size_bytes', 0)
        size_bytes_wav = wav_size.get('size_bytes', 0)
        if size_bytes_m4a > 0:
            size_increase = ((size_bytes_wav - size_bytes_m4a) / size_bytes_m4a * 100)
        else:
            size_increase = 0
        print(f"\n✓ File Size Change:")
        print(f"  M4A: {m4a_size.get('size_mb', 0)} MB | WAV: {wav_size.get('size_mb', 0)} MB")
        print(f"  Increase: {size_increase:.1f}%")
        
        # Audio properties
        print(f"\n✓ Audio Properties:")
        print(f"  Sample Rate: {m4a_stats.get('sample_rate', 0)} Hz → {wav_stats.get('sample_rate', 0)} Hz")
        print(f"  Channels: {m4a_stats.get('channels', 0)} → {wav_stats.get('channels', 0)}")
        
        # Transcription suitability
        print(f"\n✓ Transcription Suitability:")
        sample_rate = wav_stats.get('sample_rate', 0)
        channels = wav_stats.get('channels', 0)
        
        suitability_score = 100
        notes = []
        
        if sample_rate >= 16000:
            print(f"  ✅ Sample Rate {sample_rate}Hz is suitable for transcription")
        elif sample_rate >= 8000:
            print(f"  ⚠️  Sample Rate {sample_rate}Hz is acceptable but lower quality expected")
            suitability_score -= 20
            notes.append("Lower sample rate may affect transcription accuracy")
        else:
            print(f"  ❌ Sample Rate {sample_rate}Hz is too low for good transcription")
            suitability_score -= 40
            notes.append("Very low sample rate will significantly hurt transcription")
        
        if channels == 1:
            print(f"  ✅ Mono audio is standard for transcription")
        else:
            print(f"  ⚠️  {channels} channels detected, mono is preferred")
            suitability_score -= 10
            notes.append("Multi-channel audio may need mixing")
        
        codec = wav_stats.get('codec', '')
        if 'pcm' in codec.lower():
            print(f"  ✅ PCM codec is ideal for transcription services")
        else:
            print(f"  ⚠️  Codec {codec} is acceptable")
            suitability_score -= 5
        
        print(f"\n{'='*70}")
        print(f"🎯 Overall Transcription Suitability: {max(0, suitability_score)}/100")
        print(f"{'='*70}")
        
        if notes:
            print(f"\n⚠️  Notes:")
            for note in notes:
                print(f"   • {note}")
        
        return {
            "m4a": {**m4a_stats, **m4a_size},
            "wav": {**wav_stats, **wav_size},
            "suitability_score": max(0, suitability_score)
        }

    @staticmethod
    def check_transcription_readiness(video_id: str) -> dict:
        """Check if a video's audio is ready for transcription"""
        base_dir = Config.BASE_DIR
        video_dir = os.path.join(base_dir, video_id)
        
        m4a_path = os.path.join(video_dir, "original.m4a")
        wav_path = os.path.join(video_dir, "original.wav")
        transcript_path = os.path.join(video_dir, "output_wav.json")
        
        print(f"\n🔍 Checking transcription readiness for: {video_id}")
        print(f"{'='*70}")
        
        # Check file existence
        m4a_exists = os.path.exists(m4a_path)
        wav_exists = os.path.exists(wav_path)
        transcript_exists = os.path.exists(transcript_path)
        
        print(f"✓ M4A file exists: {m4a_exists}")
        print(f"✓ WAV file exists: {wav_exists}")
        print(f"✓ Transcript exists: {transcript_exists}")
        
        if m4a_exists and wav_exists:
            comparison = AudioQualityAnalyzer.compare_audio_files(m4a_path, wav_path)
            
            # Load transcript if available
            transcript_preview = None
            if transcript_exists:
                try:
                    with open(transcript_path, 'r', encoding='utf-8') as f:
                        data = json.load(f)
                        if 'words' in data and len(data['words']) > 0:
                            words = [w['text'] for w in data['words'][:10]]
                            transcript_preview = ' '.join(words) + "..."
                except:
                    pass
            
            print(f"\n📝 Transcript Preview:")
            if transcript_preview:
                print(f"   {transcript_preview}")
            else:
                print(f"   (No transcript available yet)")
            
            return comparison
        else:
            print(f"\n❌ Missing audio files. Cannot compare.")
            return {}


if __name__ == "__main__":
    # Example usage: analyze the first processed video
    import sys
    
    if len(sys.argv) > 1:
        video_id = sys.argv[1]
    else:
        # Default to the example video
        video_id = "Ygu3ktENDYQ"
    
    AudioQualityAnalyzer.check_transcription_readiness(video_id)
