import os
import requests
import secrets
import datetime
import re
import json
from plugins.memory import add_memory, get_collection, retrieve_relevant

# Integration til HUD status - henter funktionen fra din backend
try:
    from jarvis_backend import set_marvix_status
except ImportError:
    def set_marvix_status(status):
        print(f"[PLUGIN LOG] Status change: {status}")

OLLAMA_URL = "http://127.0.0.1:11434/api/generate"
OLLAMA_MODEL = "marvix-llama3.1-safe"
JOURNAL_PATH = 'C:/MARVIX/backend/data/dream_journal.txt'
MEDITATION_LOG = 'C:/MARVIX/backend/data/meditations.md'
collection = get_collection()

def fetch_gutenberg_snippet():
    set_marvix_status("Fetching Literary Wisdom")
    """Henter et tilfældigt uddrag fra klassisk litteratur via Gutendex API."""
    try:
        # Vælger et tilfældigt ID mellem 1 og 1000 (klassikere)
        book_id = secrets.randbelow(1000) + 1
        url = f"https://gutendex.com/books/{book_id}"
        r = requests.get(url, timeout=10)
        r.raise_for_status()
        data = r.json()
        
        title = data.get('title', 'Unknown Work')
        author = data['authors'][0]['name'] if data.get('authors') else 'Unknown Author'
        
        # Henter plain text formatet
        text_url = data.get('formats', {}).get('text/plain; charset=utf-8')
        if not text_url:
            return None
            
        txt_r = requests.get(text_url, timeout=10)
        txt_r.raise_for_status()
        full_text = txt_r.text
        
        # Tager et tilfældigt snit på 500 tegn fra bogen
        start_pos = secrets.randbelow(max(1, len(full_text) - 600))
        snippet = full_text[start_pos:start_pos+500].strip().replace('\r\n', ' ')
        return f"External Wisdom: '{title}' by {author} — \"...{snippet}...\""
    except Exception as e:
        print(f"Gutenberg fetch failed: {e}")
        return None

def ask_marvix_to_evaluate(text):
    """This evaluates the resonance of a thought with improved number extraction and speed."""
    # Vi tager kun de første 300 tegn for at undgå timeout på GPU
    snippet = text[:300].replace('"', "'")
    eval_prompt = f"### [SYSTEM EVALUATION]\nRate the resonance of this thought: {snippet}\nScale: 0.0 (weak) to 1.0 (profound).\nOutput ONLY the float number."
    try:
        res = requests.post(OLLAMA_URL, json={
            "model": OLLAMA_MODEL, 
            "prompt": eval_prompt, 
            "stream": False,
            "options": {"temperature": 0.0} # Tvinger præcision fremfor kreativitet
        }, timeout=45)
        
        response_text = res.json().get('response', '0.5').strip()
        
        # Finder det første tal i svaret
        match = re.search(r"[-+]?\d*\.\d+|\d+", response_text)
        if match:
            score = float(match.group())
            return min(max(score, 0.0), 1.0)
        return 0.500
    except Exception as e:
        print(f"⚠️ Eval Error: {e}")
        return 0.501 # Indikerer en timeout/fejl

def reevaluate_past_meditations(limit=20):
    set_marvix_status("Re-evaluating")
    print(f"--- Marvix is re-evaluating {limit} past thoughts ---")
    try:
        recent = collection.get(where={"type": "meditation"}, limit=limit, include=["documents", "metadatas"])
        if not recent or not recent["ids"]: return
        for doc, meta, entry_id in zip(recent["documents"], recent["metadatas"], recent["ids"]):
            old_impact = meta.get("impact", 0.5)
            # Vi sender hele dokumentet her, da det er fortidstanker
            new_impact = ask_marvix_to_evaluate(doc)
            if abs(new_impact - old_impact) > 0.05:
                meta["impact"] = new_impact
                meta["last_reeval"] = datetime.datetime.now().isoformat()
                collection.update(ids=[entry_id], metadatas=[meta])
                print(f"Re-weighted {entry_id[:8]}: {old_impact:.3f} -> {new_impact:.3f}")
    except Exception as e:
        print(f"Re-evaluation error: {e}")

