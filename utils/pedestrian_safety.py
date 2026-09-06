"""
SafeCross AI - Pedestrian Safety Intelligence Engine
Analyzes pedestrian safety relative to a configurable virtual crossing zone.
Builds on YOLOv8 detections and proximity analysis.

DISCLAIMER: This is a PROTOTYPE AI-assisted pedestrian safety system.
Risk and proximity values are estimates based on computer-vision observations.
Actual physical distance and pedestrian intent require calibrated sensors / depth information.
Recommendations are for demonstration purposes and are not a replacement for certified
traffic-control systems.
"""

import math
import cv2
import numpy as np
from datetime import datetime
from typing import Optional

from utils.proximity import bbox_center, bbox_closest_distance


# ── Crossing Zone ────────────────────────────────────────────────────────────

class CrossingZone:
    """
    Configurable virtual pedestrian crossing zone using normalized coordinates.
    Works across different image / video resolutions.
    """

    def __init__(self, x: float = 0.35, y: float = 0.55,
                 width: float = 0.30, height: float = 0.25):
        self.x = x
        self.y = y
        self.width = width
        self.height = height

    def pixel_rect(self, frame_width: int, frame_height: int) -> tuple:
        px = int(self.x * frame_width)
        py = int(self.y * frame_height)
        pw = int(self.width * frame_width)
        ph = int(self.height * frame_height)
        return (px, py, px + pw, py + ph)

    def contains_center(self, bbox: tuple, frame_width: int, frame_height: int) -> bool:
        x1, y1, x2, y2 = self.pixel_rect(frame_width, frame_height)
        cx, cy = bbox_center(bbox)
        return x1 <= cx <= x2 and y1 <= cy <= y2

    def overlaps_bbox(self, bbox: tuple, frame_width: int, frame_height: int) -> bool:
        x1, y1, x2, y2 = self.pixel_rect(frame_width, frame_height)
        bx1, by1, bx2, by2 = bbox
        return not (bx2 < x1 or bx1 > x2 or by2 < y1 or by1 > y2)


# ── Safety Analysis ──────────────────────────────────────────────────────────

def analyze_pedestrian_safety(
    detections: list,
    proximity_result: Optional[dict],
    crossing_zone: Optional[CrossingZone] = None,
    frame_width: int = 640,
    frame_height: int = 480,
) -> dict:
    """
    Analyze pedestrian safety using detections and proximity analysis.

    Returns a dict with:
        safety_score (0-100), status (SAFE/CAUTION/DANGER/CLEAR),
        conflict details, explanation, recommendation, and raw counts.
    """
    persons = [d for d in detections if d["category"] == "person"]
    vehicles = [d for d in detections if d["category"] == "vehicle"]

    result = {
        "safety_score": 100,
        "status": "CLEAR",
        "pedestrians_total": len(persons),
        "vehicles_total": len(vehicles),
        "pedestrians_in_zone": 0,
        "vehicles_in_zone": 0,
        "vehicles_near_zone": 0,
        "conflicts": [],
        "conflict_count": 0,
        "explanation": "",
        "recommendation": "",
        "has_pedestrians": len(persons) > 0,
        "has_vehicles": len(vehicles) > 0,
        "zone_active": crossing_zone is not None,
    }

    if not persons:
        result["explanation"] = "No pedestrians detected in the scene."
        result["recommendation"] = "Crossing area appears clear. Continue monitoring."
        return result

    zone = crossing_zone if crossing_zone else CrossingZone()
    fw, fh = frame_width, frame_height

    peds_in_zone = []
    peds_near_zone = []
    for p in persons:
        if zone.contains_center(p["bbox"], fw, fh):
            peds_in_zone.append(p)
        elif zone.overlaps_bbox(p["bbox"], fw, fh):
            peds_near_zone.append(p)

    vehs_in_zone = []
    vehs_near_zone = []
    for v in vehicles:
        if zone.contains_center(v["bbox"], fw, fh):
            vehs_in_zone.append(v)
        elif zone.overlaps_bbox(v["bbox"], fw, fh):
            vehs_near_zone.append(v)

    result["pedestrians_in_zone"] = len(peds_in_zone) + len(peds_near_zone)
    result["vehicles_in_zone"] = len(vehs_in_zone)
    result["vehicles_near_zone"] = len(vehs_near_zone)

    conflicts = []
    for p in persons:
        p_in_zone = zone.contains_center(p["bbox"], fw, fh) or zone.overlaps_bbox(p["bbox"], fw, fh)
        p_center = bbox_center(p["bbox"])

        for v in vehicles:
            distance = bbox_closest_distance(p["bbox"], v["bbox"])
            v_in_zone = zone.contains_center(v["bbox"], fw, fh) or zone.overlaps_bbox(v["bbox"], fw, fh)

            is_conflict = False
            severity = "LOW"

            if p_in_zone and v_in_zone and distance < 100:
                is_conflict = True
                severity = "HIGH"
            elif p_in_zone and distance < 150:
                is_conflict = True
                severity = "MEDIUM"
            elif p_in_zone and v_in_zone:
                is_conflict = True
                severity = "LOW"
            elif distance < 80:
                is_conflict = True
                severity = "HIGH"

            if is_conflict:
                conflicts.append({
                    "person_bbox": p["bbox"],
                    "vehicle_bbox": v["bbox"],
                    "person_center": p_center,
                    "vehicle_center": bbox_center(v["bbox"]),
                    "distance": round(distance, 1),
                    "severity": severity,
                    "vehicle_class": v["class_name"],
                    "pedestrian_in_zone": p_in_zone,
                    "vehicle_in_zone": v_in_zone,
                })

    result["conflicts"] = conflicts
    result["conflict_count"] = len(conflicts)

    danger_count = proximity_result["danger_count"] if proximity_result else 0
    warning_count = proximity_result["warning_count"] if proximity_result else 0

    score = 100.0
    score -= len(conflicts) * 15
    score -= len(peds_in_zone) * 8
    score -= len(vehs_in_zone) * 10
    score -= len(vehs_near_zone) * 5
    score -= danger_count * 12
    score -= warning_count * 5
    result["safety_score"] = max(0, min(100, int(score)))

    if result["safety_score"] < 40 or any(c["severity"] == "HIGH" for c in conflicts):
        result["status"] = "DANGER"
    elif result["safety_score"] < 70 or len(conflicts) > 0:
        result["status"] = "CAUTION"
    elif len(persons) > 0:
        result["status"] = "SAFE"
    else:
        result["status"] = "CLEAR"

    result["explanation"] = _build_explanation(result, peds_in_zone, peds_near_zone,
                                               vehs_in_zone, vehs_near_zone, conflicts)
    result["recommendation"] = _build_recommendation(result)

    return result


