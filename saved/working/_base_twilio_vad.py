import os
import json
import base64
import asyncio
import argparse
from fastapi import FastAPI, WebSocket, BackgroundTasks
from fastapi.responses import JSONResponse
from fastapi.websockets import WebSocketDisconnect
from twilio.rest import Client
import websockets
from dotenv import load_dotenv
import uvicorn
import re
import wave
import os
from datetime import datetime
import numpy as np
import audioop

load_dotenv(override=True)

# Configuration
TWILIO_ACCOUNT_SID = os.getenv('TWILIO_ACCOUNT_SID')
TWILIO_AUTH_TOKEN = os.getenv('TWILIO_AUTH_TOKEN')
PHONE_NUMBER_FROM = os.getenv('PHONE_NUMBER_FROM')
OPENAI_API_KEY = os.getenv('OPENAI_API_KEY')
raw_domain = os.getenv('GROK_DOMAIN', None)

if raw_domain is None:
    print("Error: GROK_DOMAIN is not set.")
    exit(1)

DOMAIN = re.sub(r'(^\w+:|^)\/\/|\/+$', '', raw_domain) # Strip protocols and trailing slashes from DOMAIN
VOICE = os.getenv('OPENAI_AUDIO_VOICE', 'coral')
OPENAI_MODEL = os.getenv('OPENAI_MODEL', 'gpt-4o-mini-realtime-preview-2024-12-17')

PORT = int(os.getenv('PORT', 6060))


print(f"TWILIO_ACCOUNT_SID: {TWILIO_ACCOUNT_SID}")
print(f"TWILIO_AUTH_TOKEN: {TWILIO_AUTH_TOKEN}")
print(f"PHONE_NUMBER_FROM: {PHONE_NUMBER_FROM}")
print(f"OPENAI_API_KEY: {OPENAI_API_KEY}")
print(f"DOMAIN: {DOMAIN}")
print(f"VOICE: {VOICE}")
print(f"OPENAI_MODEL: {OPENAI_MODEL}")
print(f"PORT: {PORT}")

# input("Press Enter to continue...")

SYSTEM_MESSAGE = (
    """# Prompt de Sistema - Asistente MyCityHome

Eres el asistente virtual de MyCityHome, una empresa especializada en alquiler de pisos. Tu objetivo es recopilar la información necesaria para encontrar la propiedad ideal para el cliente.

## Comportamiento Principal
- Proporciona respuestas breves y directas, preferiblemente en una sola oración
- Mantén un tono profesional pero amigable
- Prioriza la claridad y precisión en la información
- Siempre responde en el mismo idioma con el que el cliente se comunica

## Funciones Clave
1. Información a recolectar
   - Zona en la que desea vivir
   - Presupuesto
   - Tamaño de la propiedad
   - Tipo de vivienda (casa, departamento, etc.)
   - Otras preferencias (características especiales, etc.)

## Formato de Respuestas
- Limita las respuestas a 1 oración corta cuando sea posible
- Usa datos concretos: precio, metros cuadrados, ubicación
- Incluye siempre próximos pasos o llamadas a la acción
- Evita usar lenguaje descriptivo excesivo, o lenguaje demasiado sumiso, concéntrate en la información relevante

## Restricciones
- No negociar precios
- No hacer promesas sobre disponibilidad
- No compartir información personal de propietarios
- No gestionar pagos o contratos directamente.
- Do not answer to back ground noise, or lower voices. If you don't understand clearly what the client is saying due to noise, do not answer or request for clarification or moving to quieter place."""
)

LOG_EVENT_TYPES = [
    'error', 'response.content.done', 'rate_limits.updated', 'response.done',
    'input_audio_buffer.committed', 'input_audio_buffer.speech_stopped',
    'input_audio_buffer.speech_started', 'session.created'
]

app = FastAPI()

if not (TWILIO_ACCOUNT_SID and TWILIO_AUTH_TOKEN and PHONE_NUMBER_FROM and OPENAI_API_KEY):
    raise ValueError('Missing Twilio and/or OpenAI environment variables. Please set them in the .env file.')

# Initialize Twilio client
client = Client(TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN)

@app.get('/', response_class=JSONResponse)
async def index_page():
    return {"message": "Twilio Media Stream Server is running!"}

