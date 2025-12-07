class Config:
    XI_API_KEY = "xx"   # ElevenLabs API key
    MIN_LEN = 4.0
    MAX_LEN = 17.0
    PUNCT = (".", "?", "!")
    BASE_DIR = "./videos"

    CONVERT_URL = "http://ovrargegpudev2:38009/convert/m4a-to-wav/"
    STT_URL = "https://api.elevenlabs.io/v1/speech-to-text"
