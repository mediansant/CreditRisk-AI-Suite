#!/usr/bin/env python3
"""
Credit Risk CrewAI Integration
Implements CrewAI framework with specialized credit risk agents and direct database connections
"""

import json
import logging
import time
import asyncio
from typing import Dict, List, Any, Optional, Union
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
import threading
from concurrent.futures import ThreadPoolExecutor, as_completed
import traceback

# CrewAI imports
from crewai import Crew, Agent, Task, Process
from crewai.tools import BaseTool

# Local imports
from .database_tools import (
    DatabaseToolManager, DatabaseConfig, CustomerDatabaseTool, MarketDatabaseTool,
    DatabaseResult, create_database_config
)
from .base_agent import (
    BaseAgent, AgentConfig, AgentContext, AgentResult, AgentStatus,
    AgentPriority, create_agent_context
)
from .credit_agents import (
    DataCollectionAgent, RiskAnalysisAgent, DocumentationAgent, ReportingAgent,
    CreditAgentOrchestrator
)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class CrewTaskType(Enum):
    """Crew task types"""
    DATA_COLLECTION = "data_collection"
    RISK_ANALYSIS = "risk_analysis"
    DOCUMENTATION = "documentation"
    REPORTING = "reporting"
    PORTFOLIO_ANALYSIS = "portfolio_analysis"
    MARKET_ANALYSIS = "market_analysis"

@dataclass
class CrewTaskDefinition:
    """Crew task definition"""
    task_id: str
    task_type: CrewTaskType
    description: str
    agent_id: str
    dependencies: List[str] = field(default_factory=list)
    priority: int = 1
    timeout: int = 300  # 5 minutes
    retry_count: int = 3
    metadata: Dict[str, Any] = field(default_factory=dict)

@dataclass
class CrewExecutionResult:
    """Crew execution result"""
    success: bool
    task_results: Dict[str, Any]
    execution_time: float
    error_message: Optional[str] = None
    performance_metrics: Dict[str, Any] = field(default_factory=dict)
    metadata: Dict[str, Any] = field(default_factory=dict)

class CrewCustomerTool(BaseTool):
    """Customer database tool for CrewAI"""
    
    database_tool: Any = None
    
    def __init__(self, database_tool):
        super().__init__(
            name="customer_database_tool",
            description="Tool for accessing customer database information"
        )
        self.database_tool = database_tool
    
    def _run(self, customer_id: str = "", action: str = "get_customer", **kwargs) -> str:
        """Execute customer database operations"""
        try:
            if action == "get_customer" and customer_id:
                result = self.database_tool.get_customer(customer_id)
            elif action == "financial_summary" and customer_id:
                result = self.database_tool.get_financial_summary(customer_id)
            elif action == "search_customers":
                result = self.database_tool.search_customers(**kwargs)
            else:
                result = DatabaseResult(success=False, error=f"Invalid action: {action}")
            
            if result.success:
                return json.dumps(result.data, default=str)
            else:
                return f"Error: {result.error}"
                
        except Exception as e:
            logger.error(f"Customer database tool error: {str(e)}")
            return f"Error: {str(e)}"

class CrewMarketTool(BaseTool):
    """Market database tool for CrewAI"""
    
    database_tool: Any = None
    
    def __init__(self, database_tool):
        super().__init__(
            name="market_database_tool",
            description="Tool for accessing market database information"
        )
        self.database_tool = database_tool
    
    def _run(self, action: str = "get_market_data", **kwargs) -> str:
        """Execute market database operations"""
        try:
            if action == "get_market_data":
                result = self.database_tool.get_current_market_data()
            elif action == "calculate_benchmark":
                result = self.database_tool.calculate_risk_benchmark(
                    kwargs.get("loan_type", "personal"),
                    kwargs.get("risk_score", 650),
                    kwargs.get("loan_amount", 10000),
                    kwargs.get("term_months", 12)
                )
            else:
                result = DatabaseResult(success=False, error=f"Invalid action: {action}")
            
            if result.success:
                return json.dumps(result.data, default=str)
            else:
                return f"Error: {result.error}"
                
        except Exception as e:
            logger.error(f"Market database tool error: {str(e)}")
            return f"Error: {str(e)}"

