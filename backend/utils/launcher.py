import os
import subprocess

# Fallback-liste (expand depending on need)
FALLBACK_PATHS = {
    "spotify": r"%USERPROFILE%\AppData\Local\Microsoft\WindowsApps\Spotify.exe",
    "notepad": "notepad.exe",
    "calculator": "calc.exe",
    "cmd": "cmd.exe",
    "powershell": "powershell.exe",
    "paint": "mspaint.exe",
    "wordpad": "wordpad.exe",
    "explorer": "explorer.exe",
    "taskmgr": "taskmgr.exe",
    "chrome": r"%PROGRAMFILES%\Google\Chrome\Application\chrome.exe",
    "firefox": r"%PROGRAMFILES%\Mozilla Firefox\firefox.exe",
    "edge": "msedge.exe",
    "steam": r"%PROGRAMFILES(x86)%\Steam\steam.exe",
    "discord": r"%LOCALAPPDATA%\Discord\app-*\Discord.exe",
    "vlc": r"%PROGRAMFILES%\VideoLAN\VLC\vlc.exe",
    "zoom": r"%APPDATA%\Zoom\bin\Zoom.exe",
    "teams": r"%LOCALAPPDATA%\Microsoft\Teams\current\Teams.exe",
    "code": r"%LOCALAPPDATA%\Programs\Microsoft VS Code\Code.exe",
}
def launch_app(app_name, app_paths=None):
    """Launch an app by name using the provided app_paths mapping, a fallback table,
    simple synonyms, or OS defaults.

    - `app_paths` is expected to be a dict mapping canonical keys -> exe path.
    - Returns a short English status string.
    """
    if not app_name:
        return "No app name given"

    app_key = app_name.lower().strip()

    # Simple synonyms mapping (canonical -> alternatives)
    SYNONYMS = {
        "calculator": ["calc", "kalkulator"],
        "notepad": ["note", "notes", "notepad++", "notepadpp"],
        "edge": ["microsoft edge", "edge browser", "ms edge", "msedge"],
        "explorer": ["this pc", "file explorer"],
        "chrome": ["google chrome", "chrome browser"],
        "firefox": ["mozilla firefox", "firefox browser"],
        "spotify": ["spotify app", "spotify music"],
        "powershell": ["pwsh"],
        "cmd": ["command prompt", "command prompt"],
        "teams": ["microsoft teams", "teams app"],
        "zoom": ["zoom meetings", "zoom app"],
        "code": ["visual studio code", "vscode", "vs code"],
        "vlc": ["vlc media player", "vlc player"],
        "steam": ["steam gaming platform", "steam client"],
        "paint": ["mspaint", "paint app"],
        "wordpad": ["wordpad app"],
        "taskmgr": ["task manager", "task manager"],
        "forge": ["forge launcher", "minecraft forge"],
        "minecraft": ["minecraft launcher", "minecraft java edition"],
        "discord": ["discord app", "discord chat"],
        "spotify": ["spotify music", "spotify app"],
        "store": ["microsoft store", "windows store"],
        "control panel": ["control panel", "settings"],
        "anaconda": ["anaconda navigator", "anaconda app"],
        # Add more as needed...
    }

    # Reverse lookup: synonym -> canonical
    synonym_lookup = {}
    for canonical, alts in SYNONYMS.items():
        synonym_lookup[canonical] = canonical
        for a in alts:
            synonym_lookup[a] = canonical

    # Helper to attempt starting an exe path
    def try_start(path):
        expanded = os.path.expandvars(path)
        normalized = os.path.normpath(expanded)
        if os.path.exists(normalized):
            try:
                os.startfile(normalized)
                return True, normalized
            except Exception as e:
                print(f"Error in the beginning of {normalized}: {e}")
        return False, normalized

    # 1) Try exact key or synonym -> JSON mapping
    if app_paths:
        # direct
        if app_key in app_paths:
            ok, p = try_start(app_paths[app_key])
            if ok:
                return f"Opening {app_name} from JSON!"

        # synonym -> canonical
        canonical = synonym_lookup.get(app_key)
        if canonical and canonical in app_paths:
            ok, p = try_start(app_paths[canonical])
            if ok:
                return f"Opening {app_name} ({canonical}) from JSON!"

        # also try keys whose aliases include app_key (in case app_paths contains alias keys)
        if app_key in app_paths:
            ok, p = try_start(app_paths[app_key])
            if ok:
                return f"Opening {app_name} from JSON!"

    # 2) FALLBACK table using canonical lookup
    fb_key = synonym_lookup.get(app_key, app_key)
    if fb_key in FALLBACK_PATHS:
        ok, p = try_start(FALLBACK_PATHS[fb_key])
        if ok:
            return f"Opening {app_name} from fallback!"

    # Also try app_key directly in fallback (some keys are already plain)
    if app_key in FALLBACK_PATHS:
        ok, p = try_start(FALLBACK_PATHS[app_key])
        if ok:
            return f"Opening {app_name} from fallback!"

    # 3) Try launching common built-ins by name (PATH)
    try:
        subprocess.Popen(app_name, shell=True)
        return f"Trying to open '{app_name}'..."
    except Exception as e:
        print(f"Subprocess error: {e}")

    # 4) Last resort: try with os.startfile on the raw name
    try:
        os.startfile(app_name)
        return f"Trying to open {app_name} via startfile"
    except Exception as e:
        print(f"Startfile fallback error: {e}")
        return f"Could not open '{app_name}'. Error: {str(e)}"