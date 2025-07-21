#!/usr/bin/env python3
"""
Task Definitions and Agent Coordination
Defines tasks, dependencies, and workflow orchestration for credit agents
"""

import asyncio
import time
import json
import logging
from typing import Dict, List, Any, Optional, Union, Callable
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
from concurrent.futures import ThreadPoolExecutor, as_completed

from .base_agent import AgentContext, AgentResult, AgentStatus
from .credit_agents import (
    DataCollectionAgent, RiskAnalysisAgent, DocumentationAgent, ReportingAgent,
    CreditAgentOrchestrator
)

class TaskStatus(Enum):
    """Task execution status"""
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"
    RETRYING = "retrying"

class TaskPriority(Enum):
    """Task priority levels"""
    LOW = "low"
    NORMAL = "normal"
    HIGH = "high"
    CRITICAL = "critical"

class TaskType(Enum):
    """Task types for credit workflow"""
    DATA_COLLECTION = "data_collection"
    RISK_ANALYSIS = "risk_analysis"
    DOCUMENTATION = "documentation"
    REPORTING = "reporting"
    VALIDATION = "validation"
    APPROVAL = "approval"

@dataclass
class TaskDefinition:
    """Definition of a workflow task"""
    task_id: str
    task_type: TaskType
    name: str
    description: str
    priority: TaskPriority = TaskPriority.NORMAL
    timeout: int = 300  # seconds
    max_retries: int = 3
    retry_delay: int = 30  # seconds
    dependencies: List[str] = field(default_factory=list)
    required_agents: List[str] = field(default_factory=list)
    validation_rules: Dict[str, Any] = field(default_factory=dict)
    success_criteria: Dict[str, Any] = field(default_factory=dict)
    metadata: Dict[str, Any] = field(default_factory=dict)

@dataclass
class TaskExecution:
    """Task execution instance"""
    task_definition: TaskDefinition
    context: AgentContext
    status: TaskStatus = TaskStatus.PENDING
    start_time: Optional[datetime] = None
    end_time: Optional[datetime] = None
    result: Optional[AgentResult] = None
    error: Optional[str] = None
    retry_count: int = 0
    execution_log: List[Dict[str, Any]] = field(default_factory=list)
    dependencies_completed: List[str] = field(default_factory=list)

class BaseTask:
    """Base class for all tasks"""
    
    def __init__(self, task_definition: TaskDefinition):
        self.definition = task_definition
        self.logger = logging.getLogger(f"Task.{task_definition.task_id}")
    
    def validate_prerequisites(self, context: AgentContext) -> bool:
        """Validate task prerequisites"""
        self.logger.info(f"Validating prerequisites for task: {self.definition.name}")
        return True
    
    def execute(self, context: AgentContext, **kwargs) -> AgentResult:
        """Execute the task"""
        raise NotImplementedError("Subclasses must implement execute method")
    
    def validate_result(self, result: AgentResult) -> bool:
        """Validate task result"""
        if not result.success:
            return False
        
        # Check success criteria
        for criterion, expected_value in self.definition.success_criteria.items():
            if criterion in result.data:
                if result.data[criterion] != expected_value:
                    self.logger.warning(f"Success criterion failed: {criterion}")
                    return False
        
        return True
    
    def cleanup(self, context: AgentContext):
        """Cleanup after task execution"""
        self.logger.info(f"Cleaning up task: {self.definition.name}")

