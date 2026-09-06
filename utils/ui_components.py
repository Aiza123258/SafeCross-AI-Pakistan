"""
SafeCross AI - Shared UI Design System
Professional, consistent styling across all pages.
"""

import streamlit as st


# ── Color System ─────────────────────────────────────────────────────────────

COLORS = {
    "primary": "#1e3a5f",
    "primary_light": "#2d5a8e",
    "success": "#10b981",
    "warning": "#f59e0b",
    "danger": "#ef4444",
    "info": "#3b82f6",
    "neutral": "#6b7280",
    "bg_light": "#f8fafc",
    "bg_card": "#ffffff",
    "text_primary": "#1f2937",
    "text_secondary": "#6b7280",
    "border": "#e5e7eb",
}

STATUS_COLORS = {
    "SAFE": "#10b981",
    "CAUTION": "#f59e0b",
    "DANGER": "#ef4444",
    "CLEAR": "#6b7280",
    "CRITICAL": "#ef4444",
    "HIGH": "#f59e0b",
    "MEDIUM": "#f59e0b",
    "LOW": "#10b981",
    "NORMAL": "#10b981",
    "ACTIVE": "#3b82f6",
    "SIMULATION": "#f59e0b",
    "READY": "#10b981",
}


# ── Global CSS ───────────────────────────────────────────────────────────────