class CreditRiskCrew:
    """Credit Risk CrewAI Integration"""
    
    def __init__(self, database_config: Optional[DatabaseConfig] = None):
        """Initialize the credit risk crew"""
        self.logger = logger
        self.database_config = database_config or create_database_config()
        self.database_manager = DatabaseToolManager(self.database_config.__dict__ if self.database_config else None)
        
        # Initialize agents
        self.crew_agents = {}
        self.crew_tasks = {}
        self.execution_history = []
        self.performance_metrics = {}
        
        # Setup agents and tools
        self._setup_agents()
        self._setup_tools()
        
        self.logger.info("CreditRiskCrew initialized successfully")
    
    def _setup_agents(self):
        """Setup CrewAI agents"""
        try:
            # Data Collection Agent
            data_collector = Agent(
                role="Data Collection Specialist",
                goal="Collect comprehensive customer and market data for credit risk analysis",
                backstory="""You are an experienced data collection specialist with expertise in 
                financial data gathering. You have access to customer databases and market data 
                sources. Your role is to gather all necessary information for credit risk assessment.""",
                verbose=True,
                allow_delegation=False,
                tools=[CrewCustomerTool(self.database_manager.customer_tool)]
            )
            
            # Risk Analysis Agent
            risk_analyst = Agent(
                role="Credit Risk Analyst",
                goal="Analyze credit risk based on collected data and market conditions",
                backstory="""You are a senior credit risk analyst with 15+ years of experience in 
                financial risk assessment. You specialize in evaluating creditworthiness, calculating 
                risk scores, and determining loan terms. You use sophisticated models and market data 
                to make informed decisions.""",
                verbose=True,
                allow_delegation=False,
                tools=[
                    CrewCustomerTool(self.database_manager.customer_tool),
                    CrewMarketTool(self.database_manager.market_tool)
                ]
            )
            
            # Documentation Agent
            documenter = Agent(
                role="Documentation Specialist",
                goal="Create comprehensive documentation for credit risk assessments",
                backstory="""You are a documentation specialist who excels at creating clear, 
                comprehensive reports. You understand regulatory requirements and ensure all 
                documentation meets compliance standards. You work closely with analysts to 
                document findings and recommendations.""",
                verbose=True,
                allow_delegation=False,
                tools=[]
            )
            
            # Reporting Agent
            reporter = Agent(
                role="Reporting Specialist",
                goal="Generate actionable reports and recommendations for stakeholders",
                backstory="""You are a reporting specialist who transforms complex data into 
                actionable insights. You create executive summaries, risk reports, and 
                recommendations that help stakeholders make informed decisions. You have 
                expertise in data visualization and business communication.""",
                verbose=True,
                allow_delegation=False,
                tools=[]
            )
            
            self.crew_agents = {
                "data_collector": data_collector,
                "risk_analyst": risk_analyst,
                "documenter": documenter,
                "reporter": reporter
            }
            
            self.logger.info(f"Setup {len(self.crew_agents)} CrewAI agents")
            
        except Exception as e:
            self.logger.error(f"Error setting up agents: {str(e)}")
            raise
    
    def _setup_tools(self):
        """Setup additional tools for agents"""
        try:
            # Add market data tool to data collector
            if self.crew_agents["data_collector"].tools is None:
                self.crew_agents["data_collector"].tools = []
            self.crew_agents["data_collector"].tools.append(
                CrewMarketTool(self.database_manager.market_tool)
            )
            
            # Add customer tool to documenter and reporter
            if self.crew_agents["documenter"].tools is None:
                self.crew_agents["documenter"].tools = []
            self.crew_agents["documenter"].tools.append(
                CrewCustomerTool(self.database_manager.customer_tool)
            )
            
            if self.crew_agents["reporter"].tools is None:
                self.crew_agents["reporter"].tools = []
            self.crew_agents["reporter"].tools.append(
                CrewCustomerTool(self.database_manager.customer_tool)
            )
            
            self.logger.info("Additional tools configured for agents")
            
        except Exception as e:
            self.logger.error(f"Error setting up tools: {str(e)}")
            raise
    
    def create_credit_analysis_tasks(self, customer_id: str, loan_amount: float = 10000, 
                                   loan_type: str = "personal") -> List[Task]:
        """Create tasks for credit analysis workflow"""
        try:
            tasks = []
            
            # Task 1: Collect Customer Data
            collect_data_task = Task(
                description=f"""Collect comprehensive data for customer {customer_id}:
                1. Retrieve customer profile and financial information
                2. Gather market data and current economic indicators
                3. Collect any additional relevant data sources
                4. Validate data quality and completeness
                
                Customer ID: {customer_id}
                Loan Amount: ${loan_amount:,.2f}
                Loan Type: {loan_type}
                
                Provide a detailed summary of all collected data.""",
                agent=self.crew_agents["data_collector"],
                expected_output="""A comprehensive data collection report including:
                - Customer profile and financial summary
                - Market data and economic indicators
                - Data quality assessment
                - Any missing or incomplete information"""
            )
            tasks.append(collect_data_task)
            
            # Task 2: Analyze Credit Risk
            analyze_risk_task = Task(
                description=f"""Analyze credit risk for customer {customer_id}:
                1. Evaluate customer's creditworthiness based on collected data
                2. Calculate risk score and determine risk level
                3. Assess loan terms and interest rates
                4. Consider market conditions and economic factors
                5. Provide risk assessment with confidence level
                
                Use the data collected by the Data Collection Specialist.
                Consider loan amount: ${loan_amount:,.2f} and type: {loan_type}""",
                agent=self.crew_agents["risk_analyst"],
                expected_output="""A detailed risk analysis report including:
                - Credit risk assessment and score
                - Risk level classification
                - Recommended loan terms and interest rates
                - Confidence level and reasoning
                - Risk factors and mitigation strategies"""
            )
            tasks.append(analyze_risk_task)
            
            # Task 3: Create Documentation
            document_task = Task(
                description=f"""Create comprehensive documentation for customer {customer_id}:
                1. Document the data collection process and sources
                2. Record the risk analysis methodology and findings
                3. Create compliance documentation
                4. Prepare audit trail and supporting evidence
                5. Ensure regulatory compliance
                
                Use the data collection and risk analysis results.""",
                agent=self.crew_agents["documenter"],
                expected_output="""Complete documentation package including:
                - Data collection documentation
                - Risk analysis methodology
                - Compliance documentation
                - Audit trail and evidence
                - Regulatory compliance checklist"""
            )
            tasks.append(document_task)
            
            # Task 4: Generate Report
            report_task = Task(
                description=f"""Generate final report for customer {customer_id}:
                1. Create executive summary of findings
                2. Provide actionable recommendations
                3. Include risk assessment and loan terms
                4. Add visualizations and data summaries
                5. Prepare stakeholder communication
                
                Synthesize all previous work into a comprehensive report.""",
                agent=self.crew_agents["reporter"],
                expected_output="""Final comprehensive report including:
                - Executive summary
                - Risk assessment and recommendations
                - Loan terms and conditions
                - Data visualizations
                - Stakeholder recommendations"""
            )
            tasks.append(report_task)
            
            self.logger.info(f"Created {len(tasks)} tasks for customer {customer_id}")
            return tasks
            
        except Exception as e:
            self.logger.error(f"Error creating tasks: {str(e)}")
            raise
    
    def execute_credit_analysis(self, customer_id: str, loan_amount: float = 10000, 
                              loan_type: str = "personal") -> CrewExecutionResult:
        """Execute complete credit analysis workflow"""
        start_time = time.time()
        
        try:
            self.logger.info(f"Starting credit analysis for customer {customer_id}")
            
            # Create tasks
            tasks = self.create_credit_analysis_tasks(customer_id, loan_amount, loan_type)
            
            # Create crew
            crew = Crew(
                agents=list(self.crew_agents.values()),
                tasks=tasks,
                verbose=True,
                process=Process.sequential
            )
            
            # Execute crew
            result = crew.kickoff()
            
            # Calculate execution time
            execution_time = time.time() - start_time
            
            # Create execution result
            execution_result = CrewExecutionResult(
                success=True,
                task_results={"crew_result": result},
                execution_time=execution_time,
                performance_metrics={
                    "total_time": execution_time,
                    "tasks_completed": len(tasks),
                    "agents_used": len(self.crew_agents)
                },
                metadata={
                    "customer_id": customer_id,
                    "loan_amount": loan_amount,
                    "loan_type": loan_type,
                    "timestamp": datetime.now().isoformat()
                }
            )
            
            # Log execution
            self.execution_history.append(execution_result)
            
            self.logger.info(f"Credit analysis completed successfully in {execution_time:.2f} seconds")
            return execution_result
            
        except Exception as e:
            execution_time = time.time() - start_time
            error_msg = f"Error in credit analysis: {str(e)}"
            self.logger.error(error_msg)
            
            return CrewExecutionResult(
                success=False,
                task_results={},
                execution_time=execution_time,
                error_message=error_msg,
                metadata={
                    "customer_id": customer_id,
                    "loan_amount": loan_amount,
                    "loan_type": loan_type,
                    "timestamp": datetime.now().isoformat()
                }
            )
    
    def get_performance_metrics(self) -> Dict[str, Any]:
        """Get performance metrics from execution history"""
        if not self.execution_history:
            return {"message": "No executions recorded"}
        
        successful_executions = [ex for ex in self.execution_history if ex.success]
        failed_executions = [ex for ex in self.execution_history if not ex.success]
        
        metrics = {
            "total_executions": len(self.execution_history),
            "successful_executions": len(successful_executions),
            "failed_executions": len(failed_executions),
            "success_rate": len(successful_executions) / len(self.execution_history) * 100,
            "average_execution_time": sum(ex.execution_time for ex in successful_executions) / len(successful_executions) if successful_executions else 0,
            "total_execution_time": sum(ex.execution_time for ex in self.execution_history),
            "recent_executions": [
                {
                    "timestamp": ex.metadata.get("timestamp"),
                    "customer_id": ex.metadata.get("customer_id"),
                    "success": ex.success,
                    "execution_time": ex.execution_time
                }
                for ex in self.execution_history[-5:]  # Last 5 executions
            ]
        }
        
        return metrics
    
    def get_execution_logs(self, limit: int = 10) -> List[Dict[str, Any]]:
        """Get recent execution logs"""
        logs = []
        for execution in self.execution_history[-limit:]:
            log_entry = {
                "timestamp": execution.metadata.get("timestamp"),
                "customer_id": execution.metadata.get("customer_id"),
                "success": execution.success,
                "execution_time": execution.execution_time,
                "error_message": execution.error_message,
                "performance_metrics": execution.performance_metrics
            }
            logs.append(log_entry)
        
        return logs