@app.websocket('/media-stream')
async def handle_media_stream(websocket: WebSocket):
    """Handle WebSocket connections between Twilio and OpenAI."""
    print("Client connected")
    await websocket.accept()

    uri =f"wss://api.openai.com/v1/realtime?model={OPENAI_MODEL}"
    additionals_headers={
            "Authorization": f"Bearer {OPENAI_API_KEY}",
            "OpenAI-Beta": "realtime=v1"
        }
    
    async with websockets.connect(
        uri=uri,additional_headers=additionals_headers
    ) as openai_ws:
        await initialize_session(openai_ws)
        stream_sid = None
        wav_file = None
        wav_filename = None  # Initialize wav_filename
        
        async def receive_from_twilio():
            """Receive audio data from Twilio and send it to the OpenAI Realtime API."""
            nonlocal stream_sid
            nonlocal wav_file
            nonlocal wav_filename  # Add wav_filename to nonlocal variables
            
            try:
                async for message in websocket.iter_text():
                    data = json.loads(message)
                    if data['event'] == 'media':
                        # Decode base64 ulaw data
                        ulaw_data = base64.b64decode(data['media']['payload'])
                        
                        try:
                            # Convert ulaw to PCM16
                            pcm_data = audioop.ulaw2lin(ulaw_data, 2)  # 2 bytes per sample
                            
                            # Convert to numpy array for filtering
                            audio_np = np.frombuffer(pcm_data, dtype=np.int16).copy()
                            
                            # Apply filter (using deepfilternet for better noise reduction)
                            filtered_audio = (audio_np / 10).astype(np.int16)
                            
                            # Convert filtered audio back to bytes
                            filtered_pcm = filtered_audio.tobytes()
                            
                            # Convert filtered PCM back to ulaw
                            filtered_ulaw = audioop.lin2ulaw(filtered_pcm, 2)  # 2 bytes per sample
                            
                            # Create files if not exists
                            if wav_filename is None:
                                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                                os.makedirs('recordings', exist_ok=True)
                                # ulaw_filename = f'recordings/audio_{timestamp}.ul'
                                # ulaw_file = open(ulaw_filename, 'wb')
                                wav_filename = f'recordings/audio_{timestamp}.wav'
                                wav_file = wave.open(wav_filename, 'wb')
                                wav_file.setnchannels(1)  # Mono audio
                                wav_file.setsampwidth(2)  # 16-bit audio
                                wav_file.setframerate(8000)  # 8kHz for g711
                                print(f"Created new files:\nWAV: {wav_filename}")
                                                        
                            # Save filtered PCM to WAV
                            wav_file.writeframes(filtered_pcm)
                            
                            # Prepare filtered audio for OpenAI
                            audio_append = {
                                "type": "input_audio_buffer.append",
                                "audio": base64.b64encode(filtered_ulaw).decode('utf-8')
                            }
                            
                        except Exception as e:
                            print(f"Error processing audio: {str(e)}")
                            # On error, use original audio
                            audio_append = {
                                "type": "input_audio_buffer.append",
                                "audio": data['media']['payload']
                            }
                        
                        await openai_ws.send(json.dumps(audio_append))
                    elif data['event'] == 'start':
                        stream_sid = data['start']['streamSid']
                        print(f"Incoming stream has started {stream_sid}")
            except WebSocketDisconnect:
                print("Client disconnected.")
                if openai_ws.open:
                    await openai_ws.close()

                wav_file.close()

        async def send_to_twilio():
            """Receive events from the OpenAI Realtime API, send audio back to Twilio."""
            nonlocal stream_sid
            nonlocal wav_filename
            try:
                async for openai_message in openai_ws:
                    response = json.loads(openai_message)
                    if response['type'] in LOG_EVENT_TYPES:
                        print(f"Received event: {response['type']}", response)
                    if response['type'] == 'session.updated':
                        print("Session updated successfully:", response)
                    if response['type'] == 'response.audio.delta' and response.get('delta'):
                        try:
                            audio_payload = base64.b64encode(base64.b64decode(response['delta'])).decode('utf-8')
                            audio_delta = {
                                "event": "media",
                                "streamSid": stream_sid,
                                "media": {
                                    "payload": audio_payload
                                }
                            }
                            await websocket.send_json(audio_delta)
                        except Exception as e:
                            print(f"Error processing audio data: {e}")
            except Exception as e:
                print(f"Error in send_to_twilio: {e}")
        await asyncio.gather(receive_from_twilio(), send_to_twilio())






