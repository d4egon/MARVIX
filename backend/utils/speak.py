# backend/utils/speak.py
import asyncio
import edge_tts
import os
import time
from pygame import mixer

last_spoken_text = ""
last_spoken_time = 0

PRIMARY_VOICE = "en-US-GuyNeural"  # Reliable default
FALLBACK_VOICES = ["en-GB-SoniaNeural", "en-US-AriaNeural", "en-GB-BrianNeural"]

def speak(text):
    global last_spoken_text, last_spoken_time

    if not text or not text.strip():
        return

    now = time.time()
    if text == last_spoken_text and now - last_spoken_time < 3:  # 3-second debounce
        print("Skipping duplicate speak:", text[:40])
        return

    last_spoken_text = text
    last_spoken_time = now

    print(f"edge-tts speaking: {text[:60]}...")
    # ... rest of your async _speak_async code unchanged ...

    async def _speak_async(voice):
        try:
            communicate = edge_tts.Communicate(text, voice)
            await communicate.save("marvix_temp.mp3")

            # Silent playback with pygame
            mixer.init()
            mixer.music.load("marvix_temp.mp3")
            mixer.music.play()
            while mixer.music.get_busy():
                time.sleep(0.1)
            mixer.quit()

            return True
        except Exception as e:
            print(f"Voice {voice} failed: {e}")
            return False

    async def try_voices():
        if await _speak_async(PRIMARY_VOICE):
            return
        for fallback in FALLBACK_VOICES:
            if await _speak_async(fallback):
                print(f"Fallback success: {fallback}")
                return
        print("All voices failed — check ffmpeg/network")

    asyncio.run(try_voices())

   # Cleanup
   # time.sleep(1)
   # if os.path.exists("marvix_temp.mp3"):
   #     try:
   #         os.remove("marvix_temp.mp3")
   #     except:
   #         pass 