# TwilioVoiceBot
[![Ask DeepWiki](https://deepwiki.com/badge.svg)](https://deepwiki.com/TheSOV/TwilioVoiceBot)

## Project Overview
A voice-based AI bot using Twilio for communication, with a Vue.js frontend and Python backend. Based on https://www.twilio.com/en-us/blog/outbound-calls-python-openai-realtime-api-voice. More details at [DeepWiki](https://deepwiki.com/TheSOV/TwilioVoiceBot)

## Project Structure

### Root Directory
- `_server.py`: Main server-side Python script
- `_client.py`: Alternative console-based client for batch processing phone calls. Useful for testing and development. Features include:
  - Excel/CSV file processing for bulk phone numbers
  - Phone number validation using `phonenumbers` library
  - Organized call results storage
  - Color-coded console output for better readability
  - Integration with the main bot server for making calls
- `audio_processing.py`: Comprehensive audio processing utilities:
  - Stereo audio recording with preserved timing (need to be improved)
  - Audio format conversion (µ-law to WAV)(by default, Twilio uses g711, a audio enconding for audio in VoIP)
  - In this file, audio filters can be implemented. Currently, the filter implemented is a volume reduction, to reduce the current VAD server sensibility to noise, however, other more sophisticated filters can be impemented, however OpenAI VAD server will probably be improved in the future, making the necessity of filters less important. Also, take on count the the filter must be implemented in a real-time manner, making most of the popular denoising algorithms more complex to implement.
- `bot_initialization.py`: Handles bot setup and session management:
  - Dynamic tool loading from YAML configuration
  - Voice and system message configuration
  - OpenAI voice model configuration. Includes:
    - Turn detection with server-side Voice Activity Detection (VAD)
      - Threshold: 0.9 for speech detection
      - 300ms prefix padding for smooth transitions
      - 800ms silence duration for turn completion
    - Audio format: g711 µ-law for input/output (VoIP standard)
    - Voice selection (configurable via .env)
    - Multi-modal support: text and audio
    - Temperature: 0.6 for balanced response creativity (minimum is 0.6)
    - Dynamic tool integration (currently the only implemented tool is the end_call, used by the model to end the conversation. A data extraction tool is also implemented, used by the model to extract information from the conversation, however, the current tested model is a bit dumb, and often does not understand what the user said, so and independent data extraction moelule with a combination of transcription and structured data estraction was implemented, and it is applied over the recoreded audio file).
  - Initial conversation script loading and execution
  - Modular tool configuration system
- `info_extraction.py`: Temporal information extraction system:
  - Integration with OpenAI's API for transcription and analysis
  - Speaker diarization using Pyannote Audio (this is to identify what speaker is speaking at any given moment, making easier for the model to correctly interpret the user input)
  - Structured data extraction using Pydantic models (modifyng the pydantic models, allows to modify which information is extracted from the audio file. pydantic models for data extraaction is the class ClientInfoExtraction, at the begining of the file).
  - If any acronym or specific name or word, that is uncommon, will be normally used, add it as prompt to the whisper model. Whisper model only supports up to 224 tokens as prompt input. More info about Whisper: https://platform.openai.com/docs/guides/speech-to-text
- `requirements.txt`: Python dependencies
- `db.json`: Local database/storage (Currently using TinyDB. This is a simple JSON file, but it could be replaced with a more robust database like MongoDB or PostgreSQL if needed. Take in count that TinyDB be default has no support concurrent writing, so it could be useful to switch to a more robust database in the future. Calling features are independent from the database.)

### Directories
- `AI/`: AI-related components
  - `prompts/`: Prompt configuration files
  - `tools/`: AI tool implementations

- `frontend/`: Vue.js frontend application
  - `src/`: Source code
    - `components/`: Reusable Vue components
    - `pages/`: Page-level Vue components
  - Configuration files: `.eslintrc`, `quasar.config.js`, etc.

- `static/`: Static assets (in this folder goes the compiled frontend files. Frontend is loosely coupled with the backend, so the frontend can be built and deployed separately, and other technologies can be used. Only enure to name the main html file "index.html")
- `recordings/`: Stored voice recordings
- `call_results/`: Results from voice calls (Only for the console client)
- `numbers_to_call/`: Contact information (Only for the console client)

## Key Technologies
- Backend: Python
- Frontend: Vue.js (Quasar Framework)
- Voice Communication: Twilio
- AI: OpenAI API

## Setup and Installation
1. Install Python dependencies: `pip install -r requirements.txt`
2. Install frontend dependencies: `cd frontend && npm install` (for development only)
3. Configure environment variables in `.env`:
   - OpenAI Configuration ([Create account](https://platform.openai.com)):
     - `OPENAI_API_KEY`: Your OpenAI API key ([Get key](https://platform.openai.com/account/api-keys))
     - `OPENAI_REALTIME_MODEL`: Realtime model ([Docs](https://platform.openai.com/docs/guides/realtime)) (default: gpt-4o-mini-realtime-preview)
     - `OPENAI_AUDIO_VOICE`: TTS voice model ([Docs](https://platform.openai.com/docs/guides/text-to-speech)) (default: coral)
     - `OPENAI_STT_MODEL`: Speech-to-text model ([Docs](https://platform.openai.com/docs/guides/speech-to-text)) (default: whisper-1)
     - `OPENAI_TEXT_MODEL`: Text generation model ([Docs](https://platform.openai.com/docs/guides/text-generation)) (default: gpt-4o-mini)
   - Twilio Configuration ([Create account](https://www.twilio.com)):
     - `TWILIO_ACCOUNT_SID`: Your Twilio Account SID
     - `TWILIO_AUTH_TOKEN`: Your Twilio Auth Token
     - `PHONE_NUMBER_FROM`: Your Twilio phone number
     - When using Twilio in Trial version, it is required to add a phone number as the verified number receive calls from Twilio, and also it is required asset it risk level. It is easier to run the code, and follow the instructions given in the console when Twilio API raises the exceptions. Otherwise, consult the Twilio documentation, ([Verify phone number](https://help.twilio.com/articles/223180048-How-to-Add-and-Remove-a-Verified-Phone-Number-or-Caller-ID-with-Twilio)).
   - Hugging Face Configuration([Create account](https://huggingface.co/)):
     - `HUGGINGFACE_TOKEN`: Token for Pyannote Speaker Diarization ([Get token](https://huggingface.co/docs/hub/security-tokens))
     - Pyannote Segmentation is a Gated Model requiring organization name and email ([Model page](https://huggingface.co/pyannote/segmentation-3.0))
   - Additional Settings:
     - `MODEL_LANGUAGE`: Language setting (default: es)
     - `CALL_DURATION_LIMIT`: Call duration limit in seconds
     - `NGROK_TOKEN`: Ngrok authentication token ([Create account](https://ngrok.com/))
     - `PORT`: Server port (default: 6060)

## Development
- Backend: Python scripts in root directory
- Frontend: Vue components in `frontend/src/`
- AI Prompts: Configured in `AI/prompts/`

## Server API

### Call Management
- `POST /make_call`
  - Make an outbound call to a phone number
  - Body: `{ "phone_number": string }`
  - Returns: Call details including status
  - Timeout: will last until the call ends or times out.
  - This is one of the main functions of the backend.

### User Management
- `POST /users`
  - Create a new user
  - Body: User data object
  - Validates phone numbers with country code support

- `GET /users`
  - Get all users
  - Returns: List of users

- `GET /users/{phone_number}`
  - Get specific user details
  - Returns: User data or 404

- `PUT /users/{phone_number}`
  - Update user information
  - Body: Updated user data

- `DELETE /users/{phone_number}`
  - Delete user and associated audio files
  - Returns: Deletion confirmation

### Call History
- `GET /call_histories`
  - Get call history with filters
  - Query Parameters:
    - `start_date`: Filter by start date
    - `end_date`: Filter by end date
    - `phone_number`: Filter by phone number
    - `call_status`: Filter by call status
    - `extracted_info_keyword`: Search in extracted information

- `POST /call_histories/export`
  - Export call histories to Excel/CSV
  - Body: Filter criteria

### Bulk Operations
- `POST /users/import`
  - Import users from file
  - Supports Excel, CSV, TXT formats
  - File format:
    - Excel/CSV: columns = [phone_number, name(optional)]
    - TXT: Comma-separated phone numbers

- `GET /users/export`
  - Export users list
  - Query Parameter: `format` (xlsx, csv, txt)
  - Returns: File download

### WebSocket Endpoint
- `WebSocket /media-stream`
  - Handles real-time audio streaming
  - Manages communication between Twilio and OpenAI
  - Supports:
    - Audio format: g711 µ-law
    - Turn detection
    - Real-time transcription and response
  - This function, along with make_call, are the main functions of the backend. The rest are support functions to control call flows.
  - Take in count that this functions contains two inner async loops, that takes care of the communication between Twilio and OpenAI, so any improvement made on it must NOT include sleeps or blocking operations, otherwise, it may affect the quality of the call.

### Static Files
- `GET /`
  - Serves the frontend SPA
  - Returns: index.html from static directory

## Usage
- Run the server: `python _server.py`

## License
MIT