GLOBAL_CSS = """
<style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap');

    .stApp {
        font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif;
    }

    [data-testid="stSidebar"] {
        background: linear-gradient(180deg, #1e3a5f 0%, #0f2440 100%);
    }
    [data-testid="stSidebar"] .stMarkdown {
        color: #e2e8f0;
    }
    [data-testid="stSidebar"] .stMarkdown p,
    [data-testid="stSidebar"] .stMarkdown li,
    [data-testid="stSidebar"] .stMarkdown span {
        color: #e2e8f0 !important;
    }
    [data-testid="stSidebar"] h3 {
        color: #ffffff !important;
        font-weight: 600;
        font-size: 0.9rem;
        text-transform: uppercase;
        letter-spacing: 0.05em;
    }
    [data-testid="stSidebar"] .stAlert {
        background: rgba(255,255,255,0.08);
        border: 1px solid rgba(255,255,255,0.15);
        color: #e2e8f0 !important;
    }

    /* Sidebar navigation links */
    [data-testid="stSidebar"] a,
    [data-testid="stSidebar"] a:visited {
        color: #e2e8f0 !important;
    }
    [data-testid="stSidebar"] a:hover {
        color: #ffffff !important;
        background: rgba(255,255,255,0.1) !important;
    }
    [data-testid="stSidebar"] a p,
    [data-testid="stSidebar"] a span,
    [data-testid="stSidebar"] a div {
        color: #e2e8f0 !important;
    }
    [data-testid="stSidebar"] a:hover p,
    [data-testid="stSidebar"] a:hover span,
    [data-testid="stSidebar"] a:hover div {
        color: #ffffff !important;
    }

    /* Selected/active page in sidebar */
    [data-testid="stSidebar"] a[aria-current="page"],
    [data-testid="stSidebar"] a[aria-current="page"]:visited {
        background: rgba(255,255,255,0.15) !important;
        border-left: 3px solid #60a5fa !important;
    }
    [data-testid="stSidebar"] a[aria-current="page"] p,
    [data-testid="stSidebar"] a[aria-current="page"] span,
    [data-testid="stSidebar"] a[aria-current="page"] div {
        color: #ffffff !important;
        font-weight: 600 !important;
    }

    /* Sidebar nav header (app name link) */
    [data-testid="stSidebarNav"] a,
    [data-testid="stSidebarNav"] a:visited {
        color: #e2e8f0 !important;
    }
    [data-testid="stSidebarNav"] a:hover {
        color: #ffffff !important;
    }
    [data-testid="stSidebarNav"] p {
        color: #e2e8f0 !important;
    }

    /* Sidebar collapse button */
    [data-testid="stSidebar"] button[kind="header"] {
        color: #e2e8f0 !important;
    }

    /* Hide the root "app" entry at the top of the sidebar nav */
    [data-testid="stSidebarNavItems"] > li:first-child {
        display: none !important;
    }

    /* Remove bullet/dot markers from sidebar nav items */
    [data-testid="stSidebarNav"] li,
    [data-testid="stSidebarNavItems"] li,
    [data-testid="stSidebarNavLink"] {
        list-style: none !important;
    }
    [data-testid="stSidebarNav"] li::before,
    [data-testid="stSidebarNav"] li::marker,
    [data-testid="stSidebarNavItems"] li::before,
    [data-testid="stSidebarNavItems"] li::marker,
    [data-testid="stSidebarNavLink"]::before,
    [data-testid="stSidebarNavLink"]::marker {
        content: none !important;
        display: none !important;
    }

    /* Hide sidebar vertical scrollbar */
    [data-testid="stSidebar"] {
        scrollbar-width: none !important;
        -ms-overflow-style: none !important;
    }
    [data-testid="stSidebar"]::-webkit-scrollbar {
        display: none !important;
        width: 0 !important;
        height: 0 !important;
    }


    /* ── Match the reference viewport: navigation starts near the top ── */
    [data-testid="stAppViewContainer"] .main .block-container {
        padding-top: 0.35rem !important;
    }
    [data-testid="stHeader"] {
        background: transparent !important;
    }

    .sc-hero {
        background: linear-gradient(135deg, #1e3a5f 0%, #2d5a8e 50%, #1e3a5f 100%);
        padding: 2.25rem 2rem;
        border-radius: 14px;
        color: white;
        margin-bottom: 2rem;
        box-shadow: 0 8px 32px rgba(30,58,95,0.25);
        position: relative;
        overflow: hidden;
    }

    .sc-hero-content { position: relative; z-index: 2; max-width: 72%; }
    .sc-hero-road { position: absolute; right: -1%; bottom: -8%; width: 48%; height: 100%; opacity: .95; pointer-events: none; }
    .sc-hero-road svg { width: 100%; height: 100%; display: block; }

    .sc-hero::before {
        content: '';
        position: absolute;
        top: -50%;
        right: -20%;
        width: 60%;
        height: 200%;
        background: radial-gradient(ellipse, rgba(255,255,255,0.05) 0%, transparent 70%);
    }
    .sc-hero h1 {
        margin: 0;
        font-size: 2.55rem;
        font-weight: 700;
        letter-spacing: -0.02em;
    }
    .sc-hero .subtitle {
        font-size: 1.15rem;
        opacity: 0.9;
        margin: 0.5rem 0 0 0;
        font-weight: 400;
    }
    .sc-hero .tagline {
        font-size: 0.9rem;
        opacity: 0.7;
        margin: 1rem 0 0 0;
    }

    .sc-page-header {
        background: linear-gradient(135deg, #1e3a5f 0%, #2d5a8e 100%);
        padding: 1.55rem 2rem;
        border-radius: 12px;
        color: white;
        margin-bottom: 1.5rem;
        box-shadow: 0 4px 16px rgba(30,58,95,0.2);
    }
    .sc-page-header h2 {
        margin: 0;
        font-size: 1.6rem;
        font-weight: 700;
    }
    .sc-page-header p {
        margin: 0.3rem 0 0 0;
        opacity: 0.85;
        font-size: 0.95rem;
    }

    .sc-card {
        background: #ffffff;
        padding: 1.2rem 1.4rem;
        border-radius: 10px;
        box-shadow: 0 1px 3px rgba(0,0,0,0.06), 0 1px 2px rgba(0,0,0,0.04);
        border: 1px solid #e5e7eb;
        transition: box-shadow 0.2s ease;
    }
    .sc-card:hover {
        box-shadow: 0 4px 12px rgba(0,0,0,0.08);
    }
    .sc-card-accent {
        background: #ffffff;
        padding: 1.2rem 1.4rem;
        border-radius: 10px;
        box-shadow: 0 1px 3px rgba(0,0,0,0.06);
        border: 1px solid #e5e7eb;
        border-left: 4px solid #3b82f6;
    }

    .sc-metric {
        text-align: center;
        padding: 1rem;
    }
    .sc-metric .label {
        color: #6b7280;
        font-size: 0.8rem;
        font-weight: 500;
        text-transform: uppercase;
        letter-spacing: 0.04em;
    }
    .sc-metric .value {
        font-size: 1.8rem;
        font-weight: 700;
        margin: 0.2rem 0;
        line-height: 1.2;
    }
    .sc-metric .sub {
        color: #6b7280;
        font-size: 0.8rem;
    }

    .sc-feature-card {
        background: #ffffff;
        padding: 1.5rem;
        border-radius: 12px;
        border: 1px solid #e5e7eb;
        box-shadow: 0 1px 3px rgba(0,0,0,0.04);
        height: 100%;
        transition: transform 0.2s ease, box-shadow 0.2s ease;
    }
    .sc-feature-card:hover {
        transform: translateY(-2px);
        box-shadow: 0 8px 24px rgba(0,0,0,0.08);
    }
    .sc-feature-card .icon {
        font-size: 2rem;
        margin-bottom: 0.5rem;
    }
    .sc-feature-card .title {
        font-size: 1rem;
        font-weight: 600;
        color: #1f2937;
        margin-bottom: 0.3rem;
    }
    .sc-feature-card .desc {
        font-size: 0.85rem;
        color: #6b7280;
        line-height: 1.4;
        margin-bottom: 0.8rem;
    }
    .sc-feature-card .status {
        font-size: 0.75rem;
        font-weight: 600;
        padding: 0.2rem 0.6rem;
        border-radius: 20px;
        display: inline-block;
    }

    .sc-pipeline-step {
        text-align: center;
        padding: 1rem 0.5rem;
        border-radius: 10px;
        border: 2px solid #e5e7eb;
        background: white;
        transition: all 0.2s ease;
    }
    .sc-pipeline-step.active {
        border-color: #3b82f6;
        background: #eff6ff;
    }
    .sc-pipeline-step .step-icon {
        font-size: 1.5rem;
        margin-bottom: 0.3rem;
    }
    .sc-pipeline-step .step-label {
        font-size: 0.75rem;
        font-weight: 600;
        color: #374151;
    }

    .sc-status-badge {
        display: inline-block;
        padding: 0.2rem 0.7rem;
        border-radius: 20px;
        font-size: 0.75rem;
        font-weight: 600;
    }

    .sc-footer {
        text-align: center;
        padding: 2rem 1rem 1rem 1rem;
        margin-top: 3rem;
        border-top: 1px solid #e5e7eb;
        color: #6b7280;
        font-size: 0.85rem;
    }
    .sc-footer .brand {
        font-weight: 600;
        color: #1e3a5f;
        font-size: 0.95rem;
    }

    .sc-section-title {
        font-size: 1.2rem;
        font-weight: 600;
        color: #1f2937;
        margin: 1.5rem 0 0.8rem 0;
        padding-bottom: 0.5rem;
        border-bottom: 2px solid #e5e7eb;
    }

    div[data-testid="stMetric"] {
        background: white;
        padding: 0.8rem 1rem;
        border-radius: 8px;
        border: 1px solid #e5e7eb;
    }

    /* ── Sidebar width (reference: ~290px) ───────────────────────── */
    /* Reference sidebar: fixed width, no vertical scrolling */
    section[data-testid="stSidebar"] {
        min-width: 265px !important;
        max-width: 265px !important;
        width: 265px !important;
    }
    section[data-testid="stSidebar"] > div:first-child {
        width: 265px !important;
        min-width: 265px !important;
        max-width: 265px !important;
        overflow: hidden !important;
    }
    section[data-testid="stSidebar"] [data-testid="stSidebarContent"] {
        width: 250px !important;
        overflow: hidden !important;
    }

    /* ── Sidebar nav items: bold 15-16px, button-like ───────────── */
    [data-testid="stSidebarNav"] a,
    [data-testid="stSidebarNav"] a:visited,
    [data-testid="stSidebarNav"] a:hover {
        color: #ffffff !important;
        background: transparent !important;
        font-size: 15px !important;
        font-weight: 600 !important;
        padding: 0.55rem 0.8rem !important;
        border-radius: 8px !important;
        margin: 2px 6px !important;
        border-left: 3px solid transparent !important;
        transition: background 0.15s ease, border-color 0.15s ease;
    }
    [data-testid="stSidebarNav"] a:hover {
        background: rgba(255,255,255,0.08) !important;
    }
    [data-testid="stSidebarNav"] a[aria-current="page"],
    [data-testid="stSidebarNav"] a[aria-current="page"]:visited {
        background: rgba(96,165,250,0.18) !important;
        border-left: 3px solid #60a5fa !important;
        color: #ffffff !important;
        font-weight: 700 !important;
    }
    [data-testid="stSidebarNav"] a p,
    [data-testid="stSidebarNav"] a span,
    [data-testid="stSidebarNav"] a div {
        color: #ffffff !important;
        font-size: 15px !important;
        font-weight: 600 !important;
    }
    [data-testid="stSidebarNav"] a[aria-current="page"] p,
    [data-testid="stSidebarNav"] a[aria-current="page"] span,
    [data-testid="stSidebarNav"] a[aria-current="page"] div {
        color: #ffffff !important;
        font-weight: 700 !important;
    }

    /* ── Reference sidebar: custom functional nav ───────────────── */
    [data-testid="stSidebarNav"] { display: none !important; }
    [data-testid="stSidebar"] .sc-sidebar-brand {
        text-align: center;
        padding: 1.0rem 0 0.65rem;
        margin-bottom: 0.15rem;
    }
    [data-testid="stSidebar"] .sc-brand-row {
        display: flex;
        align-items: center;
        justify-content: center;
        gap: 8px;
    }
    [data-testid="stSidebar"] .sc-brand-shield {
        width: 28px;
        height: 32px;
        color: #f8fafc;
        flex: 0 0 auto;
    }
    [data-testid="stSidebar"] .sc-brand-name {
        color: #ffffff !important;
        font-size: 1.45rem;
        line-height: 1;
        font-weight: 800;
        letter-spacing: -0.03em;
    }
    [data-testid="stSidebar"] .sc-brand-subtitle {
        color: rgba(255,255,255,0.88) !important;
        font-size: 0.76rem;
        font-weight: 500;
        margin-top: 0.45rem;
    }
    .sc-sidebar-nav {
        margin: 0.35rem -0.25rem 0.55rem;
        padding: 0.45rem 0;
        border-top: 1px solid rgba(255,255,255,0.24);
        border-bottom: 1px solid rgba(255,255,255,0.24);
    }
    .sc-sidebar-nav [data-testid="stPageLink"] {
        margin: 0.08rem 0;
    }
    .sc-sidebar-nav [data-testid="stPageLink"] a,
    .sc-sidebar-nav [data-testid="stPageLink"] a:visited {
        min-height: 2.05rem !important;
        display: flex !important;
        align-items: center !important;
        justify-content: flex-start !important;
        gap: 10px !important;
        padding: 0.34rem 0.45rem !important;
        border-radius: 7px !important;
        border: 1px solid transparent !important;
        color: #ffffff !important;
        background: transparent !important;
        text-decoration: none !important;
        font-size: 12px !important;
        font-weight: 600 !important;
    }
    .sc-sidebar-nav [data-testid="stPageLink"] a:hover {
        background: rgba(255,255,255,0.10) !important;
        color: #ffffff !important;
    }
    .sc-sidebar-nav [data-testid="stPageLink"] a[aria-current="page"] {
        background: #0d67c8 !important;
        border-color: #2f8cff !important;
        color: #ffffff !important;
        font-weight: 800 !important;
    }
    .sc-sidebar-nav [data-testid="stPageLink"] a p,
    .sc-sidebar-nav [data-testid="stPageLink"] a span,
    .sc-sidebar-nav [data-testid="stPageLink"] a div {
        color: inherit !important;
        font-size: 13px !important;
        font-weight: inherit !important;
    }
    .sc-sidebar-nav [data-testid="stPageLink"] a svg {
        width: 16px !important;
        height: 16px !important;
        color: inherit !important;
        fill: currentColor !important;
    }

    /* ── Top horizontal nav ──────────────────────────────────────── */
    .sc-top-nav {
        display: flex;
        gap: 0;
        background: #ffffff;
        padding: 0 0 0.2rem;
        border-bottom: 1px solid #e5e7eb;
        margin: -0.45rem 0 1.1rem;
        overflow: hidden;
    }
    .sc-top-nav [data-testid="stPageLink"] { flex: 1 1 0; min-width: 0; }
    .sc-top-nav [data-testid="stPageLink"] a,
    .sc-top-nav [data-testid="stPageLink"] a:visited {
        min-height: 3.35rem !important;
        display: flex !important;
        flex-direction: column !important;
        align-items: center !important;
        justify-content: center !important;
        gap: 4px !important;
        color: #17233b !important;
        background: transparent !important;
        font-size: 11px !important;
        font-weight: 600 !important;
        padding: 0.25rem 0.15rem 0.3rem !important;
        border-bottom: 3px solid transparent !important;
        border-radius: 0 !important;
        text-decoration: none !important;
        white-space: nowrap;
    }
    .sc-top-nav [data-testid="stPageLink"] a:hover {
        background: #f7faff !important;
        color: #1269d3 !important;
    }
    .sc-top-nav [data-testid="stPageLink"] a[aria-current="page"] {
        color: #1269d3 !important;
        border-bottom-color: #1269d3 !important;
        background: #ffffff !important;
    }
    .sc-top-nav [data-testid="stPageLink"] a p,
    .sc-top-nav [data-testid="stPageLink"] a span,
    .sc-top-nav [data-testid="stPageLink"] a div {
        color: inherit !important;
        font-size: 11px !important;
        font-weight: inherit !important;
    }
    .sc-top-nav [data-testid="stPageLink"] a svg {
        width: 17px !important;
        height: 17px !important;
        color: inherit !important;
        fill: currentColor !important;
    }

    /* ── Outlined About button ──────────────────────────────────── */
    .sc-about-btn button,
    .sc-about-btn button:hover,
    .sc-about-btn button:focus {
        background: #ffffff !important;
        color: #17324d !important;
        border: 1px solid rgba(255,255,255,0.75) !important;
        border-radius: 7px !important;
        font-weight: 600 !important;
        font-size: 0.78rem !important;
        padding: 0.32rem 0.55rem !important;
        min-height: 2rem !important;
        width: 100% !important;
        box-shadow: none !important;
    }
    .sc-about-btn button p,
    .sc-about-btn button span,
    .sc-about-btn button div {
        color: #17324d !important;
        font-size: 0.78rem !important;
        font-weight: 600 !important;
    }
    .sc-about-btn button:hover {
        background: rgba(255,255,255,0.08) !important;
        border-color: #ffffff !important;
    }
    .sc-about-content {
        background: rgba(255,255,255,0.06);
        border: 1px solid rgba(255,255,255,0.15);
        border-radius: 8px;
        padding: 0.7rem 0.8rem;
        margin: 0.4rem 0 0.4rem 0;
        color: #cbd5e1;
        font-size: 0.78rem;
        line-height: 1.5;
    }
    .sc-about-content strong {
        color: #ffffff;
    }


    /* ── Sidebar interactive controls: readable on dark background ── */
    [data-testid="stSidebar"] label,
    [data-testid="stSidebar"] label p,
    [data-testid="stSidebar"] [data-testid="stWidgetLabel"],
    [data-testid="stSidebar"] [data-testid="stWidgetLabel"] p,
    [data-testid="stSidebar"] [data-testid="stMarkdownContainer"] p {
        color: #f8fafc !important;
    }
    [data-testid="stSidebar"] .stRadio > label,
    [data-testid="stSidebar"] .stSelectbox > label,
    [data-testid="stSidebar"] .stSlider > label,
    [data-testid="stSidebar"] .stCheckbox > label {
        color: #f8fafc !important;
        font-size: 0.78rem !important;
        font-weight: 600 !important;
    }
    [data-testid="stSidebar"] [role="radiogroup"] label p,
    [data-testid="stSidebar"] [role="radiogroup"] label span,
    [data-testid="stSidebar"] .stCheckbox label p {
        color: rgba(255,255,255,0.88) !important;
        font-size: 0.72rem !important;
    }
    [data-testid="stSidebar"] [data-baseweb="select"] > div {
        background: rgba(255,255,255,0.97) !important;
        color: #17324d !important;
        min-height: 2rem !important;
    }
    [data-testid="stSidebar"] [data-baseweb="select"] * {
        color: #17324d !important;
    }
    [data-testid="stSidebar"] .stExpander {
        border-color: rgba(255,255,255,0.16) !important;
        background: rgba(255,255,255,0.035) !important;
    }
    [data-testid="stSidebar"] .stExpander summary,
    [data-testid="stSidebar"] .stExpander summary p {
        color: #f8fafc !important;
        font-size: 0.74rem !important;
    }


    [data-testid="stSidebar"] .stButton button p,
    [data-testid="stSidebar"] .stButton button span,
    [data-testid="stSidebar"] .stButton button div {
        color: inherit !important;
    }

    /* ── Detection settings info panel (sidebar) ────────────────── */
    .sc-detection-panel {
        background: rgba(255,255,255,0.05);
        border: 1px solid rgba(255,255,255,0.12);
        border-radius: 8px;
        padding: 0.55rem 0.7rem;
        margin: 0.3rem 0 0.8rem 0;
    }
    .sc-detection-panel .setting-row {
        display: flex;
        justify-content: space-between;
        align-items: center;
        padding: 0.25rem 0;
        font-size: 0.78rem;
        border-bottom: 1px dashed rgba(255,255,255,0.08);
    }
    .sc-detection-panel .setting-row:last-child {
        border-bottom: none;
    }
    .sc-detection-panel .setting-row .lbl {
        color: rgba(226,232,240,0.7);
        font-weight: 500;
    }
    .sc-detection-panel .setting-row .val {
        color: #ffffff;
        font-weight: 600;
        text-align: right;
    }
    .sc-detection-panel .status-dot {
        display: inline-block;
        width: 8px;
        height: 8px;
        border-radius: 50%;
        background: #10b981;
        margin-right: 5px;
        vertical-align: middle;
        box-shadow: 0 0 6px rgba(16,185,129,0.6);
    }

    /* ===== FINAL V5 LAYOUT FIX =====
       Compact the Streamlit chrome so the dashboard starts near the top of
       the viewport.  Keep the existing visual design; only spacing/sizing. */
    [data-testid="stMainBlockContainer"],
    .stMainBlockContainer {
        padding-top: 0.45rem !important;
        padding-bottom: 1.25rem !important;
        margin-top: -5.5rem !important;
    }
    [data-testid="stAppViewContainer"] .main .block-container {
        padding-top: 0.45rem !important;
        padding-bottom: 1.25rem !important;
        margin-top: -5.5rem !important;
    }
    /* Smaller horizontal navigation: no oversized empty band. */
    .sc-top-nav {
        min-height: 3.55rem !important;
        height: 3.55rem !important;
        margin: 0 0 0.8rem !important;
        padding: 0 !important;
    }
    .sc-top-nav [data-testid="stPageLink"] a,
    .sc-top-nav [data-testid="stPageLink"] a:visited {
        min-height: 3.35rem !important;
        height: 3.35rem !important;
        gap: 3px !important;
        padding: 0.3rem 0.15rem !important;
        font-size: 11px !important;
    }
    .sc-top-nav [data-testid="stPageLink"] a p,
    .sc-top-nav [data-testid="stPageLink"] a span,
    .sc-top-nav [data-testid="stPageLink"] a div {
        font-size: 11px !important;
        font-weight: 600 !important;
    }
    .sc-top-nav [data-testid="stPageLink"] a svg {
        width: 17px !important;
        height: 17px !important;
    }
    /* Compact hero to match the supplied screenshot without wasting space. */
    .sc-hero {
        min-height: 195px !important;
        height: 195px !important;
        padding: 1.75rem 2rem !important;
        margin-bottom: 1.15rem !important;
    }
    .sc-hero h1 { font-size: 2.35rem !important; }
    .sc-hero .subtitle { font-size: 1rem !important; }
    .sc-hero .tagline { font-size: 0.82rem !important; margin-top: 0.8rem !important; }
    /* Sidebar: compact enough to fit all navigation/settings without scrolling. */
    section[data-testid="stSidebar"],
    [data-testid="stSidebar"] {
        overflow: hidden !important;
    }
    section[data-testid="stSidebar"] [data-testid="stSidebarContent"],
    section[data-testid="stSidebar"] [data-testid="stSidebarUserContent"] {
        overflow: hidden !important;
        padding-top: 0 !important;
    }
    [data-testid="stSidebar"] .sc-sidebar-brand {
        padding: 0.7rem 0 0.55rem !important;
        margin-bottom: 0 !important;
    }
    [data-testid="stSidebar"] .sc-brand-name { font-size: 1.42rem !important; }
    [data-testid="stSidebar"] .sc-brand-subtitle { font-size: 0.68rem !important; margin-top: 0.28rem !important; }
    .sc-sidebar-nav {
        margin: 0.25rem -0.15rem 0.45rem !important;
        padding: 0.25rem 0 !important;
    }
    .sc-sidebar-nav [data-testid="stPageLink"] { margin: 0 !important; }
    .sc-sidebar-nav [data-testid="stPageLink"] a,
    .sc-sidebar-nav [data-testid="stPageLink"] a:visited {
        min-height: 2.05rem !important;
        height: 2.05rem !important;
        padding: 0.25rem 0.55rem !important;
        gap: 9px !important;
        border-radius: 7px !important;
        font-size: 12px !important;
    }
    .sc-sidebar-nav [data-testid="stPageLink"] a p,
    .sc-sidebar-nav [data-testid="stPageLink"] a span,
    .sc-sidebar-nav [data-testid="stPageLink"] a div { font-size: 12px !important; }
    .sc-sidebar-nav [data-testid="stPageLink"] a svg { width: 16px !important; height: 16px !important; }
    [data-testid="stSidebar"] .sc-about-btn button {
        min-height: 2rem !important;
        padding: 0.25rem 0.5rem !important;
        font-size: 0.78rem !important;
    }
    [data-testid="stSidebar"] h3 { font-size: 0.78rem !important; margin-top: 0.55rem !important; margin-bottom: 0.25rem !important; }
    .sc-detection-panel { padding: 0.42rem 0.6rem !important; margin: 0.2rem 0 0.45rem !important; }
    .sc-detection-panel .setting-row { padding: 0.18rem 0 !important; font-size: 0.68rem !important; }
    .sc-footer { margin-top: 1.5rem !important; padding-top: 1rem !important; }
    .sc-sidebar-nav [data-testid="stPageLink"] a::before,
    .sc-sidebar-nav [data-testid="stPageLink"] a::marker { content: none !important; display: none !important; }

    /* ===== FINAL REFERENCE MATCH OVERRIDES ===== */
    /* ===== FINAL SPACING CORRECTION =====
       Remove Streamlit's large default top breathing room so the app starts
       near the top of the viewport like the supplied reference. */
    [data-testid="stAppViewContainer"] .main .block-container {
        padding-top: 0 !important;
        padding-bottom: 1.5rem !important;
        margin-top: -4.5rem !important;
    }
    [data-testid="stSidebar"] > div:first-child {
        padding-top: 0 !important;
    }
    section[data-testid="stSidebar"] [data-testid="stSidebarContent"],
    section[data-testid="stSidebar"] [data-testid="stSidebarUserContent"] {
        padding-top: 0.35rem !important;
    }
    /* Keep the top nav substantial, but do not let it create a giant blank band. */
    .sc-top-nav {
        min-height: 4.6rem !important;
        margin: 0 0 0.9rem !important;
    }
    .sc-top-nav [data-testid="stPageLink"] a,
    .sc-top-nav [data-testid="stPageLink"] a:visited {
        min-height: 4.45rem !important;
        padding: 0.45rem 0.2rem 0.4rem !important;
    }
    /* Hero should feel like the reference: wide, not overly tall, with a
       soft/lighter road image rather than a dark photographic block. */
    .sc-hero {
        min-height: 205px !important;
        padding: 1.8rem 2rem !important;
        margin-bottom: 1.25rem !important;
    }
    .sc-hero-road img {
        opacity: 0.62 !important;
        filter: saturate(0.72) brightness(1.22) contrast(0.88) !important;
        mix-blend-mode: screen !important;
    }
    .sc-hero-road::after {
        background: linear-gradient(90deg, rgba(8,78,119,.88) 0%, rgba(8,78,119,.48) 42%, rgba(8,78,119,.16) 100%) !important;
    }
    .sc-hero-content {
        max-width: 54% !important;
    }
    [data-testid="stSidebar"],
    section[data-testid="stSidebar"],
    section[data-testid="stSidebar"] > div:first-child {
        width: 282px !important;
        min-width: 282px !important;
        max-width: 282px !important;
    }
    section[data-testid="stSidebar"] [data-testid="stSidebarContent"],
    section[data-testid="stSidebar"] [data-testid="stSidebarUserContent"] {
        width: 262px !important;
        max-width: 262px !important;
        overflow-x: hidden !important;
        overflow-y: auto !important;
        scrollbar-width: none !important;
    }
    section[data-testid="stSidebar"] [data-testid="stSidebarContent"]::-webkit-scrollbar { display:none !important; }

    [data-testid="stSidebar"] .sc-sidebar-brand {
        padding: 1.15rem 0 0.9rem !important;
    }
    [data-testid="stSidebar"] .sc-brand-name {
        font-size: 1.62rem !important;
    }
    [data-testid="stSidebar"] .sc-brand-subtitle {
        font-size: 0.80rem !important;
        margin-top: 0.5rem !important;
    }
    .sc-sidebar-nav {
        margin: 0.45rem -0.15rem 0.7rem !important;
        padding: 0.55rem 0 !important;
    }
    .sc-sidebar-nav [data-testid="stPageLink"] a,
    .sc-sidebar-nav [data-testid="stPageLink"] a:visited {
        min-height: 2.55rem !important;
        padding: 0.48rem 0.62rem !important;
        gap: 12px !important;
        font-size: 15px !important;
        font-weight: 700 !important;
        border-radius: 8px !important;
    }
    .sc-sidebar-nav [data-testid="stPageLink"] a p,
    .sc-sidebar-nav [data-testid="stPageLink"] a span,
    .sc-sidebar-nav [data-testid="stPageLink"] a div {
        font-size: 15px !important;
    }
    .sc-sidebar-nav [data-testid="stPageLink"] a svg {
        width: 20px !important;
        height: 20px !important;
    }
    [data-testid="stSidebar"] .sc-about-btn button {
        min-height: 2.45rem !important;
        font-size: 0.90rem !important;
    }
    [data-testid="stSidebar"] h3 {
        font-size: 0.95rem !important;
        letter-spacing: .04em !important;
    }

    /* Larger top navigation, matching the supplied reference screenshot */
    .sc-top-nav {
        min-height: 6.2rem !important;
        margin: -0.2rem 0 1.25rem !important;
        padding: 0 !important;
        align-items: stretch !important;
    }
    .sc-top-nav [data-testid="stPageLink"] a,
    .sc-top-nav [data-testid="stPageLink"] a:visited {
        min-height: 6.0rem !important;
        gap: 8px !important;
        padding: 0.65rem 0.25rem 0.55rem !important;
        font-size: 14px !important;
        font-weight: 700 !important;
    }
    .sc-top-nav [data-testid="stPageLink"] a p,
    .sc-top-nav [data-testid="stPageLink"] a span,
    .sc-top-nav [data-testid="stPageLink"] a div {
        font-size: 14px !important;
        font-weight: 700 !important;
    }
    .sc-top-nav [data-testid="stPageLink"] a svg {
        width: 26px !important;
        height: 26px !important;
    }

    /* Hero: taller, cleaner, and with the real crossing visual on the right */
    .sc-hero {
        min-height: 235px !important;
        padding: 2.15rem 2.25rem !important;
        border-radius: 13px !important;
        margin-bottom: 1.6rem !important;
    }
    .sc-hero-content {
        max-width: 50% !important;
        z-index: 4 !important;
    }
    .sc-hero h1 {
        font-size: 2.55rem !important;
        line-height: 1.08 !important;
    }
    .sc-hero .subtitle {
        font-size: 1.08rem !important;
        margin-top: 0.7rem !important;
    }
    .sc-hero .tagline {
        font-size: 0.86rem !important;
        line-height: 1.45 !important;
        margin-top: 1rem !important;
    }
    .sc-hero-road {
        width: 55% !important;
        height: 100% !important;
        right: 0 !important;
        bottom: 0 !important;
        opacity: 1 !important;
        z-index: 2 !important;
        overflow: hidden !important;
    }
    .sc-hero-road img {
        width: 100% !important;
        height: 100% !important;
        object-fit: cover !important;
        object-position: center !important;
        display: block !important;
        filter: saturate(.9) contrast(.95) !important;
    }
    .sc-hero-road::after {
        content: '' !important;
        position: absolute !important;
        inset: 0 !important;
        background: linear-gradient(90deg, rgba(8,78,119,.72) 0%, rgba(8,78,119,.20) 35%, rgba(8,78,119,.08) 100%) !important;
        pointer-events: none !important;
    }
    .sc-hero-road svg { display: none !important; }


    /* ===== V5 ULTIMATE SPACING OVERRIDES ===== */
    [data-testid="stMainBlockContainer"], .stMainBlockContainer,
    [data-testid="stAppViewContainer"] .main .block-container {
        padding-top: 0.35rem !important;
        padding-bottom: 1.25rem !important;
        margin-top: -9rem !important;
    }
    .sc-top-nav { min-height: 3.5rem !important; height: 3.5rem !important; margin: 0 0 0.8rem !important; }
    .sc-top-nav [data-testid="stPageLink"] a,
    .sc-top-nav [data-testid="stPageLink"] a:visited { min-height: 3.3rem !important; height: 3.3rem !important; padding: 0.25rem 0.15rem !important; gap: 3px !important; font-size: 11px !important; }
    .sc-top-nav [data-testid="stPageLink"] a p, .sc-top-nav [data-testid="stPageLink"] a span, .sc-top-nav [data-testid="stPageLink"] a div { font-size: 11px !important; font-weight: 600 !important; }
    .sc-top-nav [data-testid="stPageLink"] a svg { width: 17px !important; height: 17px !important; }
    .sc-hero { min-height: 195px !important; height: 195px !important; padding: 1.7rem 2rem !important; margin-bottom: 1.1rem !important; }
    .sc-hero h1 { font-size: 2.35rem !important; }
    .sc-hero .subtitle { font-size: 1rem !important; }
    .sc-hero .tagline { font-size: 0.82rem !important; margin-top: 0.8rem !important; }
    section[data-testid="stSidebar"], [data-testid="stSidebar"],
    section[data-testid="stSidebar"] [data-testid="stSidebarContent"],
    section[data-testid="stSidebar"] [data-testid="stSidebarUserContent"] { overflow: hidden !important; }
    [data-testid="stSidebar"] .sc-sidebar-brand { padding: 0.7rem 0 0.55rem !important; }
    [data-testid="stSidebar"] .sc-brand-name { font-size: 1.42rem !important; }
    [data-testid="stSidebar"] .sc-brand-subtitle { font-size: 0.68rem !important; margin-top: 0.28rem !important; }
    .sc-sidebar-nav { margin: 0.25rem -0.15rem 0.45rem !important; padding: 0.25rem 0 !important; }
    .sc-sidebar-nav [data-testid="stPageLink"] { margin: 0 !important; }
    .sc-sidebar-nav [data-testid="stPageLink"] a, .sc-sidebar-nav [data-testid="stPageLink"] a:visited { min-height: 2.05rem !important; height: 2.05rem !important; padding: 0.25rem 0.55rem !important; gap: 9px !important; font-size: 12px !important; }
    .sc-sidebar-nav [data-testid="stPageLink"] a p, .sc-sidebar-nav [data-testid="stPageLink"] a span, .sc-sidebar-nav [data-testid="stPageLink"] a div { font-size: 12px !important; }
    .sc-sidebar-nav [data-testid="stPageLink"] a svg { width: 16px !important; height: 16px !important; }
    [data-testid="stSidebar"] .sc-about-btn button { min-height: 2rem !important; font-size: 0.78rem !important; padding: 0.25rem 0.5rem !important; }
    [data-testid="stSidebar"] h3 { font-size: 0.78rem !important; margin-top: 0.55rem !important; margin-bottom: 0.25rem !important; }
    .sc-detection-panel { padding: 0.42rem 0.6rem !important; margin: 0.2rem 0 0.45rem !important; }
    .sc-detection-panel .setting-row { padding: 0.18rem 0 !important; font-size: 0.68rem !important; }

    /* ================================================================
       FINAL USER-REFERENCE UI FIX
       Match the supplied SafeCross AI reference:
       - Keep the 7-item top navigation visible
       - Compact 226px sidebar
       - Reference-sized text/icons
       - Controlled blank space above sidebar brand
       - Compact hero with road/crossing image on right
       - No giant top gap and no sidebar scrolling
       ================================================================ */

    /* Main content: remove the old negative top-margin overrides. */
    [data-testid="stAppViewContainer"] .main .block-container,
    [data-testid="stMainBlockContainer"],
    .stMainBlockContainer {
        padding-top: 0 !important;
        padding-bottom: 1.5rem !important;
        margin-top: 0 !important;
        max-width: none !important;
    }

    /* Keep Streamlit's header visually unobtrusive. */
    [data-testid="stHeader"] {
        background: transparent !important;
        height: 0 !important;
    }

    /* ---------- SIDEBAR ---------- */
    section[data-testid="stSidebar"],
    [data-testid="stSidebar"] {
        width: 226px !important;
        min-width: 226px !important;
        max-width: 226px !important;
        overflow: hidden !important;
    }

    section[data-testid="stSidebar"] > div:first-child {
        width: 226px !important;
        min-width: 226px !important;
        max-width: 226px !important;
        overflow: hidden !important;
    }

    section[data-testid="stSidebar"] [data-testid="stSidebarContent"],
    section[data-testid="stSidebar"] [data-testid="stSidebarUserContent"] {
        width: 210px !important;
        max-width: 210px !important;
        overflow-x: hidden !important;
        overflow-y: hidden !important;
        scrollbar-width: none !important;
        padding-top: 0 !important;
    }
    section[data-testid="stSidebar"] [data-testid="stSidebarContent"]::-webkit-scrollbar,
    section[data-testid="stSidebar"] [data-testid="stSidebarUserContent"]::-webkit-scrollbar {
        display: none !important;
        width: 0 !important;
    }

    /* Reference has a modest blank band above the sidebar logo. */
    [data-testid="stSidebar"] .sc-sidebar-brand {
        padding: 4.55rem 0 0.55rem !important;
        margin: 0 !important;
    }
    [data-testid="stSidebar"] .sc-brand-row {
        gap: 6px !important;
    }
    [data-testid="stSidebar"] .sc-brand-shield {
        width: 23px !important;
        height: 27px !important;
    }
    [data-testid="stSidebar"] .sc-brand-name {
        font-size: 1.12rem !important;
        line-height: 1 !important;
        font-weight: 800 !important;
    }
    [data-testid="stSidebar"] .sc-brand-subtitle {
        font-size: 0.52rem !important;
        margin-top: 0.28rem !important;
        font-weight: 600 !important;
    }

    /* About button */
    [data-testid="stSidebar"] .sc-about-btn {
        margin: 0.45rem 0 0.65rem !important;
    }
    [data-testid="stSidebar"] .sc-about-btn button {
        min-height: 2.0rem !important;
        height: 2.0rem !important;
        padding: 0.2rem 0.35rem !important;
        font-size: 0.68rem !important;
        border-radius: 6px !important;
    }

    /* Sidebar links: same compact visual scale as supplied reference. */
    .sc-sidebar-nav {
        margin: 0.35rem -0.05rem 0.45rem !important;
        padding: 0.3rem 0 !important;
    }
    .sc-sidebar-nav [data-testid="stPageLink"] {
        margin: 0 !important;
    }
    .sc-sidebar-nav [data-testid="stPageLink"] a,
    .sc-sidebar-nav [data-testid="stPageLink"] a:visited {
        min-height: 1.85rem !important;
        height: 1.85rem !important;
        padding: 0.22rem 0.35rem !important;
        gap: 8px !important;
        border-radius: 6px !important;
        font-size: 11px !important;
        font-weight: 600 !important;
    }
    .sc-sidebar-nav [data-testid="stPageLink"] a p,
    .sc-sidebar-nav [data-testid="stPageLink"] a span,
    .sc-sidebar-nav [data-testid="stPageLink"] a div {
        font-size: 11px !important;
        font-weight: 600 !important;
        line-height: 1.15 !important;
    }
    .sc-sidebar-nav [data-testid="stPageLink"] a svg {
        width: 14px !important;
        height: 14px !important;
    }

    /* Detection settings */
    [data-testid="stSidebar"] h3 {
        font-size: 0.68rem !important;
        margin-top: 0.5rem !important;
        margin-bottom: 0.25rem !important;
        letter-spacing: .04em !important;
    }
    .sc-detection-panel {
        padding: 0.35rem 0.45rem !important;
        margin: 0.15rem 0 0.35rem !important;
        border-radius: 6px !important;
    }
    .sc-detection-panel .setting-row {
        padding: 0.13rem 0 !important;
        font-size: 0.60rem !important;
    }
    .sc-detection-panel .setting-row .lbl,
    .sc-detection-panel .setting-row .val {
        font-size: 0.60rem !important;
    }

    /* Live Detection interactive controls remain usable at the compact size. */
    [data-testid="stSidebar"] label,
    [data-testid="stSidebar"] .stRadio label,
    [data-testid="stSidebar"] .stSelectbox label {
        font-size: 0.68rem !important;
    }
    [data-testid="stSidebar"] .stRadio div[role="radiogroup"] label p {
        font-size: 0.68rem !important;
    }
    [data-testid="stSidebar"] .stSelectbox [data-baseweb="select"] {
        min-height: 2rem !important;
    }

    /* ---------- TOP HORIZONTAL NAV ---------- */
    .sc-top-nav {
        display: flex !important;
        width: 100% !important;
        min-height: 3.35rem !important;
        height: 3.35rem !important;
        margin: 0 0 0.9rem !important;
        padding: 0 !important;
        border-bottom: 1px solid #e5e7eb !important;
        overflow: hidden !important;
    }
    .sc-top-nav [data-testid="stPageLink"] {
        flex: 1 1 0 !important;
        min-width: 0 !important;
    }
    .sc-top-nav [data-testid="stPageLink"] a,
    .sc-top-nav [data-testid="stPageLink"] a:visited {
        min-height: 3.25rem !important;
        height: 3.25rem !important;
        display: flex !important;
        flex-direction: column !important;
        align-items: center !important;
        justify-content: center !important;
        gap: 3px !important;
        padding: 0.25rem 0.1rem !important;
        color: #17233b !important;
        background: transparent !important;
        font-size: 10px !important;
        font-weight: 600 !important;
        border-bottom: 2px solid transparent !important;
        border-radius: 0 !important;
        white-space: nowrap !important;
        text-decoration: none !important;
    }
    .sc-top-nav [data-testid="stPageLink"] a p,
    .sc-top-nav [data-testid="stPageLink"] a span,
    .sc-top-nav [data-testid="stPageLink"] a div {
        font-size: 10px !important;
        font-weight: 600 !important;
        line-height: 1.05 !important;
    }
    .sc-top-nav [data-testid="stPageLink"] a svg {
        width: 20px !important;
        height: 20px !important;
    }

    /* ---------- HOME HERO ---------- */
    .sc-hero {
        min-height: 155px !important;
        height: 155px !important;
        padding: 1.45rem 1.65rem !important;
        border-radius: 11px !important;
        margin-bottom: 1.0rem !important;
        overflow: hidden !important;
    }
    .sc-hero-content {
        max-width: 47% !important;
        z-index: 4 !important;
    }
    .sc-hero h1 {
        font-size: 1.85rem !important;
        line-height: 1.05 !important;
        margin: 0 !important;
    }
    .sc-hero .subtitle {
        font-size: 0.72rem !important;
        line-height: 1.35 !important;
        margin-top: 0.55rem !important;
    }
    .sc-hero .tagline {
        font-size: 0.58rem !important;
        line-height: 1.35 !important;
        margin-top: 0.7rem !important;
    }
    .sc-hero-road {
        width: 55% !important;
        height: 100% !important;
        right: 0 !important;
        bottom: 0 !important;
        opacity: 1 !important;
        z-index: 2 !important;
        overflow: hidden !important;
    }
    .sc-hero-road img {
        width: 100% !important;
        height: 100% !important;
        object-fit: cover !important;
        object-position: center !important;
        display: block !important;
        filter: saturate(.9) contrast(.95) !important;
        opacity: .78 !important;
        mix-blend-mode: normal !important;
    }
    .sc-hero-road::after {
        content: '' !important;
        position: absolute !important;
        inset: 0 !important;
        background: linear-gradient(90deg, rgba(8,78,119,.82) 0%, rgba(8,78,119,.25) 38%, rgba(8,78,119,.06) 100%) !important;
        pointer-events: none !important;
    }

    /* Home page section text/card scale matching the reference. */
    .sc-section-title {
        font-size: 0.95rem !important;
        margin: 1.0rem 0 0.55rem !important;
        padding-bottom: 0.4rem !important;
    }
    .sc-pipeline-step {
        padding: 0.75rem 0.25rem !important;
    }
    .sc-pipeline-step .step-label {
        font-size: 0.58rem !important;
    }
    .sc-feature-card {
        padding: 1rem !important;
    }
    .sc-feature-card .title {
        font-size: 0.78rem !important;
    }
    .sc-feature-card .desc {
        font-size: 0.66rem !important;
    }

    /* Footer stays inside the viewport on the compact reference layout. */
    .sc-footer {
        margin-top: 1rem !important;
        padding: 0.8rem 0 0.5rem !important;
    }

    /* Keep the custom sidebar nav and top nav visible; only Streamlit's
       duplicate auto-generated navigation is hidden. */
    [data-testid="stSidebarNav"] {
        display: none !important;
    }



    /* ================================================================
       FINAL USER REQUEST OVERRIDES
       - Remove the large empty space above the sidebar brand
       - Increase sidebar text size for readability
       - Increase homepage hero/title text size
       ================================================================ */

    /* Sidebar: start content close to the top */
    section[data-testid="stSidebar"] [data-testid="stSidebarContent"],
    section[data-testid="stSidebar"] [data-testid="stSidebarUserContent"] {
        padding-top: 0 !important;
    }

    [data-testid="stSidebar"] .sc-sidebar-brand {
        padding: 0.35rem 0 0.65rem !important;
        margin-top: 0 !important;
    }

    [data-testid="stSidebar"] .sc-brand-shield {
        width: 27px !important;
        height: 31px !important;
    }

    [data-testid="stSidebar"] .sc-brand-name {
        font-size: 1.38rem !important;
    }

    [data-testid="stSidebar"] .sc-brand-subtitle {
        font-size: 0.70rem !important;
        margin-top: 0.35rem !important;
    }

    /* Sidebar navigation: larger, clearer text */
    .sc-sidebar-nav [data-testid="stPageLink"] a,
    .sc-sidebar-nav [data-testid="stPageLink"] a:visited {
        min-height: 2.05rem !important;
        height: 2.05rem !important;
        padding: 0.28rem 0.45rem !important;
        gap: 9px !important;
        font-size: 13px !important;
        font-weight: 650 !important;
    }

    .sc-sidebar-nav [data-testid="stPageLink"] a p,
    .sc-sidebar-nav [data-testid="stPageLink"] a span,
    .sc-sidebar-nav [data-testid="stPageLink"] a div {
        font-size: 13px !important;
        line-height: 1.2 !important;
    }

    .sc-sidebar-nav [data-testid="stPageLink"] a svg {
        width: 17px !important;
        height: 17px !important;
    }

    [data-testid="stSidebar"] .sc-about-btn button,
    [data-testid="stSidebar"] .sc-about-btn button p,
    [data-testid="stSidebar"] .sc-about-btn button span,
    [data-testid="stSidebar"] .sc-about-btn button div {
        font-size: 0.75rem !important;
    }

    [data-testid="stSidebar"] h3 {
        font-size: 0.74rem !important;
    }

    .sc-detection-panel .setting-row,
    .sc-detection-panel .setting-row .lbl,
    .sc-detection-panel .setting-row .val {
        font-size: 0.66rem !important;
    }

    /* Homepage: make the main SafeCross AI text clearly larger */
    .sc-hero {
        padding: 1.7rem 1.8rem !important;
    }

    .sc-hero h1 {
        font-size: 2.35rem !important;
        line-height: 1.08 !important;
    }

    .sc-hero .subtitle {
        font-size: 0.98rem !important;
        line-height: 1.4 !important;
        margin-top: 0.6rem !important;
    }

    .sc-hero .tagline {
        font-size: 0.76rem !important;
        line-height: 1.4 !important;
        margin-top: 0.75rem !important;
    }

    /* Homepage section headings slightly larger too */
    .sc-section-title {
        font-size: 1.28rem !important;
    }


    /* ===== FINAL HERO FIX: prevent SafeCross AI heading/content from being cut ===== */
    .sc-hero {
        min-height: 225px !important;
        height: 225px !important;
        padding: 1.8rem 2rem !important;
        overflow: hidden !important;
    }

    .sc-hero-content {
        max-width: 50% !important;
        z-index: 5 !important;
    }

    .sc-hero h1 {
        font-size: 2.55rem !important;
        line-height: 1.08 !important;
        margin: 0 !important;
    }

    .sc-hero .subtitle {
        font-size: 1.02rem !important;
        line-height: 1.4 !important;
        margin-top: 0.6rem !important;
    }

    .sc-hero .tagline {
        font-size: 0.74rem !important;
        line-height: 1.45 !important;
        margin-top: 0.75rem !important;
    }

    .sc-hero-road {
        width: 55% !important;
        height: 100% !important;
        right: 0 !important;
        bottom: 0 !important;
        z-index: 2 !important;
        overflow: hidden !important;
    }


    /* ===== FINAL SIZE POLISH ===== */

    /* Give the sidebar enough width so the larger labels don't feel cramped. */
    section[data-testid="stSidebar"] {
        width: 230px !important;
        min-width: 230px !important;
    }

    section[data-testid="stSidebar"] > div:first-child {
        width: 230px !important;
    }

    /* Sidebar brand */
    [data-testid="stSidebar"] .sc-brand-name {
        font-size: 1.52rem !important;
        line-height: 1.1 !important;
    }

    [data-testid="stSidebar"] .sc-brand-subtitle {
        font-size: 0.76rem !important;
        line-height: 1.25 !important;
    }

    /* Sidebar navigation text: noticeably larger */
    .sc-sidebar-nav [data-testid="stPageLink"] a,
    .sc-sidebar-nav [data-testid="stPageLink"] a:visited {
        min-height: 2.25rem !important;
        height: 2.25rem !important;
        padding: 0.34rem 0.5rem !important;
        gap: 10px !important;
        font-size: 14.5px !important;
        font-weight: 650 !important;
    }

    .sc-sidebar-nav [data-testid="stPageLink"] a p,
    .sc-sidebar-nav [data-testid="stPageLink"] a span,
    .sc-sidebar-nav [data-testid="stPageLink"] a div {
        font-size: 14.5px !important;
        line-height: 1.2 !important;
    }

    .sc-sidebar-nav [data-testid="stPageLink"] a svg {
        width: 18px !important;
        height: 18px !important;
    }

    /* Top horizontal navigation: enlarge the tiny labels */
    .sc-top-nav [data-testid="stPageLink"] a,
    .sc-top-nav [data-testid="stPageLink"] a:visited {
        min-height: 2.35rem !important;
        padding: 0.35rem 0.15rem !important;
        font-size: 12.5px !important;
        font-weight: 650 !important;
        white-space: nowrap !important;
    }

    .sc-top-nav [data-testid="stPageLink"] a p,
    .sc-top-nav [data-testid="stPageLink"] a span,
    .sc-top-nav [data-testid="stPageLink"] a div {
        font-size: 12.5px !important;
        line-height: 1.15 !important;
    }

    .sc-top-nav [data-testid="stPageLink"] a svg {
        width: 18px !important;
        height: 18px !important;
    }

    /* Homepage hero title: large but fully visible */
    .sc-hero {
        min-height: 225px !important;
        height: 225px !important;
        padding: 1.8rem 2rem !important;
    }

    .sc-hero h1 {
        font-size: 2.55rem !important;
        line-height: 1.08 !important;
    }

    .sc-hero .subtitle {
        font-size: 1.02rem !important;
    }

</style>
"""


