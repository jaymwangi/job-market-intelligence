# dashboard/pages/about.py
"""About page - Professional modern design."""

from datetime import datetime

import streamlit as st


def render():
    """Render the professional About page."""

    st.markdown(
        """
    <style>
        /* Main container */
        .about-container {
            max-width: 1200px;
            margin: 0 auto;
        }

        /* Hero Section */
        .about-hero {
            background: linear-gradient(135deg, #1a1a2e 0%, #16213e 100%);
            border-radius: 16px;
            padding: 3rem 2.5rem;
            margin-bottom: 2rem;
            position: relative;
            overflow: hidden;
            border: 1px solid rgba(255,255,255,0.05);
        }
        .about-hero::before {
            content: '';
            position: absolute;
            top: -50%;
            right: -20%;
            width: 400px;
            height: 400px;
            background: radial-gradient(circle, rgba(108,92,231,0.1), transparent 70%);
            border-radius: 50%;
        }
        .about-hero-content {
            position: relative;
            z-index: 1;
        }
        .about-hero-badge {
            display: inline-flex;
            align-items: center;
            gap: 0.5rem;
            background: rgba(108,92,231,0.2);
            padding: 0.3rem 1rem;
            border-radius: 20px;
            font-size: 0.75rem;
            color: #a29bfe;
            border: 1px solid rgba(108,92,231,0.3);
            margin-bottom: 1rem;
        }
        .about-hero-badge-dot {
            width: 6px;
            height: 6px;
            border-radius: 50%;
            background: #00d2d3;
            display: inline-block;
            animation: pulse 2s infinite;
        }
        @keyframes pulse {
            0%, 100% { opacity: 1; transform: scale(1); }
            50% { opacity: 0.3; transform: scale(0.8); }
        }
        .about-hero-title {
            font-size: 2.5rem;
            font-weight: 700;
            color: #ffffff;
            letter-spacing: -0.02em;
            margin-bottom: 0.5rem;
            background: linear-gradient(135deg, #ffffff 60%, rgba(255,255,255,0.6));
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            background-clip: text;
        }
        .about-hero-subtitle {
            font-size: 1.1rem;
            color: rgba(255,255,255,0.5);
            font-weight: 400;
        }
        .about-hero-meta {
            display: flex;
            gap: 2rem;
            margin-top: 1.5rem;
            flex-wrap: wrap;
        }
        .about-hero-meta-item {
            display: flex;
            align-items: center;
            gap: 0.5rem;
            color: rgba(255,255,255,0.4);
            font-size: 0.85rem;
        }
        .about-hero-meta-item strong {
            color: rgba(255,255,255,0.7);
            font-weight: 500;
        }
        .about-hero-meta-item .icon-svg {
            width: 18px;
            height: 18px;
            fill: rgba(255,255,255,0.3);
            flex-shrink: 0;
        }

        /* Card styles */
        .about-card {
            background: #ffffff;
            border-radius: 16px;
            padding: 1.75rem;
            border: 1px solid rgba(0,0,0,0.04);
            box-shadow: 0 4px 20px rgba(0,0,0,0.02);
            margin-bottom: 1.5rem;
            transition: all 0.2s ease;
        }
        .about-card:hover {
            box-shadow: 0 8px 30px rgba(0,0,0,0.04);
        }
        .about-card-title {
            font-size: 1.1rem;
            font-weight: 600;
            color: #1a1a2e;
            margin-bottom: 1rem;
            display: flex;
            align-items: center;
            gap: 0.5rem;
        }
        .about-card-title .icon-svg {
            width: 24px;
            height: 24px;
            fill: #6c5ce7;
            flex-shrink: 0;
        }
        .about-card-content {
            color: #2d3436;
            line-height: 1.7;
        }

        /* Grid layout */
        .about-grid-2 {
            display: grid;
            grid-template-columns: 1fr 1fr;
            gap: 1.5rem;
            margin-bottom: 1.5rem;
        }
        .about-grid-3 {
            display: grid;
            grid-template-columns: 1fr 1fr 1fr;
            gap: 1.5rem;
            margin-bottom: 1.5rem;
        }

        /* Stat cards */
        .stat-card {
            background: #f8f9fa;
            border-radius: 12px;
            padding: 1.25rem;
            border: 1px solid rgba(0,0,0,0.04);
            text-align: center;
            transition: all 0.2s ease;
        }
        .stat-card:hover {
            background: #f0f1f3;
            transform: translateY(-2px);
        }
        .stat-card .icon-svg {
            width: 32px;
            height: 32px;
            fill: #6c5ce7;
            margin-bottom: 0.5rem;
            opacity: 0.8;
        }
        .stat-card-value {
            font-size: 1.8rem;
            font-weight: 700;
            color: #1a1a2e;
            letter-spacing: -0.02em;
        }
        .stat-card-label {
            font-size: 0.75rem;
            color: #636e72;
            font-weight: 400;
            text-transform: uppercase;
            letter-spacing: 0.06em;
            margin-top: 0.25rem;
        }

        /* Architecture diagram */
        .about-architecture {
            background: #1a1a2e;
            border-radius: 12px;
            padding: 1.5rem;
            color: #ffffff;
            font-family: 'Courier New', monospace;
            font-size: 0.85rem;
            line-height: 2;
            overflow-x: auto;
            margin: 0.5rem 0;
        }
        .about-architecture .layer {
            color: #a29bfe;
            font-weight: 500;
        }
        .about-architecture .arrow {
            color: #6c5ce7;
        }
        .about-architecture .highlight {
            color: #fdcb6e;
        }
        .about-architecture .muted {
            color: rgba(255,255,255,0.3);
        }

        /* Tech tags */
        .tech-tag {
            display: inline-flex;
            align-items: center;
            gap: 0.4rem;
            background: #f8f9fa;
            padding: 0.3rem 0.8rem;
            border-radius: 8px;
            font-size: 0.8rem;
            color: #2d3436;
            border: 1px solid #e9ecef;
            margin: 0.2rem;
            transition: all 0.2s ease;
        }
        .tech-tag:hover {
            background: #e9ecef;
            transform: translateY(-1px);
        }
        .tech-tag .icon-svg {
            width: 16px;
            height: 16px;
            fill: #6c5ce7;
            flex-shrink: 0;
        }

        /* Feature list */
        .feature-list {
            display: grid;
            grid-template-columns: 1fr 1fr;
            gap: 0.75rem;
            margin: 0.5rem 0;
        }
        .feature-item {
            display: flex;
            align-items: center;
            gap: 0.5rem;
            color: #2d3436;
            font-size: 0.9rem;
            padding: 0.3rem 0;
        }
        .feature-item .check-svg {
            width: 18px;
            height: 18px;
            fill: #00b894;
            flex-shrink: 0;
        }

        /* Responsive */
        @media (max-width: 768px) {
            .about-grid-2, .about-grid-3 {
                grid-template-columns: 1fr;
            }
            .about-hero {
                padding: 2rem 1.5rem;
            }
            .about-hero-title {
                font-size: 1.8rem;
            }
            .feature-list {
                grid-template-columns: 1fr;
            }
            .about-hero-meta {
                gap: 1rem;
            }
        }
    </style>
    """,
        unsafe_allow_html=True,
    )

    # Hero Section with SVG icons
    st.markdown(
        f"""
    <div class="about-container">
        <div class="about-hero">
            <div class="about-hero-content">
                <div class="about-hero-badge">
                    <span class="about-hero-badge-dot"></span>
                    Production Ready
                </div>
                <div class="about-hero-title">About Job Market Intelligence</div>
                <div class="about-hero-subtitle">
                    A production-grade data engineering and analytics platform for technology job market insights
                </div>
                <div class="about-hero-meta">
                    <div class="about-hero-meta-item">
                        <svg class="icon-svg" viewBox="0 0 24 24"><path d="M12 2C6.48 2 2 6.48 2 12s4.48 10 10 10 10-4.48 10-10S17.52 2 12 2zm-1 17.93c-3.95-.49-7-3.85-7-7.93 0-.62.08-1.21.21-1.79L9 15v1c0 1.1.9 2 2 2v1.93zm6.9-2.54c-.26-.81-1-1.39-1.9-1.39h-1v-3c0-.55-.45-1-1-1H8v-2h2c.55 0 1-.45 1-1V7h2c1.1 0 2-.9 2-2v-.41c2.93 1.19 5 4.06 5 7.41 0 2.08-.8 3.97-2.1 5.39z"/></svg>
                        <strong>Version</strong> 1.0.0
                    </div>
                    <div class="about-hero-meta-item">
                        <svg class="icon-svg" viewBox="0 0 24 24"><path d="M12 2C6.48 2 2 6.48 2 12s4.48 10 10 10 10-4.48 10-10S17.52 2 12 2zm-2 15l-5-5 1.41-1.41L10 14.17l7.59-7.59L19 8l-9 9z"/></svg>
                        <strong>Status</strong> Deployment Ready
                    </div>
                    <div class="about-hero-meta-item">
                        <svg class="icon-svg" viewBox="0 0 24 24"><path d="M19 3h-1V1h-2v2H8V1H6v2H5c-1.11 0-1.99.9-1.99 2L3 19c0 1.1.89 2 2 2h14c1.1 0 2-.9 2-2V5c0-1.1-.9-2-2-2zm0 16H5V8h14v11z"/></svg>
                        <strong>Released</strong> {datetime.now().strftime("%B %Y")}
                    </div>
                    <div class="about-hero-meta-item">
                        <svg class="icon-svg" viewBox="0 0 24 24"><path d="M14 2H6c-1.1 0-1.99.9-1.99 2L4 20c0 1.1.89 2 1.99 2H18c1.1 0 2-.9 2-2V8l-6-6zm2 16H8v-2h8v2zm0-4H8v-2h8v2zm-3-5V3.5L18.5 9H13z"/></svg>
                        <strong>API</strong> REST • FastAPI
                    </div>
                </div>
            </div>
        </div>
    </div>
    """,
        unsafe_allow_html=True,
    )

    # Quick Stats with SVG icons
    st.markdown(
        """
    <div class="about-grid-3">
        <div class="stat-card">
            <svg class="icon-svg" viewBox="0 0 24 24"><path d="M19 3H5c-1.1 0-2 .9-2 2v14c0 1.1.9 2 2 2h14c1.1 0 2-.9 2-2V5c0-1.1-.9-2-2-2zm-7 3c1.93 0 3.5 1.57 3.5 3.5S13.93 13 12 13s-3.5-1.57-3.5-3.5S10.07 6 12 6zm7 13H5v-.23c0-.62.28-1.2.76-1.58C7.47 15.82 9.64 15 12 15s4.53.82 6.24 2.19c.48.38.76.97.76 1.58V19z"/></svg>
            <div class="stat-card-value">4</div>
            <div class="stat-card-label">Dashboard Pages</div>
        </div>
        <div class="stat-card">
            <svg class="icon-svg" viewBox="0 0 24 24"><path d="M4 8h4V4H4v4zm6 12h4v-4h-4v4zm-6 0h4v-4H4v4zm0-6h4v-4H4v4zm6 0h4v-4h-4v4zm6-10v4h4V4h-4zm-6 4h4V4h-4v4zm6 6h4v-4h-4v4zm0 6h4v-4h-4v4z"/></svg>
            <div class="stat-card-value">15+</div>
            <div class="stat-card-label">API Endpoints</div>
        </div>
        <div class="stat-card">
            <svg class="icon-svg" viewBox="0 0 24 24"><path d="M19 3H5c-1.1 0-2 .9-2 2v14c0 1.1.9 2 2 2h14c1.1 0 2-.9 2-2V5c0-1.1-.9-2-2-2zm-7 3c1.93 0 3.5 1.57 3.5 3.5S13.93 13 12 13s-3.5-1.57-3.5-3.5S10.07 6 12 6zm7 13H5v-.23c0-.62.28-1.2.76-1.58C7.47 15.82 9.64 15 12 15s4.53.82 6.24 2.19c.48.38.76.97.76 1.58V19z"/></svg>
            <div class="stat-card-value">10+</div>
            <div class="stat-card-label">Analytics Metrics</div>
        </div>
    </div>
    """,
        unsafe_allow_html=True,
    )

    # Architecture Section
    st.markdown(
        """
    <div class="about-card">
        <div class="about-card-title">
            <svg class="icon-svg" viewBox="0 0 24 24"><path d="M12 2C6.48 2 2 6.48 2 12s4.48 10 10 10 10-4.48 10-10S17.52 2 12 2zm-1 17.93c-3.95-.49-7-3.85-7-7.93 0-.62.08-1.21.21-1.79L9 15v1c0 1.1.9 2 2 2v1.93zm6.9-2.54c-.26-.81-1-1.39-1.9-1.39h-1v-3c0-.55-.45-1-1-1H8v-2h2c.55 0 1-.45 1-1V7h2c1.1 0 2-.9 2-2v-.41c2.93 1.19 5 4.06 5 7.41 0 2.08-.8 3.97-2.1 5.39z"/></svg>
            Architecture
        </div>
        <div class="about-card-content">
            <p style="color: #636e72; font-size: 0.95rem; margin-bottom: 1rem;">
                Clean layered architecture with clear separation of concerns
            </p>
            <div class="about-architecture">
                <span class="muted">┌─────────────────────────────────────────────────────┐</span><br>
                <span class="muted">│</span>  <span class="layer">Dashboard</span>     ← UI Layer (Streamlit)                <span class="muted">│</span><br>
                <span class="muted">│</span>       <span class="arrow">↓</span>                                          <span class="muted">│</span><br>
                <span class="muted">│</span>  <span class="layer">Services</span>      ← Business Logic                    <span class="muted">│</span><br>
                <span class="muted">│</span>       <span class="arrow">↓</span>                                          <span class="muted">│</span><br>
                <span class="muted">│</span>  <span class="layer">API Client</span>    ← HTTP Transport                    <span class="muted">│</span><br>
                <span class="muted">│</span>       <span class="arrow">↓</span>                                          <span class="muted">│</span><br>
                <span class="muted">│</span>  <span class="layer">FastAPI</span>       ← Backend REST API                  <span class="muted">│</span><br>
                <span class="muted">│</span>       <span class="arrow">↓</span>                                          <span class="muted">│</span><br>
                <span class="muted">│</span>  <span class="layer">PostgreSQL</span>    ← Database                         <span class="muted">│</span><br>
                <span class="muted">└─────────────────────────────────────────────────────┘</span>
            </div>
        </div>
    </div>
    """,
        unsafe_allow_html=True,
    )

    # Two column layout: Features + Tech Stack
    col1, col2 = st.columns(2)

    with col1:
        st.markdown(
            """
        <div class="about-card" style="height: 100%;">
            <div class="about-card-title">
                <svg class="icon-svg" viewBox="0 0 24 24"><path d="M12 2C6.48 2 2 6.48 2 12s4.48 10 10 10 10-4.48 10-10S17.52 2 12 2zm-2 15l-5-5 1.41-1.41L10 14.17l7.59-7.59L19 8l-9 9z"/></svg>
                Key Features
            </div>
            <div class="about-card-content">
                <div class="feature-list">
                    <div class="feature-item">
                        <svg class="check-svg" viewBox="0 0 24 24"><path d="M12 2C6.48 2 2 6.48 2 12s4.48 10 10 10 10-4.48 10-10S17.52 2 12 2zm-2 15l-5-5 1.41-1.41L10 14.17l7.59-7.59L19 8l-9 9z"/></svg>
                        ETL Pipeline
                    </div>
                    <div class="feature-item">
                        <svg class="check-svg" viewBox="0 0 24 24"><path d="M12 2C6.48 2 2 6.48 2 12s4.48 10 10 10 10-4.48 10-10S17.52 2 12 2zm-2 15l-5-5 1.41-1.41L10 14.17l7.59-7.59L19 8l-9 9z"/></svg>
                        Analytics Engine
                    </div>
                    <div class="feature-item">
                        <svg class="check-svg" viewBox="0 0 24 24"><path d="M12 2C6.48 2 2 6.48 2 12s4.48 10 10 10 10-4.48 10-10S17.52 2 12 2zm-2 15l-5-5 1.41-1.41L10 14.17l7.59-7.59L19 8l-9 9z"/></svg>
                        REST API
                    </div>
                    <div class="feature-item">
                        <svg class="check-svg" viewBox="0 0 24 24"><path d="M12 2C6.48 2 2 6.48 2 12s4.48 10 10 10 10-4.48 10-10S17.52 2 12 2zm-2 15l-5-5 1.41-1.41L10 14.17l7.59-7.59L19 8l-9 9z"/></svg>
                        Interactive Dashboard
                    </div>
                    <div class="feature-item">
                        <svg class="check-svg" viewBox="0 0 24 24"><path d="M12 2C6.48 2 2 6.48 2 12s4.48 10 10 10 10-4.48 10-10S17.52 2 12 2zm-2 15l-5-5 1.41-1.41L10 14.17l7.59-7.59L19 8l-9 9z"/></svg>
                        Job Explorer
                    </div>
                    <div class="feature-item">
                        <svg class="check-svg" viewBox="0 0 24 24"><path d="M12 2C6.48 2 2 6.48 2 12s4.48 10 10 10 10-4.48 10-10S17.52 2 12 2zm-2 15l-5-5 1.41-1.41L10 14.17l7.59-7.59L19 8l-9 9z"/></svg>
                        Salary Analytics
                    </div>
                    <div class="feature-item">
                        <svg class="check-svg" viewBox="0 0 24 24"><path d="M12 2C6.48 2 2 6.48 2 12s4.48 10 10 10 10-4.48 10-10S17.52 2 12 2zm-2 15l-5-5 1.41-1.41L10 14.17l7.59-7.59L19 8l-9 9z"/></svg>
                        Skill Demand Analysis
                    </div>
                    <div class="feature-item">
                        <svg class="check-svg" viewBox="0 0 24 24"><path d="M12 2C6.48 2 2 6.48 2 12s4.48 10 10 10 10-4.48 10-10S17.52 2 12 2zm-2 15l-5-5 1.41-1.41L10 14.17l7.59-7.59L19 8l-9 9z"/></svg>
                        Trend Visualization
                    </div>
                </div>
            </div>
        </div>
        """,
            unsafe_allow_html=True,
        )

    with col2:
        st.markdown(
            """
        <div class="about-card" style="height: 100%;">
            <div class="about-card-title">
                <svg class="icon-svg" viewBox="0 0 24 24"><path d="M12 2C6.48 2 2 6.48 2 12s4.48 10 10 10 10-4.48 10-10S17.52 2 12 2zm-1 17.93c-3.95-.49-7-3.85-7-7.93 0-.62.08-1.21.21-1.79L9 15v1c0 1.1.9 2 2 2v1.93zm6.9-2.54c-.26-.81-1-1.39-1.9-1.39h-1v-3c0-.55-.45-1-1-1H8v-2h2c.55 0 1-.45 1-1V7h2c1.1 0 2-.9 2-2v-.41c2.93 1.19 5 4.06 5 7.41 0 2.08-.8 3.97-2.1 5.39z"/></svg>
                Technology Stack
            </div>
            <div class="about-card-content">
                <div style="display: flex; flex-wrap: wrap; gap: 0.4rem; margin-bottom: 0.75rem;">
                    <span class="tech-tag">
                        <svg class="icon-svg" viewBox="0 0 24 24"><path d="M12 2C6.48 2 2 6.48 2 12s4.48 10 10 10 10-4.48 10-10S17.52 2 12 2zm-1 17.93c-3.95-.49-7-3.85-7-7.93 0-.62.08-1.21.21-1.79L9 15v1c0 1.1.9 2 2 2v1.93zm6.9-2.54c-.26-.81-1-1.39-1.9-1.39h-1v-3c0-.55-.45-1-1-1H8v-2h2c.55 0 1-.45 1-1V7h2c1.1 0 2-.9 2-2v-.41c2.93 1.19 5 4.06 5 7.41 0 2.08-.8 3.97-2.1 5.39z"/></svg>
                        Python 3.13
                    </span>
                    <span class="tech-tag">
                        <svg class="icon-svg" viewBox="0 0 24 24"><path d="M19 3H5c-1.1 0-2 .9-2 2v14c0 1.1.9 2 2 2h14c1.1 0 2-.9 2-2V5c0-1.1-.9-2-2-2zM9 17H7v-7h2v7zm4 0h-2V7h2v10zm4 0h-2v-4h2v4z"/></svg>
                        Streamlit
                    </span>
                    <span class="tech-tag">
                        <svg class="icon-svg" viewBox="0 0 24 24"><path d="M19 3H5c-1.1 0-2 .9-2 2v14c0 1.1.9 2 2 2h14c1.1 0 2-.9 2-2V5c0-1.1-.9-2-2-2zM9 17H7v-7h2v7zm4 0h-2V7h2v10zm4 0h-2v-4h2v4z"/></svg>
                        Plotly
                    </span>
                    <span class="tech-tag">
                        <svg class="icon-svg" viewBox="0 0 24 24"><path d="M14 2H6c-1.1 0-1.99.9-1.99 2L4 20c0 1.1.89 2 1.99 2H18c1.1 0 2-.9 2-2V8l-6-6zm2 16H8v-2h8v2zm0-4H8v-2h8v2zm-3-5V3.5L18.5 9H13z"/></svg>
                        FastAPI
                    </span>
                    <span class="tech-tag">
                        <svg class="icon-svg" viewBox="0 0 24 24"><path d="M12 2C6.48 2 2 6.48 2 12s4.48 10 10 10 10-4.48 10-10S17.52 2 12 2zm-1 17.93c-3.95-.49-7-3.85-7-7.93 0-.62.08-1.21.21-1.79L9 15v1c0 1.1.9 2 2 2v1.93zm6.9-2.54c-.26-.81-1-1.39-1.9-1.39h-1v-3c0-.55-.45-1-1-1H8v-2h2c.55 0 1-.45 1-1V7h2c1.1 0 2-.9 2-2v-.41c2.93 1.19 5 4.06 5 7.41 0 2.08-.8 3.97-2.1 5.39z"/></svg>
                        PostgreSQL
                    </span>
                    <span class="tech-tag">
                        <svg class="icon-svg" viewBox="0 0 24 24"><path d="M12 2C6.48 2 2 6.48 2 12s4.48 10 10 10 10-4.48 10-10S17.52 2 12 2zm-1 17.93c-3.95-.49-7-3.85-7-7.93 0-.62.08-1.21.21-1.79L9 15v1c0 1.1.9 2 2 2v1.93zm6.9-2.54c-.26-.81-1-1.39-1.9-1.39h-1v-3c0-.55-.45-1-1-1H8v-2h2c.55 0 1-.45 1-1V7h2c1.1 0 2-.9 2-2v-.41c2.93 1.19 5 4.06 5 7.41 0 2.08-.8 3.97-2.1 5.39z"/></svg>
                        Pydantic v2
                    </span>
                    <span class="tech-tag">
                        <svg class="icon-svg" viewBox="0 0 24 24"><path d="M12 2C6.48 2 2 6.48 2 12s4.48 10 10 10 10-4.48 10-10S17.52 2 12 2zm-1 17.93c-3.95-.49-7-3.85-7-7.93 0-.62.08-1.21.21-1.79L9 15v1c0 1.1.9 2 2 2v1.93zm6.9-2.54c-.26-.81-1-1.39-1.9-1.39h-1v-3c0-.55-.45-1-1-1H8v-2h2c.55 0 1-.45 1-1V7h2c1.1 0 2-.9 2-2v-.41c2.93 1.19 5 4.06 5 7.41 0 2.08-.8 3.97-2.1 5.39z"/></svg>
                        SQLAlchemy
                    </span>
                    <span class="tech-tag">
                        <svg class="icon-svg" viewBox="0 0 24 24"><path d="M19 3H5c-1.1 0-2 .9-2 2v14c0 1.1.9 2 2 2h14c1.1 0 2-.9 2-2V5c0-1.1-.9-2-2-2zM9 17H7v-7h2v7zm4 0h-2V7h2v10zm4 0h-2v-4h2v4z"/></svg>
                        Pandas
                    </span>
                </div>
                <div style="color: #636e72; font-size: 0.85rem; margin-top: 0.5rem; border-top: 1px solid #e9ecef; padding-top: 0.75rem;">
                    <strong>Frontend:</strong> Streamlit • Plotly<br>
                    <strong>Backend:</strong> FastAPI • SQLAlchemy<br>
                    <strong>Database:</strong> PostgreSQL
                </div>
            </div>
        </div>
        """,
            unsafe_allow_html=True,
        )

    # Principles Section
    st.markdown(
        """
    <div class="about-card">
        <div class="about-card-title">
            <svg class="icon-svg" viewBox="0 0 24 24"><path d="M12 2C6.48 2 2 6.48 2 12s4.48 10 10 10 10-4.48 10-10S17.52 2 12 2zm-1 17.93c-3.95-.49-7-3.85-7-7.93 0-.62.08-1.21.21-1.79L9 15v1c0 1.1.9 2 2 2v1.93zm6.9-2.54c-.26-.81-1-1.39-1.9-1.39h-1v-3c0-.55-.45-1-1-1H8v-2h2c.55 0 1-.45 1-1V7h2c1.1 0 2-.9 2-2v-.41c2.93 1.19 5 4.06 5 7.41 0 2.08-.8 3.97-2.1 5.39z"/></svg>
            Design Principles
        </div>
        <div class="about-card-content">
            <div class="about-grid-2" style="margin-bottom: 0;">
                <div style="padding: 0.5rem;">
                    <strong style="color: #1a1a2e;">🔹 Separation of Concerns</strong>
                    <p style="color: #636e72; font-size: 0.9rem; margin-top: 0.25rem;">Each layer has a single, well-defined responsibility</p>
                </div>
                <div style="padding: 0.5rem;">
                    <strong style="color: #1a1a2e;">🔹 API-First Communication</strong>
                    <p style="color: #636e72; font-size: 0.9rem; margin-top: 0.25rem;">Frontend communicates exclusively through REST APIs</p>
                </div>
                <div style="padding: 0.5rem;">
                    <strong style="color: #1a1a2e;">🔹 Reusable Components</strong>
                    <p style="color: #636e72; font-size: 0.9rem; margin-top: 0.25rem;">DRY, composable UI elements and services</p>
                </div>
                <div style="padding: 0.5rem;">
                    <strong style="color: #1a1a2e;">🔹 Production Ready</strong>
                    <p style="color: #636e72; font-size: 0.9rem; margin-top: 0.25rem;">Built with deployment, testing, and monitoring in mind</p>
                </div>
            </div>
        </div>
    </div>
    """,
        unsafe_allow_html=True,
    )

    # Footer with SVG
    st.markdown(
        """
    <div style="text-align: center; padding: 1rem 0 0.5rem 0; color: #636e72; font-size: 0.85rem; border-top: 1px solid #e9ecef; margin-top: 1rem;">
        <div style="display: flex; justify-content: center; gap: 1.5rem; flex-wrap: wrap; align-items: center;">
            <span style="display: flex; align-items: center; gap: 0.3rem;">
                <svg width="16" height="16" viewBox="0 0 24 24" fill="#636e72"><path d="M19 3H5c-1.1 0-2 .9-2 2v14c0 1.1.9 2 2 2h14c1.1 0 2-.9 2-2V5c0-1.1-.9-2-2-2zm-7 3c1.93 0 3.5 1.57 3.5 3.5S13.93 13 12 13s-3.5-1.57-3.5-3.5S10.07 6 12 6zm7 13H5v-.23c0-.62.28-1.2.76-1.58C7.47 15.82 9.64 15 12 15s4.53.82 6.24 2.19c.48.38.76.97.76 1.58V19z"/></svg>
                Job Market Intelligence
            </span>
            <span>•</span>
            <span style="display: flex; align-items: center; gap: 0.3rem;">
                <svg width="16" height="16" viewBox="0 0 24 24" fill="#636e72"><path d="M12 21.35l-1.45-1.32C5.4 15.36 2 12.28 2 8.5 2 5.42 4.42 3 7.5 3c1.74 0 3.41.81 4.5 2.09C13.09 3.81 14.76 3 16.5 3 19.58 3 22 5.42 22 8.5c0 3.78-3.4 6.86-8.55 11.54L12 21.35z"/></svg>
                Built with ❤️ using Streamlit
            </span>
            <span>•</span>
            <span>📅 {}</span>
        </div>
    </div>
    """.format(datetime.now().strftime("%Y")),
        unsafe_allow_html=True,
    )