def main():
    """Main function for testing"""
    print("=== Credit Risk CrewAI Integration Test ===")
    
    try:
        # Initialize crew
        crew = CreditRiskCrew()
        print("✅ Crew initialized successfully")
        
        # Test customer ID (use a known customer from database)
        test_customer_id = "CUST001"
        
        # Execute credit analysis
        print(f"\n🚀 Executing credit analysis for customer {test_customer_id}...")
        result = crew.execute_credit_analysis(
            customer_id=test_customer_id,
            loan_amount=15000,
            loan_type="personal"
        )
        
        if result.success:
            print(f"✅ Credit analysis completed successfully!")
            print(f"   Execution time: {result.execution_time:.2f} seconds")
            print(f"   Tasks completed: {result.performance_metrics.get('tasks_completed', 0)}")
            print(f"   Agents used: {result.performance_metrics.get('agents_used', 0)}")
            
            # Show crew result
            crew_result = result.task_results.get("crew_result", "")
            print(f"\n📋 Crew Result Preview:")
            print(str(crew_result)[:500] + "..." if len(str(crew_result)) > 500 else str(crew_result))
        else:
            print(f"❌ Credit analysis failed: {result.error_message}")
        
        # Show performance metrics
        print(f"\n📊 Performance Metrics:")
        metrics = crew.get_performance_metrics()
        for key, value in metrics.items():
            if key != "recent_executions":
                print(f"   {key}: {value}")
        
        # Show recent logs
        print(f"\n📝 Recent Execution Logs:")
        logs = crew.get_execution_logs(limit=3)
        for log in logs:
            status = "✅" if log["success"] else "❌"
            print(f"   {status} {log['timestamp']} - Customer {log['customer_id']} - {log['execution_time']:.2f}s")
        
    except Exception as e:
        print(f"❌ Error: {str(e)}")
        traceback.print_exc()

if __name__ == "__main__":
    main() 