def inject_global_css():
    """Inject the global design system CSS into the page."""
    st.markdown(GLOBAL_CSS, unsafe_allow_html=True)


def render_page_header(title: str, subtitle: str = "", icon: str = ""):
    """Render a consistent page header."""
    display_title = f"{icon} {title}" if icon else title
    subtitle_html = f'<p>{subtitle}</p>' if subtitle else ''
    st.markdown(f"""
    <div class="sc-page-header">
        <h2>{display_title}</h2>
        {subtitle_html}
    </div>
    """, unsafe_allow_html=True)


def render_hero(title: str, subtitle: str, tagline: str = ""):
    """Render the hero section for the home page."""
    tagline_html = f'<p class="tagline">{tagline}</p>' if tagline else ''
    st.markdown(f"""
    <div class="sc-hero">
        <div class="sc-hero-content">
            <h1>{title}</h1>
            <p class="subtitle">{subtitle}</p>
            {tagline_html}
        </div>
        <div class="sc-hero-road" aria-hidden="true">
            <img src="data:image/png;base64,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" alt="Road with pedestrians crossing at a zebra crossing" />
        </div>
    </div>
    """, unsafe_allow_html=True)


def render_metric_card(label: str, value: str, color: str = "#1e3a5f", sub: str = ""):
    """Render a single metric card."""
    sub_html = f'<div class="sub">{sub}</div>' if sub else ''
    st.markdown(f"""
    <div class="sc-card">
        <div class="sc-metric">
            <div class="label">{label}</div>
            <div class="value" style="color: {color};">{value}</div>
            {sub_html}
        </div>
    </div>
    """, unsafe_allow_html=True)


