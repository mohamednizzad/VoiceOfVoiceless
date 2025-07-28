"""
Fallback Audio Processor for VoiceAccess
Works without external audio libraries for testing
"""

import threading
import time
import numpy as np
import queue
from typing import Optional, Callable
import logging
from dataclasses import dataclass
import os
import random

logger = logging.getLogger(__name__)

@dataclass
class AudioConfig:
    """Audio configuration settings"""
    sample_rate: int = 16000
    chunk_size: int = 1024
    channels: int = 1
    dtype: str = 'int16'
    buffer_size: int = 4096

class FallbackAudioProcessor:
    """Fallback audio processor that simulates audio input"""
    
    def __init__(self, config: Optional[AudioConfig] = None):
        self.config = config or AudioConfig()
        self.is_recording = False
        self.audio_queue = queue.Queue(maxsize=100)
        self.recording_thread = None
        self.callbacks = []
        
        # Performance metrics
        self.start_time = None
        self.total_chunks = 0
        self.dropped_chunks = 0
        
        # Simulation parameters
        self.simulation_active = False
        
    def initialize(self) -> bool:
        """Initialize fallback audio processor"""
        try:
            logger.info("Initializing fallback audio processor (simulation mode)")
            logger.warning("No real audio input - using simulation for testing")
            return True
        except Exception as e:
            logger.error(f"Failed to initialize fallback audio: {e}")
            return False
    
    def add_callback(self, callback: Callable[[bytes], None]):
        """Add callback function for audio data"""
        self.callbacks.append(callback)
    
    def remove_callback(self, callback: Callable[[bytes], None]):
        """Remove callback function"""
        if callback in self.callbacks:
            self.callbacks.remove(callback)
    
    def _generate_mock_audio(self) -> bytes:
        """Generate mock audio data for testing"""
        # Generate some random audio-like data
        samples = np.random.randint(-1000, 1000, self.config.chunk_size, dtype=np.int16)
        
        # Add some periodic patterns to make it more realistic
        t = np.linspace(0, 1, self.config.chunk_size)
        sine_wave = (np.sin(2 * np.pi * 440 * t) * 500).astype(np.int16)  # 440 Hz tone
        
        # Mix random noise with sine wave
        mixed = (samples * 0.3 + sine_wave * 0.7).astype(np.int16)
        
        return mixed.tobytes()
    
    def _simulation_thread(self):
        """Thread that generates mock audio data"""
        chunk_duration = self.config.chunk_size / self.config.sample_rate
        
        while self.simulation_active:
            try:
                # Generate mock audio data
                audio_data = self._generate_mock_audio()
                
                # Add to queue
                if not self.audio_queue.full():
                    self.audio_queue.put(audio_data, block=False)
                    self.total_chunks += 1
                else:
                    self.dropped_chunks += 1
                    logger.warning("Audio buffer full, dropping chunk")
                
                # Sleep to simulate real-time audio
                time.sleep(chunk_duration)
                
            except Exception as e:
                logger.error(f"Error in simulation thread: {e}")
                time.sleep(0.1)
    
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
        """Preprocess audio data"""
        try:
            # Convert bytes to numpy array
            audio_array = np.frombuffer(audio_data, dtype=np.int16)
            
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
        """Start audio recording simulation"""
        if self.is_recording:
            logger.warning("Already recording")
            return True
        
        try:
            if not self.initialize():
                return False
            
            # Start recording
            self.is_recording = True
            self.simulation_active = True
            self.start_time = time.time()
            self.total_chunks = 0
            self.dropped_chunks = 0
            
            # Start simulation thread
            self.simulation_thread = threading.Thread(target=self._simulation_thread)
            self.simulation_thread.daemon = True
            self.simulation_thread.start()
            
            # Start processing thread
            self.recording_thread = threading.Thread(target=self._processing_thread)
            self.recording_thread.daemon = True
            self.recording_thread.start()
            
            logger.info("Fallback audio recording started (simulation mode)")
            return True
            
        except Exception as e:
            logger.error(f"Failed to start recording: {e}")
            self.is_recording = False
            self.simulation_active = False
            return False
    
    def stop(self) -> bool:
        """Stop audio recording simulation"""
        if not self.is_recording:
            logger.warning("Not currently recording")
            return True
        
        try:
            self.is_recording = False
            self.simulation_active = False
            
            # Wait for threads to finish
            if hasattr(self, 'simulation_thread') and self.simulation_thread:
                self.simulation_thread.join(timeout=2.0)
            
            if self.recording_thread:
                self.recording_thread.join(timeout=2.0)
            
            # Clear audio queue
            while not self.audio_queue.empty():
                try:
                    self.audio_queue.get_nowait()
                    self.audio_queue.task_done()
                except queue.Empty:
                    break
            
            logger.info("Fallback audio recording stopped")
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
            'is_recording': self.is_recording,
            'mode': 'simulation'
        }
    
    def get_audio_level(self) -> float:
        """Get simulated audio input level"""
        if self.is_recording:
            # Return a random level that varies over time
            return random.uniform(0.1, 0.8)
        return 0.0
    
    def cleanup(self):
        """Clean up audio resources"""
        self.stop()
        logger.info("Fallback audio processor cleaned up")
    
    def __del__(self):
        """Destructor to ensure cleanup"""
        self.cleanup()

# Alias for compatibility
AudioProcessor = FallbackAudioProcessor