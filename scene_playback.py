"""Time-based, finite scene playback with deliberate pauses for readable actions."""
from __future__ import annotations


def scene_pose(metadata: dict, elapsed: float) -> int:
    """Hold the final pose instead of resetting a completed scene mid-action."""
    elapsed = max(0.0, elapsed)
    for index, seconds in metadata["timeline"]:
        if elapsed < seconds:
            return index
        elapsed -= seconds
    return metadata["timeline"][-1][0]


def scene_duration(metadata: dict) -> float:
    return sum(seconds for _, seconds in metadata["timeline"])