def render_compact_metric_card(label: str, value: str, color: str = "#1e3a5f", sub: str = ""):
    """Render a compact metric card for tight layouts (e.g. System Status row)."""
    sub_html = f'<div class="sub">{sub}</div>' if sub else ''
    st.markdown(f"""
    <div class="sc-compact-metric">
        <div class="label">{label}</div>
        <div class="value" style="color: {color};">{value}</div>
        {sub_html}
    </div>
    """, unsafe_allow_html=True)


def render_feature_card(icon: str, title: str, desc: str, status: str, status_color: str = "#10b981"):
    """Render a feature card for the home page grid."""
    st.markdown(f"""
    <div class="sc-feature-card">
        <div class="icon">{icon}</div>
        <div class="title">{title}</div>
        <div class="desc">{desc}</div>
        <span class="status" style="background: {status_color}15; color: {status_color};">{status}</span>
    </div>
    """, unsafe_allow_html=True)


def render_pipeline_step(icon: str, label: str, active: bool = False):
    """Render a single pipeline step."""
    cls = "sc-pipeline-step active" if active else "sc-pipeline-step"
    st.markdown(f"""
    <div class="{cls}">
        <div class="step-icon">{icon}</div>
        <div class="step-label">{label}</div>
    </div>
    """, unsafe_allow_html=True)


