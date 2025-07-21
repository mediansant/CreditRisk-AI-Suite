#!/usr/bin/env python3
"""
Direct Database Connection Tools for Agent Operations
Replaces MCP server HTTP communication with direct MySQL database connections
"""

import json
import logging
import time
import asyncio
from typing import Dict, List, Any, Optional, Union
from dataclasses import dataclass, field
from datetime import datetime, timedelta
import mysql.connector
from mysql.connector import pooling
import os
from contextlib import contextmanager
import numpy as np

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

@dataclass
class DatabaseResult:
    """Result from database operation"""
    success: bool
    data: Optional[Dict[str, Any]] = None
    error: Optional[str] = None
    execution_time: float = 0.0
    rows_affected: int = 0
    timestamp: datetime = field(default_factory=datetime.now)

class DatabaseConfig:
    """Database configuration with environment variable support"""
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        if config is None:
            config = {}
        
        self.host = config.get('host') or os.getenv('DB_HOST', 'localhost')
        self.port = int(config.get('port') or os.getenv('DB_PORT', 3306))
        self.database = config.get('database') or os.getenv('DB_NAME', 'credit_risk_db')
        self.user = config.get('user') or os.getenv('DB_USER', 'credit_user')
        self.password = config.get('password') or os.getenv('DB_PASSWORD', 'CreditUser2024!')
        self.charset = config.get('charset', 'utf8mb4')
        self.use_unicode = config.get('use_unicode', True)
        self.pool_size = int(config.get('pool_size', 10))
        self.pool_name = config.get('pool_name', 'agent_pool')
        
        # Connection pool configuration
        self.pool_config = {
            'pool_name': self.pool_name,
            'pool_size': self.pool_size,
            'pool_reset_session': True,
            'host': self.host,
            'port': self.port,
            'database': self.database,
            'user': self.user,
            'password': self.password,
            'charset': self.charset,
            'use_unicode': self.use_unicode,
            'autocommit': True,
            'time_zone': '+00:00'
        }

class BaseDatabaseTool:
    """Base class for database tools"""
    
    def __init__(self, config: DatabaseConfig):
        self.config = config
        self.pool = None
        self.logger = logging.getLogger(f"{self.__class__.__name__}")
        self._initialize_pool()
    
    def _initialize_pool(self):
        """Initialize database connection pool"""
        try:
            self.pool = pooling.MySQLConnectionPool(**self.config.pool_config)
            self.logger.info(f"Database connection pool initialized: {self.config.pool_name}")
        except mysql.connector.Error as e:
            self.logger.error(f"Failed to initialize connection pool: {str(e)}")
            raise
    
    @contextmanager
    def get_connection(self):
        """Get database connection from pool with automatic cleanup"""
        conn = None
        try:
            if self.pool is None:
                raise mysql.connector.Error("Connection pool not initialized")
            conn = self.pool.get_connection()
            yield conn
        except mysql.connector.Error as e:
            self.logger.error(f"Database connection error: {str(e)}")
            raise
        finally:
            if conn:
                conn.close()
    
    def execute_query(self, query: str, params: Optional[tuple] = None, 
                     fetch_one: bool = False, fetch_all: bool = True) -> DatabaseResult:
        """Execute database query with error handling"""
        start_time = time.time()
        
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor(dictionary=True)
                
                self.logger.info(f"Executing query: {query[:100]}...")
                cursor.execute(query, params or ())
                
                execution_time = time.time() - start_time
                
                if fetch_one:
                    result = cursor.fetchone()
                elif fetch_all:
                    result = cursor.fetchall()
                else:
                    result = None
                
                rows_affected = cursor.rowcount
                cursor.close()
                
                self.logger.info(f"Query executed successfully in {execution_time:.3f}s")
                
                return DatabaseResult(
                    success=True,
                    data=result,
                    execution_time=execution_time,
                    rows_affected=rows_affected
                )
                
        except mysql.connector.Error as e:
            execution_time = time.time() - start_time
            error_msg = f"Database error: {str(e)}"
            self.logger.error(error_msg)
            
            return DatabaseResult(
                success=False,
                error=error_msg,
                execution_time=execution_time
            )
        
        except Exception as e:
            execution_time = time.time() - start_time
            error_msg = f"Unexpected error: {str(e)}"
            self.logger.error(error_msg)
            
            return DatabaseResult(
                success=False,
                error=error_msg,
                execution_time=execution_time
            )
    
    def health_check(self) -> DatabaseResult:
        """Check database connectivity"""
        return self.execute_query("SELECT 1 as health_check", fetch_one=True)

