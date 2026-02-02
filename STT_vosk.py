import json
import numpy as np
from vosk import Model, KaldiRecognizer
import wave

"""Use this for speech to text for based on the device the website is open on"""

VOSK_MODEL_PATH = r"C:\Users\oadefioy\vosk-model-small-en-us-0.15"
model = Model(VOSK_MODEL_PATH)

def transcribe_wav_bytes(wav_bytes):
    wf = wave.open(wav_bytes, "rb")

    recognizer = KaldiRecognizer(model, wf.getframerate())
    recognizer.SetWords(True)

    while True:
        data = wf.readframes(4000)
        if len(data) == 0:
            break
        recognizer.AcceptWaveform(data)

    result = json.loads(recognizer.Result())
    return result.get("text", "")
