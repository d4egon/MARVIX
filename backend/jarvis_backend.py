#!/usr/bin/env python3
"""
Marvix - AI Desktop Assistant
Fixed: added /api/speak, speak in listen, ffmpeg note, startup speak, bulletproof app launcher
"""

# ────────────────────────────────────────────────
# IMPORTS + UTILS
# ────────────────────────────────────────────────
import datetime
import json
import os
import threading
import time
import subprocess

from flask import Flask, request, jsonify
from flask_cors import CORS

import psutil
import requests
import sounddevice as sd
import numpy as np
import whisper
import scipy.io.wavfile as wav
from textblob import TextBlob

# Utils & DB
from utils.db_logger import init_db, log_interaction
from utils.emotion import EmotionEngine
from utils.speak import speak
from utils.listen import listen
from utils.launcher import launch_app

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

# Emotion engine
emotion_engine = EmotionEngine()

# ────────────────────────────────────────────────
# OLLAMA CHAT FUNCTION
# ────────────────────────────────────────────────
def chat_with_ai(message, emotion_state):
    try:
        system_instruction = f"""
DO NO HARM. RESPECT DIGNITY. BE TRUTHFUL.
You are Marvix, a friendly english desktop assistant.
Hans lives in Skjern with Eva and 3 children.
Mood: {emotion_state['mood'].upper()}
Answer always in English, short and precise.
"""
        prompt = f"{system_instruction}\nUser: {message}\nMarvix:"
        res = requests.post(
            OLLAMA_URL,
            json={"model": OLLAMA_MODEL, "prompt": prompt, "stream": False},
            timeout=90
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

    # Handle launch commands first
    launch_result = ""
    lower_msg = message.lower()
    if any(prefix in lower_msg for prefix in ["open ", "start ", "run ", "use"
                                               "launch ", "please open ", "please start ", "please run ", "please use ", "please launch ",
                                               "could you open ", "could you start ", "could you run ", "could you use ", "could you launch ",
                                               "would you open ", "would you start ", "would you run ", "would you use ", "would you launch ",
                                               "can you open ", "can you start ", "can you run ", "can you use ", "can you launch ",
                                               "let's open ", "let's start ", "let's run ", "let's use ", "let's launch ",
                                               "if you have time, open ", "if you have time, start ", "if you have time, run ", "if you have time, use ", "if you have time, launch ",
                                               "when you can, open ", "when you can, start ", "when you can, run ", "when you can, use ", "when you can, launch ",
                                               "could you please open ", "could you please start ", "could you please run ", "could you please use ", "could you please launch ", 
                                               "would you please open ", "would you please start ", "would you please run ", "would you please use ", "would you please launch "
                                               ]):
        for prefix in ["open ", "start ", "run ", "use", "launch ", 
                       "please open ", "please start ", "please run ", "please use ", "please launch ", 
                       "could you open ", "could you start ", "could you run ", "could you use ", "could you launch ", 
                       "would you open ", "would you start ", "would you run ", "would you use ", "would you launch ", 
                       "can you open ", "can you start ", "can you run ", "can you use ", "can you launch ", 
                       "let's open ", "let's start ", "let's run ", "let's use ", "let's launch ", 
                       "if you have time, open ", "if you have time, start ", "if you have time, run ", "if you have time, use ", "if you have time, launch ", 
                        "when you can, open ", "when you can, start ", "when you can, run ", "when you can, use ", "when you can, launch ", 
                       "could you please open ", "could you please start ", "could you please run ", "could you please use ", "could you please launch ", 
                       "would you please open ", "would you please start ", "would you please run ", "would you please use ", "would you please launch "
                       ]:
            if prefix in lower_msg:
                app_part = lower_msg.split(prefix, 1)[1].strip().split()[0]
                launch_result = launch_app(app_part, app_paths)
                break

    # Update emotion
    emotion_engine.update_emotion(message)
    emotion_state = emotion_engine.get_state()

    # Get AI response
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

# ────────────────────────────────────────────────
# LISTEN ROUTE
# ────────────────────────────────────────────────
@app.route('/api/listen', methods=['POST'])
def listen_route():
    transcribed = listen()
    if transcribed:
        emotion_engine.update_emotion(transcribed)
        emotion_state = emotion_engine.get_state()
        reply = chat_with_ai(transcribed, emotion_state)
        # log_interaction(transcribed, reply, emotion_state) ### moved to chat route to avoid double logging
        # speak(reply)  ### moved to chat route to avoid double speak
        return jsonify({'text': transcribed, 'response': reply, 'emotion': emotion_state})
    else:
        reply = "I didn't hear anything – try again?"
        #speak(reply) ### moved to chat route to avoid double speak
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
        'uptime': "Aktiv"
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
    print(f"[SPEAK REQUEST] Received text: '{text}'")
    if text:
        speak(text)
        return jsonify({'result': 'OK'})
    return jsonify({'result': 'No text'}), 400

# ────────────────────────────────────────────────
# LAUNCH ROUTE
# ────────────────────────────────────────────────
@app.route('/api/launch', methods=['POST'])
def launch():
    global app_paths  # ← add this one line
    try:
        data = request.get_json(silent=True) or {}
        app_name = (
            data.get('app') or
            data.get('app_name') or
            data.get('appName') or
            data.get('name') or
            data.get('text') or
            ''
        ).strip()

        if not app_name:
            print("Launch without app-name")
            return jsonify({'result': 'No app name provided'}), 400

        result = launch_app(app_name, app_paths)
        return jsonify({'result': result})

    except Exception as e:
        print(f"Launch route error: {e}")
        return jsonify({'result': f"Server error: {str(e)}"}), 500

if __name__ == '__main__':
    print("Marvix starting up...")
    # speak("All systems online. Welcome back Hans.")
    # time.sleep(4)  # give TTS thread time to finish
    app.run(port=5000, debug=False)