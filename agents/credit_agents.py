#!/usr/bin/env python3
"""
Specialized Credit Agents
Implements specialized agents for credit risk management tasks
"""

import json
import logging
import time
from typing import Dict, List, Any, Optional, Union
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
import asyncio

from .base_agent import (
    BaseAgent, AgentConfig, AgentContext, AgentResult, AgentStatus,
    AgentPriority, create_agent_context
)
from .database_tools import (
    CustomerDatabaseTool, MarketDatabaseTool, DatabaseToolManager,
    DatabaseResult, create_database_config
)

class AgentPersonality(Enum):
    """Agent personality types"""
    ANALYTICAL = "analytical"
    CAUTIOUS = "cautious"
    EFFICIENT = "efficient"
    THOROUGH = "thorough"
    COLLABORATIVE = "collaborative"

class AgentRole(Enum):
    """Agent role types"""
    DATA_COLLECTOR = "data_collector"
    RISK_ANALYST = "risk_analyst"
    DOCUMENTATION_SPECIALIST = "documentation_specialist"
    REPORTING_ANALYST = "reporting_analyst"

@dataclass
class AgentBackstory:
    """Agent backstory and personality"""
    name: str
    role: AgentRole
    personality: AgentPersonality
    background: str
    expertise: List[str]
    communication_style: str
    goals: List[str]
    fears: List[str]
    strengths: List[str]
    weaknesses: List[str]

class DataCollectionAgent(BaseAgent):
    """Agent specialized in comprehensive data collection"""
    
    def __init__(self, config: AgentConfig):
        super().__init__(config)
        self.backstory = AgentBackstory(
            name="Alex DataGather",
            role=AgentRole.DATA_COLLECTOR,
            personality=AgentPersonality.EFFICIENT,
            background="Former data scientist with 8 years in financial services. Expert in data mining and customer profiling.",
            expertise=["Data extraction", "Customer profiling", "Market research", "Database optimization"],
            communication_style="Direct and efficient. Prefers structured data formats and clear specifications.",
            goals=["Collect comprehensive customer data", "Ensure data accuracy", "Optimize collection efficiency"],
            fears=["Incomplete data", "Data quality issues", "System downtime"],
            strengths=["Fast data retrieval", "Comprehensive coverage", "Quality validation"],
            weaknesses=["Sometimes overlooks context", "Can be too focused on quantity over quality"]
        )
        self.logger.info(f"Data Collection Agent '{self.backstory.name}' initialized")
    
    def execute(self, customer_id: str, collection_scope: str = "comprehensive") -> AgentResult:
        """Execute comprehensive data collection"""
        self.logger.info(f"{self.backstory.name}: Collecting data for customer {customer_id}")
        
        try:
            collected_data = {
                'customer_id': customer_id,
                'collection_timestamp': datetime.now().isoformat(),
                'collection_scope': collection_scope,
                'data_sources': [],
                'data_points': {}
            }
            
            # Basic customer data
            customer_result = self.tool_manager.customer_tool.get_customer(customer_id)
            if customer_result.success:
                collected_data['data_sources'].append('customer_profile')
                collected_data['data_points']['customer_profile'] = customer_result.data
            
            # Financial data
            financial_result = self.tool_manager.customer_tool.get_financial_summary(customer_id)
            if financial_result.success:
                collected_data['data_sources'].append('financial_summary')
                collected_data['data_points']['financial_summary'] = financial_result.data
            
            # Credit profile (using financial summary instead)
            credit_result = self.tool_manager.customer_tool.get_financial_summary(customer_id)
            if credit_result.success:
                collected_data['data_sources'].append('credit_profile')
                collected_data['data_points']['credit_profile'] = credit_result.data
            
            # Market context
            market_result = self.tool_manager.market_tool.get_current_market_data()
            if market_result.success:
                collected_data['data_sources'].append('market_context')
                collected_data['data_points']['market_context'] = market_result.data
            
            # Collection summary
            collected_data['collection_summary'] = {
                'total_sources': len(collected_data['data_sources']),
                'successful_collections': len([k for k, v in collected_data['data_points'].items() if v]),
                'missing_data': [source for source in ['customer_profile', 'financial_summary', 'credit_profile', 'market_context'] 
                               if source not in collected_data['data_points'] or not collected_data['data_points'][source]]
            }
            
            return AgentResult(
                success=True,
                data=collected_data,
                status=AgentStatus.SUCCESS,
                context=self.context,
                metadata={
                    'agent_name': self.backstory.name,
                    'collection_scope': collection_scope,
                    'data_quality_score': len(collected_data['data_sources']) / 4.0
                }
            )
            
        except Exception as e:
            return self._handle_error(e, "Data collection")

