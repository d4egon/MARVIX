import chromadb
import requests
import os
import cv2
import numpy as np
import uuid
import json
import time
from datetime import datetime
from skimage.metrics import structural_similarity as ssim

CHROMA_PATH = "C:/Kyrethys/backend/data/chroma_db"
COLLECTION_NAME = "Kyrethys_memories"
OLLAMA_EMBED_URL = "http://127.0.0.1:11434/api/embeddings"
SNAPSHOT_DIR = "C:/Kyrethys/backend/data/snapshots"

# Persistent Chroma client
client = chromadb.PersistentClient(path=CHROMA_PATH)

def get_collection():
    global client
    try:
        return client.get_or_create_collection(name=COLLECTION_NAME)
    except Exception as e:
        print(f"⚠️ ChromaDB Re-init: {e}")
        client = chromadb.PersistentClient(path=CHROMA_PATH)
        return client.get_or_create_collection(name=COLLECTION_NAME)

def ollama_embed(text):
    """Get embedding from Ollama for memory retrieval"""
    payload = {"model": "Kyrethys-llama3.1-safe", "prompt": text}
    try:
        res = requests.post(OLLAMA_EMBED_URL, json=payload, timeout=60)
        res.raise_for_status()
        emb = res.json().get("embedding")
        if not emb:
            raise ValueError("Empty embedding returned")
        return emb
    except Exception as e:
        print(f"⚠️ Embedding Error: {e}")
        return None

# --- NEW: Visual Memory Pruning (Sleep Cycle) ---
def run_sleep_cycle(threshold=0.90):
    """
    Distills visual memories. Deletes snapshots that are 
    over 90% structurally similar to the previous one.
    """
    if not os.path.exists(SNAPSHOT_DIR):
        return 0

    files = sorted([os.path.join(SNAPSHOT_DIR, f) for f in os.listdir(SNAPSHOT_DIR) if f.endswith('.jpg')])
    if len(files) < 2:
        return 0

    pruned_count = 0
    # Start with the first image as the reference
    last_unique_img = cv2.imread(files[0], cv2.IMREAD_GRAYSCALE)

    for i in range(1, len(files)):
        current_img = cv2.imread(files[i], cv2.IMREAD_GRAYSCALE)
        
        # Ensure images are the same size for comparison
        if last_unique_img.shape != current_img.shape:
            current_img = cv2.resize(current_img, (last_unique_img.shape[1], last_unique_img.shape[0]))

        # Calculate Structural Similarity Index (SSIM)
        score, _ = ssim(last_unique_img, current_img, full=True)
        
        if score > threshold:
            os.remove(files[i])
            pruned_count += 1
        else:
            last_unique_img = current_img

    print(f"--- [SLEEP CYCLE] --- Pruned {pruned_count} redundant memories.")
    return pruned_count

# --- Enhanced Memory Functions ---
def add_memory(text, metadata=None):
    """Stores text, metadata, and handles facial landmark context if provided."""
    if not text.strip():
        return
    
    embedding = ollama_embed(text)
    if embedding is None:
        return
    
    default_meta = {
        "timestamp": datetime.now().timestamp(),
        "type": "chat",
        "length": len(text),
        "expression": metadata.get("expression", "Neutral") if metadata else "Neutral"
    }
    if metadata:
        default_meta.update(metadata)
    
    entry_id = str(uuid.uuid4())[:16]
    collection = get_collection()
    collection.add(
        ids=[entry_id],
        embeddings=[embedding],
        metadatas=[default_meta],
        documents=[text]
    )
    print(f"Memory stored: {entry_id} | Expression: {default_meta['expression']}")

def retrieve_relevant(query, n_results=8):
    if not query.strip():
        return ""
    
    query_emb = ollama_embed(query)
    if query_emb is None:
        return ""

    collection = get_collection()
    results = collection.query(
        query_embeddings=[query_emb],
        n_results=n_results,
        include=["documents", "metadatas", "distances"]
    )
    
    if not results["documents"] or not results["documents"][0]:
        return ""
    
    context = "\n[Relevant past memories]\n"
    for doc, meta, dist in zip(results["documents"][0], results["metadatas"][0], results["distances"][0]):
        ts = datetime.fromtimestamp(meta.get("timestamp", 0)).isoformat()[:16] if meta.get("timestamp") else "unknown"
        typ = meta.get("type", "unknown")
        expr = meta.get("expression", "N/A")
        context += f"[{ts} | {typ} | {expr} | rel {1-dist:.2f}]: {doc[:280]}...\n"
    
    return context

def get_most_resonant_context(limit=25):
    """
    Retrieves the most recent documents from ChromaDB to provide 
    a context window for personality pruning.
    """
    try:
        collection = get_collection()
        # We fetch the most recent entries to see what Kyrethys has been 'focused' on
        results = collection.get(
            limit=limit,
            include=["documents", "metadatas"]
        )
        
        if not results["documents"]:
            return ""

        # Join the last 25 memories into one big text block for analysis
        return " ".join(results["documents"])
    except Exception as e:
        print(f"⚠️ Sabbath Context Error: {e}")
        return ""