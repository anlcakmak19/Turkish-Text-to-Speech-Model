import os
import json
from pydub import AudioSegment
from config.settings import Config


class ChunkService:

    @staticmethod
    def chunk_audio(audio_path, transcript_json, chunks_wav_dir, chunks_txt_dir):
        os.makedirs(chunks_wav_dir, exist_ok=True)
        os.makedirs(chunks_txt_dir, exist_ok=True)

        with open(transcript_json, "r", encoding="utf-8") as f:
            words = json.load(f)["words"]

        audio = AudioSegment.from_wav(audio_path)

        transcripts = []
        audios = {}
        current_text = []
        chunk_start = words[0]["start"]
        chunk_id = 1

        def save_chunk(end_time):
            nonlocal chunk_id, chunk_start, current_text

            if not current_text:
                return

            text = "".join(current_text).strip()

            transcripts.append({
                "id": chunk_id,
                "start": chunk_start,
                "end": end_time,
                "text": text,
            })

            seg = audio[int(chunk_start * 1000) : int(end_time * 1000)]
            wav_file = os.path.join(chunks_wav_dir, f"chunk_{chunk_id}.wav")
            txt_file = os.path.join(chunks_txt_dir, f"chunk_{chunk_id}.txt")

            seg.export(wav_file, format="wav")
            with open(txt_file, "w", encoding="utf-8") as ftxt:
                ftxt.write(text)

            audios[chunk_id] = wav_file

            chunk_id += 1
            chunk_start = end_time
            current_text = []

        for w in words:
            current_text.append(w["text"])
            duration = w["end"] - chunk_start
            has_punct = w["text"].strip().endswith(Config.PUNCT)

            if Config.MIN_LEN <= duration <= Config.MAX_LEN and has_punct:
                save_chunk(w["end"])
            elif duration > Config.MAX_LEN:
                save_chunk(w["end"])

        if current_text:
            save_chunk(words[-1]["end"])

        mapping_file = os.path.join(os.path.dirname(chunks_wav_dir), "chunks_mapping.json")
        with open(mapping_file, "w", encoding="utf-8") as f:
            json.dump({"transcript": transcripts, "audio": audios}, f, indent=2)

        return {"transcript": transcripts, "audio": audios}
