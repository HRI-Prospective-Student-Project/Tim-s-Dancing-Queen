<h1 align="center">DANCING-QUEEN-ROBOT</h1>
<p align="center">
  <em><code>❯ An interactive Misty robot project exploring embodied movement, music, and human–robot interaction.</code></em>
</p>
<p align="center">
    <img src="https://raw.githubusercontent.com/PKief/vscode-material-icon-theme/ec559a9f6bfd399b82bb44393651661b08aaf7ba/icons/folder-markdown-open.svg" align="center" width="30%">
</p>

<p align="center">
  <img src="https://img.shields.io/github/license/HRI-Prospective-Student-Project/Dancing-Queen-Robot?style=default&logo=opensourceinitiative&logoColor=white&color=0080ff" alt="license">
  <img src="https://img.shields.io/github/last-commit/HRI-Prospective-Student-Project/Dancing-Queen-Robot?style=default&logo=git&logoColor=white&color=0080ff" alt="last-commit">
  <img src="https://img.shields.io/github/languages/top/HRI-Prospective-Student-Project/Dancing-Queen-Robot?style=default&color=0080ff" alt="repo-top-language">
  <img src="https://img.shields.io/github/languages/count/HRI-Prospective-Student-Project/Dancing-Queen-Robot?style=default&color=0080ff" alt="repo-language-count">
</p>

## Project Overview

This repository contains the **Dancing-Queen-Robot** codebase: a Flask-based web dashboard paired with Python scripts that interact with a Misty Robotics robot via the `mistyPy` SDK.

The project includes:
- web pages (in `templates/`) designed as interactive demo pages, and  
- Python scripts that demonstrate robot behaviors such as dancing, greeting, and object/person tracking.

---

## Quick Notes

- **Robot hardware**  
  This project expects a Misty Robotics robot reachable on your local network.  
  Several scripts define a `MISTY_IP` value (for example `192.168.1.9` or `192.168.1.4`).  
  Update these values to match your robot’s actual IP address before running the code.

- **SDK wrapper**  
  The `mistyPy/` folder contains the SDK helper modules used by the examples and the web dashboard.

---

## Prerequisites
- **Python 3.8+**: A Python 3 runtime is required.
- **Python packages**: Install Python dependencies with:

```powershell
pip install -r requirements.txt
```
---
## Web / Frontend
- The frontend uses static assets in `templates/` and `static/assets`.
- The repo includes a `package.json` for front-end dependencies (Tailwind, feather-icons); run the usual Node workflows if you want to rebuild frontend assets.
- Tailwind and the feather-icons require internet connection or for them to be cached before use. 
    - One way to cache is to run `test.py` with internet (make sure each route is routed to the correct HTML page)

## Misty Desktop Environment (Windows)

This project can be developed and run using a local Python environment. The steps below summarize the Misty Robotics recommended workflow for setting up a Windows desktop environment, with a few project-specific notes.

### 1. Power on and connect Misty
- Turn on the Misty robot
- Connect it to your Wi-Fi network
- Ensure the robot and your development machine are on the same local network (LAN)

### 2. Install required tools
Install the following on your development machine:

- **Code editor**  
  Visual Studio Code:
  https://code.visualstudio.com/download

- **Python**  
  https://www.python.org/downloads/

- **Misty Python SDK**  
  Clone or download from:  
  https://github.com/MistyCommunity/Python-SDK


### 3. Create a working directory and set PATHs (Windows)

- Choose a folder to store the Misty Python SDK and your projects  
  (for example: `C:\Users\YourName\Desktop\MistyPythonSDK`).

- Open **Edit the system environment variables** → **Environment Variables**.

- Under **System variables**, select `Path` and click **Edit**.

- Add the paths to:
  - your Python installation (and `Scripts` folder),
  - your code editor binaries (e.g., VS Code), and
  - your chosen working directory (optional but helpful).

This ensures the terminal inside your editor can locate Python and related tools.

---

### 4. Configure VS Code terminal working directory (optional)

To make sure the integrated terminal opens in the correct project folder:

- Open **Settings** in Visual Studio Code.
- Search for `terminal.integrated.cwd`.
- Set it to your working directory path  
  (for example: `C:\Users\YourName\Desktop\MistyPythonSDK`).

This avoids needing to manually `cd` into the project each time.

---

### 5. Install required Python dependencies for the Misty SDK

From your project folder (or an activated virtual environment), install the required Python packages:

```powershell
pip install 'requests>=2.25.1'
pip install 'websocket-client<=0.57.0'
pip install 'yapf>=0.30.0'
```

  - For this repository also install Flask (already listed in `requirements.txt`):

