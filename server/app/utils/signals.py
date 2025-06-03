"""
Signal definitions for the detection system.

This module defines all the signals (events) that can be emitted and subscribed to
in the detection system using blinker.
"""
from blinker import signal

# Detection events
detection_made = signal('detection.made')  # Emitted for any detection
high_confidence_detection_made = signal('detection.high_confidence')  # Emitted only for high confidence detections
snapshot_made = signal('snapshot.made')  # Emitted for any snapshot