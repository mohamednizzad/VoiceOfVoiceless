"""
Audio Processing Module for VoiceAccess
Handles real-time audio capture, preprocessing, and streaming
"""

import asyncio
import threading
import time
import numpy as np
import queue
from typing import Optional, Callable
import logging
from dataclasses import dataclass
import os

# Try to import sounddevice, fall back to simulation if not available
try:
    import sounddevice as sd
    SOUNDDEVICE_AVAILABLE = True
except ImportError:
    SOUNDDEVICE_AVAILABLE = False
    sd = None
    logging.warning("sounddevice not available, will use fallback audio processor")

logger = logging.getLogger(__name__)

@dataclass
class AudioConfig:
    """Audio configuration settings optimized to prevent overflow"""
    sample_rate: int = 16000
    chunk_size: int = 512  # Reduced from 1024 to prevent overflow
    channels: int = 1
    dtype: str = 'int16'  # sounddevice uses string format
    buffer_size: int = 8192  # Increased buffer size to handle bursts

class AudioProcessor:
    """Real-time audio processor for speech recognition"""
    
    def __init__(self, config: Optional[AudioConfig] = None):
        self.config = config or AudioConfig()
        self.stream = None
        self.is_recording = False
        self.audio_queue = queue.Queue(maxsize=100)
        self.recording_thread = None
        self.callbacks = []
        
        # Performance metrics
        self.start_time = None
        self.total_chunks = 0
        self.dropped_chunks = 0
        
        # Audio device info
        self.device_info = None
        
    def initialize(self) -> bool:
        """Initialize sounddevice and check for available devices"""
        if not SOUNDDEVICE_AVAILABLE:
            logger.error("sounddevice not available - please install with: pip install sounddevice")
            return False
            
        try:
            # Check for available input devices
            devices = sd.query_devices()
            logger.info(f"Found {len(devices)} audio devices")
            
            # Find default input device
            default_device = sd.query_devices(kind='input')
            logger.info(f"Default input device: {default_device['name']}")
            
            self.device_info = default_device
            return True
            
        except Exception as e:
            logger.error(f"Failed to initialize audio: {e}")
            return False
    
    def add_callback(self, callback: Callable[[bytes], None]):
        """Add callback function for audio data"""
        self.callbacks.append(callback)
    
    def remove_callback(self, callback: Callable[[bytes], None]):
        """Remove callback function"""
        if callback in self.callbacks:
            self.callbacks.remove(callback)
    
    def _audio_callback(self, indata, frames, time, status):
        """sounddevice callback for real-time audio capture with overflow handling"""
        if status:
            if 'input_overflow' in str(status).lower():
                # Input overflow is common and not critical - just log at debug level
                logger.debug(f"Audio input overflow - this is normal under high load")
            else:
                logger.warning(f"Audio callback status: {status}")
        
        try:
            # Convert numpy array to bytes
            audio_bytes = indata.tobytes()
            
            # Add audio data to queue with non-blocking put
            try:
                self.audio_queue.put_nowait(audio_bytes)
                self.total_chunks += 1
            except queue.Full:
                # If queue is full, remove oldest item and add new one
                try:
                    self.audio_queue.get_nowait()  # Remove oldest
                    self.audio_queue.put_nowait(audio_bytes)  # Add newest
                    self.dropped_chunks += 1
                except queue.Empty:
                    pass  # Queue became empty between operations
            
        except Exception as e:
            self.dropped_chunks += 1
            logger.debug(f"Audio callback error: {e}")
    
    def _processing_thread(self):
        """Background thread for processing audio data"""
        while self.is_recording:
            try:
                # Get audio data from queue with timeout
                audio_data = self.audio_queue.get(timeout=0.1)
                
                # Apply preprocessing
                processed_data = self._preprocess_audio(audio_data)
                
                # Call all registered callbacks
                for callback in self.callbacks:
                    try:
                        callback(processed_data)
                    except Exception as e:
                        logger.error(f"Callback error: {e}")
                
                self.audio_queue.task_done()
                
            except queue.Empty:
                continue
            except Exception as e:
                logger.error(f"Processing thread error: {e}")
    
    def _preprocess_audio(self, audio_data: bytes) -> bytes:
        """Preprocess audio data for better recognition"""
        try:
            # Convert bytes to numpy array
            audio_array = np.frombuffer(audio_data, dtype=np.int16)
            
            # Apply noise reduction (simple high-pass filter)
            if len(audio_array) > 1:
                # Simple noise gate
                threshold = np.max(np.abs(audio_array)) * 0.1
                audio_array = np.where(np.abs(audio_array) < threshold, 0, audio_array)
                
                # Normalize audio
                if np.max(np.abs(audio_array)) > 0:
                    audio_array = audio_array / np.max(np.abs(audio_array)) * 32767
                    audio_array = audio_array.astype(np.int16)
            
            return audio_array.tobytes()
            
        except Exception as e:
            logger.error(f"Audio preprocessing error: {e}")
            return audio_data
    
    def start(self) -> bool:
        """Start audio recording"""
        if self.is_recording:
            logger.warning("Already recording")
            return True
        
        try:
            if not self.device_info:
                if not self.initialize():
                    return False
            
            # Start recording
            self.is_recording = True
            self.start_time = time.time()
            self.total_chunks = 0
            self.dropped_chunks = 0
            
            # Start processing thread
            self.recording_thread = threading.Thread(target=self._processing_thread)
            self.recording_thread.daemon = True
            self.recording_thread.start()
            
            # Start audio stream with sounddevice and optimized settings
            self.stream = sd.InputStream(
                samplerate=self.config.sample_rate,
                channels=self.config.channels,
                dtype=self.config.dtype,
                blocksize=self.config.chunk_size,
                callback=self._audio_callback,
                latency='low',  # Request low latency
                extra_settings=sd.CoreAudioSettings(channel_map=[1])  # Optimize for single channel
            )
            
            self.stream.start()
            
            logger.info("Audio recording started")
            return True
            
        except Exception as e:
            logger.error(f"Failed to start recording: {e}")
            self.is_recording = False
            return False
    
    def stop(self) -> bool:
        """Stop audio recording"""
        if not self.is_recording:
            logger.warning("Not currently recording")
            return True
        
        try:
            self.is_recording = False
            
            # Stop and close stream
            if self.stream:
                self.stream.stop()
                self.stream.close()
                self.stream = None
            
            # Wait for processing thread to finish
            if self.recording_thread:
                self.recording_thread.join(timeout=2.0)
            
            # Clear audio queue
            while not self.audio_queue.empty():
                try:
                    self.audio_queue.get_nowait()
                    self.audio_queue.task_done()
                except queue.Empty:
                    break
            
            logger.info("Audio recording stopped")
            return True
            
        except Exception as e:
            logger.error(f"Failed to stop recording: {e}")
            return False
    
    def get_performance_metrics(self) -> dict:
        """Get audio processing performance metrics"""
        if not self.start_time:
            return {}
        
        duration = time.time() - self.start_time
        
        return {
            'duration': duration,
            'total_chunks': self.total_chunks,
            'dropped_chunks': self.dropped_chunks,
            'drop_rate': self.dropped_chunks / max(self.total_chunks, 1) * 100,
            'chunks_per_second': self.total_chunks / max(duration, 1),
            'queue_size': self.audio_queue.qsize(),
            'is_recording': self.is_recording
        }
    
    def get_audio_level(self) -> float:
        """Get current audio input level (0.0 to 1.0)"""
        try:
            if not self.audio_queue.empty():
                # Get latest audio data without removing from queue
                audio_data = self.audio_queue.queue[-1]
                audio_array = np.frombuffer(audio_data, dtype=np.int16)
                
                # Calculate RMS level
                rms = np.sqrt(np.mean(audio_array.astype(np.float32) ** 2))
                normalized_level = min(rms / 32767.0, 1.0)
                
                return normalized_level
            
        except Exception as e:
            logger.error(f"Failed to get audio level: {e}")
        
        return 0.0
    
    def cleanup(self):
        """Clean up audio resources"""
        self.stop()
        
        # sounddevice doesn't need explicit termination
        logger.info("Audio processor cleaned up")
    
    def __del__(self):
        """Destructor to ensure cleanup"""
        self.cleanup()

