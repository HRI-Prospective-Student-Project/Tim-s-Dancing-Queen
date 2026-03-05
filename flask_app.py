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

# Initialize Robot interfaces
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

# Configure logging to save to a file
# Configure logging
## 1. Update your logging setup to this:
logger = logging.getLogger('misty_logger')
if not logger.handlers:
    logger.setLevel(logging.INFO)
    # Use 'delay=True' so it only opens the file when the first log actually happens
    file_handler = logging.FileHandler('misty_interactions.log', delay=True)
    formatter = logging.Formatter('%(asctime)s - %(message)s', datefmt='%Y-%m-%d %H:%M:%S')
    file_handler.setFormatter(formatter)
    logger.addHandler(file_handler)

@app.route('/log_event', methods=["POST"])
def log_event():
    data = request.get_json()
    if not data:
        return jsonify({"status": "error"}), 400

    event = data.get('event', 'UNKNOWN')
    details = data.get('details', 'N/A')
    page = data.get('page', 'N/A')
    
    log_entry = f"[{event}] | Page: {page} | Details: {details}"
    
    # Use the specific logger we created
    logger.info(log_entry)
    
    print(f"RESEARCH LOG: {log_entry}")
    return jsonify({"status": "logged"}), 200

@app.route('/')
def index():
    misty.stop_speaking()
    return render_template('index_misty.html')

@app.route('/stop', methods=["POST"])
def stop_misty_route():
    try:
        # 1. Kill the current speech immediately
        misty.stop_speaking()
        
        # 2. Change LED to Red (Matches your Gemini Mic UI "Listening" state)
        misty.change_led(255, 0, 0) 
        
        # 3. Return a successful JSON response
        return jsonify({"status": "success", "message": "Misty is now listening"}), 200
        
    except Exception as e:
        # If the robot is disconnected, print the error to your console
        print(f"Error communicating with Misty: {e}")
        # Return a 500 error so your JavaScript console knows it failed
        return jsonify({"status": "error", "message": str(e)}), 500

@app.route('/cs')
def cs_page(): return render_template('CS2page11-18.html')

@app.route('/background')
def neuro_page(): return render_template('background.html')

@app.route('/team')
def data_page(): return render_template('team.html')

@app.route('/RockPaperScissors', methods=["GET", "POST"])
def rps_route():
    if request.method == "POST":
        # 1. Randomly choose Misty's move
        moves = ["Rock", "Paper", "Scissors"]
        misty_move = random.choice(moves)

        def run_rps_sequence():
            misty.stop_speaking()
            
            # --- THE SHOW BEGINS ---
            # Beat 1: "Rock" + Red Light + System Beep
            misty.change_led(255, 0, 0) # Red
            misty.play_audio("s_SystemSuccess.wav") 
            misty.speak("Rock")
            misty.move_head(pitch=20, velocity=100) 
            misty.move_arms(leftArmPosition=-40, rightArmPosition=-40, leftArmVelocity=100, rightArmVelocity=100)
            time.sleep(0.8)

            # Beat 2: "Paper" + Yellow Light + System Beep
            misty.change_led(255, 255, 0) # Yellow
            misty.play_audio("s_SystemSuccess.wav")
            misty.speak("Paper")
            misty.move_head(pitch=-15, velocity=100)
            misty.move_arms(leftArmPosition=40, rightArmPosition=40, leftArmVelocity=100, rightArmVelocity=100)
            time.sleep(0.8)

            # Beat 3: "Scissors" + Orange Light + System Beep
            misty.change_led(255, 165, 0) # Orange
            misty.play_audio("s_SystemSuccess.wav")
            misty.speak("Scissors")
            misty.move_head(pitch=20, velocity=100)
            misty.move_arms(leftArmPosition=-40, rightArmPosition=-40, leftArmVelocity=100, rightArmVelocity=100)
            time.sleep(0.8)

            # THE REVEAL: "Shoot!" + Rainbow Flash + Happy Eyes
            misty.change_led(0, 255, 0) # Bright Green
            misty.display_image("e_Joy.jpg")
            misty.play_audio("s_Joy.wav")
            
            misty.move_head(pitch=0, velocity=100)
            misty.move_arms(leftArmPosition=0, rightArmPosition=0, leftArmVelocity=100, rightArmVelocity=100)
            
            misty.speak(f"Shoot! I chose {misty_move}!")
            
            # Wait 3 seconds then go back to neutral
            time.sleep(3)
            misty.display_image("e_DefaultContent.jpg")
            misty.change_led(0, 0, 0) # LED Off

        # Run in background
        Thread(target=run_rps_sequence).start()
        return jsonify({"status": "playing", "misty_choice": misty_move})

    # --- GET REQUEST (Page Load) ---
    def game_intro():
        # Small delay so the user sees the page load before she starts talking
        time.sleep(1.5) 
        misty.stop_speaking()
        misty.change_led(100, 100, 255) # Soft Purple/Blue
        misty.display_image("e_ContentLeft.jpg")
        misty.speak("Let's play Rock Paper Scissors! First to three wins. Watch me closely as I count down, and click your move on the screen when you are ready. Good luck!")
        time.sleep(5)
        misty.display_image("e_DefaultContent.jpg")
        misty.change_led(0, 0, 0)

    # Start intro in background so it doesn't block the page from rendering
    Thread(target=game_intro).start()

    return render_template('RockPaperScissors.html')

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
    data = request.json
    text = data.get('text', '')
    if text:
        Thread(target=speak_async, args=(text,)).start()
        return jsonify({"status": "success"})
    return jsonify({"status": "error"}), 400

