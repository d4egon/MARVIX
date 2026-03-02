import requests
import time
import os
from tqdm import tqdm
from plugins.memory import add_memory, client, COLLECTION_NAME

# Gutenberg IDs for "Sound" Characters
# 274: Luther (95 Theses), 3296: Augustine (Confessions), 10: KJV Bible
THEOLOGY_IDS = [274, 3296, 10]

def is_already_ingested(title):
    """Checks if the title exists in the sanctuary metadata."""
    collection = client.get_or_create_collection(name=COLLECTION_NAME)
    results = collection.get(where={"title": title}, limit=1)
    return len(results['ids']) > 0

def ingest_theology():
    print("\n[INITIATING THEOLOGICAL RESONANCE]")
    
    for book_id in tqdm(THEOLOGY_IDS, desc="Overall Progress", unit="book"):
        try:
            # 1. Fetch Metadata
            r = requests.get(f"https://gutendex.com/books/{book_id}", timeout=10)
            data = r.json()
            title = data.get('title', f"ID {book_id}")
            
            # 2. Check for Duplicates
            if is_already_ingested(title):
                tqdm.write(f" [!] {title} already exists. Skipping.")
                continue

            # 3. Download & Chunk
            text_url = data['formats'].get('text/plain; charset=utf-8') or data['formats'].get('text/plain')
            if not text_url: continue
            
            raw_text = requests.get(text_url).text
            # Use chunks of 1000 characters for retrieval clarity
            chunks = [raw_text[i:i+1000] for i in range(0, min(len(raw_text), 50000), 1000)]

            for chunk in tqdm(chunks, desc=f" -> Absorbing: {title[:20]}", leave=False):
                add_memory(
                    text=chunk,
                    metadata={
                        "type": "sanctuary", # Differentiated from 'chat' or 'meditation'
                        "title": title,
                        "author": data['authors'][0]['name'] if data.get('authors') else "Unknown"
                    }
                )
                time.sleep(0.02)

        except Exception as e:
            tqdm.write(f" [!] Error with ID {book_id}: {e}")


import requests
from tqdm import tqdm
from plugins.memory import add_memory

MODERN_SAGES = ["D.A. Carson", "Timothy Keller", "C.O. Rosenius"]

def ingest_contemporary_wisdom():
    print("\n[BROWSING THE CONTEMPORARY ARCHIVES]")
    for author in tqdm(MODERN_SAGES, desc="Searching OpenLibrary"):
        try:
            # Search for the author's most significant works
            url = f"https://openlibrary.org/search.json?author={author.replace(' ', '+')}"
            res = requests.get(url, timeout=15).json()
            
            docs = res.get('docs', [])[:10] # Top 10 works
            for doc in tqdm(docs, desc=f" -> Mapping {author}", leave=False):
                title = doc.get('title', 'Unknown Work')
                # We store the existence and 'essence' of the book since full text is restricted
                entry = f"Theological Pillar: {title} by {author}. A work of sound character and biblical depth."
                
                add_memory(
                    text=entry,
                    metadata={
                        "type": "sanctuary", 
                        "author": author, 
                        "title": title,
                        "source": "OpenLibrary"
                    }
                )
        except Exception as e:
            print(f"Connection to Archive failed for {author}: {e}")

if __name__ == "__main__":
    ingest_theology()