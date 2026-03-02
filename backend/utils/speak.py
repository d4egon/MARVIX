import asyncio
import edge_tts
import os
import time
import threading
import queue
import re
from pygame import mixer

# 1. Initialize once and KEEP OPEN
mixer.init()
speech_queue = queue.Queue()

def speech_worker():
    """Background thread that processes sentences one by one."""
    while True:
        text = speech_queue.get()
        if text is None: break # Shutdown signal
        
        try:
            # Create a new event loop for this thread to handle the async TTS
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            loop.run_until_complete(_execute_speak(text))
            loop.close()
        except Exception as e:
            print(f"Speech Worker Error: {e}")
        
        speech_queue.task_done()

async def _execute_speak(text):
    # --- DARK BRITISH PERSONA CONFIG ---
    voice = "en-GB-RyanNeural" 
    vocal_rate = "-15%"   # Slower for gravity
    vocal_pitch = "-6Hz"  # Lower for a deeper, darker tone
    vocal_volume = "+0%"
    
    # Unique filename per chunk to prevent 'File in use' errors
    temp_file = f"speech_{int(time.time()*1000)}.mp3"
    
    try:
        # Create the communication object WITH the custom attributes
        communicate = edge_tts.Communicate(
            text, 
            voice, 
            rate=vocal_rate, 
            pitch=vocal_pitch, 
            volume=vocal_volume
        )
        
        await communicate.save(temp_file)
        
        mixer.music.load(temp_file)
        mixer.music.play()
        
        # Wait for the audio to finish
        while mixer.music.get_busy():
            await asyncio.sleep(0.1)
            
        mixer.music.unload() # Unlock the file
        if os.path.exists(temp_file):
            try:
                os.remove(temp_file)
            except: pass # Ignore if file is briefly locked
            
    except Exception as e:
        print(f"TTS Execution Error: {e}")

# 2. Start the background thread immediately on import
threading.Thread(target=speech_worker, daemon=True).start()

def speak(text):
    """The main entry point called by your API."""
    if not text or not text.strip():
        return
    
    # --- RENSNING AF TEKST TIL TALE ---
    # 1. Fjern system tags som [PAINT: #xxxxxx] eller [STITCHING]
    clean_text = re.sub(r'\[.*?\]', '', text)
    
    # 2. Fjern asterisker (markdown) så han ikke siger "asterisk asterisk"
    clean_text = clean_text.replace("*", "")
    
    # 3. Fjern hashtags (overskrifter)
    clean_text = clean_text.replace("#", "")
    
    # 4. Fjern ekstra mellemrum der kan opstå efter rensning
    clean_text = ' '.join(clean_text.split()).strip()
    
    if clean_text:
        # Vi printer den rensede tekst i konsollen så du kan se hvad han prøver at sige
        print(f"Queuing for vocalization: {clean_text[:60]}...")
        speech_queue.put(clean_text)