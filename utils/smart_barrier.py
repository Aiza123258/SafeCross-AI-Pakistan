"""
SafeCross AI - Smart Barrier Decision Engine
Explainable AI-assisted barrier decision system that evaluates pedestrian safety,
traffic conditions, and emergency priority to produce safe, transparent barrier decisions.

DISCLAIMER:
Smart Barrier is a prototype AI-assisted decision simulation.
It does not directly control real-world barriers or traffic infrastructure.
Decision confidence represents confidence in the rule-based decision based on
observed inputs, not a certified probability of correctness.
Real deployment would require validated computer-vision models, calibrated sensors,
infrastructure integration, fail-safe systems, and regulatory approval.
"""

from datetime import datetime
from typing import Optional


# ── Constants ────────────────────────────────────────────────────────────────

BARRIER_STATES = (
    "CLOSED",
    "PREPARING",
    "OPEN",
    "HOLD",
    "PASSAGE_ACTIVE",
    "RESETTING",
)

DECISIONS = ("CLOSE", "PREPARE", "OPEN", "HOLD")

BARRIER_DISPLAY = {
    "CLOSED":         {"emoji": "\U0001f7e2", "color": "#10b981", "label": "CLOSED"},
    "PREPARING":      {"emoji": "\U0001f7e1", "color": "#f59e0b", "label": "PREPARING"},
    "OPEN":           {"emoji": "\U0001f534", "color": "#ef4444", "label": "OPEN"},
    "HOLD":           {"emoji": "\U0001f7e0", "color": "#f97316", "label": "HOLD"},
    "PASSAGE_ACTIVE": {"emoji": "\U0001f535", "color": "#3b82f6", "label": "PASSAGE ACTIVE"},
    "RESETTING":      {"emoji": "\u26aa",     "color": "#6b7280", "label": "RESETTING"},
}


# ── Decision Engine ──────────────────────────────────────────────────────────

