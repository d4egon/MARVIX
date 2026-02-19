import os
import json
import re
from tqdm import tqdm  # progress bar

# Almindelige mapper at scanne
directories = [
    os.path.expandvars('%ProgramFiles%'),
    os.path.expandvars('%ProgramFiles(x86)%'),
    os.path.expandvars('%APPDATA%'),
    os.path.expandvars('%LOCALAPPDATA%'),
    os.path.expandvars('%USERPROFILE%\\Desktop'),
    os.path.expandvars('%USERPROFILE%\\Downloads'),
]

# Fast-scan option (set FAST_SCAN=1 in env to limit scan to ProgramFiles folders)
if os.environ.get('FAST_SCAN') == '1':
    directories = [
        os.path.expandvars('%ProgramFiles%'),
        os.path.expandvars('%ProgramFiles(x86)%'),
    ]

exe_paths = {}

# Keywords/paths to exclude — installers, updaters, temp/downloads, redistributables
BLACKLIST_KEYWORDS = (
    'setup', 'installer', 'install', 'update', 'updater', 'patch', 'patcher',
    'driver', 'redistrib', 'vcredist', 'vc_redist', 'unins', 'uninstall', 'bootstrapper',
    'choco', 'chocolatey', 'msi', 'payload', 'extract', 'extractor', 'tmp', 'temp'
)

KNOWN_BROWSERS = ('edge', 'msedge', 'microsoftedge', 'chrome', 'googlechrome', 'firefox', 'brave', 'opera', 'vivaldi')


def generate_aliases(app_name: str) -> set:
    """Return a set of friendly alias keys for an executable base name."""
    aliases = set()
    name = app_name.lower()

    # Replace punctuation/underscores with spaces
    spaced = re.sub(r'[._\-]+', ' ', name).strip()
    compact = spaced.replace(' ', '')
    if spaced:
        aliases.add(spaced)
    if compact and compact != name:
        aliases.add(compact)

    # Browser-specific aliases
    for b in KNOWN_BROWSERS:
        if b in name:
            # common human phrases
            aliases.add('edge' if 'edge' in b else b)
            aliases.add('microsoft edge')
            aliases.add('ms edge')
            aliases.add('edge browser')
            aliases.add('microsoft edge browser')
            aliases.add('google chrome')
            aliases.add('chrome browser')
            aliases.add('firefox browser')
            aliases.add('brave browser')
            break

    # Add a plain version (no punctuation) and the original if short and legible
    plain = re.sub(r'[^a-z0-9 ]+', '', spaced)
    if plain:
        aliases.add(plain)

    # Clean up and keep only short, meaningful keys
    cleaned = {a.strip() for a in aliases if 2 < len(a) <= 40}
    return cleaned


# Saml alle filer først for at vise progress
all_files = []
for dir_path in directories:
    if not os.path.exists(dir_path):
        continue
    for root, _, files in os.walk(dir_path):
        all_files.extend((os.path.join(root, f), f) for f in files)

# Progress bar over alle filer
with tqdm(total=len(all_files), desc="Scanning .exe files") as pbar:
    for full_path, file in all_files:
        pbar.update(1)
        if not file.lower().endswith('.exe'):
            continue

        app_name = os.path.splitext(file)[0].lower()

        # Basic filters: length and blacklist keywords
        if len(app_name) <= 3:
            continue
        low = app_name.lower()
        if any(k in low for k in BLACKLIST_KEYWORDS):
            continue

        # Skip many auto-downloads / installers in Downloads or Temp
        placeholder_path = full_path.replace(os.path.expanduser('~'), '%USERPROFILE%').replace('\\', '/')
        if '/Downloads/' in placeholder_path or '/Temp/' in placeholder_path:
            continue

        # Keep first found mapping (don't overwrite existing)
        if app_name not in exe_paths:
            exe_paths[app_name] = placeholder_path

            # Generate and add friendly aliases (don't overwrite existing keys)
            aliases = generate_aliases(app_name)
            for alias in aliases:
                key = alias.replace(' ', '').lower() if ' ' not in alias else alias.lower()
                key = key.strip()
                if key and key not in exe_paths:
                    exe_paths[key] = placeholder_path


# Skriv til JSON
with open('app_paths.json', 'w', encoding='utf-8') as f:
    json.dump(exe_paths, f, indent=4, ensure_ascii=False)

print(f"\nFærdig! app_paths.json oprettet med {len(exe_paths)} apps.")
print("Eksempel (første 5):", dict(list(exe_paths.items())[:5]))