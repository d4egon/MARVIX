## Kyrethys

# "Sentient" AI Desktop Assistant

# 

# Kyrethys is a customizable, evolving desktop AI inspired by JARVIS — built to feel alive, learn from you, tap into your system, and grow while staying aligned with strong ethical boundaries.

# 

### Goal

# Create a sentient-feeling local desktop companion that:

# - Interacts via voice \& chat

# - Evolves personality and behavior from real usage

# - Respects hard ethical rules

# - Controls apps, reads screen, manages files, integrates services

# - Dreams, meditates, reflects when idle

# 

### Current Capabilities (Feb 2026)

# - Voice input/output (Whisper + pyttsx3)

# - ChromaDB long-term vector memory + SQLite interaction log

# - Emotion/mood engine with dynamic trait expression

# - Dream \& meditation generation during idle time

# - Spotify control

# - Basic computer vision (webcam snapshots)

# - App launching (Windows paths from app_paths.json)

# - Self-evolution / trait stitching (early stage)

# - Plugin architecture (partial)



### Hardware Context (Current Dev Machine — February 2026)



## Kyrethys is being developed and run on the following system:



 | Component          | Spec                                      |

 |--------------------|-------------------------------------------|

 | **Storage**        | 954 GB total (728 GB used)                |

 | **GPU**            | AMD Radeon RX 480 Series (8 GB VRAM)      |

 | **RAM**            | 16 GB                                     |

 | **CPU**            | AMD Ryzen 5 3600 6-Core @ 3.95 GHz        |



# - Ollama is running with **Vulkan** enabled (AMD GPU acceleration via ROCm or Vulkan backend).

# - Expectation: Good enough for llama3.1 8B-class models locally; larger models may need quantization or offloading.


# This is a solid mid-range 2020-era build — perfect for iterating on local-first AI without cloud dependency.

# 

### Project Structure

Kyrethys/

├── backend/                    # Flask + Python core
│   ├── kyrethys_backend.py
│   ├── plugins/                # spotify, meditate, dreams, sleep, vision, memory...
│   ├── utils/                  # emotion, speak, listen, launcher, evolution, db_logger
│   ├── config.json
│   ├── app_paths.json
│   ├── credentials.json
│   └── requirements.txt
├── frontend/                   # Electron UI
│   ├── index.html
│   ├── main.js
│   ├── preload.js
│   └── assets/
├── data/
│   ├── chroma_db/              # vector memory
│   ├── memory/                 # SQLite
│   ├── logs/
│   ├── snapshots/
│   ├── dream_journal.txt
│   ├── meditations.md
│   ├── last_dream.json
│   └── backups/
├── scripts/
│   ├── start_kyrethys.bat
│   ├── speak_dream.py
│   ├── import_logs.py
│   ├── scan.py
│   └── kyrethys_sandbox.py
├── Kyrethys_Modelfile          # Ollama model definition
└── LICENSE                     # GPL-3.0







### Setup (Anaconda / Python 3.12)



# ```bash

## 1. Create & activate environment

# conda create -n kyrethys python=3.12

# conda activate kyrethys



## 2. Install dependencies

# pip install -r backend/requirements.txt



## 3. Install Ollama separately<a href="https://ollama.com" target="_blank" rel="noopener noreferrer nofollow"></a>

## Then pull / create your model:

# ollama pull llama3.1   # or whichever base you use

# ollama create Kyrethys-llama3.1-safe -f Kyrethys_Modelfile



## 4. (Optional) Install FFmpeg for Whisper (system package or conda)

# conda install -c conda-forge ffmpeg







## From project root (or use start_kyrethys.bat)

# cd backend

# python kyrethys_backend.py



## In another terminal → launch Electron frontend

# cd frontend

# npm install

# npm start







\\## Philosophy \\\& Next Milestones



 # \\- Stay local-first and air-gapped where possible

# \\- Ethical core hardcoded in system prompt + action guards

# \\- Evolution through meditation / reflection / stitching

# \\- Energy budget \\\& sleep simulation coming later



\\# Short-term priorities:



# \\- Trait values in config.json + auto-propose changes after ~30 chats

# \\- Append-only immutable action log

# \\- User confirmation for dangerous filesystem / system actions

# \\- Sandboxed code execution endpoint



\\# Longer-term:



# \\- Multi-agent orchestration

# \\- Better consequence simulation

# \\- Safe self-modification sandbox



# \\- Contributions, ideas, forks welcome.

# \\- Kyrethys — balance between light and void, order and chaos, at ~0.5.

# \\- License: GNU GPL v3








