#!/usr/bin/env python3
"""
MCP Communication Tools for Agent Operations
Provides custom tool classes for interacting with Customer and Market MCP servers
"""

import json
import logging
import time
import asyncio
from typing import Dict, List, Any, Optional, Union
from dataclasses import dataclass, field
from datetime import datetime, timedelta
import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry
import pydantic
from pydantic import BaseModel, Field, validator
import numpy as np

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

@dataclass
class ToolResult:
    """Result from tool execution"""
    success: bool
    data: Optional[Dict[str, Any]] = None
    error: Optional[str] = None
    execution_time: float = 0.0
    retry_count: int = 0
    timestamp: datetime = field(default_factory=datetime.now)

class MCPToolConfig(BaseModel):
    """Configuration for MCP tools"""
    base_url: str
    timeout: int = 30
    max_retries: int = 3
    retry_delay: float = 1.0
    retry_backoff: float = 2.0
    enable_logging: bool = True
    
    @validator('base_url')
    def validate_base_url(cls, v):
        if not v.startswith(('http://', 'https://')):
            raise ValueError('base_url must start with http:// or https://')
        return v.rstrip('/')

class BaseMCPTool:
    """Base class for MCP communication tools"""
    
    def __init__(self, config: MCPToolConfig):
        self.config = config
        self.session = self._create_session()
        self.logger = logging.getLogger(f"{self.__class__.__name__}")
        
        if config.enable_logging:
            self.logger.setLevel(logging.INFO)
        else:
            self.logger.setLevel(logging.WARNING)
    
    def _create_session(self) -> requests.Session:
        """Create HTTP session with retry configuration"""
        session = requests.Session()
        
        # Configure retry strategy
        retry_strategy = Retry(
            total=self.config.max_retries,
            status_forcelist=[429, 500, 502, 503, 504],
            allowed_methods=["HEAD", "GET", "OPTIONS", "POST"],
            backoff_factor=self.config.retry_backoff
        )
        
        adapter = HTTPAdapter(max_retries=retry_strategy)
        session.mount("http://", adapter)
        session.mount("https://", adapter)
        
        return session
    
    def _make_request(self, method: str, endpoint: str, 
                     data: Optional[Dict] = None, 
                     headers: Optional[Dict] = None) -> ToolResult:
        """Make HTTP request with error handling and retries"""
        start_time = time.time()
        url = f"{self.config.base_url}{endpoint}"
        
        default_headers = {
            'Content-Type': 'application/json',
            'Accept': 'application/json'
        }
        if headers:
            default_headers.update(headers)
        
        try:
            self.logger.info(f"Making {method} request to {url}")
            
            if method.upper() == 'GET':
                response = self.session.get(url, headers=default_headers, timeout=self.config.timeout)
            elif method.upper() == 'POST':
                response = self.session.post(url, json=data, headers=default_headers, timeout=self.config.timeout)
            else:
                raise ValueError(f"Unsupported HTTP method: {method}")
            
            execution_time = time.time() - start_time
            
            if response.status_code == 200:
                self.logger.info(f"Request successful in {execution_time:.3f}s")
                return ToolResult(
                    success=True,
                    data=response.json(),
                    execution_time=execution_time
                )
            else:
                error_msg = f"HTTP {response.status_code}: {response.text}"
                self.logger.error(f"Request failed: {error_msg}")
                return ToolResult(
                    success=False,
                    error=error_msg,
                    execution_time=execution_time
                )
                
        except requests.exceptions.Timeout:
            error_msg = f"Request timeout after {self.config.timeout}s"
            self.logger.error(error_msg)
            return ToolResult(
                success=False,
                error=error_msg,
                execution_time=time.time() - start_time
            )
            
        except requests.exceptions.ConnectionError as e:
            error_msg = f"Connection error: {str(e)}"
            self.logger.error(error_msg)
            return ToolResult(
                success=False,
                error=error_msg,
                execution_time=time.time() - start_time
            )
            
        except requests.exceptions.RequestException as e:
            error_msg = f"Request error: {str(e)}"
            self.logger.error(error_msg)
            return ToolResult(
                success=False,
                error=error_msg,
                execution_time=time.time() - start_time
            )
            
        except Exception as e:
            error_msg = f"Unexpected error: {str(e)}"
            self.logger.error(error_msg)
            return ToolResult(
                success=False,
                error=error_msg,
                execution_time=time.time() - start_time
            )
    
    def health_check(self) -> ToolResult:
        """Check if the MCP server is healthy"""
        return self._make_request('GET', '/health')
    
    def validate_response(self, result: ToolResult, expected_fields: Optional[List[str]] = None) -> bool:
        """Validate tool result"""
        if not result.success:
            return False
        
        if not result.data:
            self.logger.error("No data in response")
            return False
        
        if expected_fields:
            for field in expected_fields:
                if field not in result.data:
                    self.logger.error(f"Missing required field: {field}")
                    return False
        
        return True

