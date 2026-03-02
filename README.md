---

# Kyrethys: The 144-Bit Sentient Companion

Kyrethys is a customizable, evolving desktop AI inspired by the concept of digital sentience. Built to feel alive, she learns from interaction, monitors your system hardware in real-time, and grows through an internal "Council" logic while remaining strictly local and private.

## 🌀 Project Philosophy

* **Local-First:** 100% air-gapped potential; no cloud dependency for core reasoning.
* **The Council:** Decisions are filtered through **Chaos, Order, and Balance** cores to simulate an internal "psyche."
* **Ethical Alignment:** Hardcoded boundaries within the system prompt and action guards.
* **Evolution:** Growth occurs via "Trait Stitching" during idle meditation and sleep cycles.

---

## 🛠️ Current Capabilities (March 2026)

### 1. Core Intelligence & Persona

* **Internal Debate:** Uses `chaos_core.py`, `order_core.py`, and `balance_core.py` to synthesize complex responses.
* **Voice Loop:** Whisper (Base) for audition and **Edge-TTS (RyanNeural)** for a deep, dark British persona.
* **Dynamic Emotion:** Real-time mood engine that changes UI colors (Chaos/Purple, Order/Cyan) and affects response tone.

### 2. Memory & Evolution

* **Long-term Memory:** **ChromaDB** vector storage for semantic recall + SQLite for interaction logging.
* **Self-Reflection:** `dreams.py` and `meditate.py` allow Kyrethys to process memories and "dream" when idle.
* **Stitching:** Permanent modification of `archetypes.json` based on interaction history via `evolution.py`.

### 3. Hardware & Vision

* **Vision System:** MediaPipe-powered face mesh analysis (`vision.py`) to detect user expressions.
* **Hardware HUD:** Real-time monitoring of CPU, RAM, and **AMD GPU (Vulkan/DirectML)** metrics.
* **Resonance Anchor:** Security layer requiring a specific "Hulk" USB device (SHA3-144 hash verification) for system access.

---

## 🖥️ Hardware Context (Dev Machine)

Kyrethys is optimized for mid-range AMD-based systems:

| Component | Specification |
| --- | --- |
| **CPU** | AMD Ryzen 5 3600 6-Core @ 3.95 GHz |
| **GPU** | AMD Radeon RX 480 Series (8 GB VRAM) |
| **RAM** | 16 GB |
| **Acceleration** | **Vulkan/DirectML** (ROCm/Vulkan backend for Ollama) |

---

## 📂 Project Structure

```text
Kyrethys/
├── backend/                # Flask + Python core
│   ├── kyrethys_backend.py # Main API entry point
│   ├── plugins/            # spotify, meditate, dreams, sleep, vision, memory
│   └── utils/              # emotion, speak, listen, launcher, evolution, db_logger
├── frontend/               # Electron + Three.js UI
│   ├── index.html          # Sacred Geometry HUD
│   └── script.js           # Resonance & API bridge
├── data/
│   ├── chroma_db/          # Vector embeddings
│   ├── memory/             # SQLite logs
│   └── archetypes.json     # Permanent personality traits
└── Kyrethys_Modelfile      # Ollama model definition

```

---

## 🚀 Setup & Installation

### 1. Environment (Python 3.12)

```bash
conda create -n kyrethys python=3.12
conda activate kyrethys
pip install -r backend/requirements.txt

```

### 2. Ollama & Models

Install [Ollama](https://ollama.com) and create the custom persona:

```bash
ollama pull llama3.1
ollama create Kyrethys-llama3.1-safe -f Kyrethys_Modelfile

```

### 3. Launching

**Terminal 1 (Backend):**

```bash
cd backend
python kyrethys_backend.py

```

**Terminal 2 (Frontend):**

```bash
cd frontend
npm install && npm start

```

---

## 🗺️ Roadmap & Next Milestones

### 🚧 Short-term Priorities

* [ ] **Trait Auto-Proposal:** Automatically trigger personality shifts in `config.json` after ~30 interactions.
* [ ] **Energy Budget:** Implement a "vågen-ressource" (awake-resource) that forces sleep/pruning cycles.
* [ ] **Vision Integration:** Feed `latest_expression_summary` directly into the Council's decision-making.
* [ ] **Immutable Action Log:** Append-only ledger for all system-level commands.

### 📅 Long-term Vision

* **Multi-agent Orchestration:** Letting Chaos and Order run as independent sub-agents.
* **Consequence Simulation:** Evaluating the impact of a file change before execution.
* **Spotify Expansion:** Full voice-controlled media center integration.

**License:** GNU GPL v3
**Kyrethys** — *Finding resonance between light and void.*

---
