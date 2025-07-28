"""
Performance Monitor Module for VoiceAccess
Real-time performance tracking and optimization
"""

import time
import psutil
import threading
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional
import streamlit as st
import plotly.graph_objects as go
import plotly.express as px
import pandas as pd
from dataclasses import dataclass, asdict
import logging
import os

logger = logging.getLogger(__name__)

@dataclass
class PerformanceMetrics:
    """Performance metrics data structure"""
    timestamp: datetime
    latency_ms: float
    cpu_percent: float
    memory_mb: float
    memory_percent: float
    transcription_accuracy: float
    connection_status: bool
    error_count: int
    requests_per_second: float
    audio_buffer_size: int
    dropped_frames: int

class PerformanceMonitor:
    """Real-time performance monitoring and optimization"""
    
    def __init__(self, max_history: int = 1000):
        self.max_history = max_history
        self.metrics_history: List[PerformanceMetrics] = []
        self.monitoring_active = False
        self.monitoring_thread = None
        self.start_time = datetime.now()
        
        # Performance thresholds
        self.thresholds = {
            'max_latency_ms': int(os.getenv('MAX_LATENCY_MS', 300)),
            'max_cpu_percent': 80.0,
            'max_memory_percent': 85.0,
            'min_accuracy': 0.85,
            'max_error_rate': 0.05
        }
        
        # Current metrics
        self.current_metrics = {
            'latency_ms': 0.0,
            'cpu_percent': 0.0,
            'memory_mb': 0.0,
            'memory_percent': 0.0,
            'accuracy': 0.0,
            'uptime_seconds': 0.0,
            'total_requests': 0,
            'error_count': 0,
            'connection_stable': True
        }
        
        # Performance alerts
        self.alerts = []
        self.last_alert_time = {}
        
    def start_monitoring(self, interval: float = 1.0) -> None:
        """Start performance monitoring"""
        if self.monitoring_active:
            logger.warning("Performance monitoring already active")
            return
        
        self.monitoring_active = True
        self.monitoring_thread = threading.Thread(
            target=self._monitoring_loop,
            args=(interval,),
            daemon=True
        )
        self.monitoring_thread.start()
        logger.info("Performance monitoring started")
    
    def stop_monitoring(self) -> None:
        """Stop performance monitoring"""
        self.monitoring_active = False
        if self.monitoring_thread:
            self.monitoring_thread.join(timeout=2.0)
        logger.info("Performance monitoring stopped")
    
    def _monitoring_loop(self, interval: float) -> None:
        """Main monitoring loop"""
        while self.monitoring_active:
            try:
                # Collect system metrics
                metrics = self._collect_system_metrics()
                
                # Add to history
                self.metrics_history.append(metrics)
                
                # Maintain history size
                if len(self.metrics_history) > self.max_history:
                    self.metrics_history = self.metrics_history[-self.max_history:]
                
                # Update current metrics
                self._update_current_metrics(metrics)
                
                # Check for performance issues
                self._check_performance_alerts(metrics)
                
                time.sleep(interval)
                
            except Exception as e:
                logger.error(f"Error in monitoring loop: {e}")
                time.sleep(interval)
    
    def _collect_system_metrics(self) -> PerformanceMetrics:
        """Collect current system performance metrics"""
        try:
            # System metrics
            cpu_percent = psutil.cpu_percent(interval=0.1)
            memory = psutil.virtual_memory()
            memory_mb = memory.used / (1024 * 1024)
            memory_percent = memory.percent
            
            # Application metrics (from session state if available)
            latency_ms = st.session_state.get('current_latency', 0.0)
            accuracy = st.session_state.get('current_accuracy', 0.0)
            connection_status = st.session_state.get('api_connected', False)
            error_count = st.session_state.get('error_count', 0)
            total_requests = st.session_state.get('total_requests', 0)
            audio_buffer_size = st.session_state.get('audio_buffer_size', 0)
            dropped_frames = st.session_state.get('dropped_frames', 0)
            
            # Calculate requests per second
            uptime = (datetime.now() - self.start_time).total_seconds()
            requests_per_second = total_requests / max(uptime, 1)
            
            return PerformanceMetrics(
                timestamp=datetime.now(),
                latency_ms=latency_ms,
                cpu_percent=cpu_percent,
                memory_mb=memory_mb,
                memory_percent=memory_percent,
                transcription_accuracy=accuracy,
                connection_status=connection_status,
                error_count=error_count,
                requests_per_second=requests_per_second,
                audio_buffer_size=audio_buffer_size,
                dropped_frames=dropped_frames
            )
            
        except Exception as e:
            logger.error(f"Error collecting metrics: {e}")
            return PerformanceMetrics(
                timestamp=datetime.now(),
                latency_ms=0.0,
                cpu_percent=0.0,
                memory_mb=0.0,
                memory_percent=0.0,
                transcription_accuracy=0.0,
                connection_status=False,
                error_count=0,
                requests_per_second=0.0,
                audio_buffer_size=0,
                dropped_frames=0
            )
    
    def _update_current_metrics(self, metrics: PerformanceMetrics) -> None:
        """Update current metrics dictionary"""
        self.current_metrics.update({
            'latency_ms': metrics.latency_ms,
            'cpu_percent': metrics.cpu_percent,
            'memory_mb': metrics.memory_mb,
            'memory_percent': metrics.memory_percent,
            'accuracy': metrics.transcription_accuracy,
            'uptime_seconds': (datetime.now() - self.start_time).total_seconds(),
            'total_requests': st.session_state.get('total_requests', 0),
            'error_count': metrics.error_count,
            'connection_stable': metrics.connection_status
        })
    
    def _check_performance_alerts(self, metrics: PerformanceMetrics) -> None:
        """Check for performance issues and generate alerts"""
        current_time = datetime.now()
        
        # Latency alert
        if metrics.latency_ms > self.thresholds['max_latency_ms']:
            self._add_alert(
                'high_latency',
                f"High latency detected: {metrics.latency_ms:.0f}ms (target: {self.thresholds['max_latency_ms']}ms)",
                'warning',
                current_time
            )
        
        # CPU usage alert
        if metrics.cpu_percent > self.thresholds['max_cpu_percent']:
            self._add_alert(
                'high_cpu',
                f"High CPU usage: {metrics.cpu_percent:.1f}% (threshold: {self.thresholds['max_cpu_percent']}%)",
                'warning',
                current_time
            )
        
        # Memory usage alert
        if metrics.memory_percent > self.thresholds['max_memory_percent']:
            self._add_alert(
                'high_memory',
                f"High memory usage: {metrics.memory_percent:.1f}% (threshold: {self.thresholds['max_memory_percent']}%)",
                'warning',
                current_time
            )
        
        # Accuracy alert
        if metrics.transcription_accuracy > 0 and metrics.transcription_accuracy < self.thresholds['min_accuracy']:
            self._add_alert(
                'low_accuracy',
                f"Low transcription accuracy: {metrics.transcription_accuracy:.1%} (minimum: {self.thresholds['min_accuracy']:.1%})",
                'error',
                current_time
            )
        
        # Connection alert
        if not metrics.connection_status:
            self._add_alert(
                'connection_lost',
                "Connection to transcription service lost",
                'error',
                current_time
            )
        
        # Dropped frames alert
        if metrics.dropped_frames > 10:
            self._add_alert(
                'dropped_frames',
                f"Audio frames being dropped: {metrics.dropped_frames}",
                'warning',
                current_time
            )
    
    def _add_alert(self, alert_type: str, message: str, severity: str, timestamp: datetime) -> None:
        """Add performance alert with rate limiting"""
        # Rate limiting: don't repeat same alert within 30 seconds
        if alert_type in self.last_alert_time:
            time_diff = (timestamp - self.last_alert_time[alert_type]).total_seconds()
            if time_diff < 30:
                return
        
        alert = {
            'type': alert_type,
            'message': message,
            'severity': severity,
            'timestamp': timestamp
        }
        
        self.alerts.append(alert)
        self.last_alert_time[alert_type] = timestamp
        
        # Keep only recent alerts
        if len(self.alerts) > 50:
            self.alerts = self.alerts[-50:]
        
        logger.warning(f"Performance alert: {message}")
    
    def get_current_metrics(self) -> Dict[str, Any]:
        """Get current performance metrics"""
        return self.current_metrics.copy()
    
    def get_metrics_summary(self, minutes: int = 5) -> Dict[str, Any]:
        """Get performance metrics summary for the last N minutes"""
        if not self.metrics_history:
            return {}
        
        cutoff_time = datetime.now() - timedelta(minutes=minutes)
        recent_metrics = [m for m in self.metrics_history if m.timestamp >= cutoff_time]
        
        if not recent_metrics:
            return {}
        
        # Calculate averages and statistics
        latencies = [m.latency_ms for m in recent_metrics if m.latency_ms > 0]
        cpu_values = [m.cpu_percent for m in recent_metrics]
        memory_values = [m.memory_percent for m in recent_metrics]
        accuracies = [m.transcription_accuracy for m in recent_metrics if m.transcription_accuracy > 0]
        
        summary = {
            'time_period_minutes': minutes,
            'sample_count': len(recent_metrics),
            'avg_latency_ms': sum(latencies) / len(latencies) if latencies else 0,
            'max_latency_ms': max(latencies) if latencies else 0,
            'min_latency_ms': min(latencies) if latencies else 0,
            'avg_cpu_percent': sum(cpu_values) / len(cpu_values) if cpu_values else 0,
            'max_cpu_percent': max(cpu_values) if cpu_values else 0,
            'avg_memory_percent': sum(memory_values) / len(memory_values) if memory_values else 0,
            'max_memory_percent': max(memory_values) if memory_values else 0,
            'avg_accuracy': sum(accuracies) / len(accuracies) if accuracies else 0,
            'connection_uptime_percent': sum(1 for m in recent_metrics if m.connection_status) / len(recent_metrics) * 100,
            'total_errors': sum(m.error_count for m in recent_metrics),
            'performance_score': self._calculate_performance_score(recent_metrics)
        }
        
        return summary
    
    def _calculate_performance_score(self, metrics: List[PerformanceMetrics]) -> float:
        """Calculate overall performance score (0-100)"""
        if not metrics:
            return 0.0
        
        scores = []
        
        # Latency score (lower is better)
        latencies = [m.latency_ms for m in metrics if m.latency_ms > 0]
        if latencies:
            avg_latency = sum(latencies) / len(latencies)
            latency_score = max(0, 100 - (avg_latency / self.thresholds['max_latency_ms']) * 100)
            scores.append(latency_score)
        
        # CPU score (lower is better)
        cpu_values = [m.cpu_percent for m in metrics]
        if cpu_values:
            avg_cpu = sum(cpu_values) / len(cpu_values)
            cpu_score = max(0, 100 - (avg_cpu / self.thresholds['max_cpu_percent']) * 100)
            scores.append(cpu_score)
        
        # Memory score (lower is better)
        memory_values = [m.memory_percent for m in metrics]
        if memory_values:
            avg_memory = sum(memory_values) / len(memory_values)
            memory_score = max(0, 100 - (avg_memory / self.thresholds['max_memory_percent']) * 100)
            scores.append(memory_score)
        
        # Accuracy score (higher is better)
        accuracies = [m.transcription_accuracy for m in metrics if m.transcription_accuracy > 0]
        if accuracies:
            avg_accuracy = sum(accuracies) / len(accuracies)
            accuracy_score = avg_accuracy * 100
            scores.append(accuracy_score)
        
        # Connection stability score
        connection_score = sum(1 for m in metrics if m.connection_status) / len(metrics) * 100
        scores.append(connection_score)
        
        return sum(scores) / len(scores) if scores else 0.0
    
    def display_metrics(self) -> None:
        """Display performance metrics in Streamlit"""
        if not self.monitoring_active:
            st.info("Performance monitoring is not active")
            return
        
        # Current metrics display
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            latency = self.current_metrics['latency_ms']
            latency_color = "green" if latency < 300 else "orange" if latency < 500 else "red"
            st.metric(
                "Latency",
                f"{latency:.0f}ms",
                delta=None,
                help="Current transcription latency"
            )
        
        with col2:
            cpu = self.current_metrics['cpu_percent']
            st.metric(
                "CPU Usage",
                f"{cpu:.1f}%",
                delta=None,
                help="Current CPU utilization"
            )
        
        with col3:
            memory = self.current_metrics['memory_percent']
            st.metric(
                "Memory Usage",
                f"{memory:.1f}%",
                delta=None,
                help="Current memory utilization"
            )
        
        with col4:
            accuracy = self.current_metrics['accuracy']
            st.metric(
                "Accuracy",
                f"{accuracy:.1%}" if accuracy > 0 else "N/A",
                delta=None,
                help="Transcription accuracy"
            )
        
        # Performance charts
        if len(self.metrics_history) > 1:
            self._render_performance_charts()
        
        # Performance alerts
        if self.alerts:
            self._render_alerts()
        
        # Performance summary
        summary = self.get_metrics_summary(5)
        if summary:
            self._render_performance_summary(summary)
    
    def _render_performance_charts(self) -> None:
        """Render performance charts"""
        # Prepare data
        df = pd.DataFrame([asdict(m) for m in self.metrics_history[-100:]])  # Last 100 points
        
        # Latency chart
        fig_latency = go.Figure()
        fig_latency.add_trace(go.Scatter(
            x=df['timestamp'],
            y=df['latency_ms'],
            mode='lines+markers',
            name='Latency (ms)',
            line=dict(color='#007bff', width=2),
            marker=dict(size=4)
        ))
        
        # Add target line
        fig_latency.add_hline(
            y=self.thresholds['max_latency_ms'],
            line_dash="dash",
            line_color="red",
            annotation_text=f"Target: {self.thresholds['max_latency_ms']}ms"
        )
        
        fig_latency.update_layout(
            title="Transcription Latency",
            xaxis_title="Time",
            yaxis_title="Latency (ms)",
            height=300,
            showlegend=False
        )
        
        st.plotly_chart(fig_latency, use_container_width=True)
        
        # System resources chart
        fig_resources = go.Figure()
        
        fig_resources.add_trace(go.Scatter(
            x=df['timestamp'],
            y=df['cpu_percent'],
            mode='lines',
            name='CPU %',
            line=dict(color='#28a745', width=2)
        ))
        
        fig_resources.add_trace(go.Scatter(
            x=df['timestamp'],
            y=df['memory_percent'],
            mode='lines',
            name='Memory %',
            line=dict(color='#dc3545', width=2)
        ))
        
        fig_resources.update_layout(
            title="System Resources",
            xaxis_title="Time",
            yaxis_title="Usage (%)",
            height=300,
            showlegend=True
        )
        
        st.plotly_chart(fig_resources, use_container_width=True)
    
    def _render_alerts(self) -> None:
        """Render performance alerts"""
        st.subheader("⚠️ Performance Alerts")
        
        # Show recent alerts (last 10)
        recent_alerts = self.alerts[-10:] if len(self.alerts) > 10 else self.alerts
        
        for alert in reversed(recent_alerts):  # Show newest first
            severity_colors = {
                'error': '#dc3545',
                'warning': '#ffc107',
                'info': '#17a2b8'
            }
            
            color = severity_colors.get(alert['severity'], '#6c757d')
            
            alert_html = f"""
            <div style="
                border-left: 4px solid {color};
                background-color: {color}20;
                padding: 10px;
                margin: 5px 0;
                border-radius: 0 5px 5px 0;
            ">
                <strong>{alert['severity'].upper()}</strong> - {alert['timestamp'].strftime('%H:%M:%S')}<br>
                {alert['message']}
            </div>
            """
            
            st.markdown(alert_html, unsafe_allow_html=True)
    
    def _render_performance_summary(self, summary: Dict[str, Any]) -> None:
        """Render performance summary"""
        st.subheader("📊 Performance Summary (Last 5 minutes)")
        
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.metric(
                "Avg Latency",
                f"{summary['avg_latency_ms']:.0f}ms",
                delta=f"Max: {summary['max_latency_ms']:.0f}ms"
            )
            
            st.metric(
                "Connection Uptime",
                f"{summary['connection_uptime_percent']:.1f}%"
            )
        
        with col2:
            st.metric(
                "Avg CPU",
                f"{summary['avg_cpu_percent']:.1f}%",
                delta=f"Peak: {summary['max_cpu_percent']:.1f}%"
            )
            
            st.metric(
                "Total Errors",
                f"{summary['total_errors']}"
            )
        
        with col3:
            st.metric(
                "Avg Memory",
                f"{summary['avg_memory_percent']:.1f}%",
                delta=f"Peak: {summary['max_memory_percent']:.1f}%"
            )
            
            score = summary['performance_score']
            score_color = "green" if score > 80 else "orange" if score > 60 else "red"
            st.metric(
                "Performance Score",
                f"{score:.0f}/100"
            )
    
    def get_optimization_recommendations(self) -> List[str]:
        """Get performance optimization recommendations"""
        recommendations = []
        
        if not self.metrics_history:
            return ["Start monitoring to get recommendations"]
        
        recent_metrics = self.metrics_history[-10:] if len(self.metrics_history) >= 10 else self.metrics_history
        
        # Analyze recent performance
        avg_latency = sum(m.latency_ms for m in recent_metrics if m.latency_ms > 0) / len([m for m in recent_metrics if m.latency_ms > 0]) if any(m.latency_ms > 0 for m in recent_metrics) else 0
        avg_cpu = sum(m.cpu_percent for m in recent_metrics) / len(recent_metrics)
        avg_memory = sum(m.memory_percent for m in recent_metrics) / len(recent_metrics)
        dropped_frames = sum(m.dropped_frames for m in recent_metrics)
        
        # Generate recommendations
        if avg_latency > self.thresholds['max_latency_ms']:
            recommendations.append("Reduce audio chunk size to improve latency")
            recommendations.append("Check network connection quality")
        
        if avg_cpu > self.thresholds['max_cpu_percent']:
            recommendations.append("Close unnecessary applications to reduce CPU load")
            recommendations.append("Consider reducing audio quality settings")
        
        if avg_memory > self.thresholds['max_memory_percent']:
            recommendations.append("Restart the application to free memory")
            recommendations.append("Reduce transcript history length")
        
        if dropped_frames > 5:
            recommendations.append("Increase audio buffer size")
            recommendations.append("Check microphone connection")
        
        # General recommendations
        if not recommendations:
            recommendations.extend([
                "Performance is good! Consider enabling additional features",
                "Monitor performance during peak usage",
                "Regular restarts can help maintain optimal performance"
            ])
        
        return recommendations[:5]  # Return top 5 recommendations