def render_footer():
    """Render the professional footer."""
    st.markdown("""
    <div class="sc-footer">
        <div class="brand">SafeCross AI</div>
        <div>Intelligent Road Safety & Emergency Management</div>
        <div style="margin-top: 0.5rem; font-size: 0.8rem;">
            Prototype &bull; AI-assisted &bull; Safety-first
        </div>
        <div style="margin-top: 0.3rem; font-size: 0.75rem; color: #9ca3af;">
            AI-assisted prototype developed for hackathon demonstration.
        </div>
    </div>
    """, unsafe_allow_html=True)


def render_section_title(title: str):
    """Render a consistent section title."""
    st.markdown(f'<div class="sc-section-title">{title}</div>', unsafe_allow_html=True)


def render_status_badge(text: str, color: str = "#6b7280"):
    """Render a status badge."""
    st.markdown(
        f'<span class="sc-status-badge" style="background: {color}15; color: {color};">{text}</span>',
        unsafe_allow_html=True,
    )


def render_sidebar_brand():
    """Render the SafeCross AI brand in the sidebar."""
    st.markdown("""
    <div class="sc-sidebar-brand">
        <div class="sc-brand-row">
            <svg class="sc-brand-shield" viewBox="0 0 32 36" aria-hidden="true">
                <path d="M16 2 L29 7 V17 C29 26 23 32 16 35 C9 32 3 26 3 17 V7 Z" fill="none" stroke="currentColor" stroke-width="2.2"/>
                <path d="M16 8 L23 11 V17 C23 22.5 20 26.2 16 28.5 C12 26.2 9 22.5 9 17 V11 Z" fill="none" stroke="currentColor" stroke-width="1.4" opacity=".7"/>
            </svg>
            <div class="sc-brand-name">SafeCross AI</div>
        </div>
        <div class="sc-brand-subtitle">Road Safety Intelligence</div>
    </div>
    """, unsafe_allow_html=True)


