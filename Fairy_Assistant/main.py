"""
main.py - Fairy Assistant SocketIO Server

Flask-SocketIO server that handles:
- Text commands from the mobile app (client_command)
- Integrates Ollama for LLM inference (streaming)
- Integrates MemoryBrain for context
"""

import os
from dotenv import load_dotenv
from flask import Flask
from flask_socketio import SocketIO, emit
import ollama
import whisper
from memory_brain import MemoryBrain
import action_parser

# Load environment variables
load_dotenv()

# Configuration
MODEL_NAME = os.getenv("MODEL_NAME", "llama3.2")
HOST = "0.0.0.0"
PORT = 5000

# Initialize Flask app
app = Flask(__name__)
app.config['SECRET_KEY'] = 'fairy-secret-key'

# Initialize SocketIO with CORS enabled
socketio = SocketIO(app, cors_allowed_origins="*", async_mode='eventlet')

# Initialize Memory Brain
print("[Fairy] Initializing Memory Brain...")
brain = MemoryBrain()

# Initialize Whisper Model
print("[Fairy] Loading Whisper Model (base)... This may take a moment.")
ear_model = whisper.load_model("base")
print("[Fairy] Whisper Model Loaded.")

# System Prompt
SYSTEM_PROMPT = """You are Fairy, a sentient, helpful local assistant living on the user's computer. 
You can switch between apps, type text, and control the system.
Your memory is persistent. Use the context provided to answer questions.
When you want to perform an action, use the tag [ACTION: TYPE | args].
"""

print(f"[Fairy] Using Ollama model: {MODEL_NAME}")

def ask_ollama_stream(prompt: str):
    """
    Send a prompt to Ollama and yield response chunks.
    """
    try:
        stream = ollama.chat(
            model=MODEL_NAME,
            messages=[{"role": "user", "content": prompt}],
            stream=True
        )
        for chunk in stream:
            yield chunk['message']['content']
    except Exception as e:
        yield f"Error: {e}"

# SocketIO Event Handlers

@socketio.on('connect')
def handle_connect():
    """Handle client connection."""
    print("[SocketIO] Client connected")
    emit('server_log', {'message': 'Connected to Fairy Assistant'})

@socketio.on('disconnect')
def handle_disconnect():
    """Handle client disconnection."""
    print("[SocketIO] Client disconnected")

@socketio.on('client_command')
def handle_client_command(data):
    """
    Handle text commands from the client.
    Expected data format: {'text': 'user message'}
    """
    text = data.get('text', '') if isinstance(data, dict) else str(data)
    print(f"[SocketIO] Cmd: {text}")
    
    if not text:
        return

    # 1. Retrieve context
    memories = brain.retrieve(text)
    context_str = "\n".join([f"- {m['text']}" for m in memories])
    
    # 2. Construct prompt
    full_prompt = f"{SYSTEM_PROMPT}\n\nCONTEXT FROM MEMORY:\n{context_str}\n\nUSER: {text}\nASSISTANT:"
    
    # 3. Call Ollama (Stream)
    full_response = ""
    print("[Fairy] Thinking...")
    
    for chunk in ask_ollama_stream(full_prompt):
        full_response += chunk
        # 4. Emit chunks
        emit('server_response', {'text': chunk, 'done': False})
    
    emit('server_response', {'text': '', 'done': True})
    print(f"[Fairy] Response: {full_response[:50]}...")

    # 5. Parse and Execute Actions (Phase 3 enabled)
    parsed = action_parser.parse_and_execute(full_response)
    if parsed['actions_found'] > 0:
        print(f"[Fairy] Actions: Found {parsed['actions_found']}, Executed {parsed['actions_executed']}")
        emit('server_log', {'message': f"Executed {parsed['actions_executed']}/{parsed['actions_found']} actions"})

    # 6. Store to Memory
    brain.store(text, metadata={"role": "user"})
    brain.store(parsed['clean_text'], metadata={"role": "assistant"})


@socketio.on('audio_command')
def handle_audio_command(audio_bytes):
    """
    Handle audio commands using Whisper STT.
    """
    print(f"[SocketIO] Received audio_command: {len(audio_bytes)} bytes")
    
    try:
        # Save temp file
        temp_file = "temp_input.wav"
        with open(temp_file, "wb") as f:
            f.write(audio_bytes)
            
        # Transcribe
        print("[Whisper] Transcribing...")
        result = ear_model.transcribe(temp_file)
        text = result["text"].strip()
        print(f"[Whisper] Heard: {text}")
        
        emit('server_action', {'type': 'transcript', 'message': text})
        
        # Pass to text handler if not empty
        if text:
            handle_client_command({'text': text})
        else:
            emit('server_log', {'message': "I didn't hear anything."})

    except Exception as e:
        print(f"[Whisper] Error: {e}")
        emit('server_log', {'message': f"Audio error: {e}"})

@app.route('/')
def index():
    return "Fairy Assistant Phase 2 Running"

if __name__ == '__main__':
    print(f"[Fairy] Starting server on {HOST}:{PORT}")
    socketio.run(app, host=HOST, port=PORT, debug=True)
