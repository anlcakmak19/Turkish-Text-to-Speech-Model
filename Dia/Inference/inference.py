import torch
import soundfile as sf
import os
from dia.model import Dia

# ---- CONFIG ----
device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
print(f"Using device: {device}")

local_ckpt = "/opt/app-root/src/vol2/dia-finetuning/checkpoints_deepl/ckpt_epoch5.pth" #pth of fine-tuned model
config_path = "dia/config_inference.json" # config.json we can dowloand from repo of dia

prompt_text = "[S2] Selamlar, nasılsın?"
output_dir = "outputs"
os.makedirs(output_dir, exist_ok=True)
output_path = os.path.join(output_dir, "single_prompt.wav")

# ---- LOAD MODEL ----
print("Loading Dia model...")
model = Dia.from_local(
    config_path=config_path,
    checkpoint_path=local_ckpt,
    device=device
)
print("Model loaded.")

# ---- INFERENCE ----
with torch.inference_mode():
    audio = model.generate(
        prompt_text,
        max_tokens=512,
        cfg_scale=1.0,
        temperature=1.0,
        top_p=0.95,
        use_cfg_filter=True,
        cfg_filter_top_k=35
    )

# ---- SAVE WAV ----
sf.write(output_path, audio, 44100)
print(f"WAV saved to: {output_path}")
