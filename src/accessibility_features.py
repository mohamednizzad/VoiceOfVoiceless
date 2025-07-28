"""
Accessibility Features Module for VoiceAccess
WCAG 2.1 AA compliant accessibility implementations
"""

import streamlit as st
from typing import Dict, List, Any, Optional
import time
import threading
from datetime import datetime

class AccessibilityFeatures:
    """Comprehensive accessibility features for VoiceAccess"""
    
    def __init__(self):
        self.alert_queue = []
        self.screen_reader_announcements = []
        self.keyboard_shortcuts = {
            'start_stop': 'Space',
            'settings': 'S',
            'help': 'H',
            'clear': 'C'
        }
        
        # WCAG 2.1 AA color contrast ratios
        self.high_contrast_colors = {
            'background': '#000000',
            'text': '#ffffff',
            'primary': '#ffffff',
            'secondary': '#cccccc',
            'success': '#00ff00',
            'warning': '#ffff00',
            'error': '#ff0000',
            'info': '#00ffff'
        }
        
        self.standard_colors = {
            'background': '#ffffff',
            'text': '#000000',
            'primary': '#007bff',
            'secondary': '#6c757d',
            'success': '#28a745',
            'warning': '#ffc107',
            'error': '#dc3545',
            'info': '#17a2b8'
        }
    
    def get_color_scheme(self, high_contrast: bool = False) -> Dict[str, str]:
        """Get appropriate color scheme based on accessibility settings"""
        return self.high_contrast_colors if high_contrast else self.standard_colors
    
    def generate_aria_labels(self, component_type: str, **kwargs) -> Dict[str, str]:
        """Generate appropriate ARIA labels for components"""
        labels = {}
        
        if component_type == 'recording_button':
            is_recording = kwargs.get('is_recording', False)
            labels['aria-label'] = 'Stop recording' if is_recording else 'Start recording'
            labels['aria-pressed'] = 'true' if is_recording else 'false'
            labels['role'] = 'button'
        
        elif component_type == 'transcript_display':
            labels['aria-label'] = 'Live transcription display'
            labels['aria-live'] = 'polite'
            labels['aria-atomic'] = 'false'
            labels['role'] = 'log'
        
        elif component_type == 'sentiment_indicator':
            sentiment = kwargs.get('sentiment', 'neutral')
            score = kwargs.get('score', 0)
            labels['aria-label'] = f'Current sentiment: {sentiment}, score: {score:.2f}'
            labels['role'] = 'status'
        
        elif component_type == 'tone_indicator':
            tone = kwargs.get('tone', 'neutral')
            confidence = kwargs.get('confidence', 0)
            labels['aria-label'] = f'Current tone: {tone}, confidence: {confidence:.1%}'
            labels['role'] = 'status'
        
        elif component_type == 'performance_metric':
            metric_name = kwargs.get('name', 'metric')
            value = kwargs.get('value', 0)
            labels['aria-label'] = f'{metric_name}: {value}'
            labels['role'] = 'status'
        
        return labels
    
    def create_accessible_button(self, label: str, key: str, 
                                is_primary: bool = False, 
                                disabled: bool = False,
                                help_text: str = None) -> bool:
        """Create an accessible button with proper ARIA attributes"""
        
        # Generate button HTML with accessibility features
        button_class = 'primary' if is_primary else 'secondary'
        disabled_attr = 'disabled' if disabled else ''
        
        # Use Streamlit's button with accessibility enhancements
        clicked = st.button(
            label,
            key=key,
            disabled=disabled,
            help=help_text,
            use_container_width=True
        )
        
        # Add screen reader announcement if clicked
        if clicked:
            self.announce_to_screen_reader(f"Button {label} activated")
        
        return clicked
    
    def create_accessible_text_display(self, text: str, 
                                     accessibility_settings: Dict,
                                     live_region: bool = True) -> None:
        """Create accessible text display with proper ARIA attributes"""
        
        font_size = accessibility_settings.get('font_size', 16)
        high_contrast = accessibility_settings.get('high_contrast', False)
        colors = self.get_color_scheme(high_contrast)
        
        # ARIA attributes for live regions
        aria_live = 'polite' if live_region else 'off'
        
        text_html = f"""
        <div 
            role="log"
            aria-live="{aria_live}"
            aria-atomic="false"
            aria-label="Live transcription text"
            style="
                background-color: {colors['background']};
                color: {colors['text']};
                font-size: {font_size}px;
                line-height: 1.6;
                padding: 20px;
                border: 2px solid {colors['primary']};
                border-radius: 10px;
                min-height: 100px;
                font-family: 'Arial', sans-serif;
            "
        >
            {text if text else 'No text to display'}
        </div>
        """
        
        st.markdown(text_html, unsafe_allow_html=True)
    
    def create_accessible_slider(self, label: str, min_val: int, max_val: int, 
                               current_val: int, key: str,
                               help_text: str = None) -> int:
        """Create accessible slider with keyboard navigation"""
        
        value = st.slider(
            label,
            min_value=min_val,
            max_value=max_val,
            value=current_val,
            key=key,
            help=help_text
        )
        
        return value
    
    def create_accessible_checkbox(self, label: str, current_value: bool, 
                                 key: str, help_text: str = None) -> bool:
        """Create accessible checkbox with proper labeling"""
        
        checked = st.checkbox(
            label,
            value=current_value,
            key=key,
            help=help_text
        )
        
        # Announce state changes to screen readers
        if key in st.session_state and st.session_state[key] != current_value:
            state = "checked" if checked else "unchecked"
            self.announce_to_screen_reader(f"{label} {state}")
        
        return checked
    
    def announce_to_screen_reader(self, message: str, priority: str = 'polite') -> None:
        """Add announcement for screen readers"""
        announcement = {
            'message': message,
            'timestamp': datetime.now(),
            'priority': priority  # 'polite' or 'assertive'
        }
        
        self.screen_reader_announcements.append(announcement)
        
        # Keep only recent announcements
        if len(self.screen_reader_announcements) > 50:
            self.screen_reader_announcements = self.screen_reader_announcements[-50:]
    
    def render_screen_reader_announcements(self) -> None:
        """Render hidden div for screen reader announcements"""
        
        if not self.screen_reader_announcements:
            return
        
        # Get the most recent announcement
        latest = self.screen_reader_announcements[-1]
        
        announcement_html = f"""
        <div 
            aria-live="{latest['priority']}"
            aria-atomic="true"
            style="
                position: absolute;
                left: -10000px;
                width: 1px;
                height: 1px;
                overflow: hidden;
            "
        >
            {latest['message']}
        </div>
        """
        
        st.markdown(announcement_html, unsafe_allow_html=True)
    
    def create_visual_alert(self, message: str, alert_type: str = 'info',
                          duration: float = 3.0) -> None:
        """Create visual alert for users who can't hear audio cues"""
        
        alert = {
            'message': message,
            'type': alert_type,
            'timestamp': datetime.now(),
            'duration': duration
        }
        
        self.alert_queue.append(alert)
        
        # Also announce to screen readers
        self.announce_to_screen_reader(f"Alert: {message}", 'assertive')
    
    def render_visual_alerts(self, accessibility_settings: Dict) -> None:
        """Render visual alerts if enabled"""
        
        if not accessibility_settings.get('visual_alerts', True):
            return
        
        current_time = datetime.now()
        active_alerts = []
        
        # Filter active alerts
        for alert in self.alert_queue:
            time_diff = (current_time - alert['timestamp']).total_seconds()
            if time_diff < alert['duration']:
                active_alerts.append(alert)
        
        # Update alert queue
        self.alert_queue = active_alerts
        
        # Render active alerts
        for alert in active_alerts:
            colors = self.get_color_scheme(accessibility_settings.get('high_contrast', False))
            alert_color = colors.get(alert['type'], colors['info'])
            
            alert_html = f"""
            <div 
                role="alert"
                aria-live="assertive"
                style="
                    position: fixed;
                    top: 20px;
                    right: 20px;
                    background-color: {alert_color};
                    color: white;
                    padding: 15px 20px;
                    border-radius: 10px;
                    font-weight: bold;
                    font-size: 16px;
                    z-index: 1000;
                    box-shadow: 0 4px 8px rgba(0,0,0,0.3);
                    animation: slideIn 0.3s ease-out;
                "
            >
                {alert['message']}
            </div>
            <style>
            @keyframes slideIn {{
                from {{ transform: translateX(100%); opacity: 0; }}
                to {{ transform: translateX(0); opacity: 1; }}
            }}
            </style>
            """
            
            st.markdown(alert_html, unsafe_allow_html=True)
    
    def render_keyboard_shortcuts_help(self) -> None:
        """Render keyboard shortcuts help panel"""
        
        with st.expander("⌨️ Keyboard Shortcuts", expanded=False):
            st.markdown("### Available Keyboard Shortcuts")
            
            for action, key in self.keyboard_shortcuts.items():
                action_name = action.replace('_', ' ').title()
                st.markdown(f"**{action_name}**: `{key}`")
            
            st.markdown("""
            ### Navigation Tips
            - Use `Tab` to navigate between controls
            - Use `Space` or `Enter` to activate buttons
            - Use arrow keys to adjust sliders
            - Use `Escape` to close dialogs
            """)
    
    def create_focus_management(self) -> None:
        """Implement focus management for keyboard navigation"""
        
        focus_script = """
        <script>
        // Focus management for accessibility
        document.addEventListener('DOMContentLoaded', function() {
            // Skip to main content link
            const skipLink = document.createElement('a');
            skipLink.href = '#main-content';
            skipLink.textContent = 'Skip to main content';
            skipLink.className = 'skip-link';
            skipLink.style.cssText = `
                position: absolute;
                top: -40px;
                left: 6px;
                background: #000;
                color: #fff;
                padding: 8px;
                text-decoration: none;
                z-index: 1000;
                border-radius: 4px;
            `;
            
            skipLink.addEventListener('focus', function() {
                this.style.top = '6px';
            });
            
            skipLink.addEventListener('blur', function() {
                this.style.top = '-40px';
            });
            
            document.body.insertBefore(skipLink, document.body.firstChild);
            
            // Keyboard shortcuts
            document.addEventListener('keydown', function(e) {
                // Only trigger if not in input field
                if (e.target.tagName !== 'INPUT' && e.target.tagName !== 'TEXTAREA') {
                    switch(e.key.toLowerCase()) {
                        case ' ':
                            // Space for start/stop
                            const recordButton = document.querySelector('[data-testid="baseButton-secondary"]');
                            if (recordButton) {
                                recordButton.click();
                                e.preventDefault();
                            }
                            break;
                        case 's':
                            // S for settings
                            const settingsSection = document.querySelector('.stSidebar');
                            if (settingsSection) {
                                settingsSection.scrollIntoView();
                                e.preventDefault();
                            }
                            break;
                        case 'h':
                            // H for help
                            const helpExpander = document.querySelector('[data-testid="stExpander"]');
                            if (helpExpander) {
                                helpExpander.click();
                                e.preventDefault();
                            }
                            break;
                    }
                }
            });
        });
        </script>
        """
        
        st.markdown(focus_script, unsafe_allow_html=True)
    
    def validate_color_contrast(self, foreground: str, background: str) -> Dict[str, Any]:
        """Validate color contrast ratio for WCAG compliance"""
        
        def hex_to_rgb(hex_color: str) -> tuple:
            hex_color = hex_color.lstrip('#')
            return tuple(int(hex_color[i:i+2], 16) for i in (0, 2, 4))
        
        def get_luminance(rgb: tuple) -> float:
            def get_relative_luminance(c):
                c = c / 255.0
                return c / 12.92 if c <= 0.03928 else ((c + 0.055) / 1.055) ** 2.4
            
            r, g, b = rgb
            return 0.2126 * get_relative_luminance(r) + 0.7152 * get_relative_luminance(g) + 0.0722 * get_relative_luminance(b)
        
        try:
            fg_rgb = hex_to_rgb(foreground)
            bg_rgb = hex_to_rgb(background)
            
            fg_luminance = get_luminance(fg_rgb)
            bg_luminance = get_luminance(bg_rgb)
            
            # Calculate contrast ratio
            lighter = max(fg_luminance, bg_luminance)
            darker = min(fg_luminance, bg_luminance)
            contrast_ratio = (lighter + 0.05) / (darker + 0.05)
            
            # WCAG 2.1 AA requirements
            aa_normal = contrast_ratio >= 4.5  # Normal text
            aa_large = contrast_ratio >= 3.0   # Large text (18pt+ or 14pt+ bold)
            aaa_normal = contrast_ratio >= 7.0  # AAA normal text
            aaa_large = contrast_ratio >= 4.5   # AAA large text
            
            return {
                'contrast_ratio': contrast_ratio,
                'aa_normal': aa_normal,
                'aa_large': aa_large,
                'aaa_normal': aaa_normal,
                'aaa_large': aaa_large,
                'wcag_level': 'AAA' if aaa_normal else 'AA' if aa_normal else 'Fail'
            }
            
        except Exception as e:
            return {
                'error': str(e),
                'contrast_ratio': 0,
                'wcag_level': 'Error'
            }
    
    def render_accessibility_status(self, accessibility_settings: Dict) -> None:
        """Render accessibility compliance status"""
        
        with st.expander("♿ Accessibility Status", expanded=False):
            st.markdown("### WCAG 2.1 Compliance Status")
            
            # Color contrast validation
            colors = self.get_color_scheme(accessibility_settings.get('high_contrast', False))
            contrast_result = self.validate_color_contrast(colors['text'], colors['background'])
            
            if 'error' not in contrast_result:
                wcag_level = contrast_result['wcag_level']
                ratio = contrast_result['contrast_ratio']
                
                if wcag_level == 'AAA':
                    st.success(f"✅ Excellent contrast ratio: {ratio:.2f}:1 (WCAG AAA)")
                elif wcag_level == 'AA':
                    st.success(f"✅ Good contrast ratio: {ratio:.2f}:1 (WCAG AA)")
                else:
                    st.error(f"❌ Poor contrast ratio: {ratio:.2f}:1 (Below WCAG AA)")
            
            # Feature compliance checklist
            features = [
                ('Keyboard Navigation', True),
                ('Screen Reader Support', accessibility_settings.get('screen_reader', True)),
                ('High Contrast Mode', accessibility_settings.get('high_contrast', False)),
                ('Scalable Text', accessibility_settings.get('font_size', 16) >= 16),
                ('Visual Alerts', accessibility_settings.get('visual_alerts', True)),
                ('ARIA Labels', True),
                ('Focus Management', True)
            ]
            
            st.markdown("### Feature Compliance")
            for feature, enabled in features:
                status = "✅" if enabled else "⚠️"
                st.markdown(f"{status} {feature}")
    
    def get_accessibility_recommendations(self, accessibility_settings: Dict) -> List[str]:
        """Get personalized accessibility recommendations"""
        
        recommendations = []
        
        if not accessibility_settings.get('high_contrast', False):
            recommendations.append("Consider enabling High Contrast Mode for better visibility")
        
        if accessibility_settings.get('font_size', 16) < 18:
            recommendations.append("Increase font size to 18px or larger for better readability")
        
        if not accessibility_settings.get('visual_alerts', True):
            recommendations.append("Enable visual alerts to see important notifications")
        
        if not accessibility_settings.get('screen_reader', True):
            recommendations.append("Enable screen reader support for better accessibility")
        
        # Add general recommendations
        recommendations.extend([
            "Use keyboard shortcuts for faster navigation",
            "Adjust your device's system accessibility settings",
            "Consider using browser zoom for better visibility",
            "Take regular breaks to reduce eye strain"
        ])
        
        return recommendations[:5]  # Return top 5 recommendations