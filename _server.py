import os
import json
import base64
import asyncio
from fastapi import FastAPI, HTTPException, WebSocket, Request, Body, File, UploadFile
from fastapi.responses import JSONResponse, FileResponse, StreamingResponse
from fastapi.websockets import WebSocketDisconnect
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
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
from pydantic import BaseModel
from tinydb import TinyDB, Query
from datetime import datetime, timezone
from info_extraction import InfoExtractionAgent
import io
import pandas as pd
import tempfile
import os
from fastapi.responses import FileResponse
import phonenumbers

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

# Initialize database
def init_db():
    """Initialize the database with required tables"""
    db = TinyDB('db.json')
    users_table = db.table('users')
    calls_table = db.table('calls')
    return db, users_table, calls_table

db, users_table, calls_table = init_db()

# Initialize info extraction agent
info_agent = InfoExtractionAgent()

def get_utc_timestamp():
    """Get current UTC timestamp in ISO format with Z suffix to indicate UTC"""
    return datetime.now(timezone.utc).strftime('%Y-%m-%dT%H:%M:%SZ')

RECORDINGS_FOLDER = os.path.abspath(os.path.join(os.path.dirname(__file__), 'recordings'))

@app.get("/")
async def serve_spa(request: Request):
    return FileResponse("static/index.html")


@app.post('/make_call')
async def initiate_call(phone_number: str = Body(..., embed=True)):
    global calls
    
    if not phone_number:
        raise HTTPException(status_code=400, detail="Phone number is required")
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


# websocket handler
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


# User endpoints
@app.post('/api/users')
async def create_user(user_data: dict = Body(...)):
    """Create a new user"""
    if not user_data.get('phone_number'):
        raise HTTPException(status_code=400, detail="Phone number is required")
    
    # Validate and format phone number
    validated_phone_number = validate_phone_number(user_data['phone_number'])
    user_data['phone_number'] = validated_phone_number
    
    # Add creation timestamp and initialize call history
    user_data['created_at'] = get_utc_timestamp()
    user_data['call_history'] = []
    
    # Check if phone number already exists
    User = Query()
    existing_user = users_table.get(User.phone_number == validated_phone_number)
    if existing_user:
        raise HTTPException(status_code=400, detail="Phone number already exists")
    
    users_table.insert(user_data)
    return user_data

def validate_phone_number(phone_number: str, default_country: str = "ES") -> str:
    """
    Validate and format phone number with specific rules:
    - Handles various input formats (with/without +, with/without country code)
    - If no country code, assume default country (Spain)
    - Verify number is valid
    - Return formatted E.164 number
    
    Args:
        phone_number (str): Phone number to validate
        default_country (str, optional): Default country code if not specified. Defaults to "ES".
    
    Raises:
        HTTPException: If phone number is invalid
    
    Returns:
        str: Validated and formatted phone number in E.164 format
    """
    # Normalize the phone number: remove spaces, dashes, parentheses
    phone_number = str(phone_number).replace(' ', '').replace('-', '').replace('(', '').replace(')', '')
    
    try:
        # Handle numbers starting with 0 or without +
        if phone_number.startswith('00'):
            # Convert international prefix 00 to +
            phone_number = f'+{phone_number[2:]}'
        elif phone_number.startswith('0'):
            # For Spanish numbers starting with 0, replace with +34
            if default_country == 'ES':
                phone_number = f'+34{phone_number[1:]}'
        elif not phone_number.startswith('+'):
            # If no + and not starting with 0, assume default country
            if default_country == 'ES':
                phone_number = f'+34{phone_number}'
        
        # Parse the number, using the default country as a fallback
        parsed_number = phonenumbers.parse(phone_number, default_country)
        
        # Validate the number
        if not phonenumbers.is_valid_number(parsed_number):
            raise ValueError(f"Invalid phone number: {phone_number}")
        
        # Format to E.164
        formatted_number = phonenumbers.format_number(parsed_number, phonenumbers.PhoneNumberFormat.E164)
        
        return formatted_number
    
    except (phonenumbers.NumberParseException, ValueError) as e:
        raise HTTPException(status_code=400, detail=str(e))

@app.get('/api/users')
async def get_users():
    """Get all users"""
    users = users_table.all()
    # Sort users by created_at in descending order
    return sorted(users, key=lambda x: x.get('created_at', ''), reverse=True)

