#!/usr/bin/env python3
"""
Base Agent Configuration and Operations
Provides base classes for agent operations with error handling and logging
"""

import json
import logging
import time
import asyncio
from typing import Dict, List, Any, Optional, Union, Callable
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from abc import ABC, abstractmethod
import traceback
from enum import Enum

from .database_tools import (
    DatabaseConfig, DatabaseResult, CustomerDatabaseTool, MarketDatabaseTool,
    DatabaseToolManager, create_database_config, validate_database_result
)

class AgentStatus(Enum):
    """Agent status enumeration"""
    IDLE = "idle"
    RUNNING = "running"
    SUCCESS = "success"
    FAILED = "failed"
    RETRYING = "retrying"

class AgentPriority(Enum):
    """Agent priority levels"""
    LOW = 1
    NORMAL = 2
    HIGH = 3
    CRITICAL = 4

@dataclass
class AgentConfig:
    """Configuration for agent operations"""
    agent_id: str
    name: str
    description: str = ""
    priority: AgentPriority = AgentPriority.NORMAL
    max_retries: int = 3
    retry_delay: float = 1.0
    retry_backoff: float = 2.0
    timeout: int = 300  # 5 minutes
    enable_logging: bool = True
    log_level: str = "INFO"
    customer_server_url: str = "http://localhost:8001"
    market_server_url: str = "http://localhost:8002"
    
    def __post_init__(self):
        """Validate configuration after initialization"""
        if self.max_retries < 0:
            raise ValueError("max_retries must be non-negative")
        if self.retry_delay < 0:
            raise ValueError("retry_delay must be non-negative")
        if self.timeout < 0:
            raise ValueError("timeout must be non-negative")

@dataclass
class AgentContext:
    """Context for agent operations"""
    session_id: str
    user_id: Optional[str] = None
    request_id: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)
    created_at: datetime = field(default_factory=datetime.now)

@dataclass
class AgentResult:
    """Result from agent operation"""
    success: bool
    data: Optional[Dict[str, Any]] = None
    error: Optional[str] = None
    status: AgentStatus = AgentStatus.IDLE
    execution_time: float = 0.0
    retry_count: int = 0
    context: Optional[AgentContext] = None
    timestamp: datetime = field(default_factory=datetime.now)
    metadata: Dict[str, Any] = field(default_factory=dict)