class RiskAnalysisAgent(BaseAgent):
    """Agent specialized in comprehensive risk analysis"""
    
    def __init__(self, config: AgentConfig):
        super().__init__(config)
        self.backstory = AgentBackstory(
            name="Dr. Sarah RiskAssess",
            role=AgentRole.RISK_ANALYST,
            personality=AgentPersonality.CAUTIOUS,
            background="PhD in Financial Risk Management with 12 years in credit risk analysis. Former regulator.",
            expertise=["Credit risk modeling", "Portfolio analysis", "Regulatory compliance", "Stress testing"],
            communication_style="Analytical and cautious. Always provides detailed risk assessments with confidence levels.",
            goals=["Identify all potential risks", "Provide accurate risk assessments", "Ensure regulatory compliance"],
            fears=["Missing critical risks", "Inaccurate assessments", "Regulatory violations"],
            strengths=["Deep risk analysis", "Regulatory knowledge", "Conservative approach"],
            weaknesses=["Can be overly cautious", "Sometimes slow to process", "May miss opportunities"]
        )
        self.logger.info(f"Risk Analysis Agent '{self.backstory.name}' initialized")
    
    def execute(self, customer_data: Dict[str, Any], loan_amount: float, loan_type: str) -> AgentResult:
        """Execute comprehensive risk analysis"""
        self.logger.info(f"{self.backstory.name}: Analyzing risk for loan application")
        
        try:
            risk_assessment = {
                'analysis_timestamp': datetime.now().isoformat(),
                'loan_details': {
                    'amount': loan_amount,
                    'type': loan_type
                },
                'risk_factors': [],
                'risk_score': 0,
                'risk_level': 'Unknown',
                'confidence_level': 0.0,
                'recommendations': [],
                'regulatory_flags': []
            }
            
            # Extract customer data
            customer_profile = customer_data.get('data_points', {}).get('customer_profile', {})
            financial_summary = customer_data.get('data_points', {}).get('financial_summary', {})
            credit_profile = customer_data.get('data_points', {}).get('credit_profile', {})
            market_context = customer_data.get('data_points', {}).get('market_context', {})
            
            # Calculate risk factors
            risk_factors = []
            risk_score = 0
            
            # Income risk
            income = financial_summary.get('annual_income', 0)
            if income > 0:
                debt_to_income = loan_amount / income
                if debt_to_income > 0.4:
                    risk_factors.append({
                        'factor': 'High debt-to-income ratio',
                        'value': f"{debt_to_income:.2%}",
                        'risk_weight': 30,
                        'description': 'Debt-to-income ratio exceeds 40%'
                    })
                    risk_score += 30
                elif debt_to_income > 0.3:
                    risk_factors.append({
                        'factor': 'Moderate debt-to-income ratio',
                        'value': f"{debt_to_income:.2%}",
                        'risk_weight': 15,
                        'description': 'Debt-to-income ratio between 30-40%'
                    })
                    risk_score += 15
            
            # Credit score risk
            credit_score = credit_profile.get('credit_score', 0)
            if credit_score < 600:
                risk_factors.append({
                    'factor': 'Poor credit score',
                    'value': credit_score,
                    'risk_weight': 40,
                    'description': 'Credit score below 600 indicates high default risk'
                })
                risk_score += 40
            elif credit_score < 650:
                risk_factors.append({
                    'factor': 'Fair credit score',
                    'value': credit_score,
                    'risk_weight': 20,
                    'description': 'Credit score between 600-650 indicates moderate risk'
                })
                risk_score += 20
            
            # Market risk
            if market_context:
                risk_environment = market_context.get('risk_environment', 'Unknown')
                if risk_environment == 'High Risk':
                    risk_factors.append({
                        'factor': 'Unfavorable market conditions',
                        'value': risk_environment,
                        'risk_weight': 25,
                        'description': 'Current market conditions indicate high risk environment'
                    })
                    risk_score += 25
            
            # Employment risk
            employment_type = customer_profile.get('employment_type', 'Unknown')
            if employment_type in ['Self-employed', 'Contractor']:
                risk_factors.append({
                    'factor': 'Non-traditional employment',
                    'value': employment_type,
                    'risk_weight': 15,
                    'description': 'Self-employed or contractor status may indicate income volatility'
                })
                risk_score += 15
            
            # Determine risk level
            if risk_score >= 70:
                risk_level = "High"
                recommendations = [
                    "Require additional collateral",
                    "Increase interest rate by 2-3%",
                    "Require co-signer",
                    "Reduce loan amount by 20-30%"
                ]
            elif risk_score >= 40:
                risk_level = "Medium"
                recommendations = [
                    "Require additional documentation",
                    "Increase interest rate by 1-2%",
                    "Consider shorter loan term"
                ]
            else:
                risk_level = "Low"
                recommendations = [
                    "Proceed with standard terms",
                    "Consider preferred customer benefits"
                ]
            
            # Regulatory compliance check
            regulatory_flags = []
            if loan_amount > 100000 and credit_score < 650:
                regulatory_flags.append("High-value loan with poor credit requires additional review")
            if debt_to_income > 0.5:
                regulatory_flags.append("Debt-to-income ratio exceeds regulatory guidelines")
            
            # Calculate confidence level
            data_completeness = len([k for k, v in customer_data.get('data_points', {}).items() if v]) / 4.0
            confidence_level = min(0.95, 0.7 + (data_completeness * 0.25))
            
            risk_assessment.update({
                'risk_factors': risk_factors,
                'risk_score': risk_score,
                'risk_level': risk_level,
                'confidence_level': confidence_level,
                'recommendations': recommendations,
                'regulatory_flags': regulatory_flags,
                'data_completeness': data_completeness
            })
            
            return AgentResult(
                success=True,
                data=risk_assessment,
                status=AgentStatus.SUCCESS,
                context=self.context,
                metadata={
                    'agent_name': self.backstory.name,
                    'risk_level': risk_level,
                    'confidence_level': confidence_level
                }
            )
            
        except Exception as e:
            return self._handle_error(e, "Risk analysis")

