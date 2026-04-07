from flask import Flask, render_template, request, jsonify
from mistyPy.Robot import Robot
import time, io, base64, threading
from threading import Thread
from STT_google import transcribe_wav_bytes
from misty_robot import MistyActions
import random 
import requests
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
is_recording = False

latest_user_text = ""
latest_misty_reply = ""
current_status = "idle" # idle, recording, thinking
recording_start_time = None
RECORDING_TIMEOUT_SECONDS = 300  # 5 Minutes
rps_active = False

# Thinking Actions List
THINKING_ACTIONS = [
    {"text": "Let me think about that.", "pitch": -15, "roll": 10, "arm": 30},
    {"text": "That is a great question! One second.", "pitch": 0, "roll": -10, "arm": 10},
    {"text": "Let's check my database.", "pitch": 10, "roll": 5, "arm": 50},
    {"text": "Give me a moment to answer.", "pitch": -5, "roll": 15, "arm": 20},
    {"text": "Processing", "pitch": -20, "roll": 0, "arm": 40}
]

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

# Define Misty's LED Colors
COLORS = {
    "recording": {"red": 255, "green": 0, "blue": 0},      # Bright Red
    "thinking": {"red": 255, "green": 255, "blue": 0},    # Yellow
    "idle": {"red": 0, "green": 47, "blue": 108}          # F&M Blue (#002F6C)
}

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

@app.route('/misty/status')
def get_status():
    global is_recording, latest_user_text, latest_misty_reply, current_status
    return jsonify({
        "is_recording": is_recording,
        "status": current_status,
        "user_text": latest_user_text,
        "misty_reply": latest_misty_reply
    })

# --- 4. NAVIGATION ROUTES ---
@app.route('/')
def start():
    misty.stop_speaking()
    misty_neutral()
    return render_template('start.html')

@app.route('/home')
def index():
    global rps_active
    rps_active = False
    misty.stop_speaking()
    
    try:
        misty.unregister_event("BumperPress")
    except Exception as e:
        print(f"Bumper unregister skipped or not needed: {e}")

    hazard_enabled = False
    for cmd in ["hazard_system_enable", "enable_hazard_system", "revert_hazard_settings"]:
        try:
            func = getattr(misty, cmd)
            if cmd == "revert_hazard_settings":
                func(revert_to_default=True)
            else:
                func()
            print(f"Success: Hazards enabled via {cmd}")
            hazard_enabled = True
            break
        except (AttributeError, TypeError):
            continue
    
    if not hazard_enabled:
        print("Warning: Could not verify Hazard System status, but continuing...")

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
    def turn_point_return():
        print("Misty: Speaking and Turning...")
        misty.drive_time(0, 80, 2500) 
        misty.change_led(255, 255, 255)
        time.sleep(2.5) 

        misty.speak("Meet the minds behind this project.")
        print("Misty: Pointing at the team!")
        misty.move_arms(-20, -20, 80, 80) 
        misty.move_head(pitch=-15, yaw=0, velocity=80)
        misty.change_led(0, 255, 0)
        
        time.sleep(5.0) 

        print("Misty: Returning to center...")
        misty.change_led(255, 255, 255)
        misty.move_arms(90, 90, 60, 60)
        misty.drive_time(0, -80, 2500)
        time.sleep(2.5)
        misty_neutral()

    threading.Thread(target=turn_point_return).start()
    return render_template('team.html')

@app.route("/gemini_misty")
def gemini_page(): 
    try:
        misty.hazard_system_disable()
    except:
        pass

    try:
        misty.register_event(
            event_type="BumpSensor", 
            event_name="BumperPress", 
            condition=None, 
            debounce=50, 
            keep_alive=True, 
            callback_function=local_bumper_handler
        )
        print("Success: Registered Bumper via Local SDK Callback")
        misty.change_led(0, 255, 0)
    except Exception as e:
        print(f"Registration Error: {e}")

    misty_neutral()
    return render_template('gemini_misty_mic.html')

def trigger_stop_and_process():
    global is_recording, current_status, recording_start_time
    if is_recording:
        print(">>> TIMEOUT TRIGGERED: Forcing stop and process... <<<")
        is_recording = False
        current_status = "thinking"
        recording_start_time = None 
        misty.change_led(255, 255, 0) 
        threading.Thread(target=stop_and_process_internal).start()

def monitor_recording_timeout():
    global is_recording, recording_start_time
    timeout_limit = RECORDING_TIMEOUT_SECONDS
    while is_recording:
        if recording_start_time:
            elapsed = (datetime.now() - recording_start_time).total_seconds()
            if elapsed >= timeout_limit:
                trigger_stop_and_process()
                break
        time.sleep(1)

def local_bumper_handler(data):
    global is_recording, recording_start_time, current_status
    msg = data.get("message", {}) if isinstance(data, dict) else getattr(data, "message", {})
    pressed = msg.get("isContacted") or msg.get("IsContacted")
    
    if pressed:
        misty.stop_speaking() 

        if not is_recording:
            print(">>> INTERRUPT: STARTING RECORDING <<<")
            is_recording = True
            current_status = "recording"
            recording_start_time = datetime.now()
            misty.change_led(255, 0, 0) 
            threading.Thread(target=start_listening_internal).start()
            threading.Thread(target=monitor_recording_timeout, daemon=True).start()
        else:
            print(">>> INTERRUPT: STOPPING & PROCESSING <<<")
            recording_start_time = None 
            is_recording = False
            current_status = "thinking"
            misty.change_led(255, 255, 0)
            threading.Thread(target=stop_and_process_internal).start()

