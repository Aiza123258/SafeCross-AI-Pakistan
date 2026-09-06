"""
SafeCross AI - Live Detection Page
Real-time vehicle and pedestrian detection using YOLOv8.
Supports image upload, webcam capture, and video file processing.
"""

import streamlit as st

# OpenCV is required only by this page. Keep the import isolated so a
# deployment dependency problem cannot crash the rest of SafeCross AI.
try:
    import cv2
    OPENCV_AVAILABLE = True
    OPENCV_ERROR = ""
except Exception as e:
    cv2 = None
    OPENCV_AVAILABLE = False
    OPENCV_ERROR = str(e)

import numpy as np
import time
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

if OPENCV_AVAILABLE:
    try:
        from utils.detector import SafeCrossDetector
        DETECTOR_AVAILABLE = True
    except Exception:
        DETECTOR_AVAILABLE = False
else:
    SafeCrossDetector = None
    DETECTOR_AVAILABLE = False

try:
    from utils.proximity import analyze_proximity, draw_proximity
    PROXIMITY_AVAILABLE = True
except ImportError:
    PROXIMITY_AVAILABLE = False

try:
    from utils.pedestrian_safety import (
        CrossingZone, analyze_pedestrian_safety,
        draw_crossing_zone, draw_conflict_indicators,
        log_safety_event,
    )
    SAFETY_AVAILABLE = True
except ImportError:
    SAFETY_AVAILABLE = False

try:
    from utils.smart_barrier import SmartBarrierDecisionEngine
    BARRIER_ENGINE_AVAILABLE = True
except ImportError:
    BARRIER_ENGINE_AVAILABLE = False

st.set_page_config(page_title="Live Detection - SafeCross AI", page_icon="", layout="wide")

try:
    from utils.ui_components import inject_global_css, render_page_header, render_footer, render_sidebar_brand, render_sidebar_about, render_sidebar_nav, render_sidebar_footer, render_top_nav
    inject_global_css()
    HAS_UI = True
except ImportError:
    HAS_UI = False

if not HAS_UI:
    st.markdown("""
    <style>
        .metric-card { background: white; padding: 1.2rem; border-radius: 8px; box-shadow: 0 2px 4px rgba(0,0,0,0.05); text-align: center; }
    </style>
    """, unsafe_allow_html=True)

with st.sidebar:
    if HAS_UI:
        render_sidebar_brand()
        render_sidebar_about()
        render_sidebar_nav()

    st.markdown("### Detection Settings")

    # Keep the sidebar compact like the reference design. Advanced controls
    # remain available without making the sidebar vertically scroll.
    source_type = st.radio(
        "Input Source",
        ["Image Upload", "Webcam", "Video File"],
        index=0,
    )

    model_size = st.selectbox(
        "Model Size",
        ["n (Nano - Fastest)", "s (Small - Balanced)", "m (Medium - Accurate)"],
        index=0,
    )
    model_map = {"n": "n", "s": "s", "m": "m"}
    selected_size = model_map[model_size[0]]

    st.markdown(
        '<div style="font-size:0.78rem;color:rgba(255,255,255,.72);margin:.25rem 0 .15rem;">'
        'AI Model: <strong style="color:#10b981;">YOLOv8n</strong></div>'
        '<div style="font-size:0.78rem;color:rgba(255,255,255,.72);">Status: '
        '<strong style="color:#10b981;">● Ready</strong></div>',
        unsafe_allow_html=True,
    )

    with st.expander("Advanced Detection Settings", expanded=False):
        confidence_threshold = st.slider(
            "Confidence Threshold", 0.05, 0.95, 0.25, 0.05
        )

        enable_proximity = st.checkbox("Enable Proximity Analysis", value=True)
        if enable_proximity:
            danger_threshold = st.slider(
                "Danger Zone (pixels)", 20, 200, 80, 10,
                help="Edge-to-edge distance below which a pedestrian-vehicle pair is DANGER"
            )
            warning_threshold = st.slider(
                "Warning Zone (pixels)", 50, 400, 180, 10,
                help="Edge-to-edge distance below which a pair is WARNING"
            )
            if warning_threshold <= danger_threshold:
                warning_threshold = danger_threshold + 20
        else:
            danger_threshold, warning_threshold = 80, 180

        enable_safety = st.checkbox("Pedestrian Safety Intelligence", value=True)
        if enable_safety and SAFETY_AVAILABLE:
            enable_crossing_zone = st.checkbox("Show Crossing Zone", value=True)
            if enable_crossing_zone:
                zone_x = st.slider("Zone X Position", 0.0, 0.8, 0.35, 0.05)
                zone_y = st.slider("Zone Y Position", 0.0, 0.8, 0.55, 0.05)
                zone_w = st.slider("Zone Width", 0.05, 0.6, 0.30, 0.05)
                zone_h = st.slider("Zone Height", 0.05, 0.6, 0.25, 0.05)
            else:
                zone_x, zone_y, zone_w, zone_h = 0.35, 0.55, 0.30, 0.25
        else:
            enable_crossing_zone = False
            zone_x, zone_y, zone_w, zone_h = 0.35, 0.55, 0.30, 0.25

    # Defaults used when the advanced panel is collapsed.
    if "confidence_threshold" not in locals():
        confidence_threshold = 0.25
        enable_proximity = True
        danger_threshold, warning_threshold = 80, 180
        enable_safety = True
        enable_crossing_zone = True
        zone_x, zone_y, zone_w, zone_h = 0.35, 0.55, 0.30, 0.25

    if HAS_UI:
        render_sidebar_footer()