def _build_explanation(result: dict, peds_in, peds_near, vehs_in, vehs_near, conflicts: list) -> str:
    parts = []
    total_peds = result["pedestrians_total"]
    in_zone = result["pedestrians_in_zone"]
    high = sum(1 for c in conflicts if c["severity"] == "HIGH")
    med = sum(1 for c in conflicts if c["severity"] == "MEDIUM")

    if total_peds == 0:
        return "No pedestrians detected in the scene."

    parts.append(f"{total_peds} pedestrian(s) detected.")

    if in_zone > 0:
        parts.append(f"{in_zone} pedestrian(s) are inside or near the crossing zone.")

    if result["vehicles_in_zone"] > 0:
        parts.append(f"{result['vehicles_in_zone']} vehicle(s) inside the crossing zone.")
    if result["vehicles_near_zone"] > 0:
        parts.append(f"{result['vehicles_near_zone']} vehicle(s) near the crossing zone.")

    if high > 0:
        parts.append(f"{high} high-severity pedestrian-vehicle conflict(s) detected.")
    if med > 0:
        parts.append(f"{med} moderate-severity conflict(s) detected.")
    if not conflicts and in_zone > 0:
        parts.append("No immediate vehicle conflicts in the crossing zone.")
    elif not conflicts:
        parts.append("No pedestrian-vehicle conflicts detected.")

    return " ".join(parts)


def _build_recommendation(result: dict) -> str:
    status = result["status"]
    conflicts = result["conflict_count"]
    peds_in_zone = result["pedestrians_in_zone"]

    if status == "DANGER":
        return (
            "AI-assisted recommendation: Potential pedestrian-vehicle conflict detected. "
            "Recommend stopping or restricting vehicle movement immediately."
        )
    elif status == "CAUTION":
        if peds_in_zone > 0 and conflicts > 0:
            return (
                "AI-assisted recommendation: Pedestrians are present near vehicle movement. "
                "Slow or temporarily restrict vehicle movement while pedestrians are crossing."
            )
        elif peds_in_zone > 0:
            return (
                "AI-assisted recommendation: Pedestrians detected in crossing zone. "
                "Monitor the crossing area and prepare to alert approaching vehicles."
            )
        else:
            return (
                "AI-assisted recommendation: Pedestrians are present near vehicle movement. "
                "Monitor the crossing area closely."
            )
    elif status == "SAFE":
        return (
            "AI-assisted recommendation: Crossing area appears clear. "
            "Continue monitoring."
        )
    else:
        return (
            "AI-assisted recommendation: No pedestrians detected. "
            "Continue standard monitoring."
        )


