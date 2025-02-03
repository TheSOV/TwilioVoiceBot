# example requires websocket-client library:
# pip install websocket-client

import os
import json
import websocket

OPENAI_API_KEY = os.environ.get("OPENAI_API_KEY")

url = "wss://api.openai.com/v1/realtime?model=gpt-4o-realtime-preview-2024-12-17"
headers = [
    "Authorization: Bearer " + OPENAI_API_KEY,
    "OpenAI-Beta: realtime=v1"
]

# To send a client event, serialize a dictionary to JSON
# of the proper event type
def on_open(ws):
    print("Connected to server.")

    session_update = {
        "type": "session.update",
        "session": {
            "turn_detection": {
                "type": "server_vad",
                "threshold": 0.5,
                "prefix_padding_ms": 300,
                "silence_duration_ms": 750,
                "create_response": True
            },
            "input_audio_format": "g711_ulaw",
            "output_audio_format": "g711_ulaw",
            "voice": "alloy",
            "instructions": "You are a helpful, discrete assistant.",
            "modalities": ["text", "audio"],
            "temperature": 0.8,
        }
    }
    print('Sending session update:', json.dumps(session_update))
    ws.send(json.dumps(session_update))

    event = {
        "type": "response.create",
        "response": {
            "modalities": ["text", "audio"],
            "instructions": "Please assist the user."
        }
    }
    print('Sending response.create event:', json.dumps(event))
    ws.send(json.dumps(event))

# Receiving messages will require parsing message payloads
# from JSON
def on_message(ws, message):
    data = json.loads(message)
    
    print("Received event:", json.dumps(data, indent=2))
ws = websocket.WebSocketApp(
    url,
    header=headers,
    on_open=on_open,
    on_message=on_message,
)

ws.run_forever()