class SmartBarrierDecisionEngine:
    """
    Explainable smart barrier decision system.

    Decision hierarchy (safety first):
        1. Critical pedestrian conflict → HOLD
        2. Active pedestrian crossing   → HOLD
        3. Emergency priority           → OPEN / PREPARE
        4. Normal traffic               → CLOSE
        5. Barrier reset                → RESETTING → CLOSED
    """

    def __init__(self):
        self.state = "CLOSED"
        self.previous_state = "CLOSED"
        self.last_decision = None

    def decide(self,
               emergency_detected: bool = False,
               emergency_priority: str = "NORMAL",
               emergency_state: str = "NORMAL",
               pedestrian_count: int = 0,
               pedestrians_in_crossing: int = 0,
               vehicle_count: int = 0,
               vehicles_in_zone: int = 0,
               potential_conflicts: int = 0,
               safety_status: str = "CLEAR",
               safety_score: int = 100,
               proximity_status: str = "SAFE") -> dict:
        """
        Evaluate all inputs and produce an explainable barrier decision.

        Returns dict with:
            decision, state, previous_state, priority, confidence,
            reason, recommended_action, safety_consideration, factors
        """
        emergency_detected = bool(emergency_detected)
        emergency_priority = emergency_priority or "NORMAL"
        emergency_state = emergency_state or "NORMAL"
        pedestrian_count = pedestrian_count if isinstance(pedestrian_count, (int, float)) else 0
        pedestrians_in_crossing = pedestrians_in_crossing if isinstance(pedestrians_in_crossing, (int, float)) else 0
        vehicle_count = vehicle_count if isinstance(vehicle_count, (int, float)) else 0
        vehicles_in_zone = vehicles_in_zone if isinstance(vehicles_in_zone, (int, float)) else 0
        potential_conflicts = potential_conflicts if isinstance(potential_conflicts, (int, float)) else 0
        safety_status = safety_status or "CLEAR"
        safety_score = safety_score if isinstance(safety_score, (int, float)) else 100
        proximity_status = proximity_status or "SAFE"

        factors = []
        confidence = 85

        # ── CASE 4: Critical pedestrian conflict (highest priority) ──
        if potential_conflicts > 0 and safety_status == "DANGER":
            decision = "HOLD"
            new_state = "HOLD"
            reason = (
                f"Critical pedestrian-vehicle conflict detected "
                f"({potential_conflicts} conflict(s)). "
                f"Safety status is DANGER (score {safety_score}/100). "
                f"Barrier opening is temporarily held for safety."
            )
            action = (
                "Hold barrier movement. Do not open until all pedestrian-vehicle "
                "conflicts are resolved. Coordinate emergency passage only after "
                "crossing area is confirmed safe."
            )
            safety = "Pedestrian safety takes absolute precedence over emergency passage."
            factors.extend([
                "Critical pedestrian-vehicle conflict",
                "Safety status DANGER",
                f"Safety score {safety_score}/100",
            ])
            confidence = min(confidence + 5, 98)

        # ── CASE 3: Active pedestrian crossing ──
        elif pedestrians_in_crossing > 0 and emergency_detected:
            decision = "HOLD"
            new_state = "HOLD"
            reason = (
                f"Emergency priority is active, but {pedestrians_in_crossing} "
                f"pedestrian(s) are currently inside the crossing zone. "
                f"Barrier cannot open safely while pedestrians are crossing."
            )
            action = (
                "Hold barrier movement and coordinate controlled emergency passage. "
                "Wait until pedestrians have cleared the crossing zone before opening."
            )
            safety = "Pedestrians in the crossing zone must clear before barrier movement."
            factors.extend([
                f"{pedestrians_in_crossing} pedestrian(s) in crossing zone",
                "Emergency priority active",
                "Crossing not yet clear",
            ])
            confidence = min(confidence + 3, 96)

        # ── CASE 5: Emergency passage active ──
        elif emergency_state == "PASSAGE_ACTIVE":
            decision = "HOLD"
            new_state = "PASSAGE_ACTIVE"
            reason = (
                "Emergency vehicle is actively passing through the controlled zone. "
                "Maintain current barrier state to allow safe passage."
            )
            action = "Maintain barrier state. Monitor for pedestrians during passage."
            safety = "Continue monitoring for pedestrian safety during emergency passage."
            factors.extend([
                "Emergency passage in progress",
                "Barrier state maintained",
            ])
            confidence = min(confidence + 5, 97)

        # ── CASE 6: Emergency cleared → reset ──
        elif emergency_state in ("PASSAGE_COMPLETED",) or (
            emergency_state == "NORMAL" and self.state not in ("CLOSED", "RESETTING")
            and not emergency_detected
        ):
            decision = "CLOSE"
            new_state = "RESETTING"
            reason = (
                "Emergency vehicle has cleared the controlled area. "
                "Barrier is resetting to normal closed state."
            )
            action = "Reset barrier to closed state. Resume normal traffic monitoring."
            safety = "Verify crossing is clear before completing reset to closed state."
            factors.extend([
                "Emergency vehicle cleared",
                "Returning to normal state",
            ])
            confidence = min(confidence + 3, 95)

        # ── CASE 2: Emergency + crossing clear → open/prepare ──
        elif emergency_detected and pedestrians_in_crossing == 0 and potential_conflicts == 0:
            if emergency_priority == "CRITICAL" or emergency_state == "PRIORITY_REQUESTED":
                decision = "OPEN"
                new_state = "OPEN"
                reason = (
                    "Emergency vehicle priority confirmed and crossing zone is clear. "
                    "No pedestrians or conflicts detected. Safe to open barrier."
                )
                action = "Open barrier for emergency vehicle passage."
                safety = "Crossing zone verified clear. Continue monitoring for new pedestrians."
                factors.extend([
                    "Emergency priority confirmed",
                    "Crossing zone clear",
                    "No pedestrian conflicts",
                ])
                confidence = min(confidence + 8, 98)
            else:
                decision = "PREPARE"
                new_state = "PREPARING"
                reason = (
                    "Emergency vehicle detected approaching. Crossing zone is clear. "
                    "Preparing barrier for potential opening."
                )
                action = "Prepare barrier. Stand by for priority request."
                safety = "Monitor crossing zone for new pedestrians while preparing."
                factors.extend([
                    "Emergency vehicle approaching",
                    "Crossing zone clear",
                    "Preparing for priority",
                ])
                confidence = min(confidence + 5, 95)

        # ── Emergency + caution proximity (not danger, but not fully safe) ──
        elif emergency_detected and proximity_status == "WARNING":
            decision = "HOLD"
            new_state = "HOLD"
            reason = (
                "Emergency priority detected, but proximity analysis shows WARNING status. "
                "Pedestrian-vehicle proximity is elevated. Holding barrier as precaution."
            )
            action = "Hold barrier until proximity status returns to SAFE."
            safety = "Elevated proximity risk requires caution before barrier movement."
            factors.extend([
                "Emergency priority active",
                "Proximity status WARNING",
                "Elevated pedestrian-vehicle risk",
            ])
            confidence = min(confidence, 88)

        # ── CASE 1: No emergency ──
        else:
            decision = "CLOSE"
            new_state = "CLOSED"
            reason = "No emergency priority detected. Maintain normal barrier closed state."
            action = "Continue normal traffic monitoring."
            safety = "Standard monitoring. No special safety considerations."
            factors.append("No emergency detected")
            if pedestrian_count > 0:
                factors.append(f"{pedestrian_count} pedestrian(s) monitored")
            confidence = min(confidence + 5, 95)

        if safety_status == "DANGER":
            confidence = min(confidence + 3, 99)

        self.previous_state = self.state
        self.state = new_state
        self.last_decision = decision

        return {
            "decision": decision,
            "state": new_state,
            "previous_state": self.previous_state,
            "priority": emergency_priority,
            "confidence": max(0, min(100, confidence)),
            "reason": reason,
            "recommended_action": action,
            "safety_consideration": safety,
            "factors": factors,
            "emergency_detected": emergency_detected,
            "pedestrian_count": pedestrian_count,
            "pedestrians_in_crossing": pedestrians_in_crossing,
            "vehicle_count": vehicle_count,
            "potential_conflicts": potential_conflicts,
            "safety_status": safety_status,
            "safety_score": safety_score,
        }

    def get_display(self) -> dict:
        return BARRIER_DISPLAY.get(self.state, BARRIER_DISPLAY["CLOSED"])

    def reset(self):
        self.state = "CLOSED"
        self.previous_state = "CLOSED"
        self.last_decision = None


