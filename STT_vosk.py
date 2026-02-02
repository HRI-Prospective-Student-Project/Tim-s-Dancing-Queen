import json
import wave
from vosk import Model, KaldiRecognizer

"""
Speech-to-Text using Vosk.
Expects WAV audio passed as a BytesIO object.
"""

VOSK_MODEL_PATH = r"C:\Users\oadefioy\vosk-model-small-en-us-0.15"
model = Model(VOSK_MODEL_PATH)

def transcribe_wav_bytes(wav_io):
    """
    Transcribes WAV audio from a BytesIO object.
    Returns recognized text as a string.
    """

    # Open WAV from memory
    wf = wave.open(wav_io, "rb")

    # Safety checks (Vosk needs mono PCM)
    if wf.getnchannels() != 1:
        raise ValueError("Audio must be mono")
    if wf.getsampwidth() != 2:
        raise ValueError("Audio must be 16-bit PCM")

    recognizer = KaldiRecognizer(model, wf.getframerate())
    recognizer.SetWords(True)

    results = []

    while True:
        data = wf.readframes(4000)
        if len(data) == 0:
            break

        if recognizer.AcceptWaveform(data):
            res = json.loads(recognizer.Result())
            results.append(res)

    # Final result
    final_res = json.loads(recognizer.FinalResult())
    results.append(final_res)

    # Combine all text segments
    text = " ".join(r.get("text", "") for r in results)

    return text.strip()
