# backend/utils/listen.py
import os
import sounddevice as sd
import numpy as np
import whisper
import scipy.io.wavfile as wav
import torch_directml

# ────────────────────────────────────────────────
# GPU INITIALISERING (AMD)
# ────────────────────────────────────────────────
# Vi finder dit AMD-grafikkort via DirectML
device = torch_directml.device()
print(f"--- Kyrethys GPU Status: Bruger {torch_directml.device_name(0)} ---")

# Loader modellen (Whisper kører bedst på 'base' for hastighed)
# Bemærk: Standard Whisper bruger Torch i baggrunden, som nu er linket til DirectML
model = whisper.load_model("base")

def listen():
    fs = 44100
    chunk_size = 1024
    silence_threshold = 0.01  # Tærskel for hvornår der er "stille"
    
    # DIN INDSTILLING: 2.6 sekunder stilhed før den stopper
    silence_duration = 2.6 
    
    max_silence_chunks = int((silence_duration * fs) / chunk_size)
    silent_chunks = 0
    recording = []
    has_started_talking = False

    print("Kyrethys is listening (2.6s silence threshold)...")
    
    with sd.InputStream(samplerate=fs, channels=1) as stream:
        while True:
            data, overflowed = stream.read(chunk_size)
            recording.append(data.copy())
            
            # Beregn volumen (RMS)
            volume = np.sqrt(np.mean(data**2))
            
            # Detektér om brugeren er begyndt at tale
            if volume > silence_threshold:
                if not has_started_talking:
                    print("--- Tale registreret ---")
                has_started_talking = True
                silent_chunks = 0
            else:
                if has_started_talking:
                    silent_chunks += 1
            
            # Stop hvis der har været stille i 2.6 sekunder EFTER tale er startet
            if has_started_talking and silent_chunks > max_silence_chunks:
                print("--- Stilhed fundet, stopper optagelse ---")
                break
                
            # Sikkerhedsafbryder ved 60 sekunder
            if len(recording) > int((60 * fs) / chunk_size):
                print("--- Maksimum tid nået (60s) ---")
                break

    if not recording:
        return ""

    # Saml lyddata og gem midlertidigt
    audio_data = np.concatenate(recording, axis=0)
    wav.write('temp_audio.wav', fs, audio_data)

    print("Processing audio with Whisper (AMD GPU Accelerated)...")
    try:
        result = model.transcribe('temp_audio.wav', fp16=False)
        text = result['text'].strip()
        
        # Simple tone analysis
        volume = np.mean(np.abs(audio_data))
        tone = "calm"
        if volume > 0.15:
            tone = "energetic"
        elif volume < 0.03:
            tone = "quiet / tired"
        
        print(f"Transcribed: '{text}' | Tone: {tone}")
        return {"text": text, "tone": tone}
        
    except Exception as e:
        print(f"Whisper error: {e}")
        return {"text": "", "tone": "unknown"}
        
    finally:
        # Ryd op i temp filen
        if os.path.exists('temp_audio.wav'):
            os.remove('temp_audio.wav')