def start_listening_internal():
    start_listening()

def stop_and_process_internal():
    stop_and_process()

@app.route('/misty/bumper_callback', methods=['POST'])
def bumper_callback_route():
    data = request.get_json(silent=True) or {}
    local_bumper_handler(data)
    return jsonify({"status": "received"}), 200

# --- 5. ROBOT CONTROL ROUTES ---
@app.route('/stop', methods=["POST"])
def stop_misty_route():
    try:
        misty.stop_speaking()
        misty_neutral(velocity=100)
        return jsonify({"status": "success"}), 200
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500

@app.route('/RockPaperScissors', methods=["GET", "POST"])
def rps_route():
    global rps_active
    if request.method == "POST":
        moves = ["Rock", "Paper", "Scissors"]
        misty_move = random.choice(moves)
        rps_active = True

        # We move the interaction into a function we can wait for
        def run_full_interaction():
            global rps_active
            misty.stop_speaking()
            
            # 1. The "Rock... Paper... Scissors..." Countdown
            beats = [
                ("Rock", 20, -40, [255,0,0]),
                ("Paper", -15, 40, [255,255,0]),
                ("Scissors", 20, -40, [255,165,0])
            ]
            
            for word, pitch, arm, color in beats:
                if not rps_active: return 
                misty.change_led(*color)
                misty.speak(word)
                misty.move_head(pitch=pitch, velocity=100)
                misty.move_arms(arm, arm, 100, 100)
                time.sleep(1.2) # Timing for each beat

            # 2. The "Shoot!" Reveal
            if not rps_active: return
            misty.change_led(0, 255, 0)
            misty.display_image("e_Joy.jpg")
            misty.move_head(0, 100)
            misty.move_arms(0, 0, 100, 100)
            
            misty.speak(f"Shoot! I chose {misty_move}!")
            # Hold the pose so the human can see what she "threw"
            time.sleep(2.0) 

            # 3. Reset
            misty.display_image("e_DefaultContent.jpg")
            misty_neutral()
            rps_active = False

        # IMPORTANT: We run the interaction in the foreground for this POST request
        # so the website 'waits' for the function to finish before getting the JSON.
        run_full_interaction() 
        
        # Now that the robot is done, we tell the website what happened
        return jsonify({
            "status": "finished", 
            "misty_choice": misty_move
        })

    return render_template('RockPaperScissors.html')

@app.route('/robots_at_fandm')
def robots_page():
    misty_neutral()
    return render_template('robots_at_fandm.html')

# --- 6. GEMINI & SPEECH PROCESSING ---
# --- 6. GEMINI & SPEECH PROCESSING (THREAD-SAFE VERSIONS) ---
@app.route('/misty/start_listening', methods=["POST"])
def start_listening():
    global is_recording, current_status
    # We use app.app_context() to prevent the "Working outside of application context" error
    with app.app_context():
        is_recording = True
        current_status = "recording"
        logger.info("EVENT: [BUMPER_PRESS] | Action: Started Recording")
        
        misty.change_led(255, 0, 0) 
        misty.start_recording_audio("capture.wav")
        
        # Only return jsonify if this was called by a web request, not a thread
        try:
            return jsonify({"status": "recording"})
        except RuntimeError:
            return None

@app.route('/misty/stop_and_process', methods=["POST"])
def stop_and_process():
    global is_recording, current_status, latest_user_text, latest_misty_reply
    
    with app.app_context():
        current_status = "thinking"
        is_recording = False 

        logger.info("EVENT: [BUMPER_PRESS] | Action: Stopped Recording / Processing")
        misty.stop_recording_audio()
        
        # Wrap request access in a try/except to handle bumper vs web clicks
        try:
            data = request.get_json(silent=True) or {}
        except RuntimeError:
            data = {}

        if not processing_lock.acquire(blocking=False):
            try:
                return jsonify({"status": "busy"}), 200
            except RuntimeError:
                return

        try:
            # --- THINKING ACTION LOGIC ---
            action = random.choice(THINKING_ACTIONS)
            misty.speak(action["text"])
            misty.move_head(pitch=action["pitch"], roll=action["roll"], yaw=0, velocity=40)
            misty.move_arms(action["arm"], action["arm"], 40, 40)
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
                latest_user_text = text
                if text and text.strip():
                    gemini_script = misty_actions.get_gemini_actions(text)
                    full_reply = " ".join([a['args'][0] for a in gemini_script if a['name'] == 'SayText'])
                    latest_misty_reply = clean_text_for_misty(full_reply)
                    logger.info(f"GEMINI_IO | User: {latest_user_text} | Misty: {latest_misty_reply}")
                    
                    misty_actions.executeActionScript(gemini_script)

                    def reset_after_speaking():
                        time.sleep(5.0) 
                        misty_neutral()
                        global current_status
                        current_status = "idle"
                    threading.Thread(target=reset_after_speaking).start()
                    
                    try:
                        return jsonify({"user_text": text, "misty_reply": latest_misty_reply})
                    except RuntimeError:
                        return

            misty.speak("I didn't catch that.") 
            misty_neutral()
            try:
                return jsonify({"user_text": "...", "misty_reply": "I didn't catch that."})
            except RuntimeError:
                return

        except Exception as e:
            print(f"Error: {e}")
            misty.change_led(255, 0, 0)
            try:
                return jsonify({"error": str(e)}), 500
            except RuntimeError:
                return
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
        misty_neutral()
    return jsonify({"status": "success"})

if __name__ == '__main__':
    app.run(debug=True, host='192.168.1.2', port=5001, threaded=True, use_reloader=False)