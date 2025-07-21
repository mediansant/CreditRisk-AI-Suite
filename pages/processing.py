"""
Processing Page Module for CreditRisk AI Suite
Enhanced workflow processing with real-time monitoring and visualization
"""

import streamlit as st
import time
import json
import threading
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional
import plotly.graph_objects as go
import plotly.express as px
from dataclasses import dataclass, asdict
import random
import pandas as pd

@dataclass
class AgentStatus:
    """Agent status information"""
    name: str
    status: str  # 'idle', 'running', 'completed', 'failed', 'paused'
    current_task: str
    progress: float  # 0-100
    start_time: Optional[datetime] = None
    end_time: Optional[datetime] = None
    error_message: Optional[str] = None
    tasks_completed: int = 0
    total_tasks: int = 0

@dataclass
class WorkflowStep:
    """Workflow step information"""
    step_id: str
    name: str
    description: str
    agent: str
    status: str  # 'pending', 'running', 'completed', 'failed', 'skipped'
    progress: float
    start_time: Optional[datetime] = None
    end_time: Optional[datetime] = None
    duration: Optional[float] = None
    error_message: Optional[str] = None
    dependencies: Optional[List[str]] = None

class AgentWorkflowManager:
    """Manages agent workflow execution and status tracking"""
    
    def __init__(self):
        self.agents = {
            "data_collection": AgentStatus(
                name="Data Collection Agent",
                status="idle",
                current_task="",
                progress=0.0,
                total_tasks=5  # Updated: 5 tasks (validating, fetching, gathering, collecting, retrieving)
            ),
            "risk_analysis": AgentStatus(
                name="Risk Analysis Agent", 
                status="idle",
                current_task="",
                progress=0.0,
                total_tasks=9  # Updated: 5 risk tasks + 4 market tasks = 9 total
            ),
            "documentation": AgentStatus(
                name="Documentation Agent",
                status="idle", 
                current_task="",
                progress=0.0,
                total_tasks=3  # Updated: 3 tasks (summary, assessment, recommendation)
            ),
            "reporting": AgentStatus(
                name="Reporting Agent",
                status="idle",
                current_task="",
                progress=0.0,
                total_tasks=3  # Updated: 3 tasks (compiling, generating, creating)
            )
        }
        
        self.workflow_steps = [
            WorkflowStep(
                step_id="init",
                name="System Initialization",
                description="Initialize CrewAI system and validate application data",
                agent="system",
                status="pending",
                progress=0.0,
                dependencies=[]
            ),
            WorkflowStep(
                step_id="data_gather",
                name="Data Collection",
                description="Gather customer data, credit history, and market information",
                agent="data_collection",
                status="pending",
                progress=0.0,
                dependencies=["init"]
            ),
            WorkflowStep(
                step_id="risk_calc",
                name="Risk Calculation",
                description="Calculate credit risk scores and financial ratios",
                agent="risk_analysis",
                status="pending",
                progress=0.0,
                dependencies=["data_gather"]
            ),
            WorkflowStep(
                step_id="market_analysis",
                name="Market Analysis",
                description="Analyze market conditions and industry trends",
                agent="risk_analysis",
                status="pending",
                progress=0.0,
                dependencies=["data_gather"]
            ),
            WorkflowStep(
                step_id="documentation",
                name="Documentation Generation",
                description="Create comprehensive analysis documentation",
                agent="documentation",
                status="pending",
                progress=0.0,
                dependencies=["risk_calc", "market_analysis"]
            ),
            WorkflowStep(
                step_id="reporting",
                name="Report Generation",
                description="Generate final recommendation report",
                agent="reporting",
                status="pending",
                progress=0.0,
                dependencies=["documentation"]
            ),
            WorkflowStep(
                step_id="finalize",
                name="Finalization",
                description="Complete analysis and prepare results",
                agent="system",
                status="pending",
                progress=0.0,
                dependencies=["reporting"]
            )
        ]
        
        self.workflow_status = "idle"  # 'idle', 'running', 'paused', 'completed', 'failed'
        self.start_time = None
        self.end_time = None
        self.current_step_index = 0
        self.execution_log = []
        
    def start_workflow(self):
        """Start the workflow execution"""
        self.workflow_status = "running"
        self.start_time = datetime.now()
        self.current_step_index = 0
        self.execution_log = []
        self._log_event("Workflow started")
        
    def pause_workflow(self):
        """Pause the workflow execution"""
        self.workflow_status = "paused"
        self._log_event("Workflow paused")
        
    def stop_workflow(self):
        """Stop workflow execution"""
        self.workflow_status = "stopped"
        self.end_time = datetime.now()
        self._log_event("Workflow stopped", "warning")
    
    def reset_workflow(self):
        """Reset workflow to initial state"""
        self.workflow_status = "idle"
        self.start_time = None
        self.end_time = None
        
        # Reset all agents
        for agent in self.agents.values():
            agent.status = "idle"
            agent.current_task = ""
            agent.progress = 0.0
            agent.tasks_completed = 0
            agent.start_time = None
            agent.end_time = None
            agent.error_message = None
        
        # Reset all workflow steps
        for step in self.workflow_steps:
            step.status = "pending"
            step.progress = 0.0
            step.start_time = None
            step.end_time = None
            step.duration = None
            step.error_message = None
        
        self.execution_log = []
        self._log_event("Workflow reset to initial state", "info")
    
    def get_workflow_progress(self) -> float:
        """Get overall workflow progress"""
        if not self.workflow_steps:
            return 0.0
        
        completed_steps = sum(1 for step in self.workflow_steps if step.status == "completed")
        progress = (completed_steps / len(self.workflow_steps)) * 100
        # Ensure progress never exceeds 100%
        return min(100.0, progress)
        
    def get_current_step(self) -> Optional[WorkflowStep]:
        """Get current workflow step"""
        if 0 <= self.current_step_index < len(self.workflow_steps):
            return self.workflow_steps[self.current_step_index]
        return None
        
    def get_agent_status(self, agent_id: str) -> Optional[AgentStatus]:
        """Get agent status by ID"""
        return self.agents.get(agent_id)
        
    def update_step_progress(self, step_id: str, progress: float, status: Optional[str] = None):
        """Update workflow step progress"""
        # Ensure progress is between 0 and 100
        progress = max(0.0, min(100.0, progress))
        
        for step in self.workflow_steps:
            if step.step_id == step_id:
                step.progress = progress
                if status:
                    step.status = status
                if progress >= 100 and step.status == "running":
                    step.status = "completed"
                    step.end_time = datetime.now()
                    if step.start_time:
                        step.duration = (step.end_time - step.start_time).total_seconds()
                break
                
    def _log_event(self, message: str, level: str = "info"):
        """Log workflow event"""
        timestamp = datetime.now().strftime("%H:%M:%S")
        self.execution_log.append(f"[{timestamp}] {level.upper()}: {message}")
        if len(self.execution_log) > 100:  # Keep only last 100 entries
            self.execution_log = self.execution_log[-100:]
    
    def validate_agent_status(self):
        """Validate and fix agent status consistency"""
        for agent_id, agent in self.agents.items():
            # Check if agent status matches task completion
            if agent.total_tasks > 0:
                completion_ratio = agent.tasks_completed / agent.total_tasks
                
                # Fix status based on actual completion
                if completion_ratio >= 1.0 and agent.status != "completed":
                    agent.status = "completed"
                    agent.progress = 100.0
                    self._log_event(f"Fixed {agent_id} status to completed", "info")
                elif completion_ratio > 0.0 and completion_ratio < 1.0 and agent.status == "completed":
                    agent.status = "running"
                    agent.progress = completion_ratio * 100.0
                    self._log_event(f"Fixed {agent_id} status to running", "info")
                elif completion_ratio == 0.0 and agent.status not in ["idle", "failed"]:
                    agent.status = "idle"
                    agent.progress = 0.0
                    self._log_event(f"Fixed {agent_id} status to idle", "info")