def render_sidebar_about():
    """Render an outlined About button in the sidebar that toggles a description."""
    if "about_open" not in st.session_state:
        st.session_state.about_open = False
    st.markdown('<div class="sc-about-btn">', unsafe_allow_html=True)
    if st.button("About SafeCross AI", key="sc_about_btn", use_container_width=True):
        st.session_state.about_open = not st.session_state.about_open
    st.markdown('</div>', unsafe_allow_html=True)
    if st.session_state.about_open:
        st.markdown("""
        <div class="sc-about-content">
            <strong>SafeCross AI</strong> is an intelligent road safety and emergency
            management platform built for Pakistan.
            <br><br>
            Combines computer vision, severity prediction, fatality risk, hotspot mapping,
            and emergency priority decision support.
        </div>
        """, unsafe_allow_html=True)


def render_sidebar_footer():
    """Render a compact footer in the sidebar."""
    st.markdown("""
    <div style="text-align: center; padding: 0.6rem 0 0.3rem 0; margin-top: 0.5rem;
                border-top: 1px solid rgba(255,255,255,0.15);">
        <div style="font-size: 0.72rem; color: rgba(255,255,255,0.7); font-weight: 600;">
            SafeCross AI
        </div>
        <div style="font-size: 0.65rem; color: rgba(255,255,255,0.5); margin-top: 0.15rem;">
            Decision Support Only
        </div>
        <div style="font-size: 0.6rem; color: rgba(255,255,255,0.4); margin-top: 0.15rem;">
            © 2026 SafeCross AI Team
        </div>
    </div>
    """, unsafe_allow_html=True)


