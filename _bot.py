import os
import json
import base64
import asyncio
from fastapi import FastAPI, WebSocket, Query
from fastapi.responses import JSONResponse
from fastapi.websockets import WebSocketDisconnect
from twilio.rest import Client
import websockets
from dotenv import load_dotenv
import uvicorn
import re
import os
import yaml
import copy
import ngrok
import traceback
import time

from audio_processing import process_input_audio, process_output_audio, AudioRecorder
from bot_initialization import initialize_session

load_dotenv(override=True)

# Load environment variables from .env file
TWILIO_ACCOUNT_SID = os.getenv('TWILIO_ACCOUNT_SID')
TWILIO_AUTH_TOKEN = os.getenv('TWILIO_AUTH_TOKEN')
PHONE_NUMBER_FROM = os.getenv('PHONE_NUMBER_FROM')

CALL_DURATION_LIMIT = int(os.getenv('CALL_DURATION_LIMIT', 120))

OPENAI_API_KEY = os.getenv('OPENAI_API_KEY')
VOICE = os.getenv('OPENAI_AUDIO_VOICE', 'coral')
OPENAI_REALTIME_MODEL = os.getenv('OPENAI_REALTIME_MODEL', 'gpt-4o-mini-realtime-preview-2024-12-17')
NGROK_TOKEN = os.getenv('NGROK_TOKEN', None)
PORT = int(os.getenv('PORT', 6060))

# initialize ngrok listener
listener = ngrok.forward(PORT, authtoken=NGROK_TOKEN)
raw_domain = listener.url()

if raw_domain is None:
    input("Error: NGROK_DOMAIN is not set. Press any key to exit...")    
    exit(1)
else:
    print("NGROK_DOMAIN: ", raw_domain)

DOMAIN = re.sub(r'(^\w+:|^)\/\/|\/+$', '', raw_domain) # Strip protocols and trailing slashes from DOMAIN

print("System data loaded from .env file:")
print(f"TWILIO_ACCOUNT_SID: {TWILIO_ACCOUNT_SID[:6]}{(len(TWILIO_ACCOUNT_SID) - 6) * '*'}")
print(f"TWILIO_AUTH_TOKEN: {TWILIO_AUTH_TOKEN[:6]}{(len(TWILIO_AUTH_TOKEN) - 6) * '*'}")
print(f"PHONE_NUMBER_FROM: {PHONE_NUMBER_FROM}")
print(f"OPENAI_API_KEY: {OPENAI_API_KEY[:6]}{(len(OPENAI_API_KEY) - 6) * '*'}")
print(f"VOICE: {VOICE}")
print(f"OPENAI_MODEL: {OPENAI_REALTIME_MODEL}")
print(f"NGROK_TOKEN: {NGROK_TOKEN[:6]}{(len(NGROK_TOKEN) - 6) * '*'}")
print(f"DOMAIN: {DOMAIN}")
print(f"PORT: {PORT}")
print()

LOG_EVENT_TYPES = [
    'error', 'response.content.done', 'rate_limits.updated', 'response.done',
    'input_audio_buffer.committed', 'input_audio_buffer.speech_stopped',
    'input_audio_buffer.speech_started', 'session.created'
]


# loads the system message from the yaml file in the AI/prompts directory
def load_system_message():
    yaml_path = os.path.join(os.path.dirname(__file__), 'AI', 'prompts', 'voice_bot_prompts.yaml')

    with open(yaml_path, 'r', encoding='utf-8') as file:
        system_config = yaml.safe_load(file)
        return system_config['system_prompt']['content']

SYSTEM_MESSAGE = load_system_message()

# print("SYSTEM_MESSAGE: ", SYSTEM_MESSAGE)

app = FastAPI()

if not (TWILIO_ACCOUNT_SID and TWILIO_AUTH_TOKEN and PHONE_NUMBER_FROM and OPENAI_API_KEY):
    raise ValueError('Missing Twilio and/or OpenAI environment variables. Please set them in the .env file.')

# Initialize Twilio client
client = Client(TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN)
# Shared state for calls

calls = []

@app.get('/', response_class=JSONResponse)
async def index_page():
    return {"message": "Twilio Media Stream Server is running!"}