def simulate_agent_workflow(workflow_manager: AgentWorkflowManager, application_data: Dict[str, Any]):
    """Simulate agent workflow execution"""
    
    # Step 1: System Initialization
    workflow_manager.update_step_progress("init", 0, "running")
    workflow_manager.workflow_steps[0].start_time = datetime.now()
    
    for progress in range(0, 101, 10):
        workflow_manager.update_step_progress("init", progress)
        time.sleep(0.1)
    
    workflow_manager.update_step_progress("init", 100, "completed")
    workflow_manager.workflow_steps[0].end_time = datetime.now()
    workflow_manager.workflow_steps[0].duration = (workflow_manager.workflow_steps[0].end_time - workflow_manager.workflow_steps[0].start_time).total_seconds()
    
    # Step 2: Data Collection
    workflow_manager.update_step_progress("data_gather", 0, "running")
    workflow_manager.workflow_steps[1].start_time = datetime.now()
    workflow_manager.agents["data_collection"].status = "running"
    
    data_tasks = [
        "Validating customer information",
        "Fetching credit bureau data", 
        "Gathering employment verification",
        "Collecting financial statements",
        "Retrieving market data"
    ]
    
    for i, task in enumerate(data_tasks):
        workflow_manager.agents["data_collection"].current_task = task
        workflow_manager.agents["data_collection"].tasks_completed = i + 1  # Fix: i+1 not i
        workflow_manager.agents["data_collection"].total_tasks = len(data_tasks)
        progress = ((i + 1) / len(data_tasks)) * 100  # Fix: i+1 for proper progress
        workflow_manager.update_step_progress("data_gather", progress)
        time.sleep(0.3)
    
    workflow_manager.agents["data_collection"].status = "completed"
    workflow_manager.agents["data_collection"].progress = 100
    workflow_manager.agents["data_collection"].tasks_completed = len(data_tasks)  # Ensure final count
    workflow_manager.update_step_progress("data_gather", 100, "completed")
    workflow_manager.workflow_steps[1].end_time = datetime.now()
    workflow_manager.workflow_steps[1].duration = (workflow_manager.workflow_steps[1].end_time - workflow_manager.workflow_steps[1].start_time).total_seconds()
    
    # Step 3: Risk Calculation
    workflow_manager.update_step_progress("risk_calc", 0, "running")
    workflow_manager.workflow_steps[2].start_time = datetime.now()
    workflow_manager.agents["risk_analysis"].status = "running"
    
    risk_tasks = [
        "Calculating credit score",
        "Computing debt-to-income ratio",
        "Analyzing payment history",
        "Evaluating collateral value",
        "Assessing market risk"
    ]
    
    for i, task in enumerate(risk_tasks):
        workflow_manager.agents["risk_analysis"].current_task = task
        workflow_manager.agents["risk_analysis"].tasks_completed = i + 1  # Fix: i+1 not i
        workflow_manager.agents["risk_analysis"].total_tasks = len(risk_tasks)
        progress = ((i + 1) / len(risk_tasks)) * 100  # Fix: i+1 for proper progress
        workflow_manager.update_step_progress("risk_calc", progress)
        time.sleep(0.4)
    
    workflow_manager.update_step_progress("risk_calc", 100, "completed")
    workflow_manager.workflow_steps[2].end_time = datetime.now()
    workflow_manager.workflow_steps[2].duration = (workflow_manager.workflow_steps[2].end_time - workflow_manager.workflow_steps[2].start_time).total_seconds()
    
    # Step 4: Market Analysis
    workflow_manager.update_step_progress("market_analysis", 0, "running")
    workflow_manager.workflow_steps[3].start_time = datetime.now()
    
    market_tasks = [
        "Analyzing industry trends",
        "Evaluating economic indicators",
        "Assessing regional factors",
        "Reviewing competitor rates"
    ]
    
    for i, task in enumerate(market_tasks):
        workflow_manager.agents["risk_analysis"].current_task = task
        workflow_manager.agents["risk_analysis"].tasks_completed = i + 1  # Fix: i+1 not i
        workflow_manager.agents["risk_analysis"].total_tasks = len(market_tasks)
        progress = ((i + 1) / len(market_tasks)) * 100  # Fix: i+1 for proper progress
        workflow_manager.update_step_progress("market_analysis", progress)
        time.sleep(0.3)
    
    workflow_manager.agents["risk_analysis"].status = "completed"
    workflow_manager.agents["risk_analysis"].progress = 100
    workflow_manager.agents["risk_analysis"].tasks_completed = len(risk_tasks) + len(market_tasks)  # Total tasks for risk analysis agent
    workflow_manager.update_step_progress("market_analysis", 100, "completed")
    workflow_manager.workflow_steps[3].end_time = datetime.now()
    workflow_manager.workflow_steps[3].duration = (workflow_manager.workflow_steps[3].end_time - workflow_manager.workflow_steps[3].start_time).total_seconds()
    
    # Step 5: Documentation
    workflow_manager.update_step_progress("documentation", 0, "running")
    workflow_manager.workflow_steps[4].start_time = datetime.now()
    workflow_manager.agents["documentation"].status = "running"
    
    doc_tasks = [
        "Creating analysis summary",
        "Generating risk assessment report",
        "Preparing recommendation document"
    ]
    
    for i, task in enumerate(doc_tasks):
        workflow_manager.agents["documentation"].current_task = task
        workflow_manager.agents["documentation"].tasks_completed = i + 1  # Fix: i+1 not i
        workflow_manager.agents["documentation"].total_tasks = len(doc_tasks)
        progress = ((i + 1) / len(doc_tasks)) * 100  # Fix: i+1 for proper progress
        workflow_manager.update_step_progress("documentation", progress)
        time.sleep(0.2)
    
    workflow_manager.agents["documentation"].status = "completed"
    workflow_manager.agents["documentation"].progress = 100
    workflow_manager.agents["documentation"].tasks_completed = len(doc_tasks)  # Ensure final count
    workflow_manager.update_step_progress("documentation", 100, "completed")
    workflow_manager.workflow_steps[4].end_time = datetime.now()
    workflow_manager.workflow_steps[4].duration = (workflow_manager.workflow_steps[4].end_time - workflow_manager.workflow_steps[4].start_time).total_seconds()
    
    # Step 6: Reporting
    workflow_manager.update_step_progress("reporting", 0, "running")
    workflow_manager.workflow_steps[5].start_time = datetime.now()
    workflow_manager.agents["reporting"].status = "running"
    
    report_tasks = [
        "Compiling final report",
        "Generating recommendations",
        "Creating executive summary"
    ]
    
    for i, task in enumerate(report_tasks):
        workflow_manager.agents["reporting"].current_task = task
        workflow_manager.agents["reporting"].tasks_completed = i + 1  # Fix: i+1 not i
        workflow_manager.agents["reporting"].total_tasks = len(report_tasks)
        progress = ((i + 1) / len(report_tasks)) * 100  # Fix: i+1 for proper progress
        workflow_manager.update_step_progress("reporting", progress)
        time.sleep(0.3)
    
    workflow_manager.agents["reporting"].status = "completed"
    workflow_manager.agents["reporting"].progress = 100
    workflow_manager.agents["reporting"].tasks_completed = len(report_tasks)  # Ensure final count
    workflow_manager.update_step_progress("reporting", 100, "completed")
    workflow_manager.workflow_steps[5].end_time = datetime.now()
    workflow_manager.workflow_steps[5].duration = (workflow_manager.workflow_steps[5].end_time - workflow_manager.workflow_steps[5].start_time).total_seconds()
    
    # Step 7: Finalization
    workflow_manager.update_step_progress("finalize", 0, "running")
    workflow_manager.workflow_steps[6].start_time = datetime.now()
    
    for progress in range(0, 101, 20):
        workflow_manager.update_step_progress("finalize", progress)
        time.sleep(0.1)
    
    workflow_manager.update_step_progress("finalize", 100, "completed")
    workflow_manager.workflow_steps[6].end_time = datetime.now()
    workflow_manager.workflow_steps[6].duration = (workflow_manager.workflow_steps[6].end_time - workflow_manager.workflow_steps[6].start_time).total_seconds()
    
    workflow_manager.workflow_status = "completed"
    workflow_manager.end_time = datetime.now()