class AudioBuffer:
    """Circular buffer for audio data"""
    
    def __init__(self, max_size: int = 10):
        self.max_size = max_size
        self.buffer = []
        self.current_index = 0
    
    def add(self, audio_data: bytes):
        """Add audio data to buffer"""
        if len(self.buffer) < self.max_size:
            self.buffer.append(audio_data)
        else:
            self.buffer[self.current_index] = audio_data
            self.current_index = (self.current_index + 1) % self.max_size
    
    def get_recent(self, count: int = 5) -> list:
        """Get recent audio chunks"""
        if not self.buffer:
            return []
        
        count = min(count, len(self.buffer))
        if len(self.buffer) < self.max_size:
            return self.buffer[-count:]
        else:
            # Handle circular buffer
            result = []
            for i in range(count):
                index = (self.current_index - count + i) % self.max_size
                result.append(self.buffer[index])
            return result
    
    def clear(self):
        """Clear buffer"""
        self.buffer.clear()
        self.current_index = 0

# Auto-fallback logic
if not SOUNDDEVICE_AVAILABLE:
    logger.warning("sounddevice not available, importing fallback audio processor")
    try:
        from .audio_processor_fallback import FallbackAudioProcessor
        # Replace the main AudioProcessor with the fallback
        AudioProcessor = FallbackAudioProcessor
        logger.info("Using fallback audio processor (simulation mode)")
    except ImportError:
        logger.error("Could not import fallback audio processor")