class DataCollectionTask(BaseTask):
    """Data collection task"""
    
    def __init__(self, customer_id: str, collection_scope: str = "comprehensive"):
        task_def = TaskDefinition(
            task_id=f"data_collection_{customer_id}_{int(time.time())}",
            task_type=TaskType.DATA_COLLECTION,
            name="Customer Data Collection",
            description=f"Collect comprehensive data for customer {customer_id}",
            priority=TaskPriority.HIGH,
            timeout=600,
            max_retries=3,
            required_agents=["data_collection_agent"],
            success_criteria={
                "data_sources_count": 3,
                "collection_quality": 0.8
            },
            metadata={
                "customer_id": customer_id,
                "collection_scope": collection_scope
            }
        )
        super().__init__(task_def)
        self.customer_id = customer_id
        self.collection_scope = collection_scope
    
    def validate_prerequisites(self, context: AgentContext) -> bool:
        """Validate data collection prerequisites"""
        # Check if customer ID is provided
        if not self.customer_id:
            self.logger.error("Customer ID is required for data collection")
            return False
        
        # Check if required agents are available
        if "data_collection_agent" not in context.metadata.get("available_agents", []):
            self.logger.error("Data collection agent not available")
            return False
        
        return True
    
    def execute(self, context: AgentContext, **kwargs) -> AgentResult:
        """Execute data collection task"""
        self.logger.info(f"Executing data collection for customer: {self.customer_id}")
        
        # Get the data collection agent
        data_agent = kwargs.get('data_agent')
        if not data_agent:
            return AgentResult(
                success=False,
                error="Data collection agent not provided",
                status=AgentStatus.FAILED,
                context=context
            )
        
        # Execute data collection
        result = data_agent.run(context, self.customer_id, self.collection_scope)
        
        # Validate result
        if result.success:
            data_sources = result.data.get('data_sources', [])
            collection_summary = result.data.get('collection_summary', {})
            
            # Check success criteria
            if len(data_sources) >= self.definition.success_criteria['data_sources_count']:
                self.logger.info(f"Data collection successful: {len(data_sources)} sources")
            else:
                self.logger.warning(f"Insufficient data sources: {len(data_sources)}")
                result.success = False
                result.error = f"Insufficient data sources collected: {len(data_sources)}"
        
        return result

class RiskAnalysisTask(BaseTask):
    """Risk analysis task"""
    
    def __init__(self, customer_data: Dict[str, Any], loan_details: Dict[str, Any]):
        task_def = TaskDefinition(
            task_id=f"risk_analysis_{int(time.time())}",
            task_type=TaskType.RISK_ANALYSIS,
            name="Credit Risk Analysis",
            description="Analyze credit risk for loan application",
            priority=TaskPriority.CRITICAL,
            timeout=900,
            max_retries=2,
            dependencies=["data_collection"],
            required_agents=["risk_analysis_agent"],
            success_criteria={
                "risk_level": "defined",
                "confidence_level": 0.7
            },
            metadata={
                "loan_amount": loan_details.get('amount'),
                "loan_type": loan_details.get('type')
            }
        )
        super().__init__(task_def)
        self.customer_data = customer_data
        self.loan_details = loan_details
    
    def validate_prerequisites(self, context: AgentContext) -> bool:
        """Validate risk analysis prerequisites"""
        # Check if customer data is available
        if not self.customer_data:
            self.logger.error("Customer data is required for risk analysis")
            return False
        
        # Check if loan details are provided
        if not self.loan_details.get('amount') or not self.loan_details.get('type'):
            self.logger.error("Loan amount and type are required for risk analysis")
            return False
        
        return True
    
    def execute(self, context: AgentContext, **kwargs) -> AgentResult:
        """Execute risk analysis task"""
        self.logger.info("Executing risk analysis")
        
        # Get the risk analysis agent
        risk_agent = kwargs.get('risk_agent')
        if not risk_agent:
            return AgentResult(
                success=False,
                error="Risk analysis agent not provided",
                status=AgentStatus.FAILED,
                context=context
            )
        
        # Execute risk analysis
        result = risk_agent.run(
            context, 
            self.customer_data, 
            self.loan_details.get('amount'), 
            self.loan_details.get('type')
        )
        
        # Validate result
        if result.success:
            risk_level = result.data.get('risk_level')
            confidence_level = result.data.get('confidence_level', 0)
            
            # Check success criteria
            if risk_level and confidence_level >= self.definition.success_criteria['confidence_level']:
                self.logger.info(f"Risk analysis successful: {risk_level} risk, {confidence_level:.2%} confidence")
            else:
                self.logger.warning(f"Risk analysis quality insufficient: {confidence_level:.2%} confidence")
                result.success = False
                result.error = f"Insufficient confidence level: {confidence_level:.2%}"
        
        return result

