import sounddevice as sd
import numpy as np
import threading
import time
import json
import os
from vosk import Model, KaldiRecognizer

# -----------------------------
# CONFIG
# -----------------------------
RECORD_RATE = 44100
CHANNELS = 1                  # ✅ SINGLE microphone
RECORD_SECONDS = 5
DEVICE_NAME = "Microphone"    # partial name is OK
EXTRA_RECORD = 3

# -----------------------------
# VOSK MODEL PATH
# -----------------------------
VOSK_MODEL_PATH = r"C:\Users\oadefioy\vosk-model-small-en-us-0.15"

if not os.path.exists(VOSK_MODEL_PATH):
    raise RuntimeError(f"Vosk model not found at {VOSK_MODEL_PATH}")

vosk_model = Model(VOSK_MODEL_PATH)

# -----------------------------
# DEVICE LOOKUP
# -----------------------------
def get_device_index_by_name(name):
    devices = sd.query_devices()
    for idx, dev in enumerate(devices):
        if name.lower() in dev["name"].lower():
            return idx
    raise RuntimeError(
        f"Audio device '{name}' not found.\nAvailable devices:\n" +
        "\n".join(d["name"] for d in devices)
    )

# -----------------------------
# SPEECH-TO-TEXT
# -----------------------------
def transcribe_audio(audio, samplerate):
    recognizer = KaldiRecognizer(vosk_model, samplerate)
    recognizer.SetWords(True)

    audio_bytes = audio.astype(np.int16).tobytes()
    recognizer.AcceptWaveform(audio_bytes)
    result = json.loads(recognizer.Result())

    return result.get("text", "(no speech detected)").strip()

# -----------------------------
# ROBOT HEAD CONTROL (STUB)
# -----------------------------
def raise_head():
    """
    Replace this with Misty SDK call later.
    """
    
    # Raise head
    #misty.move_head(pitch=40, roll=0, yaw=0, velocity=50)

# -----------------------------
# STOP FLAG
# -----------------------------
stop_flag = False

def stop_recording_listener():
    global stop_flag
    input("Press ENTER to stop recording early...\n")
    stop_flag = True

# -----------------------------
# MAIN RECORDING FUNCTION
# -----------------------------
def record_and_transcribe(duration=RECORD_SECONDS, device_name=DEVICE_NAME):
    global stop_flag
    stop_flag = False
    stop_requested_time = None

    device_index = get_device_index_by_name(device_name)

    threading.Thread(
        target=stop_recording_listener,
        daemon=True
    ).start()

    print(f"Recording from device: {device_name}")
    print("Recording...")

    audio_chunks = []

    def callback(indata, frames, time_info, status):
        nonlocal stop_requested_time
        audio_chunks.append(indata.copy())

        if stop_flag and stop_requested_time is None:
            stop_requested_time = time.time()

        if stop_requested_time is not None:
            if time.time() - stop_requested_time >= EXTRA_RECORD:
                raise sd.CallbackStop()

    try:
        with sd.InputStream(
            samplerate=RECORD_RATE,
            channels=CHANNELS,
            dtype="int16",
            device=device_index,
            callback=callback
        ):
            sd.sleep((duration + EXTRA_RECORD) * 1000)
    except Exception as e:
        print(f"Recording stopped: {e}")

    if not audio_chunks:
        return "(no audio)"

    audio = np.concatenate(audio_chunks, axis=0).flatten()
    print("Recording complete.")

    # ✅ Raise head (no direction logic)
    raise_head()

    return transcribe_audio(audio, RECORD_RATE)

# -----------------------------
# TEST MAIN
# -----------------------------
if __name__ == "__main__":
    print(
        "Starting test recording.\n"
        "Press ENTER to stop early "
        "(5 seconds + 3 extra seconds recorded)."
    )

    transcript = record_and_transcribe()

    print("\n=== Test Results ===")
    print(f"Transcript: {transcript}")
    print("===================")
