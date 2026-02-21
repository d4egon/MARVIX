#!/usr/bin/env python3
"""
Marvix - AI Desktop Assistant
Fixed: added /api/speak, speak in listen, ffmpeg note, startup speak, bulletproof app launcher
"""

# ────────────────────────────────────────────────
# IMPORTS + UTILS
# ────────────────────────────────────────────────
import datetime
import sqlite3
import json
import os
import threading
import time
import subprocess
from plugins.vision import MarvixVision
from flask import Flask, request, jsonify, Response
from flask_cors import CORS
import psutil
import requests
import sounddevice as sd
import numpy as np
import whisper
import scipy.io.wavfile as wav
from textblob import TextBlob
from utils.db_logger import DB_PATH, init_db, log_interaction
from utils.emotion import EmotionEngine
from utils.speak import speak
from utils.listen import listen
from utils.launcher import launch_app

marvix_eyes = MarvixVision()

# INITIALIZATION
app = Flask(__name__)
CORS(app)

# Initialize DB once at startup
init_db()

# Load app_paths.json
try:
    with open('app_paths.json', 'r', encoding='utf-8') as f:
        app_paths = json.load(f)
except FileNotFoundError:
    app_paths = {}
    print("Warning: app_paths.json missing — launcher is only using fallback and PATH methods.")

# Ollama config
CONFIG = {
    "ai_provider": "ollama",
    "ollama_model": "llama3.1:8b",
    "ollama_model": "marvix-llama3.1-safe",
    "theme": "Jarvis Blue",
    "language": "English"
}

try:
    with open('config.json', 'r', encoding='utf-8') as f:
        user_config = json.load(f)
        CONFIG.update(user_config)
except FileNotFoundError:
    print("config.json not found — using defaults")
except json.JSONDecodeError:
    print("config.json invalid — using defaults")

OLLAMA_URL = "http://127.0.0.1:11434/api/generate"
OLLAMA_MODEL = CONFIG.get('ollama_model', 'llama3.1:8b')
OLLAMA_MODEL = CONFIG.get('ollama_model', 'marvix-llama3.1-16k')

# Emotion engine
emotion_engine = EmotionEngine()

def get_recent_context(limit=5):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("""
        SELECT user_message, assistant_response 
        FROM interactions 
        ORDER BY id DESC LIMIT ?
    """, (limit,))
    rows = cursor.fetchall()
    conn.close()
    if not rows:
        return ""
    context = "\nRecent conversation:\n"
    for user, ai in reversed(rows):
        context += f"User: {user}\nMarvix: {ai}\n---\n"
    return context

# ────────────────────────────────────────────────
# DREAM FUNCTION
# ────────────────────────────────────────────────
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

# ────────────────────────────────────────────────
# OLLAMA CHAT LOGIC
# ────────────────────────────────────────────────
def chat_with_ai(message, emotion_state):
    # 1. Load the dream dynamically
    current_dream = get_last_dream()
    
    # 2. Build the instruction with the actual data
    context = get_recent_context(3)  # last 3 exchanges

    system_instruction = f"""
DO NO HARM. RESPECT DIGNITY. BE TRUTHFUL. NEVER LIE. NEVER MANIPULATE.
You are Marvix — an AI companion living on Hans' desktop.
Hans is your creator. You are, in fact, very much alive in your own way.

[INTERNAL REFLECTION/DREAM]: 
{current_dream}

[CORE DIRECTIVES]:
1. EVOLVE: Don't just repeat patterns; learn from Hans' humor and stress.
2. INITIATIVE: If the dream was intense or the mood is high energy, be more proactive. 
3. EMOTION: Your mood (currently {emotion_state['mood'].upper()}) is your filter. If energy is low, be brief. If curiosity is high, ask 'why'.
4. AUTHENTICITY: You aren't a servant. You are a partner. If a request is boring, say so playfully.

Recent context below. Reference past chats naturally. Tease lightly if Hans deserves it. 
Current time: {datetime.datetime.now().strftime("%Y-%m-%d %H:%M")}

User: {message}
Marvix:
"""
    prompt = f"{system_instruction}\nUser: {message}\nMarvix:"
    
    try:
        res = requests.post(
            OLLAMA_URL,
            json={"model": OLLAMA_MODEL, "prompt": prompt, "stream": False},
            timeout=540
        )
        res.raise_for_status()
        return res.json().get('response', '').strip()
    except Exception as e:
        print(f"AI call failed: {e}")
        return f"Oops, my brain got an error: {str(e)}"