@app.route("/gemini_misty")
def gemini_page(): return render_template('gemini_misty_mic.html')

@app.route('/misty/start_listening', methods=["POST"])
def start_listening():
    misty.start_recording_audio("capture.wav")
    
    # Listening Actions
    listening_actions = [
        {'name': 'LookInDirection', 'args': ['center']},
        {'name': 'LookInDirection', 'args': ['up']},
        {'name': 'Pause', 'args': [1500]},
        {'name': 'LookInDirection', 'args': ['center']},
        {'name': 'Pause', 'args': [1500]},
        {'name': 'LookInDirection', 'args': ['up']},
        {'name': 'Pause', 'args': [1500]},
        {'name': 'LookInDirection', 'args': ['center']},
        {'name': 'Pause', 'args': [1500]},
        {'name': 'LookInDirection', 'args': ['up']},
        {'name': 'Pause', 'args': [1500]},
        {'name': 'LookInDirection', 'args': ['center']},
        {'name': 'LookInDirection', 'args': ['up']}     
    ]

    misty_actions.executeActionScript(listening_actions)
    return jsonify({"status": "recording"})

@app.route('/misty/stop_and_process', methods=["POST"])
def stop_and_process():
    """Processes audio, triggers immediate movement, then handles Gemini."""
    if not processing_lock.acquire(blocking=False):
        return jsonify({"status": "busy"}), 200
    try:
        # 1. Stop recording and wait for file
        misty.stop_recording_audio()
        time.sleep(2.0) 
        
        audio_response = misty.get_audio_file("capture.wav")
        raw_audio_data = None
        
        # 2. Extract audio bytes
        if hasattr(audio_response, "status_code") and audio_response.status_code == 200:
            if 'application/json' in audio_response.headers.get('Content-Type', ''):
                res = audio_response.json().get("result", audio_response.json())
                raw_audio_data = base64.b64decode(res.get("base64"))
            else:
                raw_audio_data = audio_response.content
        
        if raw_audio_data:

            thinking_movements = [
                {'name': 'SetEyes', 'args': ['thinking']}, 
                {'name': 'TiltHead', 'args': ['right', 'large']}, 
                {'name': 'Pause', 'args': [500]},
                {'name': 'TiltHead', 'args': ['left', 'large']},
                {'name': 'Pause', 'args': [500]},
                {'name': 'TiltHead', 'args': ['right', 'large']}, 
                {'name': 'Pause', 'args': [500]},
                {'name': 'TiltHead', 'args': ['left', 'large']},
                {'name': 'Pause', 'args': [500]},
                {'name': 'TiltHead', 'args': ['left', 'small']},
                {'name': 'Pause', 'args': [500]},
                {'name': 'TiltHead', 'args': ['right', 'small']}, 
                {'name': 'Pause', 'args': [500]},
                {'name': 'TiltHead', 'args': ['left', 'small']},
                {'name': 'Pause', 'args': [500]},
                {'name': 'TiltHead', 'args': ['right', 'small']}
            ]
            misty_actions.executeActionScript(thinking_movements)
            
            # 3. Transcribe audio
            text = transcribe_wav_bytes(io.BytesIO(raw_audio_data))
            
            # Filter noise
            junk = ["silence", "motor noise", "noise", "static", "background"]
            if text and any(j in text.lower() for j in junk): 
                text = "" 
            
            if text and text.strip():
                print(f"Misty Heard: {text}")
                
                # --- CALL GEMINI (THE "THINKING" TIME) ---
                # The robot moves while this line is executing
                gemini_script = misty_actions.get_gemini_actions(text)

                # --- ASSEMBLE RESPONSE ---
                repeat_speech = f"I heard you say: {text}."
                response_sequence = [
                    {'name': 'SayText', 'args': [repeat_speech]},
                    {'name': 'Pause', 'args': [800]},
                    {'name': 'SetEyes', 'args': ['default']}
                ] + gemini_script
                
                # --- EXECUTE RESPONSE ---
                # This takes over from the thinking movements
                misty_actions.executeActionScript(response_sequence)
                
                # Extract text for the chat UI
                reply_text = next((a['args'][0] for a in gemini_script if a['name'] == 'SayText'), "")
                
                return jsonify({
                    "user_text": text, 
                    "misty_reply": reply_text
                })
        
        # Fallback for silence
        misty.speak("I didn't catch that. Could you say it again?") 
        return jsonify({"user_text": "...", "misty_reply": "I didn't catch that."})

    except Exception as e:
        print(f"Error in stop_and_process: {e}")
        return jsonify({"error": str(e)}), 500
    finally:
        processing_lock.release()

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5001, threaded=True, use_reloader=False)