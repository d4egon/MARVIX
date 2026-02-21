# backend/utils/db_logger.py
import sqlite3
import os
from datetime import datetime

DB_PATH = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'data', 'memory', 'marvix_logs.db')

def init_db():
    """Create the logs table if it doesn't exist."""
    os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
    
    conn = sqlite3.connect(DB_PATH)
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
            emotion_color TEXT
        )
    ''')
    conn.commit()
    conn.close()

def log_interaction(user_message: str, assistant_response: str, emotion_state: dict):
    """Log a full interaction to SQLite."""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    now = datetime.utcnow().isoformat()
    
    cursor.execute('''
        INSERT INTO interactions 
        (timestamp, user_message, assistant_response, 
         emotion_mood, emotion_energy, emotion_curiosity, emotion_color)
        VALUES (?, ?, ?, ?, ?, ?, ?)
    ''', (
        now,
        user_message,
        assistant_response,
        emotion_state.get('mood', 'unknown'),
        emotion_state.get('energy', 0),
        emotion_state.get('curiosity', 0),
        emotion_state.get('color', '#00d4ff')
    ))
    
    conn.commit()
    conn.close()