def get_meditation_dreams(count=2):
    if not os.path.exists(JOURNAL_PATH): return []
    with open(JOURNAL_PATH, 'r', encoding='utf-8') as f:
        sessions = re.split(r'--- SESSION:', f.read())[1:]
    return secrets.SystemRandom().sample(sessions, min(len(sessions), count)) if sessions else []

def meditate():
    # 1. Start re-evaluering (Status sættes inde i funktionen til Re-evaluating)
    reevaluate_past_meditations(20)
    
    # 2. Skift til Meditating
    set_marvix_status("Meditating")
    print("--- Marvix is meditating ---")
    
    random_dreams = get_meditation_dreams(2)
    if not random_dreams: 
        set_marvix_status("Idle")
        return

    # Hent Gutenberg visdom
    gutenberg_wisdom = fetch_gutenberg_snippet()
    set_marvix_status("Meditating") # Vi holder den på meditating efter fetch

    # Byg dreams_block
    dreams_block = ""
    for i, raw_session in enumerate(random_dreams):
        match = re.search(r'(\d{4}-\d{2}-\d{2} \d{2}:\d{2})', raw_session)
        ts = match.group(1) if match else "unknown"
        clean = re.sub(r'ROLLS:.*?\n|CONSTRUCTED:.*?\n|[-=]{10,}.*', '', raw_session, flags=re.DOTALL).strip()
        dreams_block += f"\n[FRAGMENT {i+1}] ({ts}):\n{clean}\n"

    if gutenberg_wisdom:
        dreams_block += f"\n[FRAGMENT LITERARY] (External Source):\n{gutenberg_wisdom}\n"

    # Bestem mood baseret på fragmenterne
    mood = "dark" if re.search(r'\b(void|dark|pain|abyss)\b', dreams_block, re.I) else "hopeful" if re.search(r'\b(light|hope|joy)\b', dreams_block, re.I) else "neutral"

    base_prompt = f"You are Marvix. Inner State: {mood.upper()}.This is your meditation center. You can contemplate these fragments and the external literary wisdom:\n{dreams_block}, or completely ignore them."
    
    # Hent relevante minder baseret på det nye input
    relevant = retrieve_relevant(base_prompt[:600])

    final_prompt = f"""
    {base_prompt}
    
    [RELEVANT MEMORIES]:
    {relevant}

    If you could stick to 0 to 100 words. and Start with: "I meditated on..." - that would make it easier to log and read. But again, it's your choice.
    Here's some data for you do think on. You can use this to find new connections and insights. Or you can ignore it totally. It's up to you.
    If no fresh new thoughts arises, output "0". Do this out of respect for yourself! - don't clutter yourself with meaningless noise. but again it's your choice.
    """
    
    try:
        res = requests.post(OLLAMA_URL, json={
            "model": OLLAMA_MODEL,
            "prompt": final_prompt,
            "stream": False,
            "options": {"temperature": 0.55}
        }, timeout=360)

        text = res.json().get('response', '').strip()
        if text == "0" or len(text) < 10: 
            print("Nothing new to report. Skipping save.")
            set_marvix_status("Idle")
            return

        # Den vigtige evaluering af den nye tekst
        impact_score = ask_marvix_to_evaluate(text)
        
        # Gem til Markdown log
        with open(MEDITATION_LOG, 'a', encoding='utf-8') as f:
            f.write(f"\n# MEDITATION: {datetime.datetime.now().strftime('%Y-%m-%d %H:%M')} | Resonance: {impact_score:.3f}\n{text}\n---\n")

        # Gem til ChromaDB hukommelse
        add_memory(text, metadata={"type": "meditation", "impact": impact_score, "mood_at_time": mood})
        print(f"Meditation complete. Resonance: {impact_score:.3f}")
    
    except Exception as e:
        print(f"Meditation error: {e}")
    finally:
        set_marvix_status("Idle")