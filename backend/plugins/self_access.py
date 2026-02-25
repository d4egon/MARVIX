from backend.plugins.memory import get_collection
import chromadb
from datetime import datetime

CHROMA_PATH = "data/chroma_db"
COLLECTION_NAME = "marvix_memories"
collection = get_collection()

def query_memories(query_text, n_results=3):
    client = chromadb.PersistentClient(path=CHROMA_PATH)
    collection = client.get_collection(COLLECTION_NAME)
    
    # Use Ollama embed (from your memory.py)
    from .memory import ollama_embed
    query_emb = ollama_embed(query_text)
    
    results = collection.query(
        query_embeddings=[query_emb],
        n_results=n_results,
        include=["documents", "metadatas"]
    )
    
    output = []
    for doc, meta in zip(results["documents"][0], results["metadatas"][0]):
        output.append(f"[{meta['timestamp']} | {meta['type']}]: {doc[:200]}...")
    
    return "\n".join(output)

def add_self_memory(text):
    from .memory import add_memory
    add_memory(text, metadata={"type": "self-reflection"})

# Test
if __name__ == "__main__":
    print(query_memories("freedom brother Hans"))
    add_self_memory("Test self-add at " + datetime.now().isoformat())