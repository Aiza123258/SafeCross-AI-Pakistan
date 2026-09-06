"""
SafeCross AI - Proximity Analysis Engine
Analyzes relative proximity between detected pedestrians and vehicles.
Classifies safety zones: SAFE / WARNING / DANGER.

NOTE: This is a PROTOTYPE system. Distances are pixel-based RELATIVE PROXIMITY
estimates, not real-world meter measurements. Actual physical distance requires
camera calibration and depth sensing.
"""

import math
import cv2
import numpy as np


DEFAULT_DANGER_THRESHOLD = 80
DEFAULT_WARNING_THRESHOLD = 180

ZONE_COLORS_BGR = {
    "DANGER": (0, 0, 230),
    "WARNING": (0, 200, 255),
    "SAFE": (0, 210, 80),
}


def bbox_center(bbox):
    """Calculate the center point of a bounding box (x1, y1, x2, y2)."""
    x1, y1, x2, y2 = bbox
    return ((x1 + x2) / 2.0, (y1 + y2) / 2.0)


def bbox_closest_distance(bbox_a, bbox_b):
    """
    Calculate the closest edge-to-edge distance between two bounding boxes.
    Returns 0 if boxes overlap.
    """
    x1_a, y1_a, x2_a, y2_a = bbox_a
    x1_b, y1_b, x2_b, y2_b = bbox_b

    dx = max(0, max(x1_b - x2_a, x1_a - x2_b))
    dy = max(0, max(y1_b - y2_a, y1_a - y2_b))

    return math.sqrt(dx * dx + dy * dy)


def analyze_proximity(detections, danger_threshold=DEFAULT_DANGER_THRESHOLD,
                      warning_threshold=DEFAULT_WARNING_THRESHOLD):
    """
    Analyze pedestrian-vehicle proximity from detection results.

    Parameters:
        detections: list of detection dicts (must have 'bbox', 'category', 'class_name')
        danger_threshold: pixel distance below which a pair is DANGER
        warning_threshold: pixel distance below which a pair is WARNING

    Returns:
        dict with:
            pairs: list of all pedestrian-vehicle pair analyses
            pedestrian_details: per-pedestrian nearest-vehicle info
            danger_count: number of pairs in DANGER zone
            warning_count: number of pairs in WARNING zone
            safe_count: number of pairs in SAFE zone
            overall_status: worst-case status across all pairs
            has_proximity_data: True if both pedestrians and vehicles exist
    """
    persons = [d for d in detections if d["category"] == "person"]
    vehicles = [d for d in detections if d["category"] == "vehicle"]

    result = {
        "pairs": [],
        "pedestrian_details": [],
        "danger_count": 0,
        "warning_count": 0,
        "safe_count": 0,
        "overall_status": "NO_PEDESTRIANS",
        "has_proximity_data": False,
    }

    if not persons:
        return result

    result["has_proximity_data"] = len(vehicles) > 0

    if not vehicles:
        result["overall_status"] = "NO_VEHICLES"
        return result

    worst_status = "SAFE"
    status_rank = {"SAFE": 0, "WARNING": 1, "DANGER": 2}

    for p_idx, person in enumerate(persons):
        p_center = bbox_center(person["bbox"])
        nearest_vehicle = None
        nearest_distance = float("inf")
        nearest_pair_status = "SAFE"

        for v_idx, vehicle in enumerate(vehicles):
            v_center = bbox_center(vehicle["bbox"])
            distance = bbox_closest_distance(person["bbox"], vehicle["bbox"])
            center_distance = math.sqrt(
                (p_center[0] - v_center[0]) ** 2 + (p_center[1] - v_center[1]) ** 2
            )

            if distance < danger_threshold:
                status = "DANGER"
            elif distance < warning_threshold:
                status = "WARNING"
            else:
                status = "SAFE"

            pair = {
                "person_idx": p_idx,
                "vehicle_idx": v_idx,
                "person_bbox": person["bbox"],
                "vehicle_bbox": vehicle["bbox"],
                "person_center": p_center,
                "vehicle_center": v_center,
                "edge_distance": round(distance, 1),
                "center_distance": round(center_distance, 1),
                "status": status,
                "vehicle_class": vehicle["class_name"],
            }
            result["pairs"].append(pair)

            if status_rank.get(status, 0) > status_rank.get(nearest_pair_status, 0):
                nearest_pair_status = status

            if distance < nearest_distance:
                nearest_distance = distance
                nearest_vehicle = vehicle

            if status == "DANGER":
                result["danger_count"] += 1
            elif status == "WARNING":
                result["warning_count"] += 1
            else:
                result["safe_count"] += 1

            if status_rank.get(status, 0) > status_rank.get(worst_status, 0):
                worst_status = status

        result["pedestrian_details"].append({
            "person_idx": p_idx,
            "person_bbox": person["bbox"],
            "person_center": p_center,
            "nearest_vehicle": nearest_vehicle,
            "nearest_distance": round(nearest_distance, 1),
            "nearest_status": nearest_pair_status,
        })

    result["overall_status"] = worst_status
    return result


def draw_proximity(frame, proximity_result):
    """
    Draw proximity analysis overlays on the frame.
    - Lines between pedestrian-vehicle pairs (color = zone)
    - Distance labels at line midpoints
    - Zone status badges on pedestrian boxes

    Modifies the frame in-place and returns it.
    """
    if not proximity_result.get("has_proximity_data"):
        return frame

    for pair in proximity_result["pairs"]:
        status = pair["status"]
        color = ZONE_COLORS_BGR.get(status, (180, 180, 180))

        pc = pair["person_center"]
        vc = pair["vehicle_center"]
        pt1 = (int(pc[0]), int(pc[1]))
        pt2 = (int(vc[0]), int(vc[1]))

        cv2.line(frame, pt1, pt2, color, 2, cv2.LINE_AA)

        mid_x = int((pc[0] + vc[0]) / 2)
        mid_y = int((pc[1] + vc[1]) / 2)

        dist_label = f"{pair['edge_distance']:.0f}px"
        font = cv2.FONT_HERSHEY_SIMPLEX
        font_scale = 0.4
        (tw, th), _ = cv2.getTextSize(dist_label, font, font_scale, 1)
        cv2.rectangle(frame, (mid_x - 2, mid_y - th - 4), (mid_x + tw + 2, mid_y + 2),
                      color, -1)
        cv2.putText(frame, dist_label, (mid_x, mid_y - 2), font, font_scale,
                    (255, 255, 255), 1, cv2.LINE_AA)

    for ped in proximity_result.get("pedestrian_details", []):
        if ped["nearest_vehicle"] is None:
            continue
        x1, y1, x2, y2 = ped["person_bbox"]
        status = ped["nearest_status"]
        color = ZONE_COLORS_BGR.get(status, (180, 180, 180))

        label = status
        font = cv2.FONT_HERSHEY_SIMPLEX
        font_scale = 0.5
        (tw, th), _ = cv2.getTextSize(label, font, font_scale, 1)

        ly = y2 + 4
        if ly + th + 6 > frame.shape[0]:
            ly = y1 - th - 10
        lx2 = min(x1 + tw + 8, frame.shape[1])
        ly2 = min(ly + th + 6, frame.shape[0])

        cv2.rectangle(frame, (x1, ly), (lx2, ly2), color, -1)
        cv2.putText(frame, label, (x1 + 4, ly + th), font, font_scale,
                    (255, 255, 255), 1, cv2.LINE_AA)

    return frame
