import pandas as pd
from processors.youtube_processor import YouTubeProcessor


if __name__ == "__main__":
    df = pd.read_csv("video_list_tr.csv")
    df = df.drop_duplicates(subset=["url"]).reset_index(drop=True)

    urls = df["url"].tolist()

    for url in urls:
        try:
            YouTubeProcessor(url).run()
        except Exception as e:
            print(f"❌ Error processing {url}: {e}")
