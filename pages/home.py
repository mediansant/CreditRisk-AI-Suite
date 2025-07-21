"""
Home Page Module for CreditRisk AI Suite
Enhanced with improved UI/UX and loading states
"""

import streamlit as st
from datetime import datetime
import time

def show_system_status_card():
    """Display system status with enhanced styling"""
    st.markdown('<div class="metric-card">', unsafe_allow_html=True)
    
    # Calculate overall system status
    all_online = all(status == 'online' for status in st.session_state.system_status.values())
    any_online = any(status == 'online' for status in st.session_state.system_status.values())
    
    if all_online:
        status_text = "🟢 All Systems Online"
        status_class = "success-metric"
    elif any_online:
        status_text = "🟡 Partial System Online"
        status_class = "warning-metric"
    else:
        status_text = "🔴 System Offline"
        status_class = "error-metric"
    
    st.markdown(f'<div class="{status_class}">', unsafe_allow_html=True)
    st.metric(label="System Status", value=status_text)
    st.markdown('</div>', unsafe_allow_html=True)
    st.markdown('</div>', unsafe_allow_html=True)

def show_metrics_dashboard():
    """Display key metrics with enhanced styling"""
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.markdown('<div class="metric-card">', unsafe_allow_html=True)
        analyses_count = len(st.session_state.analysis_results)
        st.metric(
            label="📊 Analyses Completed",
            value=analyses_count,
            delta=f"+{analyses_count}" if analyses_count > 0 else None
        )
        st.markdown('</div>', unsafe_allow_html=True)
    
    with col2:
        st.markdown('<div class="metric-card">', unsafe_allow_html=True)
        if st.session_state.performance_monitor:
            realtime = st.session_state.performance_monitor.get_realtime_metrics()
            recent_executions = realtime.get('performance', {}).get('recent_executions', 0)
            st.metric(
                label="⚡ Recent Executions", 
                value=recent_executions,
                delta=f"+{recent_executions}" if recent_executions > 0 else None
            )
        else:
            st.metric(label="⚡ Recent Executions", value=0)
        st.markdown('</div>', unsafe_allow_html=True)
    
    with col3:
        st.markdown('<div class="metric-card">', unsafe_allow_html=True)
        if st.session_state.performance_monitor:
            realtime = st.session_state.performance_monitor.get_realtime_metrics()
            avg_time = realtime.get('performance', {}).get('average_execution_time', 0)
            st.metric(
                label="⏱️ Avg Execution Time", 
                value=f"{avg_time:.2f}s",
                delta="Faster" if avg_time < 5.0 else "Slower" if avg_time > 10.0 else None
            )
        else:
            st.metric(label="⏱️ Avg Execution Time", value="N/A")
        st.markdown('</div>', unsafe_allow_html=True)

def show_welcome_section():
    """Display welcome section with enhanced styling"""
    st.markdown('<h2 class="sub-header">🚀 Welcome to CreditRisk AI Suite</h2>', unsafe_allow_html=True)
    
    st.markdown("""
    <div class="info-card">
        <p>This application provides comprehensive credit risk analysis using advanced AI agents and real-time performance monitoring.</p>
    </div>
    """, unsafe_allow_html=True)
    
    # Key features with icons and descriptions
    features = [
        ("🤖", "AI-Powered Analysis", "CrewAI agents for specialized credit risk assessment"),
        ("📊", "Real-time Monitoring", "Performance metrics and system health tracking"),
        ("🗄️", "Direct Database Integration", "Optimized MySQL connections with connection pooling"),
        ("📈", "Advanced Analytics", "Comprehensive reporting and visualization"),
        ("⚡", "High Performance", "Optimized workflows and resource management"),
        ("🔒", "Secure Processing", "Enterprise-grade security and data protection")
    ]
    
    # Display features in a grid
    cols = st.columns(2)
    for i, (icon, title, description) in enumerate(features):
        with cols[i % 2]:
            st.markdown(f"""
            <div class="metric-card">
                <h4>{icon} {title}</h4>
                <p>{description}</p>
            </div>
            """, unsafe_allow_html=True)

