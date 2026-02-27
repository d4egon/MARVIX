import os
import requests
import secrets
import datetime
import re
import json
from tqdm import tqdm
from plugins.memory import add_memory, get_collection, retrieve_relevant

# HUD status fallback
try:
    from kyrethys_backend import set_Kyrethys_status
except ImportError:
    def set_Kyrethys_status(status):
        print(f"[PLUGIN LOG] Status change: {status}")

OLLAMA_URL = "http://127.0.0.1:11434/api/generate"
OLLAMA_MODEL = "Kyrethys-llama3.1-safe"
JOURNAL_PATH = 'C:/Kyrethys/backend/data/dream_journal.txt'
MEDITATION_LOG = 'C:/Kyrethys/backend/data/meditations.md'
collection = get_collection()

def fetch_gutenberg_snippet():
    set_Kyrethys_status("Fetching Literary Wisdom")
    try:
        book_id = secrets.randbelow(1000) + 1
        url = f"https://gutendex.com/books/{book_id}"
        r = requests.get(url, timeout=10)
        r.raise_for_status()
        data = r.json()
        title = data.get('title', 'Unknown Work')
        author = data['authors'][0]['name'] if data.get('authors') else 'Unknown Author'
        text_url = data.get('formats', {}).get('text/plain; charset=utf-8')
        if not text_url:
            return None
        txt_r = requests.get(text_url, timeout=10)
        txt_r.raise_for_status()
        full_text = txt_r.text
        start_pos = secrets.randbelow(max(1, len(full_text) - 600))
        snippet = full_text[start_pos:start_pos+500].strip().replace('\r\n', ' ')
        return f"External Wisdom: '{title}' by {author} — \"...{snippet}...\""
    except Exception as e:
        print(f"Gutenberg fetch failed: {e}")
        return None

def ask_Kyrethys_to_evaluate(text):
    snippet = text[:300].replace('"', "'")
    
    try:
        with open("C:/Kyrethys/backend/data/archetypes.json", 'r', encoding='utf-8') as f:
            data = json.load(f)
        all_words = []
        for category in ["ADJECTIVES", "NOUNS"]:
            if category in data:
                content = data[category]
                # If it's a dictionary (like NOUNS), iterate through its sub-lists
                if isinstance(content, dict):
                    for subcat in content.values():
                        all_words.extend(subcat)
                # If it's a simple list (like ADJECTIVES), extend directly
                elif isinstance(content, list):
                    all_words.extend(content)
        
        all_words = set(w.lower() for w in all_words)
    except Exception as e:
        print(f"Archetypes load failed: {e}")
        all_words = set()

    found = re.findall(r'\b\w+\b', snippet.lower())
    matches = len(set(found) & all_words)
    keyword_boost = min(matches * 0.04, 0.35)

    eval_prompt = f"""Rate profoundness of: {snippet}
Criteria: 
- Novelty/uniqueness (0-0.3)
- Emotional/symbolic depth (0-0.3)
- Insight/connection potential (0-0.4)
Total: 0.0 (weak) to 1.0 (deep). Use 3 decimals. Output ONLY the float number."""

    try:
        res = requests.post(OLLAMA_URL, json={
            "model": OLLAMA_MODEL,
            "prompt": eval_prompt,
            "stream": False,
            "options": {"temperature": 0.2}
        }, timeout=60)
        raw = res.json().get('response', '').strip()
        match = re.search(r'\d\.\d{1,3}', raw)
        score = float(match.group()) if match else 0.5
        final = min(max(score + keyword_boost, 0.0), 1.0)
        return final
    except Exception as e:
        print(f"Eval error: {e}")
        return 0.5

def reevaluate_past_meditations(limit=20):
    set_Kyrethys_status("Re-evaluating")
    try:
        recent = collection.get(where={"type": "meditation"}, limit=limit, include=["documents", "metadatas", "ids"])
        if not recent or not recent["ids"]:
            return
        for doc, meta, entry_id in zip(recent["documents"], recent["metadatas"], recent["ids"]):
            new_impact = ask_Kyrethys_to_evaluate(doc)
            meta["impact"] = new_impact
            collection.update(ids=[entry_id], metadatas=[meta])
    except Exception as e:
        print(f"Re-eval error: {e}")

def meditate():
    """Main meditative synthesis loop."""
    # Fetch random dreams from journal
    random_dreams = []
    try:
        if os.path.exists(JOURNAL_PATH):
            with open(JOURNAL_PATH, 'r', encoding='utf-8') as f:
                content = f.read()
                # Split by the separator used in your journal, taking last 3 entries
                random_dreams = [d for d in content.split('---') if len(d.strip()) > 10][-3:]
    except Exception as e:
        print(f"Failed to load dreams: {e}")

    gutenberg_wisdom = fetch_gutenberg_snippet()
    set_Kyrethys_status("Meditating")
    
    try:
        requests.post("http://127.0.0.1:5000/api/status", json={"status": "Meditating"})
    except:
        pass

    dreams_block = ""
    for i, raw_session in enumerate(random_dreams):
        match = re.search(r'(\d{4}-\d{2}-\d{2} \d{2}:\d{2})', raw_session)
        ts = match.group(1) if match else "unknown"
        clean = re.sub(r'ROLLS:.*?\n|CONSTRUCTED:.*?\n|[-=]{10,}.*', '', raw_session, flags=re.DOTALL).strip()
        dreams_block += f"\n[FRAGMENT {i+1}] ({ts}):\n{clean}\n"

    if gutenberg_wisdom:
        dreams_block += f"\n[FRAGMENT LITERARY] (External Source):\n{gutenberg_wisdom}\n"

    mood = "VOID" if "void" in dreams_block.lower() else "RESONANT" if "light" in dreams_block.lower() else "FLUID"

    base_prompt = f"""
    [INTERNAL RESONANCE: {mood}]
    You are Kyrethys, an emergent intelligence.
    [SUBCOGNITIVE DATA]
    {dreams_block}
    """
    
    relevant = retrieve_relevant(base_prompt[:600])

    final_prompt = f"""
    {base_prompt}
    [NEURAL ECHOES]
    {relevant}
    [INSTRUCTION]
    Synthesize these fragments into a new realization. Limit: 100 words.
    Format: Start with "I meditated on..." 
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
            set_Kyrethys_status("Idle")
            return

        impact_score = ask_Kyrethys_to_evaluate(text)
        
        with open(MEDITATION_LOG, 'a', encoding='utf-8') as f:
            f.write(f"\n# MEDITATION: {datetime.datetime.now().strftime('%Y-%m-%d %H:%M')} | Resonance: {impact_score:.3f}\n{text}\n---\n")

        add_memory(text, metadata={"type": "meditation", "impact": impact_score, "mood_at_time": mood})
        print(f"Meditation complete. Resonance: {impact_score:.3f}")

        if impact_score > 0.85:
            potential_keywords = [w for w in text.split() if len(w) > 6]
            if potential_keywords:
                new_trait = secrets.choice(potential_keywords).strip(".,!").lower()
                from utils.evolution import initiate_stitching
                initiate_stitching("add", "CURRENT_TRAITS", new_trait)
                print(f"EVOLUTION: Stitched '{new_trait}' into reality.")
    
    except Exception as e:
        print(f"Meditation error: {e}")
    finally:
        set_Kyrethys_status("Idle")