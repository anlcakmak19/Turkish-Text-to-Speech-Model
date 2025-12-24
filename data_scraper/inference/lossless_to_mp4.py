import os
from pathlib import Path
from moviepy.editor import AudioFileClip, ColorClip

def create_ultra_lossless_video(audio_path, output_path):
    """Convert a WAV audio file to MP4 with a black screen background."""
    try:
        # 1. Load the audio
        audio = AudioFileClip(audio_path)
        
        # 2. Determine Codec based on your needs
        # Most AI models (Torch/Tensorflow) output 32-bit Float.
        # Using 'aac' for MP4 compatibility
        audio_codec = 'aac'

        # 3. Create Black Screen
        video = ColorClip(size=(1280, 720), color=(0,0,0), duration=audio.duration)
        video = video.set_audio(audio)
        
        # 4. Write File as .MP4
        if output_path.endswith(".mov"):
            output_path = output_path.replace(".mov", ".mp4")

        print(f"Processing: {os.path.basename(audio_path)} -> {os.path.basename(output_path)}")
        
        video.write_videofile(
            output_path, 
            fps=1, 
            codec="libx264", 
            audio_codec=audio_codec,
            verbose=False,
            logger=None
        )
        print(f"✓ Completed: {os.path.basename(output_path)}\n")
        return True
    except Exception as e:
        print(f"✗ Error processing {audio_path}: {str(e)}\n")
        return False

def batch_convert_wav_to_mp4(inference_outputs_dir, mp4_output_dir):
    """Convert all WAV files from all folders in inference_outputs to MP4."""
    print("=" * 60)
    print("Starting batch conversion of WAV files to MP4")
    print("=" * 60 + "\n")
    
    # Create mp4 output directory if it doesn't exist
    os.makedirs(mp4_output_dir, exist_ok=True)
    
    total_files = 0
    successful = 0
    failed = 0
    
    # Iterate through all subdirectories in inference_outputs
    for subdir in sorted(os.listdir(inference_outputs_dir)):
        subdir_path = os.path.join(inference_outputs_dir, subdir)
        
        if not os.path.isdir(subdir_path):
            continue
        
        print(f"\nProcessing folder: {subdir}")
        print("-" * 60)
        
        # Find all WAV files in this subdirectory
        wav_files = sorted(Path(subdir_path).glob("*.wav"))
        
        if not wav_files:
            print(f"  No WAV files found in {subdir}/")
            continue
        
        print(f"  Found {len(wav_files)} WAV files\n")
        
        for wav_file in wav_files:
            total_files += 1
            # Create output filename based on input filename
            output_filename = wav_file.stem + ".mp4"
            output_path = os.path.join(mp4_output_dir, output_filename)
            
            if create_ultra_lossless_video(str(wav_file), output_path):
                successful += 1
            else:
                failed += 1
    
    # Print summary
    print("\n" + "=" * 60)
    print("Batch Conversion Summary")
    print("=" * 60)
    print(f"Total files processed: {total_files}")
    print(f"Successful: {successful}")
    print(f"Failed: {failed}")
    print(f"Output directory: {mp4_output_dir}")
    print("=" * 60)

if __name__ == "__main__":
    script_dir = os.path.dirname(os.path.abspath(__file__))
    inference_outputs_dir = os.path.join(script_dir, "inference_outputs")
    mp4_output_dir = os.path.join(script_dir, "mp4")
    
    batch_convert_wav_to_mp4(inference_outputs_dir, mp4_output_dir)