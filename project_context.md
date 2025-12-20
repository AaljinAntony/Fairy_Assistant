# PROJECT: FAIRY ASSISTANT (LINUX LOCAL EDITION)

**Version:** 3.2.0 (Ubuntu 24.04 Optimized)  
**Type:** Privacy-First AI Agent  
**Environment:** Ubuntu 24.04 (Host) + Android (Client)  
**Language:** Python 3.10+ (Backend), Dart (Mobile)

---

## 1. HIGH-LEVEL OBJECTIVE

Build "Fairy," a personal AI operating system that runs entirely on local hardware.

- **Privacy:** No data leaves the local network.
- **Intelligence:** Powered by Ollama (Llama 3.2 / Mistral) running on the host PC.
- **Hearing:** Powered by OpenAI Whisper running locally on the host PC.
- **Interface:** A custom Flutter app for voice input and text output.

---

## 2. SYSTEM ARCHITECTURE

### A. The Brain (Linux Host)

- **OS Requirement:** Ubuntu 24.04 running on Xorg (X11).
  - **CRITICAL:** Automation tools (xdotool, pyautogui) do not work on Wayland.
- **Runtime:** `python main.py` using Flask-SocketIO (Async Mode).
- **Server:** WebSocket server listening on `0.0.0.0:5000`.
- **Inference Engine:**
  - **LLM:** `ollama` library interacting with local model.
  - **STT:** `openai-whisper` (Base model) using CPU/GPU.
- **Memory:** `chromadb` (Persistent Vector Store) saved to `./memory_db`.

### B. The Hands (Android - Custom App)

- **Framework:** Flutter (Dart).
- **Functionality:**
  - **Socket Client:** Maintains a persistent WebSocket connection to the PC via `10.0.2.2:5000` (Android Emulator alias).
  - **Audio Streamer:** Records audio (Push-to-Talk) and uploads WAV bytes to the `audio_command` event.
  - **Text-to-Speech:** Uses `flutter_tts` to speak Fairy's responses.
  - **Actuator:** Listens for `server_action` events to trigger native Android Intents (SMS, Phone, Apps).

---

## 3. DIRECTORY STRUCTURE

```
Fairy_Assistant/
├── .venv/                  # Python Virtual Environment
├── .env                    # Config (e.g., MODEL_NAME="llama3.2")
├── .env.example            # Environment template
├── requirements.txt        # Python dependencies
├── main.py                 # SocketIO Server & Event Loop
├── memory_brain.py         # ChromaDB wrapper
├── action_parser.py        # Logic to parse [ACTION] tags
├── run_dev.sh              # Developer script to launch backend + Flutter
├── verify_linux.py         # Automation tests
├── verify_backend.py       # Backend verification
├── tools/
│   ├── linux_ops.py        # Desktop automation (X11/subprocess)
│   └── android_ops.py      # SocketIO Emitters
├── tests/
│   └── test_server.py      # Server tests
├── mobile_app/             # Flutter Project
│   ├── lib/main.dart       # Main Flutter application
│   ├── pubspec.yaml        # Flutter dependencies
│   └── android/            # Android-specific configuration
├── context/
│   └── ai_context.md       # Persona & Few-Shot Prompts
└── project_context.md      # THIS FILE
```

---

## 4. INTER-PROCESS COMMUNICATION (Socket.IO)

### A. Events

| Event | Direction | Description |
|-------|-----------|-------------|
| `client_command` | Android → PC | User typed text |
| `audio_command` | Android → PC | Raw audio bytes (WAV) |
| `server_action` | PC → Android | JSON payload |

### B. Action Types

| Type | Description |
|------|-------------|
| `speak` | Text-to-Speech string |
| `transcript` | STT text for UI display |
| `log` | Debug info |
| `trigger_intent` | Hardware control (SMS, Call, etc.) |

### C. Action Tags & Handlers

The LLM outputs tags. `action_parser.py` executes them.

| Intent | Output Tag | Handler |
|--------|------------|---------|
| Open App | `[ACTION: OPEN_LINUX <app>]` | `linux_ops.py` |
| Type | `[ACTION: TYPE_LINUX <text>]` | `linux_ops.py` |
| Lock | `[ACTION: SYSTEM_LINUX lock]` | `linux_ops.py` |
| Mute | `[ACTION: SYSTEM_LINUX mute]` | `linux_ops.py` |
| Screenshot | `[ACTION: SCREENSHOT_LINUX]` | `linux_ops.py` |
| Android Msg | `[ACTION: ANDROID_MSG ...]` | `android_ops.py` |

---

## 5. DEPENDENCIES & REQUIREMENTS

### A. System Packages (Ubuntu/Debian)

Install via `sudo apt install`:
- `python3-venv`, `python3-dev`
- `xdotool` (Required for window focus/typing)
- `scrot` (Required for screenshots/vision)
- `libasound2-dev`, `portaudio19-dev` (Required for PyAudio/Whisper)
- `ffmpeg` (Required for audio conversion)

### B. Python Libraries (pip)

- `flask`, `flask-socketio`, `eventlet` (Server)
- `ollama` (Local LLM)
- `openai-whisper`, `torch`, `numpy` (Local STT)
- `chromadb` (Memory)
- `pyautogui`, `python-xlib` (Automation)
- `python-dotenv`

### C. Flutter Packages (pubspec.yaml)

- `socket_io_client: ^3.0.0` - Server communication
- `record: ^5.0.0` - Audio capture
- `path_provider: ^2.1.0` - File utilities
- `permission_handler: ^11.0.0` - Permission handling
- `url_launcher: ^6.2.0` - Opening WhatsApp/Maps
- `flutter_tts: ^4.2.0` - Text-to-Speech

---

## 6. DEVELOPMENT WORKFLOW

### Quick Start

```bash
# Terminal: Start everything
cd Fairy_Assistant
./run_dev.sh
```

This script:
1. Activates the Python virtual environment
2. Starts the `main.py` backend server
3. Waits for server initialization
4. Launches the Flutter app on the connected emulator/device

### Manual Setup

1. **Environment Setup:**
   - Switch Ubuntu to Xorg
   - Install system packages (apt)
   - Create `.venv` and install `requirements.txt`
   - Copy `.env.example` to `.env` and configure

2. **Brain Logic:**
   - `main.py` handles SocketIO events
   - `ask_local_llm()` queries Ollama
   - `transcribe_audio()` uses Whisper

3. **Linux Hands:**
   - `tools/linux_ops.py` handles desktop automation
   - Ensure `DISPLAY=:0` is set

4. **Mobile App:**
   - Uses `10.0.2.2:5000` for Android Emulator → Host connection
   - "Hold to Talk" button for voice input
   - TTS for Fairy's spoken responses

---

## 7. TESTING

```bash
# Run server tests
cd Fairy_Assistant
source .venv/bin/activate
python -m pytest tests/
```

---

## 8. CURRENT STATUS

- ✅ Backend server with SocketIO communication
- ✅ Memory persistence with ChromaDB
- ✅ Action parsing for Linux automation
- ✅ Flutter mobile app with voice recording
- ✅ Text-to-Speech integration
- ✅ Developer utility script (`run_dev.sh`)
- ✅ Verification scripts (`verify_linux.py`, `verify_backend.py`)
- ✅ Screenshot screenshot capability (via `scrot`)
- ⏳ Android intent handlers (SMS, Call) - In Progress
- ⏳ Vision integration (multimodal LLM analysis) - Planned