def create_workflow_visualization(workflow_manager: AgentWorkflowManager):
    """Create workflow visualization using Plotly"""
    
    # Create Gantt chart for workflow steps
    fig = go.Figure()
    
    colors = {
        'pending': '#E0E0E0',
        'running': '#FFA500',
        'completed': '#00FF00',
        'failed': '#FF0000',
        'skipped': '#808080'
    }
    
    for step in workflow_manager.workflow_steps:
        if step.start_time and step.end_time:
            duration = (step.end_time - step.start_time).total_seconds()
            fig.add_trace(go.Bar(
                name=step.name,
                x=[duration],
                y=[step.agent],
                orientation='h',
                marker_color=colors.get(step.status, '#E0E0E0'),
                text=f"{step.name}<br>{duration:.1f}s",
                textposition='auto',
                hovertemplate=f"<b>{step.name}</b><br>" +
                             f"Status: {step.status}<br>" +
                             f"Duration: {duration:.1f}s<br>" +
                             f"Progress: {step.progress:.1f}%<extra></extra>"
            ))
    
    fig.update_layout(
        title="Workflow Execution Timeline",
        xaxis_title="Duration (seconds)",
        yaxis_title="Agent",
        height=400,
        showlegend=False
    )
    
    return fig

def create_agent_performance_chart(workflow_manager: AgentWorkflowManager):
    """Create agent performance visualization"""
    
    agents_data = []
    for agent_id, agent in workflow_manager.agents.items():
        agents_data.append({
            'Agent': agent.name,
            'Tasks Completed': agent.tasks_completed,
            'Total Tasks': agent.total_tasks,
            'Progress': agent.progress,
            'Status': agent.status
        })
    
    df = pd.DataFrame(agents_data)
    
    fig = px.bar(df, x='Agent', y='Tasks Completed', 
                 color='Status',
                 title="Agent Task Completion Status",
                 color_discrete_map={
                     'idle': '#E0E0E0',
                     'running': '#FFA500', 
                     'completed': '#00FF00',
                     'failed': '#FF0000'
                 })
    
    fig.update_layout(height=300)
    return fig

