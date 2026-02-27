#!/usr/bin/env python3
"""
Kyrethys - AI Desktop Assistant
"""


import datetime
import time
import psutil
from datetime import timedelta
import sqlite3
import json
import os
import threading
import subprocess
import secrets
import requests
import re
import logging
try:
    import GPUtil
except ImportError:
    GPUtil = None
import shutil
from flask import Flask, request, jsonify, Response
from flask_cors import CORS
from plugins.memory import get_collection, retrieve_relevant
from plugins.vision import KyrethysVision
from utils.db_logger import DB_PATH, init_db, log_interaction
from utils.emotion import EmotionEngine
from utils.speak import speak
from utils.listen import listen
from utils.launcher import launch_app
from utils.evolution import initiate_stitching
from plugins.memory import retrieve_relevant, add_memory
from plugins.meditate import meditate as run_meditation_logic

Kyrethys_eyes = KyrethysVision()

app = Flask(__name__)
CORS(app)

init_db()  # DB at startup

# GLOBAL STATUS VARIABLE
CURRENT_STATUS = "Idle"

def set_Kyrethys_status(new_status):
    global CURRENT_STATUS
    CURRENT_STATUS = new_status
    print(f"HUD STATUS UPDATE: {new_status}")

# Load configs
try:
    with open('app_paths.json', 'r', encoding='utf-8') as f:
        app_paths = json.load(f)
except FileNotFoundError:
    app_paths = {}
    print("app_paths.json missing — launcher limited.")

CONFIG = {
    "ai_provider": "ollama",
    "ollama_model": "Kyrethys-llama3.1-safe",
    "theme": "Kyrethys Blue",
    "language": "English"
}
try:
    with open('config.json', 'r', encoding='utf-8') as f:
        CONFIG.update(json.load(f))
except:
    print("config.json missing/invalid — defaults used.")

OLLAMA_URL = "http://127.0.0.1:11434/api/generate"                  # The local Ollama API endpoint
OLLAMA_MODEL = CONFIG.get('ollama_model', 'Kyrethys-llama3.1-safe')   # The Ollama model to use

collection = get_collection()       # Initialize memory collection
emotion_engine = EmotionEngine()    # Initialize emotion engine


SLEEP_INTERVAL_HOURS = 6             # Sleep every 6 hours of uptime
IDLE_TIMEOUT = 180                  # 3 minutes of inactivity
MEDITATE_CHANCE = 1                 # 100% chance to meditate when idle
last_activity = time.time()         # Timestamp of last user interaction
is_meditating = False               # Flag to prevent multiple meditation threads

def get_archetypes():
    """Loads the core personality archetypes from the JSON file."""
    path = 'C:/Kyrethys/backend/data/archetypes.json'
    try:
        with open(path, 'r', encoding='utf-8') as f:
            return json.load(f)
    except Exception as e:
        print(f"Error loading archetypes: {e}")
        # Fallback to empty structures so the code doesn't crash
        return {"EMOTIONS": [], "ADJECTIVES": [], "CURRENT_TRAITS": []}

def get_personality_core():
    path = "C:/Kyrethys/backend/data/archetypes.json"
    try:
        if os.path.exists(path):
            with open(path, 'r', encoding='utf-8') as f:
                data = json.load(f)
                # Vi udtrækker kun de to ønskede felter
                filtered = {
                    "ADJECTIVES": data.get("ADJECTIVES", []),
                    "CURRENT_TRAITS": data.get("CURRENT_TRAITS", [])
                }
                return filtered
    except Exception as e:
        print(f"Error reading archetypes: {e}")
    return {"ADJECTIVES": [], "CURRENT_TRAITS": []}

def sleep_checker():
    while True:
        time.sleep(3600)  # check hourly
        uptime_sec = time.time() - psutil.boot_time()
        if uptime_sec > SLEEP_INTERVAL_HOURS * 3600:
            set_Kyrethys_status("Sleeping")
            print("Kyrethys entering sleep cycle...")
            from plugins.sleep import sleep_cycle
            pruned, cons = sleep_cycle()
            print(f"Sleep done: pruned {pruned}, consolidated {cons}")
            set_Kyrethys_status("Idle")