class BaseAgent(ABC):
    """Base class for all agents"""
    
    def __init__(self, config: AgentConfig):
        self.config = config
        self.status = AgentStatus.IDLE
        self.logger = self._setup_logging()
        self.tool_manager = self._setup_tools()
        self.context: Optional[AgentContext] = None
        self.start_time: Optional[datetime] = None
        self.retry_count = 0
        
    def _setup_logging(self) -> logging.Logger:
        """Setup logging for the agent"""
        logger = logging.getLogger(f"Agent.{self.config.agent_id}")
        
        if self.config.enable_logging:
            level = getattr(logging, self.config.log_level.upper(), logging.INFO)
            logger.setLevel(level)
            
            # Create handler if none exists
            if not logger.handlers:
                handler = logging.StreamHandler()
                formatter = logging.Formatter(
                    '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
                )
                handler.setFormatter(formatter)
                logger.addHandler(handler)
        else:
            logger.setLevel(logging.WARNING)
        
        return logger
    
    def _setup_tools(self) -> DatabaseToolManager:
        """Setup database tool manager"""
        db_config = {
            'host': 'localhost',
            'port': 3306,
            'database': 'credit_risk_db',
            'user': 'credit_user',
            'password': 'CreditUser2024!',
            'pool_size': 10
        }
        
        return DatabaseToolManager(db_config)
    
    def set_context(self, context: AgentContext):
        """Set agent context"""
        self.context = context
        self.logger.info(f"Agent context set: {context.session_id}")
    
    def _pre_execute(self) -> bool:
        """Pre-execution checks and setup"""
        self.start_time = datetime.now()
        self.status = AgentStatus.RUNNING
        self.retry_count = 0
        
        # Health check
        health_results = self.tool_manager.health_check_all()
        all_healthy = all(result.success for result in health_results.values())
        
        if not all_healthy:
            failed_servers = [name for name, result in health_results.items() if not result.success]
            self.logger.error(f"Health check failed for servers: {failed_servers}")
            return False
        
        self.logger.info("Pre-execution checks passed")
        return True
    
    def _post_execute(self, result: AgentResult):
        """Post-execution cleanup and logging"""
        if self.start_time:
            execution_time = (datetime.now() - self.start_time).total_seconds()
            result.execution_time = execution_time
        
        result.timestamp = datetime.now()
        result.context = self.context
        result.retry_count = self.retry_count
        
        if result.success:
            self.status = AgentStatus.SUCCESS
            self.logger.info(f"Agent execution successful in {result.execution_time:.3f}s")
        else:
            self.status = AgentStatus.FAILED
            self.logger.error(f"Agent execution failed: {result.error}")
    
    def _handle_error(self, error: Exception, operation: str) -> AgentResult:
        """Handle errors during agent execution"""
        error_msg = f"{operation} failed: {str(error)}"
        self.logger.error(error_msg)
        
        if self.config.enable_logging:
            self.logger.debug(f"Error traceback: {traceback.format_exc()}")
        
        return AgentResult(
            success=False,
            error=error_msg,
            status=AgentStatus.FAILED,
            context=self.context
        )
    
    def _retry_operation(self, operation: Callable, *args, **kwargs) -> AgentResult:
        """Retry operation with exponential backoff"""
        for attempt in range(self.config.max_retries + 1):
            try:
                self.retry_count = attempt
                if attempt > 0:
                    self.status = AgentStatus.RETRYING
                    self.logger.warning(f"Retrying operation (attempt {attempt}/{self.config.max_retries})")
                
                result = operation(*args, **kwargs)
                
                if result.success:
                    return result
                
                if attempt < self.config.max_retries:
                    sleep_time = self.config.retry_delay * (self.config.retry_backoff ** attempt)
                    self.logger.info(f"Operation failed, retrying in {sleep_time:.1f}s")
                    time.sleep(sleep_time)
                
            except Exception as e:
                if attempt < self.config.max_retries:
                    sleep_time = self.config.retry_delay * (self.config.retry_backoff ** attempt)
                    self.logger.error(f"Operation exception, retrying in {sleep_time:.1f}s: {str(e)}")
                    time.sleep(sleep_time)
                else:
                    return self._handle_error(e, "Retry operation")
        
        return AgentResult(
            success=False,
            error="Max retries exceeded",
            status=AgentStatus.FAILED,
            context=self.context
        )
    
    @abstractmethod
    def execute(self, *args, **kwargs) -> AgentResult:
        """Execute agent operation - must be implemented by subclasses"""
        pass
    
    def run(self, context: Optional[AgentContext] = None, *args, **kwargs) -> AgentResult:
        """Run agent with full lifecycle management"""
        if context:
            self.set_context(context)
        
        self.logger.info(f"Starting agent execution: {self.config.name}")
        
        # Pre-execution checks
        if not self._pre_execute():
            return AgentResult(
                success=False,
                error="Pre-execution checks failed",
                status=AgentStatus.FAILED,
                context=self.context
            )
        
        try:
            # Execute with retry logic
            result = self._retry_operation(self.execute, *args, **kwargs)
            
            # Post-execution cleanup
            self._post_execute(result)
            
            return result
            
        except Exception as e:
            result = self._handle_error(e, "Agent execution")
            self._post_execute(result)
            return result

class CustomerAnalysisAgent(BaseAgent):
    """Agent for customer data analysis"""
    
    def execute(self, customer_id: str, analysis_type: str = "comprehensive") -> AgentResult:
        """Execute customer analysis"""
        self.logger.info(f"Analyzing customer {customer_id} with type: {analysis_type}")
        
        try:
            if analysis_type == "basic":
                result = self.tool_manager.customer_tool.get_customer(customer_id)
            elif analysis_type == "financial":
                result = self.tool_manager.customer_tool.get_financial_summary(customer_id)
            elif analysis_type == "credit":
                result = self.tool_manager.customer_tool.get_financial_summary(customer_id)
            elif analysis_type == "comprehensive":
                result = self.tool_manager.get_customer_with_market_context(customer_id)
            else:
                return AgentResult(
                    success=False,
                    error=f"Unknown analysis type: {analysis_type}",
                    status=AgentStatus.FAILED,
                    context=self.context
                )
            
            if result.success:
                return AgentResult(
                    success=True,
                    data=result.data,
                    status=AgentStatus.SUCCESS,
                    context=self.context
                )
            else:
                return AgentResult(
                    success=False,
                    error=result.error,
                    status=AgentStatus.FAILED,
                    context=self.context
                )
                
        except Exception as e:
            return self._handle_error(e, "Customer analysis")

