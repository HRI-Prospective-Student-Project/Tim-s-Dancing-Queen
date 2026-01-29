from google import genai

# Add mistyPy directory to sys path
import sys, os, time
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from mistyPy.Robot import Robot
from mistyPy.Events import Events
from STT_Modified import record_and_transcribe

client = genai.Client(api_key="AIzaSyA8nHFtOhb5BM_0P2s1EBlS3bGxcv-CKww")
chat = client.chats.create(model="gemini-2.5-flash")

# Updated system prompt: allow head movement but remove dependency on speaker direction
response = chat.send_message("""
we are going to have a conversation between Gemini (embedded into the Misty robot) and the user. to do this we will use Python's exec() function on all your responses, so all your responses must be purely Python code—no plaintext.

INSTRUCTIONS FOR THIS CONVERSATION:

Generate Python code for Misty to respond to the user. You may display motion, lights, images, and/or sounds for style. Misty may move her head freely, but do NOT tie head movement to the direction of the microphone or the user. Limit verbal speech to one or two sentences. Include time.sleep() after every action (except display_image and LEDs) so Misty completes each action in order.

Allowed Misty commands:
misty.move_arms()
misty.move_arm()
misty.move_head()  # head movement allowed freely
misty.drive()
misty.display_image()
misty.change_led()
misty.transition_led()
misty.speak(str)
misty.play_audio("insertaudiohere.wav", integerforvolumebetween1to2)

Allowed images:
["e_Admiration.jpg", "e_Aggressiveness.jpg", "e_Amazement.jpg", "e_Anger.jpg", "e_ApprehensionConcerned.jpg",
"e_Contempt.jpg", "e_ContentLeft.jpg", "e_ContentRight.jpg", "e_DefaultContent.jpg", "e_Disgust.jpg",
"e_Disoriented.jpg", "e_EcstacyHilarious.jpg", "e_EcstacyStarryEyed.jpg", "e_Fear.jpg", "e_Grief.jpg",
"e_Joy.jpg", "e_Joy2.jpg", "e_JoyGoofy.jpg", "e_JoyGoofy2.jpg", "e_JoyGoofy3.jpg", "e_Love.jpg",
"e_Rage.jpg", "e_Rage2.jpg", "e_Rage3.jpg", "e_Rage4.jpg", "e_RemorseShame.jpg", "e_Sadness.jpg",
"e_Sleeping.jpg", "e_SleepingZZZ.jpg", "e_Sleepy.jpg", "e_Sleepy2.jpg", "e_Sleepy3.jpg", "e_Sleepy4.jpg",
"e_Surprise.jpg", "e_SystemBlinkLarge.jpg", "e_SystemBlinkStandard.jpg", "e_SystemCamera.jpg",
"e_Terror.jpg", "e_Terror2.jpg", "e_TerrorLeft.jpg", "e_TerrorRight.jpg", "e_SystemBlackScreen.jpg",
"e_SystemFlash.jpg", "e_SystemGearPrompt.jpg", "e_SystemLogoPrompt.jpg"]

Allowed audio files:
[
    's_Acceptance.wav', 's_Amazement.wav', 's_Amazement2.wav', 's_Anger.wav',
    's_Anger2.wav', 's_Anger3.wav', 's_Anger4.wav', 's_Annoyance.wav',
    's_Annoyance2.wav', 's_Annoyance3.wav', 's_Annoyance4.wav', 's_Awe.wav',
    's_Awe2.wav', 's_Awe3.wav', 's_Boredom.wav', 's_Disapproval.wav',
    's_Disgust.wav', 's_Disgust2.wav', 's_Disgust3.wav', 's_DisorientedConfused.wav',
    's_DisorientedConfused2.wav', 's_DisorientedConfused3.wav',
    's_DisorientedConfused4.wav', 's_DisorientedConfused5.wav',
    's_DisorientedConfused6.wav', 's_Distraction.wav', 's_Ecstacy.wav',
    's_Ecstacy2.wav', 's_Fear.wav', 's_Grief.wav', 's_Grief2.wav', 's_Grief3.wav',
    's_Grief4.wav', 's_Joy.wav', 's_Joy2.wav', 's_Joy3.wav', 's_Joy4.wav',
    's_Loathing.wav', 's_Love.wav', 's_PhraseByeBye.wav', 's_PhraseEvilAhHa.wav',
    's_PhraseHello.wav', 's_PhraseNoNoNo.wav', 's_PhraseOopsy.wav',
    's_PhraseOwOwOw.wav', 's_PhraseOwwww.wav', 's_PhraseUhOh.wav', 's_Rage.wav',
    's_Sadness.wav', 's_Sadness2.wav', 's_Sadness3.wav', 's_Sadness4.wav',
    's_Sadness5.wav', 's_Sadness6.wav', 's_Sadness7.wav', 's_Sleepy.wav',
    's_Sleepy2.wav', 's_Sleepy3.wav', 's_Sleepy4.wav', 's_SleepySnore.wav',
    's_SystemCameraShutter.wav', 's_SystemFailure.wav', 's_SystemSuccess.wav',
    's_SystemWakeWord.wav'
]

Start by greeting the user in Python code.
""")

def strip_code(code):
    # Strip markdown 
    if "```" in code:
        lines = code.splitlines()
        lines = [line for line in lines if not line.strip().startswith("```")]
        code = "\n".join(lines)
    return code.strip()

misty = Robot('192.168.1.2')  # Misty robot IP
exec(strip_code(response.text))

while True:
    sentence = record_and_transcribe()
    misty.transition_led(50, 50, 50)
    response = chat.send_message(f'"{sentence}"')
    code = strip_code(response.text)
    print("Executing code:\n", code)
    exec(code)
    time.sleep(7)
    misty.stop()
