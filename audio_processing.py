import base64
import audioop
import numpy as np
import wave
import os
from datetime import datetime

def process_input_audio(ulaw_data, wav_filename=None, wav_file=None, file_dir='recordings/input'):
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
    if wav_filename is None or wav_file is None:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        os.makedirs(file_dir, exist_ok=True)
        # ulaw_filename = f'recordings/audio_{timestamp}.ul'
        # ulaw_file = open(ulaw_filename, 'wb')
        wav_filename = f'{file_dir}/audio_{timestamp}.wav'
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

    return audio_append, wav_filename, wav_file
    


def process_output_audio(ulaw_data, wav_filename=None, wav_file=None, file_dir='recordings/output', stream_sid=None):
    """
    Process output audio from OpenAI, converting ulaw to WAV.

    Args:
        ulaw_data (str): Base64 encoded ulaw audio data
        wav_filename (str, optional): Existing WAV filename
        wav_file (wave.Wave_write, optional): Existing WAV file object
        file_dir (str, optional): Directory to save WAV files
        stream_sid (str, optional): Stream ID for logging

    Returns:
        tuple: (audio_delta dict, wav_filename, wav_file)
    """
    try:
        # Decode the base64 ulaw data
        ulaw_bytes = base64.b64decode(ulaw_data)
        
        # Create files if not exists
        if wav_filename is None or wav_file is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            os.makedirs(file_dir, exist_ok=True)
            wav_filename = f'{file_dir}/output_audio_{timestamp}.wav'
            wav_file = wave.open(wav_filename, 'wb')
            wav_file.setnchannels(1)  # Mono audio
            wav_file.setsampwidth(2)  # 16-bit audio
            wav_file.setframerate(8000)  # 8kHz for g711
            print(f"Created new output audio file: {wav_filename}")
        
        # Convert ulaw to PCM
        pcm_data = audioop.ulaw2lin(ulaw_bytes, 2)  # 2 bytes per sample
        
        # Save PCM data to WAV file
        wav_file.writeframes(pcm_data)
        
        # Prepare audio delta for Twilio
        audio_delta = {
            "event": "media",
            "streamSid": stream_sid,
            "media": {
                "payload": ulaw_data  # Keep original ulaw payload for Twilio
            }
        }

        return audio_delta, wav_filename, wav_file

    except Exception as e:
        print(f"Error processing output audio: {e}")
        return None, wav_filename, wav_file
