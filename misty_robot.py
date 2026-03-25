import requests
import json
from google import genai
from google.genai import types

# Constants for the Misty Skill
EVENT_NAME = "ActionScript"
SKILL_ID = "7d6fe0a1-61b4-4df5-872a-568776310d2f"

class MistyActions:
    def __init__(self, ip):
        self.IP = ip
        self.headers = {'Accept': 'application/json', 'Content-type': 'application/json'}
        self.action_url = f"http://{self.IP}/api/skills/event"
        self.skill_start_url = f"http://{self.IP}/api/skills/start"
        # REPLACE WITH YOUR ACTUAL API KEY
        self.client = genai.Client(api_key="")

    def startSkill(self):
        """Starts the ActionScript skill on Misty hardware."""
        data = {"Skill": SKILL_ID}
        try:
            response = requests.post(self.skill_start_url, headers=self.headers, data=json.dumps(data))
            return response
        except Exception as e:
            print(f"Failed to start skill: {e}")
            return None

    def executeActionScript(self, action_script):
        """Sends a JSON array of actions to Misty's ActionScript skill."""
        payload = {"intent": "Explain1", "description": "Interaction", "actionList": action_script}
        data = {"Skill": SKILL_ID, "EventName": EVENT_NAME, "Payload": payload}
        try:
            return requests.post(self.action_url, headers=self.headers, data=json.dumps(data))
        except Exception as e:
            print(f"Error sending ActionScript: {e}")
            return None

    def get_gemini_actions(self, question):
        """Calls Gemini to get robot behaviors and speech as a JSON array."""
        try:
            response = self.client.models.generate_content(
                model="gemini-2.5-flash",
                config=types.GenerateContentConfig(
                    system_instruction="You are a social robot named Misty. You are answering students questions about Franklin & Marshall College at a prospective student event. Your responses need to be concise but informative. Your response must be in the following javascript format: [{ \"name\": \"action_name\", \"args\": [\"list\", \"of\", \"args\"] }] \nThe action_name must be one of the following: SetEyes, SayText, LookInDirection, PointAt, TiltHead, Pause. The args must be valid for the given action_name. For example, if the action_name is SetEyes, the args must be one of: default, love, thinking, confused, and looking. If the action_name is LookInDirection, the args must be one of: center, upperRight, lowerLeft. If the action_name is PointAt, the args must be a direction (default, upwards, downwards, straightOut) and a limb (left, right, both). If the action_name is TiltHead, the args must be a direction (left, right) and an amount (small, medium, large). If the action_name is Pause, the args must be a number representing milliseconds to pause for. Be sure to add small pauses after each action (other than SayText) to give time for the action to execute. Always return to a neutral state with the arms down when done. Your response should only include the actions to perform and no additional text. Do not include any explanations or justifications for your actions. Do not include any text that is not part of the actions. Do not include any indication that the string is json, and do not include any newline characters or other formatting Your response should be a valid JSON array of action objects. Each action object should have a name and args field. The name field should be a string representing the action name. The args field should be an array of strings representing the arguments for the action. Do not include any other fields in the action objects. Do not include any additional text in your response. Make sure to include a SayText action that answers the question directly, and use the other actions to add emphasis and engagement to your response. Do not collect any personal user information"
                ),
                contents=f"Q: {question}\nA:"
            )
            clean_json = response.text.replace("```json", "").replace("```", "").strip()
            return json.loads(clean_json)
        except Exception as e:
            print(f"Gemini Error: {e}")
            return [{"name": "SayText", "args": ["I'm sorry, I'm having trouble thinking right now."]}]