def show_quick_start_guide():
    """Display quick start guide with enhanced styling"""
    st.markdown('<h3 class="section-header">📋 Quick Start Guide</h3>', unsafe_allow_html=True)
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("""
        <div class="info-card">
            <h4>🔧 Step 1: Initialize System</h4>
            <ul>
                <li>Click "Initialize System" in the sidebar</li>
                <li>Verify all components are online</li>
                <li>Check system status indicators</li>
            </ul>
        </div>
        
        <div class="info-card">
            <h4>📝 Step 2: Submit Application</h4>
            <ul>
                <li>Navigate to the Application page</li>
                <li>Enter customer information</li>
                <li>Validate data and submit for analysis</li>
            </ul>
        </div>
        """, unsafe_allow_html=True)
    
    with col2:
        st.markdown("""
        <div class="info-card">
            <h4>⚙️ Step 3: Monitor Processing</h4>
            <ul>
                <li>Watch real-time processing on the Processing page</li>
                <li>Track agent interactions and performance</li>
                <li>Monitor system resources</li>
            </ul>
        </div>
        
        <div class="info-card">
            <h4>📊 Step 4: View Results</h4>
            <ul>
                <li>Access detailed results and reports</li>
                <li>Review analytics and performance metrics</li>
                <li>Download reports in multiple formats</li>
            </ul>
        </div>
        """, unsafe_allow_html=True)

def show_system_components():
    """Display system components status with enhanced styling"""
    st.markdown('<h3 class="section-header">🔧 System Components</h3>', unsafe_allow_html=True)
    
    status_col1, status_col2 = st.columns(2)
    
    with status_col1:
        # Database Connection
        st.markdown("**🗄️ Database Connection**")
        if st.session_state.database_manager:
            st.markdown("""
            <div class="success-metric">
                <p>✅ Connected to MySQL database</p>
                <small>Direct connection with connection pooling</small>
            </div>
            """, unsafe_allow_html=True)
        else:
            st.markdown("""
            <div class="error-metric">
                <p>❌ Database not initialized</p>
                <small>Click "Initialize System" to connect</small>
            </div>
            """, unsafe_allow_html=True)
        
        # Performance Monitor
        st.markdown("**📊 Performance Monitor**")
        if st.session_state.performance_monitor:
            st.markdown("""
            <div class="success-metric">
                <p>✅ Real-time monitoring active</p>
                <small>Tracking system metrics and performance</small>
            </div>
            """, unsafe_allow_html=True)
        else:
            st.markdown("""
            <div class="error-metric">
                <p>❌ Monitor not initialized</p>
                <small>Initialize system to enable monitoring</small>
            </div>
            """, unsafe_allow_html=True)
    
    with status_col2:
        # CrewAI Agents
        st.markdown("**🤖 CrewAI Agents**")
        if st.session_state.crew_initialized:
            st.markdown("""
            <div class="success-metric">
                <p>✅ 4 specialized agents ready</p>
                <small>Data Collection, Risk Analysis, Documentation, Reporting</small>
            </div>
            """, unsafe_allow_html=True)
        else:
            st.markdown("""
            <div class="warning-metric">
                <p>⚠️ CrewAI needs initialization</p>
                <small>Some features may be limited</small>
            </div>
            """, unsafe_allow_html=True)
        
        # Analysis Engine
        st.markdown("**⚙️ Analysis Engine**")
        if st.session_state.crew_initialized and st.session_state.database_manager:
            st.markdown("""
            <div class="success-metric">
                <p>✅ Ready for credit analysis</p>
                <small>Complete workflow orchestration available</small>
            </div>
            """, unsafe_allow_html=True)
        else:
            st.markdown("""
            <div class="error-metric">
                <p>❌ System not fully initialized</p>
                <small>Initialize all components to begin analysis</small>
            </div>
            """, unsafe_allow_html=True)

def show_recent_activity():
    """Display recent activity with enhanced styling"""
    if st.session_state.analysis_results:
        st.markdown('<h3 class="section-header">📋 Recent Activity</h3>', unsafe_allow_html=True)
        
        recent_results = st.session_state.analysis_results[-3:]  # Last 3 results
        
        for i, result in enumerate(recent_results):
            with st.expander(f"📊 Analysis #{len(st.session_state.analysis_results) - 2 + i} - {result.get('customer_id', 'Unknown')} - {result.get('analysis_time', 'Unknown time')}"):
                col1, col2, col3 = st.columns(3)
                
                with col1:
                    risk_score = result.get('risk_score', 0)
                    risk_color = "🟢" if risk_score < 30 else "🟡" if risk_score < 70 else "🔴"
                    st.metric(f"{risk_color} Risk Score", f"{risk_score}/100")
                
                with col2:
                    risk_level = result.get('risk_level', 'Unknown')
                    level_color = "🟢" if risk_level == 'Low' else "🟡" if risk_level == 'Medium' else "🔴"
                    st.metric(f"{level_color} Risk Level", risk_level)
                
                with col3:
                    recommendation = result.get('recommendation', 'Unknown')
                    rec_color = "🟢" if recommendation == 'Approve' else "🔴" if recommendation == 'Reject' else "🟡"
                    st.metric(f"{rec_color} Recommendation", recommendation)