@app.get('/api/users/{phone_number}')
async def get_user(phone_number: str):
    UserQuery = Query()
    user = users_table.get(UserQuery.phone_number == phone_number)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return user

@app.put('/api/users/{phone_number}')
async def update_user(phone_number: str, user_data: dict = Body(...)):
    UserQuery = Query()
    if not users_table.get(UserQuery.phone_number == phone_number):
        raise HTTPException(status_code=404, detail="User not found")
    
    user_data['updated_at'] = get_utc_timestamp()
    users_table.update(user_data, UserQuery.phone_number == phone_number)
    return user_data

@app.delete('/api/users/{phone_number}')
async def delete_user(phone_number: str):
    """
    Delete a user and their associated audio files
    
    Args:
        phone_number (str): Phone number of the user to delete
    
    Returns:
        dict: Confirmation of deletion
    """
    # Find the user first
    User = Query()
    user_record = users_table.search(User.phone_number == phone_number)
    
    if not user_record:
        raise HTTPException(status_code=404, detail="User not found")
    
    # Delete associated wav files from call history
    for call in user_record[0].get('call_history', []):
        audio_file_name = call.get('audio_file_name')
        if audio_file_name and os.path.exists(audio_file_name):
            try:
                os.remove(audio_file_name)
                print(f"Deleted audio file: {audio_file_name}")
            except Exception as e:
                print(f"Error deleting audio file {audio_file_name}: {e}")
    
    # Delete the user from the database
    users_table.remove(User.phone_number == phone_number)
    
    return {"message": "User and associated audio files deleted successfully"}

@app.post('/api/users/{phone_number}/calls')
async def record_call(phone_number: str, call_data: dict = Body(...)):
    await asyncio.sleep(5) # to allow closing the sockets.

    UserQuery = Query()
    user = users_table.get(UserQuery.phone_number == phone_number)
    
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    # Prepare call record
    call_record = {
        "timestamp": get_utc_timestamp(),
        **call_data
    }
    
    # Only process transcription if audio file exists and call was completed
    if call_data.get('audio_file_name') and call_data.get('call_status') == 'completed':
        try:
            # Perform transcription and info extraction
            information, conversation = info_agent.extract_info(call_data['audio_file_name'])
            
            # Add extracted information to call record
            call_record['extracted_info'] = information.model_dump()['parsed']
            call_record['conversation'] = "\n".join([
                f"{turn['speaker']}: {turn['text']}" for turn in conversation
            ])
        except Exception as e:
            # Log the error but don't prevent saving the call record
            call_record['extraction_error'] = str(e)
    
    # Update user with call history
    if 'call_history' not in user:
        user['call_history'] = []
    
    user['call_history'].append(call_record)
    user['last_called_at'] = get_utc_timestamp()
    
    # Update user in the database
    users_table.update(user, UserQuery.phone_number == phone_number)
    
    return call_record

@app.get('/api/call_histories')
async def get_call_histories(
    start_date: str = None,
    end_date: str = None,
    phone_number: str = None,
    call_status: str = None,
    extracted_info_keyword: str = None
):
    # Start with all users
    users = users_table.all()
    
    # Filter users by call history
    filtered_call_histories = []
    
    for user in users:
        if 'call_history' not in user:
            continue
        
        for call in user['call_history']:
            # Apply filters
            match = True
            
            # Phone number filter
            if phone_number and phone_number.lower() not in user['phone_number'].lower():
                match = False
                continue
            
            # Call status filter
            if call_status and call.get('call_status', '').lower() != call_status.lower():
                match = False
                continue
            
            # Date filters
            if start_date:
                call_date = datetime.fromisoformat(call['timestamp'].replace('Z', '+00:00'))
                start = datetime.fromisoformat(start_date.replace('Z', '+00:00'))
                if call_date < start:
                    match = False
                    continue
            
            if end_date:
                call_date = datetime.fromisoformat(call['timestamp'].replace('Z', '+00:00'))
                end = datetime.fromisoformat(end_date.replace('Z', '+00:00'))
                if call_date > end:
                    match = False
                    continue
            
            # Extracted info keyword filter
            if extracted_info_keyword:
                if 'extracted_info' not in call:
                    match = False
                    continue
                
                keyword_match = False
                for value in call['extracted_info'].values():
                    if extracted_info_keyword.lower() in str(value).lower():
                        keyword_match = True
                        break
                
                if not keyword_match:
                    match = False
                    continue
            
            # If all filters pass, add the call with user's phone number
            if match:
                call_with_phone = call.copy()
                call_with_phone['phone_number'] = user['phone_number']
                filtered_call_histories.append(call_with_phone)
    
    # Sort by timestamp in descending order
    filtered_call_histories.sort(key=lambda x: x['timestamp'], reverse=True)
    
    return filtered_call_histories