```powershell
pip install -r requirements.txt
```
---
### 6) Generate Robot wrappers (Robot Generator)

  - Create a small script (for example `update.py`) in your working directory to regenerate the SDK command wrappers for your specific robot model and firmware. Example contents:

```python
from mistyPy.GenerateRobot import RobotGenerator
RobotGenerator("ROBOT-IP_ADDRESS-GOES-HERE")
```

  - Run it from the terminal:

```powershell
python update.py
```

  - This step will update `mistyPy` wrappers (e.g., `RobotCommands.py` / `Websocket.py`) to match your robot's available commands and websockets.
---
### 7) Create and or run your Python project

  - Keep your project files in or next to the Misty SDK folder so imports like `from mistyPy.Robot import Robot` resolve. Alternatively, install the SDK into your virtualenv.
  - Update the robot IP in scripts (e.g., `MISTY_IP = "192.168.1.X"` or `Robot("192.168.1.X")`) to match your robot.

  - Run an example script to verify connectivity, for example:

```powershell
python Examples\examples_first_skill.py
```

  - For the Flask web dashboard (if using live robot features):

```powershell
python app.py
```
---
### 8) Troubleshooting tips

  - Verify the robot and development machine are on the same network and that the robot IP is correct.
  - If you have firewall restrictions, allow the developer tools/terminal access or temporarily disable the blocking rules while testing.
  - Make sure assets referenced by the code (audio/images) exist on the robot or change the filenames in code.
  - If a command is missing, re-run `update.py` to refresh the generated SDK wrappers.

For full details and images, consult the original Misty lesson: https://lessons.mistyrobotics.com/misty-lessons/desktop-environment

---
## How to run the web app (local)

```powershell
python app.py
```

The Flask apps run on `0.0.0.0:5001` by default (see file top-level `if __name__ == '__main__'` blocks).
Link to page is in the terminal
Running the robot and dashboard together
- The web dashboard (`app.py`) and the robot behavior script (`DancingQueen.py`) are intended to run at the same time so the dashboard can send commands/events and the robot-side event loop can respond. Start them in separate terminals (or separate machines) on the same network. Example (two terminals):

```powershell
# Terminal A: serve the dashboard
python app.py

# Terminal B: run robot behavior/event loop
python DancingQueen.py
```

- If you only want the frontend without connecting to the robot, `test.py`.
---

### Key Scripts & Purpose
- **`app.py`**  
  Main Flask application that interacts with the Misty robot via `mistyPy.Robot`.  
  Provides routes used by the web dashboard, including JSON endpoints such as:
  - `/speak`
  - `/mistyStart`
  - `/directSpeak`

- **`DancingQueen.py`**  
  Primary robot behavior script.  
  Implements dancing routines, touch-based interactions, and event-driven behavior such as pose estimation and object/person tracking.

- **`Examples/generate_robot.py`**  
  Utility script that uses `mistyPy.GenerateRobot.RobotGenerator` to regenerate command wrappers for a robot at a specified IP address.  
  This is used when customizing or updating SDK wrappers to match a specific robot or firmware version.

- **`Examples/example_first_skill.py`**  
  Example robot behavior demonstrating basic speech and event subscription.  
  To add new events:
  - add the event name as a string to the `available_events` list in `mistyPy/Events.py`, and  
  - create a variable corresponding to that event name.
---
### Configuring the Robot IP
- Several files hardcode a robot IP (e.g., `192.168.1.9`, `192.168.1.4`, `192.168.1.1`). Update the `MISTY_IP` or `Robot(...)` lines to the actual IP of your Misty robot before running the scripts.
---
### Running Examples
- To run an example that controls the robot (ensure robot is reachable and you have permission to control it):

```powershell
python Examples\examples_first_skill.py
```
---
### Testing
- There are no automated unit tests included. Manual testing is via the Flask apps and running the example robot scripts.
---
## Folder Structure (high level)
- `app.py` — Flask app (live robot integration)
- `DancingQueen.py` — robot behavior / event-driven logic
- `Examples/` — sample scripts and SDK generator
- `mistyPy/` — local SDK wrapper used by examples
- `templates/` and `static/` — frontend pages and assets
---
## Troubleshooting & Tips
- If you see network or connection errors, verify the robot and your development machine are on the same network and confirm the robot IP.
- Many Misty commands assume audio assets and images are available on the robot (e.g., `s_Success3.wav`, `e_Joy3.jpg`). If a command fails to find an asset, either upload the asset to the robot via the Misty tools or change the filename used in code.
---
### License
- This repository contains code derived from Misty Robotics samples. The `Examples/generate_robot.py` file includes a Misty Robotics Apache 2.0 header; respect the respective licenses when re-using code.

---