# ── Page Header ──────────────────────────────────────────────────────────────

if HAS_UI:
    render_top_nav()
    render_page_header("Live Vehicle & Pedestrian Detection", "Real-time AI-powered detection using YOLOv8 — vehicles, pedestrians, proximity analysis, and safety intelligence")
else:
    st.markdown("## Live Vehicle & Pedestrian Detection")

if not OPENCV_AVAILABLE:
    st.error("Live Detection is temporarily unavailable on this deployment because the OpenCV runtime library could not be loaded.")
    st.info("The deployment configuration includes the required OpenCV system libraries. Rebuild/redeploy the app after dependency changes.")
    st.stop()

if not DETECTOR_AVAILABLE:
    st.error("Live Detection engine could not be initialized. Please redeploy so the pinned YOLO/OpenCV dependencies are installed.")
    st.stop()


# ── Load Model ──────────────────────────────────────────────────────────────

@st.cache_resource
def load_detector(size="n"):
    with st.spinner(f"Loading YOLOv8{size} model..."):
        return SafeCrossDetector(model_size=size)


try:
    detector = load_detector(selected_size)
except Exception as e:
    st.error(f"Failed to load model: {e}")
    st.info("The YOLOv8 model weights are downloaded automatically on first use. Check your internet connection.")
    st.stop()


# ── Helper: Display detection results ───────────────────────────────────────

def show_detection_summary(annotated_frame, detections, inference_time):
    persons, vehicles = SafeCrossDetector.count_by_category(detections)
    breakdown = SafeCrossDetector.vehicle_breakdown(detections)
    total = len(detections)

    st.markdown("### Detection Results")

    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.markdown(f"""
        <div class="metric-card" style="border-left: 4px solid #059669;">
            <div style="color: #6b7280; font-size: 0.85rem;">Total Detections</div>
            <div style="font-size: 2rem; font-weight: 700; color: #059669;">{total}</div>
        </div>
        """, unsafe_allow_html=True)
    with col2:
        st.markdown(f"""
        <div class="metric-card" style="border-left: 4px solid #0ea5e9;">
            <div style="color: #6b7280; font-size: 0.85rem;">Pedestrians</div>
            <div style="font-size: 2rem; font-weight: 700; color: #0ea5e9;">{persons}</div>
        </div>
        """, unsafe_allow_html=True)
    with col3:
        st.markdown(f"""
        <div class="metric-card" style="border-left: 4px solid #f59e0b;">
            <div style="color: #6b7280; font-size: 0.85rem;">Vehicles</div>
            <div style="font-size: 2rem; font-weight: 700; color: #f59e0b;">{vehicles}</div>
        </div>
        """, unsafe_allow_html=True)
    with col4:
        fps = 1.0 / inference_time if inference_time > 0 else 0
        st.markdown(f"""
        <div class="metric-card" style="border-left: 4px solid #8b5cf6;">
            <div style="color: #6b7280; font-size: 0.85rem;">Inference Speed</div>
            <div style="font-size: 2rem; font-weight: 700; color: #8b5cf6;">{fps:.1f}</div>
            <div style="color: #6b7280; font-size: 0.8rem;">FPS</div>
        </div>
        """, unsafe_allow_html=True)

    st.markdown("---")

    detail_col1, detail_col2 = st.columns([2, 1])

    with detail_col1:
        if detections:
            st.markdown("#### Detection Details")
            rows = []
            for i, d in enumerate(detections, 1):
                cat_icon = "🚶" if d["category"] == "person" else "🚗"
                rows.append({
                    "#": i,
                    "Type": f"{cat_icon} {d['class_name']}",
                    "Confidence": f"{d['confidence']:.0%}",
                    "Position": f"({d['bbox'][0]}, {d['bbox'][1]}) → ({d['bbox'][2]}, {d['bbox'][3]})",
                })
            st.dataframe(rows, use_container_width=True, hide_index=True)
        else:
            st.info("No vehicles or pedestrians detected in this frame.")

    with detail_col2:
        st.markdown("#### Vehicle Breakdown")
        if breakdown:
            for vtype, count in sorted(breakdown.items(), key=lambda x: -x[1]):
                st.markdown(f"**{vtype}**: {count}")
        else:
            st.markdown("*No vehicles detected*")

        st.markdown("#### Safety Assessment")
        if persons > 0 and vehicles > 0:
            st.warning(f"⚠️ **Shared Zone** — {persons} pedestrian(s) and {vehicles} vehicle(s) detected in the same frame. Monitor proximity closely.")
        elif persons > 0:
            st.info(f"🚶 **Pedestrian Zone** — {persons} pedestrian(s) detected. No vehicles in frame.")
        elif vehicles > 0:
            st.success(f"🚗 **Vehicle Flow** — {vehicles} vehicle(s) detected. No pedestrians in frame.")
        else:
            st.success("✅ **Clear Zone** — No road users detected.")


