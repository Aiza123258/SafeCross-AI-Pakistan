"""
SafeCross AI - Emergency Vehicle Priority Engine
State machine + decision engine + smart barrier simulation for emergency vehicle priority.

HONESTY NOTE:
Standard YOLOv8 COCO detection does NOT provide dedicated ambulance recognition.
The COCO classes available are: Person, Car, Motorcycle, Bus, Truck.
This module provides an Emergency Scenario Demo Mode for prototype demonstration.
Real-world emergency vehicle recognition requires a dedicated trained model,
validated sensors, and safety certification.

DISCLAIMER:
Prototype AI-assisted emergency-priority simulation.
This system does not directly control real-world traffic signals, barriers, or
emergency infrastructure. Emergency vehicle recognition and priority decisions
require validated models, calibrated sensors, infrastructure integration, and
safety certification before real-world deployment.
"""

from datetime import datetime
from typing import Optional


# ── State Machine ────────────────────────────────────────────────────────────

EMERGENCY_STATES = (
    "NORMAL",
    "EMERGENCY_DETECTED",
    "PRIORITY_REQUESTED",
    "PASSAGE_ACTIVE",
    "PASSAGE_COMPLETED",
)


class EmergencyPriorityEngine:
    """
    State machine for emergency vehicle priority management.

    State flow:
        NORMAL → EMERGENCY_DETECTED → PRIORITY_REQUESTED → PASSAGE_ACTIVE → PASSAGE_COMPLETED → NORMAL
    """

    def __init__(self):
        self.state = "NORMAL"
        self.priority_level = "NORMAL"
        self.emergency_detected = False
        self.demo_mode = True
        self.current_scenario = "no_emergency"

    def set_scenario(self, scenario: str):
        """Set the demo scenario and transition to the appropriate state."""
        self.current_scenario = scenario

        scenario_state_map = {
            "no_emergency": "NORMAL",
            "ambulance_approaching": "EMERGENCY_DETECTED",
            "ambulance_at_barrier": "PRIORITY_REQUESTED",
            "ambulance_passing": "PASSAGE_ACTIVE",
            "ambulance_cleared": "PASSAGE_COMPLETED",
        }

        target = scenario_state_map.get(scenario, "NORMAL")
        self.emergency_detected = target != "NORMAL" and target != "PASSAGE_COMPLETED"
        self.state = target

    def decide(self, detections: Optional[list] = None,
               proximity_result: Optional[dict] = None,
               safety_result: Optional[dict] = None) -> dict:
        """
        Generate an emergency priority decision based on current state and traffic context.

        Returns a dict with:
            state, priority_level, priority (YES/NO), recommended_action,
            pedestrian_conflict, pedestrian_safe, emergency_detected,
            scenario, demo_mode, vehicle_count, pedestrian_count
        """
        pedestrians = [d for d in (detections or []) if d.get("category") == "person"]
        vehicles = [d for d in (detections or []) if d.get("category") == "vehicle"]
        ped_count = len(pedestrians)
        veh_count = len(vehicles)

        ped_conflict = False
        ped_safe = True
        if safety_result:
            ped_conflict = safety_result.get("conflict_count", 0) > 0
            ped_safe = safety_result.get("status") in ("SAFE", "CLEAR")

        if self.state == "NORMAL":
            return self._build_result(
                "NORMAL", False,
                "Continue normal traffic monitoring.",
                ped_conflict, ped_safe, ped_count, veh_count,
            )

        if self.state == "PASSAGE_COMPLETED":
            return self._build_result(
                "NORMAL", False,
                "Emergency vehicle has cleared. Returning to normal monitoring.",
                ped_conflict, ped_safe, ped_count, veh_count,
            )

        if self.state == "EMERGENCY_DETECTED":
            return self._build_result(
                "HIGH", True,
                "AI-assisted recommendation: Emergency vehicle detected approaching. "
                "Prepare controlled traffic priority.",
                ped_conflict, ped_safe, ped_count, veh_count,
            )

        if self.state == "PRIORITY_REQUESTED":
            if ped_conflict or not ped_safe:
                return self._build_result(
                    "CRITICAL", True,
                    "AI-assisted recommendation: Emergency priority requested. "
                    "Pedestrian crossing detected — hold vehicle movement and "
                    "coordinate controlled emergency passage only when crossing is clear.",
                    ped_conflict, ped_safe, ped_count, veh_count,
                )
            return self._build_result(
                "CRITICAL", True,
                "AI-assisted recommendation: Open barrier for emergency vehicle passage. "
                "Crossing area is clear.",
                ped_conflict, ped_safe, ped_count, veh_count,
            )

        if self.state == "PASSAGE_ACTIVE":
            return self._build_result(
                "CRITICAL", True,
                "AI-assisted recommendation: Emergency vehicle is passing through. "
                "Maintain barrier open. Monitor for pedestrians.",
                ped_conflict, ped_safe, ped_count, veh_count,
            )

        return self._build_result(
            "NORMAL", False,
            "Continue normal traffic monitoring.",
            ped_conflict, ped_safe, ped_count, veh_count,
        )

    def _build_result(self, priority_level: str, priority: bool,
                      recommendation: str, ped_conflict: bool, ped_safe: bool,
                      ped_count: int, veh_count: int) -> dict:
        self.priority_level = priority_level
        return {
            "state": self.state,
            "priority_level": priority_level,
            "priority": priority,
            "recommended_action": recommendation,
            "pedestrian_conflict": ped_conflict,
            "pedestrian_safe": ped_safe,
            "emergency_detected": self.emergency_detected,
            "current_scenario": self.current_scenario,
            "demo_mode": self.demo_mode,
            "vehicle_count": veh_count,
            "pedestrian_count": ped_count,
        }

    def reset(self):
        self.state = "NORMAL"
        self.priority_level = "NORMAL"
        self.emergency_detected = False
        self.current_scenario = "no_emergency"


