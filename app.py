import os
import json
import base64
import asyncio
import argparse
from fastapi import FastAPI, WebSocket, BackgroundTasks, Query
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

from audio_processing import process_input_audio, process_output_audio
from bot_initialization import initialize_session


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
OPENAI_REALTIME_MODEL = os.getenv('OPENAI_REALTIME_MODEL', 'gpt-4o-mini-realtime-preview-2024-12-17')

PORT = int(os.getenv('PORT', 6060))

print(f"TWILIO_ACCOUNT_SID: {TWILIO_ACCOUNT_SID}")
print(f"TWILIO_AUTH_TOKEN: {TWILIO_AUTH_TOKEN}")
print(f"PHONE_NUMBER_FROM: {PHONE_NUMBER_FROM}")
print(f"OPENAI_API_KEY: {OPENAI_API_KEY}")
print(f"DOMAIN: {DOMAIN}")
print(f"VOICE: {VOICE}")
print(f"OPENAI_MODEL: {OPENAI_REALTIME_MODEL}")
print(f"PORT: {PORT}")

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
call_results = {}
call_sid = None

@app.get('/', response_class=JSONResponse)
async def index_page():
    return {"message": "Twilio Media Stream Server is running!"}



@app.post('/make_call')
async def initiate_call(phone_number: str = Query(...)):
    global call_sid
    """
    Endpoint to make a call to a single phone number and wait for result.
    
    :param phone_number: Phone number to call (as a query parameter)
    :return: JSON response with call details
    """
    try:
        # Validate the phone number
        is_allowed = await check_number_allowed(phone_number)
        if not is_allowed:
            return JSONResponse(content={
                "error": f"The number {phone_number} is not recognized as a valid outgoing number or caller ID."
            }, status_code=400)
        
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
        
        # Log the call SID
        await log_call_sid(call.sid)
        call_sid = call.sid
        
        # Initialize the result for this call
        
        # Wait for the result (with a timeout)
        for _ in range(600):  # 1 minute timeout
            await asyncio.sleep(1)
            # print(call_results)
            if call_results:
                result = copy.deepcopy(call_results)
                call_results.clear()
                return JSONResponse(content={
                    "message": "Call completed",
                    "phone_number": phone_number,
                    "result": result
                })
        
        # Timeout occurred

        return JSONResponse(content={
            "error": "Call result timeout",
            "call_sid": call.sid
        }, status_code=408)
    
    except Exception as e:
        return JSONResponse(content={
            "error": str(e)
        }, status_code=500)

