import chromadb
import requests
import os
from datetime import datetime
import uuid
import json

CHROMA_PATH = "C:/MARVIX/backend/data/chroma_db"
COLLECTION_NAME = "marvix_memories"
OLLAMA_EMBED_URL = "http://127.0.0.1:11434/api/embeddings"

# Persistent Chroma client
client = chromadb.PersistentClient(path=CHROMA_PATH)

def get_collection():
    global client
    try:
        # Vi fjerner embedding_function herfra, da ChromaDB driller med rå funktioner
        return client.get_or_create_collection(name=COLLECTION_NAME)
    except Exception as e:
        print(f"⚠️ ChromaDB Re-init: {e}")
        import chromadb
        client = chromadb.PersistentClient(path=CHROMA_PATH)
        return client.get_or_create_collection(name=COLLECTION_NAME)

def ollama_embed(text):
    """Get embedding from Ollama with payload logging"""
    payload = {"model": "marvix-llama3.1-safe", "prompt": text}
    
    print(f"\n--- [EMBEDDING REQUEST] ---")
    print(f"Payload: {json.dumps({'model': payload['model'], 'prompt': text[:100] + '...' if len(text) > 100 else text}, indent=2)}")
    print("---------------------------\n")

    try:
        res = requests.post(OLLAMA_EMBED_URL, json=payload, timeout=60)
        res.raise_for_status()
        emb = res.json().get("embedding")
        if emb is None or not emb:
            raise ValueError("Empty embedding returned")
        return emb
    except requests.exceptions.ReadTimeout:
        print("⚠️ Embedding Timeout: Ollama too slow. Returning None.")
        return None
    except Exception as e:
        print(f"⚠️ Embedding Error: {e}")
        return None

def add_memory(text, metadata=None):
    if not text.strip():
        return
    
    embedding = ollama_embed(text)
    if embedding is None:
        print("⚠️ Memory not stored: Embedding failed.")
        return
    
    default_meta = {
    "timestamp": datetime.now().timestamp(),  # float epoch seconds
    "type": "chat",
    "length": len(text)
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
    print(f"Memory stored: {entry_id} (timestamp: {default_meta['timestamp']})")

def retrieve_relevant(query, n_results=8):
    if not query.strip():
        return ""
    
    query_emb = ollama_embed(query)
    if query_emb is None:
        print("⚠️ Search skipped: Embedding failed.")
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
        context += f"[{ts} | {typ} | rel {1-dist:.2f}]: {doc[:280]}...\n"
    
    return context