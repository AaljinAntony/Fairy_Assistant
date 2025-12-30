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
HOST = os.getenv("HOST_IP", "0.0.0.0")
PORT = int(os.getenv("PORT", 5000))
DEBUG = os.getenv("DEBUG_MODE", "True") == "True"

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

# System Prompt - Loaded from context/ai_context.md
try:
    with open("context/ai_context.md", "r") as f:
        SYSTEM_PROMPT = f.read()
except FileNotFoundError:
    print("[Fairy] Warning: context/ai_context.md not found. Using default prompt.")
    SYSTEM_PROMPT = """You are Fairy. Use [ACTION: TYPE | text] or [ACTION: OPEN | app]."""

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
    Handle text commands from the client with ReAct loop.
    Expected data format: {'text': 'user message'}
    
    ReAct Loop: Continues executing actions until the LLM produces
    a final answer (no action tag) or reaches max steps.
    """
    MAX_STEPS = 5
    
    text = data.get('text', '') if isinstance(data, dict) else str(data)
    print(f"[SocketIO] Cmd: {text}")
    
    if not text:
        return

    # 1. Retrieve context from memory
    memories = brain.retrieve(text)
    context_str = "\n".join([f"- {m['text']}" for m in memories])
    
    # 2. Initialize conversation history for this request
    conversation_history = [
        {"role": "system", "content": SYSTEM_PROMPT},
        {"role": "user", "content": f"CONTEXT FROM MEMORY:\n{context_str}\n\nUSER: {text}"}
    ]
    
    step = 0
    final_response = ""
    
    while step < MAX_STEPS:
        step += 1
        print(f"\n[Loop Step {step}] Thinking...")
        
        # 3. Call Ollama with conversation history
        full_response = ""
        try:
            stream = ollama.chat(
                model=MODEL_NAME,
                messages=conversation_history,
                stream=True
            )
            for chunk in stream:
                chunk_text = chunk['message']['content']
                full_response += chunk_text
                # Emit chunks to client so they see the thought process
                emit('server_response', {'text': chunk_text, 'done': False})
        except Exception as e:
            error_msg = f"Error: {e}"
            emit('server_response', {'text': error_msg, 'done': True})
            print(f"[Fairy] {error_msg}")
            return
        
        emit('server_response', {'text': '', 'done': True})
        print(f"[Fairy] Response: {full_response[:80]}...")
        
        # Add assistant response to history
        conversation_history.append({"role": "assistant", "content": full_response})
        final_response = full_response
        
        # 4. Parse and execute actions
        parsed = action_parser.parse_and_execute(full_response)
        
        if parsed['actions_found'] > 0:
            print(f"[Fairy] Actions: Found {parsed['actions_found']}, Executed {parsed['actions_executed']}")
            emit('server_log', {'message': f"Executed {parsed['actions_executed']}/{parsed['actions_found']} actions"})
            
            # Safety check: if actions found but none executed, the AI is hallucinating invalid actions
            if parsed['actions_executed'] == 0:
                print(f"[Loop] Invalid/unknown action detected. Stopping agent to prevent spiraling.")
                emit('server_log', {'message': "Unknown action detected - stopping"})
                break
            
            # 5. Append observation to conversation history for next iteration
            observations = parsed.get('observations', [])
            if observations:
                observation_text = "\n".join([f"[OBSERVATION] {obs}" for obs in observations])
                print(f"[Observation] {observation_text}")
                conversation_history.append({
                    "role": "user", 
                    "content": f"System Observation:\n{observation_text}\n\nContinue with the task."
                })
            # Continue the loop to let AI process the observation
        else:
            # No action found - AI is done talking
            print(f"[Loop Complete] No action found. Steps: {step}")
            break
    
    if step >= MAX_STEPS:
        print(f"[Loop] Max steps ({MAX_STEPS}) reached. Stopping.")
        emit('server_log', {'message': f"Max steps ({MAX_STEPS}) reached"})

    # 6. Store to Memory (only final exchange)
    brain.store(text, metadata={"role": "user"})
    clean_text = action_parser.ACTION_PATTERN.sub('', final_response).strip()
    brain.store(clean_text, metadata={"role": "assistant"})


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
    print("[Fairy] Configuration loaded from .env")
    socketio.run(app, host=HOST, port=PORT, debug=DEBUG)
