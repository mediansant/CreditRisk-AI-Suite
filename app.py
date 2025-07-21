#!/usr/bin/env python3
"""
CreditRisk AI Suite
Multi-page application for credit risk analysis with CrewAI integration
"""

import streamlit as st
import sys
import os
from datetime import datetime, timedelta
import json
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from typing import Dict, Any, Optional

# Add agents directory to path for imports
sys.path.append('agents')

# Configure page
st.set_page_config(
    page_title="CreditRisk AI Suite",
    page_icon="🏦",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS for styling
st.markdown("""
<style>
    /* Global Styles */
    .main {
        padding: 2rem 1rem;
    }
    
    .stApp {
        background: linear-gradient(135deg, #f5f7fa 0%, #c3cfe2 100%);
        min-height: 100vh;
    }
    
    .main .block-container {
        background: rgba(255, 255, 255, 0.98);
        border-radius: 15px;
        box-shadow: 0 8px 32px rgba(0, 0, 0, 0.08);
        backdrop-filter: blur(10px);
        border: 1px solid rgba(255, 255, 255, 0.3);
        padding: 2rem;
        margin-top: 1rem;
        margin-bottom: 1rem;
    }
    
    /* Typography */
    .main-header {
        font-size: 3rem;
        font-weight: 800;
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        background-clip: text;
        text-align: center;
        margin-bottom: 2rem;
        text-shadow: 2px 2px 4px rgba(0, 0, 0, 0.1);
        animation: fadeInUp 0.8s ease-out;
    }
    
    .sub-header {
        font-size: 1.8rem;
        font-weight: 700;
        color: #1a202c;
        margin-bottom: 1.5rem;
        border-left: 4px solid #3182ce;
        padding-left: 1rem;
        animation: slideInLeft 0.6s ease-out;
        text-shadow: 1px 1px 2px rgba(0, 0, 0, 0.05);
    }
    
    .section-header {
        font-size: 1.4rem;
        font-weight: 600;
        color: #2d3748;
        margin-bottom: 1rem;
        display: flex;
        align-items: center;
        gap: 0.5rem;
    }
    
    /* Cards and Containers */
    .metric-card {
        background: linear-gradient(135deg, #ffffff 0%, #f7fafc 100%);
        padding: 1.5rem;
        border-radius: 12px;
        border: 1px solid rgba(49, 130, 206, 0.15);
        box-shadow: 0 4px 15px rgba(0, 0, 0, 0.06);
        margin-bottom: 1rem;
        transition: all 0.3s ease;
        position: relative;
        overflow: hidden;
    }
    
    .metric-card::before {
        content: '';
        position: absolute;
        top: 0;
        left: 0;
        width: 4px;
        height: 100%;
        background: linear-gradient(135deg, #3182ce 0%, #2b6cb0 100%);
        transition: width 0.3s ease;
    }
    
    .metric-card:hover {
        transform: translateY(-2px);
        box-shadow: 0 8px 25px rgba(0, 0, 0, 0.12);
    }
    
    .metric-card:hover::before {
        width: 8px;
    }
    
    .success-metric {
        border-left-color: #28a745;
        background: linear-gradient(135deg, #d4edda 0%, #c3e6cb 100%);
    }
    
    .warning-metric {
        border-left-color: #ffc107;
        background: linear-gradient(135deg, #fff3cd 0%, #ffeaa7 100%);
    }
    
    .error-metric {
        border-left-color: #dc3545;
        background: linear-gradient(135deg, #f8d7da 0%, #f5c6cb 100%);
    }
    
    .info-card {
        background: linear-gradient(135deg, #e3f2fd 0%, #bbdefb 100%);
        border: 1px solid rgba(33, 150, 243, 0.2);
        border-radius: 12px;
        padding: 1.5rem;
        margin-bottom: 1rem;
        box-shadow: 0 4px 15px rgba(33, 150, 243, 0.1);
    }
    
    /* Sidebar Styling */
    .css-1d391kg {
        background: linear-gradient(180deg, #2c3e50 0%, #34495e 100%);
    }
    
    .sidebar .sidebar-content {
        background: linear-gradient(180deg, #2c3e50 0%, #34495e 100%);
        color: white;
    }
    
    /* Buttons */
    .stButton > button {
        width: 100%;
        margin-bottom: 0.5rem;
        background: linear-gradient(135deg, #3182ce 0%, #2b6cb0 100%);
        color: white;
        border: none;
        border-radius: 8px;
        padding: 0.75rem 1.5rem;
        font-weight: 600;
        transition: all 0.3s ease;
        box-shadow: 0 4px 15px rgba(49, 130, 206, 0.3);
    }
    
    .stButton > button:hover {
        transform: translateY(-2px);
        box-shadow: 0 8px 25px rgba(49, 130, 206, 0.4);
        background: linear-gradient(135deg, #2b6cb0 0%, #2c5282 100%);
    }
    
    .stButton > button:active {
        transform: translateY(0);
    }
    
    /* Form Styling for Better Readability */
    .stTextInput > div > div > input {
        background-color: #ffffff;
        border: 2px solid #e2e8f0;
        border-radius: 8px;
        color: #2d3748;
        font-weight: 500;
    }
    
    .stTextInput > div > div > input:focus {
        border-color: #3182ce;
        box-shadow: 0 0 0 3px rgba(49, 130, 206, 0.1);
    }
    
    .stNumberInput > div > div > input {
        background-color: #ffffff;
        border: 2px solid #e2e8f0;
        border-radius: 8px;
        color: #2d3748;
        font-weight: 500;
    }
    
    .stNumberInput > div > div > input:focus {
        border-color: #3182ce;
        box-shadow: 0 0 0 3px rgba(49, 130, 206, 0.1);
    }
    
    .stSelectbox > div > div > div {
        background-color: #ffffff;
        border: 2px solid #e2e8f0;
        border-radius: 8px;
        color: #2d3748;
        font-weight: 500;
    }
    
    .stSelectbox > div > div > div:focus {
        border-color: #3182ce;
        box-shadow: 0 0 0 3px rgba(49, 130, 206, 0.1);
    }
    
    .stTextArea > div > div > textarea {
        background-color: #ffffff;
        border: 2px solid #e2e8f0;
        border-radius: 8px;
        color: #2d3748;
        font-weight: 500;
    }
    
    .stTextArea > div > div > textarea:focus {
        border-color: #3182ce;
        box-shadow: 0 0 0 3px rgba(49, 130, 206, 0.1);
    }
    
    /* Label Styling */
    .stTextInput > label, .stNumberInput > label, .stSelectbox > label, .stTextArea > label {
        color: #1a202c;
        font-weight: 600;
        font-size: 0.95rem;
        margin-bottom: 0.5rem;
    }
    
    /* Help Text Styling */
    .stTextInput > div > div > div > div, .stNumberInput > div > div > div > div, 
    .stSelectbox > div > div > div > div, .stTextArea > div > div > div > div {
        color: #4a5568;
        font-size: 0.85rem;
        font-style: italic;
    }
    
    /* Section Headers in Forms */
    h3 {
        color: #1a202c;
        font-weight: 700;
        font-size: 1.3rem;
        margin-top: 2rem;
        margin-bottom: 1rem;
        padding-bottom: 0.5rem;
        border-bottom: 2px solid #e2e8f0;
    }
    
    /* Metric Display */
    .stMetric > div > div > div {
        color: #1a202c;
        font-weight: 600;
    }
    
    .stMetric > div > div > div > div {
        color: #4a5568;
        font-weight: 500;
    }
    
    /* Ensure form text is visible */
    .stMarkdown {
        color: #1a202c !important;
        font-weight: 500;
    }
    
    .stMarkdown p {
        color: #2d3748 !important;
        font-weight: 400;
        line-height: 1.6;
    }
    
    .stMarkdown h3, .stMarkdown h4 {
        color: #1a202c !important;
        font-weight: 700;
        margin-top: 1.5rem;
        margin-bottom: 1rem;
    }
    
    /* Form container styling */
    .stForm {
        background: rgba(255, 255, 255, 0.95);
        border-radius: 12px;
        padding: 1.5rem;
        margin: 1rem 0;
        border: 1px solid rgba(49, 130, 206, 0.1);
    }
    
    /* Success, warning, error messages */
    .stAlert {
        border-radius: 8px;
        border: none;
        margin: 1rem 0;
        padding: 1rem;
    }
    
    .stAlert[data-baseweb="notification"] {
        background-color: rgba(255, 255, 255, 0.95);
        border: 1px solid rgba(49, 130, 206, 0.2);
    }
    
    /* Caption text visibility */
    .stCaption {
        color: #4a5568 !important;
        font-weight: 500;
        font-size: 0.9rem;
    }
    
    /* Expander styling */
    .streamlit-expanderHeader {
        background-color: rgba(255, 255, 255, 0.9);
        border: 1px solid rgba(49, 130, 206, 0.15);
        border-radius: 8px;
        color: #1a202c;
        font-weight: 600;
    }
    
    .streamlit-expanderContent {
        background-color: rgba(255, 255, 255, 0.95);
        border: 1px solid rgba(49, 130, 206, 0.1);
        border-radius: 8px;
        margin-top: 0.5rem;
        padding: 1rem;
    }
    
    /* Status Indicators */
    .status-indicator {
        display: inline-block;
        width: 12px;
        height: 12px;
        border-radius: 50%;
        margin-right: 8px;
        animation: pulse 2s infinite;
    }
    
    .status-online {
        background: linear-gradient(135deg, #28a745 0%, #20c997 100%);
        box-shadow: 0 0 10px rgba(40, 167, 69, 0.5);
    }
    
    .status-offline {
        background: linear-gradient(135deg, #dc3545 0%, #e74c3c 100%);
        box-shadow: 0 0 10px rgba(220, 53, 69, 0.5);
    }
    
    .status-warning {
        background: linear-gradient(135deg, #ffc107 0%, #ffb347 100%);
        box-shadow: 0 0 10px rgba(255, 193, 7, 0.5);
    }
    
    /* Loading States */
    .loading-container {
        display: flex;
        flex-direction: column;
        align-items: center;
        justify-content: center;
        padding: 2rem;
        background: rgba(255, 255, 255, 0.9);
        border-radius: 12px;
        box-shadow: 0 4px 15px rgba(0, 0, 0, 0.1);
    }
    
    .loading-spinner {
        width: 50px;
        height: 50px;
        border: 4px solid #f3f3f3;
        border-top: 4px solid #667eea;
        border-radius: 50%;
        animation: spin 1s linear infinite;
        margin-bottom: 1rem;
    }
    
    /* Progress Bars */
    .stProgress > div > div > div > div {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
    }
    
    /* Alerts and Messages */
    .stAlert {
        border-radius: 8px;
        border: none;
        box-shadow: 0 4px 15px rgba(0, 0, 0, 0.1);
    }
    
    /* Form Elements */
    .stTextInput > div > div > input {
        border-radius: 8px;
        border: 2px solid #e2e8f0;
        transition: all 0.3s ease;
        background-color: #ffffff;
        color: #2d3748;
        font-weight: 500;
    }
    
    .stTextInput > div > div > input:focus {
        border-color: #3182ce;
        box-shadow: 0 0 0 3px rgba(49, 130, 206, 0.1);
    }
    
    .stSelectbox > div > div > div {
        border-radius: 8px;
        border: 2px solid #e2e8f0;
        background-color: #ffffff;
        color: #2d3748;
        font-weight: 500;
    }
    
    .stSelectbox > div > div > div:focus {
        border-color: #3182ce;
        box-shadow: 0 0 0 3px rgba(49, 130, 206, 0.1);
    }
    
    .stNumberInput > div > div > input {
        border-radius: 8px;
        border: 2px solid #e2e8f0;
        background-color: #ffffff;
        color: #2d3748;
        font-weight: 500;
    }
    
    .stNumberInput > div > div > input:focus {
        border-color: #3182ce;
        box-shadow: 0 0 0 3px rgba(49, 130, 206, 0.1);
    }
    
    .stTextArea > div > div > textarea {
        border-radius: 8px;
        border: 2px solid #e2e8f0;
        background-color: #ffffff;
        color: #2d3748;
        font-weight: 500;
    }
    
    .stTextArea > div > div > textarea:focus {
        border-color: #3182ce;
        box-shadow: 0 0 0 3px rgba(49, 130, 206, 0.1);
    }
    
    /* Charts and Visualizations */
    .js-plotly-plot {
        border-radius: 12px;
        box-shadow: 0 4px 15px rgba(0, 0, 0, 0.1);
        overflow: hidden;
    }
    
    /* Animations */
    @keyframes fadeInUp {
        from {
            opacity: 0;
            transform: translateY(30px);
        }
        to {
            opacity: 1;
            transform: translateY(0);
        }
    }
    
    @keyframes slideInLeft {
        from {
            opacity: 0;
            transform: translateX(-30px);
        }
        to {
            opacity: 1;
            transform: translateX(0);
        }
    }
    
    @keyframes pulse {
        0% {
            transform: scale(1);
            opacity: 1;
        }
        50% {
            transform: scale(1.1);
            opacity: 0.7;
        }
        100% {
            transform: scale(1);
            opacity: 1;
        }
    }
    
    @keyframes spin {
        0% { transform: rotate(0deg); }
        100% { transform: rotate(360deg); }
    }
    
    /* Responsive Design */
    @media (max-width: 768px) {
        .main-header {
            font-size: 2rem;
        }
        
        .sub-header {
            font-size: 1.4rem;
        }
        
        .metric-card {
            padding: 1rem;
        }
    }
    
    /* Custom Scrollbar */
    ::-webkit-scrollbar {
        width: 8px;
    }
    
    ::-webkit-scrollbar-track {
        background: #f1f1f1;
        border-radius: 4px;
    }
    
    ::-webkit-scrollbar-thumb {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        border-radius: 4px;
    }
    
    ::-webkit-scrollbar-thumb:hover {
        background: linear-gradient(135deg, #5a6fd8 0%, #6a4190 100%);
    }
    
    /* Tooltips */
    .tooltip {
        position: relative;
        display: inline-block;
    }
    
    .tooltip .tooltiptext {
        visibility: hidden;
        width: 200px;
        background-color: #333;
        color: #fff;
        text-align: center;
        border-radius: 6px;
        padding: 5px;
        position: absolute;
        z-index: 1;
        bottom: 125%;
        left: 50%;
        margin-left: -100px;
        opacity: 0;
        transition: opacity 0.3s;
    }
    
    .tooltip:hover .tooltiptext {
        visibility: visible;
        opacity: 1;
    }
</style>
""", unsafe_allow_html=True)

def init_session_state():
    """Initialize session state variables"""
    if 'current_page' not in st.session_state:
        st.session_state.current_page = 'Home'
    
    if 'crew_initialized' not in st.session_state:
        st.session_state.crew_initialized = False
    
    if 'performance_monitor' not in st.session_state:
        st.session_state.performance_monitor = None
    
    if 'database_manager' not in st.session_state:
        st.session_state.database_manager = None
    
    if 'analysis_results' not in st.session_state:
        st.session_state.analysis_results = []
    
    if 'current_analysis' not in st.session_state:
        st.session_state.current_analysis = None
    
    if 'system_status' not in st.session_state:
        st.session_state.system_status = {
            'database': 'offline',
            'crew': 'offline',
            'monitor': 'offline'
        }
    
    # Error handling and validation states
    if 'error_messages' not in st.session_state:
        st.session_state.error_messages = []
    
    if 'success_messages' not in st.session_state:
        st.session_state.success_messages = []
    
    if 'loading_states' not in st.session_state:
        st.session_state.loading_states = {
            'system_init': False,
            'database_connection': False,
            'crew_initialization': False,
            'analysis_processing': False
        }
    
    if 'validation_errors' not in st.session_state:
        st.session_state.validation_errors = {}

def show_loading_state(state_key: str, message: str = "Loading..."):
    """Display a loading state with spinner and message"""
    if st.session_state.loading_states.get(state_key, False):
        with st.spinner(message):
            st.markdown(f"""
            <div class="loading-container">
                <div class="loading-spinner"></div>
                <p>{message}</p>
            </div>
            """, unsafe_allow_html=True)
            st.stop()

def show_error_message(message: str, error_type: str = "error"):
    """Display error messages with proper styling"""
    if error_type == "error":
        st.error(f"❌ {message}")
    elif error_type == "warning":
        st.warning(f"⚠️ {message}")
    elif error_type == "info":
        st.info(f"ℹ️ {message}")

def show_success_message(message: str):
    """Display success messages with proper styling"""
    st.success(f"✅ {message}")

def validate_system_requirements():
    """Validate system requirements and dependencies"""
    errors = []
    warnings = []
    
    try:
        import streamlit
        import pandas
        import plotly
        import numpy
    except ImportError as e:
        errors.append(f"Missing required dependency: {str(e)}")
    
    try:
        import crewai
    except ImportError:
        warnings.append("CrewAI not available - some features may be limited")
    
    try:
        import mysql.connector
    except ImportError:
        warnings.append("MySQL connector not available - database features may be limited")
    
    return errors, warnings

def initialize_system():
    """Initialize the credit risk analysis system with enhanced error handling"""
    st.session_state.loading_states['system_init'] = True
    
    try:
        # Validate system requirements
        errors, warnings = validate_system_requirements()
        
        if errors:
            for error in errors:
                show_error_message(error, "error")
            st.session_state.loading_states['system_init'] = False
            return False
        
        if warnings:
            for warning in warnings:
                show_error_message(warning, "warning")
        
        with st.spinner("Initializing system components..."):
            # Import here to avoid circular imports
            try:
                from agents.database_tools import DatabaseToolManager, create_database_config
                from agents.performance_monitor import PerformanceMonitor
            except ImportError as e:
                show_error_message(f"Failed to import required modules: {str(e)}", "error")
                st.session_state.loading_states['system_init'] = False
                return False
            
            # Initialize database manager
            if st.session_state.database_manager is None:
                st.session_state.loading_states['database_connection'] = True
                try:
                    db_config = create_database_config()
                    st.session_state.database_manager = DatabaseToolManager(db_config.__dict__)
                    st.session_state.system_status['database'] = 'online'
                    show_success_message("Database connection established successfully")
                except Exception as e:
                    show_error_message(f"Database initialization failed: {str(e)}", "error")
                    st.session_state.system_status['database'] = 'offline'
                finally:
                    st.session_state.loading_states['database_connection'] = False
            
            # Initialize performance monitor
            if st.session_state.performance_monitor is None:
                try:
                    st.session_state.performance_monitor = PerformanceMonitor(enable_system_monitoring=True)
                    st.session_state.performance_monitor.start_monitoring()
                    st.session_state.system_status['monitor'] = 'online'
                    show_success_message("Performance monitoring activated")
                except Exception as e:
                    show_error_message(f"Performance monitor initialization failed: {str(e)}", "warning")
                    st.session_state.system_status['monitor'] = 'offline'
            
            # Initialize crew (if needed)
            if not st.session_state.crew_initialized:
                st.session_state.loading_states['crew_initialization'] = True
                try:
                    from agents.credit_risk_crew import CreditRiskCrew
                    crew = CreditRiskCrew()
                    st.session_state.crew = crew
                    st.session_state.crew_initialized = True
                    st.session_state.system_status['crew'] = 'online'
                    show_success_message("CrewAI agents initialized successfully")
                except Exception as e:
                    st.session_state.system_status['crew'] = 'warning'
                    show_error_message(f"CrewAI initialization warning: {str(e)}", "warning")
                finally:
                    st.session_state.loading_states['crew_initialization'] = False
            
            st.session_state.loading_states['system_init'] = False
            show_success_message("System initialized successfully!")
            return True
            
    except Exception as e:
        st.session_state.loading_states['system_init'] = False
        show_error_message(f"Critical error during system initialization: {str(e)}", "error")
        return False

def render_sidebar():
    """Render the sidebar navigation with enhanced error handling"""
    st.sidebar.markdown("## 🏦 CreditRisk AI Suite")
    st.sidebar.markdown("---")
    
    # System status with enhanced indicators
    st.sidebar.markdown("### System Status")
    
    # Database status
    db_status = st.session_state.system_status.get('database', 'offline')
    db_color = '🟢' if db_status == 'online' else '🔴' if db_status == 'offline' else '🟡'
    st.sidebar.markdown(f"{db_color} Database: {db_status.title()}")
    
    # Crew status
    crew_status = st.session_state.system_status.get('crew', 'offline')
    crew_color = '🟢' if crew_status == 'online' else '🔴' if crew_status == 'offline' else '🟡'
    st.sidebar.markdown(f"{crew_color} CrewAI: {crew_status.title()}")
    
    # Monitor status
    monitor_status = st.session_state.system_status.get('monitor', 'offline')
    monitor_color = '🟢' if monitor_status == 'online' else '🔴' if monitor_status == 'offline' else '🟡'
    st.sidebar.markdown(f"{monitor_color} Monitor: {monitor_status.title()}")
    
    st.sidebar.markdown("---")
    
    # Navigation with validation
    st.sidebar.markdown("### Navigation")
    
    pages = {
        'Home': '🏠',
        'Application': '📝',
        'Processing': '⚙️',
        'Results': '📊',
        'Analytics': '📈'
    }
    
    for page_name, icon in pages.items():
        if st.sidebar.button(f"{icon} {page_name}", key=f"nav_{page_name}"):
            # Validate page access
            if page_name == 'Results' and not st.session_state.analysis_results:
                show_error_message("No analysis results available. Please complete an analysis first.", "warning")
            elif page_name == 'Analytics' and not st.session_state.database_manager:
                show_error_message("Database not available. Please initialize the system first.", "warning")
            else:
                st.session_state.current_page = page_name
                st.rerun()
    
    st.sidebar.markdown("---")
    
    # System controls with enhanced feedback
    st.sidebar.markdown("### System Controls")
    
    if st.sidebar.button("🔄 Initialize System"):
        if initialize_system():
            st.rerun()
    
    if st.sidebar.button("🧹 Clear Results"):
        st.session_state.analysis_results = []
        st.session_state.current_analysis = None
        st.session_state.error_messages = []
        st.session_state.success_messages = []
        show_success_message("Results and messages cleared!")
        st.rerun()
    
    # Error and success message display
    if st.session_state.error_messages:
        st.sidebar.markdown("### ⚠️ Recent Errors")
        for error in st.session_state.error_messages[-3:]:  # Show last 3 errors
            st.sidebar.error(error[:50] + "..." if len(error) > 50 else error)
    
    if st.session_state.success_messages:
        st.sidebar.markdown("### ✅ Recent Success")
        for success in st.session_state.success_messages[-3:]:  # Show last 3 successes
            st.sidebar.success(success[:50] + "..." if len(success) > 50 else success)

# Main application logic with enhanced error handling
def main():
    """Main application function with comprehensive error handling"""
    try:
        # Render sidebar
        render_sidebar()
        
        # Show loading states
        show_loading_state('system_init', "Initializing system...")
        show_loading_state('database_connection', "Connecting to database...")
        show_loading_state('crew_initialization', "Initializing AI agents...")
        
        # Render current page with error handling
        current_page = st.session_state.current_page
        
        try:
            if current_page == 'Home':
                from pages.home import render_home_page
                render_home_page()
            elif current_page == 'Application':
                from pages.application import render_application_page
                render_application_page()
            elif current_page == 'Processing':
                from pages.processing import render_processing_page
                render_processing_page()
            elif current_page == 'Results':
                from pages.results import render_results_page
                render_results_page()
            elif current_page == 'Analytics':
                from pages.analytics import render_analytics_page
                render_analytics_page()
            else:
                show_error_message(f"Unknown page: {current_page}", "error")
                st.session_state.current_page = 'Home'
                st.rerun()
                
        except ImportError as e:
            show_error_message(f"Failed to load page module: {str(e)}", "error")
            st.session_state.current_page = 'Home'
            st.rerun()
        except Exception as e:
            show_error_message(f"Error rendering page: {str(e)}", "error")
            st.error("An unexpected error occurred. Please try refreshing the page.")
            
    except Exception as e:
        st.error(f"Critical application error: {str(e)}")
        st.error("Please restart the application or contact support if the problem persists.")

# Initialize session state
init_session_state()

if __name__ == "__main__":
    main() 