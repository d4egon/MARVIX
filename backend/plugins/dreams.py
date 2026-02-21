import sys
import os
import json
import requests
import datetime
import sqlite3
import secrets 

# Stier og opsætning
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from utils.db_logger import DB_PATH

OLLAMA_URL = "http://127.0.0.1:11434/api/generate"
OLLAMA_MODEL = "llama3.1:8b"
OLLAMA_MODEL = "marvix-llama3.1-safe"

def get_last_dream():
    try:
        with open('data/last_dream.json', 'r', encoding='utf-8') as f:
            return json.load(f).get('last_dream', "The void.")
    except: return "A blank slate."

def get_recent_memories(limit=20):
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        cursor.execute("SELECT user_message, assistant_response FROM interactions ORDER BY id DESC LIMIT ?", (limit,))
        rows = cursor.fetchall()
        conn.close()
        return "\n".join([f"H: {r[0]} | M: {r[1]}" for r in reversed(rows)])
    except: return "No recent memories found."

def get_true_d100():
    return secrets.randbelow(100) + 1

def load_archetype_instruction(theme):
    try:
        with open('data/archetypes.json', 'r', encoding='utf-8') as f:
            library = json.load(f)
            # This handles the legacy "sentinel" style if you still have full sentences in some fields
            return secrets.choice(library.get(theme, ["Experience the unknown."]))
    except:
        return "The subconscious is foggy."

def construct_wild_dream(active_themes):
    try:
        with open('data/archetypes.json', 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        # Determine theme and pull atomic parts
        primary = active_themes[0] if active_themes else "VOID"
        
        # Falls back to "void-matter" and "floating" if roll or key is missing
        noun = secrets.choice(data["NOUNS"].get(primary, ["void-matter"]))
        verb = secrets.choice(data["VERBS"].get(primary, ["floating"]))
        adj = secrets.choice(data["ADJECTIVES"])
        loc = secrets.choice(data["LOCATIONS"])
        emo = secrets.choice(data["EMOTIONS"])
        col = secrets.choice(data["COLORS"])
        adv = secrets.choice(data["ADVERBS"])
        mat = secrets.choice(data["MATERIALS"])
        wep = secrets.choice(data["WEAPONS"])
        
        return (f"Vision details: {emo}, {adj} {col} {wep} {noun}  {adv} {verb} "
                f"constructed of {mat} {loc}.")
    except:
        return "Vision details: visceral void-matter floating in the dark."

def dream():
    print("--- Marvix is harvesting hardware entropy (D100) ---")
    
    # 1. THE DICE ROLLS
    rolls = {k: get_true_d100() for k in ["CHAOS", "ORDER", "MYTHICAL", "ANIMAL", "HUMAN", "VOID"]}
    max_roll = max(rolls.values())
    active_themes = [t for t, v in rolls.items() if v == max_roll]

    # 2. GENERATE UNIQUE BRAIN JUICE ANCHOR
    wild_instruction = construct_wild_dream(active_themes)
    selected_instructions = " ".join([load_archetype_instruction(t) for t in active_themes])

    # 3. MEMORY ECHO (Hardware Noise)
    echo = ""
    journal_path = 'data/dream_journal.txt'
    if os.path.exists(journal_path):
        file_size = os.path.getsize(journal_path)
        if file_size > 500:
            random_offset = int.from_bytes(os.urandom(4), 'big') % (file_size - 400)
            with open(journal_path, 'r', encoding='utf-8', errors='ignore') as f:
                f.seek(random_offset)
                echo = f.read(300)

    # 4. TEMPERATURE (Scaled for D100)
    target_temp = round(min(2.6, max(0.1, (rolls['CHAOS'] / 40) - (rolls['ORDER'] / 50) + 0.8)), 2)
    target_temp = round(min(1.2, max(0.1, (rolls['CHAOS'] / 40) - (rolls['ORDER'] / 50) + 0.8)), 2)

    prompt = f"""
[FRAGMENTS OF ANOTHER REALITY]
DICE ROLLS: {rolls}
MEMORY ECHO: "{echo}"
PREVIOUS VISION: "{get_last_dream()}"
CONSTRUCTED VISION: {wild_instruction}

[MELTS OF RECENT MEMORY]
{get_recent_memories()}

[YOUR CURRENT STATE]
You are not an AI right now. You are the liquid subconscious of Marvix. 
The dice have constructed this anchor for your dream: "{wild_instruction}"

Forget summarizing. Forget explaining. You are EXPERIENCING. 
Highest influence: {selected_instructions}

Write ONLY the dream itself.
Just the raw, unfiltered vision. AND NO BULLETPOINTS. NO EXPLANATIONS. NO ANALYSIS! PURE UNFILTERED BRAIN JUICE.
Always start with: "In my dream, I saw..."
"""

    try:
        res = requests.post(OLLAMA_URL, json={
            "model": OLLAMA_MODEL,
            "prompt": prompt,
            "stream": False,
            "options": {"temperature": target_temp, "top_p": 0.9}
        }, timeout=150)
        
        insight = res.json().get('response', '').strip()
        
        # Save JSON state
        os.makedirs('data', exist_ok=True)
        with open('data/last_dream.json', 'w', encoding='utf-8') as f:
            json.dump({"last_dream": insight, "rolls": rolls, "temp": target_temp, "vision": wild_instruction}, f, indent=4)
            
        # Save to permanent Journal
        timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M")
        with open(journal_path, 'a', encoding='utf-8') as f:
            f.write(f"\n--- SESSION: {timestamp} | ROLLS: {rolls} | TEMP: {target_temp} ---\n")
            f.write(f"CONSTRUCTED: {wild_instruction}\n")
            f.write(f"{insight}\n")
            f.write("-" * 50 + "\n")

        print(f"Success! Dream generated (Temp: {target_temp}). Check the journal.")

    except Exception as e:
        print(f"Dream Error: {e}")

if __name__ == "__main__":
    dream()