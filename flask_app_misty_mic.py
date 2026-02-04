"""
Flask Application for F&M Computer Science Major Page
(Misty Mic Version - Corrected)
"""

from flask import Flask, render_template, request, jsonify
from mistyPy.Robot import Robot
import time
import io
import base64
from threading import Thread
# We use the same Google STT logic, just fed from a different source
from STT_google import transcribe_wav_bytes

app = Flask(__name__)
MISTY_IP = "192.168.1.3"

misty = Robot(MISTY_IP)
misty.set_default_volume(120) 

def speak_async(text):
    """Stops any current speech and tells Misty to speak asynchronously."""
    misty.stop_speaking()
    misty.speak(text)

# --- STANDARD ROUTES ---

@app.route('/')
def index():
    misty.stop_speaking()
    # Ensure this template exists, otherwise change back to 'index11-192.html'
    return render_template('index_misty.html')

@app.route('/cs')
def cs_page():
    return render_template('CS2page11-18.html')

# --- NEW MISTY MIC ROUTES ---

@app.route("/gemini_misty")
def GeminiMisty():
    """Renders the new HTML page specifically for Misty's Mic"""
    return render_template('gemini_misty_mic.html')

@app.route('/misty/start_listening', methods=["POST"])
def start_listening():
    print("Commanding Misty to start recording...")
    # FIX: Changed from start_recording to start_recording_audio
    misty.start_recording_audio("capture.wav")
    return jsonify({"status": "recording"})

@app.route('/misty/stop_and_process', methods=["POST"])
def stop_and_process():
    print("Commanding Misty to stop recording...")
    # FIX: Changed from stop_recording to stop_recording_audio
    misty.stop_recording_audio()
    
    # 1. WAIT: Recording takes a moment to save to Misty's internal storage
    time.sleep(1) 
    
    print("Downloading audio file from Misty (this takes a few seconds)...")
    try:
        # 2. DOWNLOAD: Fetch the file from the robot
        # This returns a JSON response containing the Base64 string of the audio
        audio_response = misty.get_audio_file("capture.wav")
        
        # Parse the response to get the raw base64 string
        b64_string = ""
        
        # Robust parsing to handle different mistyPy versions
        if isinstance(audio_response, dict) and "base64" in audio_response:
             b64_string = audio_response["base64"]
        elif isinstance(audio_response, str):
             b64_string = audio_response
        else:
            # Fallback if it's a requests.Response object
            try:
                b64_string = audio_response.json()["base64"]
            except Exception as parse_error:
                print(f"Could not parse audio response: {audio_response}")
                return jsonify({"error": "Failed to parse audio from Misty"}), 500

        # 3. CONVERT: Base64 string -> Raw Bytes
        audio_bytes = io.BytesIO(base64.b64decode(b64_string))
        
        # 4. TRANSCRIBE: Use your existing STT file
        text = transcribe_wav_bytes(audio_bytes)
        
        if text:
            print(f"Transcript: {text}")
            # Make Misty speak the result
            Thread(target=speak_async, args=(text,)).start()
            return jsonify({"text": text})
        else:
            print("Transcript was empty (silence or noise)")
            return jsonify({"text": ""})

    except Exception as e:
        print(f"Error processing Misty's audio: {e}")
        return jsonify({"error": str(e)}), 500

if __name__ == '__main__':
    print("Running Misty Mic Version on Port 5002")
    app.run(debug=True, host='0.0.0.0', port=5002)