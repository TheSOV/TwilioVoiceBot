import base64
import audioop
import numpy as np
import wave
import os
from datetime import datetime
import struct
import time

class AudioRecorder:
    """
    Stereo audio recorder to write input and output audio with preserved timing
    """
    def __init__(self, file_dir='recordings/combined', frame_rate=4000):
        self.wav_file = None
        self.wav_filename = None
        self.file_dir = file_dir
        self.input_frames = []
        self.output_frames = []
        self.start_time = None
        self.frame_rate = frame_rate
        self.frame_duration = 1 / frame_rate  # Duration of a single frame at 8kHz

    def create_wav_file(self):
        if self.wav_file is not None:
            self.wav_file.close()

        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        os.makedirs(self.file_dir, exist_ok=True)
        self.wav_filename = f'{self.file_dir}/combined_audio_{timestamp}.wav'
        self.wav_file = wave.open(self.wav_filename, 'wb')
        self.wav_file.setnchannels(2)  # Stereo
        self.wav_file.setsampwidth(2)  # 16-bit audio
        self.wav_file.setframerate(self.frame_rate)  # 8kHz for g711
        self.start_time = time.time()
        print(f"Created new stereo audio file: {self.wav_filename}")

    def write_input_audio(self, input_bytes):
        if self.wav_file is None:
            self.create_wav_file()
        
        # Store input frames
        self.input_frames.append(input_bytes)
        
        # Synchronize channels if needed
        self._synchronize_channels()

    def write_output_audio(self, output_bytes):
        if self.wav_file is None:
            self.create_wav_file()
        
        # Store output frames
        self.output_frames.append(output_bytes)
        
        # Synchronize channels if needed
        self._synchronize_channels()

    def _synchronize_channels(self):
        # Ensure both input and output have same number of frames
        while len(self.input_frames) < len(self.output_frames):
            self.input_frames.append(b'\x00\x00')
        while len(self.output_frames) < len(self.input_frames):
            self.output_frames.append(b'\x00\x00')
        
        # Write synchronized stereo frames
        if self.input_frames and self.output_frames:
            stereo_frames = bytearray()
            for input_frame, output_frame in zip(self.input_frames, self.output_frames):
                stereo_frames.extend(input_frame)  # Left channel (input)
                stereo_frames.extend(output_frame)  # Right channel (output)
            
            # Calculate expected write time based on frame count
            current_time = time.time()
            expected_duration = len(self.input_frames) * self.frame_duration
            actual_elapsed = current_time - self.start_time
            
            # Add delay if writing too fast
            if actual_elapsed < expected_duration:
                time.sleep(expected_duration - actual_elapsed)
            
            self.wav_file.writeframes(bytes(stereo_frames))
            
            # Clear processed frames
            self.input_frames.clear()
            self.output_frames.clear()

    def close_wav_file(self):
        if self.wav_file is not None:
            # Write any remaining frames
            if self.input_frames or self.output_frames:
                self._synchronize_channels()
            
            self.wav_file.close()
            self.wav_file = None
            self.start_time = None

# Global audio recorder instance
audio_recorder = AudioRecorder()

def process_input_audio(ulaw_data, wav_filename=None, wav_file=None, file_dir='recordings/input'):
    # Convert ulaw to PCM16
    pcm_data = audioop.ulaw2lin(ulaw_data, 2)  # 2 bytes per sample
    
    # Convert to numpy array for filtering
    audio_np = np.frombuffer(pcm_data, dtype=np.int16).copy()
    
    # Apply filter (using deepfilternet for better noise reduction)
    filtered_audio = (audio_np / 5).astype(np.int16)
    
    # Convert filtered audio back to bytes
    filtered_pcm = filtered_audio.tobytes()
    
    # Write to combined audio file (left channel)
    audio_recorder.write_input_audio(filtered_pcm)
    
    # Convert filtered PCM back to ulaw
    filtered_ulaw = audioop.lin2ulaw(filtered_pcm, 2)  # 2 bytes per sample
    
    # Prepare filtered audio for OpenAI
    audio_append = {
        "type": "input_audio_buffer.append",
        "audio": base64.b64encode(filtered_ulaw).decode('utf-8')
    }

    return audio_append, audio_recorder.wav_filename, audio_recorder.wav_file

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
        
        # Convert ulaw to PCM
        pcm_data = audioop.ulaw2lin(ulaw_bytes, 2)  # 2 bytes per sample
        
        # Write to combined audio file (right channel)
        audio_recorder.write_output_audio(pcm_data)
        
        # Prepare audio delta for Twilio
        audio_delta = {
            "event": "media",
            "streamSid": stream_sid,
            "media": {
                "payload": base64.b64encode(ulaw_bytes).decode('utf-8')  # Encode payload as base64
            }
        }

        return audio_delta, audio_recorder.wav_filename, audio_recorder.wav_file

    except Exception as e:
        print(f"Error processing output audio: {e}")
        return None, audio_recorder.wav_filename, audio_recorder.wav_file
