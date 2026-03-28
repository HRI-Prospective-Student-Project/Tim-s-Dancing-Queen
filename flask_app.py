from flask import Flask, render_template, request, jsonify
from mistyPy.Robot import Robot
import time, io, base64, threading
from threading import Thread
from STT_google import transcribe_wav_bytes
from misty_robot import MistyActions
import random 
import json
import re
import logging
from datetime import datetime

app = Flask(__name__)

# --- 1. INITIALIZE ROBOT INTERFACES ---
MISTY_IP = "192.168.1.3"
misty = Robot(MISTY_IP)
misty_actions = MistyActions(MISTY_IP)
misty.set_default_volume(30) 
processing_lock = threading.Lock()

# Auto-start skill at launch
try:
    misty_actions.startSkill()
except:
    pass

def misty_neutral(velocity=60):
    """Helper function to reset Misty to a neutral state."""
    misty.move_head(pitch=0, roll=0, yaw=0, velocity=velocity)
    misty.move_arms(90, 90, velocity, velocity)
    misty.change_led(255, 255, 255) # White light

def speak_async(text):
    misty.stop_speaking()
    time.sleep(0.1) 
    misty.speak(text)

# --- 2. CONFIGURE RESEARCH LOGGING ---
logger = logging.getLogger('misty_logger')
if not logger.handlers:
    logger.setLevel(logging.INFO)
    file_handler = logging.FileHandler('misty_interactions.log', delay=True)
    formatter = logging.Formatter('%(asctime)s - %(message)s', datefmt='%Y-%m-%d %H:%M:%S')
    file_handler.setFormatter(formatter)
    logger.addHandler(file_handler)

# --- 3. LOGGING ROUTE ---
@app.route('/log_event', methods=["POST"])
def log_event():
    data = request.get_json(silent=True)
    if not data:
        return jsonify({"status": "ignored"}), 200

    sess_id = data.get('sessionId', 'NO_SESS')
    event = data.get('event', 'UNKNOWN')
    details = data.get('details', 'N/A')
    page = data.get('page', 'N/A')
    
    log_entry = f"ID: {sess_id} | [{event}] | Page: {page} | Details: {details}"
    logger.info(log_entry)
    print(f"RESEARCH LOG: {log_entry}")
    return jsonify({"status": "logged"}), 200

# --- 4. NAVIGATION ROUTES ---
@app.route('/')
def index():
    misty.stop_speaking()
    misty_neutral()
    return render_template('index_misty.html')

@app.route('/cs')
def cs_page(): 
    misty_neutral()
    return render_template('CS2page11-18.html')

@app.route('/background')
def neuro_page(): 
    misty_neutral()
    return render_template('background.html')

@app.route('/team')
def data_page(): 
    def turn_point():
        # 1. TURN THE BASE (The Tracks)
        # drive_time(linear_velocity, angular_velocity, time_ms)
        # Angular 50 turns her left. 1500ms is roughly a 45-degree turn.
        misty.drive_time(0, 50, 1500) 
        time.sleep(1.6) # Wait for the physical turn to finish

        # 2. POINT THE ARMS
        misty.move_arms(90, 90, 60, 60)
        misty.change_led(0, 255, 0) # Green for "Presenting"
        
        time.sleep(3.0) # Hold the pose
        
        # 3. RETURN TO CENTER
        # Angular -50 turns her back to the right.
        misty.drive_time(0, -50, 1500)
        time.sleep(1.6)
        
        misty_neutral()

    # Start the movement in the background so the page loads immediately
    threading.Thread(target=turn_point).start()
    return render_template('team.html')

@app.route("/gemini_misty")
def gemini_page(): 
    misty_neutral()
    return render_template('gemini_misty_mic.html')

# --- 5. ROBOT CONTROL ROUTES ---
@app.route('/stop', methods=["POST"])
def stop_misty_route():
    try:
        misty.stop_speaking()
        misty_neutral(velocity=100) # Fast reset on stop
        return jsonify({"status": "success"}), 200
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500