@app.post('/api/call_histories/export')
async def export_call_histories(request: dict):
    calls = request.get('calls', [])

    # Convert the calls data to a pandas DataFrame
    df = pd.DataFrame(calls)
    
    # Format the timestamp column if it exists
    if 'timestamp' in df.columns:
        df['timestamp'] = pd.to_datetime(df['timestamp']).dt.strftime('%Y-%m-%d %H:%M:%S')
    
    # Format duration to MM:SS if it exists
    if 'call_duration' in df.columns:
        df['call_duration'] = df['call_duration'].apply(lambda x: 
            '-' if pd.isnull(x) or x is None else f"{int(x // 60)}:{int(x % 60):02d}"
        )
    
    # Format column names for better readability
    df.columns = [col.replace('_', ' ').title() for col in df.columns]
    
    # Create a temporary file
    temp_file = tempfile.NamedTemporaryFile(delete=False, suffix='.xlsx')
    temp_path = temp_file.name
    temp_file.close()
    
    try:
        # Write DataFrame to Excel
        df.to_excel(temp_path, index=False, engine='openpyxl')
        
        # Return the file as a response
        response = FileResponse(
            temp_path,
            media_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
            filename=f'call_history_{datetime.now().strftime("%Y%m%d")}.xlsx'
        )
        
        # Custom background task for file deletion
        async def cleanup():
            try:
                os.unlink(temp_path)
            except Exception as e:
                print(f"Error deleting temp file: {e}")
        
        response.background = cleanup
        
        return response
    except Exception as e:
        # If something goes wrong, ensure temp file is deleted
        if os.path.exists(temp_path):
            os.unlink(temp_path)
        raise

@app.post('/api/users/import')
async def import_users(file: UploadFile = File(...)):
    """
    Import users from Excel, CSV, or TXT file
    
    File formats:
    - Excel/CSV: First column = phone number, second column (optional) = name
    - TXT: Comma-separated phone numbers only
    
    Returns:
        dict: Summary of import results
    """
    # Read the file content
    content = await file.read()
    filename = file.filename.lower()
    
    # Validate file type
    if not filename.endswith(('.xlsx', '.xls', '.csv', '.txt')):
        raise HTTPException(status_code=400, detail="Invalid file type. Supported: .xlsx, .xls, .csv, .txt")
    
    try:
        # Process different file types
        imported_users = []
        failed_users = []
        
        if filename.endswith(('.xlsx', '.xls', '.csv')):
            # Read Excel or CSV with string dtype, skipping header
            try:
                if filename.endswith('.csv'):
                    df = pd.read_csv(io.BytesIO(content), header=0, dtype=str)
                else:
                    df = pd.read_excel(io.BytesIO(content), header=0, dtype=str)
            except Exception as e:
                raise HTTPException(status_code=400, detail=f"Error reading file: {str(e)}")
            
            for index, row in df.iterrows():
                try:
                    # Read phone number as string
                    phone_number = str(row.iloc[0]).strip()
                    
                    # Validate phone number
                    try:
                        validated_number = validate_phone_number(phone_number)
                    except Exception as validation_error:
                        failed_users.append({
                            'row': index + 2,  # +2 to account for 0-indexing and header
                            'input': phone_number,
                            'error': str(validation_error)
                        })
                        continue
                    
                    # Prepare user data
                    user_data = {
                        'phone_number': validated_number,
                        # Handle name: use empty string if NaN or no second column
                        'name': str(row.iloc[1]).strip() if len(row) > 1 and pd.notna(row.iloc[1]) else '',
                        'comments': '',
                        'created_at': get_utc_timestamp(),
                        'updated_at': get_utc_timestamp()
                    }
                    
                    # Check if user already exists
                    User = Query()
                    existing_user = users_table.search(User.phone_number == validated_number)
                    
                    if existing_user:
                        # Update existing user
                        users_table.update(user_data, User.phone_number == validated_number)
                    else:
                        # Create new user
                        users_table.insert(user_data)
                    
                    imported_users.append(validated_number)
                except Exception as e:
                    failed_users.append({
                        'row': index + 2,
                        'input': str(row.iloc[0]),
                        'error': str(e)
                    })
        
        elif filename.endswith('.txt'):
            # Read TXT (comma-separated phone numbers)
            try:
                phone_numbers = content.decode('utf-8').replace('\n', '').split(',')
            except Exception as e:
                raise HTTPException(status_code=400, detail=f"Error reading TXT file: {str(e)}")
            
            for index, phone_number in enumerate(phone_numbers):
                try:
                    # Normalize phone number
                    phone_number = phone_number.strip()
                    
                    # Skip empty entries
                    if not phone_number:
                        continue
                    
                    # Validate phone number
                    try:
                        validated_number = validate_phone_number(phone_number)
                    except Exception as validation_error:
                        failed_users.append({
                            'row': index + 1,
                            'input': phone_number,
                            'error': str(validation_error)
                        })
                        continue
                    
                    # Prepare user data
                    user_data = {
                        'phone_number': validated_number,
                        'name': '',
                        'comments': '',
                        'created_at': get_utc_timestamp(),
                        'updated_at': get_utc_timestamp()
                    }
                    
                    # Check if user already exists
                    User = Query()
                    existing_user = users_table.search(User.phone_number == validated_number)
                    
                    if existing_user:
                        # Update existing user
                        users_table.update(user_data, User.phone_number == validated_number)
                    else:
                        # Create new user
                        users_table.insert(user_data)
                    
                    imported_users.append(validated_number)
                except Exception as e:
                    failed_users.append({
                        'row': index + 1,
                        'input': phone_number,
                        'error': str(e)
                    })
        
        return {
            "message": "Users imported successfully",
            "imported_count": len(imported_users),
            "failed_count": len(failed_users),
            "imported_users": imported_users,
            "failed_users": failed_users
        }
    
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Error processing file: {str(e)}")

