#!/usr/bin/env python3
"""
Color Decision - Data structures for tracking and explaining color selection decisions
Provides transparency into why specific colors are chosen for ambient lighting
"""

from dataclasses import dataclass, field
from datetime import datetime
from typing import Tuple, List, Optional
try:
    from PIL import Image
    PIL_AVAILABLE = True
except ImportError:
    PIL_AVAILABLE = False
    Image = None


@dataclass
class ColorScoreBreakdown:
    """Detailed breakdown of how a color's ambient score was calculated"""

    # Score components (points)
    saturation_score: float = 0.0      # 0-80 points
    brightness_score: float = 0.0       # -50 to +30 points
    prevalence_score: float = 0.0       # 0-25 points
    hue_preference_score: float = 0.0   # 8-20 points
    penalties: float = 0.0              # Negative adjustments

    # Explanation strings
    saturation_reason: str = ""
    brightness_reason: str = ""
    prevalence_reason: str = ""
    hue_reason: str = ""
    penalty_reasons: List[str] = field(default_factory=list)

    @property
    def total_score(self) -> float:
        """Calculate total score from components"""
        return max(0, (
            self.saturation_score +
            self.brightness_score +
            self.prevalence_score +
            self.hue_preference_score +
            self.penalties
        ))

    def get_summary(self) -> str:
        """Get a one-line summary of the scoring"""
        parts = []
        if self.saturation_score > 0:
            parts.append(f"Sat:{self.saturation_score:.0f}")
        if self.brightness_score != 0:
            parts.append(f"Bri:{self.brightness_score:+.0f}")
        if self.prevalence_score > 0:
            parts.append(f"Prev:{self.prevalence_score:.0f}")
        if self.hue_preference_score > 0:
            parts.append(f"Hue:{self.hue_preference_score:.0f}")
        if self.penalties < 0:
            parts.append(f"Pen:{self.penalties:.0f}")
        return " | ".join(parts) + f" = {self.total_score:.0f}"


@dataclass
class ColorCandidate:
    """A color being considered for ambient lighting"""

    hex_color: str
    rgb: Tuple[int, int, int]
    hsv: Tuple[float, float, float]
    screen_percentage: float
    score_breakdown: ColorScoreBreakdown
    is_winner: bool = False
    rejection_reason: Optional[str] = None  # Why it was rejected (if applicable)

    @property
    def total_score(self) -> float:
        """Get total score from breakdown"""
        return self.score_breakdown.total_score

    @property
    def hue_degrees(self) -> float:
        """Get hue in degrees (0-360)"""
        return self.hsv[0] * 360

    @property
    def saturation_percent(self) -> float:
        """Get saturation as percentage"""
        return self.hsv[1] * 100

    @property
    def brightness_percent(self) -> float:
        """Get brightness/value as percentage"""
        return self.hsv[2] * 100


@dataclass
class ColorDecisionReport:
    """Complete report of a color selection decision"""

    timestamp: datetime
    winner: Optional[ColorCandidate]
    candidates: List[ColorCandidate]  # All considered colors with scores
    screen_thumbnail: Optional[any] = None  # PIL Image if available
    decision_summary: str = ""  # Human-readable explanation

    @classmethod
    def create(
        cls,
        winner: Optional[ColorCandidate],
        candidates: List[ColorCandidate],
        screen_thumbnail: Optional[any] = None
    ) -> "ColorDecisionReport":
        """Create a decision report with auto-generated summary"""
        report = cls(
            timestamp=datetime.now(),
            winner=winner,
            candidates=candidates,
            screen_thumbnail=screen_thumbnail,
            decision_summary=""
        )
        report.decision_summary = report._generate_summary()
        return report

    def _generate_summary(self) -> str:
        """Generate a human-readable summary of the decision"""
        if not self.winner:
            return "No suitable colors found on screen - all candidates were rejected due to low saturation or extreme brightness."

        w = self.winner
        breakdown = w.score_breakdown

        # Build explanation
        parts = []

        # Hue explanation
        hue_name = self._get_hue_name(w.hue_degrees)
        parts.append(f"{hue_name} hue ({w.hue_degrees:.0f}°) - {breakdown.hue_reason.split(' - ')[-1] if ' - ' in breakdown.hue_reason else 'selected'}")

        # Saturation explanation
        if w.saturation_percent >= 70:
            parts.append(f"High saturation ({w.saturation_percent:.0f}%) ensures vivid appearance")
        else:
            parts.append(f"Saturation of {w.saturation_percent:.0f}% provides good vibrancy")

        # Prevalence
        if w.screen_percentage > 3:
            parts.append(f"Covers {w.screen_percentage:.1f}% of visible screen content")

        # Penalties note
        if breakdown.penalties < 0:
            penalty_note = ", ".join(breakdown.penalty_reasons) if breakdown.penalty_reasons else "penalties applied"
            parts.append(f"Note: {penalty_note}")

        return ". ".join(parts) + "."

    def _get_hue_name(self, hue_deg: float) -> str:
        """Get name for hue value"""
        if 0 <= hue_deg < 30 or 330 <= hue_deg <= 360:
            return "Red"
        elif 30 <= hue_deg < 60:
            return "Orange"
        elif 60 <= hue_deg < 90:
            return "Yellow"
        elif 90 <= hue_deg < 150:
            return "Green"
        elif 150 <= hue_deg < 210:
            return "Cyan"
        elif 210 <= hue_deg < 280:
            return "Blue"
        elif 280 <= hue_deg < 330:
            return "Purple/Magenta"
        return "Unknown"

    def get_runner_ups(self, count: int = 3) -> List[ColorCandidate]:
        """Get the top N runner-up candidates (excluding winner)"""
        non_winners = [c for c in self.candidates if not c.is_winner]
        sorted_candidates = sorted(non_winners, key=lambda c: c.total_score, reverse=True)
        return sorted_candidates[:count]

    def get_rejected(self) -> List[ColorCandidate]:
        """Get all rejected candidates"""
        return [c for c in self.candidates if c.rejection_reason is not None]

    def to_dict(self) -> dict:
        """Convert to dictionary for JSON serialization"""
        return {
            "timestamp": self.timestamp.isoformat(),
            "winner": {
                "hex_color": self.winner.hex_color,
                "rgb": self.winner.rgb,
                "hsv": self.winner.hsv,
                "screen_percentage": self.winner.screen_percentage,
                "total_score": self.winner.total_score,
                "score_breakdown": {
                    "saturation": self.winner.score_breakdown.saturation_score,
                    "brightness": self.winner.score_breakdown.brightness_score,
                    "prevalence": self.winner.score_breakdown.prevalence_score,
                    "hue_preference": self.winner.score_breakdown.hue_preference_score,
                    "penalties": self.winner.score_breakdown.penalties,
                }
            } if self.winner else None,
            "decision_summary": self.decision_summary,
            "candidates_count": len(self.candidates),
            "rejected_count": len(self.get_rejected()),
        }
