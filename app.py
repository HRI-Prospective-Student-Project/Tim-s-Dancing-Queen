"""
Flask Application for F&M Computer Science Major Page
"""

from flask import Flask, render_template, request, jsonify
from mistyPy.Robot import Robot
from DancingQueen import idle
import requests
import time
import os

app = Flask(__name__)
MISTY_IP = "192.168.1.7"

misty = Robot(MISTY_IP)

# to change the volume at which misty speaks
misty.set_default_volume(10) 

@app.route('/')
def index():
    """Home page - renders the index template"""
    misty.stop_speaking()
    return render_template('indexenhanced.html')

@app.route('/cs')
def cs_page():
    """Computer Science major page"""
    return render_template('CS_enhanced.html')

@app.route('/neuro')
def neuro_page():
    """Neuroscience major page"""
    return render_template('neuro_simplified.html')

@app.route('/RockPaperScissors')
def academics_page():
    """Academics page"""
    return render_template('RPSgame.html')

@app.route('/speak', methods = ["GET", "POST"])
def misty_speak():
    # textObj = json.load(request.data)
    # print(textObj["text"])
    # misty.speak(textObj["text"])

    text = request.json.get('text', '')
    print("Speaking:", text)
    # Add your Misty call here
    misty.speak(text)
    return jsonify({"message": f"Misty speaking: {text}"})

@app.route('/speakOnClick', methods = ["GET", "POST"])
def misty_speakOnClick():
    # textObj = json.load(request.data)
    # print(textObj["text"])
    # misty.speak(textObj["text"])
    misty.stop_speaking()
    text = request.json.get('text', '')
    print("Speaking:", text)
    # Add your Misty call here
    print(text)
    misty.speak(text)
    return jsonify({"message": f"Misty speaking: {text}"})

@app.route('/mistyStart', methods = ["POST"])
def misty_start():
    misty.move_arm("right", 0)
    misty.speak("Rock")
    time.sleep(.2)
    misty.move_arm("right", 30)
    misty.speak("Paper")
    time.sleep(.2)
    misty.move_arm("right", 0)
    misty.speak("Scissor")
    time.sleep(.2)
    misty.move_arm("right", 30)
    time.sleep(.2)
    misty.speak("Shoot")
    misty.move_arm("right", 0)
    time.sleep(.2)
    misty.move_arm('right', 90)
    
    return jsonify({"message": "Misty is starting"})

@app.route('/directSpeak', methods = ["GET","POST"])
def misty_direct():
    text = request.json.get('text', '')
    print("Speaking:", text)

    misty.speak(text)

    return jsonify({"message": "text"})

@app.route('/exit')
def misty_goodbye():

    misty.speak("Goodbye")
    idle()

    return render_template('indexenhanced.html')

@app.errorhandler(404)
def not_found(error):
    return '<h1>404 - Page Not Found</h1><p>The page you are looking for does not exist.</p>', 404

@app.errorhandler(500)
def internal_error(error):
    return '<h1>500 - Internal Server Error</h1><p>Something went wrong on our end.</p>', 500

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5001)