class DocumentationTask(BaseTask):
    """Documentation task"""
    
    def __init__(self, customer_data: Dict[str, Any], risk_assessment: Dict[str, Any], 
               loan_details: Dict[str, Any]):
        task_def = TaskDefinition(
            task_id=f"documentation_{int(time.time())}",
            task_type=TaskType.DOCUMENTATION,
            name="Documentation Creation",
            description="Create comprehensive documentation package",
            priority=TaskPriority.HIGH,
            timeout=600,
            max_retries=2,
            dependencies=["data_collection", "risk_analysis"],
            required_agents=["documentation_agent"],
            success_criteria={
                "compliance_status": "Compliant",
                "sections_count": 4
            },
            metadata={
                "loan_type": loan_details.get('type'),
                "risk_level": risk_assessment.get('risk_level')
            }
        )
        super().__init__(task_def)
        self.customer_data = customer_data
        self.risk_assessment = risk_assessment
        self.loan_details = loan_details
    
    def validate_prerequisites(self, context: AgentContext) -> bool:
        """Validate documentation prerequisites"""
        # Check if customer data is available
        if not self.customer_data:
            self.logger.error("Customer data is required for documentation")
            return False
        
        # Check if risk assessment is available
        if not self.risk_assessment:
            self.logger.error("Risk assessment is required for documentation")
            return False
        
        return True
    
    def execute(self, context: AgentContext, **kwargs) -> AgentResult:
        """Execute documentation task"""
        self.logger.info("Executing documentation creation")
        
        # Get the documentation agent
        doc_agent = kwargs.get('doc_agent')
        if not doc_agent:
            return AgentResult(
                success=False,
                error="Documentation agent not provided",
                status=AgentStatus.FAILED,
                context=context
            )
        
        # Execute documentation creation
        result = doc_agent.run(
            context, 
            self.customer_data, 
            self.risk_assessment, 
            self.loan_details
        )
        
        # Validate result
        if result.success:
            compliance_status = result.data.get('compliance_status')
            sections_count = len(result.data.get('sections', {}))
            
            # Check success criteria
            if (compliance_status == self.definition.success_criteria['compliance_status'] and
                sections_count >= self.definition.success_criteria['sections_count']):
                self.logger.info(f"Documentation successful: {compliance_status}, {sections_count} sections")
            else:
                self.logger.warning(f"Documentation quality insufficient: {compliance_status}, {sections_count} sections")
                result.success = False
                result.error = f"Documentation quality insufficient: {compliance_status}"
        
        return result

class ReportingTask(BaseTask):
    """Reporting task"""
    
    def __init__(self, customer_data: Dict[str, Any], risk_assessment: Dict[str, Any], 
               documentation: Dict[str, Any], report_type: str = "comprehensive"):
        task_def = TaskDefinition(
            task_id=f"reporting_{int(time.time())}",
            task_type=TaskType.REPORTING,
            name="Report Generation",
            description="Generate comprehensive credit report",
            priority=TaskPriority.NORMAL,
            timeout=300,
            max_retries=2,
            dependencies=["data_collection", "risk_analysis", "documentation"],
            required_agents=["reporting_agent"],
            success_criteria={
                "recommendations_count": 1,
                "executive_summary": "complete"
            },
            metadata={
                "report_type": report_type,
                "risk_level": risk_assessment.get('risk_level')
            }
        )
        super().__init__(task_def)
        self.customer_data = customer_data
        self.risk_assessment = risk_assessment
        self.documentation = documentation
        self.report_type = report_type
    
    def validate_prerequisites(self, context: AgentContext) -> bool:
        """Validate reporting prerequisites"""
        # Check if all required data is available
        if not all([self.customer_data, self.risk_assessment, self.documentation]):
            self.logger.error("Customer data, risk assessment, and documentation are required for reporting")
            return False
        
        return True
    
    def execute(self, context: AgentContext, **kwargs) -> AgentResult:
        """Execute reporting task"""
        self.logger.info(f"Executing report generation: {self.report_type}")
        
        # Get the reporting agent
        report_agent = kwargs.get('report_agent')
        if not report_agent:
            return AgentResult(
                success=False,
                error="Reporting agent not provided",
                status=AgentStatus.FAILED,
                context=context
            )
        
        # Execute report generation
        result = report_agent.run(
            context, 
            self.customer_data, 
            self.risk_assessment, 
            self.documentation, 
            self.report_type
        )
        
        # Validate result
        if result.success:
            recommendations = result.data.get('recommendations', [])
            executive_summary = result.data.get('executive_summary', {})
            
            # Check success criteria
            if (len(recommendations) >= self.definition.success_criteria['recommendations_count'] and
                executive_summary):
                self.logger.info(f"Report generation successful: {len(recommendations)} recommendations")
            else:
                self.logger.warning(f"Report quality insufficient: {len(recommendations)} recommendations")
                result.success = False
                result.error = f"Insufficient recommendations: {len(recommendations)}"
        
        return result