def show_proximity_summary(proximity_result):
    """Display the Pedestrian-Vehicle Proximity Analysis section."""
    st.markdown("---")

    status = proximity_result.get("overall_status", "NO_PEDESTRIANS")

    if status == "NO_PEDESTRIANS":
        st.info("🚶 No pedestrians detected — proximity analysis not applicable.")
        return
    if status == "NO_VEHICLES":
        st.success("🚶 Pedestrian(s) detected with no vehicles in frame — zone is clear.")
        return

    status_colors = {"DANGER": "#ef4444", "WARNING": "#f59e0b", "SAFE": "#10b981"}
    status_icons = {"DANGER": "🔴", "WARNING": "🟡", "SAFE": "🟢"}
    color = status_colors.get(status, "#6b7280")
    icon = status_icons.get(status, "⚪")

    st.markdown(f"""
    <div style="background: linear-gradient(135deg, {color}15, {color}30);
                padding: 1.5rem; border-radius: 10px;
                border: 2px solid {color}; margin-bottom: 1rem;">
        <h3 style="margin:0; color: {color};">
            {icon} Pedestrian-Vehicle Proximity Analysis — {status}
        </h3>
        <p style="margin:0.5rem 0 0 0; color: #374151;">
            Prototype relative-proximity estimate. Actual physical distance requires camera calibration / depth sensing.
        </p>
    </div>
    """, unsafe_allow_html=True)

    m1, m2, m3, m4 = st.columns(4)
    with m1:
        st.markdown(f"""
        <div class="metric-card" style="border-left: 4px solid #ef4444;">
            <div style="color: #6b7280; font-size: 0.85rem;">Danger Pairs</div>
            <div style="font-size: 2rem; font-weight: 700; color: #ef4444;">{proximity_result['danger_count']}</div>
        </div>
        """, unsafe_allow_html=True)
    with m2:
        st.markdown(f"""
        <div class="metric-card" style="border-left: 4px solid #f59e0b;">
            <div style="color: #6b7280; font-size: 0.85rem;">Warning Pairs</div>
            <div style="font-size: 2rem; font-weight: 700; color: #f59e0b;">{proximity_result['warning_count']}</div>
        </div>
        """, unsafe_allow_html=True)
    with m3:
        st.markdown(f"""
        <div class="metric-card" style="border-left: 4px solid #10b981;">
            <div style="color: #6b7280; font-size: 0.85rem;">Safe Pairs</div>
            <div style="font-size: 2rem; font-weight: 700; color: #10b981;">{proximity_result['safe_count']}</div>
        </div>
        """, unsafe_allow_html=True)
    with m4:
        peds_in_danger = sum(1 for p in proximity_result["pedestrian_details"] if p["nearest_status"] == "DANGER")
        st.markdown(f"""
        <div class="metric-card" style="border-left: 4px solid #8b5cf6;">
            <div style="color: #6b7280; font-size: 0.85rem;">Pedestrians at Risk</div>
            <div style="font-size: 2rem; font-weight: 700; color: #8b5cf6;">{peds_in_danger}</div>
        </div>
        """, unsafe_allow_html=True)

    if proximity_result["danger_count"] > 0:
        st.error(f"🚨 **CRITICAL ALERT:** {proximity_result['danger_count']} pedestrian-vehicle pair(s) in DANGER zone — immediate collision risk!")
    elif proximity_result["warning_count"] > 0:
        st.warning(f"⚠️ **CAUTION:** {proximity_result['warning_count']} pedestrian-vehicle pair(s) in WARNING zone — monitor closely.")
    else:
        st.success("✅ All pedestrian-vehicle pairs are in the SAFE zone.")

    danger_pairs = [p for p in proximity_result["pairs"] if p["status"] == "DANGER"]
    warning_pairs = [p for p in proximity_result["pairs"] if p["status"] == "WARNING"]
    notable = danger_pairs + warning_pairs

    if notable:
        st.markdown("#### Proximity Details")
        rows = []
        for pair in notable:
            icon = "🔴" if pair["status"] == "DANGER" else "🟡"
            rows.append({
                "Status": f"{icon} {pair['status']}",
                "Pedestrian": f"Person at ({int(pair['person_center'][0])}, {int(pair['person_center'][1])})",
                "Nearest Vehicle": f"{pair['vehicle_class']}",
                "Edge Distance": f"{pair['edge_distance']:.0f} px",
                "Center Distance": f"{pair['center_distance']:.0f} px",
            })
        st.dataframe(rows, use_container_width=True, hide_index=True)

    st.caption("⚠️ Distances are pixel-based relative proximity estimates, not real-world measurements. "
               "Actual physical distance requires camera calibration and depth sensing.")


