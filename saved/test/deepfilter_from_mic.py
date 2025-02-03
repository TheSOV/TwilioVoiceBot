import os
import pyaudio
import numpy as np
import torch
import wave
from datetime import datetime
from scipy import signal
from df.enhance import enhance, init_df, load_audio, save_audio

class RealtimeDeepFilter:
    def __init__(self, input_sample_rate=8000, output_sample_rate=48000, channels=1, chunk_size=480, record_duration=5):
        """
        Initialize real-time DeepFilter audio processing with resampling and recording.
        
        Args:
            input_sample_rate (int): Input audio sample rate
            output_sample_rate (int): Sample rate required by DeepFilterNet
            channels (int): Number of audio channels
            chunk_size (int): Number of samples per chunk
            record_duration (int): Duration of recording in seconds
        """
        # Initialize PyAudio
        self.p = pyaudio.PyAudio()
        
        # DeepFilterNet initialization
        self.model, self.df_state, _ = init_df()
        
        # Audio stream parameters
        self.input_sample_rate = input_sample_rate
        self.output_sample_rate = output_sample_rate
        self.channels = channels
        self.input_chunk_size = chunk_size
        self.record_duration = record_duration
        
        # Prepare recording buffers
        self.original_audio_frames = []
        self.enhanced_audio_frames = []
        
        # Calculate resampling parameters
        self.resample_ratio = self.output_sample_rate / self.input_sample_rate
        self.output_chunk_size = int(self.input_chunk_size * self.resample_ratio)
        
        # Prepare output directory
        self.output_dir = "recordings"
        os.makedirs(self.output_dir, exist_ok=True)
        
        # Open input and output streams
        self.input_stream = self.p.open(
            format=pyaudio.paFloat32,
            channels=self.channels,
            rate=self.input_sample_rate,
            input=True,
            output=True,
            frames_per_buffer=self.input_chunk_size,
            stream_callback=self.audio_callback
        )
        
        # Generate unique timestamp for this recording session
        self.timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

    def resample_audio(self, audio_chunk):
        """
        Resample audio from input rate to output rate.
        
        Args:
            audio_chunk (np.ndarray): Input audio chunk
        
        Returns:
            np.ndarray: Resampled audio chunk
        """
        # Resample using scipy's resample function
        resampled_chunk = signal.resample(
            audio_chunk, 
            int(len(audio_chunk) * self.resample_ratio)
        )
        
        return resampled_chunk

    def save_audio(self, filename, frames, sample_rate):
        """
        Save audio frames to a WAV file.
        
        Args:
            filename (str): Output filename
            frames (list): List of audio frames
            sample_rate (int): Audio sample rate
        """
        full_path = os.path.join(self.output_dir, filename)
        
        with wave.open(full_path, 'wb') as wf:
            wf.setnchannels(self.channels)
            wf.setsampwidth(self.p.get_sample_size(pyaudio.paFloat32))
            wf.setframerate(sample_rate)
            wf.writeframes(b''.join(frames))
        
        print(f"Saved audio to {full_path}")

    def audio_callback(self, in_data, frame_count, time_info, status):
        """
        Real-time audio processing callback.
        
        Args:
            in_data (bytes): Input audio data
            frame_count (int): Number of frames
            time_info (dict): Timing information
            status (int): Status flags
        
        Returns:
            tuple: Processed audio data and status
        """
        try:
            # Convert input bytes to numpy float32 array
            audio_chunk = np.frombuffer(in_data, dtype=np.float32)
            
            # Store original audio frames
            self.original_audio_frames.append(in_data)
            
            # Resample audio to 48 kHz
            resampled_chunk = self.resample_audio(audio_chunk)
            
            # Convert to PyTorch tensor
            audio_tensor = torch.from_numpy(resampled_chunk).float()
            
            # Reshape to match DeepFilterNet expectations (batch, samples)
            audio_tensor = audio_tensor.unsqueeze(0)
            
            # Apply DeepFilter noise reduction
            enhanced_tensor = enhance(self.model, self.df_state, audio_tensor)
            
            # Convert tensor back to numpy
            enhanced_chunk = enhanced_tensor.numpy()
            
            # Convert enhanced chunk to bytes and store
            enhanced_bytes = enhanced_chunk.astype(np.float32).tobytes()
            self.enhanced_audio_frames.append(enhanced_bytes)
            
            # Convert back to bytes for output
            out_data = enhanced_bytes
            
            return (out_data, pyaudio.paContinue)
        
        except Exception as e:
            print(f"Error in audio processing: {e}")
            return (in_data, pyaudio.paContinue)

    def start(self):
        """Start the audio stream"""
        print("Starting real-time DeepFilter audio processing...")
        print(f"Input sample rate: {self.input_sample_rate} Hz")
        print(f"Output sample rate: {self.output_sample_rate} Hz")
        print(f"Recording duration: {self.record_duration} seconds")
        print("Press Ctrl+C to stop.")
        
        try:
            # Keep the stream active
            self.input_stream.start_stream()
            
            # Wait for stream to be active for specified duration
            for _ in range(int(self.record_duration * (self.input_sample_rate / self.input_chunk_size))):
                torch.cuda.empty_cache()  # Clear CUDA cache if using GPU
                
            # Stop the stream
            self.input_stream.stop_stream()
            
            # Save recorded audio files
            original_filename = f"original_audio_{self.timestamp}.wav"
            enhanced_filename = f"enhanced_audio_{self.timestamp}.wav"
            
            self.save_audio(original_filename, self.original_audio_frames, self.input_sample_rate)
            self.save_audio(enhanced_filename, self.enhanced_audio_frames, self.output_sample_rate)
            
from df.enhance import enhance, init_df, load_audio, save_audio
from df.utils import download_file

if __name__ == "__main__":
    # Load default model
    model, df_state, _ = init_df()
    # Download and open some audio file. You use your audio files here
    audio_path = "recordings/audio_20250129_072721.wav"
    audio, _ = load_audio(audio_path, sr=df_state.sr())
    # Denoise the audio
    enhanced = enhance(model, df_state, audio)
    # Save for listening
    # save_audio("enhanced.wav", enhanced, df_state.sr())
    