@app.websocket('/media-stream')
async def handle_media_stream(websocket: WebSocket):
    global call_sid
    """Handle WebSocket connections between Twilio and OpenAI."""
    print("Client connected")
    await websocket.accept()

    uri =f"wss://api.openai.com/v1/realtime?model={OPENAI_REALTIME_MODEL}"
    additionals_headers={
            "Authorization": f"Bearer {OPENAI_API_KEY}",
            "OpenAI-Beta": "realtime=v1"
        }
    
    stream_sid = None
    input_wav_file = None
    output_wav_file = None
    wav_filename = None  # Initialize wav_filename
    end_call = False
    global call_results
    global call_sid
    
    async with websockets.connect(
        uri=uri,additional_headers=additionals_headers
    ) as openai_ws:
        # here starts the openai session, and sents the system message and the first message to the user
        await initialize_session(openai_ws, VOICE, SYSTEM_MESSAGE)
        
        async def receive_from_twilio():
            """Receive audio data from Twilio and send it to the OpenAI Realtime API."""
            nonlocal stream_sid, input_wav_file, wav_filename, output_wav_file, end_call
            global call_sid
            
            try:
                async for message in websocket.iter_text():
                    # get messages at the socket connected to Twilio, it will have all the audio streams from the user
                    data = json.loads(message)

                    # Detect call end event
                    if data['event'] == 'stop':
                        print("Call stopped by Twilio")
                        call_results.update({
                            "status": "completed",
                            "stream_sid": stream_sid
                        })
                        return  # Exit the coroutine

                    #verify if the message is a media event, which means, that the message is an audio stream
                    if data['event'] == 'media':
                        # Decode base64 ulaw data, the code by default uses g711_ulaw encoding for voice audio
                        ulaw_data = base64.b64decode(data['media']['payload'])
                        
                        # Process the audio data, in process_input_audio function you can add new filter features 
                        # if required, also handle the wav file creation to record the input audio, for later processing
                        # and use.
                        audio_append, wav_filename, input_wav_file = process_input_audio(ulaw_data, wav_filename, input_wav_file)
                        
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
                                await asyncio.sleep(0.2)
                                print(f"Error sending audio data: {e}")
                                
                        if not sent:
                            print("Failed to send audio data after 3 attempts")
                            raise Exception("Failed to send audio data after 3 attempts")
                    
                    # Handle the 'start' event, this occurs when the Twilio client starts the stream
                    elif data['event'] == 'start':
                        stream_sid = data['start']['streamSid']
                        print(f"Incoming stream has started {stream_sid}")
            
            # Handle disconnections, directly by handling the WebSocketDisconnect exception
            except WebSocketDisconnect:
                print("Client disconnected.")
                call_results.update({
                    "status": "operai_disconnected",
                    "stream_sid": stream_sid
                })

            except Exception as e:
                print(f"Error in receive_from_twilio: {e}")
                call_results.update({
                    "status": "openai_disconnected",
                    "stream_sid": stream_sid
                })

            finally:
                # Close the WebSocket connection to OpenAI
                try:
                    await openai_ws.close()
                    client.calls(call_sid).update(status="completed")

                except Exception as e:
                    print(f"Error closing OpenAI WebSocket: {e}")

                # Close the WAV file to properly terminate recording
                if input_wav_file:
                    input_wav_file.close()
                if output_wav_file:
                    output_wav_file.close()

        async def send_to_twilio():
            """Receive events from the OpenAI Realtime API, send audio back to Twilio."""
            nonlocal stream_sid, output_wav_file, wav_filename
            global call_sid
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
                                wav_filename, 
                                output_wav_file, 
                                stream_sid=stream_sid
                            )
                            
                            # Send the audio delta back to Twilio
                            if audio_delta:
                                await websocket.send_json(audio_delta)

                        except Exception as e:
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

                                    if tool_name == 'save_information':
                                        # call_results["information"] = tool_args
                                        call_results.update({
                                            "information": tool_args
                                        })
                                        # print("call_results ", call_results)

                                        tool_response = {
                                            "type": "conversation.item.create",
                                            "item": {
                                                "type": "function_call_output",
                                                "call_id": tool_call_id,
                                                "output": json.dumps({
                                                    "response": "Indica al cliente que más tarde será contactado vía WhatsApp, desea buenas tardes y pide permiso para terminar la llamada. Si el cliente confirma, use la herramienta 'end_call'."
                                                })
                                            }
                                        }
                                        
                                        await openai_ws.send(json.dumps(tool_response))
                                        

                                        tool_response = {
                                            "type": "response.create"
                                            }
                                        await openai_ws.send(json.dumps(tool_response))

                                        if tool_name == 'end_call':
                                            try:
                                                # Ensure call_sid is not None before attempting to end the call
                                                if call_sid:
                                                    client.calls(call_sid).update(status="completed")
                                                    print(f"\n--- Call {call_sid} Ended by Assistant ---")
                                                else:
                                                    print("No active call to end.")
                                                
                                                # Reset call_sid to None
                                                call_sid = None
                                                
                                                # Print final call results
                                                print("Final Call Results:")
                                                print(json.dumps(call_results, indent=2))
                                                print("----------------------------\n")
                                                
                                                # Optional: Break out of the processing loop
                                                break
                                            except Exception as end_call_error:
                                                print(f"Error ending call: {end_call_error}")
                                                # Even if there's an error, reset call_sid
                                                call_sid = None
                                        
                                        

            except Exception as e:
                print(f"Error in send_to_twilio: {e}")
                call_results.update({
                    "status": "error",
                    "error_message": str(e),
                    "stream_sid": stream_sid
                })

        try:
            # Run the asyncio event loop, to continuously communicate with Twilio and OpenAI
            await asyncio.gather(receive_from_twilio(), send_to_twilio())

        except Exception as global_error:
            print(f"Unexpected global error in handle_media_stream: {global_error}")
            
            # Attempt to end the call if possible
            try:
                if call_sid:
                    client.calls(call_sid).update(status="completed")
                    print(f"\n--- Call {call_sid} Force Ended Due to Error ---")
            except Exception as end_call_error:
                print(f"Error force-ending call: {end_call_error}")
            
            # Update call results with the global error
            call_results.update({
                "status": "error",
                "error_message": str(global_error),
                "stream_sid": stream_sid
            })
            
            # Re-raise the error if needed for further handling
            raise

        finally:
            # Ensure call is ended and resources are cleaned up
            try:
                if call_sid:
                    client.calls(call_sid).update(status="completed")
            except Exception as final_end_call_error:
                print(f"Final error ending call: {final_end_call_error}")

            # Ensure all files are closed
            if input_wav_file:
                input_wav_file.close()
            if output_wav_file:
                output_wav_file.close()

            # Ensure WebSocket connections are closed
            try:
                await websocket.close()
            except Exception as ws_close_error:
                print(f"Error closing WebSocket: {ws_close_error}")

        # Ensure call results are set if not already set
        if not call_results:
            call_results.update({
                "status": "unknown",
                "stream_sid": stream_sid
            })
        
        print("Call results updated:", call_results)

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
    # parser = argparse.ArgumentParser(description="Run the Twilio AI voice assistant server.")
    # parser.add_argument('--call', required=True, help="The phone number to call, e.g., '--call=+18005551212'")
    # args = parser.parse_args()

    # phone_number = args.call
    # print(
    #     'Our recommendation is to always disclose the use of AI for outbound or inbound calls.\n'
    #     'Reminder: All of the rules of TCPA apply even if a call is made by AI.\n'
    #     'Check with your counsel for legal and compliance advice.'
    # )

    # loop = asyncio.get_event_loop()
    # loop.run_until_complete(make_call(phone_number))
    
    uvicorn.run(app, host="0.0.0.0", port=PORT)


    #ngrok http 6060
    #python _base_twilio_vad.py --call=+34616642830
    #powershell Invoke-RestMethod -Method Post -Uri "http://localhost:6060/make_call?phone_number=+1234567890"
    #cmd curl -X "POST" "http://localhost:6060/make_call?phone_number=+34616642830"