from flask import Flask, render_template, request, jsonify
from mistyPy.Robot import Robot
import time, io, base64, threading
from threading import Thread
from STT_google import transcribe_wav_bytes
from misty_robot import MistyActions
import random 
import json
import logging
from datetime import datetime

app = Flask(__name__)
MISTY_IP = "192.168.1.3"

# --- 1. INITIALIZE ROBOT INTERFACES ---
misty = Robot(MISTY_IP)
misty_actions = MistyActions(MISTY_IP)
misty.set_default_volume(10) 
processing_lock = threading.Lock()

# Auto-start skill at launch
try:
    misty_actions.startSkill()
except:
    pass

def speak_async(text):
    misty.stop_speaking()
    time.sleep(0.1) 
    misty.speak(text)

# --- 2. CONFIGURE RESEARCH LOGGING ---
logger = logging.getLogger('misty_logger')
if not logger.handlers:
    logger.setLevel(logging.INFO)
    # delay=True prevents file lock issues during Flask startup
    file_handler = logging.FileHandler('misty_interactions.log', delay=True)
    formatter = logging.Formatter('%(asctime)s - %(message)s', datefmt='%Y-%m-%d %H:%M:%S')
    file_handler.setFormatter(formatter)
    logger.addHandler(file_handler)

# --- 3. LOGGING ROUTE (Used by global.js) ---
@app.route('/log_event', methods=["POST"])
def log_event():
    data = request.get_json()
    if not data:
        return jsonify({"status": "error"}), 400

    sess_id = data.get('sessionId', 'NO_SESS')
    event = data.get('event', 'UNKNOWN')
    details = data.get('details', 'N/A')
    page = data.get('page', 'N/A')
    
    log_entry = f"ID: {sess_id} | [{event}] | Page: {page} | Details: {details}"
    logger.info(log_entry)
    print(f"RESEARCH LOG: {log_entry}")
    return jsonify({"status": "logged"}), 200

# --- 4. NAVIGATION ROUTES & SESSION RESET ---
@app.route('/')
def index():
    # Reset Misty to a neutral state when someone returns to the home page
    misty.stop_speaking()
    misty.move_head(pitch=0, roll=0, yaw=0)
    misty.move_arms(0, 0)
    misty.change_led(255, 255, 255) # White light for "Ready"
    return render_template('index_misty.html')

@app.route('/cs')
def cs_page(): return render_template('CS2page11-18.html')

@app.route('/background')
def neuro_page(): return render_template('background.html')

@app.route('/team')
def data_page(): return render_template('team.html')

@app.route("/gemini_misty")
def gemini_page(): return render_template('gemini_misty_mic.html')

# --- 5. ROBOT CONTROL ROUTES ---
@app.route('/stop', methods=["POST"])
def stop_misty_route():
    try:
        misty.stop_speaking()
        misty.change_led(255, 0, 0) # Red for "Listening"
        return jsonify({"status": "success"}), 200
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500

@app.route('/RockPaperScissors', methods=["GET", "POST"])
def rps_route():
    if request.method == "POST":
        data = request.get_json()
        sess_id = data.get('sessionId', 'NO_SESS')
        
        moves = ["Rock", "Paper", "Scissors"]
        misty_move = random.choice(moves)
        
        logger.info(f"ID: {sess_id} | [GAME_RPS] | Details: Misty chose {misty_move}")

        def run_rps_sequence():
            misty.stop_speaking()
            # Countdown Sequence
            beats = [("Rock", 20, -40, [255,0,0]), ("Paper", -15, 40, [255,255,0]), ("Scissors", 20, -40, [255,165,0])]
            for word, pitch, arm, color in beats:
                misty.change_led(*color)
                misty.speak(word)
                misty.move_head(pitch=pitch, velocity=100)
                misty.move_arms(arm, arm, 100, 100)
                time.sleep(0.8)

            # Reveal
            misty.change_led(0, 255, 0)
            misty.display_image("e_Joy.jpg")
            misty.move_head(0, 100)
            misty.move_arms(0, 0, 100, 100)
            misty.speak(f"Shoot! I chose {misty_move}!")
            time.sleep(3)
            misty.display_image("e_DefaultContent.jpg")

        Thread(target=run_rps_sequence).start()
        return jsonify({"status": "playing", "misty_choice": misty_move})

    return render_template('RockPaperScissors.html')

# --- 6. GEMINI & SPEECH PROCESSING ---
@app.route('/misty/start_listening', methods=["POST"])
def start_listening():
    misty.start_recording_audio("capture.wav")
    # Immediate movement to signal attention
    misty_actions.executeActionScript([{'name': 'LookInDirection', 'args': ['up']}])
    return jsonify({"status": "recording"})

@app.route('/misty/stop_and_process', methods=["POST"])
def stop_and_process():
    data = request.get_json()
    sess_id = data.get('sessionId', 'NO_SESS')

    if not processing_lock.acquire(blocking=False):
        return jsonify({"status": "busy"}), 200
    try:
        misty.stop_recording_audio()
        time.sleep(2.0) 
        
        audio_response = misty.get_audio_file("capture.wav")
        raw_audio_data = None
        
        if hasattr(audio_response, "status_code") and audio_response.status_code == 200:
            if 'application/json' in audio_response.headers.get('Content-Type', ''):
                res = audio_response.json().get("result", audio_response.json())
                raw_audio_data = base64.b64decode(res.get("base64"))
            else:
                raw_audio_data = audio_response.content
        
        if raw_audio_data:
            # Feedback: Thinking Movements
            thinking_movements = [{'name': 'SetEyes', 'args': ['thinking']}, {'name': 'TiltHead', 'args': ['right', 'large']}]
            misty_actions.executeActionScript(thinking_movements)
            
            text = transcribe_wav_bytes(io.BytesIO(raw_audio_data))
            
            if text and text.strip():
                logger.info(f"ID: {sess_id} | [GEMINI_QUERY] | Details: {text}")

                gemini_script = misty_actions.get_gemini_actions(text)
                
                # Log full Gemini decision for research transparency
                logger.info(f"ID: {sess_id} | [GEMINI_RESPONSE_SCRIPT] | Details: {json.dumps(gemini_script)}")

                response_sequence = [{'name': 'SayText', 'args': [f"I heard you say: {text}."]}] + gemini_script
                misty_actions.executeActionScript(response_sequence)
                
                reply_text = next((a['args'][0] for a in gemini_script if a['name'] == 'SayText'), "")
                return jsonify({"user_text": text, "misty_reply": reply_text})

        misty.speak("I didn't catch that.") 
        return jsonify({"user_text": "...", "misty_reply": "I didn't catch that."})

    except Exception as e:
        print(f"Error: {e}")
        return jsonify({"error": str(e)}), 500
    finally:
        processing_lock.release()

@app.route('/speak', methods=["POST"])
def handle_speak():
    data = request.json
    text = data.get('text', '')
    if text:
        Thread(target=speak_async, args=(text,)).start()
        return jsonify({"status": "success"})
    return jsonify({"status": "error"}), 400

if __name__ == '__main__':
    # use_reloader=False is vital to prevent the double-start file lock issue
    app.run(debug=True, host='0.0.0.0', port=5001, threaded=True, use_reloader=False)