def show_safety_summary(safety_result, event_log=None):
    """Display the Pedestrian Safety Intelligence section."""
    st.markdown("---")

    status = safety_result.get("status", "CLEAR")
    score = safety_result.get("safety_score", 100)

    status_colors = {"DANGER": "#ef4444", "CAUTION": "#f59e0b", "SAFE": "#10b981", "CLEAR": "#6b7280"}
    status_icons = {"DANGER": "🔴", "CAUTION": "🟡", "SAFE": "🟢", "CLEAR": "⚪"}
    color = status_colors.get(status, "#6b7280")
    icon = status_icons.get(status, "⚪")

    st.markdown(f"""
    <div style="background: linear-gradient(135deg, {color}15, {color}30);
                padding: 1.5rem; border-radius: 10px;
                border: 2px solid {color}; margin-bottom: 1rem;">
        <h3 style="margin:0; color: {color};">
            {icon} Pedestrian Safety Intelligence — {status}
        </h3>
        <p style="margin:0.3rem 0 0 0; color: #374151; font-size: 0.95rem;">
            AI-Assisted Safety Score: <strong>{score} / 100</strong>
        </p>
    </div>
    """, unsafe_allow_html=True)

    s1, s2, s3, s4 = st.columns(4)
    with s1:
        st.markdown(f"""
        <div class="metric-card" style="border-left: 4px solid #0ea5e9;">
            <div style="color: #6b7280; font-size: 0.85rem;">Pedestrians Detected</div>
            <div style="font-size: 2rem; font-weight: 700; color: #0ea5e9;">{safety_result['pedestrians_total']}</div>
        </div>
        """, unsafe_allow_html=True)
    with s2:
        st.markdown(f"""
        <div class="metric-card" style="border-left: 4px solid #8b5cf6;">
            <div style="color: #6b7280; font-size: 0.85rem;">In Crossing Zone</div>
            <div style="font-size: 2rem; font-weight: 700; color: #8b5cf6;">{safety_result['pedestrians_in_zone']}</div>
        </div>
        """, unsafe_allow_html=True)
    with s3:
        st.markdown(f"""
        <div class="metric-card" style="border-left: 4px solid #f59e0b;">
            <div style="color: #6b7280; font-size: 0.85rem;">Nearby Vehicles</div>
            <div style="font-size: 2rem; font-weight: 700; color: #f59e0b;">{safety_result['vehicles_in_zone'] + safety_result['vehicles_near_zone']}</div>
        </div>
        """, unsafe_allow_html=True)
    with s4:
        st.markdown(f"""
        <div class="metric-card" style="border-left: 4px solid #ef4444;">
            <div style="color: #6b7280; font-size: 0.85rem;">Potential Conflicts</div>
            <div style="font-size: 2rem; font-weight: 700; color: #ef4444;">{safety_result['conflict_count']}</div>
        </div>
        """, unsafe_allow_html=True)

    st.markdown(f"**Explanation:** {safety_result['explanation']}")

    rec = safety_result["recommendation"]
    if status == "DANGER":
        st.error(f"🚨 {rec}")
    elif status == "CAUTION":
        st.warning(f"⚠️ {rec}")
    elif status == "SAFE":
        st.success(f"✅ {rec}")
    else:
        st.info(f"ℹ️ {rec}")

    if safety_result["conflicts"]:
        st.markdown("#### Conflict Details")
        rows = []
        for c in safety_result["conflicts"]:
            sev_icon = {"HIGH": "🔴", "MEDIUM": "🟡", "LOW": "🟢"}.get(c["severity"], "⚪")
            rows.append({
                "Severity": f"{sev_icon} {c['severity']}",
                "Pedestrian in Zone": "Yes" if c["pedestrian_in_zone"] else "No",
                "Vehicle": c["vehicle_class"],
                "Distance": f"{c['distance']:.0f} px",
            })
        st.dataframe(rows, use_container_width=True, hide_index=True)

    if event_log:
        st.markdown("#### Safety Event Log")
        log_rows = []
        for evt in event_log[-20:]:
            log_rows.append({
                "Time": evt["timestamp"],
                "Event": evt["event_type"],
                "Status": evt["status"],
                "Score": evt["safety_score"],
                "Peds": evt["pedestrians"],
                "Vehicles": evt["vehicles"],
                "Conflicts": evt["conflicts"],
            })
        st.dataframe(log_rows, use_container_width=True, hide_index=True)

    st.caption(
        "This is a prototype AI-assisted pedestrian safety system. "
        "Risk and proximity values are estimates based on computer-vision observations. "
        "Actual physical distance and pedestrian intent require calibrated sensors / depth information. "
        "Recommendations are for demonstration purposes and are not a replacement for certified traffic-control systems."
    )


