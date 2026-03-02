import sqlite3
import os
import json
import cv2
from datetime import datetime
from plugins.vision import KyrethysVision
# Her bruger vi den 'dybe' import som vi ved virker
from mediapipe.python.solutions import face_mesh as mp_face_mesh

DB_PATH = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'data', 'memory', 'Kyrethys_logs.db')

# Initialisér komponenter
Kyrethys_eyes = KyrethysVision()
# Initialisér face_mesh med den korrekte sti
face_mesh = mp_face_mesh.FaceMesh(
    static_image_mode=True, 
    max_num_faces=1, 
    refine_landmarks=True
)

def init_db():
    os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
    with sqlite3.connect(DB_PATH, check_same_thread=False, timeout=10) as conn:
        cursor = conn.cursor()
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS interactions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp TEXT NOT NULL,
                user_message TEXT,
                assistant_response TEXT,
                emotion_mood TEXT,
                emotion_energy INTEGER,
                emotion_curiosity INTEGER,
                emotion_color TEXT,
                snapshot_path TEXT,
                face_coordinates_json TEXT,
                ai_learned_tag TEXT
            )
        ''')
        conn.commit()

def extract_face_mesh(image_path):
    print(f"DEBUG: Analyserer ansigtstræk på: {image_path}")
    image = cv2.imread(image_path)
    if image is None: return None

    # Nu vender billedet allerede rigtigt fra vision.py
    results = face_mesh.process(cv2.cvtColor(image, cv2.COLOR_BGR2RGB))
    
    if results.multi_face_landmarks:
        print("DEBUG: Læring fuldført (468 punkter registreret).")
        coords = [{"x": l.x, "y": l.y, "z": l.z} for l in results.multi_face_landmarks[0].landmark]
        return json.dumps(coords)
    
    print("DEBUG: Kunne ikke finde ansigt (tjek lys/vinkel).")
    return None

def log_interaction(user_message: str, assistant_response: str, emotion_state: dict, snapshot_filename: str = None):
    # Vi har fjernet Kyrethys_eyes.take_snapshot() herfra for at undgå dobbelt-blink!
    
    # 2. Udtræk koordinater (kun hvis vi har fået et filnavn fra backenden)
    coords_json = None
    if snapshot_filename:
        # DB_PATH er i backend/utils/../data/memory/
        # Vi skal 3 niveauer op for at ramme backend-roden
        base_dir = os.path.dirname(os.path.dirname(os.path.dirname(DB_PATH)))
        img_path = os.path.join(base_dir, 'data', 'snapshots', snapshot_filename)
        
        if os.path.exists(img_path):
            coords_json = extract_face_mesh(img_path)
        else:
            print(f"DEBUG: Kunne ikke finde filen til FaceMesh: {img_path}")

    # 3. Gem i DB
    with sqlite3.connect(DB_PATH, check_same_thread=False, timeout=10) as conn:
        cursor = conn.cursor()
        now = datetime.utcnow().isoformat()
        
        cursor.execute('''
            INSERT INTO interactions 
            (timestamp, user_message, assistant_response, emotion_mood, 
             emotion_energy, emotion_curiosity, emotion_color, 
             snapshot_path, face_coordinates_json, ai_learned_tag)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            now, user_message, assistant_response, 
            emotion_state.get('mood', 'stable'),
            emotion_state.get('energy', 0), 
            emotion_state.get('curiosity', 0), 
            emotion_state.get('color', '#00d4ff'),
            snapshot_filename, coords_json, "pattern_captured"
        ))
        conn.commit()