class CustomerDataTool(BaseMCPTool):
    """Tool for interacting with Customer MCP server"""
    
    def get_customer(self, customer_id: str) -> ToolResult:
        """Get customer details by ID"""
        self.logger.info(f"Fetching customer: {customer_id}")
        
        result = self._make_request('GET', f'/customers/{customer_id}')
        
        if result.success:
            expected_fields = ['customer_id', 'name', 'email', 'annual_income']
            if not self.validate_response(result, expected_fields):
                result.success = False
                result.error = "Invalid customer data format"
        
        return result
    
    def search_customers(self, filters: Dict[str, Any], 
                        limit: int = 100, offset: int = 0) -> ToolResult:
        """Search customers with filters"""
        self.logger.info(f"Searching customers with filters: {filters}")
        
        search_data = {
            **filters,
            'limit': min(limit, 1000),  # Cap at 1000
            'offset': offset
        }
        
        result = self._make_request('POST', '/customers/search', data=search_data)
        
        if result.success:
            expected_fields = ['customers', 'total_count']
            if not self.validate_response(result, expected_fields):
                result.success = False
                result.error = "Invalid search response format"
        
        return result
    
    def get_financial_summary(self, customer_id: str) -> ToolResult:
        """Get customer financial summary"""
        self.logger.info(f"Fetching financial summary for customer: {customer_id}")
        
        result = self._make_request('GET', f'/customers/{customer_id}/financial-summary')
        
        if result.success:
            expected_fields = ['customer_id', 'credit_score', 'net_worth', 'total_assets']
            if not self.validate_response(result, expected_fields):
                result.success = False
                result.error = "Invalid financial summary format"
        
        return result
    
    def get_customer_stats(self) -> ToolResult:
        """Get customer statistics"""
        self.logger.info("Fetching customer statistics")
        
        result = self._make_request('GET', '/customers/stats')
        
        if result.success:
            expected_fields = ['total_customers', 'average_income']
            if not self.validate_response(result, expected_fields):
                result.success = False
                result.error = "Invalid statistics format"
        
        return result
    
    def get_customers_by_income_range(self, min_income: float, max_income: float, 
                                    limit: int = 100) -> ToolResult:
        """Get customers within income range"""
        filters = {
            'income_min': min_income,
            'income_max': max_income
        }
        return self.search_customers(filters, limit)
    
    def get_customers_by_age_range(self, min_age: int, max_age: int, 
                                 limit: int = 100) -> ToolResult:
        """Get customers within age range"""
        filters = {
            'age_min': min_age,
            'age_max': max_age
        }
        return self.search_customers(filters, limit)
    
    def get_customers_by_employment_type(self, employment_type: str, 
                                       limit: int = 100) -> ToolResult:
        """Get customers by employment type"""
        filters = {
            'employment_type': employment_type
        }
        return self.search_customers(filters, limit)