@app.post('/make_call')
async def initiate_call(phone_number: str = Query(...)):
    global calls
    """
    Endpoint to make a call to a single phone number and wait for result.
    
    :param phone_number: Phone number to call (as a query parameter)
    :return: JSON response with call details
    """
    try:        
        # Make the call
        outbound_twiml = (
            f'<?xml version="1.0" encoding="UTF-8"?>'
            f'<Response><Connect><Stream url="wss://{DOMAIN}/media-stream" /></Connect></Response>'
        )

        call = client.calls.create(
            from_=PHONE_NUMBER_FROM,
            to=phone_number,
            twiml=outbound_twiml
        )

        my_call = {
            "call_sid": call.sid,
            "phone_number": phone_number,
            "call_status": "in_progress"
        }
        calls.append(my_call)
        
        # Initialize the result for this call
        
        # Wait for the result (with a timeout)
        for _ in range(600):  # 1 minute timeout
            await asyncio.sleep(1)
            current_call = None
            for _call in calls:
                if _call['call_sid'] == call.sid:
                    current_call = _call

            if current_call:
                if current_call['call_status'] == 'completed' or current_call['call_status'] == 'failed' or current_call['call_status'] == 'busy' or current_call['call_status'] == 'canceled':
                    result = copy.deepcopy(current_call)
                    calls.remove(current_call)
                    return JSONResponse(content=result)
            
            else:
                break
        
        # Timeout occurred

        return JSONResponse(content={
            "error": "Call result timeout",
            "call_sid": call.sid,
        }, status_code=408)
    
    except Exception as e:
        traceback.print_exc()
        return JSONResponse(content={
            "error": str(e)
        }, status_code=500)