def show_system_health_dashboard():
    """Display system health dashboard with enhanced styling"""
    st.markdown('<h3 class="section-header">🏥 System Health Dashboard</h3>', unsafe_allow_html=True)
    
    if st.session_state.performance_monitor:
        realtime = st.session_state.performance_monitor.get_realtime_metrics()
        
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            cpu_usage = realtime.get('system', {}).get('cpu_usage_percent', 0)
            cpu_color = "🟢" if cpu_usage < 70 else "🟡" if cpu_usage < 90 else "🔴"
            cpu_status = "Normal" if cpu_usage < 70 else "High" if cpu_usage < 90 else "Critical"
            st.metric(f"{cpu_color} CPU Usage", f"{cpu_usage:.1f}%", delta=cpu_status)
        
        with col2:
            memory_usage = realtime.get('system', {}).get('memory_usage_percent', 0)
            memory_color = "🟢" if memory_usage < 70 else "🟡" if memory_usage < 90 else "🔴"
            memory_status = "Normal" if memory_usage < 70 else "High" if memory_usage < 90 else "Critical"
            st.metric(f"{memory_color} Memory Usage", f"{memory_usage:.1f}%", delta=memory_status)
        
        with col3:
            recent_executions = realtime.get('performance', {}).get('recent_executions', 0)
            st.metric("📊 Recent Executions", recent_executions)
        
        with col4:
            avg_time = realtime.get('performance', {}).get('average_execution_time', 0)
            time_status = "Fast" if avg_time < 5.0 else "Slow" if avg_time > 10.0 else "Normal"
            st.metric("⏱️ Avg Execution Time", f"{avg_time:.2f}s", delta=time_status)
        
        # Additional health metrics
        st.markdown("---")
        health_col1, health_col2 = st.columns(2)
        
        with health_col1:
            st.markdown("**📈 Performance Trends**")
            # Placeholder for performance trend chart
            st.info("Performance trend visualization will be displayed here")
        
        with health_col2:
            st.markdown("**🔍 System Alerts**")
            alerts = []
            if cpu_usage > 80:
                alerts.append(f"⚠️ High CPU usage: {cpu_usage:.1f}%")
            if memory_usage > 80:
                alerts.append(f"⚠️ High memory usage: {memory_usage:.1f}%")
            if avg_time > 10:
                alerts.append(f"⚠️ Slow execution time: {avg_time:.2f}s")
            
            if alerts:
                for alert in alerts:
                    st.warning(alert)
            else:
                st.success("✅ All systems operating normally")
    else:
        st.markdown("""
        <div class="info-card">
            <p>Performance monitor not available. Initialize the system to view health metrics.</p>
        </div>
        """, unsafe_allow_html=True)

def show_action_buttons():
    """Display action buttons with enhanced styling"""
    st.markdown('<h3 class="section-header">🎯 Quick Actions</h3>', unsafe_allow_html=True)
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        if st.button("🚀 Start New Analysis", key="start_analysis"):
            st.session_state.current_page = 'Application'
            st.rerun()
    
    with col2:
        if st.button("📊 View Analytics", key="view_analytics"):
            if st.session_state.database_manager:
                st.session_state.current_page = 'Analytics'
                st.rerun()
            else:
                st.error("Database not available. Please initialize the system first.")
    
    with col3:
        if st.button("📋 View Results", key="view_results"):
            if st.session_state.analysis_results:
                st.session_state.current_page = 'Results'
                st.rerun()
            else:
                st.error("No analysis results available. Please complete an analysis first.")

def render_home_page():
    """Render the enhanced home page with improved UI/UX"""
    # Main header with animation
    st.markdown('<h1 class="main-header">🏦 CreditRisk AI Suite</h1>', unsafe_allow_html=True)
    
    # System status overview
    show_system_status_card()
    
    # Key metrics dashboard
    show_metrics_dashboard()
    
    # Welcome section
    show_welcome_section()
    
    # Quick start guide
    show_quick_start_guide()
    
    # System components status
    show_system_components()
    
    # Recent activity
    show_recent_activity()
    
    # System health dashboard
    show_system_health_dashboard()
    
    # Quick action buttons
    show_action_buttons()
    
    # Footer with additional information
    st.markdown("---")
    st.markdown("""
    <div style="text-align: center; color: #666; font-size: 0.9rem;">
        <p>💡 <strong>Tip:</strong> Use the sidebar to navigate between pages and monitor system status</p>
        <p>🔄 <strong>Need help?</strong> Check the documentation or contact support</p>
    </div>
    """, unsafe_allow_html=True) 