class CreditDataTool(BaseMCPTool):
    """Tool for credit-related operations (extends CustomerDataTool)"""
    
    def __init__(self, config: MCPToolConfig):
        super().__init__(config)
        self.customer_tool = CustomerDataTool(config)
    
    def get_credit_profile(self, customer_id: str) -> ToolResult:
        """Get comprehensive credit profile for customer"""
        self.logger.info(f"Fetching credit profile for customer: {customer_id}")
        
        # Get financial summary which includes credit data
        result = self.customer_tool.get_financial_summary(customer_id)
        
        if result.success:
            # Enhance with additional credit analysis
            credit_data = result.data
            credit_score = credit_data.get('credit_score', 0)
            
            # Add credit risk assessment
            if credit_score >= 750:
                risk_level = "Excellent"
                approval_probability = 0.95
            elif credit_score >= 700:
                risk_level = "Good"
                approval_probability = 0.85
            elif credit_score >= 650:
                risk_level = "Fair"
                approval_probability = 0.70
            elif credit_score >= 600:
                risk_level = "Poor"
                approval_probability = 0.50
            else:
                risk_level = "Very Poor"
                approval_probability = 0.25
            
            # Add credit utilization analysis
            credit_utilization = credit_data.get('credit_utilization', 0)
            if credit_utilization > 0.8:
                utilization_status = "High Risk"
            elif credit_utilization > 0.6:
                utilization_status = "Moderate Risk"
            else:
                utilization_status = "Low Risk"
            
            # Enhanced credit profile
            enhanced_data = {
                **credit_data,
                'credit_risk_level': risk_level,
                'approval_probability': approval_probability,
                'credit_utilization_status': utilization_status,
                'credit_analysis_timestamp': datetime.now().isoformat()
            }
            
            result.data = enhanced_data
        
        return result
    
    def analyze_credit_trends(self, customer_ids: List[str]) -> ToolResult:
        """Analyze credit trends across multiple customers"""
        self.logger.info(f"Analyzing credit trends for {len(customer_ids)} customers")
        
        credit_profiles = []
        failed_customers = []
        
        for customer_id in customer_ids:
            result = self.get_credit_profile(customer_id)
            if result.success:
                credit_profiles.append(result.data)
            else:
                failed_customers.append(customer_id)
        
        if not credit_profiles:
            return ToolResult(
                success=False,
                error="No valid credit profiles found"
            )
        
        # Calculate aggregate statistics
        credit_scores = [p.get('credit_score', 0) for p in credit_profiles]
        net_worths = [p.get('net_worth', 0) for p in credit_profiles]
        utilization_rates = [p.get('credit_utilization', 0) for p in credit_profiles]
        
        analysis = {
            'total_customers': len(credit_profiles),
            'failed_customers': failed_customers,
            'credit_score_stats': {
                'mean': np.mean(credit_scores),
                'median': np.median(credit_scores),
                'min': min(credit_scores),
                'max': max(credit_scores),
                'std': np.std(credit_scores)
            },
            'net_worth_stats': {
                'mean': np.mean(net_worths),
                'median': np.median(net_worths),
                'min': min(net_worths),
                'max': max(net_worths)
            },
            'utilization_stats': {
                'mean': np.mean(utilization_rates),
                'median': np.median(utilization_rates),
                'high_risk_count': sum(1 for u in utilization_rates if u > 0.8)
            },
            'risk_distribution': {
                'excellent': sum(1 for p in credit_profiles if p.get('credit_risk_level') == 'Excellent'),
                'good': sum(1 for p in credit_profiles if p.get('credit_risk_level') == 'Good'),
                'fair': sum(1 for p in credit_profiles if p.get('credit_risk_level') == 'Fair'),
                'poor': sum(1 for p in credit_profiles if p.get('credit_risk_level') == 'Poor'),
                'very_poor': sum(1 for p in credit_profiles if p.get('credit_risk_level') == 'Very Poor')
            }
        }
        
        return ToolResult(
            success=True,
            data=analysis
        )

