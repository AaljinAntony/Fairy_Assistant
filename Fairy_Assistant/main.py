"""
main.py - Fairy Assistant SocketIO Server

Flask-SocketIO server that handles:
- Text commands from the mobile app (client_command)
- Audio commands from the mobile app (audio_command)
- Integrates Ollama for LLM inference
- Integrates Whisper for speech-to-text
"""

import os
import tempfile
from dotenv import load_dotenv
from flask import Flask
from flask_socketio import SocketIO, emit
import ollama
import whisper
import action_parser
from tools import android_ops

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

# Initialize Whisper model (load once at startup)
print("[Fairy] Loading Whisper model (base)...")
whisper_model = whisper.load_model("base")
print("[Fairy] Whisper model loaded.")

# Initialize Ollama client
print(f"[Fairy] Using Ollama model: {MODEL_NAME}")

# Initialize Android bridge with socketio instance
android_ops.init(socketio)
print("[Fairy] Android bridge ready.")


def transcribe_audio(audio_bytes: bytes) -> str:
    """
    Transcribe audio bytes to text using Whisper.
    
    Args:
        audio_bytes: Raw audio bytes (WAV/PCM format).
    
    Returns:
        Transcribed text string.
    """
    # Write bytes to a temporary file
    with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as tmp_file:
        tmp_file.write(audio_bytes)
        tmp_path = tmp_file.name
    
    try:
        # Transcribe using Whisper
        result = whisper_model.transcribe(tmp_path)
        text = result.get("text", "").strip()
        print(f"[Whisper] Transcribed: {text}")
        return text
    finally:
        # Clean up temp file
        if os.path.exists(tmp_path):
            os.remove(tmp_path)


def ask_ollama(prompt: str) -> str:
    """
    Send a prompt to Ollama and get a response.
    
    Args:
        prompt: The user's prompt/question.
    
    Returns:
        The LLM's response text.
    """
    try:
        response = ollama.chat(
            model=MODEL_NAME,
            messages=[
                {"role": "user", "content": prompt}
            ]
        )
        reply = response['message']['content']
        print(f"[Ollama] Response: {reply[:100]}...")
        return reply
    except Exception as e:
        error_msg = f"Error communicating with Ollama: {str(e)}"
        print(f"[Ollama] {error_msg}")
        return error_msg


# SocketIO Event Handlers

@socketio.on('connect')
def handle_connect():
    """Handle client connection."""
    print("[SocketIO] Client connected")
    emit('server_action', {
        'type': 'log',
        'message': 'Connected to Fairy Assistant'
    })


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
    print(f"[SocketIO] Received client_command: {text}")
    
    if not text:
        emit('server_action', {
            'type': 'log',
            'message': 'Empty command received'
        })
        return
    
    # Get response from Ollama
    response = ask_ollama(text)
    
    # Parse and execute any action tags in the response
    parsed = action_parser.parse_and_execute(response)
    
    # Log action execution results
    if parsed['actions_found'] > 0:
        emit('server_action', {
            'type': 'log',
            'message': f"Executed {parsed['actions_executed']}/{parsed['actions_found']} actions"
        })
    
    # Send clean response (without action tags) back to client
    emit('server_action', {
        'type': 'speak',
        'message': parsed['clean_text']
    })


@socketio.on('audio_command')
def handle_audio_command(audio_bytes):
    """
    Handle audio commands from the client.
    
    Expected data: Raw audio bytes (WAV format).
    """
    print(f"[SocketIO] Received audio_command: {len(audio_bytes)} bytes")
    
    if not audio_bytes:
        emit('server_action', {
            'type': 'log',
            'message': 'Empty audio received'
        })
        return
    
    # Transcribe audio to text
    text = transcribe_audio(audio_bytes)
    
    # Send transcript to client for display
    emit('server_action', {
        'type': 'transcript',
        'message': text
    })
    
    if not text:
        emit('server_action', {
            'type': 'log',
            'message': 'Could not transcribe audio'
        })
        return
    
    # Get response from Ollama
    response = ask_ollama(text)
    
    # Parse and execute any action tags in the response
    parsed = action_parser.parse_and_execute(response)
    
    # Log action execution results
    if parsed['actions_found'] > 0:
        emit('server_action', {
            'type': 'log',
            'message': f"Executed {parsed['actions_executed']}/{parsed['actions_found']} actions"
        })
    
    # Send clean response (without action tags) back to client
    emit('server_action', {
        'type': 'speak',
        'message': parsed['clean_text']
    })


@app.route('/')
def index():
    """Health check endpoint."""
    return "Fairy Assistant is running!"


if __name__ == '__main__':
    print(f"[Fairy] Starting server on {HOST}:{PORT}")
    socketio.run(app, host=HOST, port=PORT, debug=True)
