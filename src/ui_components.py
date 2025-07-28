"""
UI Components Module for VoiceAccess
Custom Streamlit components and UI utilities
"""

import streamlit as st
import plotly.graph_objects as go
import plotly.express as px
import pandas as pd
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional
import time

class UIComponents:
    """Custom UI components for VoiceAccess"""
    
    def __init__(self):
        self.theme_colors = {
            'primary': '#007bff',
            'success': '#28a745',
            'warning': '#ffc107',
            'danger': '#dc3545',
            'info': '#17a2b8',
            'light': '#f8f9fa',
            'dark': '#343a40'
        }
    
    def render_connection_status(self, is_connected: bool, latency: float = 0) -> None:
        """Render connection status indicator"""
        col1, col2 = st.columns([1, 1])
        
        with col1:
            if is_connected:
                st.success("🟢 Connected")
            else:
                st.error("🔴 Disconnected")
        
        with col2:
            if is_connected and latency > 0:
                color = "green" if latency < 300 else "orange" if latency < 500 else "red"
                st.markdown(f"<span style='color: {color}'>⚡ {latency:.0f}ms</span>", 
                           unsafe_allow_html=True)
    
    def render_audio_level_meter(self, level: float) -> None:
        """Render audio input level meter"""
        # Create a horizontal progress bar for audio level
        progress_html = f"""
        <div style="
            width: 100%;
            height: 20px;
            background-color: #e0e0e0;
            border-radius: 10px;
            overflow: hidden;
            margin: 10px 0;
        ">
            <div style="
                width: {level * 100}%;
                height: 100%;
                background: linear-gradient(90deg, 
                    #28a745 0%, 
                    #ffc107 70%, 
                    #dc3545 90%);
                transition: width 0.1s ease;
            "></div>
        </div>
        <p style="text-align: center; margin: 5px 0; font-size: 12px;">
            Audio Level: {level:.1%}
        </p>
        """
        st.markdown(progress_html, unsafe_allow_html=True)
    
    def render_transcript_display(self, transcripts: List[Dict], 
                                accessibility_settings: Dict) -> None:
        """Render the main transcript display area"""
        
        font_size = accessibility_settings.get('font_size', 16)
        high_contrast = accessibility_settings.get('high_contrast', False)
        
        # Apply styling based on accessibility settings
        bg_color = "#000000" if high_contrast else "#ffffff"
        text_color = "#ffffff" if high_contrast else "#000000"
        border_color = "#ffffff" if high_contrast else "#007bff"
        
        if not transcripts:
            placeholder_html = f"""
            <div style="
                background-color: {bg_color};
                color: {text_color};
                border: 2px dashed {border_color};
                border-radius: 10px;
                padding: 40px;
                text-align: center;
                font-size: {font_size}px;
                min-height: 200px;
                display: flex;
                align-items: center;
                justify-content: center;
            ">
                <div>
                    <h3>🎤 Ready to Listen</h3>
                    <p>Click "Start Recording" to begin real-time transcription</p>
                </div>
            </div>
            """
            st.markdown(placeholder_html, unsafe_allow_html=True)
            return
        
        # Display recent transcripts
        transcript_html = f"""
        <div style="
            background-color: {bg_color};
            color: {text_color};
            border: 2px solid {border_color};
            border-radius: 10px;
            padding: 20px;
            font-size: {font_size}px;
            line-height: 1.6;
            min-height: 300px;
            max-height: 500px;
            overflow-y: auto;
        ">
        """
        
        # Show last 10 transcripts
        recent_transcripts = transcripts[-10:] if len(transcripts) > 10 else transcripts
        
        for i, transcript in enumerate(recent_transcripts):
            timestamp = transcript.get('timestamp', datetime.now())
            speaker = transcript.get('speaker', 'Unknown')
            text = transcript.get('text', '')
            confidence = transcript.get('confidence', 0)
            is_final = transcript.get('is_final', True)
            
            # Color coding for confidence
            confidence_color = "#28a745" if confidence > 0.8 else "#ffc107" if confidence > 0.6 else "#dc3545"
            
            # Style for partial vs final transcripts
            opacity = "1.0" if is_final else "0.7"
            font_weight = "bold" if is_final else "normal"
            
            transcript_html += f"""
            <div style="
                margin-bottom: 15px;
                padding: 10px;
                background-color: {'#333333' if high_contrast else '#f8f9fa'};
                border-radius: 5px;
                opacity: {opacity};
                font-weight: {font_weight};
            ">
                <div style="
                    font-size: {font_size - 2}px;
                    color: {'#cccccc' if high_contrast else '#6c757d'};
                    margin-bottom: 5px;
                ">
                    <strong>{speaker}</strong> • {timestamp.strftime('%H:%M:%S')} • 
                    <span style="color: {confidence_color}">
                        {confidence:.1%} confidence
                    </span>
                    {'• (partial)' if not is_final else ''}
                </div>
                <div>{text}</div>
            </div>
            """
        
        transcript_html += "</div>"
        st.markdown(transcript_html, unsafe_allow_html=True)
    
    def render_sentiment_indicator(self, sentiment_data: Dict) -> None:
        """Render sentiment analysis indicator"""
        if not sentiment_data:
            st.info("😐 No sentiment data")
            return
        
        label = sentiment_data.get('label', 'neutral')
        score = sentiment_data.get('score', 0)
        confidence = sentiment_data.get('confidence', 0)
        
        # Sentiment emoji mapping
        emoji_map = {
            'positive': '😊',
            'negative': '😔',
            'neutral': '😐'
        }
        
        emoji = emoji_map.get(label, '😐')
        
        # Color coding
        if label == 'positive':
            color = "#28a745"
        elif label == 'negative':
            color = "#dc3545"
        else:
            color = "#6c757d"
        
        sentiment_html = f"""
        <div style="
            text-align: center;
            padding: 20px;
            border-radius: 10px;
            background-color: {color}20;
            border: 2px solid {color};
        ">
            <div style="font-size: 48px; margin-bottom: 10px;">{emoji}</div>
            <div style="font-size: 18px; font-weight: bold; color: {color};">
                {label.title()}
            </div>
            <div style="font-size: 14px; margin-top: 5px;">
                Score: {score:.2f} | Confidence: {confidence:.1%}
            </div>
        </div>
        """
        
        st.markdown(sentiment_html, unsafe_allow_html=True)
    
    def render_tone_indicator(self, tone_data: Dict) -> None:
        """Render tone detection indicator"""
        if not tone_data:
            st.info("🎵 No tone data")
            return
        
        tone = tone_data.get('tone', 'neutral')
        confidence = tone_data.get('confidence', 0)
        
        # Tone emoji and color mapping
        tone_config = {
            'happy': {'emoji': '😄', 'color': '#ffc107'},
            'sad': {'emoji': '😢', 'color': '#6f42c1'},
            'angry': {'emoji': '😠', 'color': '#dc3545'},
            'excited': {'emoji': '🤩', 'color': '#fd7e14'},
            'calm': {'emoji': '😌', 'color': '#20c997'},
            'neutral': {'emoji': '😐', 'color': '#6c757d'}
        }
        
        config = tone_config.get(tone, tone_config['neutral'])
        
        tone_html = f"""
        <div style="
            text-align: center;
            padding: 20px;
            border-radius: 10px;
            background-color: {config['color']}20;
            border: 2px solid {config['color']};
        ">
            <div style="font-size: 48px; margin-bottom: 10px;">{config['emoji']}</div>
            <div style="font-size: 18px; font-weight: bold; color: {config['color']};">
                {tone.title()}
            </div>
            <div style="font-size: 14px; margin-top: 5px;">
                Confidence: {confidence:.1%}
            </div>
        </div>
        """
        
        st.markdown(tone_html, unsafe_allow_html=True)
    
    def render_performance_chart(self, metrics_history: List[Dict]) -> None:
        """Render performance metrics chart"""
        if not metrics_history:
            st.info("No performance data available")
            return
        
        # Create DataFrame from metrics
        df = pd.DataFrame(metrics_history)
        
        if 'timestamp' not in df.columns:
            df['timestamp'] = pd.date_range(
                start=datetime.now() - timedelta(minutes=len(df)),
                periods=len(df),
                freq='1min'
            )
        
        # Create latency chart
        fig = go.Figure()
        
        fig.add_trace(go.Scatter(
            x=df['timestamp'],
            y=df.get('latency', [0] * len(df)),
            mode='lines+markers',
            name='Latency (ms)',
            line=dict(color='#007bff', width=2),
            marker=dict(size=6)
        ))
        
        # Add target latency line
        fig.add_hline(
            y=300,
            line_dash="dash",
            line_color="red",
            annotation_text="Target: 300ms"
        )
        
        fig.update_layout(
            title="Real-time Performance Metrics",
            xaxis_title="Time",
            yaxis_title="Latency (ms)",
            height=300,
            showlegend=True,
            template="plotly_white"
        )
        
        st.plotly_chart(fig, use_container_width=True)
    
    def render_sentiment_timeline(self, sentiment_history: List[Dict]) -> None:
        """Render sentiment analysis timeline"""
        if not sentiment_history:
            st.info("No sentiment history available")
            return
        
        # Prepare data
        timestamps = []
        scores = []
        labels = []
        
        for item in sentiment_history[-50:]:  # Last 50 items
            timestamps.append(item.get('timestamp', datetime.now()))
            scores.append(item.get('score', 0))
            labels.append(item.get('label', 'neutral'))
        
        # Create chart
        fig = go.Figure()
        
        # Color mapping for sentiment
        colors = ['#dc3545' if score < -0.1 else '#28a745' if score > 0.1 else '#6c757d' 
                 for score in scores]
        
        fig.add_trace(go.Scatter(
            x=timestamps,
            y=scores,
            mode='lines+markers',
            name='Sentiment Score',
            line=dict(color='#007bff', width=2),
            marker=dict(
                size=8,
                color=colors,
                line=dict(width=1, color='white')
            ),
            text=labels,
            hovertemplate='<b>%{text}</b><br>Score: %{y:.2f}<br>Time: %{x}<extra></extra>'
        ))
        
        # Add neutral line
        fig.add_hline(y=0, line_dash="dash", line_color="gray", opacity=0.5)
        
        fig.update_layout(
            title="Sentiment Analysis Timeline",
            xaxis_title="Time",
            yaxis_title="Sentiment Score",
            yaxis=dict(range=[-1, 1]),
            height=300,
            template="plotly_white"
        )
        
        st.plotly_chart(fig, use_container_width=True)
    
    def render_accessibility_controls(self) -> Dict[str, Any]:
        """Render accessibility control panel"""
        st.subheader("♿ Accessibility Settings")
        
        settings = {}
        
        col1, col2 = st.columns(2)
        
        with col1:
            settings['high_contrast'] = st.checkbox(
                "🌓 High Contrast Mode",
                help="Switch to high contrast colors for better visibility"
            )
            
            settings['large_text'] = st.checkbox(
                "🔍 Large Text Mode",
                help="Increase text size for better readability"
            )
        
        with col2:
            settings['visual_alerts'] = st.checkbox(
                "⚡ Visual Alerts",
                value=True,
                help="Enable visual flash notifications"
            )
            
            settings['screen_reader'] = st.checkbox(
                "📢 Screen Reader Support",
                value=True,
                help="Optimize for screen reader compatibility"
            )
        
        settings['font_size'] = st.slider(
            "📝 Font Size",
            min_value=12,
            max_value=28,
            value=16,
            step=2,
            help="Adjust text size for comfortable reading"
        )
        
        # Color theme selection
        settings['color_theme'] = st.selectbox(
            "🎨 Color Theme",
            options=['Default', 'High Contrast', 'Dark Mode', 'Colorblind Friendly'],
            help="Choose a color theme that works best for you"
        )
        
        return settings
    
    def render_visual_alert(self, message: str, alert_type: str = "info") -> None:
        """Render visual alert with flash effect"""
        colors = {
            'info': '#17a2b8',
            'success': '#28a745',
            'warning': '#ffc107',
            'error': '#dc3545'
        }
        
        color = colors.get(alert_type, colors['info'])
        
        alert_html = f"""
        <div style="
            background-color: {color};
            color: white;
            padding: 15px;
            border-radius: 10px;
            text-align: center;
            font-weight: bold;
            font-size: 18px;
            animation: flash 0.5s ease-in-out;
            margin: 10px 0;
        ">
            {message}
        </div>
        <style>
        @keyframes flash {{
            0% {{ opacity: 0; transform: scale(0.8); }}
            50% {{ opacity: 1; transform: scale(1.05); }}
            100% {{ opacity: 1; transform: scale(1); }}
        }}
        </style>
        """
        
        st.markdown(alert_html, unsafe_allow_html=True)
    
    def render_speaker_indicator(self, current_speaker: str, 
                               speaker_history: List[str]) -> None:
        """Render current speaker indicator"""
        # Get unique speakers
        unique_speakers = list(set(speaker_history)) if speaker_history else [current_speaker]
        
        speaker_html = f"""
        <div style="
            background: linear-gradient(90deg, #007bff, #0056b3);
            color: white;
            padding: 10px 20px;
            border-radius: 25px;
            text-align: center;
            font-weight: bold;
            margin: 10px 0;
        ">
            🎤 Current Speaker: {current_speaker}
        </div>
        """
        
        st.markdown(speaker_html, unsafe_allow_html=True)
        
        # Show speaker history if multiple speakers
        if len(unique_speakers) > 1:
            with st.expander(f"👥 Speakers in conversation ({len(unique_speakers)})"):
                for i, speaker in enumerate(unique_speakers, 1):
                    is_current = speaker == current_speaker
                    status = "🔴 Speaking" if is_current else "⚪ Silent"
                    st.write(f"{i}. {speaker} {status}")
    
    def apply_custom_css(self, accessibility_settings: Dict) -> None:
        """Apply custom CSS based on accessibility settings"""
        high_contrast = accessibility_settings.get('high_contrast', False)
        font_size = accessibility_settings.get('font_size', 16)
        
        css = f"""
        <style>
        .main .block-container {{
            padding-top: 2rem;
            padding-bottom: 2rem;
        }}
        
        .stButton > button {{
            width: 100%;
            border-radius: 10px;
            font-weight: bold;
            font-size: {font_size}px;
        }}
        
        .stSelectbox > div > div {{
            font-size: {font_size}px;
        }}
        
        .stCheckbox > label {{
            font-size: {font_size}px;
        }}
        
        .stSlider > div > div {{
            font-size: {font_size}px;
        }}
        """
        
        if high_contrast:
            css += """
            .stApp {
                background-color: #000000;
                color: #ffffff;
            }
            
            .stSidebar {
                background-color: #1a1a1a;
            }
            
            .stButton > button {
                background-color: #ffffff;
                color: #000000;
                border: 2px solid #ffffff;
            }
            
            .stButton > button:hover {
                background-color: #cccccc;
                border-color: #cccccc;
            }
            """
        
        css += "</style>"
        st.markdown(css, unsafe_allow_html=True)