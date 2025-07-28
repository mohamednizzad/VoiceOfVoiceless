"""
Transcription Service Module for VoiceAccess
Handles AssemblyAI Universal-Streaming integration
"""

import asyncio
import json
import time
import websockets
import threading
from typing import Optional, Callable, Dict, Any
import logging
from dataclasses import dataclass
import os
from datetime import datetime
import assemblyai as aai

logger = logging.getLogger(__name__)

@dataclass
class TranscriptionResult:
    """Transcription result data structure"""
    text: str
    confidence: float
    speaker: Optional[str] = None
    timestamp: Optional[datetime] = None
    is_final: bool = False
    sentiment: Optional[Dict[str, Any]] = None
    tone: Optional[Dict[str, Any]] = None

class TranscriptionService:
    """Real-time transcription service using AssemblyAI Universal-Streaming"""
    
    def __init__(self):
        self.api_key = os.getenv('ASSEMBLYAI_API_KEY')
        self.transcriber = None
        self.is_connected = False
        self.callbacks = []
        self.session_id = None
        
        # Performance tracking
        self.start_time = None
        self.total_requests = 0
        self.total_latency = 0
        self.error_count = 0
        
        # Configuration
        self.config = {
            'sample_rate': int(os.getenv('AUDIO_SAMPLE_RATE', 16000)),
            'enable_speaker_diarization': os.getenv('ENABLE_SPEAKER_DIARIZATION', 'True').lower() == 'true',
            'enable_sentiment_analysis': os.getenv('ENABLE_SENTIMENT_ANALYSIS', 'True').lower() == 'true',
            'enable_tone_detection': os.getenv('ENABLE_TONE_DETECTION', 'True').lower() == 'true',
            'confidence_threshold': float(os.getenv('CONFIDENCE_THRESHOLD', 0.7))
        }
        
        # Initialize AssemblyAI
        if self.api_key:
            aai.settings.api_key = self.api_key
        else:
            logger.error("AssemblyAI API key not found")
    
    def add_callback(self, callback: Callable[[TranscriptionResult], None]):
        """Add callback for transcription results"""
        self.callbacks.append(callback)
    
    def remove_callback(self, callback: Callable[[TranscriptionResult], None]):
        """Remove callback"""
        if callback in self.callbacks:
            self.callbacks.remove(callback)
    
    def _on_data(self, transcript: aai.RealtimeTranscript):
        """Handle real-time transcription data"""
        try:
            request_start = time.time()
            
            # Skip partial transcripts if confidence is too low
            if not transcript.partial and hasattr(transcript, 'confidence'):
                if transcript.confidence < self.config['confidence_threshold']:
                    return
            
            # Create transcription result
            result = TranscriptionResult(
                text=transcript.text,
                confidence=getattr(transcript, 'confidence', 0.0),
                speaker=getattr(transcript, 'speaker', None),
                timestamp=datetime.now(),
                is_final=not transcript.partial
            )
            
            # Add sentiment analysis if enabled
            if self.config['enable_sentiment_analysis'] and hasattr(transcript, 'sentiment'):
                result.sentiment = self._extract_sentiment(transcript)
            
            # Add tone detection if enabled
            if self.config['enable_tone_detection']:
                result.tone = self._detect_tone(transcript.text)
            
            # Calculate latency
            latency = (time.time() - request_start) * 1000
            self.total_latency += latency
            self.total_requests += 1
            
            # Call all registered callbacks
            for callback in self.callbacks:
                try:
                    callback(result)
                except Exception as e:
                    logger.error(f"Callback error: {e}")
            
            logger.debug(f"Transcription processed in {latency:.2f}ms")
            
        except Exception as e:
            logger.error(f"Error processing transcription data: {e}")
            self.error_count += 1
    
    def _on_error(self, error: aai.RealtimeError):
        """Handle transcription errors with improved error handling"""
        logger.error(f"Transcription error: {error}")
        self.error_count += 1
        
        # Handle specific error types
        error_str = str(error).lower()
        
        if "model deprecated" in error_str or "4105" in str(error):
            logger.error("Model deprecated error - need to update AssemblyAI SDK or use new model")
            logger.info("Attempting to reconnect with updated configuration...")
            threading.Thread(target=self._reconnect, daemon=True).start()
        elif "connection" in error_str or "websocket" in error_str:
            logger.info("Connection error - attempting to reconnect...")
            threading.Thread(target=self._reconnect, daemon=True).start()
        elif "rate limit" in error_str:
            logger.warning("Rate limit exceeded - waiting before reconnect...")
            time.sleep(5)
            threading.Thread(target=self._reconnect, daemon=True).start()
        else:
            logger.warning(f"Unhandled error type: {error}")
            # Still attempt reconnect for unknown errors
            threading.Thread(target=self._reconnect, daemon=True).start()
    
    def _extract_sentiment(self, transcript) -> Dict[str, Any]:
        """Extract sentiment information from transcript"""
        try:
            # This would be implemented based on AssemblyAI's sentiment analysis
            # For now, we'll simulate sentiment analysis
            text = transcript.text.lower()
            
            # Simple sentiment analysis based on keywords
            positive_words = ['good', 'great', 'excellent', 'happy', 'love', 'amazing', 'wonderful']
            negative_words = ['bad', 'terrible', 'awful', 'hate', 'sad', 'angry', 'horrible']
            
            positive_count = sum(1 for word in positive_words if word in text)
            negative_count = sum(1 for word in negative_words if word in text)
            
            if positive_count > negative_count:
                sentiment_score = min(0.8, positive_count * 0.3)
                sentiment_label = 'positive'
            elif negative_count > positive_count:
                sentiment_score = max(-0.8, -negative_count * 0.3)
                sentiment_label = 'negative'
            else:
                sentiment_score = 0.0
                sentiment_label = 'neutral'
            
            return {
                'label': sentiment_label,
                'score': sentiment_score,
                'confidence': 0.75
            }
            
        except Exception as e:
            logger.error(f"Sentiment extraction error: {e}")
            return {'label': 'neutral', 'score': 0.0, 'confidence': 0.0}
    
    def _detect_tone(self, text: str) -> Dict[str, Any]:
        """Detect tone from text"""
        try:
            text_lower = text.lower()
            
            # Simple tone detection based on patterns
            tone_patterns = {
                'excited': ['!', 'wow', 'amazing', 'incredible', 'fantastic'],
                'calm': ['okay', 'fine', 'sure', 'alright', 'peaceful'],
                'angry': ['damn', 'hell', 'angry', 'mad', 'furious'],
                'sad': ['sad', 'depressed', 'down', 'unhappy', 'crying'],
                'happy': ['happy', 'joy', 'cheerful', 'glad', 'delighted'],
                'neutral': []
            }
            
            tone_scores = {}
            for tone, patterns in tone_patterns.items():
                score = sum(1 for pattern in patterns if pattern in text_lower)
                if tone == 'excited' and '!' in text:
                    score += text.count('!')
                tone_scores[tone] = score
            
            # Find dominant tone
            max_tone = max(tone_scores.items(), key=lambda x: x[1])
            
            if max_tone[1] > 0:
                tone_label = max_tone[0]
                confidence = min(0.9, max_tone[1] * 0.3)
            else:
                tone_label = 'neutral'
                confidence = 0.5
            
            return {
                'tone': tone_label,
                'confidence': confidence,
                'scores': tone_scores
            }
            
        except Exception as e:
            logger.error(f"Tone detection error: {e}")
            return {'tone': 'neutral', 'confidence': 0.0, 'scores': {}}
    
    def connect(self) -> bool:
        """Connect to AssemblyAI real-time transcription with updated model"""
        try:
            if not self.api_key:
                logger.error("API key not available")
                return False
            
            # Create real-time transcriber with updated configuration
            self.transcriber = aai.RealtimeTranscriber(
                sample_rate=self.config['sample_rate'],
                on_data=self._on_data,
                on_error=self._on_error,
                # Use the new Universal-Streaming model
                model='universal-streaming'
            )
            
            # Connect to the service
            self.transcriber.connect()
            self.is_connected = True
            self.start_time = time.time()
            self.session_id = f"session_{int(time.time())}"
            
            logger.info("Connected to AssemblyAI Universal-Streaming (updated model)")
            return True
            
        except Exception as e:
            logger.error(f"Failed to connect to transcription service: {e}")
            logger.info("Attempting fallback connection without model specification...")
            
            # Fallback: try without model specification
            try:
                self.transcriber = aai.RealtimeTranscriber(
                    sample_rate=self.config['sample_rate'],
                    on_data=self._on_data,
                    on_error=self._on_error
                )
                
                self.transcriber.connect()
                self.is_connected = True
                self.start_time = time.time()
                self.session_id = f"session_{int(time.time())}"
                
                logger.info("Connected to AssemblyAI with fallback configuration")
                return True
                
            except Exception as fallback_error:
                logger.error(f"Fallback connection also failed: {fallback_error}")
                self.is_connected = False
                return False
    
    def disconnect(self) -> bool:
        """Disconnect from transcription service"""
        try:
            if self.transcriber and self.is_connected:
                self.transcriber.close()
                self.is_connected = False
                logger.info("Disconnected from transcription service")
            
            return True
            
        except Exception as e:
            logger.error(f"Error disconnecting: {e}")
            return False
    
    def _reconnect(self):
        """Attempt to reconnect to the service"""
        max_retries = 3
        retry_delay = 2
        
        for attempt in range(max_retries):
            logger.info(f"Reconnection attempt {attempt + 1}/{max_retries}")
            
            # Disconnect first
            self.disconnect()
            
            # Wait before retry
            time.sleep(retry_delay)
            
            # Try to reconnect
            if self.connect():
                logger.info("Reconnection successful")
                return
            
            retry_delay *= 2  # Exponential backoff
        
        logger.error("Failed to reconnect after maximum retries")
    
    def stream_audio(self, audio_data: bytes):
        """Stream audio data for transcription"""
        try:
            if not self.is_connected or not self.transcriber:
                logger.warning("Not connected to transcription service")
                return False
            
            # Stream audio data
            self.transcriber.stream(audio_data)
            return True
            
        except Exception as e:
            logger.error(f"Error streaming audio: {e}")
            self.error_count += 1
            return False
    
    def get_performance_metrics(self) -> Dict[str, Any]:
        """Get transcription service performance metrics"""
        if not self.start_time:
            return {}
        
        duration = time.time() - self.start_time
        avg_latency = self.total_latency / max(self.total_requests, 1)
        
        return {
            'session_id': self.session_id,
            'is_connected': self.is_connected,
            'duration': duration,
            'total_requests': self.total_requests,
            'error_count': self.error_count,
            'error_rate': self.error_count / max(self.total_requests, 1) * 100,
            'average_latency_ms': avg_latency,
            'requests_per_second': self.total_requests / max(duration, 1),
            'uptime_percentage': ((duration - (self.error_count * 0.1)) / max(duration, 1)) * 100
        }
    
    def get_connection_status(self) -> Dict[str, Any]:
        """Get current connection status"""
        return {
            'connected': self.is_connected,
            'session_id': self.session_id,
            'api_key_configured': bool(self.api_key),
            'last_error_count': self.error_count,
            'configuration': self.config
        }