@app.route('/RockPaperScissors', methods=["GET", "POST"])
def rps_route():
    if request.method == "POST":
        data = request.get_json(silent=True) or {}
        sess_id = data.get('sessionId', 'NO_SESS')
        moves = ["Rock", "Paper", "Scissors"]
        misty_move = random.choice(moves)

        def run_full_interaction():
            misty.stop_speaking()
            
            beats = [
                ("Rock", 20, -40, [255,0,0]),
                ("Paper", -15, 40, [255,255,0]),
                ("Scissors", 20, -40, [255,165,0])
            ]
            for word, pitch, arm, color in beats:
                misty.change_led(*color)
                misty.speak(word)
                misty.move_head(pitch=pitch, velocity=100)
                misty.move_arms(arm, arm, 100, 100)
                time.sleep(1.2) 

            misty.change_led(0, 255, 0)
            misty.display_image("e_Joy.jpg")
            misty.move_head(0, 100)
            misty.move_arms(0, 0, 100, 100)
            
            misty.speak(f"Shoot! I chose {misty_move}!")
            time.sleep(2.5) # Wait for speech to finish
            
            misty.display_image("e_DefaultContent.jpg")
            misty_neutral() # Return to straight position

        run_full_interaction() 
        return jsonify({"status": "done", "misty_choice": misty_move})

    return render_template('RockPaperScissors.html')

#Robot page
@app.route('/robots_at_fandm')
def robots_page():
    # Reset Misty when showing the department robots
    misty_neutral()
    return render_template('robots_at_fandm.html')

# --- 6. GEMINI & SPEECH PROCESSING ---
@app.route('/misty/start_listening', methods=["POST"])
def start_listening():
    misty.change_led(255, 0, 0)
    misty.start_recording_audio("capture.wav")
    misty_actions.executeActionScript([{'name': 'LookInDirection', 'args': ['up']}])
    return jsonify({"status": "recording"})

@app.route('/misty/stop_and_process', methods=["POST"])
def stop_and_process():
    data = request.get_json(silent=True) or {}
    sess_id = data.get('sessionId', 'NO_SESS')
    print(f"Processing request for session: {sess_id}")

    if not processing_lock.acquire(blocking=False):
        return jsonify({"status": "busy"}), 200
    
    try:
        misty.stop_recording_audio()
        # --- THINKING ANIMATION START ---
        misty.change_led(0, 0, 255)
        misty.move_head(pitch=-15, roll=20, yaw=0, velocity=40)
        misty.move_arms(20, 20, 40, 40) 
        time.sleep(1.0) 
        
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
            
            if text and text.strip():
                logger.info(f"ID: {sess_id} | [GEMINI_QUERY] | Details: {text}")
                gemini_script = misty_actions.get_gemini_actions(text)
                logger.info(f"ID: {sess_id} | [GEMINI_RESPONSE] | Details: {json.dumps(gemini_script)}")

                misty_actions.executeActionScript(gemini_script)
                
                full_reply = " ".join([a['args'][0] for a in gemini_script if a['name'] == 'SayText'])
                clean_reply = clean_text_for_misty(full_reply)

                # Reset to neutral after speech (adjust delay if needed)
                def reset_after_speaking():
                    time.sleep(5.0) 
                    misty_neutral()
                threading.Thread(target=reset_after_speaking).start()

                return jsonify({"user_text": text, "misty_reply": clean_reply})

        misty.speak("I didn't catch that.") 
        misty_neutral()
        return jsonify({"user_text": "...", "misty_reply": "I didn't catch that."})

    except Exception as e:
        print(f"Error: {e}")
        misty.change_led(255, 0, 0)
        return jsonify({"error": str(e)}), 500
    finally:
        if processing_lock.locked():
            processing_lock.release()

def clean_text_for_misty(text):
    return re.sub(r'[\*\#\_>]', '', text)

@app.route('/speak', methods=['POST'])
def handle_speak():
    data = request.get_json()
    text = data.get('text', '')
    misty.speak(text)
    
    if "yay!" in text.lower():
        misty.move_arms(40, 40, 100, 100)
        time.sleep(0.5)
        misty.move_arms(-40, -40, 100, 100)
        time.sleep(0.5)
        misty_neutral() # Reset arms and head after "Yay!"
        
    return jsonify({"status": "success"})

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5001, threaded=True, use_reloader=False)