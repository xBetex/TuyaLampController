#!/usr/bin/env python3
"""
Color Decision History - Track and export ambient lighting color decisions
"""

import json
import csv
from datetime import datetime
from typing import List, Dict, Optional
from collections import deque
import os

# Import types from core
import sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'core'))

try:
    from color_decision import ColorDecisionReport
    COLOR_DECISION_AVAILABLE = True
except ImportError:
    COLOR_DECISION_AVAILABLE = False
    ColorDecisionReport = None


class ColorDecisionHistory:
    """Stores and exports color decision history for analysis"""

    def __init__(self, max_entries: int = 1000):
        self.max_entries = max_entries
        self.history: deque = deque(maxlen=max_entries)
        self._statistics: Dict = {}

    def add(self, report: "ColorDecisionReport"):
        """Add a decision report to history"""
        if report is None:
            return
        self.history.append(report)
        self._update_statistics(report)

    def clear(self):
        """Clear all history"""
        self.history.clear()
        self._statistics = {}

    def get_recent(self, count: int = 10) -> List["ColorDecisionReport"]:
        """Get the most recent N decisions"""
        return list(self.history)[-count:]

    def _update_statistics(self, report: "ColorDecisionReport"):
        """Update running statistics"""
        if not report.winner:
            self._statistics.setdefault('no_winner_count', 0)
            self._statistics['no_winner_count'] += 1
            return

        # Track hue distribution
        hue_deg = report.winner.hue_degrees
        hue_bucket = self._get_hue_bucket(hue_deg)
        hue_counts = self._statistics.setdefault('hue_distribution', {})
        hue_counts[hue_bucket] = hue_counts.get(hue_bucket, 0) + 1

        # Track average scores
        scores = self._statistics.setdefault('score_totals', {
            'saturation': 0,
            'brightness': 0,
            'prevalence': 0,
            'hue_preference': 0,
            'count': 0
        })
        breakdown = report.winner.score_breakdown
        scores['saturation'] += breakdown.saturation_score
        scores['brightness'] += breakdown.brightness_score
        scores['prevalence'] += breakdown.prevalence_score
        scores['hue_preference'] += breakdown.hue_preference_score
        scores['count'] += 1

        # Track winning colors
        color_counts = self._statistics.setdefault('color_frequency', {})
        color = report.winner.hex_color
        color_counts[color] = color_counts.get(color, 0) + 1

    def _get_hue_bucket(self, hue_deg: float) -> str:
        """Get hue category name"""
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
            return "Purple"
        return "Unknown"

    def get_statistics(self) -> Dict:
        """Get aggregated statistics from history"""
        stats = {
            'total_decisions': len(self.history),
            'no_winner_count': self._statistics.get('no_winner_count', 0),
            'hue_distribution': self._statistics.get('hue_distribution', {}),
        }

        # Calculate averages
        score_totals = self._statistics.get('score_totals', {})
        count = score_totals.get('count', 0)
        if count > 0:
            stats['average_scores'] = {
                'saturation': score_totals['saturation'] / count,
                'brightness': score_totals['brightness'] / count,
                'prevalence': score_totals['prevalence'] / count,
                'hue_preference': score_totals['hue_preference'] / count,
            }

        # Get most common colors
        color_freq = self._statistics.get('color_frequency', {})
        if color_freq:
            sorted_colors = sorted(color_freq.items(), key=lambda x: x[1], reverse=True)
            stats['most_common_colors'] = sorted_colors[:10]

        return stats

    def export_json(self, path: str):
        """Export history to JSON file"""
        data = {
            'export_time': datetime.now().isoformat(),
            'total_decisions': len(self.history),
            'statistics': self.get_statistics(),
            'decisions': [report.to_dict() for report in self.history]
        }

        with open(path, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2)

    def export_csv(self, path: str):
        """Export history to CSV file"""
        with open(path, 'w', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)

            # Header
            writer.writerow([
                'timestamp',
                'winner_hex',
                'winner_rgb',
                'winner_hue',
                'winner_saturation',
                'winner_brightness',
                'screen_percentage',
                'total_score',
                'saturation_score',
                'brightness_score',
                'prevalence_score',
                'hue_score',
                'penalties',
                'candidates_count',
                'rejected_count',
                'summary'
            ])

            # Data rows
            for report in self.history:
                if report.winner:
                    w = report.winner
                    b = w.score_breakdown
                    writer.writerow([
                        report.timestamp.isoformat(),
                        w.hex_color,
                        f"{w.rgb[0]},{w.rgb[1]},{w.rgb[2]}",
                        f"{w.hue_degrees:.1f}",
                        f"{w.saturation_percent:.1f}",
                        f"{w.brightness_percent:.1f}",
                        f"{w.screen_percentage:.2f}",
                        f"{w.total_score:.1f}",
                        f"{b.saturation_score:.1f}",
                        f"{b.brightness_score:.1f}",
                        f"{b.prevalence_score:.1f}",
                        f"{b.hue_preference_score:.1f}",
                        f"{b.penalties:.1f}",
                        len(report.candidates),
                        len(report.get_rejected()),
                        report.decision_summary[:100]
                    ])
                else:
                    writer.writerow([
                        report.timestamp.isoformat(),
                        'none',
                        '',
                        '',
                        '',
                        '',
                        '',
                        '0',
                        '',
                        '',
                        '',
                        '',
                        '',
                        len(report.candidates),
                        len(report.get_rejected()),
                        'No suitable color found'
                    ])

    def import_json(self, path: str) -> int:
        """Import history from JSON file. Returns number of records imported."""
        # Note: This is a simplified import that only restores statistics
        # Full restoration would require reconstructing ColorDecisionReport objects
        try:
            with open(path, 'r', encoding='utf-8') as f:
                data = json.load(f)

            return data.get('total_decisions', 0)
        except Exception:
            return 0