# ── Top Horizontal Navigation ────────────────────────────────────────────────
_NAV_ITEMS = [
    ("app.py", "Home", ":material/home:"),
    ("pages/1__Severity_Predictor.py", "Severity Predictor", ":material/bar_chart:"),
    ("pages/2__Fatality_Risk.py", "Fatality Risk", ":material/person_alert:"),
    ("pages/3__Pakistan_Dashboard.py", "Pakistan Dashboard", ":material/grid_view:"),
    ("pages/4__Hotspot_Map.py", "Hotspot Map", ":material/location_on:"),
    ("pages/5__Emergency_Response.py", "Emergency Response", ":material/local_shipping:"),
    ("pages/6__Live_Detection.py", "Live Detection", ":material/videocam:"),
    ("pages/7__Emergency_Priority.py", "Emergency Priority", ":material/warning:"),
    ("pages/8__Prediction_History.py", "Prediction History", ":material/history:"),
]


def render_sidebar_nav():
    """Render the seven functional sidebar links with professional Material icons."""
    st.markdown('<div class="sc-sidebar-nav">', unsafe_allow_html=True)
    for path, label, icon in _NAV_ITEMS:
        st.page_link(path, label=label, icon=icon, use_container_width=True)
    st.markdown('</div>', unsafe_allow_html=True)