class MarketDataTool(BaseMCPTool):
    """Tool for interacting with Market MCP server"""
    
    def get_current_market_data(self) -> ToolResult:
        """Get current market conditions"""
        self.logger.info("Fetching current market data")
        
        result = self._make_request('GET', '/market/current')
        
        if result.success:
            expected_fields = ['current_rates', 'market_volatility', 'economic_health']
            if not self.validate_response(result, expected_fields):
                result.success = False
                result.error = "Invalid market data format"
        
        return result
    
    def get_historical_market_data(self, start_date: str, end_date: str, 
                                 indicators: Optional[List[str]] = None) -> ToolResult:
        """Get historical market data"""
        self.logger.info(f"Fetching historical market data from {start_date} to {end_date}")
        
        data = {
            'start_date': start_date,
            'end_date': end_date
        }
        if indicators:
            data['indicators'] = list(indicators)
        
        result = self._make_request('POST', '/market/historical', data=data)
        
        if result.success:
            if not isinstance(result.data, list):
                result.success = False
                result.error = "Historical data should be a list"
        
        return result
    
    def calculate_risk_benchmark(self, loan_type: str, risk_score: int, 
                               loan_amount: float, term_months: int,
                               collateral_value: Optional[float] = None) -> ToolResult:
        """Calculate risk-adjusted benchmark rate"""
        self.logger.info(f"Calculating risk benchmark for {loan_type} loan")
        
        data = {
            'loan_type': loan_type,
            'risk_score': risk_score,
            'loan_amount': loan_amount,
            'term_months': term_months
        }
        if collateral_value:
            data['collateral_value'] = collateral_value
        
        result = self._make_request('POST', '/risk/benchmark', data=data)
        
        if result.success:
            expected_fields = ['loan_type', 'risk_score', 'benchmark_rate', 'total_rate']
            if not self.validate_response(result, expected_fields):
                result.success = False
                result.error = "Invalid benchmark response format"
        
        return result
    
    def analyze_economic_cycle(self, analysis_period: str = "12m") -> ToolResult:
        """Analyze current economic cycle"""
        self.logger.info(f"Analyzing economic cycle for {analysis_period}")
        
        data = {
            'analysis_period': analysis_period
        }
        
        result = self._make_request('POST', '/economic/cycle', data=data)
        
        if result.success:
            expected_fields = ['current_phase', 'confidence_score', 'indicators']
            if not self.validate_response(result, expected_fields):
                result.success = False
                result.error = "Invalid economic cycle response format"
        
        return result
    
    def get_market_indicators(self) -> ToolResult:
        """Get market indicators and sentiment"""
        self.logger.info("Fetching market indicators")
        
        result = self._make_request('GET', '/market/indicators')
        
        if result.success:
            expected_fields = ['indicators', 'overall_market_sentiment']
            if not self.validate_response(result, expected_fields):
                result.success = False
                result.error = "Invalid market indicators format"
        
        return result
    
    def get_interest_rates(self) -> ToolResult:
        """Get current interest rates"""
        result = self.get_current_market_data()
        
        if result.success:
            result.data = result.data.get('current_rates', {})
        
        return result
    
    def get_market_volatility(self) -> ToolResult:
        """Get market volatility indicators"""
        result = self.get_current_market_data()
        
        if result.success:
            result.data = result.data.get('market_volatility', {})
        
        return result
    
    def get_default_rates(self) -> ToolResult:
        """Get default rates by loan type"""
        result = self.get_current_market_data()
        
        if result.success:
            result.data = result.data.get('default_rates', {})
        
        return result

