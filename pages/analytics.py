"""
Analytics Page Module for CreditRisk AI Suite
Enhanced analytics dashboard with comprehensive data visualization and insights
"""

import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import plotly.subplots as sp
from datetime import datetime, timedelta
import numpy as np
from typing import Dict, Any, List, Optional
import sqlite3
import json

class AnalyticsDatabase:
    """Database manager for analytics data"""
    
    def __init__(self, db_path: str = "analytics.db"):
        self.db_path = db_path
        self.init_database()
    
    def init_database(self):
        """Initialize the analytics database"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                # Create analytics table
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS credit_analyses (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        customer_id TEXT NOT NULL,
                        risk_score INTEGER NOT NULL,
                        risk_level TEXT NOT NULL,
                        approval_probability REAL NOT NULL,
                        recommendation TEXT NOT NULL,
                        recommended_rate REAL NOT NULL,
                        recommended_amount REAL NOT NULL,
                        execution_time REAL NOT NULL,
                        agents_used INTEGER NOT NULL,
                        tasks_completed INTEGER NOT NULL,
                        analysis_time TIMESTAMP NOT NULL,
                        application_data TEXT,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                    )
                ''')
                
                # Create performance metrics table
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS performance_metrics (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        metric_name TEXT NOT NULL,
                        metric_value REAL NOT NULL,
                        metric_unit TEXT,
                        recorded_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                    )
                ''')
                
                # Create system events table
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS system_events (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        event_type TEXT NOT NULL,
                        event_description TEXT,
                        severity TEXT NOT NULL,
                        recorded_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                    )
                ''')
                
                conn.commit()
                
        except Exception as e:
            st.error(f"Database initialization failed: {str(e)}")
    
    def save_analysis_result(self, result: Dict[str, Any]):
        """Save analysis result to database"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                cursor.execute('''
                    INSERT INTO credit_analyses (
                        customer_id, risk_score, risk_level, approval_probability,
                        recommendation, recommended_rate, recommended_amount,
                        execution_time, agents_used, tasks_completed, analysis_time,
                        application_data
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ''', (
                    result.get('customer_id', 'Unknown'),
                    result.get('risk_score', 0),
                    result.get('risk_level', 'Unknown'),
                    result.get('approval_probability', 0.0),
                    result.get('recommendation', 'Unknown'),
                    result.get('recommended_rate', 0.0),
                    result.get('recommended_amount', 0.0),
                    result.get('execution_time', 0.0),
                    result.get('agents_used', 0),
                    result.get('tasks_completed', 0),
                    result.get('analysis_time', datetime.now().isoformat()),
                    json.dumps(result.get('application_data', {}))
                ))
                
                conn.commit()
                
        except Exception as e:
            st.error(f"Failed to save analysis result: {str(e)}")
    
    def get_analyses(self, start_date: Optional[datetime] = None, end_date: Optional[datetime] = None) -> pd.DataFrame:
        """Get analyses from database with optional date filtering"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                query = "SELECT * FROM credit_analyses"
                params = []
                
                if start_date or end_date:
                    query += " WHERE 1=1"
                    if start_date:
                        query += " AND analysis_time >= ?"
                        params.append(start_date.isoformat())
                    if end_date:
                        query += " AND analysis_time <= ?"
                        params.append(end_date.isoformat())
                
                query += " ORDER BY analysis_time DESC"
                
                df = pd.read_sql_query(query, conn, params=params)
                
                # Parse application_data JSON
                if 'application_data' in df.columns:
                    df['application_data'] = df['application_data'].apply(
                        lambda x: json.loads(x) if x else {}
                    )
                
                return df
                
        except Exception as e:
            st.error(f"Failed to retrieve analyses: {str(e)}")
            return pd.DataFrame()
    
    def get_performance_metrics(self, metric_name: Optional[str] = None, days: int = 30) -> pd.DataFrame:
        """Get performance metrics from database"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                query = "SELECT * FROM performance_metrics"
                params = []
                
                if metric_name:
                    query += " WHERE metric_name = ?"
                    params.append(metric_name)
                
                query += f" AND recorded_at >= datetime('now', '-{days} days')"
                query += " ORDER BY recorded_at DESC"
                
                df = pd.read_sql_query(query, conn, params=params)
                return df
                
        except Exception as e:
            st.error(f"Failed to retrieve performance metrics: {str(e)}")
            return pd.DataFrame()

def create_risk_distribution_chart(df: pd.DataFrame) -> go.Figure:
    """Create risk distribution chart"""
    if df.empty:
        return go.Figure()
    
    # Risk level distribution
    risk_counts = df['risk_level'].value_counts()
    
    fig = go.Figure(data=[
        go.Bar(
            x=risk_counts.index,
            y=risk_counts.values,
            marker_color=['#2E8B57', '#FFD700', '#FF6347', '#DC143C', '#8B0000'],
            text=risk_counts.values,
            textposition='auto'
        )
    ])
    
    fig.update_layout(
        title="Risk Level Distribution",
        xaxis_title="Risk Level",
        yaxis_title="Number of Analyses",
        height=400
    )
    
    return fig

def create_risk_score_histogram(df: pd.DataFrame) -> go.Figure:
    """Create risk score histogram"""
    if df.empty:
        return go.Figure()
    
    fig = px.histogram(
        df, 
        x='risk_score',
        nbins=20,
        title="Risk Score Distribution",
        labels={'risk_score': 'Risk Score', 'count': 'Number of Analyses'},
        color_discrete_sequence=['#1f77b4']
    )
    
    fig.update_layout(height=400)
    return fig

def create_approval_trend_chart(df: pd.DataFrame) -> go.Figure:
    """Create approval probability trend chart"""
    if df.empty:
        return go.Figure()
    
    # Convert analysis_time to datetime if it's not already
    df['analysis_time'] = pd.to_datetime(df['analysis_time'])
    
    fig = px.line(
        df,
        x='analysis_time',
        y='approval_probability',
        title="Approval Probability Trend Over Time",
        labels={'analysis_time': 'Analysis Time', 'approval_probability': 'Approval Probability'},
        markers=True
    )
    
    fig.update_layout(height=400)
    return fig

def create_execution_performance_chart(df: pd.DataFrame) -> go.Figure:
    """Create execution performance chart"""
    if df.empty:
        return go.Figure()
    
    df['analysis_time'] = pd.to_datetime(df['analysis_time'])
    
    fig = go.Figure()
    
    # Add execution time line
    fig.add_trace(go.Scatter(
        x=df['analysis_time'],
        y=df['execution_time'],
        mode='lines+markers',
        name='Execution Time (s)',
        line=dict(color='#1f77b4')
    ))
    
    # Add tasks completed line
    fig.add_trace(go.Scatter(
        x=df['analysis_time'],
        y=df['tasks_completed'],
        mode='lines+markers',
        name='Tasks Completed',
        line=dict(color='#ff7f0e'),
        yaxis='y2'
    ))
    
    fig.update_layout(
        title="Execution Performance Over Time",
        xaxis_title="Analysis Time",
        yaxis=dict(title="Execution Time (seconds)", side="left"),
        yaxis2=dict(title="Tasks Completed", side="right", overlaying="y"),
        height=400
    )
    
    return fig

def create_recommendation_analysis_chart(df: pd.DataFrame) -> go.Figure:
    """Create recommendation analysis chart"""
    if df.empty:
        return go.Figure()
    
    # Recommendation distribution
    rec_counts = df['recommendation'].value_counts()
    
    fig = px.pie(
        values=rec_counts.values,
        names=rec_counts.index,
        title="Recommendation Distribution",
        color_discrete_sequence=px.colors.qualitative.Set3
    )
    
    fig.update_layout(height=400)
    return fig

def create_financial_metrics_chart(df: pd.DataFrame) -> go.Figure:
    """Create financial metrics chart"""
    if df.empty:
        return go.Figure()
    
    # Extract financial data from application_data
    financial_data = []
    for _, row in df.iterrows():
        app_data = row.get('application_data', {})
        if isinstance(app_data, dict):
            financial_data.append({
                'analysis_time': row['analysis_time'],
                'annual_income': app_data.get('annual_income', 0),
                'credit_score': app_data.get('credit_score', 0),
                'loan_amount': app_data.get('loan_amount', 0),
                'recommended_amount': row.get('recommended_amount', 0)
            })
    
    if not financial_data:
        return go.Figure()
    
    financial_df = pd.DataFrame(financial_data)
    financial_df['analysis_time'] = pd.to_datetime(financial_df['analysis_time'])
    
    fig = sp.make_subplots(
        rows=2, cols=2,
        subplot_titles=('Annual Income Trend', 'Credit Score Trend', 'Loan Amount vs Recommended', 'Income Distribution'),
        specs=[[{"type": "scatter"}, {"type": "scatter"}],
               [{"type": "scatter"}, {"type": "histogram"}]]
    )
    
    # Annual income trend
    fig.add_trace(
        go.Scatter(x=financial_df['analysis_time'], y=financial_df['annual_income'], 
                  mode='lines+markers', name='Annual Income'),
        row=1, col=1
    )
    
    # Credit score trend
    fig.add_trace(
        go.Scatter(x=financial_df['analysis_time'], y=financial_df['credit_score'], 
                  mode='lines+markers', name='Credit Score'),
        row=1, col=2
    )
    
    # Loan amount vs recommended
    fig.add_trace(
        go.Scatter(x=financial_df['loan_amount'], y=financial_df['recommended_amount'], 
                  mode='markers', name='Loan vs Recommended'),
        row=2, col=1
    )
    
    # Income distribution
    fig.add_trace(
        go.Histogram(x=financial_df['annual_income'], name='Income Distribution'),
        row=2, col=2
    )
    
    fig.update_layout(height=600, title_text="Financial Metrics Analysis")
    
    return fig

def calculate_summary_statistics(df: pd.DataFrame) -> Dict[str, Any]:
    """Calculate summary statistics from analysis data"""
    if df.empty:
        return {}
    
    stats = {
        'total_analyses': len(df),
        'avg_risk_score': df['risk_score'].mean(),
        'median_risk_score': df['risk_score'].median(),
        'std_risk_score': df['risk_score'].std(),
        'avg_approval_probability': df['approval_probability'].mean(),
        'avg_execution_time': df['execution_time'].mean(),
        'avg_agents_used': df['agents_used'].mean(),
        'avg_tasks_completed': df['tasks_completed'].mean(),
        'success_rate': (df['recommendation'].str.contains('Approve', case=False).sum() / len(df)) * 100,
        'risk_level_distribution': df['risk_level'].value_counts().to_dict(),
        'recommendation_distribution': df['recommendation'].value_counts().to_dict()
    }
    
    # Calculate approval rate by risk level
    approval_by_risk = df.groupby('risk_level')['approval_probability'].mean().to_dict()
    stats['approval_rate_by_risk'] = approval_by_risk
    
    # Calculate performance metrics
    if len(df) > 1:
        stats['execution_time_trend'] = 'increasing' if df['execution_time'].iloc[-1] > df['execution_time'].iloc[0] else 'decreasing'
        stats['risk_score_trend'] = 'increasing' if df['risk_score'].iloc[-1] > df['risk_score'].iloc[0] else 'decreasing'
    
    return stats

def render_analytics_page():
    """Render the enhanced analytics page"""
    st.markdown('<h1 class="sub-header">📊 Analytics & Reporting Dashboard</h1>', unsafe_allow_html=True)
    
    # Initialize database
    if 'analytics_db' not in st.session_state:
        st.session_state.analytics_db = AnalyticsDatabase()
    
    # Save current analysis results to database if available
    if st.session_state.analysis_results:
        for result in st.session_state.analysis_results:
            st.session_state.analytics_db.save_analysis_result(result)
    
    # Date range filter
    st.markdown("### 📅 Date Range Filter")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        date_range = st.selectbox(
            "Select Date Range",
            ["Last 7 days", "Last 30 days", "Last 90 days", "Last 6 months", "Last year", "All time", "Custom"]
        )
    
    with col2:
        if date_range == "Custom":
            start_date_input = st.date_input("Start Date", value=datetime.now() - timedelta(days=30))
            if isinstance(start_date_input, tuple) and len(start_date_input) > 0:
                start_date = datetime.combine(start_date_input[0], datetime.min.time()) if start_date_input[0] else None
            elif not isinstance(start_date_input, tuple):
                start_date = datetime.combine(start_date_input, datetime.min.time()) if start_date_input else None
            else:
                start_date = None
        else:
            start_date = None
    
    with col3:
        if date_range == "Custom":
            end_date_input = st.date_input("End Date", value=datetime.now())
            if isinstance(end_date_input, tuple) and len(end_date_input) > 0:
                end_date = datetime.combine(end_date_input[0], datetime.max.time()) if end_date_input[0] else None
            elif not isinstance(end_date_input, tuple):
                end_date = datetime.combine(end_date_input, datetime.max.time()) if end_date_input else None
            else:
                end_date = None
        else:
            end_date = None
    
    # Calculate date range
    if date_range == "Last 7 days":
        start_date = datetime.now() - timedelta(days=7)
        end_date = datetime.now()
    elif date_range == "Last 30 days":
        start_date = datetime.now() - timedelta(days=30)
        end_date = datetime.now()
    elif date_range == "Last 90 days":
        start_date = datetime.now() - timedelta(days=90)
        end_date = datetime.now()
    elif date_range == "Last 6 months":
        start_date = datetime.now() - timedelta(days=180)
        end_date = datetime.now()
    elif date_range == "Last year":
        start_date = datetime.now() - timedelta(days=365)
        end_date = datetime.now()
    elif date_range == "All time":
        start_date = None
        end_date = None
    
    # Get filtered data
    df = st.session_state.analytics_db.get_analyses(start_date, end_date)
    
    if df.empty:
        st.info("No analysis data available for the selected date range.")
        return
    
    # Summary Statistics
    st.markdown("### 📈 Summary Statistics")
    
    stats = calculate_summary_statistics(df)
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.markdown('<div class="metric-card">', unsafe_allow_html=True)
        st.metric("Total Analyses", stats.get('total_analyses', 0))
        st.markdown('</div>', unsafe_allow_html=True)
    
    with col2:
        avg_risk = stats.get('avg_risk_score', 0)
        st.markdown('<div class="metric-card">', unsafe_allow_html=True)
        st.metric("Average Risk Score", f"{avg_risk:.1f}/100")
        st.markdown('</div>', unsafe_allow_html=True)
    
    with col3:
        success_rate = stats.get('success_rate', 0)
        success_color = "success-metric" if success_rate >= 70 else "warning-metric" if success_rate >= 50 else "error-metric"
        st.markdown(f'<div class="metric-card {success_color}">', unsafe_allow_html=True)
        st.metric("Approval Rate", f"{success_rate:.1f}%")
        st.markdown('</div>', unsafe_allow_html=True)
    
    with col4:
        avg_exec_time = stats.get('avg_execution_time', 0)
        st.markdown('<div class="metric-card">', unsafe_allow_html=True)
        st.metric("Avg Execution Time", f"{avg_exec_time:.2f}s")
        st.markdown('</div>', unsafe_allow_html=True)
    
    # Risk Assessment Analytics
    st.markdown("### 🎯 Risk Assessment Analytics")
    
    col1, col2 = st.columns(2)
    
    with col1:
        risk_dist_chart = create_risk_distribution_chart(df)
        st.plotly_chart(risk_dist_chart, use_container_width=True)
    
    with col2:
        risk_hist_chart = create_risk_score_histogram(df)
        st.plotly_chart(risk_hist_chart, use_container_width=True)
    
    # Approval Trends
    st.markdown("### ✅ Approval Trends")
    
    approval_trend_chart = create_approval_trend_chart(df)
    st.plotly_chart(approval_trend_chart, use_container_width=True)
    
    # Performance Analytics
    st.markdown("### ⚡ Performance Analytics")
    
    col1, col2 = st.columns(2)
    
    with col1:
        exec_perf_chart = create_execution_performance_chart(df)
        st.plotly_chart(exec_perf_chart, use_container_width=True)
    
    with col2:
        rec_analysis_chart = create_recommendation_analysis_chart(df)
        st.plotly_chart(rec_analysis_chart, use_container_width=True)
    
    # Financial Metrics
    st.markdown("### 💰 Financial Metrics Analysis")
    
    financial_chart = create_financial_metrics_chart(df)
    st.plotly_chart(financial_chart, use_container_width=True)
    
    # Detailed Statistics
    st.markdown("### 📊 Detailed Statistics")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("**Risk Level Distribution**")
        risk_dist = stats.get('risk_level_distribution', {})
        for level, count in risk_dist.items():
            percentage = (count / stats.get('total_analyses', 1)) * 100
            st.write(f"- {level}: {count} ({percentage:.1f}%)")
        
        st.markdown("**Approval Rate by Risk Level**")
        approval_by_risk = stats.get('approval_rate_by_risk', {})
        for level, rate in approval_by_risk.items():
            st.write(f"- {level}: {rate:.1f}%")
    
    with col2:
        st.markdown("**Recommendation Distribution**")
        rec_dist = stats.get('recommendation_distribution', {})
        for rec, count in rec_dist.items():
            percentage = (count / stats.get('total_analyses', 1)) * 100
            st.write(f"- {rec}: {count} ({percentage:.1f}%)")
        
        st.markdown("**Performance Metrics**")
        st.write(f"- Average Agents Used: {stats.get('avg_agents_used', 0):.1f}")
        st.write(f"- Average Tasks Completed: {stats.get('avg_tasks_completed', 0):.1f}")
        st.write(f"- Risk Score Standard Deviation: {stats.get('std_risk_score', 0):.1f}")
    
    # Trend Analysis
    st.markdown("### 📈 Trend Analysis")
    
    if len(df) > 1:
        col1, col2, col3 = st.columns(3)
        
        with col1:
            exec_trend = stats.get('execution_time_trend', 'stable')
            trend_icon = "📈" if exec_trend == 'increasing' else "📉" if exec_trend == 'decreasing' else "➡️"
            st.metric("Execution Time Trend", f"{trend_icon} {exec_trend.title()}")
        
        with col2:
            risk_trend = stats.get('risk_score_trend', 'stable')
            trend_icon = "📈" if risk_trend == 'increasing' else "📉" if risk_trend == 'decreasing' else "➡️"
            st.metric("Risk Score Trend", f"{trend_icon} {risk_trend.title()}")
        
        with col3:
            # Calculate month-over-month growth
            df['month'] = pd.to_datetime(df['analysis_time']).dt.to_period('M')
            monthly_counts = df.groupby('month').size()
            if len(monthly_counts) > 1:
                growth_rate = ((monthly_counts.iloc[-1] - monthly_counts.iloc[-2]) / monthly_counts.iloc[-2]) * 100
                st.metric("Monthly Growth", f"{growth_rate:.1f}%")
            else:
                st.metric("Monthly Growth", "N/A")
    
    # Data Export
    st.markdown("### 📄 Data Export")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        # Export filtered data as CSV
        csv_data = df.to_csv(index=False)
        st.download_button(
            label="📊 Export Analytics Data (CSV)",
            data=csv_data,
            file_name=f"analytics_data_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
            mime="text/csv"
        )
    
    with col2:
        # Export summary statistics as JSON
        summary_json = json.dumps(stats, indent=2, default=str)
        st.download_button(
            label="📋 Export Summary Statistics (JSON)",
            data=summary_json,
            file_name=f"summary_statistics_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json",
            mime="application/json"
        )
    
    with col3:
        # Export detailed report
        report_text = f"""
# Credit Risk Analytics Report
Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
Date Range: {date_range}

## Summary Statistics
- Total Analyses: {stats.get('total_analyses', 0)}
- Average Risk Score: {stats.get('avg_risk_score', 0):.1f}/100
- Approval Rate: {stats.get('success_rate', 0):.1f}%
- Average Execution Time: {stats.get('avg_execution_time', 0):.2f}s

## Risk Level Distribution
"""
        for level, count in stats.get('risk_level_distribution', {}).items():
            percentage = (count / stats.get('total_analyses', 1)) * 100
            report_text += f"- {level}: {count} ({percentage:.1f}%)\n"
        
        report_text += "\n## Recommendation Distribution\n"
        for rec, count in stats.get('recommendation_distribution', {}).items():
            percentage = (count / stats.get('total_analyses', 1)) * 100
            report_text += f"- {rec}: {count} ({percentage:.1f}%)\n"
        
        st.download_button(
            label="📝 Export Analytics Report (MD)",
            data=report_text,
            file_name=f"analytics_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.md",
            mime="text/markdown"
        )
    
    # Action Buttons
    st.markdown("### 🎯 Actions")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        if st.button("🔄 Refresh Data", type="primary"):
            st.rerun()
    
    with col2:
        if st.button("📊 View Results"):
            st.session_state.current_page = 'Results'
            st.rerun()
    
    with col3:
        if st.button("📝 New Analysis"):
            st.session_state.current_page = 'Application'
            st.rerun() 