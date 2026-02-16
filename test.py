"""
Flask Application for F&M Computer Science Major Page
"""

from flask import Flask, render_template, request, jsonify
from mistyPy.Robot import Robot
import json
import requests
import os
import re
import html
from threading import Thread

app = Flask(__name__)

# misty = Robot("192.168.1.3") #misty IP
# misty.set_default_volume(20) 

@app.route('/')
def index():
    """Home page - renders the index template"""
    return render_template('index_misty.html')

@app.route('/cs')
def cs_page():
    """Computer Science major page"""
    return render_template('CS2page11-18.html')

@app.route('/background')
def dev_log_page():
    """How the Robot was Coded - Replaced Neuroscience page"""
    # This points to the new HTML file you created with the 6-picture tile
    return render_template('background.html')

@app.route('/datascience')
def data_page():
    """Data Science major page"""
    return render_template('dataSci.html')

@app.route('/cognitivescience')
def cog_page():
    """Cognitive Science major page"""
    return render_template('cogSci.html')

@app.route('/RockPaperScissors')
def academics_page():
    """Rock Paper Scissors Game page"""
    return render_template('RPSgame11-18.html')

@app.route('/more')
def additionalinfo_page():
    """Additional info page"""
    return render_template('additional_info.html')

@app.route("/gemini")
def gemini():
    """Gemini Chat Page"""
    return render_template('gemini.html')

def extract_text():
    if request.is_json:
        text = request.json.get('text', '')
    else:
        text = request.get_data(as_text=True)

    # Decode HTML entities (&amp; → &)
    text = html.unescape(text)

    # Remove HTML tags
    text = re.sub(r'<[^>]+>', '', text)

    return text.strip()


@app.route('/speak', methods=['POST'])
def misty_speak():
    text = extract_text()
    print("Speaking:", text)
    # misty.speak(text)
    return jsonify({"message": f"Misty speaking: {text}"})


@app.route('/speakOnClick', methods=['POST'])
def misty_speakOnClick():
    text = extract_text()
    print("Speaking:", text)
    # misty.speak(text)
    return jsonify({"message": f"Misty speaking: {text}"})

@app.route('/mistyStart', methods = ["POST"])
def misty_start():
    # misty.speak("Ready?")
    return jsonify({"message": "Misty is starting"})

@app.route('/directSpeak', methods = ["GET","POST"])
def misty_direct():
    text = extract_text()
    if text:
        # misty.speak(text)
        return jsonify({"message": f"Misty speaking: {text}"})
    return jsonify({"message": "No text provided"})

@app.route('/exit')
def misty_goodbye():
    return render_template('index11-192.html')

@app.errorhandler(404)
def not_found(error):
    return '<h1>404 - Page Not Found</h1><p>The page you are looking for does not exist.</p>', 404

@app.errorhandler(500)
def internal_error(error):
    return '<h1>500 - Internal Server Error</h1><p>Something went wrong on our end.</p>', 500

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5001)