class CustomerDatabaseTool(BaseDatabaseTool):
    """Direct database tool for customer operations"""
    
    def get_customer(self, customer_id: str) -> DatabaseResult:
        """Get customer details by ID"""
        self.logger.info(f"Fetching customer: {customer_id}")
        
        query = """
            SELECT c.customer_id, c.name, c.age, c.email, c.phone, c.annual_income,
                   c.employment_type, c.employment_years, c.education_level,
                   c.marital_status, c.dependents, c.address, c.city, c.state, c.zip, 
                   c.created_at, COALESCE(ch.credit_score, 0) as credit_score
            FROM customers c
            LEFT JOIN credit_histories ch ON c.customer_id = ch.customer_id
            WHERE c.customer_id = %s
        """
        
        result = self.execute_query(query, (customer_id,), fetch_one=True)
        
        if result.success and not result.data:
            result.success = False
            result.error = "Customer not found"
        
        return result
    
    def search_customers(self, filters: Dict[str, Any], 
                        limit: int = 100, offset: int = 0) -> DatabaseResult:
        """Search customers with filters"""
        self.logger.info(f"Searching customers with filters: {filters}")
        
        # Build dynamic query with credit_score
        query = """
            SELECT c.customer_id, c.name, c.age, c.email, c.phone, c.annual_income,
                   c.employment_type, c.employment_years, c.education_level,
                   c.marital_status, c.dependents, c.address, c.city, c.state, c.zip, 
                   c.created_at, COALESCE(ch.credit_score, 0) as credit_score
            FROM customers c
            LEFT JOIN credit_histories ch ON c.customer_id = ch.customer_id
            WHERE 1=1
        """
        params = []
        
        # Add search conditions
        if filters.get('name'):
            query += " AND c.name LIKE %s"
            params.append(f"%{filters['name']}%")
        
        if filters.get('age_min') is not None:
            query += " AND c.age >= %s"
            params.append(filters['age_min'])
        
        if filters.get('age_max') is not None:
            query += " AND c.age <= %s"
            params.append(filters['age_max'])
        
        if filters.get('income_min') is not None:
            query += " AND c.annual_income >= %s"
            params.append(filters['income_min'])
        
        if filters.get('income_max') is not None:
            query += " AND c.annual_income <= %s"
            params.append(filters['income_max'])
        
        if filters.get('employment_type'):
            query += " AND c.employment_type = %s"
            params.append(filters['employment_type'])
        
        if filters.get('state'):
            query += " AND c.state = %s"
            params.append(filters['state'])
        
        # Get total count first
        count_query = query.replace(
            "SELECT c.customer_id, c.name, c.age, c.email, c.phone, c.annual_income, c.employment_type, c.employment_years, c.education_level, c.marital_status, c.dependents, c.address, c.city, c.state, c.zip, c.created_at, COALESCE(ch.credit_score, 0) as credit_score",
            "SELECT COUNT(*) as total"
        )
        
        count_result = self.execute_query(count_query, tuple(params), fetch_one=True)
        total_count = count_result.data['total'] if count_result.success and count_result.data else 0
        
        # Add pagination
        query += " ORDER BY c.created_at DESC LIMIT %s OFFSET %s"
        params.extend([limit, offset])
        
        result = self.execute_query(query, tuple(params), fetch_all=True)
        
        if result.success:
            result.data = {
                'customers': result.data,
                'total_count': total_count,
                'limit': limit,
                'offset': offset
            }
        
        return result
    
    def search_customers_flexible(self, search_term: str, limit: int = 100, offset: int = 0) -> DatabaseResult:
        """Flexible search customers by name, customer_id, or email"""
        self.logger.info(f"Flexible search for customers with term: {search_term}")
        
        # Build query that searches across multiple fields and includes credit_score
        query = """
            SELECT c.customer_id, c.name, c.age, c.email, c.phone, c.annual_income,
                   c.employment_type, c.employment_years, c.education_level,
                   c.marital_status, c.dependents, c.address, c.city, c.state, c.zip, 
                   c.created_at, COALESCE(ch.credit_score, 0) as credit_score
            FROM customers c
            LEFT JOIN credit_histories ch ON c.customer_id = ch.customer_id
            WHERE c.name LIKE %s OR c.customer_id LIKE %s OR c.email LIKE %s
            ORDER BY c.created_at DESC LIMIT %s OFFSET %s
        """
        
        search_pattern = f"%{search_term}%"
        params = (search_pattern, search_pattern, search_pattern, limit, offset)
        
        result = self.execute_query(query, params, fetch_all=True)
        
        if result.success:
            # Get total count for pagination
            count_query = """
                SELECT COUNT(*) as total
                FROM customers c
                WHERE c.name LIKE %s OR c.customer_id LIKE %s OR c.email LIKE %s
            """
            count_params = (search_pattern, search_pattern, search_pattern)
            count_result = self.execute_query(count_query, count_params, fetch_one=True)
            total_count = count_result.data['total'] if count_result.success and count_result.data else 0
            
            result.data = {
                'customers': result.data,
                'total_count': total_count,
                'limit': limit,
                'offset': offset
            }
        
        return result
    
    def get_financial_summary(self, customer_id: str) -> DatabaseResult:
        """Get comprehensive financial summary for customer"""
        self.logger.info(f"Fetching financial summary for customer: {customer_id}")
        
        query = """
            SELECT 
                c.customer_id,
                c.name,
                ch.credit_score,
                ch.total_credit_limit,
                ch.credit_utilization,
                fs.monthly_income,
                fs.monthly_expenses,
                fs.checking,
                fs.savings,
                fs.investments,
                fs.real_estate,
                fs.credit_cards,
                fs.loans,
                fs.mortgage,
                fs.other_debt,
                COUNT(la.loan_id) as loan_count,
                COALESCE(SUM(la.loan_amount), 0) as total_loan_amount
            FROM customers c
            LEFT JOIN credit_histories ch ON c.customer_id = ch.customer_id
            LEFT JOIN financial_statements fs ON c.customer_id = fs.customer_id
            LEFT JOIN loan_applications la ON c.customer_id = la.customer_id
            WHERE c.customer_id = %s
            GROUP BY c.customer_id, c.name, ch.credit_score, ch.total_credit_limit, 
                     ch.credit_utilization, fs.monthly_income, fs.monthly_expenses,
                     fs.checking, fs.savings, fs.investments, fs.real_estate,
                     fs.credit_cards, fs.loans, fs.mortgage, fs.other_debt
        """
        
        result = self.execute_query(query, (customer_id,), fetch_one=True)
        
        if result.success and result.data:
            # Calculate derived fields
            total_assets = (
                float(result.data.get('checking', 0) or 0) +
                float(result.data.get('savings', 0) or 0) +
                float(result.data.get('investments', 0) or 0) +
                float(result.data.get('real_estate', 0) or 0)
            )
            
            total_liabilities = (
                float(result.data.get('credit_cards', 0) or 0) +
                float(result.data.get('loans', 0) or 0) +
                float(result.data.get('mortgage', 0) or 0) +
                float(result.data.get('other_debt', 0) or 0)
            )
            
            if result.data is not None:
                result.data.update({
                    'total_assets': total_assets,
                    'total_liabilities': total_liabilities,
                    'net_worth': total_assets - total_liabilities
                })
        
        return result
    
    def get_customer_stats(self) -> DatabaseResult:
        """Get customer statistics"""
        self.logger.info("Fetching customer statistics")
        
        query = """
            SELECT 
                COUNT(*) as total_customers,
                AVG(annual_income) as avg_income,
                AVG(age) as avg_age,
                COUNT(CASE WHEN employment_type = 'Full-time' THEN 1 END) as full_time_count,
                COUNT(CASE WHEN employment_type = 'Part-time' THEN 1 END) as part_time_count,
                COUNT(CASE WHEN employment_type = 'Self-employed' THEN 1 END) as self_employed_count,
                COUNT(CASE WHEN employment_type = 'Retired' THEN 1 END) as retired_count
            FROM customers
        """
        
        return self.execute_query(query, fetch_one=True)
    
    def get_customers_by_income_range(self, min_income: float, max_income: float, 
                                    limit: int = 100) -> DatabaseResult:
        """Get customers within income range"""
        query = """
            SELECT customer_id, name, age, email, annual_income, employment_type
            FROM customers 
            WHERE annual_income BETWEEN %s AND %s
            ORDER BY annual_income DESC
            LIMIT %s
        """
        
        return self.execute_query(query, (min_income, max_income, limit), fetch_all=True)

