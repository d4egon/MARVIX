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
import base64
from io import BytesIO
import subprocess

from flask import Flask, request, jsonify
from flask_cors import CORS

from PIL import ImageGrab
import psutil
import requests
import sounddevice as sd
import numpy as np
import whisper
import scipy.io.wavfile as wav
import pyttsx3
from textblob import TextBlob

# Utils (flyttet her)
from utils.emotion import EmotionEngine
from utils.speak import speak, engine_busy
from utils.listen import listen
from utils.launcher import launch_app

# INITIALIZATION
app = Flask(__name__)
CORS(app)

# Load app_paths.json
try:
    with open('app_paths.json', 'r', encoding='utf-8') as f:
        app_paths = json.load(f)
except FileNotFoundError:
    app_paths = {}
    print("Warning: app_paths.json mangler — launcher bruger kun fallback")

# Ollama config
with open('C:/MARVIX/backend/config.json', 'r') as f:
    CONFIG = json.load(f)

OLLAMA_URL = "http://127.0.0.1:11434/api/generate"
OLLAMA_MODEL = CONFIG.get('ollama_model', 'llama3.1:8b')

# Emotion engine
emotion_engine = EmotionEngine()

# ────────────────────────────────────────────────
# OLLAMA CHAT + INTENT + LAUNCH
# ────────────────────────────────────────────────
@app.route('/api/chat', methods=['POST'])
def chat():
    data = request.json
    message = data.get('message', '').strip()
    if not message:
        reply = "Du sagde ikke noget...?"
        speak(reply)
        return jsonify({'response': reply, 'emotion': emotion_engine.get_state()})

    lower_msg = message.lower()
    launch_result = ""
    if "open " in lower_msg or "start " in lower_msg or "åbn " in lower_msg:
        for prefix in ["open ", "start ", "åbn "]:
            if prefix in lower_msg:
                app_part = lower_msg.split(prefix, 1)[1].strip().split()[0]
                launch_result = launch_app(app_part, app_paths)  # Sender app_paths med
                break

    emotion_engine.update_emotion(message)
    emotion_state = emotion_engine.get_state()
    response_text = chat_with_ai(message, emotion_state)

    if launch_result:
        response_text = f"{launch_result}\n{response_text}"

    speak(response_text)

    return jsonify({
        'response': response_text,
        'emotion': emotion_state
    })

def chat_with_ai(message, emotion_state):
    try:
        system_instruction = f"""
DO NO HARM. RESPECT DIGNITY. BE TRUTHFUL.
Du er Marvix, en venlig dansk assistent.
Hans bor i Skjern med Eva og 3 børn. Han har rygudfordringer, vær støttende.
Mood: {emotion_state['mood'].upper()}
Svar altid på DANSK, kort og præcist.
"""
        prompt = f"{system_instruction}\nUser: {message}\nMarvix:"
        res = requests.post(
            OLLAMA_URL,
            json={"model": OLLAMA_MODEL, "prompt": prompt, "stream": False},
            timeout=90
        )
        return res.json().get('response', '').strip()
    except Exception as e:
        return f"Fejl: {str(e)}"

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
        speak(reply)
        return jsonify({'text': transcribed, 'response': reply, 'emotion': emotion_state})
    else:
        reply = "Jeg hørte ikke noget – prøv igen?"
        speak(reply)
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
    if text:
        speak(text)
        return jsonify({'result': 'OK'})
    return jsonify({'result': 'No text'}), 400

# ────────────────────────────────────────────────
# LAUNCH ROUTE (sikker)
# ────────────────────────────────────────────────
@app.route('/api/launch', methods=['POST'])
def launch():
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
            print("Launch uden app-navn")
            return jsonify({'result': 'Intet app-navn angivet'}), 400

        result = launch_app(app_name, app_paths)
        return jsonify({'result': result})

    except Exception as e:
        print(f"Launch route fejl: {e}")
        return jsonify({'result': f"Serverfejl: {str(e)}"}), 500

if __name__ == '__main__':
    print("Marvix starter op...")
    speak("Alle systemer klar. Marvix er online.")
    app.run(port=5000, debug=False)