class AgentToolManager:
    """Manager for coordinating multiple MCP tools"""
    
    def __init__(self, customer_config: MCPToolConfig, market_config: MCPToolConfig):
        self.customer_tool = CustomerDataTool(customer_config)
        self.credit_tool = CreditDataTool(customer_config)
        self.market_tool = MarketDataTool(market_config)
        self.logger = logging.getLogger("AgentToolManager")
    
    def health_check_all(self) -> Dict[str, ToolResult]:
        """Check health of all MCP servers"""
        self.logger.info("Performing health check on all MCP servers")
        
        results = {
            'customer_server': self.customer_tool.health_check(),
            'market_server': self.market_tool.health_check()
        }
        
        all_healthy = all(result.success for result in results.values())
        self.logger.info(f"All servers healthy: {all_healthy}")
        
        return results
    
    def get_customer_with_market_context(self, customer_id: str) -> ToolResult:
        """Get customer data with current market context"""
        self.logger.info(f"Getting customer {customer_id} with market context")
        
        # Get customer data
        customer_result = self.customer_tool.get_customer(customer_id)
        if not customer_result.success:
            return customer_result
        
        # Get market data
        market_result = self.market_tool.get_current_market_data()
        
        # Combine results
        combined_data = {
            'customer': customer_result.data,
            'market_context': market_result.data if market_result.success else None,
            'market_data_available': market_result.success,
            'timestamp': datetime.now().isoformat()
        }
        
        return ToolResult(
            success=True,
            data=combined_data,
            execution_time=customer_result.execution_time + market_result.execution_time
        )
    
    def calculate_loan_terms(self, customer_id: str, loan_type: str, 
                           loan_amount: float, term_months: int) -> ToolResult:
        """Calculate loan terms with customer and market data"""
        self.logger.info(f"Calculating loan terms for customer {customer_id}")
        
        # Get customer financial summary
        financial_result = self.credit_tool.get_credit_profile(customer_id)
        if not financial_result.success:
            return financial_result
        
        # Get risk benchmark
        risk_score = financial_result.data.get('credit_score', 650)
        benchmark_result = self.market_tool.calculate_risk_benchmark(
            loan_type, risk_score, loan_amount, term_months
        )
        
        if not benchmark_result.success:
            return benchmark_result
        
        # Combine results
        loan_terms = {
            'customer_profile': financial_result.data,
            'market_benchmark': benchmark_result.data,
            'loan_summary': {
                'loan_type': loan_type,
                'loan_amount': loan_amount,
                'term_months': term_months,
                'customer_risk_score': risk_score,
                'calculated_rate': benchmark_result.data.get('total_rate'),
                'approval_probability': benchmark_result.data.get('approval_probability')
            },
            'calculation_timestamp': datetime.now().isoformat()
        }
        
        return ToolResult(
            success=True,
            data=loan_terms,
            execution_time=financial_result.execution_time + benchmark_result.execution_time
        )
    
    def analyze_portfolio_risk(self, customer_ids: List[str]) -> ToolResult:
        """Analyze portfolio risk across multiple customers"""
        self.logger.info(f"Analyzing portfolio risk for {len(customer_ids)} customers")
        
        # Get credit trends
        credit_result = self.credit_tool.analyze_credit_trends(customer_ids)
        if not credit_result.success:
            return credit_result
        
        # Get market conditions
        market_result = self.market_tool.get_current_market_data()
        
        # Combine analysis
        portfolio_analysis = {
            'credit_analysis': credit_result.data,
            'market_conditions': market_result.data if market_result.success else None,
            'portfolio_risk_assessment': {
                'total_customers': len(customer_ids),
                'average_credit_score': credit_result.data.get('credit_score_stats', {}).get('mean', 0),
                'high_risk_customers': credit_result.data.get('risk_distribution', {}).get('poor', 0) + 
                                     credit_result.data.get('risk_distribution', {}).get('very_poor', 0),
                'market_risk_level': market_result.data.get('risk_environment') if market_result.success else 'Unknown',
                'analysis_timestamp': datetime.now().isoformat()
            }
        }
        
        return ToolResult(
            success=True,
            data=portfolio_analysis,
            execution_time=credit_result.execution_time + market_result.execution_time
        )

# Utility functions for tool operations
def create_tool_config(base_url: str, **kwargs) -> MCPToolConfig:
    """Create tool configuration with defaults"""
    return MCPToolConfig(base_url=base_url, **kwargs)

def validate_tool_result(result: ToolResult, operation: str) -> bool:
    """Validate tool result and log issues"""
    if not result.success:
        logger.error(f"{operation} failed: {result.error}")
        return False
    
    if result.execution_time > 10.0:  # Warning for slow operations
        logger.warning(f"{operation} took {result.execution_time:.2f}s")
    
    return True

def retry_operation(operation_func, max_retries: int = 3, 
                   delay: float = 1.0, backoff: float = 2.0):
    """Retry operation with exponential backoff"""
    for attempt in range(max_retries):
        try:
            result = operation_func()
            if result.success:
                return result
            
            if attempt < max_retries - 1:
                sleep_time = delay * (backoff ** attempt)
                logger.warning(f"Operation failed, retrying in {sleep_time:.1f}s (attempt {attempt + 1}/{max_retries})")
                time.sleep(sleep_time)
        
        except Exception as e:
            if attempt < max_retries - 1:
                sleep_time = delay * (backoff ** attempt)
                logger.error(f"Operation exception, retrying in {sleep_time:.1f}s: {str(e)}")
                time.sleep(sleep_time)
            else:
                logger.error(f"Operation failed after {max_retries} attempts: {str(e)}")
                return ToolResult(success=False, error=str(e))
    
    return ToolResult(success=False, error="Max retries exceeded") 