"""
Flask Application for F&M Computer Science Major Page
"""

from flask import Flask, render_template, request, jsonify
from mistyPy.Robot import Robot
import requests
import time
import os

app = Flask(__name__)
MISTY_IP = "192.168.1.2"

misty = Robot(MISTY_IP)

# to change the volume at which misty speaks
misty.set_default_volume(120) 

def dance():
    misty.play_audio("s_Success3.wav")
    misty.move_arms(80, -80)
    misty.move_head(0, 20, 0)
    time.sleep(0.5)
    misty.move_arms(-80, 80)
    misty.move_head(0, -20, 0)
    time.sleep(.5)
    misty.display_image("e_Joy3.jpg")

@app.route('/')
def index():
    """Home page - renders the index template"""
    misty.stop_speaking()
    return render_template('index11-192.html')

@app.route('/cs')
def cs_page():
    """Computer Science major page"""
    return render_template('CS2page11-18.html')

@app.route('/neuro')
def neuro_page():
    """Neuroscience major page"""
    return render_template('neuropage11-18.html')

@app.route('/datascience')
def data_page():
    """Neuroscience major page"""
    return render_template('dataSci.html')

@app.route('/cognitivescience')
def cog_page():
    """Neuroscience major page"""
    return  render_template('cogSci.html')

@app.route('/RockPaperScissors')
def academics_page():
    """Academics page"""

    return render_template('RPSgame11-18.html')

@app.route('/more')
def additionalinfo_page():
    """Additional info page"""
    
    return render_template('additional_info.html')

@app.route("/gemini")
def Gemini():
    """Gemini Chat Page"""
    return render_template('gemini.html')

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
    # misty.stop_speaking()
    text = request.json.get('text', '')
    print("Speaking:", text)
    # Add your Misty call here
    print(text)
    misty.speak(text)
    return jsonify({"message": f"Misty speaking: {text}"})

@app.route('/mistyStart', methods = ["POST"])
def misty_start():
    misty.move_arm("right", 0)
    time.sleep(.5)
    misty.speak("Rock")
    misty.move_arm("right", 90)

    time.sleep(.5)
    misty.move_arm("left", 0)
    misty.speak("Paper")
    misty.move_arm("left", 90)

    time.sleep(.5)
    misty.move_arms(0, 0)
    misty.speak("Scissor")
    misty.move_arms(90, 90)

    time.sleep(.5)
    misty.move_arms(0, 0)
    misty.speak("Shoot")
    misty.move_arms(90, 90)

    misty.stop()
    
    return jsonify({"message": "Misty is starting"})

@app.route('/directSpeak', methods = ["GET","POST"])
def misty_direct():
    text = request.json.get('text', '')
    print("Speaking:", text)

    misty.speak(text)

    if ("lose" in text):
        print("HERE lose")
        dance()
        time.sleep(.5)
        dance()
        misty.move_arms(90)
    elif("kidding" in text ):
        print("HERE KIDDING")
        #time.sleep(10)
        misty.drive_time(0, 30, 14500)
        misty.display_image("e_Joy.jpg")
        misty.play_audio("s_Joy.wav")
        misty.speak("HahahahahaHahahahahaHahahahaha" \
        "HahahahahaHahahahahaHa     hahahahaHahahahahahahahaha     hahahahaHahahahahahahahaha")

    misty.display_image("e_DefaultContent.jpg")

    return jsonify({"message": "text"})

@app.route('/exit')
def misty_goodbye():

    misty.speak("Goodbye")
    #idle()

    return render_template('indexe11-192.html')

@app.errorhandler(404)
def not_found(error):
    return '<h1>404 - Page Not Found</h1><p>The page you are looking for does not exist.</p>', 404

@app.errorhandler(500)
def internal_error(error):
    return '<h1>500 - Internal Server Error</h1><p>Something went wrong on our end.</p>', 500

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5001)