class DocumentationAgent(BaseAgent):
    """Agent specialized in documentation and compliance"""
    
    def __init__(self, config: AgentConfig):
        super().__init__(config)
        self.backstory = AgentBackstory(
            name="Marcus DocuMaster",
            role=AgentRole.DOCUMENTATION_SPECIALIST,
            personality=AgentPersonality.THOROUGH,
            background="Former legal assistant with 10 years in financial compliance. Expert in regulatory documentation.",
            expertise=["Regulatory compliance", "Documentation standards", "Legal requirements", "Audit preparation"],
            communication_style="Detailed and precise. Always includes proper citations and references.",
            goals=["Ensure complete documentation", "Maintain regulatory compliance", "Prepare audit-ready materials"],
            fears=["Missing documentation", "Regulatory violations", "Audit failures"],
            strengths=["Attention to detail", "Regulatory knowledge", "Documentation standards"],
            weaknesses=["Can be overly detailed", "Sometimes slow to complete", "May focus too much on form over function"]
        )
        self.logger.info(f"Documentation Agent '{self.backstory.name}' initialized")
    
    def execute(self, customer_data: Dict[str, Any], risk_assessment: Dict[str, Any], 
               loan_details: Dict[str, Any]) -> AgentResult:
        """Execute comprehensive documentation"""
        self.logger.info(f"{self.backstory.name}: Creating documentation package")
        
        try:
            documentation_package = {
                'documentation_id': f"DOC_{int(time.time())}",
                'created_timestamp': datetime.now().isoformat(),
                'documentation_version': '1.0',
                'compliance_status': 'Pending Review',
                'sections': {},
                'required_documents': [],
                'compliance_checklist': {},
                'audit_trail': []
            }
            
            # Customer Information Section
            customer_profile = customer_data.get('data_points', {}).get('customer_profile', {})
            documentation_package['sections']['customer_information'] = {
                'customer_id': customer_profile.get('customer_id'),
                'name': customer_profile.get('name'),
                'email': customer_profile.get('email'),
                'phone': customer_profile.get('phone'),
                'address': customer_profile.get('address'),
                'date_of_birth': customer_profile.get('date_of_birth'),
                'employment_type': customer_profile.get('employment_type'),
                'annual_income': customer_profile.get('annual_income'),
                'verification_status': 'Verified' if customer_profile else 'Pending'
            }
            
            # Financial Information Section
            financial_summary = customer_data.get('data_points', {}).get('financial_summary', {})
            documentation_package['sections']['financial_information'] = {
                'credit_score': financial_summary.get('credit_score'),
                'net_worth': financial_summary.get('net_worth'),
                'total_assets': financial_summary.get('total_assets'),
                'total_liabilities': financial_summary.get('total_liabilities'),
                'credit_utilization': financial_summary.get('credit_utilization'),
                'payment_history': financial_summary.get('payment_history'),
                'verification_status': 'Verified' if financial_summary else 'Pending'
            }
            
            # Loan Application Section
            documentation_package['sections']['loan_application'] = {
                'loan_type': loan_details.get('type'),
                'loan_amount': loan_details.get('amount'),
                'loan_purpose': loan_details.get('purpose', 'General'),
                'term_months': loan_details.get('term_months'),
                'collateral_value': loan_details.get('collateral_value'),
                'application_date': datetime.now().isoformat(),
                'status': 'Under Review'
            }
            
            # Risk Assessment Section
            documentation_package['sections']['risk_assessment'] = {
                'risk_level': risk_assessment.get('risk_level'),
                'risk_score': risk_assessment.get('risk_score'),
                'confidence_level': risk_assessment.get('confidence_level'),
                'risk_factors': risk_assessment.get('risk_factors', []),
                'recommendations': risk_assessment.get('recommendations', []),
                'regulatory_flags': risk_assessment.get('regulatory_flags', []),
                'assessment_date': risk_assessment.get('analysis_timestamp')
            }
            
            # Required Documents Checklist
            required_docs = [
                'Government-issued ID',
                'Proof of income (pay stubs, tax returns)',
                'Bank statements (last 3 months)',
                'Employment verification',
                'Credit report authorization'
            ]
            
            if loan_details.get('type') == 'mortgage':
                required_docs.extend([
                    'Property appraisal',
                    'Title search',
                    'Homeowners insurance'
                ])
            
            if risk_assessment.get('risk_level') == 'High':
                required_docs.extend([
                    'Additional collateral documentation',
                    'Co-signer information',
                    'Enhanced income verification'
                ])
            
            documentation_package['required_documents'] = required_docs
            
            # Compliance Checklist
            compliance_checklist = {
                'identity_verification': 'Pending',
                'income_verification': 'Pending',
                'credit_check_authorization': 'Pending',
                'regulatory_disclosures': 'Pending',
                'fair_lending_compliance': 'Pending',
                'data_privacy_compliance': 'Pending'
            }
            
            # Update based on available data
            if customer_profile:
                compliance_checklist['identity_verification'] = 'Complete'
            if financial_summary:
                compliance_checklist['income_verification'] = 'Complete'
            if customer_data.get('data_points', {}).get('credit_profile'):
                compliance_checklist['credit_check_authorization'] = 'Complete'
            
            documentation_package['compliance_checklist'] = compliance_checklist
            
            # Audit Trail
            audit_trail = [
                {
                    'timestamp': datetime.now().isoformat(),
                    'action': 'Documentation package created',
                    'agent': self.backstory.name,
                    'details': 'Initial documentation package generated'
                },
                {
                    'timestamp': datetime.now().isoformat(),
                    'action': 'Compliance checklist initialized',
                    'agent': self.backstory.name,
                    'details': f"Compliance items: {len(compliance_checklist)}"
                }
            ]
            
            documentation_package['audit_trail'] = audit_trail
            
            # Overall compliance status
            completed_items = sum(1 for status in compliance_checklist.values() if status == 'Complete')
            total_items = len(compliance_checklist)
            compliance_percentage = (completed_items / total_items) * 100
            
            if compliance_percentage >= 80:
                documentation_package['compliance_status'] = 'Compliant'
            elif compliance_percentage >= 60:
                documentation_package['compliance_status'] = 'Partially Compliant'
            else:
                documentation_package['compliance_status'] = 'Non-Compliant'
            
            return AgentResult(
                success=True,
                data=documentation_package,
                status=AgentStatus.SUCCESS,
                context=self.context,
                metadata={
                    'agent_name': self.backstory.name,
                    'compliance_percentage': compliance_percentage,
                    'total_sections': len(documentation_package['sections'])
                }
            )
            
        except Exception as e:
            return self._handle_error(e, "Documentation creation")

