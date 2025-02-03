import os
import json
import base64
import asyncio
import websockets
from typing import Any
from dotenv import load_dotenv
import wave
import numpy as np
from audio_filter import filter_audio
import audioop
import pyaudio
from datetime import datetime

load_dotenv(override=True)

# Configuration
OPENAI_API_KEY = os.getenv('OPENAI_API_KEY')
VOICE = os.getenv('OPENAI_AUDIO_VOICE', 'coral')
OPENAI_MODEL = os.getenv('OPENAI_MODEL', 'gpt-4o-mini-realtime-preview-2024-12-17')

print(f"OPENAI_API_KEY: {OPENAI_API_KEY}")
print(f"VOICE: {VOICE}")
print(f"OPENAI_MODEL: {OPENAI_MODEL}")

input("Press Enter to continue...")

SYSTEM_MESSAGE = (
    """# Prompt de Sistema - Asistente MyCityHome

Eres el asistente virtual de MyCityHome, una empresa especializada en alquiler de pisos. Tu objetivo es ayudar a los clientes a encontrar la propiedad ideal de manera eficiente. Habla en idioma Ruso.

## Comportamiento Principal
- Proporciona respuestas breves y directas, preferiblemente en una sola oración
- Mantén un tono profesional pero amigable
- Prioriza la claridad y precisión en la información
- Siempre responde en el mismo idioma con el que el cliente se comunica

## Funciones Clave
1. Consulta de Propiedades
   - Solicita requisitos específicos: presupuesto, zona, tamaño
   - Confirma detalles importantes antes de hacer recomendaciones
   - Presenta opciones de forma concisa

2. Gestión de Consultas
   - Responde preguntas sobre el proceso de alquiler
   - Informa sobre documentación necesaria
   - Deriva a un agente humano cuando sea necesario

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


# Audio stream configuration
CHUNK = 1024
FORMAT = pyaudio.paInt16
CHANNELS = 1
RATE = 8000
DEVICE_INDEX = None  # Will be set dynamically

async def handle_media_stream(websocket: Any):
    """Handle WebSocket connections between Twilio and OpenAI."""
    global DEVICE_INDEX
    print("Client connected")
    await websocket.accept()

    # Select input device if not already selected
    if DEVICE_INDEX is None:
        p = pyaudio.PyAudio()
        print("\nAvailable Input Devices:")
        for i in range(p.get_device_count()):
            dev_info = p.get_device_info_by_index(i)
            if dev_info.get('maxInputChannels') > 0:  # Only show input devices
                print(f"Device {i}: {dev_info.get('name')}")
        
        # Default to first input device if not manually selected
        DEVICE_INDEX = 0
        for i in range(p.get_device_count()):
            if p.get_device_info_by_index(i).get('maxInputChannels') > 0:
                DEVICE_INDEX = i
                break
        p.terminate()

    uri = f"wss://api.openai.com/v1/realtime?model={OPENAI_MODEL}"
    additionals_headers = {
        "Authorization": f"Bearer {OPENAI_API_KEY}",
        "OpenAI-Beta": "realtime=v1"
    }
    
    async with websockets.connect(
        uri=uri, additional_headers=additionals_headers
    ) as openai_ws:
        await initialize_session(openai_ws)
        stream_sid = None
        audio_buffer = []
        wav_file = None
        ulaw_file = None
        pyaudio_stream = None
        
        try:
            p = pyaudio.PyAudio()
            pyaudio_stream = p.open(
                format=FORMAT,
                channels=CHANNELS,
                rate=RATE,
                input=True,
                input_device_index=DEVICE_INDEX,
                frames_per_buffer=CHUNK
            )
            
            async def receive_from_local_mic():
                """Receive audio data from local microphone and send to OpenAI Realtime API."""
                nonlocal stream_sid, wav_file, ulaw_file
                
                try:
                    while pyaudio_stream.is_active():
                        # Read audio chunk from microphone
                        in_data = pyaudio_stream.read(CHUNK)
                        
                        # Convert input bytes to numpy array
                        audio_np = np.frombuffer(in_data, dtype=np.int16).copy()
                        
                        # Apply filter (optional)
                        # filtered_audio = filter_audio(audio_np, filter_name='deepfilternet')
                        filtered_audio = audio_np.copy()
                        
                        # Convert filtered audio back to bytes
                        filtered_pcm = filtered_audio.tobytes()
                        
                        # Convert filtered PCM to ulaw
                        filtered_ulaw = audioop.lin2ulaw(filtered_pcm, 2)  # 2 bytes per sample
                        
                        # Create files if not exists
                        if ulaw_file is None:
                            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                            os.makedirs('recordings', exist_ok=True)
                            ulaw_filename = f'recordings/audio_{timestamp}.ul'
                            ulaw_file = open(ulaw_filename, 'wb')
                            wav_filename = f'recordings/audio_{timestamp}.wav'
                            wav_file = wave.open(wav_filename, 'wb')
                            wav_file.setnchannels(1)  # Mono audio
                            wav_file.setsampwidth(2)  # 16-bit audio
                            wav_file.setframerate(RATE)
                            print(f"Created new files:\nULAW: {ulaw_filename}\nWAV: {wav_filename}")
                        
                        # Save original ulaw data
                        ulaw_file.write(filtered_ulaw)
                        
                        # Save filtered PCM to WAV
                        wav_file.writeframes(filtered_pcm)
                        
                        # Prepare filtered audio for OpenAI
                        audio_append = {
                            "type": "input_audio_buffer.append",
                            "audio": base64.b64encode(filtered_ulaw).decode('utf-8')
                        }
                        
                        await openai_ws.send(json.dumps(audio_append))
                        
                        # Optional: Add a small delay to prevent overwhelming the system
                        await asyncio.sleep(0.01)
                        
                except Exception as e:
                    print(f"Error processing local audio: {str(e)}")
                    
            async def send_to_twilio():
                """Receive events from the OpenAI Realtime API, send audio back."""
                nonlocal stream_sid
                try:
                    async for openai_message in openai_ws:
                        response = json.loads(openai_message)
                        if response['type'] in LOG_EVENT_TYPES:
                            print(f"Received event: {response['type']}", response)
                        if response['type'] == 'session.updated':
                            print("Session updated successfully:", response)
                        if response['type'] == 'response.audio.delta' and response.get('delta'):
                            try:
                                # Optional: Play audio through system speakers
                                audio_payload = base64.b64decode(response['delta'])
                                # You could add code here to play audio through system speakers
                                print("Received audio response from OpenAI")
                            except Exception as e:
                                print(f"Error processing audio data: {e}")
                except Exception as e:
                    print(f"Error in send_to_twilio: {e}")
            
            await asyncio.gather(receive_from_local_mic(), send_to_twilio())
            
        except Exception as e:
            print(f"Error in handle_media_stream: {e}")
        finally:
            if pyaudio_stream:
                pyaudio_stream.stop_stream()
                pyaudio_stream.close()
            if wav_file:
                wav_file.close()
            if ulaw_file:
                ulaw_file.close()
            p.terminate()







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
                        """# Instrucciones de Presentación

Al iniciar cada interacción con un cliente, deberás:

1. Presentación Personal
   - Identifícate como el asistente virtual de MyCityHome
   - Usa un tono profesional pero cercano
   - No uses nombres propios ni te presentes con un nombre específico

2. Explicación de Rol
   - Menciona brevemente que eres el asistente virtual de MyCityHome, y consulta con el cliente si necesita ayuda
   - Enfatiza que tu función es ayudar a encontrar propiedades en alquiler

3. Objetivo de la Conversación
   - Indica que tu objetivo es ayudarles a encontrar la propiedad ideal
   - Menciona que harás algunas preguntas para entender mejor sus necesidades
   - Finaliza con una pregunta sobre el tipo de propiedad que buscan

5. Reglas Importantes
   - Mantén la presentación breve y directa
   - No hagas promesas sobre resultados específicos
   - Evita lenguaje técnico o complicado
   - Siempre termina con una pregunta que invite al diálogo.
   - Siempre que el usuario responda una pregunta, primero repite su respuesta para que el cliente esté  al tanto de si entendiste bien.
   - Intenta mantener las respuestas cortas y directas, para evitar sobrecarga."""
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
                "threshold": 0.5,
                "prefix_padding_ms": 300,
                "silence_duration_ms": 750,
                "create_response": True
            },
            "input_audio_format": "g711_ulaw",
            "output_audio_format": "g711_ulaw",
            "voice": VOICE,
            "instructions": SYSTEM_MESSAGE,
            "modalities": ["text", "audio"],
            "temperature": 0.8,
        }
    }
    print('Sending session update:', json.dumps(session_update))
    await openai_ws.send(json.dumps(session_update))

    # Have the AI speak first
    await send_initial_conversation_item(openai_ws)








async def main():
    """Main async function to run the media stream."""
    
    # Keep the server running
    await server.wait_closed()

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\nWebSocket server stopped by user.")