def render_processing_page():
    """Render the enhanced processing page"""
    st.markdown('<h1 class="sub-header">⚙️ Agent Processing Workflow</h1>', unsafe_allow_html=True)
    
    # Initialize workflow manager in session state
    if 'workflow_manager' not in st.session_state:
        st.session_state.workflow_manager = AgentWorkflowManager()
    
    workflow_manager = st.session_state.workflow_manager
    
    # Check if we have an application to process
    if not st.session_state.current_analysis:
        st.warning("No application to process. Please submit an application first.")
        if st.button("Go to Application"):
            st.session_state.current_page = 'Application'
            st.rerun()
        return
    
    # Display current application
    st.markdown("### 📋 Current Application")
    app_data = st.session_state.current_analysis
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.markdown(f"**Customer ID:** {app_data['customer_id']}")
        st.markdown(f"**Name:** {app_data['name']}")
        st.markdown(f"**Loan Amount:** ${app_data['loan_amount']:,.2f}")
    
    with col2:
        st.markdown(f"**Credit Score:** {app_data['credit_score']}")
        st.markdown(f"**Annual Income:** ${app_data['annual_income']:,.2f}")
        st.markdown(f"**Loan Type:** {app_data['loan_type'].title()}")
    
    with col3:
        st.markdown(f"**Term:** {app_data['term_months']} months")
        st.markdown(f"**Submitted:** {app_data['submission_time'][:19]}")
        
        # Risk indicators
        if 'risk_indicators' in app_data:
            dti_ratio = app_data['risk_indicators']['debt_to_income_ratio']
            if dti_ratio <= 30:
                st.success(f"DTI: {dti_ratio:.1f}% (Good)")
            elif dti_ratio <= 50:
                st.warning(f"DTI: {dti_ratio:.1f}% (Moderate)")
            else:
                st.error(f"DTI: {dti_ratio:.1f}% (High)")
    
    # Processing controls
    st.markdown("### 🎛️ Workflow Controls")
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        if st.button("🚀 Start Workflow", type="primary", disabled=workflow_manager.workflow_status == "running"):
            workflow_manager.start_workflow()
            # Start workflow in background thread
            thread = threading.Thread(
                target=simulate_agent_workflow,
                args=(workflow_manager, app_data)
            )
            thread.start()
            st.rerun()
    
    with col2:
        if st.button("⏸️ Pause Workflow", disabled=workflow_manager.workflow_status != "running"):
            workflow_manager.pause_workflow()
            st.rerun()
    
    with col3:
        if st.button("⏹️ Stop Workflow", disabled=workflow_manager.workflow_status not in ["running", "paused"]):
            workflow_manager.stop_workflow()
            st.rerun()
    
    with col4:
        if st.button("🔄 Reset Workflow", disabled=workflow_manager.workflow_status == "running"):
            workflow_manager.reset_workflow()
            st.rerun()
    
    # Overall workflow status
    st.markdown("### 📊 Workflow Status")
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        if workflow_manager.workflow_status == "idle":
            st.info("🟡 Status: Idle")
        elif workflow_manager.workflow_status == "running":
            st.success("🟢 Status: Running")
        elif workflow_manager.workflow_status == "paused":
            st.warning("🟡 Status: Paused")
        elif workflow_manager.workflow_status == "completed":
            st.success("🟢 Status: Completed")
        elif workflow_manager.workflow_status == "failed":
            st.error("🔴 Status: Failed")
        else:
            st.info("⚪ Status: Stopped")
    
    with col2:
        progress = workflow_manager.get_workflow_progress()
        st.metric("Overall Progress", f"{progress:.1f}%")
    
    with col3:
        if workflow_manager.start_time:
            duration = datetime.now() - workflow_manager.start_time
            st.metric("Duration", f"{duration.total_seconds():.1f}s")
    
    with col4:
        completed_steps = sum(1 for step in workflow_manager.workflow_steps if step.status == "completed")
        total_steps = len(workflow_manager.workflow_steps)
        st.metric("Steps Completed", f"{completed_steps}/{total_steps}")
    
    # Workflow progress bar
    if workflow_manager.workflow_status in ["running", "paused", "completed"]:
        progress = workflow_manager.get_workflow_progress()
        # Ensure progress is between 0 and 100 before converting to 0-1 range
        progress = max(0.0, min(100.0, progress))
        st.progress(progress / 100)
        
        # Current step indicator
        current_step = workflow_manager.get_current_step()
        if current_step and current_step.status == "running":
            st.info(f"🔄 Current Step: {current_step.name} ({current_step.progress:.1f}%)")
    
    # Agent status dashboard
    st.markdown("### 🤖 Agent Status Dashboard")
    
    # Validate agent status consistency before display
    workflow_manager.validate_agent_status()
    
    agent_cols = st.columns(4)
    
    for i, (agent_id, agent) in enumerate(workflow_manager.agents.items()):
        with agent_cols[i]:
            # Agent status card
            if agent.status == "idle":
                status_color = "🟡"
                status_text = "Idle"
            elif agent.status == "running":
                status_color = "🟢"
                status_text = "Running"
            elif agent.status == "completed":
                status_color = "✅"
                status_text = "Completed"
            elif agent.status == "failed":
                status_color = "🔴"
                status_text = "Failed"
            else:
                status_color = "⚪"
                status_text = "Unknown"
            
            st.markdown(f"**{agent.name}**")
            st.markdown(f"{status_color} {status_text}")
            
            if agent.current_task:
                st.caption(f"Task: {agent.current_task}")
            
            if agent.total_tasks > 0:
                progress = (agent.tasks_completed / agent.total_tasks) * 100
                # Ensure progress is between 0 and 100 before converting to 0-1 range
                progress = max(0.0, min(100.0, progress))
                st.progress(progress / 100)
                st.caption(f"Tasks: {agent.tasks_completed}/{agent.total_tasks}")
    
    # Debug information (can be toggled)
    if st.checkbox("🔧 Show Debug Information", value=False):
        st.markdown("### 🔍 Debug Information")
        
        debug_cols = st.columns(2)
        
        with debug_cols[0]:
            st.markdown("**Agent Details:**")
            for agent_id, agent in workflow_manager.agents.items():
                st.markdown(f"""
                **{agent.name}:**
                - Status: {agent.status}
                - Progress: {agent.progress:.1f}%
                - Tasks: {agent.tasks_completed}/{agent.total_tasks}
                - Current Task: {agent.current_task or 'None'}
                """)
        
        with debug_cols[1]:
            st.markdown("**Workflow Steps:**")
            for step in workflow_manager.workflow_steps:
                st.markdown(f"""
                **{step.name}:**
                - Status: {step.status}
                - Progress: {step.progress:.1f}%
                - Duration: {step.duration or 'N/A'}s
                """)
    
    # Workflow steps visualization
    st.markdown("### 📋 Workflow Steps")
    
    for step in workflow_manager.workflow_steps:
        col1, col2, col3, col4 = st.columns([2, 1, 1, 1])
        
        with col1:
            st.markdown(f"**{step.name}**")
            st.caption(step.description)
        
        with col2:
            if step.status == "pending":
                st.markdown("⏳ Pending")
            elif step.status == "running":
                st.markdown("🔄 Running")
            elif step.status == "completed":
                st.markdown("✅ Completed")
            elif step.status == "failed":
                st.markdown("❌ Failed")
            else:
                st.markdown("⏭️ Skipped")
        
        with col3:
            st.markdown(f"{step.progress:.1f}%")
        
        with col4:
            if step.duration:
                st.markdown(f"{step.duration:.1f}s")
            elif step.start_time and step.status == "running":
                duration = (datetime.now() - step.start_time).total_seconds()
                st.markdown(f"{duration:.1f}s")
            else:
                st.markdown("-")
    
    # Workflow visualization
    if workflow_manager.workflow_status in ["running", "completed"]:
        st.markdown("### 📈 Workflow Visualization")
        
        try:
            fig = create_workflow_visualization(workflow_manager)
            st.plotly_chart(fig, use_container_width=True)
        except Exception as e:
            st.warning(f"Could not generate workflow visualization: {str(e)}")
    
    # Real-time metrics
    if st.session_state.performance_monitor:
        st.markdown("### 📊 Real-time System Metrics")
        
        realtime = st.session_state.performance_monitor.get_realtime_metrics()
        
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            cpu_usage = realtime.get('system', {}).get('cpu_usage_percent', 0)
            st.metric("CPU Usage", f"{cpu_usage:.1f}%")
        
        with col2:
            memory_usage = realtime.get('system', {}).get('memory_usage_percent', 0)
            st.metric("Memory Usage", f"{memory_usage:.1f}%")
        
        with col3:
            recent_executions = realtime.get('performance', {}).get('recent_executions', 0)
            st.metric("Recent Executions", recent_executions)
        
        with col4:
            avg_execution_time = realtime.get('performance', {}).get('average_execution_time', 0)
            st.metric("Avg Execution Time", f"{avg_execution_time:.2f}s")
    
    # Execution log
    if workflow_manager.execution_log:
        st.markdown("### 📝 Execution Log")
        
        with st.expander("View execution log"):
            for log_entry in workflow_manager.execution_log[-10:]:  # Show last 10 entries
                # Handle both old dictionary format and new string format
                if isinstance(log_entry, dict):
                    # Old format: dictionary with timestamp, level, message
                    timestamp = log_entry.get('timestamp', '')[:19]
                    level = log_entry.get('level', 'info')
                    message = log_entry.get('message', '')
                else:
                    # New format: string with "[timestamp] LEVEL: message"
                    log_entry_str = str(log_entry)
                    if ']' in log_entry_str and ':' in log_entry_str:
                        try:
                            # Parse "[timestamp] LEVEL: message" format
                            timestamp_part = log_entry_str.split(']')[0] + ']'
                            timestamp = timestamp_part[1:-1]  # Remove brackets
                            remaining = log_entry_str.split(']', 1)[1].strip()
                            if ':' in remaining:
                                level_part, message = remaining.split(':', 1)
                                level = level_part.strip().lower()
                                message = message.strip()
                            else:
                                level = 'info'
                                message = remaining
                        except:
                            # Fallback if parsing fails
                            timestamp = datetime.now().strftime("%H:%M:%S")
                            level = 'info'
                            message = log_entry_str
                    else:
                        # Simple string format
                        timestamp = datetime.now().strftime("%H:%M:%S")
                        level = 'info'
                        message = log_entry_str
                
                if level == "info":
                    st.info(f"**{timestamp}** - {message}")
                elif level == "warning":
                    st.warning(f"**{timestamp}** - {message}")
                elif level == "error":
                    st.error(f"**{timestamp}** - {message}")
                else:
                    st.write(f"**{timestamp}** - {message}")
    
    # Error handling and recovery
    if workflow_manager.workflow_status == "failed":
        st.markdown("### ❌ Error Recovery")
        
        st.error("Workflow execution failed. Please review the errors below:")
        
        # Show failed steps
        failed_steps = [step for step in workflow_manager.workflow_steps if step.status == "failed"]
        for step in failed_steps:
            with st.expander(f"Failed: {step.name}"):
                st.error(f"Error: {step.error_message}")
                st.info("**Recovery Options:**")
                st.markdown("1. **Retry Step**: Attempt to re-run the failed step")
                st.markdown("2. **Skip Step**: Continue with remaining steps")
                st.markdown("3. **Restart Workflow**: Begin from the beginning")
                
                col1, col2, col3 = st.columns(3)
                with col1:
                    if st.button(f"Retry {step.name}", key=f"retry_{step.step_id}"):
                        step.status = "pending"
                        step.error_message = None
                        st.rerun()
                
                with col2:
                    if st.button(f"Skip {step.name}", key=f"skip_{step.step_id}"):
                        step.status = "skipped"
                        st.rerun()
                
                with col3:
                    if st.button("Restart Workflow", key="restart_workflow"):
                        st.session_state.workflow_manager = AgentWorkflowManager()
                        st.rerun()
    
    # Workflow completion handling
    if workflow_manager.workflow_status == "completed":
        st.success("🎉 Workflow completed successfully!")
        
        # Calculate execution time
        if workflow_manager.start_time and workflow_manager.end_time:
            total_time = (workflow_manager.end_time - workflow_manager.start_time).total_seconds()
            st.metric("Total Execution Time", f"{total_time:.2f} seconds")
        
        # Create result data
        result = {
            "customer_id": app_data['customer_id'],
            "analysis_time": datetime.now().isoformat(),
            "status": "completed",
            "risk_score": random.randint(60, 95),
            "risk_level": random.choice(["Low", "Medium", "High"]),
            "approval_probability": random.uniform(0.7, 0.98),
            "recommended_rate": random.uniform(3.5, 8.5),
            "recommended_amount": app_data['loan_amount'],
            "recommendation": random.choice(["Approve", "Approve with Conditions", "Deny"]),
            "execution_time": total_time if workflow_manager.start_time and workflow_manager.end_time else 0,
            "agents_used": len(workflow_manager.agents),
            "tasks_completed": sum(agent.tasks_completed for agent in workflow_manager.agents.values()),
            "application_data": app_data,
            "workflow_data": {
                "steps_completed": len([s for s in workflow_manager.workflow_steps if s.status == "completed"]),
                "total_steps": len(workflow_manager.workflow_steps),
                "agent_status": {k: v.status for k, v in workflow_manager.agents.items()}
            }
        }
        
        # Store result
        if 'analysis_results' not in st.session_state:
            st.session_state.analysis_results = []
        st.session_state.analysis_results.append(result)
        
        # Navigation options
        col1, col2 = st.columns(2)
        
        with col1:
            if st.button("📊 View Results", type="primary"):
                st.session_state.current_page = 'Results'
                st.rerun()
        
        with col2:
            if st.button("🔄 Process Another Application"):
                st.session_state.current_page = 'Application'
                st.session_state.current_analysis = None
                st.session_state.workflow_manager = AgentWorkflowManager()
                st.rerun()
    
    # Processing tips
    st.markdown("### 💡 Processing Tips")
    
    st.info("""
    **For optimal workflow execution:**
    - Monitor agent status and system resources
    - Review execution log for detailed progress
    - Use pause/stop controls if needed
    - Check error recovery options for failed steps
    - View workflow visualization for timeline analysis
    """) 