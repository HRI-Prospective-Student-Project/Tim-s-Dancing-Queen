from flask import Flask, render_template, request, jsonify
from mistyPy.Robot import Robot
import time, io, base64, threading
from threading import Thread
from STT_google import transcribe_wav_bytes

app = Flask(__name__)
MISTY_IP = "192.168.1.5"

# Initialize Misty
misty = Robot(MISTY_IP)
misty.set_default_volume(80) 
processing_lock = threading.Lock()

def speak_async(text):
    """Clears the buffer and makes Misty speak."""
    misty.stop_speaking()
    time.sleep(0.1) 
    misty.speak(text)

# --- NAVIGATION & STOP LOGIC ---

@app.route('/')
def index():
    """Stops all speech when returning home."""
    misty.stop_speaking()
    return render_template('index_misty.html')

@app.route('/stop', methods=["POST"])
def stop_misty_route():
    """Dedicated route to kill speech immediately."""
    misty.stop_speaking()
    return jsonify({"status": "stopped"})

# --- MAJOR PAGES ---

@app.route('/cs')
def cs_page(): return render_template('CS2page11-18.html')

@app.route('/neuro')
def neuro_page(): return render_template('neuropage11-18.html')

@app.route('/datascience')
def data_page(): return render_template('dataSci.html')

@app.route('/RockPaperScissors')
def rps_page():
    """Serves the Rock Paper Scissors game."""
    return render_template('RockPaperScissors.html')

# --- SPEAKING ROUTES ---

@app.route('/speak', methods=["POST"])
@app.route('/speakOnClick', methods=["POST"])
def handle_speak():
    data = request.json
    text = data.get('text', '')
    if text:
        Thread(target=speak_async, args=(text,)).start()
        return jsonify({"status": "success"})
    return jsonify({"status": "error"}), 400

@app.route('/directSpeak', methods=["POST"])
def direct_speak():
    """Specific route used by the RPS game logic."""
    data = request.json
    text = data.get('text', '')
    if text:
        Thread(target=speak_async, args=(text,)).start()
        return jsonify({"status": "success"})
    return jsonify({"status": "error"}), 400

@app.route('/mistyStart', methods=["POST"])
def misty_start():
    """Triggers Misty's reaction when a game round starts."""
    # Add misty movement logic here if desired
    return jsonify({"status": "success"})

# --- GEMINI MISTY MIC LOGIC ---

@app.route("/gemini_misty")
def gemini_page():
    return render_template('gemini_misty_mic.html')

@app.route('/misty/start_listening', methods=["POST"])
def start_listening():
    misty.start_recording_audio("capture.wav")
    return jsonify({"status": "recording"})

@app.route('/misty/stop_and_process', methods=["POST"])
def stop_and_process():
    if not processing_lock.acquire(blocking=False):
        return jsonify({"status": "busy"}), 200
    try:
        misty.stop_recording_audio()
        time.sleep(2.5) 
        audio_response = misty.get_audio_file("capture.wav")
        raw_audio_data = None
        
        if hasattr(audio_response, "status_code") and audio_response.status_code == 200:
            if 'application/json' in audio_response.headers.get('Content-Type', ''):
                res = audio_response.json().get("result", audio_response.json())
                raw_audio_data = base64.b64decode(res.get("base64"))
            else:
                raw_audio_data = audio_response.content
        
        if raw_audio_data:
            text = transcribe_wav_bytes(io.BytesIO(raw_audio_data))
            
            # --- PYTHON JUNK FILTER (Prevents Speaking) ---
            junk = ["silence", "motor noise", "noise", "static", "background"]
            if text and any(j in text.lower() for j in junk):
                text = "" # Wipes the text if it's just noise
            
            if text and text.strip():
                print(f"Misty heard: {text}")
                Thread(target=speak_async, args=(text,)).start()
                return jsonify({"text": text})
        
        # Fallback if noise or silence
        misty.speak("I didn't hear anything.") 
        return jsonify({"text": "I didn't hear anything."})
    finally:
        processing_lock.release()

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5001)