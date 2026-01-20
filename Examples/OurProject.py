from mistyPy.Robot import Robot
from mistyPy.Events import Events
import random
import time
import math

misty = Robot("192.168.1.3")
misty.change_led(0, 255, 0)
misty.move_head(0, 0, 0)

#modes
turn_in_place = True
follow_human = True

#constants
yaw_left = 81.36
yaw_right = -85.37
pitch_up = -40.10
pitch_down = 26.92

#variables
curr_head_pitch = 0
curr_head_yaw = 0
waving_now = False

#Event handler for getting the current head position
def curr_position(data):
    global curr_head_pitch, curr_head_yaw
    if data["message"]["sensorId"] == "ahp":
        curr_head_pitch = data["message"]["value"]
        print(curr_head_pitch)
    if data["message"]["sensorId"] == "ahy":
        curr_head_yaw = data["message"]["value"]
        print(curr_head_yaw)

def get_pos():
    misty.register_event(event_name="get_curr_position", event_type= Events.ActuatorPosition, keep_alive= True, callback_function=curr_position)
    time.sleep(0.25)
    misty.unregister_event(event_name="get_curr_position")

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
        time.sleep(0.75)
        time.sleep(2)


    time.sleep(1.5)
    misty.display_image("e_DefaultContent.jpg")
    misty.transition_led(0, 40, 90, 0, 130, 255, "Breathe", 1200)
    misty.move_arms(random.randint(70, 89), random.randint(70, 89))
    time.sleep(1.5)
    waving_now = False

def pair_correlation(keypoint_one, keypoint_two):
    return keypoint_one["imageY"] > keypoint_two["imageY"]

def confident(data):
    return data["confidence"] >= 0.6

# Functions helper for the human pose
def scale_valid(keypoint_one, keypoint_two):
    x_offset = keypoint_one["imageX"] - keypoint_two["imageX"]
    y_offset = keypoint_one["imageY"] - keypoint_two["imageY"]
    return math.sqrt(x_offset**2 + y_offset**2) > 60

def human_pose(data):
    global waving_now
    print("starting pose estimation")
    keypoints = data["message"]["keypoints"]
   
    # 5,6- Shoulder 7,8- Elbow  9,10- Wrist

    if (waving_now == False):
        #left hand
        if (confident(keypoints[7]) and confident(keypoints[5]) and confident(keypoints[9])):
            if (pair_correlation(keypoints[7],keypoints[5]) and pair_correlation(keypoints[5],keypoints[9])):
                if (scale_valid(keypoints[7],keypoints[5])):
                    waving_now = True
                    misty.speak("Hello")
                    wave_back("left")
                   
        #right hand
        elif (confident(keypoints[8]) and confident(keypoints[6]) and confident(keypoints[10])):
            if (pair_correlation(keypoints[8],keypoints[6]) and pair_correlation(keypoints[6],keypoints[10])):
                if (scale_valid(keypoints[8],keypoints[6])):
                    waving_now = True
                    misty.speak("Hi")
                    wave_back("right")      


# Event handler for person detection
def person_detection(data):
    # while confidence is less than .8
    dance()
    time.sleep(5)

    if data["message"]["confidence"] >= 0.75:
        print("person_detected")
        misty.change_led(255, 255, 255)
        misty.wave_back("right")
        # misty.speak("Hello, how are you?")

        width_of_human = data["message"]["imageLocationRight"] - data["message"]["imageLocationLeft"]
        x_error = (160.0 - (data["message"]["imageLocationLeft"] + data["message"]["imageLocationRight"]) / 2.0) / 160.0
        # Use this for non-human tracking
        # y_error = (160.0 - ((data["message"]["imageLocationTop"] + data["message"]["imageLocationBottom"]) / 2.0)) / 160.0
        
        #Use this for human tracking
        y_error = (160.0 - 0.8 * data["message"]["imageLocationTop"] - 0.2 * data["message"]["imageLocationBottom"]) / 160.0

        threshold = max((0.3 if turn_in_place or follow_human else 0.2), (321.0 - width_of_human) / 1000.0)
        damper_gain = 5.0 if turn_in_place or follow_human else 7.0

        get_pos()
        actuate_to_yaw = curr_head_yaw + x_error * ((yaw_left - yaw_right) / damper_gain) if abs(x_error) > threshold else None
        actuate_to_pitch = curr_head_pitch - y_error * ((pitch_down - pitch_up) / 3.0) if abs(y_error) > threshold else None

        linear_velocity = 0
        angular_velocity = 0

        if actuate_to_yaw and abs(actuate_to_yaw) > 15 and (turn_in_place or follow_human):
            angular_velocity = math.copysign(min(abs(actuate_to_yaw) * 0.6, 25), actuate_to_yaw)

        if angular_velocity != 0:
            if math.copysign(1, actuate_to_yaw - curr_head_yaw) == math.copysign(1, angular_velocity):
                if abs(actuate_to_yaw) > 40:
                    actuate_to_yaw /= 1.5
            else:
                actuate_to_yaw = 0
                angular_velocity = 0
                if not follow_human:
                    misty.stop()

        if follow_human:
            if angular_velocity == 0:
                linear_velocity = (130 - width_of_human) * 0.5
                linear_velocity = min(abs(linear_velocity), 20) * math.copysign(1, linear_velocity)
                linear_velocity = linear_velocity if abs(linear_velocity) > 5 else 0
                misty.change_led(0, 255, 255)
                misty.change_led(255, 0, 0)

        misty.move_head(actuate_to_pitch, None, actuate_to_yaw)
        if turn_in_place or follow_human:
            misty.drive(0, angular_velocity)

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

def start_person_tracking() :
    misty.start_object_detector(0.5, 0, 15)
    misty.register_event(event_name="person_detection", event_type= Events.ObjectDetection, callback_function=person_detection, keep_alive=True)

def start_human_pose_estimation():
    misty.start_pose_estimation(0.2, 0, 1)
    misty.register_event(event_name="pose_estimation", event_type=Events.PoseEstimation, keep_alive= True, callback_function= human_pose)

start_person_tracking()
start_human_pose_estimation()
misty.keep_alive()