@app.websocket('/media-stream')
async def handle_media_stream(websocket: WebSocket):
    global calls
    """Handle WebSocket connections between Twilio and OpenAI."""
    print("Client connected")
    await websocket.accept()

    uri =f"wss://api.openai.com/v1/realtime?model={OPENAI_REALTIME_MODEL}"
    additionals_headers={
            "Authorization": f"Bearer {OPENAI_API_KEY}",
            "OpenAI-Beta": "realtime=v1"
        }
    
    call_init_time = time.time()
    call_end_time = None
    call_end_called = False
    audio_recorder = AudioRecorder()
    stream_sid = None
    input_wav_file = None
    output_wav_file = None
    wav_filename = None  # Initialize wav_filename
    current_call = None
    global calls
    
    async with websockets.connect(
        uri=uri,additional_headers=additionals_headers
    ) as openai_ws:
        # here starts the openai session, and sents the system message and the first message to the user
        await initialize_session(openai_ws, VOICE, SYSTEM_MESSAGE)
        
        async def receive_from_twilio():
            """Receive audio data from Twilio and send it to the OpenAI Realtime API."""
            nonlocal stream_sid, input_wav_file, wav_filename, output_wav_file, current_call, call_init_time, call_end_called, call_end_time
            
            try:
                
                async for message in websocket.iter_text():
                    if call_end_time is not None:
                        if time.time() - call_end_time >= 5:                            
                            client.calls(current_call['call_sid']).update(status="completed")
                            current_call['call_status'] = "completed"

                    # check if the call has exceeded the duration limit
                    if CALL_DURATION_LIMIT > 0 and not call_end_called and time.time() - call_init_time >= CALL_DURATION_LIMIT:
                        final_conversation_item = {
                                                    "type": "conversation.item.create",
                                                    "item": {
                                                        "type": "message",
                                                        "role": "assistant",
                                                        "content": [
                                                            {
                                                                "type": "text",
                                                                "text": "Discúlpate, explica al cliente que el tiempo de llamada ha terminado, que un miembro de nuestro equipo se comunicará con él, y usa la herramienta 'end_call' para terminar la llamada."
                                                            }
                                                        ]
                                                    }
                                                }
                        await openai_ws.send(json.dumps(final_conversation_item))
                        await openai_ws.send(json.dumps({"type": "response.create"}))
                        call_end_called = True
                    
                    if current_call:
                        current_call['call_duration'] = time.time() - call_init_time

                    # get messages at the socket connected to Twilio, it will have all the audio streams from the user
                    data = json.loads(message)

                    # Detect call end event
                    if data['event'] == 'stop':
                        print("Call stopped by Twilio")
                        current_call['call_status'] = "completed"

                        return  # Exit the coroutine

                    #verify if the message is a media event, which means, that the message is an audio stream
                    if data['event'] == 'media':

                        # Decode base64 ulaw data, the code by default uses g711_ulaw encoding for voice audio
                        ulaw_data = base64.b64decode(data['media']['payload'])
                        
                        # Process the audio data, in process_input_audio function you can add new filter features 
                        # if required, also handle the wav file creation to record the input audio, for later processing
                        # and use.
                        audio_append, wav_filename, input_wav_file = process_input_audio(ulaw_data, audio_recorder, wav_filename, input_wav_file, phone_number=current_call['phone_number'])
                        
                        # Send the processed audio data to the OpenAI Realtime API
                        sent = False
                        count = 0
                        while not sent and count < 3:
                            try:
                                count += 1
                                await openai_ws.send(json.dumps(audio_append))
                                sent = True
                                break
                            except Exception as e:
                                traceback.print_exc()
                                await asyncio.sleep(0.2)
                                print(f"Error sending audio data: {e}")
                                
                        if not sent:
                            print("Failed to send audio data after 3 attempts")
                            raise Exception("Failed to send audio data after 3 attempts")
                    
                    # Handle the 'start' event, this occurs when the Twilio client starts the stream
                    elif data['event'] == 'start':
                        stream_sid = data['start']['streamSid']
                        call_sid = data['start']['callSid']

                        for _call in calls:
                            if _call['call_sid'] == call_sid:
                                current_call = _call

                        if current_call:
                            current_call['stream_sid'] = stream_sid
                        else:
                            raise Exception("Call not found")
            
            # Handle disconnections, directly by handling the WebSocketDisconnect exception
            except WebSocketDisconnect:
                traceback.print_exc()
                print("Client disconnected.")
                current_call['call_status'] = "disconnected"

            except Exception as e:
                traceback.print_exc()
                print(f"Error in receive_from_twilio: {e}")
                current_call['call_status'] = "disconnected"

            finally:
                # Close the WebSocket connection to OpenAI
                try:
                    await openai_ws.close()                

                except Exception as e:
                    traceback.print_exc()
                    print(f"Error closing OpenAI WebSocket: {e}")

                # Close the WAV file to properly terminate recording
                if input_wav_file:
                    input_wav_file.close()
                if output_wav_file:
                    output_wav_file.close()

                wav_filename = None
                output_wav_file = None
                input_wav_file = None

        async def send_to_twilio():
            """Receive events from the OpenAI Realtime API, send audio back to Twilio."""
            nonlocal stream_sid, output_wav_file, wav_filename, current_call, call_end_time
            try:
                #similar to the receive_from_twilio function, this function will receive the events from the OpenAI Realtime API
                # and send the audio back to Twilio
                async for openai_message in openai_ws:
                    response = json.loads(openai_message)

                    #log the events
                    if response['type'] in LOG_EVENT_TYPES:
                        print(f"Received event: {response['type']}", response)

                    #log the session updates
                    if response['type'] == 'session.updated':
                        print("Session updated successfully:", response)

                    #handle the audio delta events, this events contain the audio data
                    if response['type'] == 'response.audio.delta' and response.get('delta'):
                        try:
                            # Process the output audio and save to WAV
                            audio_delta, wav_filename, output_wav_file = process_output_audio(
                                response['delta'], 
                                audio_recorder,
                                wav_filename, 
                                output_wav_file, 
                                stream_sid=stream_sid,
                                phone_number=current_call['phone_number']
                            )
                            current_call['audio_file_name'] = wav_filename
                            
                            # Send the audio delta back to Twilio
                            if audio_delta:
                                await websocket.send_json(audio_delta)

                        except Exception as e:
                            traceback.print_exc()
                            print(f"Error processing audio data: {e}")                        

                    if response['type'] == 'response.done':
                        # print()
                        # print("Response Output")
                        response_output = response["response"].get('output', None)
                        # print("response_output ", response_output)
                        # print()

                        if response_output:
                                       
                            for ro in response_output:
                                is_tool_call = ro.get('type', '') == 'function_call'

                                # print()
                                # print("is_tool_call ", is_tool_call)
                                if is_tool_call:
                                    # Handle the function call
                                    tool_name = ro['name']
                                    tool_args = ro['arguments']
                                    tool_call_id = ro['call_id']

                                    print()
                                    print("tool_name ", tool_name)
                                    print("tool_args ", tool_args)
                                    print("tool_call_id ", tool_call_id)

                                    if tool_name == 'end_call':
                                        try:
                                            # trigger Good Bye message to the user
                                            final_conversation_item = {
                                                "type": "conversation.item.create",
                                                "item": {
                                                    "type": "message",
                                                    "role": "assistant",
                                                    "content": [
                                                        {
                                                            "type": "text",
                                                            "text": "Despídete del cliente cordialmente."
                                                        }
                                                    ]
                                                }
                                            }
                                            await openai_ws.send(json.dumps(final_conversation_item))
                                            await openai_ws.send(json.dumps({"type": "response.create"}))
                                            call_end_time = time.time()
                                            

                                        except Exception as end_call_error:
                                            traceback.print_exc()
                                            print(f"Error ending call: {end_call_error}")

            except Exception as e:
                traceback.print_exc()
                print(f"Error in send_to_twilio: {e}")
                current_call['call_status'] = "disconnected"


        try:
            # Run the asyncio event loop, to continuously communicate with Twilio and OpenAI
            await asyncio.gather(receive_from_twilio(), send_to_twilio())

        except Exception as global_error:
            traceback.print_exc()
            print(f"Unexpected global error in handle_media_stream: {global_error}")
                        
            current_call['call_status'] = "disconnected"
            
            # Re-raise the error if needed for further handling
            raise

        finally:
            # Ensure call is ended and resources are cleaned up
            try:
                # if call_sid:
                #     client.calls(call_sid).update(status="completed")
                pass
            except Exception as final_end_call_error:
                traceback.print_exc()
                print(f"Final error ending call: {final_end_call_error}")

            # Ensure all files are closed
            if input_wav_file:
                input_wav_file.close()
            if output_wav_file:
                output_wav_file.close()

            wav_filename = None
            output_wav_file = None
            input_wav_file = None

            # Ensure WebSocket connections are closed
            try:
                await websocket.close()
            except Exception as ws_close_error:
                traceback.print_exc()
                print(f"Error closing WebSocket: {ws_close_error}")

        current_call['call_status'] = "disconnected"


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
        traceback.print_exc()
        print(f"Error checking phone number: {e}")
        return False


