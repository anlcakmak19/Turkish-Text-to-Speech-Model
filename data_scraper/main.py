import pandas as pd
from processors.youtube_processor import YouTubeProcessor


if __name__ == "__main__":
    df = pd.read_csv("data.csv")
    df = df.drop_duplicates(subset=["url"]).reset_index(drop=True)

    print(f"Processing {len(df)} videos from data.csv\n")
    print("="*70)

    successful = 0
    failed = 0

    for idx, row in df.iterrows():
        url = row["url"]
        
        # Get crop settings from CSV if available
        crop_time = None
        if "crop" in df.columns and "time" in df.columns:
            should_crop = str(row.get("crop", "")).strip().upper() == "TRUE"
            time_str = str(row.get("time", "")).strip()
            
            if should_crop and time_str:
                crop_time = time_str
                print(f"\n>>> Video {idx + 1}/{len(df)}: {url}")
                print(f"Cropping enabled: {crop_time}")
            else:
                print(f"\n>>> Video {idx + 1}/{len(df)}: {url}")
                print(f"Processing full video (no cropping)")
        else:
            print(f"\n>>> Video {idx + 1}/{len(df)}: {url}")
            print(f"Processing full video")

        try:
            processor = YouTubeProcessor(url, crop_time=crop_time)
            processor.run()
            successful += 1
            print(f"Completed video {idx + 1}/{len(df)}")
        except Exception as e:
            failed += 1
            print(f"Error processing {url}: {e}")
            continue

 