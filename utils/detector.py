"""
SafeCross AI - Real-Time Object Detection Engine
YOLOv8-based vehicle and pedestrian detection for road safety monitoring.
"""

import cv2
import numpy as np
from ultralytics import YOLO


PERSON_CLASSES = {0}

VEHICLE_CLASSES = {1, 2, 3, 5, 7}

COCO_NAMES = {
    0: "Person", 1: "Car", 2: "Motorcycle", 3: "Bus",
    5: "Truck", 7: "Truck",
}

COLORS = {
    "Person": (0, 200, 255),
    "Car": (50, 220, 50),
    "Motorcycle": (255, 165, 0),
    "Bus": (220, 50, 220),
    "Truck": (50, 50, 255),
}


class SafeCrossDetector:
    """YOLOv8 detector tuned for road-safety vehicle and pedestrian monitoring."""

    def __init__(self, model_size="n"):
        self.model = YOLO(f"yolov8{model_size}.pt")
        self.target_ids = PERSON_CLASSES | VEHICLE_CLASSES

    def detect(self, frame, conf=0.25):
        """
        Run detection on a BGR frame.

        Returns:
            annotated_frame: BGR frame with bounding boxes drawn
            detections: list of {bbox, class_name, class_id, confidence, category}
        """
        results = self.model(frame, verbose=False, conf=conf)[0]

        detections = []
        annotated = frame.copy()

        if results.boxes is None or len(results.boxes) == 0:
            return annotated, detections

        boxes = results.boxes.xyxy.cpu().numpy()
        confidences = results.boxes.conf.cpu().numpy()
        class_ids = results.boxes.cls.cpu().numpy().astype(int)

        for box, conf_val, cls_id in zip(boxes, confidences, class_ids):
            if cls_id not in self.target_ids:
                continue

            x1, y1, x2, y2 = box.astype(int)
            cls_name = COCO_NAMES.get(cls_id, self.model.names.get(cls_id, f"Class_{cls_id}"))
            category = "person" if cls_id in PERSON_CLASSES else "vehicle"
            color = COLORS.get(cls_name, (200, 200, 200))

            detections.append({
                "bbox": (x1, y1, x2, y2),
                "class_name": cls_name,
                "class_id": int(cls_id),
                "confidence": float(conf_val),
                "category": category,
            })

            self._draw_box(annotated, (x1, y1, x2, y2), cls_name, float(conf_val), color)

        return annotated, detections

    @staticmethod
    def _draw_box(frame, bbox, cls_name, conf, color):
        x1, y1, x2, y2 = bbox
        thickness = 2
        cv2.rectangle(frame, (x1, y1), (x2, y2), color, thickness)

        label = f"{cls_name} {conf:.0%}"
        font = cv2.FONT_HERSHEY_SIMPLEX
        font_scale = 0.55
        (tw, th), baseline = cv2.getTextSize(label, font, font_scale, 1)

        label_y = y1 - 8 if y1 - th - 12 > 0 else y1 + 4
        lx2 = min(x1 + tw + 8, frame.shape[1])
        ly2 = min(label_y + th + 6, frame.shape[0])

        cv2.rectangle(frame, (x1, label_y - 2), (lx2, ly2), color, -1)
        cv2.putText(frame, label, (x1 + 4, label_y + th), font, font_scale,
                    (255, 255, 255), 1, cv2.LINE_AA)

    @staticmethod
    def count_by_category(detections):
        persons = sum(1 for d in detections if d["category"] == "person")
        vehicles = sum(1 for d in detections if d["category"] == "vehicle")
        return persons, vehicles

    @staticmethod
    def vehicle_breakdown(detections):
        breakdown = {}
        for d in detections:
            if d["category"] == "vehicle":
                name = d["class_name"]
                breakdown[name] = breakdown.get(name, 0) + 1
        return breakdown
