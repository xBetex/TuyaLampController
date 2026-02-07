"""
Tabs package - UI tab components for Smart Lamp Controller
"""

from .base_tab import BaseTab
from .white_light_tab import WhiteLightTab
from .color_tab import ColorTab
from .effects_tab import EffectsTab
from .ambilight_tab import AmbilightTab

__all__ = [
    'BaseTab',
    'WhiteLightTab',
    'ColorTab',
    'EffectsTab',
    'AmbilightTab',
]

# Audio tab is only available if audio dependencies are present
try:
    from .audio_tab import AudioTab
    __all__.append('AudioTab')
    AUDIO_TAB_AVAILABLE = True
except ImportError:
    AudioTab = None
    AUDIO_TAB_AVAILABLE = False