class ReportingAgent(BaseAgent):
    """Agent specialized in reporting and insights"""
    
    def __init__(self, config: AgentConfig):
        super().__init__(config)
        self.backstory = AgentBackstory(
            name="Dr. Emily ReportGenius",
            role=AgentRole.REPORTING_ANALYST,
            personality=AgentPersonality.ANALYTICAL,
            background="PhD in Business Analytics with 15 years in financial reporting. Expert in data visualization and insights.",
            expertise=["Data analysis", "Report generation", "Business intelligence", "Executive summaries"],
            communication_style="Clear and analytical. Focuses on actionable insights and key metrics.",
            goals=["Generate insightful reports", "Provide actionable recommendations", "Ensure report accuracy"],
            fears=["Inaccurate data", "Missing key insights", "Poor report quality"],
            strengths=["Data analysis", "Clear communication", "Insight generation"],
            weaknesses=["Can be too analytical", "Sometimes overlooks practical aspects", "May focus too much on details"]
        )
        self.logger.info(f"Reporting Agent '{self.backstory.name}' initialized")
    
    def execute(self, customer_data: Dict[str, Any], risk_assessment: Dict[str, Any], 
               documentation: Dict[str, Any], report_type: str = "comprehensive") -> AgentResult:
        """Execute comprehensive reporting"""
        self.logger.info(f"{self.backstory.name}: Generating {report_type} report")
        
        try:
            report = {
                'report_id': f"RPT_{int(time.time())}",
                'generated_timestamp': datetime.now().isoformat(),
                'report_type': report_type,
                'executive_summary': {},
                'detailed_analysis': {},
                'recommendations': [],
                'risk_metrics': {},
                'compliance_summary': {},
                'visualization_data': {},
                'next_steps': []
            }
            
            # Executive Summary
            customer_profile = customer_data.get('data_points', {}).get('customer_profile', {})
            financial_summary = customer_data.get('data_points', {}).get('financial_summary', {})
            
            report['executive_summary'] = {
                'customer_name': customer_profile.get('name', 'N/A'),
                'customer_id': customer_profile.get('customer_id', 'N/A'),
                'loan_amount': documentation.get('sections', {}).get('loan_application', {}).get('loan_amount', 0),
                'loan_type': documentation.get('sections', {}).get('loan_application', {}).get('loan_type', 'N/A'),
                'risk_level': risk_assessment.get('risk_level', 'Unknown'),
                'credit_score': financial_summary.get('credit_score', 'N/A'),
                'annual_income': customer_profile.get('annual_income', 0),
                'recommendation': self._generate_recommendation(risk_assessment),
                'key_highlights': self._generate_highlights(customer_data, risk_assessment)
            }
            
            # Detailed Analysis
            report['detailed_analysis'] = {
                'customer_profile_analysis': self._analyze_customer_profile(customer_profile),
                'financial_analysis': self._analyze_financial_profile(financial_summary),
                'risk_analysis': self._analyze_risk_factors(risk_assessment),
                'market_context': self._analyze_market_context(customer_data.get('data_points', {}).get('market_context', {}))
            }
            
            # Recommendations
            report['recommendations'] = self._generate_recommendations(risk_assessment, customer_data)
            
            # Risk Metrics
            report['risk_metrics'] = {
                'overall_risk_score': risk_assessment.get('risk_score', 0),
                'risk_level': risk_assessment.get('risk_level', 'Unknown'),
                'confidence_level': risk_assessment.get('confidence_level', 0.0),
                'risk_factors_count': len(risk_assessment.get('risk_factors', [])),
                'regulatory_flags_count': len(risk_assessment.get('regulatory_flags', [])),
                'debt_to_income_ratio': self._calculate_dti_ratio(customer_profile, documentation),
                'credit_utilization': financial_summary.get('credit_utilization', 0)
            }
            
            # Compliance Summary
            compliance_checklist = documentation.get('compliance_checklist', {})
            report['compliance_summary'] = {
                'overall_status': documentation.get('compliance_status', 'Unknown'),
                'completed_items': sum(1 for status in compliance_checklist.values() if status == 'Complete'),
                'total_items': len(compliance_checklist),
                'completion_percentage': (sum(1 for status in compliance_checklist.values() if status == 'Complete') / len(compliance_checklist)) * 100 if compliance_checklist else 0,
                'pending_items': [item for item, status in compliance_checklist.items() if status == 'Pending'],
                'regulatory_flags': risk_assessment.get('regulatory_flags', [])
            }
            
            # Visualization Data
            report['visualization_data'] = {
                'risk_distribution': {
                    'low_risk': 1 if risk_assessment.get('risk_level') == 'Low' else 0,
                    'medium_risk': 1 if risk_assessment.get('risk_level') == 'Medium' else 0,
                    'high_risk': 1 if risk_assessment.get('risk_level') == 'High' else 0
                },
                'compliance_progress': {
                    'completed': report['compliance_summary']['completed_items'],
                    'pending': report['compliance_summary']['total_items'] - report['compliance_summary']['completed_items']
                },
                'risk_factors': {
                    factor['factor']: factor['risk_weight'] 
                    for factor in risk_assessment.get('risk_factors', [])
                }
            }
            
            # Next Steps
            report['next_steps'] = self._generate_next_steps(risk_assessment, documentation, report_type)
            
            return AgentResult(
                success=True,
                data=report,
                status=AgentStatus.SUCCESS,
                context=self.context,
                metadata={
                    'agent_name': self.backstory.name,
                    'report_type': report_type,
                    'insights_generated': len(report['recommendations'])
                }
            )
            
        except Exception as e:
            return self._handle_error(e, "Report generation")
    
    def _generate_recommendation(self, risk_assessment: Dict[str, Any]) -> str:
        """Generate executive recommendation"""
        risk_level = risk_assessment.get('risk_level', 'Unknown')
        if risk_level == 'Low':
            return "APPROVE - Low risk profile, recommend standard terms"
        elif risk_level == 'Medium':
            return "APPROVE WITH CONDITIONS - Moderate risk, recommend enhanced terms"
        elif risk_level == 'High':
            return "DECLINE OR RESTRUCTURE - High risk profile, requires significant modifications"
        else:
            return "UNDER REVIEW - Insufficient data for recommendation"
    
    def _generate_highlights(self, customer_data: Dict[str, Any], risk_assessment: Dict[str, Any]) -> List[str]:
        """Generate key highlights"""
        highlights = []
        
        customer_profile = customer_data.get('data_points', {}).get('customer_profile', {})
        financial_summary = customer_data.get('data_points', {}).get('financial_summary', {})
        
        if customer_profile.get('annual_income', 0) > 100000:
            highlights.append("High-income customer with strong earning potential")
        
        if financial_summary.get('credit_score', 0) >= 750:
            highlights.append("Excellent credit score indicating strong payment history")
        
        if risk_assessment.get('risk_level') == 'Low':
            highlights.append("Low-risk profile suitable for preferred terms")
        
        if len(risk_assessment.get('regulatory_flags', [])) == 0:
            highlights.append("No regulatory compliance issues identified")
        
        return highlights
    
    def _analyze_customer_profile(self, customer_profile: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze customer profile"""
        return {
            'employment_stability': 'Stable' if customer_profile.get('employment_type') in ['Full-time', 'Government'] else 'Variable',
            'income_level': 'High' if customer_profile.get('annual_income', 0) > 75000 else 'Moderate' if customer_profile.get('annual_income', 0) > 40000 else 'Low',
            'profile_completeness': 'Complete' if customer_profile else 'Incomplete'
        }
    
    def _analyze_financial_profile(self, financial_summary: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze financial profile"""
        credit_score = financial_summary.get('credit_score', 0)
        return {
            'credit_quality': 'Excellent' if credit_score >= 750 else 'Good' if credit_score >= 700 else 'Fair' if credit_score >= 650 else 'Poor',
            'credit_utilization': 'Low' if financial_summary.get('credit_utilization', 0) < 0.3 else 'Moderate' if financial_summary.get('credit_utilization', 0) < 0.6 else 'High',
            'net_worth_position': 'Positive' if financial_summary.get('net_worth', 0) > 0 else 'Negative'
        }
    
    def _analyze_risk_factors(self, risk_assessment: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze risk factors"""
        return {
            'primary_risk_factors': [factor['factor'] for factor in risk_assessment.get('risk_factors', [])[:3]],
            'risk_distribution': {
                'high_weight': len([f for f in risk_assessment.get('risk_factors', []) if f.get('risk_weight', 0) >= 30]),
                'medium_weight': len([f for f in risk_assessment.get('risk_factors', []) if 15 <= f.get('risk_weight', 0) < 30]),
                'low_weight': len([f for f in risk_assessment.get('risk_factors', []) if f.get('risk_weight', 0) < 15])
            }
        }
    
    def _analyze_market_context(self, market_context: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze market context"""
        if not market_context:
            return {'market_impact': 'Unknown - No market data available'}
        
        return {
            'market_impact': 'Favorable' if market_context.get('risk_environment') == 'Low Risk' else 'Unfavorable' if market_context.get('risk_environment') == 'High Risk' else 'Neutral',
            'interest_rate_environment': market_context.get('current_rates', {}).get('prime_rate', 'Unknown')
        }
    
    def _generate_recommendations(self, risk_assessment: Dict[str, Any], customer_data: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Generate detailed recommendations"""
        recommendations = []
        
        # Risk-based recommendations
        risk_level = risk_assessment.get('risk_level', 'Unknown')
        if risk_level == 'High':
            recommendations.append({
                'category': 'Risk Mitigation',
                'recommendation': 'Require additional collateral or co-signer',
                'priority': 'High',
                'rationale': 'High-risk profile requires additional security'
            })
        
        # Income-based recommendations
        customer_profile = customer_data.get('data_points', {}).get('customer_profile', {})
        income = customer_profile.get('annual_income', 0)
        if income < 50000:
            recommendations.append({
                'category': 'Income Verification',
                'recommendation': 'Require additional income documentation',
                'priority': 'Medium',
                'rationale': 'Low income requires enhanced verification'
            })
        
        # Compliance recommendations
        if risk_assessment.get('regulatory_flags'):
            recommendations.append({
                'category': 'Compliance',
                'recommendation': 'Enhanced regulatory review required',
                'priority': 'High',
                'rationale': 'Regulatory flags identified'
            })
        
        return recommendations
    
    def _calculate_dti_ratio(self, customer_profile: Dict[str, Any], documentation: Dict[str, Any]) -> float:
        """Calculate debt-to-income ratio"""
        income = customer_profile.get('annual_income', 0)
        loan_amount = documentation.get('sections', {}).get('loan_application', {}).get('loan_amount', 0)
        
        if income > 0:
            return loan_amount / income
        return 0.0
    
    def _generate_next_steps(self, risk_assessment: Dict[str, Any], documentation: Dict[str, Any], report_type: str) -> List[str]:
        """Generate next steps"""
        next_steps = []
        
        if risk_assessment.get('risk_level') == 'High':
            next_steps.append("Schedule risk committee review")
            next_steps.append("Prepare enhanced documentation requirements")
        
        if documentation.get('compliance_status') != 'Compliant':
            next_steps.append("Complete pending compliance items")
            next_steps.append("Schedule compliance review")
        
        if report_type == 'comprehensive':
            next_steps.append("Schedule customer interview")
            next_steps.append("Prepare loan terms proposal")
        
        next_steps.append("Update customer relationship management system")
        next_steps.append("Schedule follow-up review")
        
        return next_steps

class CreditAgentOrchestrator:
    """Orchestrator for credit agents with communication protocols"""
    
    def __init__(self):
        self.agents = {}
        self.communication_log = []
        self.logger = logging.getLogger("CreditAgentOrchestrator")
    
    def register_agent(self, agent: BaseAgent):
        """Register an agent"""
        self.agents[agent.config.agent_id] = agent
        self.logger.info(f"Registered agent: {agent.config.agent_id} ({agent.config.name})")
    
    def log_communication(self, from_agent: str, to_agent: str, message: str, data: Any = None):
        """Log agent communication"""
        communication_entry = {
            'timestamp': datetime.now().isoformat(),
            'from_agent': from_agent,
            'to_agent': to_agent,
            'message': message,
            'data': data
        }
        self.communication_log.append(communication_entry)
        self.logger.info(f"Communication: {from_agent} -> {to_agent}: {message}")
    
    def run_credit_workflow(self, customer_id: str, loan_details: Dict[str, Any], 
                          context: Optional[AgentContext] = None) -> Dict[str, AgentResult]:
        """Run complete credit workflow"""
        if not context:
            context = create_agent_context(f"credit_workflow_{int(time.time())}")
        
        self.logger.info(f"Starting credit workflow for customer {customer_id}")
        
        workflow_results = {}
        
        # Step 1: Data Collection
        self.log_communication("Orchestrator", "DataCollectionAgent", "Begin data collection", customer_id)
        data_agent = self.agents.get('data_collection_agent')
        if data_agent:
            data_result = data_agent.run(context, customer_id, "comprehensive")
            workflow_results['data_collection'] = data_result
            self.log_communication("DataCollectionAgent", "Orchestrator", "Data collection completed", 
                                 {"success": data_result.success, "sources": len(data_result.data.get('data_sources', [])) if data_result.success else 0})
        
        # Step 2: Risk Analysis
        if workflow_results.get('data_collection', AgentResult(success=False)).success:
            self.log_communication("Orchestrator", "RiskAnalysisAgent", "Begin risk analysis", loan_details)
            risk_agent = self.agents.get('risk_analysis_agent')
            if risk_agent:
                risk_result = risk_agent.run(context, workflow_results['data_collection'].data, 
                                           loan_details.get('amount'), loan_details.get('type'))
                workflow_results['risk_analysis'] = risk_result
                self.log_communication("RiskAnalysisAgent", "Orchestrator", "Risk analysis completed", 
                                     {"success": risk_result.success, "risk_level": risk_result.data.get('risk_level') if risk_result.success else 'Unknown'})
        
        # Step 3: Documentation
        if workflow_results.get('risk_analysis', AgentResult(success=False)).success:
            self.log_communication("Orchestrator", "DocumentationAgent", "Begin documentation", "Create documentation package")
            doc_agent = self.agents.get('documentation_agent')
            if doc_agent:
                doc_result = doc_agent.run(context, workflow_results['data_collection'].data, 
                                         workflow_results['risk_analysis'].data, loan_details)
                workflow_results['documentation'] = doc_result
                self.log_communication("DocumentationAgent", "Orchestrator", "Documentation completed", 
                                     {"success": doc_result.success, "compliance_status": doc_result.data.get('compliance_status') if doc_result.success else 'Unknown'})
        
        # Step 4: Reporting
        if (workflow_results.get('documentation', AgentResult(success=False)).success and 
            workflow_results.get('risk_analysis', AgentResult(success=False)).success):
            self.log_communication("Orchestrator", "ReportingAgent", "Begin report generation", "Generate comprehensive report")
            report_agent = self.agents.get('reporting_agent')
            if report_agent:
                report_result = report_agent.run(context, workflow_results['data_collection'].data, 
                                               workflow_results['risk_analysis'].data, 
                                               workflow_results['documentation'].data, "comprehensive")
                workflow_results['reporting'] = report_result
                self.log_communication("ReportingAgent", "Orchestrator", "Report generation completed", 
                                     {"success": report_result.success, "report_type": report_result.data.get('report_type') if report_result.success else 'Unknown'})
        
        # Workflow summary
        successful_steps = sum(1 for result in workflow_results.values() if result.success)
        total_steps = len(workflow_results)
        
        self.log_communication("Orchestrator", "System", "Workflow completed", 
                             {"successful_steps": successful_steps, "total_steps": total_steps})
        
        return workflow_results

# Factory function for creating credit agents
def create_credit_agents(customer_server_url: str = "http://localhost:8001", 
                        market_server_url: str = "http://localhost:8002") -> CreditAgentOrchestrator:
    """Create and configure all credit agents"""
    
    # Create configurations
    data_config = AgentConfig(
        agent_id="data_collection_agent",
        name="Data Collection Agent",
        description="Comprehensive data collection specialist",
        priority=AgentPriority.HIGH,
        customer_server_url=customer_server_url,
        market_server_url=market_server_url
    )
    
    risk_config = AgentConfig(
        agent_id="risk_analysis_agent",
        name="Risk Analysis Agent",
        description="Comprehensive risk assessment specialist",
        priority=AgentPriority.CRITICAL,
        customer_server_url=customer_server_url,
        market_server_url=market_server_url
    )
    
    doc_config = AgentConfig(
        agent_id="documentation_agent",
        name="Documentation Agent",
        description="Documentation and compliance specialist",
        priority=AgentPriority.HIGH,
        customer_server_url=customer_server_url,
        market_server_url=market_server_url
    )
    
    report_config = AgentConfig(
        agent_id="reporting_agent",
        name="Reporting Agent",
        description="Reporting and insights specialist",
        priority=AgentPriority.NORMAL,
        customer_server_url=customer_server_url,
        market_server_url=market_server_url
    )
    
    # Create agents
    data_agent = DataCollectionAgent(data_config)
    risk_agent = RiskAnalysisAgent(risk_config)
    doc_agent = DocumentationAgent(doc_config)
    report_agent = ReportingAgent(report_config)
    
    # Create orchestrator
    orchestrator = CreditAgentOrchestrator()
    orchestrator.register_agent(data_agent)
    orchestrator.register_agent(risk_agent)
    orchestrator.register_agent(doc_agent)
    orchestrator.register_agent(report_agent)
    
    return orchestrator 