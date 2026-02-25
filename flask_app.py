from flask import Flask, render_template, request, jsonify
from mistyPy.Robot import Robot
import time, io, base64, threading
from threading import Thread
from STT_google import transcribe_wav_bytes
from misty_robot import MistyActions
import random 
import json

app = Flask(__name__)
MISTY_IP = "192.168.1.2"

# Initialize Robot interfaces
misty = Robot(MISTY_IP)
misty_actions = MistyActions(MISTY_IP)
misty.set_default_volume(80) 
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

@app.route('/')
def index():
    misty.stop_speaking()
    return render_template('index_misty.html')

@app.route('/stop', methods=["POST"])
def stop_misty_route():
    misty.stop_speaking()
    return jsonify({"status": "stopped"})

@app.route('/cs')
def cs_page(): return render_template('CS2page11-18.html')

@app.route('/background')
def neuro_page(): return render_template('background.html')

@app.route('/datascience')
def data_page(): return render_template('dataSci.html')

@app.route('/RockPaperScissors', methods=["GET", "POST"])
def rps_route():
    if request.method == "POST":
        # 1. Randomly choose Misty's move
        moves = ["Rock", "Paper", "Scissors"]
        misty_move = random.choice(moves)

        def run_rps_sequence():
            # Clear any previous speech/actions
            misty.stop_speaking()
            
            # --- THE "HUMAN" COUNTDOWN ---
            # Beat 1: "Rock" + Head Down
            misty.speak("Rock")
            misty.move_head(pitch=20, roll=0, yaw=0, velocity=100) 
            time.sleep(0.8)

            # Beat 2: "Paper" + Head Up
            misty.speak("Paper")
            misty.move_head(pitch=-15, roll=0, yaw=0, velocity=100)
            time.sleep(0.8)

            # Beat 3: "Scissors" + Head Down
            misty.speak("Scissors")
            misty.move_head(pitch=20, roll=0, yaw=0, velocity=100)
            time.sleep(0.8)

            # THE REVEAL: "Shoot!" + Level Head + Flash LED
            misty.move_head(pitch=0, roll=0, yaw=0, velocity=100)
            misty.change_led(79, 70, 229) # Indigo/Purple flash
            misty.speak(f"Shoot! I chose {misty_move}!")
            
            # Change eyes to show excitement
            misty.display_image("e_Joy.jpg") 
            time.sleep(3)
            misty.display_image("e_DefaultContent.jpg")

        # Run in background so the UI doesn't lag
        Thread(target=run_rps_sequence).start()
        return jsonify({"status": "playing", "misty_choice": misty_move})

    # If it's a GET request, just show the page
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
        {'name': 'SetEyes', 'args': ['wonder']},
        {'name': 'TiltHead', 'args': ['forward', 'small']},
        {'name': 'Pause', 'args': [1000]},
        {'name': 'TiltHead', 'args': ['forward', 'none']},
        {'name': 'Pause', 'args': [1000]}
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
    app.run(debug=True, host='0.0.0.0', port=5001)