@app.post('/api/users/export')
async def export_users(format: str = 'xlsx'):
    """
    Export users to specified format
    
    Supported formats:
    - xlsx: Excel file with phone number and name
    - csv: CSV file with phone number and name
    - txt: Comma-separated phone numbers
    
    Returns:
        StreamingResponse with exported file
    """
    # Validate format
    supported_formats = ['xlsx', 'csv', 'txt']
    if format not in supported_formats:
        raise HTTPException(status_code=400, detail=f"Invalid format. Supported: {', '.join(supported_formats)}")
    
    # Get all users
    all_users = users_table.all()
    
    # Prepare data based on format
    if format in ['xlsx', 'csv']:
        # Prepare DataFrame
        df = pd.DataFrame([
            {
                'Phone Number': user['phone_number'], 
                'Name': user.get('name', '')
            } for user in all_users
        ])
        
        # Create in-memory buffer
        buffer = io.BytesIO()
        
        if format == 'xlsx':
            df.to_excel(buffer, index=False, engine='openpyxl')
            content_type = 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
            filename = 'users_export.xlsx'
        else:
            df.to_csv(buffer, index=False)
            content_type = 'text/csv'
            filename = 'users_export.csv'
        
        buffer.seek(0)
        
        return StreamingResponse(
            buffer, 
            media_type=content_type, 
            headers={'Content-Disposition': f'attachment; filename="{filename}"'}
        )
    
    elif format == 'txt':
        # Create comma-separated phone numbers
        phone_numbers = ','.join(user['phone_number'] for user in all_users)
        
        buffer = io.BytesIO(phone_numbers.encode('utf-8'))
        buffer.seek(0)
        
        return StreamingResponse(
            buffer, 
            media_type='text/plain', 
            headers={'Content-Disposition': 'attachment; filename="users_export.txt"'}
        )

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, replace with your frontend URL
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount recordings directory for direct file serving
app.mount("/recordings", StaticFiles(directory=RECORDINGS_FOLDER), name="recordings")

# Mount static files last to not interfere with other routes
app.mount("/", StaticFiles(directory="static", html=True), name="static")

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=PORT)


    #ngrok http 6060
    #python _base_twilio_vad.py --call=+34616642830
    #powershell Invoke-RestMethod -Method Post -Uri "http://localhost:6060/make_call?phone_number=+1234567890"
    #cmd curl -X "POST" "http://localhost:6060/make_call?phone_number=%2B34616642830"