class MarketDatabaseTool(BaseDatabaseTool):
    """Direct database tool for market data operations"""
    
    def get_current_market_data(self) -> DatabaseResult:
        """Get current market conditions"""
        self.logger.info("Fetching current market data")
        
        query = """
            SELECT 
                fed_funds_rate, prime_rate, treasury_1yr, treasury_10yr,
                unemployment_rate, inflation_rate, gdp_growth,
                personal_loan_default_rate, auto_loan_default_rate,
                mortgage_default_rate, business_loan_default_rate,
                vix, credit_spread, housing_price_index
            FROM market_data 
            WHERE date = (SELECT MAX(date) FROM market_data)
        """
        
        return self.execute_query(query, fetch_one=True)
    
    def get_historical_market_data(self, start_date: str, end_date: str, 
                                 indicators: Optional[List[str]] = None) -> DatabaseResult:
        """Get historical market data"""
        self.logger.info(f"Fetching historical market data from {start_date} to {end_date}")
        
        if indicators:
            # Build dynamic query based on requested indicators
            indicator_list = ', '.join(indicators)
            query = f"""
                SELECT date, {indicator_list}
                FROM market_data 
                WHERE date BETWEEN %s AND %s
                ORDER BY date
            """
        else:
            query = """
                SELECT *
                FROM market_data 
                WHERE date BETWEEN %s AND %s
                ORDER BY date
            """
        
        return self.execute_query(query, (start_date, end_date), fetch_all=True)
    
    def calculate_risk_benchmark(self, loan_type: str, risk_score: int, 
                               loan_amount: float, term_months: int,
                               collateral_value: Optional[float] = None) -> DatabaseResult:
        """Calculate risk-adjusted benchmark rates"""
        self.logger.info(f"Calculating risk benchmark for {loan_type} loan")
        
        # Get current market rates
        market_query = """
            SELECT 
                fed_funds_rate, prime_rate, treasury_10yr,
                personal_loan_default_rate, auto_loan_default_rate,
                mortgage_default_rate, business_loan_default_rate
            FROM market_data 
            WHERE date = (SELECT MAX(date) FROM market_data)
        """
        
        market_result = self.execute_query(market_query, fetch_one=True)
        
        if not market_result.success:
            return market_result
        
        # Calculate benchmark based on loan type and risk
        market_data = market_result.data
        if market_data is None:
            return DatabaseResult(
                success=False,
                error="No market data available for benchmark calculation"
            )
        base_rate = float(market_data['prime_rate'])
        
        # Risk premium based on credit score
        if risk_score >= 800:
            risk_premium = 0.5
        elif risk_score >= 700:
            risk_premium = 1.0
        elif risk_score >= 600:
            risk_premium = 2.0
        else:
            risk_premium = 3.5
        
        # Loan type adjustment
        type_adjustments = {
            'personal': 2.0,
            'auto': 1.5,
            'mortgage': 0.5,
            'business': 2.5
        }
        
        type_adjustment = type_adjustments.get(loan_type.lower(), 1.0)
        
        # Calculate final rate
        benchmark_rate = base_rate + risk_premium + type_adjustment
        
        # Calculate approval probability
        if risk_score >= 750:
            approval_prob = 0.95
        elif risk_score >= 650:
            approval_prob = 0.80
        elif risk_score >= 550:
            approval_prob = 0.60
        else:
            approval_prob = 0.30
        
        result_data = {
            'loan_type': loan_type,
            'risk_score': risk_score,
            'benchmark_rate': round(benchmark_rate, 2),
            'risk_premium': risk_premium,
            'type_adjustment': type_adjustment,
            'base_rate': base_rate,
            'approval_probability': approval_prob,
            'market_conditions': market_data
        }
        
        return DatabaseResult(
            success=True,
            data=result_data,
            execution_time=market_result.execution_time
        )
    
    def analyze_economic_cycle(self, analysis_period: str = "12m") -> DatabaseResult:
        """Analyze current economic cycle"""
        self.logger.info(f"Analyzing economic cycle for period: {analysis_period}")
        
        # Calculate months to look back
        months = 12 if analysis_period == "12m" else 6
        
        query = """
            SELECT 
                date,
                gdp_growth,
                unemployment_rate,
                inflation_rate,
                fed_funds_rate,
                housing_price_index
            FROM market_data 
            WHERE date >= DATE_SUB((SELECT MAX(date) FROM market_data), INTERVAL %s MONTH)
            ORDER BY date
        """
        
        return self.execute_query(query, (months,), fetch_all=True)

