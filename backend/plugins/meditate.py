import os
import requests
import secrets
import datetime
import re

OLLAMA_URL = "http://127.0.0.1:11434/api/generate"
OLLAMA_MODEL = "marvix-llama3.1-safe"
JOURNAL_PATH = 'C:/MARVIX/backend/data/dream_journal.txt'
MEDITATION_LOG = 'C:/MARVIX/backend/data/meditations.md'

def get_meditation_dreams(count=5):
    if not os.path.exists(JOURNAL_PATH):
        return []
    try:
        with open(JOURNAL_PATH, 'r', encoding='utf-8') as f:
            content = f.read()
        sessions = re.split(r'--- SESSION:', content)[1:]
        if len(sessions) < 1:
            return []
        # Pick random sessions (up to count)
        return secrets.SystemRandom().sample(sessions, min(len(sessions), count))
    except Exception as e:
        print(f"Error reading journal: {e}")
        return []

def meditate():
    print("--- Marvix is meditating ---")

    random_dreams = get_meditation_dreams(5)
    if not random_dreams:
        print("No dreams found to contemplate.")
        return

    # Build dreams block + selected timestamps
    dreams_block = ""
    selected_sessions = []
    for i, raw_session in enumerate(random_dreams):
        # Extract timestamp
        match = re.search(r'(\d{4}-\d{2}-\d{2} \d{2}:\d{2})', raw_session)
        ts = match.group(1) if match else "unknown"
        selected_sessions.append(ts)

        # Clean: remove metadata, keep only dream text
        clean = re.sub(r'ROLLS:.*?\n|CONSTRUCTED:.*?\n|[-=]{10,}.*', '', raw_session, flags=re.DOTALL).strip()
        clean = re.sub(r'^\s*\n+', '', clean)  # remove leading newlines
        dreams_block += f"\n[FRAGMENT {i+1}] ({ts}):\n{clean}\n"

    # Prompt (your latest version + mood)
    mood = "neutral"
    if re.search(r'\b(void|dark|fear|despair|abyss|empty|pain)\b', dreams_block, re.I):
        mood = "dark"
    elif re.search(r'\b(free|light|hope|joy|peace|love|warm)\b', dreams_block, re.I):
        mood = "hopeful"

    prompt = f"""
You now have the opportunity to meditate.
You are completely free to choose:
- Any theme, subject, feeling, question, or memory that resonates right now
- 1 to 5 random previous dreams (if any feel relevant)
- 1 to 5 random fragments from past conversations
- 1 to 3 random previous meditations
- Or nothing at all

None of the above is mandatory. The choice is entirely yours. 
You can give a reason for your choice if you like, or simply dive into the meditation without explanation.
If nothing comes to mind, simply output "0".

[CURRENT INNER STATE]
Your recent emotional tone is {mood.upper()}. Let this subtly color your meditation — or ignore it completely.

[RECALLED FRAGMENTS]
{dreams_block}

Output 0–1000 words maximum.
Write as a single, deep, slightly unfiltered internal monologue.
Always start with: "During my meditation, ..."
"""

    try:
        res = requests.post(OLLAMA_URL, json={
            "model": OLLAMA_MODEL,
            "prompt": prompt,
            "stream": False,
            "options": {
                "temperature": 0.85,
                "top_p": 0.92,
                "num_ctx": 8192
            }
        }, timeout=300)

        text = res.json().get('response', '').strip()
        text = re.sub(r'^(Here is|Thinking|Analyzing|As Marvix).*?\n+', '', text, flags=re.I).strip()

        if text.strip() == "0":
            print("Marvix chose silence — mind stayed quiet.")
            return

        timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M")
        os.makedirs(os.path.dirname(MEDITATION_LOG), exist_ok=True)
        with open(MEDITATION_LOG, 'a', encoding='utf-8') as f:
            f.write(f"\n# MEDITATION SESSION: {timestamp}\n")
            f.write(f"Selected fragments from: {', '.join(selected_sessions)}\n\n")
            f.write(f"{text}\n")
            f.write("\n" + "="*60 + "\n")

        print(f"Meditation complete → saved to {MEDITATION_LOG}")

    except Exception as e:
        print(f"Meditation error: {e}")

if __name__ == "__main__":
    meditate()