# async def make_call(phone_number_to_call: str):
#     """Make an outbound call."""
#     if not phone_number_to_call:
#         raise ValueError("Please provide a phone number to call.")

#     is_allowed = await check_number_allowed(phone_number_to_call)
#     if not is_allowed:
#         raise ValueError(f"The number {phone_number_to_call} is not recognized as a valid outgoing number or caller ID.")

#     # Ensure compliance with applicable laws and regulations
#     # All of the rules of TCPA apply even if a call is made by AI.
#     # Do your own diligence for compliance.

#     outbound_twiml = (
#         f'<?xml version="1.0" encoding="UTF-8"?>'
#         f'<Response><Connect><Stream url="wss://{DOMAIN}/media-stream" /></Connect></Response>'
#     )

#     call = client.calls.create(
#         from_=PHONE_NUMBER_FROM,
#         to=phone_number_to_call,
#         twiml=outbound_twiml
#     )

#     await log_call_sid(call.sid)

async def log_call_sid(call_sid):
    """Log the call SID."""
    print(f"Call started with SID: {call_sid}")


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=PORT)


    #ngrok http 6060
    #python _base_twilio_vad.py --call=+34616642830
    #powershell Invoke-RestMethod -Method Post -Uri "http://localhost:6060/make_call?phone_number=+1234567890"
    #cmd curl -X "POST" "http://localhost:6060/make_call?phone_number=%2B34616642830"