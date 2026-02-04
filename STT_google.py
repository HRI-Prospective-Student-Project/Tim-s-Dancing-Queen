import speech_recognition as sr
import io
import subprocess
import imageio_ffmpeg

"""
Speech-to-Text using Google Web Speech API.
Uses direct FFmpeg (via imageio-ffmpeg) to convert WebM/Ogg to WAV.
"""

def transcribe_wav_bytes(input_data):
    """
    1. Converts WebM/Ogg audio to WAV using FFmpeg.
    2. Sends the WAV to Google for transcription.
    """
    
    # --- PART 1: CONVERT AUDIO (Keep this! It fixes the browser format issue) ---
    
    # 1. Get raw bytes from input
    if isinstance(input_data, io.BytesIO):
        input_data.seek(0)
        audio_bytes = input_data.read()
    else:
        audio_bytes = input_data

    # 2. Get the path to the FFmpeg executable
    ffmpeg_exe = imageio_ffmpeg.get_ffmpeg_exe()

    # 3. Define the FFmpeg conversion command
    command = [
        ffmpeg_exe,
        '-i', 'pipe:0',    # Read from memory
        '-ar', '16000',    # 16kHz
        '-ac', '1',        # Mono
        '-f', 'wav',       # WAV format
        '-hide_banner',
        '-loglevel', 'error', 
        'pipe:1'           # Write to memory
    ]

    try:
        process = subprocess.Popen(
            command,
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE
        )
        wav_data, stderr_data = process.communicate(input=audio_bytes)
        
        if process.returncode != 0:
            print(f"FFmpeg Error: {stderr_data.decode()}")
            return "Error processing audio"

    except Exception as e:
        print(f"Subprocess Error: {e}")
        return "Error processing audio"

    # --- PART 2: GOOGLE SPEECH RECOGNITION ---
    
    recognizer = sr.Recognizer()
    
    # Load the converted WAV data into SpeechRecognition
    wav_io = io.BytesIO(wav_data)
    
    try:
        with sr.AudioFile(wav_io) as source:
            # Read the entire audio file
            audio = recognizer.record(source)
            
        # Send to Google (uses the free web API)
        # Note: This requires an internet connection!
        print("Sending to Google...")
        text = recognizer.recognize_google(audio)
        print(f"Google says: {text}")
        return text

    except sr.UnknownValueError:
        # Google couldn't understand the audio
        return ""
    except sr.RequestError as e:
        # Could not request results (internet down or API block)
        print(f"Could not request results from Google Service; {e}")
        return "Error connecting to Google"
    except Exception as e:
        print(f"General Error: {e}")
        return ""