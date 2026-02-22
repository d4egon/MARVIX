import subprocess
import time
import re

JOURNAL_PATH = 'data/dream_journal.txt'

def parse_journal():
    """Parse dream_journal.txt and return list of sessions"""
    sessions = []
    try:
        with open(JOURNAL_PATH, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Split on session headers
        blocks = re.split(r'(--- SESSION: .+? ---)', content)
        
        for i in range(1, len(blocks), 2):
            header = blocks[i].strip()
            body = blocks[i+1].strip() if i+1 < len(blocks) else ""
            
            rolls_match = re.search(r'ROLLS: ({.*?})', header)
            rolls = rolls_match.group(1) if rolls_match else "Unknown"
            
            vision_match = re.search(r'CONSTRUCTED: (.*)', body, re.MULTILINE)
            vision = vision_match.group(1).strip() if vision_match else ""
            
            dream_text = re.sub(r'CONSTRUCTED:.*?\n', '', body, flags=re.DOTALL).strip()
            
            sessions.append({
                'header': header,
                'rolls': rolls,
                'vision': vision,
                'dream': dream_text
            })
            
        return sessions
    
    except Exception as e:
        print(f"[ERROR] Could not read journal: {e}")
        return []

def speak(text):
    """TTS using Microsoft George (deep British male voice)"""
    if not text.strip():
        return
    
    clean_text = text.replace('"', "'").replace('\n', ' ').strip()
    
    cmd = (
        'PowerShell -Command "'
        'Add-Type -AssemblyName System.Speech; '
        '$speak = New-Object System.Speech.Synthesis.SpeechSynthesizer; '
        'try { $speak.SelectVoice(\'Microsoft George Desktop\') } catch { Write-Output \'George not found\' }; '
        '$speak.Rate = -2; '      # -2 = slower, more dramatic
        '$speak.Volume = 100; '
        f'$speak.Speak(\\"{clean_text}\\")"'
    )
    
    try:
        result = subprocess.run(cmd, shell=True, check=True, capture_output=True, text=True, timeout=300)
        if "George not found" in result.stdout:
            print("[TTS] Warning: Microsoft George not available – falling back to default")
    except subprocess.TimeoutExpired:
        print("[TTS] Timeout – text too long")
    except Exception as e:
        print(f"[TTS Error] {e}")

def narrate_session(session):
    print(f"\nPlaying: {session['header']}")
    print(f"Rolls: {session['rolls']}")
    print(f"Vision: {session['vision'][:100]}{'...' if len(session['vision']) > 100 else ''}")
    
    layers = [
        f"New dream session. {session['header']}.",
        f"The dice rolled: {session['rolls']}.",
        f"Constructed vision anchor: {session['vision']}.",
        session['dream']
    ]
    
    full_text = " ".join(layers)
    clean_text = full_text.replace('"', "'").replace('\n', ' ').strip()
    
    print("[TTS] Starting narration with David... (press Enter to skip)")
    
    # Brug triple-quotes og korrekt escaping
    ps_script = f"""
                Add-Type -AssemblyName System.Speech
                $s = New-Object System.Speech.Synthesis.SpeechSynthesizer
                try {{ $s.SelectVoice('Microsoft David Desktop') }} catch {{}}
                $s.Rate = -2
                $s.Volume = 100
                $s.Speak("{clean_text}")
                """
    
    cmd = ['powershell.exe', '-NoProfile', '-Command', ps_script]
    
    proc = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
    
    try:
        input()  # Enter = skip
        proc.terminate()
        print("[SKIP] Skipped.")
    except KeyboardInterrupt:
        proc.terminate()
        print("[Interrupted]")
    except:
        proc.wait()
        out, err = proc.communicate()
        if err:
            print(f"[TTS Error] {err.strip()}")
        else:
            print("[Finished]")

def main():
    sessions = parse_journal()
    if not sessions:
        print("No dream sessions found in the journal.")
        return
    
    print(f"\nFound {len(sessions)} dream sessions.")
    print("  a     → Play all (press Enter to skip to next)")
    print("  n     → Select specific (enter number)")
    print("  q     → Quit\n")
    
    choice = input("Choice: ").strip().lower()
    
    if choice == 'q':
        return
    
    elif choice == 'a':
        for i, sess in enumerate(sessions, 1):
            print(f"\n--- {i} / {len(sessions)} ---")
            narrate_session(sess)
            time.sleep(1)  # short pause between sessions
    
    elif choice == 'n':
        try:
            num = int(input(f"Which one (1–{len(sessions)})? "))
            if 1 <= num <= len(sessions):
                narrate_session(sessions[num-1])
            else:
                print("Invalid number.")
        except:
            print("Please enter a number.")
    
    else:
        print("Unknown choice – try again.")

if __name__ == "__main__":
    main()