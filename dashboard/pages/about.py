# dashboard/pages/about.py
import streamlit as st
from datetime import datetime

from core.config import settings


def render():
    """Render the professional About page."""
    
    # Custom CSS for About page
    st.markdown("""
    <style>
        .about-header {
            margin-bottom: 2rem;
        }
        .about-title {
            font-size: 2rem;
            font-weight: 700;
            color: #1a1a2e;
            letter-spacing: -0.02em;
        }
        .about-subtitle {
            font-size: 1rem;
            color: #636e72;
            font-weight: 400;
            margin-top: 0.25rem;
        }
        .about-card {
            background: #ffffff;
            border-radius: 12px;
            padding: 1.5rem;
            border: 1px solid #e9ecef;
            box-shadow: 0 1px 3px rgba(0,0,0,0.04);
            margin: 1.5rem 0;
        }
        .about-card-title {
            font-size: 1.1rem;
            font-weight: 600;
            color: #1a1a2e;
            margin-bottom: 0.75rem;
        }
        .about-card-content {
            color: #2d3436;
            line-height: 1.6;
        }
        .about-badge {
            display: inline-block;
            background: #f8f9fa;
            padding: 0.25rem 0.75rem;
            border-radius: 20px;
            font-size: 0.75rem;
            color: #636e72;
            border: 1px solid #e9ecef;
        }
        .about-grid {
            display: grid;
            grid-template-columns: 1fr 1fr;
            gap: 1rem;
            margin: 1rem 0;
        }
        .about-grid-item {
            background: #f8f9fa;
            padding: 1rem;
            border-radius: 8px;
            border: 1px solid #e9ecef;
        }
        .about-grid-item-label {
            font-size: 0.75rem;
            color: #636e72;
            text-transform: uppercase;
            letter-spacing: 0.04em;
            font-weight: 600;
        }
        .about-grid-item-value {
            font-size: 1rem;
            font-weight: 500;
            color: #1a1a2e;
            margin-top: 0.25rem;
        }
        .about-architecture {
            background: #1a1a2e;
            border-radius: 10px;
            padding: 1.5rem;
            color: #ffffff;
            font-family: 'Courier New', monospace;
            font-size: 0.85rem;
            line-height: 1.8;
            margin: 1rem 0;
            overflow-x: auto;
        }
        .about-architecture .arrow {
            color: #6c5ce7;
        }
        .about-architecture .highlight {
            color: #fdcb6e;
        }
        .about-divider {
            border: none;
            height: 1px;
            background: #e9ecef;
            margin: 1.5rem 0;
        }
        .about-footer {
            text-align: center;
            color: #636e72;
            font-size: 0.85rem;
            padding: 0.5rem 0 0 0;
        }
        .about-status-badge {
            display: inline-flex;
            align-items: center;
            gap: 0.5rem;
            background: #00b89410;
            padding: 0.25rem 0.75rem;
            border-radius: 20px;
            font-size: 0.8rem;
            color: #00b894;
            border: 1px solid #00b89430;
        }
        .about-status-dot {
            width: 6px;
            height: 6px;
            border-radius: 50%;
            background: #00b894;
            display: inline-block;
            animation: pulse 2s infinite;
        }
        @keyframes pulse {
            0% { opacity: 1; }
            50% { opacity: 0.4; }
            100% { opacity: 1; }
        }
        .about-tech-tag {
            display: inline-block;
            background: #f8f9fa;
            padding: 0.2rem 0.6rem;
            border-radius: 4px;
            font-size: 0.75rem;
            color: #2d3436;
            border: 1px solid #e9ecef;
            margin: 0.2rem;
        }
    </style>
    """, unsafe_allow_html=True)
    
    # Header
    st.markdown(f"""
    <div class="about-header">
        <div class="about-title">ℹ️ About</div>
        <div class="about-subtitle">Job Market Intelligence Platform</div>
    </div>
    """, unsafe_allow_html=True)
    
    # Status Badge
    st.markdown("""
    <div style="margin-bottom: 1rem;">
        <span class="about-status-badge">
            <span class="about-status-dot"></span>
            Sprint 5.3 • Production Ready
        </span>
        <span class="about-badge" style="margin-left: 0.5rem;">v1.0.0</span>
    </div>
    """, unsafe_allow_html=True)
    
    # Quick Info Grid
    st.markdown("""
    <div class="about-grid">
        <div class="about-grid-item">
            <div class="about-grid-item-label">📦 Version</div>
            <div class="about-grid-item-value">Sprint 5.3</div>
        </div>
        <div class="about-grid-item">
            <div class="about-grid-item-label">🏗️ Status</div>
            <div class="about-grid-item-value">Production Ready</div>
        </div>
        <div class="about-grid-item">
            <div class="about-grid-item-label">📅 Released</div>
            <div class="about-grid-item-value">July 2026</div>
        </div>
        <div class="about-grid-item">
            <div class="about-grid-item-label">🔌 API</div>
            <div class="about-grid-item-value">REST • FastAPI</div>
        </div>
    </div>
    """, unsafe_allow_html=True)
    
    # Architecture Section
    st.markdown("""
    <div class="about-card">
        <div class="about-card-title">🏛️ Architecture</div>
        <div class="about-card-content">
            <p style="color: #636e72; font-size: 0.9rem; margin-bottom: 1rem;">
                Clean layered architecture with clear separation of concerns
            </p>
            <div class="about-architecture">
                <span style="color: #6c5ce7;">┌─────────────────────────────────────────────┐</span><br>
                <span style="color: #6c5ce7;">│</span>  <span class="highlight">Pages</span>        ← UI Layer (Streamlit)          <span style="color: #6c5ce7;">│</span><br>
                <span style="color: #6c5ce7;">│</span>       <span class="arrow">↓</span>                                    <span style="color: #6c5ce7;">│</span><br>
                <span style="color: #6c5ce7;">│</span>  <span class="highlight">Services</span>     ← Business Logic               <span style="color: #6c5ce7;">│</span><br>
                <span style="color: #6c5ce7;">│</span>       <span class="arrow">↓</span>                                    <span style="color: #6c5ce7;">│</span><br>
                <span style="color: #6c5ce7;">│</span>  <span class="highlight">Mappers</span>      ← Presentation Transformation  <span style="color: #6c5ce7;">│</span><br>
                <span style="color: #6c5ce7;">│</span>       <span class="arrow">↓</span>                                    <span style="color: #6c5ce7;">│</span><br>
                <span style="color: #6c5ce7;">│</span>  <span class="highlight">API Client</span>   ← HTTP Transport               <span style="color: #6c5ce7;">│</span><br>
                <span style="color: #6c5ce7;">│</span>       <span class="arrow">↓</span>                                    <span style="color: #6c5ce7;">│</span><br>
                <span style="color: #6c5ce7;">│</span>  <span class="highlight">FastAPI</span>      ← Backend REST API             <span style="color: #6c5ce7;">│</span><br>
                <span style="color: #6c5ce7;">└─────────────────────────────────────────────┘</span>
            </div>
        </div>
    </div>
    """, unsafe_allow_html=True)
    
    # Principles Section
    st.markdown("""
    <div class="about-card">
        <div class="about-card-title">📐 Principles</div>
        <div class="about-card-content">
            <ul style="margin: 0; padding-left: 1.25rem; color: #2d3436;">
                <li>🔹 <strong>Separation of concerns</strong> — Each layer has a single responsibility</li>
                <li>🔹 <strong>Reusable components</strong> — DRY, composable UI elements</li>
                <li>🔹 <strong>API-only communication</strong> — Frontend never talks directly to database</li>
                <li>🔹 <strong>Modular structure</strong> — Easy to extend and maintain</li>
                <li>🔹 <strong>Independent frontend</strong> — Works with any backend that implements the API contract</li>
            </ul>
        </div>
    </div>
    """, unsafe_allow_html=True)
    
    # Tech Stack
    st.markdown("""
    <div class="about-card">
        <div class="about-card-title">⚡ Technology Stack</div>
        <div class="about-card-content">
            <div style="display: flex; flex-wrap: wrap; gap: 0.5rem; margin-bottom: 0.5rem;">
                <span class="about-tech-tag">🐍 Python 3.13</span>
                <span class="about-tech-tag">📊 Streamlit 1.28+</span>
                <span class="about-tech-tag">📈 Plotly 5.17+</span>
                <span class="about-tech-tag">🚀 FastAPI</span>
                <span class="about-tech-tag">🐘 PostgreSQL</span>
                <span class="about-tech-tag">📦 Pydantic 2.0+</span>
                <span class="about-tech-tag">🔧 REST API</span>
                <span class="about-tech-tag">💾 SQLAlchemy</span>
            </div>
            <div style="color: #636e72; font-size: 0.85rem; margin-top: 0.5rem;">
                <span>Frontend: Streamlit • </span>
                <span>Visualization: Plotly • </span>
                <span>Backend: FastAPI • </span>
                <span>Database: PostgreSQL</span>
            </div>
        </div>
    </div>
    """, unsafe_allow_html=True)
    
    # Removed the footer section since app.py already has a global footer