"""
VoiceAccess - Real-Time Voice Transcription for Accessibility
AssemblyAI Voice Agents Challenge Submission

A Streamlit application providing real-time speech transcription, 
tone detection, and sentiment analysis for deaf and hard-of-hearing individuals.
"""

import streamlit as st
import asyncio
import json
import time
from datetime import datetime
from typing import Dict, List, Optional
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Import custom modules (to be created)
from src.audio_processor import AudioProcessor
from src.transcription_service import create_transcription_service
from src.ui_components import UIComponents
from src.accessibility_features import AccessibilityFeatures
from src.performance_monitor import PerformanceMonitor

# Page configuration
st.set_page_config(
    page_title="VoiceAccess - Real-Time Transcription",
    page_icon="🎤",
    layout="wide",
    initial_sidebar_state="expanded"
)

class VoiceAccessApp:
    """Main application class for VoiceAccess"""
    
    def __init__(self):
        self.setup_session_state()
        self.audio_processor = AudioProcessor()
        self.transcription_service = create_transcription_service()
        self.ui_components = UIComponents()
        self.accessibility = AccessibilityFeatures()
        self.performance_monitor = PerformanceMonitor()
        
    def setup_session_state(self):
        """Initialize session state variables"""
        if 'is_recording' not in st.session_state:
            st.session_state.is_recording = False
        if 'transcripts' not in st.session_state:
            st.session_state.transcripts = []
        if 'sentiment_history' not in st.session_state:
            st.session_state.sentiment_history = []
        if 'tone_history' not in st.session_state:
            st.session_state.tone_history = []
        if 'performance_metrics' not in st.session_state:
            st.session_state.performance_metrics = {}
        if 'accessibility_settings' not in st.session_state:
            st.session_state.accessibility_settings = {
                'high_contrast': False,
                'large_text': False,
                'visual_alerts': True,
                'font_size': 16
            }
    
    def render_header(self):
        """Render application header"""
        col1, col2, col3 = st.columns([2, 1, 1])
        
        with col1:
            st.title("🎤 VoiceAccess")
            st.caption("Real-time transcription for accessibility")
        
        with col2:
            # Connection status indicator
            if st.session_state.get('api_connected', False):
                st.success("🟢 Connected")
            else:
                st.error("🔴 Disconnected")
        
        with col3:
            # Performance metrics
            latency = st.session_state.performance_metrics.get('latency', 0)
            st.metric("Latency", f"{latency:.0f}ms")
    
    def render_sidebar(self):
        """Render sidebar with controls and settings"""
        with st.sidebar:
            st.header("Controls")
            
            # Recording controls
            if st.button("🎤 Start Recording" if not st.session_state.is_recording else "⏹️ Stop Recording"):
                st.session_state.is_recording = not st.session_state.is_recording
                if st.session_state.is_recording:
                    self.start_recording()
                else:
                    self.stop_recording()
            
            st.divider()
            
            # Accessibility settings
            st.header("Accessibility")
            
            st.session_state.accessibility_settings['high_contrast'] = st.checkbox(
                "High Contrast Mode",
                value=st.session_state.accessibility_settings['high_contrast']
            )
            
            st.session_state.accessibility_settings['large_text'] = st.checkbox(
                "Large Text",
                value=st.session_state.accessibility_settings['large_text']
            )
            
            st.session_state.accessibility_settings['font_size'] = st.slider(
                "Font Size",
                min_value=12,
                max_value=24,
                value=st.session_state.accessibility_settings['font_size']
            )
            
            st.divider()
            
            # Audio settings
            st.header("Audio Settings")
            
            audio_quality = st.selectbox(
                "Audio Quality",
                ["High", "Medium", "Low"],
                index=0
            )
            
            noise_reduction = st.checkbox("Noise Reduction", value=True)
            
            st.divider()
            
            # Performance monitoring
            st.header("Performance")
            
            if st.session_state.performance_metrics:
                metrics = st.session_state.performance_metrics
                st.metric("Average Latency", f"{metrics.get('avg_latency', 0):.0f}ms")
                st.metric("Accuracy", f"{metrics.get('accuracy', 0):.1f}%")
                st.metric("Uptime", f"{metrics.get('uptime', 0):.1f}%")
    
    def render_main_content(self):
        """Render main transcription area"""
        # Apply accessibility styles
        if st.session_state.accessibility_settings['high_contrast']:
            st.markdown("""
                <style>
                .main-content {
                    background-color: #000000;
                    color: #FFFFFF;
                    padding: 20px;
                    border-radius: 10px;
                }
                </style>
            """, unsafe_allow_html=True)
        
        # Main transcription display
        st.header("Live Transcription")
        
        # Create placeholder for real-time updates
        transcript_placeholder = st.empty()
        
        # Display current transcription
        if st.session_state.transcripts:
            latest_transcript = st.session_state.transcripts[-1]
            
            font_size = st.session_state.accessibility_settings['font_size']
            
            transcript_html = f"""
            <div style="
                font-size: {font_size}px;
                line-height: 1.6;
                padding: 20px;
                background-color: {'#000000' if st.session_state.accessibility_settings['high_contrast'] else '#f8f9fa'};
                color: {'#FFFFFF' if st.session_state.accessibility_settings['high_contrast'] else '#000000'};
                border-radius: 10px;
                min-height: 200px;
                border: 2px solid #007bff;
            ">
                <strong>Speaker:</strong> {latest_transcript.get('speaker', 'Unknown')}<br>
                <strong>Text:</strong> {latest_transcript.get('text', '')}<br>
                <strong>Confidence:</strong> {latest_transcript.get('confidence', 0):.2f}
            </div>
            """
            
            transcript_placeholder.markdown(transcript_html, unsafe_allow_html=True)
        else:
            transcript_placeholder.info("Click 'Start Recording' to begin transcription...")
    
    def render_analytics_panel(self):
        """Render sentiment and tone analysis"""
        col1, col2 = st.columns(2)
        
        with col1:
            st.subheader("Sentiment Analysis")
            
            if st.session_state.sentiment_history:
                latest_sentiment = st.session_state.sentiment_history[-1]
                
                # Sentiment indicator
                sentiment_score = latest_sentiment.get('score', 0)
                sentiment_label = latest_sentiment.get('label', 'Neutral')
                
                if sentiment_score > 0.1:
                    st.success(f"😊 Positive ({sentiment_score:.2f})")
                elif sentiment_score < -0.1:
                    st.error(f"😔 Negative ({sentiment_score:.2f})")
                else:
                    st.info(f"😐 Neutral ({sentiment_score:.2f})")
                
                # Sentiment chart (placeholder)
                st.line_chart([s.get('score', 0) for s in st.session_state.sentiment_history[-10:]])
            else:
                st.info("No sentiment data available")
        
        with col2:
            st.subheader("Tone Detection")
            
            if st.session_state.tone_history:
                latest_tone = st.session_state.tone_history[-1]
                
                tone_label = latest_tone.get('tone', 'Neutral')
                tone_confidence = latest_tone.get('confidence', 0)
                
                # Tone indicator with emoji
                tone_emojis = {
                    'happy': '😄',
                    'sad': '😢',
                    'angry': '😠',
                    'excited': '🤩',
                    'calm': '😌',
                    'neutral': '😐'
                }
                
                emoji = tone_emojis.get(tone_label.lower(), '😐')
                st.info(f"{emoji} {tone_label.title()} ({tone_confidence:.2f})")
                
                # Tone distribution (placeholder)
                tone_counts = {}
                for tone_data in st.session_state.tone_history[-20:]:
                    tone = tone_data.get('tone', 'neutral')
                    tone_counts[tone] = tone_counts.get(tone, 0) + 1
                
                if tone_counts:
                    st.bar_chart(tone_counts)
            else:
                st.info("No tone data available")
    
    def start_recording(self):
        """Start audio recording and transcription"""
        try:
            # Initialize audio processor
            self.audio_processor.start()
            
            # Connect to AssemblyAI
            self.transcription_service.connect()
            
            st.session_state.api_connected = True
            st.success("Recording started!")
            
        except Exception as e:
            st.error(f"Failed to start recording: {str(e)}")
            st.session_state.is_recording = False
    
    def stop_recording(self):
        """Stop audio recording and transcription"""
        try:
            # Stop audio processor
            self.audio_processor.stop()
            
            # Disconnect from AssemblyAI
            self.transcription_service.disconnect()
            
            st.session_state.api_connected = False
            st.info("Recording stopped!")
            
        except Exception as e:
            st.error(f"Failed to stop recording: {str(e)}")
    
    def run(self):
        """Main application entry point"""
        # Check API key
        if not os.getenv('ASSEMBLYAI_API_KEY'):
            st.error("⚠️ AssemblyAI API key not found. Please add it to your .env file.")
            st.stop()
        
        # Render UI components
        self.render_header()
        self.render_sidebar()
        
        # Main content area
        self.render_main_content()
        
        st.divider()
        
        # Analytics panel
        self.render_analytics_panel()
        
        # Performance monitoring (if enabled)
        if os.getenv('ENABLE_PERFORMANCE_MONITORING', 'True').lower() == 'true':
            with st.expander("Performance Metrics"):
                self.performance_monitor.display_metrics()

def main():
    """Application entry point"""
    app = VoiceAccessApp()
    app.run()

if __name__ == "__main__":
    main()