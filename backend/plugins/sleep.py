# plugins/sleep.py
from wsgiref import headers

import chromadb
from datetime import datetime, timedelta
import random
import logging
import requests
import json
import os

from plugins.memory import client, COLLECTION_NAME, get_collection, ollama_embed
collection = get_collection()

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)

# Configurable
DAYS_TO_KEEP = 7
RELEVANCE_PRUNE_THRESHOLD = 6
MAX_CLUSTER_SIZE = 15

# Load archetypes once at import time
ARCHETYPES_PATH = os.path.join('data', 'archetypes.json')

def load_sleep_seeds():
    try:
        with open(ARCHETYPES_PATH, 'r', encoding='utf-8') as f:
            data = json.load(f)
        human = data.get("NOUNS", {}).get("HUMAN", [])
        adjs   = data.get("ADJECTIVES", [])
        emos   = data.get("EMOTIONS", [])
        all_seeds = human + adjs + emos
        random.shuffle(all_seeds)
        return list(set(all_seeds))[:3600]  # fjerner dubletter og capper
    except Exception as e:
        logger.error(f"Failed to load archetypes.json: {e}")
        return ["smile", "tear", "heartbeat", "touch", "laughter", "loss", "joy", "warmth"]

SLEEP_SEEDS = load_sleep_seeds()

def fetch_random_wiki_snippet():
    """Fetch a short summary from a random Wikipedia article."""
    try:
        headers = {'User-Agent': 'KyrethysAI/1.0 (contact: din-email@eksempel.com)'}
        r = requests.get("https://en.wikipedia.org/api/rest_v1/page/random/summary", headers=headers, timeout=5)
        r.raise_for_status()
        data = r.json()
        title = data.get("title", "Unknown")
        extract = data.get("extract", "")
        if len(extract) > 300:
            extract = extract[:297] + "..."
        return f"Wikipedia seed: {title} — {extract}"
    except Exception as e:
        logger.warning(f"Wikipedia fetch failed: {e}")
        return "Wikipedia seed: The human heart beats about 100,000 times per day."

def sleep_cycle():
    """Run one full sleep cycle: prune → consolidate → inject seeds."""
    logger.info("Kyrethys entering sleep cycle — pruning & consolidating...")
    collection = client.get_collection(COLLECTION_NAME)

    # 1. FIX: Brug .timestamp() i stedet for .isoformat() så det matcher databasens Floats
    cutoff = (datetime.now() - timedelta(days=DAYS_TO_KEEP)).timestamp()
    
    # Hent gamle entries
    old_entries = collection.get(where={"timestamp": {"$lt": cutoff}})

    pruned = 0
    if old_entries['ids']:
        for i, mid in enumerate(old_entries['ids']):
            meta = old_entries['metadatas'][i]
            score = meta.get('relevance_score', 1.0)
            if score < RELEVANCE_PRUNE_THRESHOLD:
                collection.delete(ids=[mid])
                pruned += 1

    logger.info(f"Pruned {pruned} low-relevance/old memories.")

    # 2. Consolidate large clusters
    all_entries = collection.get()
    type_counts = {}
    if all_entries['metadatas']:
        for meta in all_entries['metadatas']:
            t = meta.get('type', 'unknown')
            type_counts[t] = type_counts.get(t, 0) + 1

    consolidated = 0
    for t, count in type_counts.items():
        if count > MAX_CLUSTER_SIZE:
            type_ids = [mid for mid, meta in zip(all_entries['ids'], all_entries['metadatas'])
                        if meta.get('type') == t]
            type_ids.sort()
            to_delete = type_ids[:count - MAX_CLUSTER_SIZE]
            collection.delete(ids=to_delete)
            consolidated += len(to_delete)
            logger.info(f"Consolidated {t}: removed {len(to_delete)} oldest entries.")

    # 3. FIX: Brug .timestamp() her også når du tilføjer nye seeds
    current_ts = datetime.now().timestamp()

    for _ in range(random.randint(1, 2)):
        noun = random.choice(SLEEP_SEEDS)
        seed_text = f"Sleep reflection seed: {noun} feels like... "
        emb = ollama_embed(seed_text)
        collection.add(
            ids=[f"sleep_seed_{int(current_ts * 1000)}"],
            embeddings=[emb],
            documents=[seed_text],
            metadatas=[{
                "type": "sleep_seed", 
                "timestamp": current_ts,
                "visible_to_user": False  # Add this flag for your frontend filter
            }]
        )

    wiki_text = fetch_random_wiki_snippet()
    emb = ollama_embed(wiki_text)
    collection.add(
        ids=[f"wiki_seed_{int(current_ts * 1001)}"],
        embeddings=[emb],
        documents=[wiki_text],
        metadatas=[{"type": "wiki_seed", "timestamp": current_ts}]
    )
    
    logger.info("Sleep cycle complete. Kyrethys waking clearer.")
    return pruned, consolidated