class MockTranscriptionService(TranscriptionService):
    """Mock transcription service for testing without API key or when model is deprecated"""
    
    def __init__(self):
        super().__init__()
        self.mock_responses = [
            "Hello, how are you today?",
            "This is a test of the transcription system.",
            "The weather is really nice outside.",
            "I hope this application works well.",
            "Thank you for using VoiceAccess.",
            "The audio quality sounds good.",
            "Real-time transcription is working.",
            "This demonstrates the accessibility features.",
            "The sentiment analysis is functioning.",
            "Voice recognition technology is amazing."
        ]
        self.response_index = 0
        self.mock_thread = None
    
    def connect(self) -> bool:
        """Mock connection"""
        self.is_connected = True
        self.start_time = time.time()
        self.session_id = f"mock_session_{int(time.time())}"
        logger.info("Connected to mock transcription service")
        return True
    
    def stream_audio(self, audio_data: bytes):
        """Mock audio streaming with simulated responses"""
        if not self.is_connected:
            return False
        
        # Simulate transcription with delay
        if not self.mock_thread or not self.mock_thread.is_alive():
            self.mock_thread = threading.Thread(target=self._generate_mock_response)
            self.mock_thread.daemon = True
            self.mock_thread.start()
        
        return True
    
    def _generate_mock_response(self):
        """Generate mock transcription response"""
        time.sleep(0.2)  # Simulate processing delay
        
        text = self.mock_responses[self.response_index % len(self.mock_responses)]
        self.response_index += 1
        
        result = TranscriptionResult(
            text=text,
            confidence=0.95,
            speaker="Speaker 1",
            timestamp=datetime.now(),
            is_final=True,
            sentiment={'label': 'positive', 'score': 0.3, 'confidence': 0.8},
            tone={'tone': 'neutral', 'confidence': 0.7}
        )
        
        # Call callbacks
        for callback in self.callbacks:
            try:
                callback(result)
            except Exception as e:
                logger.error(f"Mock callback error: {e}")
        
        self.total_requests += 1
        self.total_latency += 200  # Mock 200ms latency

def create_transcription_service() -> TranscriptionService:
    """Factory function to create appropriate transcription service"""
    api_key = os.getenv('ASSEMBLYAI_API_KEY')
    
    if not api_key:
        logger.warning("No API key found - using mock transcription service")
        return MockTranscriptionService()
    
    # Try to create real service
    try:
        service = TranscriptionService()
        # Test connection
        if service.connect():
            logger.info("Real transcription service created successfully")
            service.disconnect()  # Disconnect test connection
            return service
        else:
            logger.warning("Failed to connect to real service - using mock")
            return MockTranscriptionService()
    except Exception as e:
        logger.error(f"Error creating transcription service: {e}")
        logger.warning("Falling back to mock transcription service")
        return MockTranscriptionService()