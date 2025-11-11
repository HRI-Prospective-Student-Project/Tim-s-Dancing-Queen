"""
Flask Application for F&M Computer Science Major Page
"""

from flask import Flask, render_template, request, jsonify
from mistyPy.Robot import Robot
import requests
import os

app = Flask(__name__)
MISTY_IP = "192.168.1.4"

misty = Robot(MISTY_IP)

# to change the volume at which misty speaks
misty.set_default_volume(20) 

@app.route('/')
def index():
    """Home page - renders the index template"""
    misty.stop_speaking()
    return render_template('indexenhanced.html')

@app.route('/cs')
def cs_page():
    """Computer Science major page"""
    return render_template('CSpage.html')

@app.route('/neuro')
def neuro_page():
    """Neuroscience major page"""
    return render_template('neuropage.html')

@app.route('/academics')
def academics_page():
    """Academics page"""
    return render_template('academics.html')

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

@app.route('/exit')
def misty_goodbye():

    misty.speak("Goodbye")
    os.system('start cmd /k "python DancingQueen.py"')

    return render_template('indexenhanced.html')

@app.errorhandler(404)
def not_found(error):
    return '<h1>404 - Page Not Found</h1><p>The page you are looking for does not exist.</p>', 404

@app.errorhandler(500)
def internal_error(error):
    return '<h1>500 - Internal Server Error</h1><p>Something went wrong on our end.</p>', 500

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5001)

