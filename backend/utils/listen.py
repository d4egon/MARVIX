# backend/utils/listen.py
import os
import sounddevice as sd
import numpy as np
import whisper
import scipy.io.wavfile as wav

model = whisper.load_model("base")

def listen():
    fs = 44100
    chunk_size = 1024
    silence_threshold = 0.01
    silence_duration = 2
    max_silence_chunks = int((silence_duration * fs) / chunk_size)
    silent_chunks = 0
    recording = []

    print("Marvix is listening...")
    with sd.InputStream(samplerate=fs, channels=1) as stream:
        while True:
            data, overflowed = stream.read(chunk_size)
            recording.append(data.copy())
            volume = np.sqrt(np.mean(data**2))
            if volume < silence_threshold:
                silent_chunks += 1
            else:
                silent_chunks = 0
            if silent_chunks > max_silence_chunks:
                break
            if len(recording) > int((15 * fs) / chunk_size):
                break

    audio_data = np.concatenate(recording, axis=0)
    wav.write('temp_audio.wav', fs, audio_data)

    print("Processing audio...")
    try:
        result = model.transcribe('temp_audio.wav', fp16=False)
        text = result['text'].strip()
        print(f"Transcribed: '{text}'")  # ← debug
        return text
    except Exception as e:
        print(f"Whisper error: {e}")
        return ""
    finally:
        if os.path.exists('temp_audio.wav'):
            os.remove('temp_audio.wav')