class DatabaseToolManager:
    """Manager for database tools with connection pooling"""
    
    def __init__(self, db_config: Optional[Dict[str, Any]] = None):
        self.config = DatabaseConfig(db_config)
        self.customer_tool = CustomerDatabaseTool(self.config)
        self.market_tool = MarketDatabaseTool(self.config)
        self.logger = logging.getLogger(self.__class__.__name__)
    
    def health_check_all(self) -> Dict[str, DatabaseResult]:
        """Check health of all database tools"""
        results = {}
        
        # Test customer tool
        customer_health = self.customer_tool.health_check()
        results['customer_tool'] = customer_health
        
        # Test market tool
        market_health = self.market_tool.health_check()
        results['market_tool'] = market_health
        
        # Overall health
        overall_healthy = all(result.success for result in results.values())
        results['overall'] = DatabaseResult(
            success=overall_healthy,
            data={'status': 'healthy' if overall_healthy else 'unhealthy'},
            error=None if overall_healthy else 'One or more tools failed health check'
        )
        
        return results
    
    def get_customer_with_market_context(self, customer_id: str) -> DatabaseResult:
        """Get customer data with market context"""
        self.logger.info(f"Getting customer {customer_id} with market context")
        
        # Get customer data
        customer_result = self.customer_tool.get_customer(customer_id)
        if not customer_result.success:
            return customer_result
        
        # Get current market data
        market_result = self.market_tool.get_current_market_data()
        if not market_result.success:
            return market_result
        
        # Combine data
        combined_data = {
            'customer': customer_result.data,
            'market_context': market_result.data,
            'analysis_timestamp': datetime.now().isoformat()
        }
        
        return DatabaseResult(
            success=True,
            data=combined_data,
            execution_time=customer_result.execution_time + market_result.execution_time
        )
    
    def calculate_loan_terms(self, customer_id: str, loan_type: str, 
                           loan_amount: float, term_months: int) -> DatabaseResult:
        """Calculate loan terms with customer and market data"""
        self.logger.info(f"Calculating loan terms for customer {customer_id}")
        
        # Get customer financial summary
        financial_result = self.customer_tool.get_financial_summary(customer_id)
        if not financial_result.success:
            return financial_result
        
        # Calculate risk benchmark
        risk_score = financial_result.data.get('credit_score', 650) if financial_result.data else 650
        benchmark_result = self.market_tool.calculate_risk_benchmark(
            loan_type, risk_score, loan_amount, term_months
        )
        
        if not benchmark_result.success:
            return benchmark_result
        
        # Combine results
        loan_terms = {
            'customer_id': customer_id,
            'loan_type': loan_type,
            'loan_amount': loan_amount,
            'term_months': term_months,
            'customer_profile': financial_result.data,
            'risk_assessment': benchmark_result.data,
            'calculated_rate': benchmark_result.data['benchmark_rate'] if benchmark_result.data else 0,
            'approval_probability': benchmark_result.data['approval_probability'] if benchmark_result.data else 0
        }
        
        return DatabaseResult(
            success=True,
            data=loan_terms,
            execution_time=financial_result.execution_time + benchmark_result.execution_time
        )

def create_database_config(**kwargs) -> DatabaseConfig:
    """Create database configuration with defaults"""
    return DatabaseConfig(kwargs)

def validate_database_result(result: DatabaseResult, operation: str) -> bool:
    """Validate database operation result"""
    if not result.success:
        logger.error(f"Database operation failed: {operation} - {result.error}")
        return False
    
    if not result.data:
        logger.warning(f"Database operation returned no data: {operation}")
        return False
    
    return True

def retry_database_operation(operation_func, max_retries: int = 3, 
                           delay: float = 1.0, backoff: float = 2.0):
    """Retry database operation with exponential backoff"""
    for attempt in range(max_retries):
        try:
            result = operation_func()
            if result.success:
                return result
            
            if attempt < max_retries - 1:
                time.sleep(delay * (backoff ** attempt))
                
        except Exception as e:
            if attempt < max_retries - 1:
                time.sleep(delay * (backoff ** attempt))
            else:
                return DatabaseResult(
                    success=False,
                    error=f"Operation failed after {max_retries} attempts: {str(e)}"
                )
    
    return DatabaseResult(
        success=False,
        error=f"Operation failed after {max_retries} attempts"
    ) 