def render_top_nav():
    """Render the seven functional horizontal page links with Material icons."""
    st.markdown('<div class="sc-top-nav">', unsafe_allow_html=True)
    cols = st.columns(len(_NAV_ITEMS), gap="small")
    for col, (path, label, icon) in zip(cols, _NAV_ITEMS):
        with col:
            st.page_link(path, label=label, icon=icon, use_container_width=True)
    st.markdown('</div>', unsafe_allow_html=True)


# ── Detection Settings Info Panel (sidebar) ────────────────────────────────

def render_detection_settings_panel(
    source: str = "Image Upload",
    model: str = "n (Nano - Fastest)",
):
    """Render a compact read-only Detection Settings panel in the sidebar.

    Used on pages that are NOT Live Detection. The full interactive controls
    remain on the Live Detection page.
    """
    st.markdown("### Detection Settings")
    st.markdown(f"""
    <div class="sc-detection-panel">
        <div class="setting-row">
            <span class="lbl">Input Source</span>
            <span class="val">{source}</span>
        </div>
        <div class="setting-row">
            <span class="lbl">Model Size</span>
            <span class="val">{model}</span>
        </div>
        <div class="setting-row">
            <span class="lbl">AI Model</span>
            <span class="val">YOLOv8n</span>
        </div>
        <div class="setting-row">
            <span class="lbl">Status</span>
            <span class="val" style="color: #10b981;">
                <span class="status-dot"></span>Ready
            </span>
        </div>
    </div>
    """, unsafe_allow_html=True)