def show_barrier_recommendation(safety_result, proximity_result, detections):
    """Display a Smart Barrier Recommendation based on current detection frame."""
    if not BARRIER_ENGINE_AVAILABLE:
        return

    if "barrier_rec_engine" not in st.session_state:
        st.session_state.barrier_rec_engine = SmartBarrierDecisionEngine()

    rec_engine = st.session_state.barrier_rec_engine

    persons = [d for d in detections if d.get("category") == "person"]
    vehicles = [d for d in detections if d.get("category") == "vehicle"]

    proximity_status = "SAFE"
    if proximity_result:
        if proximity_result.get("danger_count", 0) > 0:
            proximity_status = "DANGER"
        elif proximity_result.get("warning_count", 0) > 0:
            proximity_status = "WARNING"

    barrier_inputs = {
        "emergency_detected": False,
        "emergency_priority": "NORMAL",
        "emergency_state": "NORMAL",
        "pedestrian_count": len(persons),
        "pedestrians_in_crossing": safety_result.get("pedestrians_in_zone", 0) if safety_result else 0,
        "vehicle_count": len(vehicles),
        "vehicles_in_zone": 0,
        "potential_conflicts": safety_result.get("conflict_count", 0) if safety_result else 0,
        "safety_status": safety_result.get("status", "CLEAR") if safety_result else "CLEAR",
        "safety_score": safety_result.get("safety_score", 100) if safety_result else 100,
        "proximity_status": proximity_status,
    }

    b_decision = rec_engine.decide(**barrier_inputs)

    st.markdown("---")
    d_color = {"CLOSE": "#10b981", "PREPARE": "#f59e0b", "OPEN": "#3b82f6", "HOLD": "#ef4444"}.get(b_decision["decision"], "#6b7280")

    st.markdown(f"""
    <div style="background: {d_color}10; padding: 1rem; border-radius: 8px;
                border: 1px solid {d_color}; margin-bottom: 0.5rem;">
        <div style="display: flex; justify-content: space-between; align-items: center;">
            <div>
                <strong style="color: {d_color}; font-size: 1.2rem;">
                    Smart Barrier: {b_decision['decision']}
                </strong>
                <span style="color: #6b7280; font-size: 0.85rem; margin-left: 1rem;">
                    Confidence: {b_decision['confidence']}%
                </span>
            </div>
        </div>
        <p style="margin: 0.5rem 0 0 0; color: #374151; font-size: 0.9rem;">
            {b_decision['reason']}
        </p>
    </div>
    """, unsafe_allow_html=True)

    st.caption("AI-assisted simulation. Does not control real-world barriers or traffic infrastructure.")


# ── Mode: Image Upload ──────────────────────────────────────────────────────

if source_type == "Image Upload":
    st.markdown("#### Upload an image of a road scene")
    uploaded = st.file_uploader(
        "Upload an image of a road scene",
        type=["jpg", "jpeg", "png", "bmp"],
        help="200MB per file • JPG, PNG, BMP",
    )

    if uploaded is not None:
        file_bytes = np.asarray(bytearray(uploaded.read()), dtype=np.uint8)
        frame = cv2.imdecode(file_bytes, cv2.IMREAD_COLOR)

        if frame is None:
            st.error("Could not read the image. Try a different file.")
            st.stop()

        frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)

        with st.spinner("Running detection..."):
            t0 = time.time()
            annotated, detections = detector.detect(frame_rgb.copy(), conf=confidence_threshold)
            inference_time = time.time() - t0

        proximity_result = None
        if enable_proximity and PROXIMITY_AVAILABLE:
            proximity_result = analyze_proximity(detections, danger_threshold, warning_threshold)
            draw_proximity(annotated, proximity_result)

        safety_result = None
        if enable_safety and SAFETY_AVAILABLE:
            h_img, w_img = annotated.shape[:2]
            crossing_zone = CrossingZone(zone_x, zone_y, zone_w, zone_h) if enable_crossing_zone else None
            safety_result = analyze_pedestrian_safety(
                detections, proximity_result, crossing_zone, w_img, h_img
            )
            if enable_crossing_zone:
                draw_crossing_zone(annotated, crossing_zone, safety_result)
            draw_conflict_indicators(annotated, safety_result.get("conflicts", []))

        col_display, col_info = st.columns([3, 1])

        with col_display:
            st.image(annotated, channels="RGB", use_container_width=True)

        with col_info:
            st.markdown(f"""
            **Image Size:** {frame.shape[1]}×{frame.shape[0]}
            **Inference:** {inference_time*1000:.0f} ms
            **Confidence:** ≥{confidence_threshold:.0%}
            """)

        st.markdown("---")
        show_detection_summary(annotated, detections, inference_time)

        if proximity_result is not None:
            show_proximity_summary(proximity_result)

        if safety_result is not None:
            show_safety_summary(safety_result)

        show_barrier_recommendation(safety_result, proximity_result, detections)


# ── Mode: Webcam ────────────────────────────────────────────────────────────

