import socketio
import time

sio = socketio.Client()

@sio.event
def connect():
    print("Connected to server")
    # Send a test command
    print("Sending command: 'Hello Fairy'")
    sio.emit('client_command', {'text': 'Hello Fairy'})

@sio.event
def server_response(data):
    print(f"Received response: {data}")
    if data.get('done'):
        print("Response complete. Disconnecting...")
        sio.disconnect()

@sio.event
def server_log(data):
    print(f"Server Log: {data}")

@sio.event
def disconnect():
    print("Disconnected from server")

def main():
    max_retries = 5
    for i in range(max_retries):
        try:
            print(f"Attempting connection (try {i+1}/{max_retries})...")
            sio.connect('http://localhost:5000')
            sio.wait()
            break
        except Exception as e:
            print(f"Connection failed: {e}")
            time.sleep(2)

if __name__ == '__main__':
    main()