class LoanCalculationAgent(BaseAgent):
    """Agent for loan calculations"""
    
    def execute(self, customer_id: str, loan_type: str, 
               loan_amount: float, term_months: int) -> AgentResult:
        """Execute loan calculation"""
        self.logger.info(f"Calculating loan for customer {customer_id}")
        
        try:
            result = self.tool_manager.calculate_loan_terms(
                customer_id, loan_type, loan_amount, term_months
            )
            
            if result.success:
                return AgentResult(
                    success=True,
                    data=result.data,
                    status=AgentStatus.SUCCESS,
                    context=self.context
                )
            else:
                return AgentResult(
                    success=False,
                    error=result.error,
                    status=AgentStatus.FAILED,
                    context=self.context
                )
                
        except Exception as e:
            return self._handle_error(e, "Loan calculation")

class MarketAnalysisAgent(BaseAgent):
    """Agent for market data analysis"""
    
    def execute(self, analysis_type: str = "current", 
               start_date: Optional[str] = None, 
               end_date: Optional[str] = None) -> AgentResult:
        """Execute market analysis"""
        self.logger.info(f"Analyzing market data with type: {analysis_type}")
        
        try:
            if analysis_type == "current":
                result = self.tool_manager.market_tool.get_current_market_data()
            elif analysis_type == "historical":
                if not start_date or not end_date:
                    return AgentResult(
                        success=False,
                        error="Historical analysis requires start_date and end_date",
                        status=AgentStatus.FAILED,
                        context=self.context
                    )
                result = self.tool_manager.market_tool.get_historical_market_data(
                    start_date, end_date
                )
            elif analysis_type == "economic_cycle":
                result = self.tool_manager.market_tool.analyze_economic_cycle()
            elif analysis_type == "indicators":
                result = self.tool_manager.market_tool.get_current_market_data()
            else:
                return AgentResult(
                    success=False,
                    error=f"Unknown market analysis type: {analysis_type}",
                    status=AgentStatus.FAILED,
                    context=self.context
                )
            
            if result.success:
                return AgentResult(
                    success=True,
                    data=result.data,
                    status=AgentStatus.SUCCESS,
                    context=self.context
                )
            else:
                return AgentResult(
                    success=False,
                    error=result.error,
                    status=AgentStatus.FAILED,
                    context=self.context
                )
                
        except Exception as e:
            return self._handle_error(e, "Market analysis")

class PortfolioAnalysisAgent(BaseAgent):
    """Agent for portfolio risk analysis"""
    
    def execute(self, customer_ids: List[str]) -> AgentResult:
        """Execute portfolio analysis"""
        self.logger.info(f"Analyzing portfolio for {len(customer_ids)} customers")
        
        try:
            # For now, use a simple approach - get customer data for each customer
            portfolio_data = []
            for customer_id in customer_ids:
                customer_result = self.tool_manager.customer_tool.get_customer(customer_id)
                if customer_result.success:
                    portfolio_data.append(customer_result.data)
            
            result = DatabaseResult(
                success=True,
                data={'customers': portfolio_data, 'total_customers': len(portfolio_data)}
            )
            
            if result.success:
                return AgentResult(
                    success=True,
                    data=result.data,
                    status=AgentStatus.SUCCESS,
                    context=self.context
                )
            else:
                return AgentResult(
                    success=False,
                    error=result.error,
                    status=AgentStatus.FAILED,
                    context=self.context
                )
                
        except Exception as e:
            return self._handle_error(e, "Portfolio analysis")

