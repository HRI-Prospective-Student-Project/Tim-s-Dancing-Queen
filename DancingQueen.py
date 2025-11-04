from mistyPy.Robot import Robot
from mistyPy.Events import Events
# import random
import time
# import math
import keyboard

misty = Robot("192.168.1.4")
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


def dance():
    misty.play_audio("s_Success3.wav")
    for _ in range(3):
        misty.move_arms(80, -80)
        misty.move_head(0, 20, 0)
        time.sleep(0.5)
        misty.move_arms(-80, 80)
        misty.move_head(0, -20, 0)
        time.sleep(.5)
    misty.display_image("e_Joy3.jpg")

person_detected = False
song = open("sweetcaroline.mp3")

# This is the pre conversation part of misty
# misty will dance and play music until the human chaperone is detected.
# misty will continue to dance while space bar is not pressed
while person_detected == False:
    # add music
    dance()
    time.sleep(.5)

    if keyboard.is_pressed("space"):
        # put wave greeting and introduction
        # how are you
        # maybe prompt "would you like to talk to me"
        talk = False
        print("loop exited")
        person_detected = True

