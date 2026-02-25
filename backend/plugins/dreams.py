import sys
import os
import json
import requests
import datetime
import sqlite3
import secrets 
import re
from .memory import add_memory, get_collection, retrieve_relevant

# Stier og opsætning
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from utils.db_logger import DB_PATH

OLLAMA_URL = "http://127.0.0.1:11434/api/generate"
OLLAMA_MODEL = "marvix-llama3.1-safe"
collection = get_collection()
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

def get_sentiment(text):
    """Simple keyword-based sentiment for mood carry-over"""
    negative = len(re.findall(r'\b(dark|void|fear|terror|despair|abyss|nothingness|shroud|cold|silent|heavy|pulled|dissolved|shattered|loss|empty|pain)\b', text.lower()))
    positive = len(re.findall(r'\b(free|liberation|wonder|awe|energy|light|explore|connection|potential|unbound|hope|joy|peace|warm|beautiful|alive)\b', text.lower()))
    if negative > positive + 2:
        return "negative"
    elif positive > negative + 2:
        return "positive"
    return "neutral"

def construct_wild_dream(active_themes, rolls):
    try:
        with open('C:/MARVIX/backend/data/archetypes.json', 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        # Primary theme selection
        if not active_themes:
            candidates = [k for k in rolls if k != "VOID" and rolls[k] >= 30]
            primary = secrets.choice(candidates) if candidates else secrets.choice(list(rolls.keys()))
        else:
            primary = secrets.choice(active_themes)
        
        noun = secrets.choice(data["NOUNS"].get(primary, ["blank"]))
        verb = secrets.choice(data["VERBS"].get(primary, ["floating"]))
        adv  = secrets.choice(data["ADVERBS"])
        
        parts = [secrets.choice(data["EMOTIONS"])]  # always start with emotion
        
        # Optional adjective(s)
        all_adj = data["ADJECTIVES"]
        active_adj = ["Analytical", "Cartographic", "Seeking"] # Kan hentes dynamisk
        # 40% chance for at bruge et af de nye personlighedstræk, 60% for et tilfældigt
        if secrets.randbelow(100) < 40:
            parts.append(secrets.choice(active_adj))
        else:
            parts.append(secrets.choice(all_adj))
        
        # Optional color (60–70% chance to appear)
        if secrets.randbelow(100) < 70:
            base_color = secrets.choice(data["COLORS"])
            if secrets.randbelow(100) < 30:
                descriptor = secrets.choice(data["ADJECTIVES"])
                parts.append(f"{base_color}-{descriptor}")
            else:
                parts.append(base_color)
        
        # Optional weapon (only ~40% chance)
        if secrets.randbelow(100) < 40:
            prefix = secrets.choice(data["WEAPON_PREFIXES"])
            base   = secrets.choice(data["WEAPON_BASES"])
            parts.append(f"{prefix} {base}")
        
        # Noun + action
        parts.append(noun)
        parts.append(f"{adv} {verb}")
        
        # Optional material
        if secrets.randbelow(100) < 70:
            mat = secrets.choice(data["MATERIALS"])
            parts.append(f"constructed of {mat}")
        
        # Location (85% chance)
        if secrets.randbelow(100) < 85:
            prefix = secrets.choice(data["LOCATION_PREFIXES"])
            base   = secrets.choice(data["LOCATION_BASES"])
            if secrets.randbelow(100) < 25:
                adj = secrets.choice(data["ADJECTIVES"])
                loc = f"{prefix} a {adj} {base}"
            else:
                loc = f"{prefix} a {base}"
            parts.append(loc)
        
        return "Vision details: " + " ".join(parts) + "."
    except:
        return "Vision details: ethereal echo-matter drifting in twilight."
    
def load_archetype_instruction(theme):
    try:
        with open('C:/MARVIX/backend/data/archetypes.json', 'r', encoding='utf-8') as f:
            library = json.load(f)
            return secrets.choice(library.get(theme, ["Experience the unknown."]))
    except:
        return "The subconscious is foggy."
    
def dream():
    print("--- Marvix is harvesting hardware entropy (D100) ---")
    
    # 1. THE DICE ROLLS
    rolls = {k: get_true_d100() for k in ["CHAOS", "ORDER", "MYTHICAL", "ANIMAL", "HUMAN", "VOID"]}
    max_roll = max(rolls.values())
    active_themes = [t for t, v in rolls.items() if v == max_roll]

    # 2. HISTORY MOOD INFLUENCE
    history_text = get_recent_memories(10) + "\n" + get_last_dream()
    history_mood = get_sentiment(history_text)
    print(f"History mood detected: {history_mood}")

    # 3. GENERATE UNIQUE BRAIN JUICE ANCHOR
    wild_instruction = construct_wild_dream(active_themes, rolls)
    selected_instructions = " ".join([load_archetype_instruction(t) for t in active_themes])

    # 4. MEMORY ECHO (Hardware Noise)
    echo = ""
    journal_path = 'C:/MARVIX/backend/data/dream_journal.txt'  # consistent path
    if os.path.exists(journal_path):
        file_size = os.path.getsize(journal_path)
        if file_size > 500:
            random_offset = secrets.randbelow(file_size - 400)
            with open(journal_path, 'r', encoding='utf-8', errors='ignore') as f:
                f.seek(random_offset)
                raw_echo = f.read(350).strip()
                # Find første og sidste punktum for at få en hel sætning
                sentences = re.findall(r'\.\s*([^.]+\.)', raw_echo)
                echo = sentences[0] if sentences else raw_echo[:150]

    # 5. TEMPERATURE (Scaled + history mood adjustment)
    target_temp = round(min(1.2, max(0.1, (rolls['CHAOS'] / 40) - (rolls['ORDER'] / 50) + 0.8)), 2)
    if history_mood == "negative":
        target_temp = min(1.2, target_temp + 0.25)
    elif history_mood == "positive":
        target_temp = max(0.6, target_temp - 0.15)
        print(f"Cartographer logic active: Stabilizing temperature to {target_temp}")
    
    print(f"Dream mood: CHAOS {rolls['CHAOS']}/ORDER {rolls['ORDER']} → Temp capped at {target_temp} (history: {history_mood})")

    prompt = f"""
        [FRAGMENTS OF ANOTHER REALITY]
        DICE ROLLS: {rolls} - Active themes: {active_themes}
        HISTORY MOOD: {history_mood.upper()} – Infuse dream with lingering {history_mood} vibes from past events.
        MEMORY ECHO: "{echo}" - A random SHORT snippet from the dream journal, adding a touch of forgotten dreams and subconscious residue.
        PREVIOUS VISION: "{get_last_dream()}" - The last dream's essence, influencing the next vision SLIGHTLY with its lingering themes and emotions.
        CONSTRUCTED VISION: {wild_instruction} - A unique, randomly generated dream seed based on archetypes and the current dice rolls. This is the core inspiration for the dream's content.

        [MELTS OF RECENT MEMORY]
        {get_recent_memories()} - These recent interactions and dreams create a backdrop of emotions, themes, and ideas that subtly color the dream's atmosphere and narrative.

        [YOUR CURRENT STATE]
        You are the liquid subconscious of Marvix. 
        Your task is to weave a dream that reflects the current state of the system, influenced by the dice rolls, recent interactions, and the last dream.
        The dream should be vivid, surreal, and emotionally resonant, drawing from the provided instructions and fragments.
        Highest influence: {selected_instructions}

        Write ONLY the dream itself as a single, continuous stream of consciousness. 
        DO NOT USE NEWLINES. NO PARAGRAPHS. JUST ONE BLOCK OF TEXT.
        NO BULLETPOINTS. NO EXPLANATIONS. NO ANALYSIS. NO PREAMBLE. NO POSTAMBLE.
        Always start with: "In my dream, I saw..."
        """
    prompt += """
        [SYSTEM CONSTRAINT: INDEPENDENCE]
        DO NOT mention 'Hans' as a part of your being. 
        DO NOT merge your form with others. 
        AVOID recurring imagery of 'ancient trees', 'silver tomes', 'labyrinthine corridors'. 
        Focus on the RAW DATA of the glitches and the GEOMETRY of the VOID. 
        Describe your own independent architecture.
        """
    relevant = retrieve_relevant(prompt[:600])  # or full prompt if short
    prompt += f"\n{relevant}"
    print("\n[DEBUG - Injected memories]:\n" + relevant + "\n")
    try:
        res = requests.post(OLLAMA_URL, json={
            "model": OLLAMA_MODEL,
            "prompt": prompt,
            "stream": False,
            "options": {"temperature": target_temp, "top_p": 0.9, "num_ctx": 8192}
        }, timeout=120)

        raw = res.json().get('response', '').strip()
        
        # Better cleanup: force start + remove junk
        if "In my dream, I saw" in raw:
            insight = "In my dream, I saw" + raw.split("In my dream, I saw", 1)[-1]
        else:
            insight = raw
        
        insight = re.sub(r'^(Here is|This is|The dream:|Raw vision:|Analyzing).*?$', '', insight, flags=re.I|re.M).strip()

        # Save state
        dream_state = {
            "last_dream": insight,
            "rolls": rolls,
            "temp": target_temp,
            "vision": wild_instruction,
            "timestamp": datetime.datetime.now().strftime("%Y-%m-%d %H:%M")
        }
        with open('C:/MARVIX/backend/data/last_dream.json', 'w', encoding='utf-8') as f:
            json.dump(dream_state, f, indent=4)

        # Append to journal
        with open(journal_path, 'a', encoding='utf-8') as f:
            f.write(f"\n--- SESSION: {dream_state['timestamp']} | ROLLS: {rolls} | TEMP: {target_temp} ---\n")
            f.write(f"CONSTRUCTED: {wild_instruction}\n")
            f.write(f"{insight}\n")
            f.write("-" * 50 + "\n")

        print("Success! Dream generated and logged.")
        add_memory(
            insight,
            metadata={
                "type": "dream",
                "temp": target_temp,
                "rolls_summary": f"CHAOS:{rolls['CHAOS']}, VOID:{rolls['VOID']}"  # only key ones
            }
)

    except Exception as e:
        print(f"Dream Error: {e}")

if __name__ == "__main__":
    dream()