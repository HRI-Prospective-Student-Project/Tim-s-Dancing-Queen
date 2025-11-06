from mistyPy.Robot import Robot
from mistyPy.Events import Events
import random
import time
# import math
import keyboard

misty = Robot("192.168.1.10")

# misty.change_led(0, 255, 0)
# misty.move_head(0, 0, 0)

# #modes
# turn_in_place = True
# follow_human = True

# #constants
# yaw_left = 81.36
# yaw_right = -85.37
# pitch_up = -40.10
# pitch_down = 26.92

# #variables
# curr_head_pitch = 0
# curr_head_yaw = 0
# waving_now = False

def wave_back(arm):
    global waving_now
    if arm == "left":
        print("Waving back left")
        misty.play_audio("s_Acceptance.wav")
        misty.display_image("e_Joy2.jpg")
        misty.transition_led(0, 90, 0, 0, 255, 0, "Breathe", 800)
        misty.move_arms(80, -89)
        time.sleep(1)
        misty.move_arms(80, 0)
        time.sleep(0.75)
        misty.move_arms(80, -89)
        time.sleep(0.75)
        time.sleep(2)
    else :
        print("Waving back right")
        misty.play_audio("s_Awe.wav")
        misty.display_image("e_Love.jpg")
        misty.transition_led(90, 0, 0, 255, 0, 0, "Breathe", 800)
        misty.move_arms(-89, 80)
        time.sleep(1)
        misty.move_arms(0, 80)
        time.sleep(0.75)
        misty.move_arms(-89, 80)
        time.sleep(0.5)
        # time.sleep(2)


    misty.display_image("e_DefaultContent.jpg")
    misty.transition_led(0, 40, 90, 0, 130, 255, "Breathe", 1200)
    misty.move_arms(random.randint(70, 89), random.randint(70, 89))
    waving_now = False

def dance():
    misty.drive(0, 20)
    misty.play_audio("s_Success3.wav")
    misty.move_arms(80, -80)
    misty.move_head(0, 20, 0)
    time.sleep(0.5)
    misty.move_arms(-80, 80)
    misty.move_head(0, -20, 0)
    time.sleep(.5)
    misty.display_image("e_Joy3.jpg")

person_detected = False
moving = False # Whether Misty is moving or not

misty.set_default_volume(10)

try:
    print("Stop the robot by pressing ctrl+C")
    while person_detected == False:
        # add music

        dance()
        # misty.play_audio("sweetcaroline.mp3")
        misty.play_audio("s_Awe.wav")
except KeyboardInterrupt:
    print("Exited manually")

misty.stop_audio()
misty.stop()

introQuestions = ["Do you have any questions?", "What would you like to learn about F and M", "What's up. what do you wanna know?"]

question = random.randint(0, len(introQuestions) - 1)

wave_back("right")
misty.speak("Hello, my name is Misty.")
misty.speak(introQuestions[question])
misty.speak("Pick something from the dashboard")