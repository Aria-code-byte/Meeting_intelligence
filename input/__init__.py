"""
Meeting input module.

Provides unified interfaces for acquiring meeting content from multiple sources:
- Audio file upload
- Video file upload (with audio extraction)
- In-app audio recording
"""

from input.types import MeetingInputResult

__all__ = ["MeetingInputResult"]