elif source_type == "Webcam":
    st.info("📷 Click the button below to capture a frame from your camera for analysis.")

    camera_frame = st.camera_input("Take a photo")

    if camera_frame is not None:
        file_bytes = np.asarray(bytearray(camera_frame.read()), dtype=np.uint8)
        frame = cv2.imdecode(file_bytes, cv2.IMREAD_COLOR)

        if frame is None:
            st.error("Could not read camera frame.")
            st.stop()

        frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)

        with st.spinner("Analyzing camera feed..."):
            t0 = time.time()
            annotated, detections = detector.detect(frame_rgb.copy(), conf=confidence_threshold)
            inference_time = time.time() - t0

        proximity_result = None
        if enable_proximity and PROXIMITY_AVAILABLE:
            proximity_result = analyze_proximity(detections, danger_threshold, warning_threshold)
            draw_proximity(annotated, proximity_result)

        safety_result = None
        if enable_safety and SAFETY_AVAILABLE:
            h_img, w_img = annotated.shape[:2]
            crossing_zone = CrossingZone(zone_x, zone_y, zone_w, zone_h) if enable_crossing_zone else None
            safety_result = analyze_pedestrian_safety(
                detections, proximity_result, crossing_zone, w_img, h_img
            )
            if enable_crossing_zone:
                draw_crossing_zone(annotated, crossing_zone, safety_result)
            draw_conflict_indicators(annotated, safety_result.get("conflicts", []))

        st.image(annotated, channels="RGB", use_container_width=True)

        st.markdown("---")
        show_detection_summary(annotated, detections, inference_time)

        if proximity_result is not None:
            show_proximity_summary(proximity_result)

        if safety_result is not None:
            show_safety_summary(safety_result)

        show_barrier_recommendation(safety_result, proximity_result, detections)


# ── Mode: Video File ────────────────────────────────────────────────────────