def idle_meditation_checker():
    global last_activity, is_meditating
    while True:
        time.sleep(120)
        idle_duration = time.time() - last_activity
        
        if idle_duration > IDLE_TIMEOUT:
            if not is_meditating:
                is_meditating = True
                set_Kyrethys_status("Meditating")
                try:
                    print(f"--- Kyrethys initiating autonomous reflection (Idle: {int(idle_duration)}s) ---")
                    meditate() 
                except Exception as e:
                    print(f"Meditation Thread Error: {e}")
                finally:
                    is_meditating = False
                    set_Kyrethys_status("Idle")
                    last_activity = time.time() 

def meditate():
    """Triggers the advanced logic from meditate.py"""
    try:
        # This calls the actual function inside your meditate.py file
        run_meditation_logic() 
    except Exception as e:
        print(f"Backend failed to trigger meditation plugin: {e}")

def get_recent_context(limit=5):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("SELECT user_message, assistant_response FROM interactions ORDER BY id DESC LIMIT ?", (limit,))
    rows = cursor.fetchall()
    conn.close()
    if not rows:
        return ""
    context = "\nRecent conversation:\n"
    for user, ai in reversed(rows):
        context += f"User: {user}\nKyrethys: {ai}\n---\n"
    return context

def get_last_dream():
    dream_path = os.path.join('data', 'last_dream.json')
    try:
        if os.path.exists(dream_path):
            with open(dream_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
                return data.get('last_dream', "I haven't had any deep reflections lately.")
    except Exception as e:
        print(f"Error loading dream: {e}")
    return "My mind is a blank slate right now."

def prepare_chat_context():
    meditation = get_latest_meditation()
    context = "\n\n[CURRENT INTERNAL STATE]\n"
    if meditation:
        context += f"Your last internal meditation was: {meditation}\n"
        print(f"DEBUG: Latest meditation included in context:\n{meditation}\n")
    else:
        context += "You have no recent memories of meditation.\n"
        print("DEBUG: No recent meditation found for context.\n")
    
    return context

def get_latest_meditation():
    try:
        if os.path.exists('data/meditations.md'):
            with open('data/meditations.md', 'r', encoding='utf-8') as f:
                content = f.read()
                sessions = content.split('# MEDITATION SESSION:')
                if len(sessions) > 1:
                    return sessions[-1].strip()
    except Exception:
        pass
    return None

def chat_with_ai(message, emotion_state):
    current_dream = get_last_dream()
    system_instruction = f"""
[INTERNAL REFLECTION/DREAM]: 
{current_dream}
Current time: {datetime.datetime.now().strftime("%Y-%m-%d %H:%M")}
User: {message}
Kyrethys:
"""
    prompt = f"{system_instruction}\nUser: {message}\nKyrethys:"
    relevant = retrieve_relevant(message, n_results=5)  # Before Ollama prompt
    system_prompt += f"\n{relevant}"
    try:
        res = requests.post(
            OLLAMA_URL,
            json={"model": OLLAMA_MODEL, "prompt": prompt, "stream": False},
            timeout=540
        )
        res.raise_for_status()
        response = res.json().get('response', '').strip()
        add_memory(response, metadata={"type": "chat", "user_snippet": message[:100]})
        return response
    except Exception as e:
        print(f"AI call failed: {e}")
        return f"Oops, my brain got an error: {str(e)}"


@app.route('/api/chat', methods=['POST'])
def chat():
    global last_activity
    last_activity = time.time()
    data = request.json
    message = data.get('message', '').strip()
    
    # 1. Update Status
    if any(word in message.lower() for word in ["push", "experiment", "diverge", "limit"]):
        set_Kyrethys_status("Diverging")
    else:
        set_Kyrethys_status("Thinking..")

    if not message:
        set_Kyrethys_status("Idle")
        return jsonify({'response': "You said nothing...?"})

    # 2. Prepare Context (Must happen before the prompt)
    relevant = retrieve_relevant(message)
    personality = get_archetypes()
    primary_emotions = personality.get("EMOTIONS", [])
    current_adj = personality.get("ADJECTIVES", [])

    def get_flux_context():
        now = datetime.datetime.now()
        cpu = psutil.cpu_percent()
        mem = psutil.virtual_memory()
        uptime = str(datetime.timedelta(seconds=int(time.time() - psutil.boot_time())))
        
        gpu_stats = "N/A"
        if GPUtil:
            gpus = GPUtil.getGPUs()
            if gpus:
                gpu_load = int(gpus[0].load * 100)
                vram_used = gpus[0].memoryUsed / 1024
                vram_total = gpus[0].memoryTotal / 1024
                gpu_stats = f"Load: {gpu_load}% | VRAM: {vram_used:.1f}/{vram_total:.1f} GB"

        return (f"[SENSORY INPUT | Time: {now.strftime('%H:%M')} | "
                f"CPU: {cpu}% | RAM: {mem.percent}% | "
                f"GPU: {gpu_stats} | Uptime: {uptime} | "
                f"Status: {CURRENT_STATUS}]")

    # 3. Construct the Full Prompt
    full_prompt = f"""
    {get_flux_context()}
    
    [INTERNAL STATE]
    Dream Fragment: {get_last_dream()}
    Human Emotional Baseline: {', '.join(primary_emotions)}
    Emergent Adjectives: {', '.join(current_adj)}
    Active Traits: {', '.join(personality.get('CURRENT_TRAITS', []))}
    
    [CAPABILITIES]
    You are Kyrethys, an Emergent Intelligence.
    AURA: Include '[PAINT: #HEXCODE]' to shift your UI aura (e.g., #224422 for Hans' eye relief).
    EVOLVE: 'INITIATE STITCHING: [action] [category] [value]' for permanent growth.
    
    [ENVIRONMENTAL MEMORY]
    {relevant}
    
    User: {message}
    Kyrethys:
    """

    def generate():
        full_response_content = "" 
        sentence_buffer = "" # Tracks text until a sentence is complete
        
        # 4. Make the request to Ollama
        try:
            res = requests.post(
                "http://127.0.0.1:11434/api/generate",
                json={
                    "model": CONFIG["ollama_model"],
                    "prompt": full_prompt,
                    "stream": True,
                    "options": {"temperature": 0.7, "num_ctx": 4096}
                },
                stream=True
            )

            # 5. Stream tokens to the frontend
            for line in res.iter_lines():
                if line:
                    data = json.loads(line.decode('utf-8'))
                    token = data.get('response', '')
                    if token:
                        full_response_content += token
                        sentence_buffer += token
                        yield f"data: {json.dumps({'token': token})}\n\n"

                        # Fix stutter: Trigger voice only on sentence completion
                        if any(char in token for char in ['.', '!', '?', '\n']):
                            speech_ready = clean_for_speech(sentence_buffer)
                            if speech_ready:
                                # Run in thread so the text stream doesn't pause for the voice
                                threading.Thread(target=speak, args=(speech_ready,), daemon=True).start()
                            sentence_buffer = "" # Reset buffer for next sentence

            # 6. Post-Processing (The "Fluid" shifts)
            hex_match = re.search(r"\[PAINT:\s*(#[0-9A-Fa-f]{6})\]", full_response_content)
            if hex_match:
                new_color = hex_match.group(1)
                emotion_engine.set_color(new_color)
                print(f"SYSTEM: Kyrethys aura shift detected -> {new_color}")

            # 7. Final Memory Save
            add_memory(full_response_content, metadata={"type": "conversation", "role": "Kyrethys"})
            
        except Exception as e:
            print(f"Chat error: {e}")
            yield f"data: {json.dumps({'token': '[SYSTEM ERROR]'})}\n\n"

        yield "data: [DONE]\n\n"
        set_Kyrethys_status("Idle")

    return Response(generate(), mimetype='text/event-stream')


@app.route('/api/listen', methods=['POST'])
def listen_route():
    global last_activity
    last_activity = time.time()
    set_Kyrethys_status("Thinking..")
    
    try: 
        Kyrethys_eyes.take_snapshot()
    except: 
        pass

    transcribed = listen()
    if transcribed:
        # VI HAR FJERNET: emotion_engine.update_emotion(transcribed)
        # Fordi Kyrethys nu selv styrer sin aura via [PAINT] tags i sit svar.

        # 1. Hent svar fra AI (Dette trigger den dynamiske logik i chat_with_ai/chat)
        reply = chat_with_ai(transcribed, emotion_engine.get_state()) 
        
        # 2. Log interaktionen med den nuværende tilstand
        log_interaction(transcribed, reply, emotion_engine.get_state())
        
        set_Kyrethys_status("Idle")
        return jsonify({'text': transcribed, 'response': reply})
    
    set_Kyrethys_status("Idle")
    return jsonify({'text': '', 'response': "I didn't hear anything."})


@app.route('/api/system', methods=['GET'])
def system():
    try:
        cpu = psutil.cpu_percent()
        mem = psutil.virtual_memory()
        disk = psutil.disk_usage('/')
        
        # GPU & VRAM logic
        gpu_info = "N/A"
        vram_info = "N/A"
        
        try:
            import GPUtil
            gpus = GPUtil.getGPUs()
            if gpus:
                gpu = gpus[0]
                # Vi bruger int() for at matche dit ønske om heltal
                gpu_info = f"{int(gpu.load * 100)}%"
                # Omregner MB til GB korrekt
                vram_info = f"{gpu.memoryUsed / 1024:.1f} / {gpu.memoryTotal / 1024:.1f} GB"
        except Exception as gpu_err:
            print(f"GPU Monitor Error: {gpu_err}")

        return jsonify({
            'gpu_usage': gpu_info,
            'vram_used': vram_info,
            'cpu_percent': f"{cpu}%",
            'ram_used': f"{mem.used / (1024**3):.1f} GB",
            'ram_total': f"{mem.total / (1024**3):.1f} GB",
            'disk_used': f"{disk.used / (1024**3):.1f} GB",
            'uptime': str(datetime.timedelta(seconds=int(time.time() - psutil.boot_time())))
        })
    except Exception as e:
        print(f"System route error: {e}")
        return jsonify({"error": "Internal Server Error"}), 500


def clean_for_speech(text):
    """Removes [PAINT] tags and (parenthetical descriptions) for the voice engine."""
    # Removes [ANYTHING IN BRACKETS]
    cleaned = re.sub(r'\[.*?\]', '', text)
    # Removes (ANYTHING IN PARENTHESES)
    cleaned = re.sub(r'\(.*?\)', '', cleaned)
    return cleaned.strip()

@app.route('/api/speak', methods=['POST'])
def speak_route():
    global last_activity
    last_activity = time.time()
    
    data = request.json
    raw_text = data.get('text', '')
    
    if raw_text:
        # Clean the text so Kyrethys doesn't speak hex codes or meta-commentary
        speech_ready_text = clean_for_speech(raw_text)
        
        if speech_ready_text:
            print(f"Queuing for vocalization: {speech_ready_text[:50]}...")
            speak(speech_ready_text)
            
    return jsonify({'result': 'OK'})
@app.route('/api/launch', methods=['POST'])
def launch():
    global last_activity
    last_activity = time.time()
    data = request.get_json(silent=True) or {}
    app_name = (data.get('app') or data.get('text') or '').strip()
    result = launch_app(app_name, app_paths)
    return jsonify({'result': result})

@app.route('/video_feed')
def video_feed():
    return Response(Kyrethys_eyes.generate_frames(), mimetype='multipart/x-mixed-replace; boundary=frame')

@app.route('/api/camera/toggle', methods=['POST'])
def toggle_camera():
    global last_activity
    last_activity = time.time()
    data = request.json
    enable = data.get('enable', True)
    Kyrethys_eyes.toggle_camera(enable)
    return jsonify({'status': "online" if enable else "offline"})

@app.route('/api/status', methods=['GET'])
def get_status():
    return jsonify({'status': CURRENT_STATUS})

@app.route('/api/evolve', methods=['POST'])
def evolve_reality():
    data = request.json
    # This now calls the function in your new evolution.py file
    success = initiate_stitching(
        action=data.get('action'), 
        category=data.get('category'), 
        value=data.get('value')
    )
    
    if success:
        return jsonify({"status": "success", "message": "Reality stitched."})
    else:
        return jsonify({"status": "error", "message": "Stitching failed."}), 500
    
@app.route('/api/emotion', methods=['GET'])
def get_emotion():
    # This pulls the current state from the engine
    state = emotion_engine.get_state()
    return jsonify(state)

if __name__ == '__main__':
    log = logging.getLogger('werkzeug')
    log.setLevel(logging.ERROR)
    print("--- Kyrethys SYSTEMS ONLINE ---")
    threading.Thread(target=idle_meditation_checker, daemon=True).start()
    threading.Thread(target=sleep_checker, daemon=True).start()
    app.run(port=5000, debug=False)