# ── Smart Barrier Simulation ─────────────────────────────────────────────────

BARRIER_STATES = {
    "CLOSED": {"emoji": "\U0001f7e2", "color": "#10b981", "label": "CLOSED"},
    "PREPARING": {"emoji": "\U0001f7e1", "color": "#f59e0b", "label": "PREPARING"},
    "OPEN": {"emoji": "\U0001f534", "color": "#ef4444", "label": "OPEN"},
    "PASSAGE_ACTIVE": {"emoji": "\U0001f535", "color": "#3b82f6", "label": "PASSAGE ACTIVE"},
}


class SmartBarrier:
    """
    Simulated smart barrier with state transitions and minimum duration
    to prevent rapid OPEN/CLOSE flickering.
    """

    MIN_PASSAGE_SECONDS = 3

    def __init__(self):
        self.state = "CLOSED"
        self.last_transition_time = datetime.now()

    def update(self, priority_decision: dict):
        """Update barrier state based on the emergency priority decision."""
        state = priority_decision.get("state", "NORMAL")

        if state == "EMERGENCY_DETECTED" and self.state == "CLOSED":
            self._transition("PREPARING")
        elif state == "PRIORITY_REQUESTED" and self.state in ("CLOSED", "PREPARING"):
            self._transition("OPEN")
        elif state == "PASSAGE_ACTIVE" and self.state in ("PREPARING", "OPEN"):
            self._transition("PASSAGE_ACTIVE")
        elif state == "NORMAL" and self.state != "CLOSED":
            elapsed = (datetime.now() - self.last_transition_time).total_seconds()
            if elapsed >= self.MIN_PASSAGE_SECONDS or self.state == "PREPARING":
                self._transition("CLOSED")

    def _transition(self, new_state: str):
        self.state = new_state
        self.last_transition_time = datetime.now()

    def get_display(self) -> dict:
        return BARRIER_STATES.get(self.state, BARRIER_STATES["CLOSED"])

    def force_state(self, new_state: str):
        self.state = new_state
        self.last_transition_time = datetime.now()


# ── Demo Scenarios ───────────────────────────────────────────────────────────

DEMO_SCENARIOS = {
    "no_emergency": {
        "label": "No Emergency",
        "description": "Normal traffic flow. No emergency vehicles detected.",
        "detections": [
            {"bbox": (50, 300, 120, 450), "class_name": "Car", "class_id": 1,
             "confidence": 0.85, "category": "vehicle"},
            {"bbox": (200, 320, 270, 440), "class_name": "Car", "class_id": 1,
             "confidence": 0.80, "category": "vehicle"},
            {"bbox": (400, 280, 440, 420), "class_name": "Person", "class_id": 0,
             "confidence": 0.75, "category": "person"},
        ],
    },
    "ambulance_approaching": {
        "label": "Ambulance Approaching",
        "description": "Emergency vehicle detected approaching the controlled zone.",
        "detections": [
            {"bbox": (30, 280, 180, 430), "class_name": "Ambulance", "class_id": 100,
             "confidence": 0.92, "category": "emergency"},
            {"bbox": (300, 310, 370, 430), "class_name": "Car", "class_id": 1,
             "confidence": 0.82, "category": "vehicle"},
            {"bbox": (500, 290, 540, 420), "class_name": "Person", "class_id": 0,
             "confidence": 0.78, "category": "person"},
        ],
    },
    "ambulance_at_barrier": {
        "label": "Ambulance at Barrier",
        "description": "Emergency vehicle is at the barrier, requesting priority passage.",
        "detections": [
            {"bbox": (150, 270, 320, 430), "class_name": "Ambulance", "class_id": 100,
             "confidence": 0.95, "category": "emergency"},
            {"bbox": (450, 310, 520, 430), "class_name": "Car", "class_id": 1,
             "confidence": 0.80, "category": "vehicle"},
        ],
    },
    "ambulance_passing": {
        "label": "Ambulance Passing",
        "description": "Emergency vehicle is passing through the controlled zone.",
        "detections": [
            {"bbox": (250, 260, 430, 430), "class_name": "Ambulance", "class_id": 100,
             "confidence": 0.96, "category": "emergency"},
        ],
    },
    "ambulance_cleared": {
        "label": "Ambulance Cleared",
        "description": "Emergency vehicle has cleared the zone. Returning to normal.",
        "detections": [
            {"bbox": (50, 300, 120, 450), "class_name": "Car", "class_id": 1,
             "confidence": 0.83, "category": "vehicle"},
            {"bbox": (200, 320, 270, 440), "class_name": "Car", "class_id": 1,
             "confidence": 0.79, "category": "vehicle"},
        ],
    },
}


# ── Event Logging ────────────────────────────────────────────────────────────

def log_emergency_event(event_type: str, priority_level: str = "NORMAL",
                        barrier_state: str = "CLOSED",
                        pedestrian_status: str = "CLEAR",
                        vehicle_count: int = 0,
                        recommendation: str = "") -> dict:
    """Create a timestamped emergency event record."""
    return {
        "timestamp": datetime.now().strftime("%H:%M:%S"),
        "event": event_type,
        "priority_level": priority_level,
        "barrier_state": barrier_state,
        "pedestrian_status": pedestrian_status,
        "vehicle_count": vehicle_count,
        "recommendation": recommendation,
    }