# ── Visual Annotation ────────────────────────────────────────────────────────

def draw_crossing_zone(frame, zone: CrossingZone, safety_result: dict):
    """Draw the crossing zone overlay on the frame. Modifies in-place and returns it."""
    h, w = frame.shape[:2]
    x1, y1, x2, y2 = zone.pixel_rect(w, h)

    status = safety_result.get("status", "SAFE")
    color_map = {
        "DANGER": (0, 0, 220),
        "CAUTION": (0, 200, 255),
        "SAFE": (0, 210, 80),
        "CLEAR": (180, 180, 180),
    }
    color = color_map.get(status, (180, 180, 180))

    overlay = frame.copy()
    cv2.rectangle(overlay, (x1, y1), (x2, y2), color, -1)
    cv2.addWeighted(overlay, 0.2, frame, 0.8, 0, frame)

    cv2.rectangle(frame, (x1, y1), (x2, y2), color, 3)

    stripe_count = max(3, (x2 - x1) // 30)
    stripe_gap = (x2 - x1) // stripe_count
    for i in range(1, stripe_count):
        sx = x1 + i * stripe_gap
        cv2.line(frame, (sx, y1), (sx, y2), color, 1)

    label = f"CROSSING ZONE [{status}]"
    font = cv2.FONT_HERSHEY_SIMPLEX
    font_scale = 0.6
    (tw, th), _ = cv2.getTextSize(label, font, font_scale, 1)
    cv2.rectangle(frame, (x1, y1 - th - 12), (x1 + tw + 10, y1 - 2), color, -1)
    cv2.putText(frame, label, (x1 + 5, y1 - 6), font, font_scale,
                (255, 255, 255), 1, cv2.LINE_AA)

    score = safety_result.get("safety_score", 100)
    score_label = f"Score: {score}/100"
    (sw, sh), _ = cv2.getTextSize(score_label, font, font_scale, 1)
    cv2.rectangle(frame, (x2 - sw - 15, y1 - sh - 12), (x2, y1 - 2), color, -1)
    cv2.putText(frame, score_label, (x2 - sw - 10, y1 - 6), font, font_scale,
                (255, 255, 255), 1, cv2.LINE_AA)

    return frame


def draw_conflict_indicators(frame, conflicts: list):
    """Draw conflict lines and severity labels on the frame."""
    severity_colors = {
        "HIGH": (0, 0, 255),
        "MEDIUM": (0, 165, 255),
        "LOW": (0, 255, 255),
    }

    for conflict in conflicts:
        color = severity_colors.get(conflict["severity"], (200, 200, 200))
        pc = conflict["person_center"]
        vc = conflict["vehicle_center"]
        pt1 = (int(pc[0]), int(pc[1]))
        pt2 = (int(vc[0]), int(vc[1]))

        cv2.line(frame, pt1, pt2, color, 3, cv2.LINE_AA)

        mid_x = int((pc[0] + vc[0]) / 2)
        mid_y = int((pc[1] + vc[1]) / 2)

        label = f"CONFLICT ({conflict['severity']})"
        font = cv2.FONT_HERSHEY_SIMPLEX
        font_scale = 0.45
        (tw, th), _ = cv2.getTextSize(label, font, font_scale, 1)
        cv2.rectangle(frame, (mid_x - 4, mid_y - th - 8), (mid_x + tw + 4, mid_y + 4),
                      color, -1)
        cv2.putText(frame, label, (mid_x, mid_y - 2), font, font_scale,
                    (255, 255, 255), 1, cv2.LINE_AA)

    return frame


# ── Event Logging ────────────────────────────────────────────────────────────

def log_safety_event(safety_result: dict, event_type: str = "FRAME_ANALYSIS") -> dict:
    """Create a timestamped safety event record for the session log."""
    return {
        "timestamp": datetime.now().strftime("%H:%M:%S"),
        "event_type": event_type,
        "status": safety_result["status"],
        "safety_score": safety_result["safety_score"],
        "pedestrians": safety_result["pedestrians_total"],
        "vehicles": safety_result["vehicles_total"],
        "conflicts": safety_result["conflict_count"],
        "peds_in_zone": safety_result["pedestrians_in_zone"],
        "recommendation": safety_result["recommendation"],
    }