# ── Extended Demo Scenarios ──────────────────────────────────────────────────

SMART_BARRIER_SCENARIOS = {
    "normal_traffic": {
        "label": "Normal Traffic",
        "description": "Normal traffic flow. No emergency vehicles. Barrier stays closed.",
        "expected_decision": "CLOSE",
        "inputs": {
            "emergency_detected": False,
            "emergency_priority": "NORMAL",
            "emergency_state": "NORMAL",
            "pedestrian_count": 1,
            "pedestrians_in_crossing": 0,
            "vehicle_count": 3,
            "vehicles_in_zone": 0,
            "potential_conflicts": 0,
            "safety_status": "SAFE",
            "safety_score": 92,
            "proximity_status": "SAFE",
        },
    },
    "emergency_clear_crossing": {
        "label": "Emergency — Crossing Clear",
        "description": "Ambulance approaching. No pedestrians in crossing. Expected: OPEN/PREPARE.",
        "expected_decision": "OPEN",
        "inputs": {
            "emergency_detected": True,
            "emergency_priority": "CRITICAL",
            "emergency_state": "PRIORITY_REQUESTED",
            "pedestrian_count": 0,
            "pedestrians_in_crossing": 0,
            "vehicle_count": 2,
            "vehicles_in_zone": 1,
            "potential_conflicts": 0,
            "safety_status": "SAFE",
            "safety_score": 88,
            "proximity_status": "SAFE",
        },
    },
    "emergency_pedestrian_crossing": {
        "label": "Emergency — Pedestrian Crossing",
        "description": "Ambulance approaching but pedestrians are in the crossing zone. Expected: HOLD.",
        "expected_decision": "HOLD",
        "inputs": {
            "emergency_detected": True,
            "emergency_priority": "CRITICAL",
            "emergency_state": "PRIORITY_REQUESTED",
            "pedestrian_count": 3,
            "pedestrians_in_crossing": 2,
            "vehicle_count": 4,
            "vehicles_in_zone": 2,
            "potential_conflicts": 0,
            "safety_status": "CAUTION",
            "safety_score": 58,
            "proximity_status": "WARNING",
        },
    },
    "emergency_danger_conflict": {
        "label": "Emergency + Dangerous Conflict",
        "description": "Ambulance + critical pedestrian-vehicle conflict. Expected: HOLD (safety first).",
        "expected_decision": "HOLD",
        "inputs": {
            "emergency_detected": True,
            "emergency_priority": "CRITICAL",
            "emergency_state": "PRIORITY_REQUESTED",
            "pedestrian_count": 2,
            "pedestrians_in_crossing": 1,
            "vehicle_count": 5,
            "vehicles_in_zone": 3,
            "potential_conflicts": 2,
            "safety_status": "DANGER",
            "safety_score": 22,
            "proximity_status": "DANGER",
        },
    },
    "emergency_approaching": {
        "label": "Emergency Approaching",
        "description": "Ambulance detected approaching. Crossing clear. Expected: PREPARE.",
        "expected_decision": "PREPARE",
        "inputs": {
            "emergency_detected": True,
            "emergency_priority": "HIGH",
            "emergency_state": "EMERGENCY_DETECTED",
            "pedestrian_count": 1,
            "pedestrians_in_crossing": 0,
            "vehicle_count": 3,
            "vehicles_in_zone": 0,
            "potential_conflicts": 0,
            "safety_status": "SAFE",
            "safety_score": 90,
            "proximity_status": "SAFE",
        },
    },
    "emergency_passage_active": {
        "label": "Emergency Passage Active",
        "description": "Ambulance is passing through the controlled zone. Expected: HOLD (maintain).",
        "expected_decision": "HOLD",
        "inputs": {
            "emergency_detected": True,
            "emergency_priority": "CRITICAL",
            "emergency_state": "PASSAGE_ACTIVE",
            "pedestrian_count": 0,
            "pedestrians_in_crossing": 0,
            "vehicle_count": 1,
            "vehicles_in_zone": 0,
            "potential_conflicts": 0,
            "safety_status": "SAFE",
            "safety_score": 95,
            "proximity_status": "SAFE",
        },
    },
    "emergency_cleared": {
        "label": "Emergency Cleared",
        "description": "Ambulance has cleared the zone. Barrier resetting to closed.",
        "expected_decision": "CLOSE",
        "inputs": {
            "emergency_detected": False,
            "emergency_priority": "NORMAL",
            "emergency_state": "PASSAGE_COMPLETED",
            "pedestrian_count": 1,
            "pedestrians_in_crossing": 0,
            "vehicle_count": 2,
            "vehicles_in_zone": 0,
            "potential_conflicts": 0,
            "safety_status": "SAFE",
            "safety_score": 95,
            "proximity_status": "SAFE",
        },
    },
}


# ── Event Logging ────────────────────────────────────────────────────────────

def log_barrier_event(decision_result: dict) -> dict:
    """Create a timestamped smart barrier event record."""
    return {
        "timestamp": datetime.now().strftime("%H:%M:%S"),
        "previous_state": decision_result.get("previous_state", "CLOSED"),
        "new_state": decision_result.get("state", "CLOSED"),
        "decision": decision_result.get("decision", "CLOSE"),
        "priority": decision_result.get("priority", "NORMAL"),
        "confidence": decision_result.get("confidence", 0),
        "reason": decision_result.get("reason", ""),
        "pedestrian_count": decision_result.get("pedestrian_count", 0),
        "vehicle_count": decision_result.get("vehicle_count", 0),
        "conflict_count": decision_result.get("potential_conflicts", 0),
    }