class AgentFactory:
    """Factory for creating agents"""
    
    @staticmethod
    def create_agent(agent_type: str, config: AgentConfig) -> BaseAgent:
        """Create agent instance based on type"""
        if agent_type == "customer_analysis":
            return CustomerAnalysisAgent(config)
        elif agent_type == "loan_calculation":
            return LoanCalculationAgent(config)
        elif agent_type == "market_analysis":
            return MarketAnalysisAgent(config)
        elif agent_type == "portfolio_analysis":
            return PortfolioAnalysisAgent(config)
        else:
            raise ValueError(f"Unknown agent type: {agent_type}")
    
    @staticmethod
    def create_default_config(agent_id: str, name: str, **kwargs) -> AgentConfig:
        """Create default agent configuration"""
        return AgentConfig(
            agent_id=agent_id,
            name=name,
            **kwargs
        )

class AgentOrchestrator:
    """Orchestrator for managing multiple agents"""
    
    def __init__(self):
        self.agents: Dict[str, BaseAgent] = {}
        self.logger = logging.getLogger("AgentOrchestrator")
    
    def register_agent(self, agent: BaseAgent):
        """Register an agent"""
        self.agents[agent.config.agent_id] = agent
        self.logger.info(f"Registered agent: {agent.config.agent_id}")
    
    def get_agent(self, agent_id: str) -> Optional[BaseAgent]:
        """Get agent by ID"""
        return self.agents.get(agent_id)
    
    def run_agent(self, agent_id: str, context: Optional[AgentContext] = None, 
                 *args, **kwargs) -> AgentResult:
        """Run a specific agent"""
        agent = self.get_agent(agent_id)
        if not agent:
            return AgentResult(
                success=False,
                error=f"Agent not found: {agent_id}",
                status=AgentStatus.FAILED
            )
        
        if context:
            agent.set_context(context)
        
        return agent.run(*args, **kwargs)
    
    def run_workflow(self, workflow: List[Dict[str, Any]]) -> List[AgentResult]:
        """Run a workflow of agents"""
        results = []
        
        for step in workflow:
            agent_id = step.get('agent_id')
            if not agent_id:
                self.logger.error("Workflow step missing agent_id")
                continue
                
            context_data = step.get('context', {})
            args = step.get('args', [])
            kwargs = step.get('kwargs', {})
            
            # Create context
            context = AgentContext(
                session_id=context_data.get('session_id', f"workflow_{int(time.time())}"),
                user_id=context_data.get('user_id'),
                request_id=context_data.get('request_id'),
                metadata=context_data.get('metadata', {})
            )
            
            # Run agent
            result = self.run_agent(agent_id, context, *args, **kwargs)
            results.append(result)
            
            # Check if workflow should continue
            if not result.success and step.get('stop_on_failure', True):
                self.logger.error(f"Workflow stopped due to agent failure: {agent_id}")
                break
        
        return results
    
    def get_agent_status(self) -> Dict[str, AgentStatus]:
        """Get status of all agents"""
        return {agent_id: agent.status for agent_id, agent in self.agents.items()}
    
    def health_check(self) -> Dict[str, bool]:
        """Check health of all agents"""
        health_status = {}
        
        for agent_id, agent in self.agents.items():
            try:
                # Check if agent's tool manager is healthy
                health_results = agent.tool_manager.health_check_all()
                health_status[agent_id] = all(result.success for result in health_results.values())
            except Exception as e:
                self.logger.error(f"Health check failed for agent {agent_id}: {str(e)}")
                health_status[agent_id] = False
        
        return health_status

# Utility functions
def create_agent_context(session_id: str, user_id: Optional[str] = None, 
                        request_id: Optional[str] = None, 
                        metadata: Optional[Dict[str, Any]] = None) -> AgentContext:
    """Create agent context"""
    return AgentContext(
        session_id=session_id,
        user_id=user_id,
        request_id=request_id,
        metadata=metadata or {}
    )

def validate_agent_result(result: AgentResult, operation: str) -> bool:
    """Validate agent result and log issues"""
    if not result.success:
        logging.error(f"{operation} failed: {result.error}")
        return False
    
    if result.execution_time > 60.0:  # Warning for slow operations
        logging.warning(f"{operation} took {result.execution_time:.2f}s")
    
    return True 