class TaskCoordinator:
    """Coordinates task execution and dependencies"""
    
    def __init__(self):
        self.tasks: Dict[str, TaskExecution] = {}
        self.execution_order: List[str] = []
        self.logger = logging.getLogger("TaskCoordinator")
        self.executor = ThreadPoolExecutor(max_workers=4)
    
    def add_task(self, task: BaseTask, context: AgentContext) -> str:
        """Add a task to the coordinator"""
        task_execution = TaskExecution(
            task_definition=task.definition,
            context=context
        )
        
        self.tasks[task.definition.task_id] = task_execution
        self.logger.info(f"Added task: {task.definition.name} ({task.definition.task_id})")
        
        return task.definition.task_id
    
    def resolve_dependencies(self) -> List[List[str]]:
        """Resolve task dependencies and return execution order"""
        # Create dependency graph
        dependency_graph = {}
        for task_id, task_exec in self.tasks.items():
            dependency_graph[task_id] = task_exec.task_definition.dependencies
        
        # Topological sort
        execution_levels = []
        visited = set()
        temp_visited = set()
        
        def dfs(node: str, level: int):
            if node in temp_visited:
                raise ValueError(f"Circular dependency detected: {node}")
            
            if node in visited:
                return
            
            temp_visited.add(node)
            
            # Process dependencies first
            for dep in dependency_graph.get(node, []):
                if dep in self.tasks:
                    dfs(dep, level + 1)
            
            temp_visited.remove(node)
            visited.add(node)
            
            # Add to appropriate level
            while len(execution_levels) <= level:
                execution_levels.append([])
            execution_levels[level].append(node)
        
        # Process all tasks
        for task_id in self.tasks.keys():
            if task_id not in visited:
                dfs(task_id, 0)
        
        self.execution_order = [task_id for level in execution_levels for task_id in level]
        self.logger.info(f"Execution order resolved: {self.execution_order}")
        
        return execution_levels
    
    def execute_task(self, task_id: str, agents: Dict[str, Any]) -> TaskExecution:
        """Execute a single task"""
        if task_id not in self.tasks:
            raise ValueError(f"Task not found: {task_id}")
        
        task_exec = self.tasks[task_id]
        task = self._create_task_instance(task_exec.task_definition)
        
        self.logger.info(f"Executing task: {task_exec.task_definition.name}")
        task_exec.status = TaskStatus.RUNNING
        task_exec.start_time = datetime.now()
        
        try:
            # Validate prerequisites
            if not task.validate_prerequisites(task_exec.context):
                raise ValueError("Task prerequisites not met")
            
            # Execute task
            result = task.execute(task_exec.context, **agents)
            task_exec.result = result
            
            # Validate result
            if result.success and not task.validate_result(result):
                result.success = False
                result.error = "Task result validation failed"
            
            if result.success:
                task_exec.status = TaskStatus.COMPLETED
                self.logger.info(f"Task completed successfully: {task_exec.task_definition.name}")
            else:
                task_exec.status = TaskStatus.FAILED
                task_exec.error = result.error
                self.logger.error(f"Task failed: {task_exec.task_definition.name} - {result.error}")
            
        except Exception as e:
            task_exec.status = TaskStatus.FAILED
            task_exec.error = str(e)
            self.logger.error(f"Task execution error: {task_exec.task_definition.name} - {str(e)}")
        
        finally:
            task_exec.end_time = datetime.now()
            task.cleanup(task_exec.context)
        
        return task_exec
    
    def _create_task_instance(self, task_def: TaskDefinition) -> BaseTask:
        """Create task instance from definition"""
        # This would typically use a factory pattern
        # For now, we'll create based on task type
        if task_def.task_type == TaskType.DATA_COLLECTION:
            return DataCollectionTask(
                task_def.metadata.get('customer_id'),
                task_def.metadata.get('collection_scope', 'comprehensive')
            )
        elif task_def.task_type == TaskType.RISK_ANALYSIS:
            return RiskAnalysisTask(
                task_def.metadata.get('customer_data', {}),
                task_def.metadata.get('loan_details', {})
            )
        elif task_def.task_type == TaskType.DOCUMENTATION:
            return DocumentationTask(
                task_def.metadata.get('customer_data', {}),
                task_def.metadata.get('risk_assessment', {}),
                task_def.metadata.get('loan_details', {})
            )
        elif task_def.task_type == TaskType.REPORTING:
            return ReportingTask(
                task_def.metadata.get('customer_data', {}),
                task_def.metadata.get('risk_assessment', {}),
                task_def.metadata.get('documentation', {}),
                task_def.metadata.get('report_type', 'comprehensive')
            )
        else:
            raise ValueError(f"Unknown task type: {task_def.task_type}")
    
    def execute_workflow(self, agents: Dict[str, Any]) -> Dict[str, TaskExecution]:
        """Execute complete workflow"""
        self.logger.info("Starting workflow execution")
        
        # Resolve dependencies
        execution_levels = self.resolve_dependencies()
        
        # Execute tasks level by level
        for level_idx, level_tasks in enumerate(execution_levels):
            self.logger.info(f"Executing level {level_idx + 1}: {level_tasks}")
            
            # Execute tasks in parallel within each level
            futures = []
            for task_id in level_tasks:
                future = self.executor.submit(self.execute_task, task_id, agents)
                futures.append((task_id, future))
            
            # Wait for all tasks in this level to complete
            for task_id, future in futures:
                try:
                    task_exec = future.result()
                    self.logger.info(f"Level {level_idx + 1} task completed: {task_id}")
                except Exception as e:
                    self.logger.error(f"Level {level_idx + 1} task failed: {task_id} - {str(e)}")
                    # Mark dependent tasks as cancelled
                    self._cancel_dependent_tasks(task_id)
        
        # Return execution results
        return {task_id: task_exec for task_id, task_exec in self.tasks.items()}
    
    def _cancel_dependent_tasks(self, failed_task_id: str):
        """Cancel tasks that depend on the failed task"""
        for task_id, task_exec in self.tasks.items():
            if (failed_task_id in task_exec.task_definition.dependencies and 
                task_exec.status == TaskStatus.PENDING):
                task_exec.status = TaskStatus.CANCELLED
                self.logger.info(f"Cancelled dependent task: {task_id}")
    
    def get_workflow_status(self) -> Dict[str, Any]:
        """Get overall workflow status"""
        status_counts = {}
        for status in TaskStatus:
            status_counts[status.value] = 0
        
        for task_exec in self.tasks.values():
            status_counts[task_exec.status.value] += 1
        
        total_tasks = len(self.tasks)
        completed_tasks = status_counts[TaskStatus.COMPLETED.value]
        failed_tasks = status_counts[TaskStatus.FAILED.value]
        
        return {
            "total_tasks": total_tasks,
            "completed_tasks": completed_tasks,
            "failed_tasks": failed_tasks,
            "success_rate": completed_tasks / total_tasks if total_tasks > 0 else 0,
            "status_breakdown": status_counts,
            "execution_order": self.execution_order
        }