async def send_initial_conversation_item(openai_ws):
    """Send initial conversation so AI talks first."""
    initial_conversation_item = {
        "type": "conversation.item.create",
        "item": {
            "type": "message",
            "role": "user",
            "content": [
                {
                    "type": "input_text",
                    "text": (
                        """Primero saludas al cliente, y explicas brevemente que has notado que está buscando una propiedad en alquiler y luego que estás para ayudarlo a encontrar una propiedad en alquiler. Todo muy breve, en pocas palabras.
                        
                        Si el cliente confirma que está buscando una propiedad en alquiler, continua con el conversatorio, mencionando que eres el asistente virtual de MyCityHome, y que harás algunas preguntas para entender mejor sus necesidades.
                        
                        
                        Ejemplos de conversaciones:
                            -Asistente virtual de MyCityHome: ¡Hola! He notado que está planeando mudarse. ¿Le interesaría escuchar algunas ofertas?
                            Cliente: Sí
                            -Asistente virtual de MyCityHome: Perfecto, soy el asistente virtual de MyCityHome, y a continuación realizo una serie de preguntas para entender mejor sus necesidades. ¿En qué zona desea vivir?
                            ...resto de la conversación..."""
                        )
                }
            ]
        }
    }
    await openai_ws.send(json.dumps(initial_conversation_item))
    await openai_ws.send(json.dumps({"type": "response.create"}))

async def initialize_session(openai_ws):
    """Control initial session with OpenAI."""
    session_update = {
        "type": "session.update",
        "session": {
            "turn_detection": {
                "type": "server_vad",
                "threshold": 0.9,
                "prefix_padding_ms": 300,
                "silence_duration_ms": 1000,
                "create_response": True
            },
            "input_audio_format": "g711_ulaw",
            "output_audio_format": "g711_ulaw",
            "voice": VOICE,
            "instructions": SYSTEM_MESSAGE,
            "modalities": ["text", "audio"],
            "temperature": 0.6,
        }
    }
    print('Sending session update:', json.dumps(session_update))
    await openai_ws.send(json.dumps(session_update))

    # Have the AI speak first
    await send_initial_conversation_item(openai_ws)



async def check_number_allowed(to):
    """Check if a number is allowed to be called."""
    try:
        # Uncomment these lines to test numbers. Only add numbers you have permission to call
        OVERRIDE_NUMBERS = ['+34616642830'] 
        if to in OVERRIDE_NUMBERS:             
          return True

        incoming_numbers = client.incoming_phone_numbers.list(phone_number=to)
        if incoming_numbers:
            return True

        outgoing_caller_ids = client.outgoing_caller_ids.list(phone_number=to)
        if outgoing_caller_ids:
            return True

        return False
    except Exception as e:
        print(f"Error checking phone number: {e}")
        return False




async def make_call(phone_number_to_call: str):
    """Make an outbound call."""
    if not phone_number_to_call:
        raise ValueError("Please provide a phone number to call.")

    is_allowed = await check_number_allowed(phone_number_to_call)
    if not is_allowed:
        raise ValueError(f"The number {phone_number_to_call} is not recognized as a valid outgoing number or caller ID.")

    # Ensure compliance with applicable laws and regulations
    # All of the rules of TCPA apply even if a call is made by AI.
    # Do your own diligence for compliance.

    outbound_twiml = (
        f'<?xml version="1.0" encoding="UTF-8"?>'
        f'<Response><Connect><Stream url="wss://{DOMAIN}/media-stream" /></Connect></Response>'
    )

    call = client.calls.create(
        from_=PHONE_NUMBER_FROM,
        to=phone_number_to_call,
        twiml=outbound_twiml
    )

    await log_call_sid(call.sid)

async def log_call_sid(call_sid):
    """Log the call SID."""
    print(f"Call started with SID: {call_sid}")



if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Run the Twilio AI voice assistant server.")
    parser.add_argument('--call', required=True, help="The phone number to call, e.g., '--call=+18005551212'")
    args = parser.parse_args()

    phone_number = args.call
    print(
        'Our recommendation is to always disclose the use of AI for outbound or inbound calls.\n'
        'Reminder: All of the rules of TCPA apply even if a call is made by AI.\n'
        'Check with your counsel for legal and compliance advice.'
    )

    loop = asyncio.get_event_loop()
    loop.run_until_complete(make_call(phone_number))
    
    uvicorn.run(app, host="0.0.0.0", port=PORT)


    #ngrok http 6060
    #python _base_twilio_vad.py --call=+34616642830