elif source_type == "Video File":
    uploaded_video = st.file_uploader(
        "Upload a video file",
        type=["mp4", "avi", "mov", "mkv"],
        help="Upload a video of a road scene for frame-by-frame analysis."
    )

    if uploaded_video is not None:
        tfile = uploaded_video
        temp_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "_temp_video.mp4")

        with open(temp_path, "wb") as f:
            f.write(tfile.read())

        cap = cv2.VideoCapture(temp_path)

        if not cap.isOpened():
            st.error("Could not open the video file.")
            st.stop()

        total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
        fps_video = cap.get(cv2.CAP_PROP_FPS)
        width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
        height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
        duration = total_frames / fps_video if fps_video > 0 else 0

        st.markdown(f"""
        **Video Info:** {width}×{height} | {total_frames} frames | {fps_video:.1f} FPS | {duration:.1f}s
        """)

        process_mode = st.radio("Processing Mode", ["Process All Frames", "Sample Every Nth Frame"], horizontal=True)

        sample_rate = 1
        if process_mode == "Sample Every Nth Frame":
            sample_rate = st.slider("Sample Rate (process every Nth frame)", 1, 30, 5)

        if st.button("▶ Process Video", type="primary", use_container_width=True):
            progress_bar = st.progress(0)
            status_text = st.empty()
            frame_placeholder = st.empty()

            all_detections = []
            frame_times = []
            processed_count = 0
            display_count = 0

            prox_danger_frames = 0
            prox_warning_frames = 0
            prox_safe_frames = 0
            prox_no_ped_frames = 0
            prox_max_danger = 0
            prox_max_warning = 0
            worst_frame_data = None

            safety_event_log = []
            safety_danger_frames = 0
            safety_caution_frames = 0
            safety_safe_frames = 0
            safety_clear_frames = 0
            max_pedestrians = 0
            max_conflicts = 0
            worst_safety_score = 100
            worst_safety_frame = None

            cap.set(cv2.CAP_PROP_POS_FRAMES, 0)

            while True:
                ret, frame = cap.read()
                if not ret:
                    break

                processed_count += 1

                if processed_count % sample_rate != 0:
                    continue

                frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                t0 = time.time()
                annotated, detections = detector.detect(frame_rgb.copy(), conf=confidence_threshold)
                inference_time = time.time() - t0
                frame_times.append(inference_time)
                display_count += 1

                all_detections.extend(detections)

                if enable_proximity and PROXIMITY_AVAILABLE:
                    prox = analyze_proximity(detections, danger_threshold, warning_threshold)
                    draw_proximity(annotated, prox)

                    if prox["overall_status"] == "DANGER":
                        prox_danger_frames += 1
                    elif prox["overall_status"] == "WARNING":
                        prox_warning_frames += 1
                    elif prox["overall_status"] == "SAFE":
                        prox_safe_frames += 1
                    else:
                        prox_no_ped_frames += 1

                    if prox["danger_count"] > prox_max_danger:
                        prox_max_danger = prox["danger_count"]
                        worst_frame_data = {
                            "frame": display_count,
                            "danger": prox["danger_count"],
                            "warning": prox["warning_count"],
                        }
                    if prox["warning_count"] > prox_max_warning:
                        prox_max_warning = prox["warning_count"]

                if enable_safety and SAFETY_AVAILABLE:
                    h_vid, w_vid = annotated.shape[:2]
                    crossing_zone = CrossingZone(zone_x, zone_y, zone_w, zone_h) if enable_crossing_zone else None
                    safety_res = analyze_pedestrian_safety(
                        detections, prox if (enable_proximity and PROXIMITY_AVAILABLE) else None,
                        crossing_zone, w_vid, h_vid
                    )
                    if enable_crossing_zone:
                        draw_crossing_zone(annotated, crossing_zone, safety_res)
                    draw_conflict_indicators(annotated, safety_res.get("conflicts", []))

                    if safety_res["status"] == "DANGER":
                        safety_danger_frames += 1
                    elif safety_res["status"] == "CAUTION":
                        safety_caution_frames += 1
                    elif safety_res["status"] == "SAFE":
                        safety_safe_frames += 1
                    else:
                        safety_clear_frames += 1

                    if safety_res["pedestrians_total"] > max_pedestrians:
                        max_pedestrians = safety_res["pedestrians_total"]
                    if safety_res["conflict_count"] > max_conflicts:
                        max_conflicts = safety_res["conflict_count"]
                    if safety_res["safety_score"] < worst_safety_score:
                        worst_safety_score = safety_res["safety_score"]
                        worst_safety_frame = display_count

                    if safety_res["conflict_count"] > 0 or safety_res["status"] in ("DANGER", "CAUTION"):
                        evt_type = "PEDESTRIAN CONFLICT" if safety_res["conflict_count"] > 0 else "CROSSING ACTIVE"
                        safety_event_log.append(log_safety_event(safety_res, evt_type))

                annotated_rgb = cv2.cvtColor(annotated, cv2.COLOR_BGR2RGB)
                frame_placeholder.image(annotated_rgb, channels="RGB", use_container_width=True)

                pct = processed_count / total_frames
                progress_bar.progress(min(pct, 1.0))
                status_text.text(f"Frame {processed_count}/{total_frames} | "
                                 f"Detections: {len(detections)} | "
                                 f"Speed: {1.0/inference_time:.1f} FPS")

            cap.release()

            try:
                os.remove(temp_path)
            except OSError:
                pass

            st.markdown("---")
            st.markdown("### Video Analysis Summary")

            avg_inference = np.mean(frame_times) if frame_times else 0
            avg_fps = 1.0 / avg_inference if avg_inference > 0 else 0
            total_persons = sum(1 for d in all_detections if d["category"] == "person")
            total_vehicles = sum(1 for d in all_detections if d["category"] == "vehicle")

            sum_col1, sum_col2, sum_col3, sum_col4 = st.columns(4)
            with sum_col1:
                st.metric("Frames Processed", f"{display_count:,}")
            with sum_col2:
                st.metric("Avg FPS", f"{avg_fps:.1f}")
            with sum_col3:
                st.metric("Total Pedestrians", f"{total_persons:,}")
            with sum_col4:
                st.metric("Total Vehicles", f"{total_vehicles:,}")

            if all_detections:
                st.markdown("#### Detection Distribution")
                class_counts = {}
                for d in all_detections:
                    name = d["class_name"]
                    class_counts[name] = class_counts.get(name, 0) + 1

                import plotly.express as px
                import pandas as pd
                chart_df = pd.DataFrame([
                    {"Class": k, "Count": v}
                    for k, v in sorted(class_counts.items(), key=lambda x: -x[1])
                ])
                fig = px.bar(chart_df, x="Class", y="Count", color="Class",
                             color_discrete_map={
                                 "Person": "#0ea5e9", "Car": "#22c55e",
                                 "Motorcycle": "#f59e0b", "Bus": "#a855f7", "Truck": "#3b82f6"
                             })
                fig.update_layout(showlegend=False, height=300)
                st.plotly_chart(fig, use_container_width=True)

            if enable_proximity and PROXIMITY_AVAILABLE:
                st.markdown("---")
                st.markdown("### Pedestrian-Vehicle Proximity Analysis (Video)")

                st.caption("⚠️ Prototype relative-proximity estimate. Actual physical distance requires camera calibration / depth sensing.")

                vp1, vp2, vp3, vp4 = st.columns(4)
                with vp1:
                    st.metric("Danger Frames", f"{prox_danger_frames}")
                with vp2:
                    st.metric("Warning Frames", f"{prox_warning_frames}")
                with vp3:
                    st.metric("Safe Frames", f"{prox_safe_frames}")
                with vp4:
                    st.metric("No Pedestrian Frames", f"{prox_no_ped_frames}")

                st.markdown("---")

                vp5, vp6 = st.columns(2)
                with vp5:
                    st.metric("Max Danger Pairs (single frame)", f"{prox_max_danger}")
                with vp6:
                    st.metric("Max Warning Pairs (single frame)", f"{prox_max_warning}")

                if worst_frame_data:
                    st.warning(
                        f"🚨 **Worst frame:** Frame #{worst_frame_data['frame']} — "
                        f"{worst_frame_data['danger']} danger pair(s), "
                        f"{worst_frame_data['warning']} warning pair(s)"
                    )

                total_analyzed = prox_danger_frames + prox_warning_frames + prox_safe_frames + prox_no_ped_frames
                if total_analyzed > 0:
                    import pandas as pd
                    prox_chart_df = pd.DataFrame([
                        {"Zone": "Danger", "Frames": prox_danger_frames},
                        {"Zone": "Warning", "Frames": prox_warning_frames},
                        {"Zone": "Safe", "Frames": prox_safe_frames},
                        {"Zone": "No Pedestrians", "Frames": prox_no_ped_frames},
                    ])
                    fig_prox = px.bar(prox_chart_df, x="Zone", y="Frames", color="Zone",
                                      color_discrete_map={
                                          "Danger": "#ef4444", "Warning": "#f59e0b",
                                          "Safe": "#10b981", "No Pedestrians": "#6b7280"
                                      })
                    fig_prox.update_layout(showlegend=False, height=300,
                                           title="Frame Distribution by Proximity Zone")
                    st.plotly_chart(fig_prox, use_container_width=True)

            if enable_safety and SAFETY_AVAILABLE:
                st.markdown("---")

                safety_status_overall = "DANGER" if safety_danger_frames > 0 else (
                    "CAUTION" if safety_caution_frames > 0 else "SAFE")
                ss_colors = {"DANGER": "#ef4444", "CAUTION": "#f59e0b", "SAFE": "#10b981"}
                ss_color = ss_colors.get(safety_status_overall, "#6b7280")

                st.markdown(f"""
                <div style="background: linear-gradient(135deg, {ss_color}15, {ss_color}30);
                            padding: 1.5rem; border-radius: 10px;
                            border: 2px solid {ss_color}; margin-bottom: 1rem;">
                    <h3 style="margin:0; color: {ss_color};">
                        Pedestrian Safety Intelligence (Video)
                    </h3>
                    <p style="margin:0.3rem 0 0 0; color: #374151;">
                        Worst Safety Score: <strong>{worst_safety_score} / 100</strong>
                        {f'at Frame #{worst_safety_frame}' if worst_safety_frame else ''}
                    </p>
                </div>
                """, unsafe_allow_html=True)

                st.caption(
                    "This is a prototype AI-assisted pedestrian safety system. "
                    "Risk and proximity values are estimates based on computer-vision observations. "
                    "Actual physical distance and pedestrian intent require calibrated sensors / depth information. "
                    "Recommendations are for demonstration purposes and are not a replacement for certified traffic-control systems."
                )

                vs1, vs2, vs3, vs4 = st.columns(4)
                with vs1:
                    st.metric("Danger Frames", f"{safety_danger_frames}")
                with vs2:
                    st.metric("Caution Frames", f"{safety_caution_frames}")
                with vs3:
                    st.metric("Safe Frames", f"{safety_safe_frames}")
                with vs4:
                    st.metric("Clear Frames", f"{safety_clear_frames}")

                st.markdown("---")

                vs5, vs6, vs7 = st.columns(3)
                with vs5:
                    st.metric("Max Simultaneous Pedestrians", f"{max_pedestrians}")
                with vs6:
                    st.metric("Max Conflicts (single frame)", f"{max_conflicts}")
                with vs7:
                    st.metric("Total Conflict Events", f"{len(safety_event_log)}")

                if worst_safety_frame:
                    st.warning(f"🚨 **Worst safety score:** {worst_safety_score}/100 at Frame #{worst_safety_frame}")

                total_safety = safety_danger_frames + safety_caution_frames + safety_safe_frames + safety_clear_frames
                if total_safety > 0:
                    safety_chart_df = pd.DataFrame([
                        {"Status": "Danger", "Frames": safety_danger_frames},
                        {"Status": "Caution", "Frames": safety_caution_frames},
                        {"Status": "Safe", "Frames": safety_safe_frames},
                        {"Status": "Clear", "Frames": safety_clear_frames},
                    ])
                    fig_safety = px.bar(safety_chart_df, x="Status", y="Frames", color="Status",
                                        color_discrete_map={
                                            "Danger": "#ef4444", "Caution": "#f59e0b",
                                            "Safe": "#10b981", "Clear": "#6b7280"
                                        })
                    fig_safety.update_layout(showlegend=False, height=300,
                                             title="Frame Distribution by Safety Status")
                    st.plotly_chart(fig_safety, use_container_width=True)

                if safety_event_log:
                    st.markdown("#### Safety Event Log")
                    log_rows = []
                    for evt in safety_event_log[-30:]:
                        log_rows.append({
                            "Time": evt["timestamp"],
                            "Event": evt["event_type"],
                            "Status": evt["status"],
                            "Score": evt["safety_score"],
                            "Peds": evt["pedestrians"],
                            "Vehicles": evt["vehicles"],
                            "Conflicts": evt["conflicts"],
                        })
                    st.dataframe(log_rows, use_container_width=True, hide_index=True)

    else:
        st.info("Upload a video file to begin frame-by-frame analysis.")


# ── Footer ──────────────────────────────────────────────────────────────────

if HAS_UI:
    render_footer()
else:
    st.markdown("---")
    st.caption("**SafeCross AI — Live Detection Module** | Powered by YOLOv8 (Ultralytics)")