class EnhancedCreditAgentOrchestrator(CreditAgentOrchestrator):
    """Enhanced orchestrator with task coordination"""
    
    def __init__(self):
        super().__init__()
        self.task_coordinator = TaskCoordinator()
        self.logger = logging.getLogger("EnhancedCreditAgentOrchestrator")
    
    def create_credit_workflow(self, customer_id: str, loan_details: Dict[str, Any], 
                             context: AgentContext) -> List[str]:
        """Create a complete credit workflow with tasks"""
        self.logger.info(f"Creating credit workflow for customer: {customer_id}")
        
        # Create data collection task
        data_task = DataCollectionTask(customer_id, "comprehensive")
        data_task_id = self.task_coordinator.add_task(data_task, context)
        
        # Create risk analysis task (depends on data collection)
        risk_task = RiskAnalysisTask({}, loan_details)  # Will be updated with actual data
        risk_task_id = self.task_coordinator.add_task(risk_task, context)
        
        # Create documentation task (depends on data collection and risk analysis)
        doc_task = DocumentationTask({}, {}, loan_details)  # Will be updated with actual data
        doc_task_id = self.task_coordinator.add_task(doc_task, context)
        
        # Create reporting task (depends on all previous tasks)
        report_task = ReportingTask({}, {}, {}, "comprehensive")  # Will be updated with actual data
        report_task_id = self.task_coordinator.add_task(report_task, context)
        
        return [data_task_id, risk_task_id, doc_task_id, report_task_id]
    
    def run_enhanced_workflow(self, customer_id: str, loan_details: Dict[str, Any], 
                            context: Optional[AgentContext] = None) -> Dict[str, Any]:
        """Run enhanced workflow with task coordination"""
        if not context:
            context = create_agent_context(f"enhanced_workflow_{int(time.time())}")
        
        self.logger.info(f"Running enhanced workflow for customer: {customer_id}")
        
        # Create workflow tasks
        task_ids = self.create_credit_workflow(customer_id, loan_details, context)
        
        # Prepare agents
        agents = {
            'data_agent': self.agents.get('data_collection_agent'),
            'risk_agent': self.agents.get('risk_analysis_agent'),
            'doc_agent': self.agents.get('documentation_agent'),
            'report_agent': self.agents.get('reporting_agent')
        }
        
        # Execute workflow
        workflow_results = self.task_coordinator.execute_workflow(agents)
        
        # Update task data for dependent tasks
        self._update_task_dependencies(workflow_results, customer_id, loan_details)
        
        # Get workflow status
        workflow_status = self.task_coordinator.get_workflow_status()
        
        return {
            "workflow_id": context.session_id,
            "customer_id": customer_id,
            "task_results": workflow_results,
            "workflow_status": workflow_status,
            "communication_log": self.communication_log
        }
    
    def _update_task_dependencies(self, workflow_results: Dict[str, TaskExecution], 
                                customer_id: str, loan_details: Dict[str, Any]):
        """Update task dependencies with actual data"""
        # Find data collection result
        data_result = None
        for task_exec in workflow_results.values():
            if task_exec.task_definition.task_type == TaskType.DATA_COLLECTION:
                if task_exec.result and task_exec.result.success:
                    data_result = task_exec.result.data
                break
        
        # Find risk analysis result
        risk_result = None
        for task_exec in workflow_results.values():
            if task_exec.task_definition.task_type == TaskType.RISK_ANALYSIS:
                if task_exec.result and task_exec.result.success:
                    risk_result = task_exec.result.data
                break
        
        # Find documentation result
        doc_result = None
        for task_exec in workflow_results.values():
            if task_exec.task_definition.task_type == TaskType.DOCUMENTATION:
                if task_exec.result and task_exec.result.success:
                    doc_result = task_exec.result.data
                break
        
        # Update dependent tasks with actual data
        for task_exec in workflow_results.values():
            if task_exec.task_definition.task_type == TaskType.RISK_ANALYSIS and data_result:
                task_exec.task_definition.metadata['customer_data'] = data_result
            
            elif task_exec.task_definition.task_type == TaskType.DOCUMENTATION:
                if data_result:
                    task_exec.task_definition.metadata['customer_data'] = data_result
                if risk_result:
                    task_exec.task_definition.metadata['risk_assessment'] = risk_result
            
            elif task_exec.task_definition.task_type == TaskType.REPORTING:
                if data_result:
                    task_exec.task_definition.metadata['customer_data'] = data_result
                if risk_result:
                    task_exec.task_definition.metadata['risk_assessment'] = risk_result
                if doc_result:
                    task_exec.task_definition.metadata['documentation'] = doc_result

# Factory function for creating enhanced orchestrator
def create_enhanced_credit_agents(customer_server_url: str = "http://localhost:8001", 
                                market_server_url: str = "http://localhost:8002") -> EnhancedCreditAgentOrchestrator:
    """Create enhanced credit agent orchestrator with task coordination"""
    orchestrator = EnhancedCreditAgentOrchestrator()
    
    # Create and register agents
    from .credit_agents import create_credit_agents
    base_orchestrator = create_credit_agents(customer_server_url, market_server_url)
    orchestrator.agents = base_orchestrator.agents
    
    return orchestrator 