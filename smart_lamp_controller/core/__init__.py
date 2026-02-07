"""
Core package - Core functionality for Smart Lamp Controller
"""

from .device_manager import DeviceManager
from .audio_processor import AudioProcessor, AUDIO_AVAILABLE
from .ambilight_processor import AmbilightProcessor, AMBILIGHT_AVAILABLE
from .smart_ambient_processor import SmartAmbientProcessor
from .effects_engine import EffectsEngine
from .color_selection_logic import ColorSelectionLogic, SCREEN_CAPTURE_AVAILABLE

# Color decision types
try:
    from .color_decision import (
        ColorScoreBreakdown,
        ColorCandidate,
        ColorDecisionReport,
    )
    COLOR_DECISION_AVAILABLE = True
except ImportError:
    COLOR_DECISION_AVAILABLE = False

__all__ = [
    'DeviceManager',
    'AudioProcessor',
    'AUDIO_AVAILABLE',
    'AmbilightProcessor',
    'AMBILIGHT_AVAILABLE',
    'SmartAmbientProcessor',
    'EffectsEngine',
    'ColorSelectionLogic',
    'SCREEN_CAPTURE_AVAILABLE',
    'ColorScoreBreakdown',
    'ColorCandidate',
    'ColorDecisionReport',
    'COLOR_DECISION_AVAILABLE',
]