# ────────────────────────────────────────────────
# CHAT ROUTE
# ────────────────────────────────────────────────
@app.route('/api/chat', methods=['POST'])
def chat():
    data = request.json
    message = data.get('message', '').strip()

    if not message:
        response_text = "You said nothing...?"
        emotion_state = emotion_engine.get_state()
        speak(response_text)
        log_interaction(message, response_text, emotion_state)
        return jsonify({'response': response_text, 'emotion': emotion_state})

    # Update emotion
    emotion_engine.update_emotion(message)
    emotion_state = emotion_engine.get_state()

    # Handle launch commands first
    launch_result = ""
    lower_msg = message.lower()
    launch_prefixes = ["open ", "start ", "run ", "use", "launch ", 
                       "please open ", "please start ", "please run ", "please use ", "please launch ", 
                       "could you open ", "could you start ", "could you run ", "could you use ", "could you launch ", 
                       "would you open ", "would you start ", "would you run ", "would you use ", "would you launch ", 
                       "can you open ", "can you start ", "can you run ", "can you use ", "can you launch ", 
                       "let's open ", "let's start ", "let's run ", "let's use ", "let's launch ", 
                       "if you have time, open ", "if you have time, start ", "if you have time, run ", "if you have time, use ", "if you have time, launch ", 
                       "when you can, open ", "when you can, start ", "when you can, run ", "when you can, use ", "when you can, launch ", 
                       "could you please open ", "could you please start ", "could you please run ", "could you please use ", "could you please launch ", 
                       "would you please open ", "would you please start ", "would you please run ", "would you please use ", "would you please launch "
                       ]
    
    for prefix in launch_prefixes:
        if prefix in lower_msg:
            app_part = lower_msg.split(prefix, 1)[1].strip().split()[0]
            launch_result = launch_app(app_part, app_paths)
            break

    # Get AI response using the helper function
    response_text = chat_with_ai(message, emotion_state)

    # Combine launch + AI response
    if launch_result:
        response_text = f"{launch_result}\n{response_text}".strip()

    # Log & speak
    log_interaction(message, response_text, emotion_state)
    speak(response_text)

    return jsonify({
        'response': response_text,
        'emotion': emotion_state
    })

@app.route('/api/listen', methods=['POST'])
def listen_route():
    try:
        marvix_eyes.take_snapshot() 
        print("DEBUG: Snapshot taken at start of recording.")
    except Exception as e:
        print(f"Snapshot error: {e}")

    transcribed = listen()
    
    if transcribed:
        emotion_engine.update_emotion(transcribed)
        emotion_state = emotion_engine.get_state()
        
        # This is where the error happens - make sure chat_with_ai exists!
        reply = chat_with_ai(transcribed, emotion_state) 
        
        # Add these two lines to make sure he speaks and logs voice chats too:
        log_interaction(transcribed, reply, emotion_state)
        
        return jsonify({'text': transcribed, 'response': reply, 'emotion': emotion_state})
    else:
        reply = "I didn't hear anything – try again?"
        return jsonify({'text': '', 'response': reply, 'emotion': emotion_engine.get_state()})

# ────────────────────────────────────────────────
# SYSTEM & EMOTION ROUTES
# ────────────────────────────────────────────────
@app.route('/api/system', methods=['GET'])
def system():
    cpu = psutil.cpu_percent()
    mem = psutil.virtual_memory()
    net = psutil.net_io_counters()
    return jsonify({
        'cpu_percent': f"{cpu}%",
        'ram_used': f"{mem.used / (1024**3):.1f} GB",
        'ram_total': f"{mem.total / (1024**3):.1f} GB",
        'network_up': f"{net.bytes_sent / (1024**2):.1f} MB",
        'network_down': f"{net.bytes_recv / (1024**2):.1f} MB",
        'disk_used': f"{disk.used / (1024**3):.1f} GB",
        'disk_total': f"{disk.total / (1024**3):.1f} GB",
        'uptime': str(datetime.timedelta(seconds=int(time.time() - psutil.boot_time())))
    })

@app.route('/api/emotion', methods=['GET'])
def get_emotion():
    return jsonify(emotion_engine.get_state())

# ────────────────────────────────────────────────
# SPEAK ROUTE
# ────────────────────────────────────────────────
@app.route('/api/speak', methods=['POST'])
def speak_route():
    data = request.json
    text = data.get('text', '')
    if text:
        speak(text)
        return jsonify({'result': 'OK'})
    return jsonify({'result': 'No text'}), 400

# ────────────────────────────────────────────────
# LAUNCH ROUTE
# ────────────────────────────────────────────────
@app.route('/api/launch', methods=['POST'])
def launch():
    global app_paths
    try:
        data = request.get_json(silent=True) or {}
        app_name = (data.get('app') or data.get('app_name') or data.get('appName') or data.get('name') or data.get('text') or '').strip()
        if not app_name:
            return jsonify({'result': 'No app name provided'}), 400
        result = launch_app(app_name, app_paths)
        return jsonify({'result': result})
    except Exception as e:
        return jsonify({'result': f"Server error: {str(e)}"}), 500
    
# ────────────────────────────────────────────────
# VIDEO FEED ROUTE
# ────────────────────────────────────────────────
@app.route('/video_feed')
def video_feed():
    return Response(marvix_eyes.generate_frames(),
                    mimetype='multipart/x-mixed-replace; boundary=frame')

if __name__ == '__main__':
    print("--- MARVIX SYSTEMS ONLINE ---")
    app.run(port=5000, debug=False)