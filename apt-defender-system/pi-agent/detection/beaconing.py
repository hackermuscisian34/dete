"""
Beaconing Detector - Detect periodic C2 communications
"""
import logging
from typing import List, Dict
from datetime import datetime
from collections import defaultdict
import numpy as np

logger = logging.getLogger(__name__)

class BeaconingDetector:
    """Statistical analysis for beaconing detection"""
    
    def __init__(self, min_connections: int = 10, max_jitter_percent: float = 0.05):
        """
        Args:
            min_connections: Minimum connections to consider for beaconing
            max_jitter_percent: Maximum jitter (5% = 0.05) to flag as beaconing
        """
        self.min_connections = min_connections
        self.max_jitter_percent = max_jitter_percent
    
    def analyze_connections(self, connections: List[Dict]) -> List[Dict]:
        """
        Analyze network connections for beaconing patterns
        
        Args:
            connections: List of connection records with 'dst_ip', 'timestamp', 'process_name'
        
        Returns:
            List of beaconing detections
        """
        # Group connections by destination IP
        grouped = defaultdict(list)
        
        for conn in connections:
            key = (conn.get('dst_ip'), conn.get('process_name'))
            grouped[key].append(conn.get('timestamp'))
        
        detections = []
        
        for (dst_ip, process_name), timestamps in grouped.items():
            if len(timestamps) < self.min_connections:
                continue
            
            # Analyze timing pattern
            result = self._analyze_timing_pattern(timestamps)
            
            if result['is_beaconing']:
                detections.append({
                    "dst_ip": dst_ip,
                    "process_name": process_name,
                    "connection_count": len(timestamps),
                    "average_interval_seconds": result['avg_interval'],
                    "jitter_percent": result['jitter_percent'],
                    "severity": self._calculate_severity(result),
                    "explanation": self._generate_explanation(dst_ip, process_name, result),
                    "recommended_action": "investigate"
                })
        
        return detections
    
    def _analyze_timing_pattern(self, timestamps: List[datetime]) -> Dict:
        """
        Analyze timing pattern of connections
        
        Statistical beaconing detection based on:
        - Regularity (low jitter)
        - Periodic intervals
        """
        if len(timestamps) < 2:
            return {"is_beaconing": False}
        
        # Sort timestamps
        sorted_times = sorted(timestamps)
        
        # Calculate intervals between connections
        intervals = []
        for i in range(1, len(sorted_times)):
            delta = (sorted_times[i] - sorted_times[i-1]).total_seconds()
            intervals.append(delta)
        
        if not intervals:
            return {"is_beaconing": False}
        
        # Calculate statistics
        avg_interval = np.mean(intervals)
        std_interval = np.std(intervals)
        
        # Calculate jitter (coefficient of variation)
        jitter = std_interval / avg_interval if avg_interval > 0 else 1.0
        
        # Beaconing if:
        # 1. Low jitter (regular intervals)
        # 2. Reasonable interval (not immediate connections)
        is_beaconing = (
            jitter < self.max_jitter_percent and
            avg_interval > 1.0  # At least 1 second apart
        )
        
        return {
            "is_beaconing": is_beaconing,
            "avg_interval": avg_interval,
            "std_interval": std_interval,
            "jitter_percent": jitter,
            "connection_count": len(timestamps)
        }
    
    def _calculate_severity(self, analysis: Dict) -> int:
        """Calculate threat severity (1-10)"""
        jitter = analysis['jitter_percent']
        interval = analysis['avg_interval']
        count = analysis['connection_count']
        
        # Lower jitter = more suspicious
        # More connections = more confident
        # Common beacon intervals: 60s, 120s, 300s
        
        severity = 5  # Base severity
        
        # Very low jitter (< 1%)
        if jitter < 0.01:
            severity += 3
        elif jitter < 0.02:
            severity += 2
        elif jitter < 0.05:
            severity += 1
        
        # Many connections
        if count > 50:
            severity += 2
        elif count > 20:
            severity += 1
        
        return min(severity, 10)
    
    def _generate_explanation(self, dst_ip: str, process_name: str, analysis: Dict) -> str:
        """Generate human-readable explanation"""
        interval = int(analysis['avg_interval'])
        count = analysis['connection_count']
        jitter = analysis['jitter_percent'] * 100
        
        return (
            f"A program ({process_name}) is connecting to {dst_ip} every {interval} seconds "
            f"with very regular timing ({jitter:.1f}% variation). "
            f"This pattern was observed {count} times and is typical of malware "
            f"communicating with an attacker's command server."
        )
