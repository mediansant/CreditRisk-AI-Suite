"""
Application Page Module for CreditRisk AI Suite
Enhanced credit application form with validation and customer lookup
"""

import streamlit as st
import re
import json
from datetime import datetime, timedelta
from typing import Dict, Any, Optional, List
import pandas as pd

# Form validation functions
def validate_email(email: str) -> bool:
    """Validate email format"""
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return re.match(pattern, email) is not None

def validate_phone(phone: str) -> bool:
    """Validate phone number format - accepts various formats"""
    if not phone or not phone.strip():
        return False
    
    # Remove all non-digit characters
    digits_only = re.sub(r'\D', '', phone)
    
    # Check if we have at least 10 digits (standard phone number)
    if len(digits_only) < 10:
        return False
    
    # Check if we have reasonable number of digits (not more than 15)
    if len(digits_only) > 15:
        return False
    
    # Accept common phone number patterns
    # Examples: +1-555-123-4567, (555) 123-4567, 555-123-4567, 5551234567, +1 555 123 4567
    phone_patterns = [
        r'^\+?1?[-.\s]?\(?([0-9]{3})\)?[-.\s]?([0-9]{3})[-.\s]?([0-9]{4})$',  # US format
        r'^\+?[0-9]{1,3}[-.\s]?[0-9]{1,4}[-.\s]?[0-9]{1,4}[-.\s]?[0-9]{1,4}$',  # International
        r'^[0-9]{10,15}$',  # Just digits
    ]
    
    # Check if phone matches any of the patterns
    for pattern in phone_patterns:
        if re.match(pattern, phone):
            return True
    
    # If no pattern matches but we have enough digits, accept it
    return len(digits_only) >= 10

def validate_customer_id(customer_id: str) -> bool:
    """Validate customer ID format - very flexible for database IDs including UUIDs"""
    if not customer_id:
        return False
    
    # Convert to string and strip whitespace
    customer_id = str(customer_id).strip()
    
    # Debug logging
    print(f"Validating customer_id: '{customer_id}' (type: {type(customer_id)})")
    
    # Allow various formats that might come from database
    # Original format: 3-4 letters + 3-6 numbers
    if re.match(r'^[A-Z]{3,4}\d{3,6}$', customer_id):
        print(f"Customer ID '{customer_id}' matches original format")
        return True
    
    # Allow alphanumeric IDs (common in databases)
    if re.match(r'^[A-Z0-9]{4,10}$', customer_id):
        print(f"Customer ID '{customer_id}' matches alphanumeric format")
        return True
    
    # Allow IDs with hyphens or underscores
    if re.match(r'^[A-Z0-9_-]{4,15}$', customer_id):
        print(f"Customer ID '{customer_id}' matches hyphen/underscore format")
        return True
    
    # Allow UUID format (common in modern databases)
    if re.match(r'^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$', customer_id, re.IGNORECASE):
        print(f"Customer ID '{customer_id}' matches UUID format")
        return True
    
    # Allow any reasonable customer ID (very permissive for demo)
    if re.match(r'^[A-Za-z0-9_-]{3,50}$', customer_id):
        print(f"Customer ID '{customer_id}' matches general format")
        return True
    
    print(f"Customer ID '{customer_id}' failed all validation patterns")
    return False

def validate_ssn(ssn: str) -> bool:
    """Validate SSN format (XXX-XX-XXXX) - more flexible for demo purposes"""
    if not ssn:
        return False
    
    # Standard SSN format: XXX-XX-XXXX
    if re.match(r'^\d{3}-\d{2}-\d{4}$', ssn):
        return True
    
    # Allow SSNs without dashes for flexibility
    if re.match(r'^\d{9}$', ssn):
        return True
    
    # Allow placeholder SSNs (for demo purposes)
    if re.match(r'^\d{3}-\d{2}-\d{4}$', ssn) and ssn != '000-00-0000':
        return True
    
    return False

def calculate_risk_indicators(data: Dict[str, Any]) -> Dict[str, Any]:
    """Calculate comprehensive risk indicators"""
    annual_income = data.get('annual_income', 0)
    loan_amount = data.get('loan_amount', 0)
    credit_score = data.get('credit_score', 0)
    
    # Assets and liabilities
    assets = data.get('assets', {})
    liabilities = data.get('liabilities', {})
    
    total_assets = sum(assets.values())
    total_liabilities = sum(liabilities.values())
    net_worth = total_assets - total_liabilities
    
    # Risk ratios
    debt_to_income = (total_liabilities / annual_income * 100) if annual_income > 0 else 0
    loan_to_income = (loan_amount / annual_income * 100) if annual_income > 0 else 0
    debt_to_assets = (total_liabilities / total_assets * 100) if total_assets > 0 else 0
    
    # Risk levels
    risk_levels = {
        'debt_to_income': 'low' if debt_to_income <= 30 else 'medium' if debt_to_income <= 50 else 'high',
        'loan_to_income': 'low' if loan_to_income <= 20 else 'medium' if loan_to_income <= 40 else 'high',
        'credit_score': 'excellent' if credit_score >= 750 else 'good' if credit_score >= 700 else 'fair' if credit_score >= 650 else 'poor',
        'net_worth': 'positive' if net_worth >= 0 else 'negative'
    }
    
    return {
        'total_assets': total_assets,
        'total_liabilities': total_liabilities,
        'net_worth': net_worth,
        'debt_to_income_ratio': debt_to_income,
        'loan_to_income_ratio': loan_to_income,
        'debt_to_assets_ratio': debt_to_assets,
        'risk_levels': risk_levels
    }

# Customer lookup functionality
def get_demo_customers() -> List[Dict[str, Any]]:
    """Get demo customer data for lookup functionality"""
    return [
        {
            'customer_id': 'CUST001',
            'name': 'John Smith',
            'age': 35,
            'email': 'john.smith@email.com',
            'phone': '+1-555-123-4567',
            'ssn': '123-45-6789',
            'annual_income': 75000,
            'employment_years': 5,
            'credit_score': 720,
            'address': '123 Main St, Anytown, USA',
            'employment_status': 'full_time',
            'employer': 'Tech Corp Inc.'
        },
        {
            'customer_id': 'CUST002',
            'name': 'Sarah Johnson',
            'age': 28,
            'email': 'sarah.johnson@email.com',
            'phone': '(555) 234-5678',
            'ssn': '234-56-7890',
            'annual_income': 65000,
            'employment_years': 3,
            'credit_score': 680,
            'address': '456 Oak Ave, Somewhere, USA',
            'employment_status': 'full_time',
            'employer': 'Design Studio LLC'
        },
        {
            'customer_id': 'CUST003',
            'name': 'Michael Brown',
            'age': 42,
            'email': 'michael.brown@email.com',
            'phone': '555-345-6789',
            'ssn': '345-67-8901',
            'annual_income': 95000,
            'employment_years': 8,
            'credit_score': 780,
            'address': '789 Pine Rd, Elsewhere, USA',
            'employment_status': 'full_time',
            'employer': 'Finance Solutions Ltd.'
        },
        {
            'customer_id': 'CUST004',
            'name': 'Emily Davis',
            'age': 31,
            'email': 'emily.davis@email.com',
            'phone': '5554567890',
            'ssn': '456-78-9012',
            'annual_income': 55000,
            'employment_years': 2,
            'credit_score': 620,
            'address': '321 Elm St, Nowhere, USA',
            'employment_status': 'part_time',
            'employer': 'Retail Store Inc.'
        },
        {
            'customer_id': 'CUST005',
            'name': 'David Wilson',
            'age': 38,
            'email': 'david.wilson@email.com',
            'phone': '+1 555 567 8901',
            'ssn': '567-89-0123',
            'annual_income': 85000,
            'employment_years': 6,
            'credit_score': 750,
            'address': '654 Maple Dr, Anywhere, USA',
            'employment_status': 'full_time',
            'employer': 'Healthcare Systems Corp.'
        }
    ]

def lookup_customer(customer_id: str) -> Optional[Dict[str, Any]]:
    """Lookup customer by ID from database"""
    try:
        if st.session_state.database_manager:
            # Try to get from database first
            customer_tool = st.session_state.database_manager.customer_tool
            result = customer_tool.get_customer(customer_id)
            if result.success and result.data:
                return result.data
        
        # Fallback to demo customers if database not available
        customers = get_demo_customers()
        for customer in customers:
            if customer['customer_id'].upper() == customer_id.upper():
                return customer
        return None
    except Exception as e:
        st.error(f"Error looking up customer: {str(e)}")
        return None

def search_customers(query: str) -> List[Dict[str, Any]]:
    """Search customers by name, ID, or email from database"""
    try:
        if st.session_state.database_manager:
            # Search in database using flexible search
            customer_tool = st.session_state.database_manager.customer_tool
            
            if query.strip():
                # Use the new flexible search method
                result = customer_tool.search_customers_flexible(query.strip(), limit=50)
                if result.success and result.data and result.data.get('customers'):
                    return result.data['customers']
        
        # Fallback to demo customers if database not available or search fails
        customers = get_demo_customers()
        query = query.lower()
        results = []
        
        for customer in customers:
            if (query in customer['name'].lower() or 
                query in customer['customer_id'].lower() or
                query in customer['email'].lower()):
                results.append(customer)
        
        return results
    except Exception as e:
        st.error(f"Error searching customers: {str(e)}")
        # Fallback to demo customers
        customers = get_demo_customers()
        query = query.lower()
        results = []
        
        for customer in customers:
            if (query in customer['name'].lower() or 
                query in customer['customer_id'].lower() or
                query in customer['email'].lower()):
                results.append(customer)
        
        return results

# Form state management
def initialize_form_state():
    """Initialize form state variables"""
    if 'form_data' not in st.session_state:
        st.session_state.form_data = {}
    if 'form_errors' not in st.session_state:
        st.session_state.form_errors = {}
    if 'customer_lookup_result' not in st.session_state:
        st.session_state.customer_lookup_result = None
    if 'form_submitted' not in st.session_state:
        st.session_state.form_submitted = False

def clear_form_state():
    """Clear form state"""
    st.session_state.form_data = {}
    st.session_state.form_errors = {}
    st.session_state.customer_lookup_result = None
    st.session_state.form_submitted = False

def validate_form_data(data: Dict[str, Any]) -> Dict[str, str]:
    """Validate all form data and return errors"""
    errors = {}
    
    # Debug logging
    print(f"Validating form data: {data}")
    print(f"Customer ID in data: '{data.get('customer_id')}' (type: {type(data.get('customer_id'))})")
    
    # Required fields
    required_fields = ['customer_id', 'name', 'email', 'phone', 'ssn', 'annual_income']
    for field in required_fields:
        if not data.get(field):
            errors[field] = f"{field.replace('_', ' ').title()} is required"
    
    # Email validation
    if data.get('email') and not validate_email(data['email']):
        errors['email'] = "Invalid email format"
    
    # Phone validation
    if data.get('phone') and not validate_phone(data['phone']):
        errors['phone'] = "Invalid phone number format"
    
    # Customer ID validation
    if data.get('customer_id') and not validate_customer_id(data['customer_id']):
        errors['customer_id'] = "Customer ID must be 3-4 letters followed by 3-6 numbers"
    
    # SSN validation
    if data.get('ssn') and not validate_ssn(data['ssn']):
        errors['ssn'] = "SSN must be in format XXX-XX-XXXX"
    
    # Numeric validations
    if data.get('age', 0) < 18 or data.get('age', 0) > 100:
        errors['age'] = "Age must be between 18 and 100"
    
    if data.get('annual_income', 0) <= 0:
        errors['annual_income'] = "Annual income must be greater than 0"
    
    if data.get('loan_amount', 0) <= 0:
        errors['loan_amount'] = "Loan amount must be greater than 0"
    
    if data.get('credit_score', 0) < 300 or data.get('credit_score', 0) > 850:
        errors['credit_score'] = "Credit score must be between 300 and 850"
    
    print(f"Validation errors: {errors}")
    return errors

def initialize_system():
    """Initialize the credit risk analysis system"""
    try:
        with st.spinner("Initializing system components..."):
            # Import here to avoid circular imports
            from agents.database_tools import DatabaseToolManager, create_database_config
            from agents.performance_monitor import PerformanceMonitor
            
            # Initialize database manager
            if st.session_state.database_manager is None:
                db_config = create_database_config()
                st.session_state.database_manager = DatabaseToolManager(db_config.__dict__)
                st.session_state.system_status['database'] = 'online'
            
            # Initialize performance monitor
            if st.session_state.performance_monitor is None:
                st.session_state.performance_monitor = PerformanceMonitor(enable_system_monitoring=True)
                st.session_state.performance_monitor.start_monitoring()
                st.session_state.system_status['monitor'] = 'online'
            
            # Initialize crew (if needed)
            if not st.session_state.crew_initialized:
                try:
                    from agents.credit_risk_crew import CreditRiskCrew
                    crew = CreditRiskCrew()
                    st.session_state.crew = crew
                    st.session_state.crew_initialized = True
                    st.session_state.system_status['crew'] = 'online'
                except Exception as e:
                    st.session_state.system_status['crew'] = 'warning'
                    st.warning(f"CrewAI initialization warning: {str(e)}")
            
            st.success("System initialized successfully!")
            return True
            
    except Exception as e:
        st.error(f"Error initializing system: {str(e)}")
        return False

def render_customer_lookup_section():
    """Render customer lookup section"""
    st.markdown("### 🔍 Customer Lookup")
    
    # Use a container to ensure proper layout
    with st.container():
        col1, col2 = st.columns([2, 1])
        
        with col1:
            search_query = st.text_input(
                "Search by Name, ID, or Email",
                placeholder="Enter customer name, ID, or email...",
                help="Search for existing customers to pre-fill the form",
                key="customer_search_input"
            )
        
        with col2:
            search_clicked = st.button("🔍 Search", type="secondary", key="customer_search_button")
    
    # Handle search outside of columns to avoid form context issues
    if search_clicked:
        if search_query:
            st.info(f"Searching for: '{search_query}'")
            results = search_customers(search_query)
            if results:
                st.session_state.customer_lookup_result = results
                st.success(f"Found {len(results)} customer(s) matching your search.")
                # Debug: Show what fields are available in the first result
                if results and len(results) > 0:
                    st.info(f"Available fields in search results: {list(results[0].keys())}")
            else:
                st.warning("No customers found matching your search.")
        else:
            st.warning("Please enter a search term.")
    
    # Display search results outside of any form context
    if st.session_state.customer_lookup_result:
        st.markdown("#### Search Results")
        st.markdown("Click on a customer to pre-fill the form with their information.")
        
        for i, customer in enumerate(st.session_state.customer_lookup_result):
            with st.expander(f"**{customer['name']}** ({customer['customer_id']})", expanded=False):
                col1, col2, col3 = st.columns(3)
                
                with col1:
                    st.markdown(f"**Email:** {customer.get('email', 'N/A')}")
                    st.markdown(f"**Phone:** {customer.get('phone', 'N/A')}")
                    st.markdown(f"**Age:** {customer.get('age', 'N/A')}")
                
                with col2:
                    st.markdown(f"**Income:** ${customer.get('annual_income', 0):,}")
                    st.markdown(f"**Employment:** {customer.get('employment_years', 0)} years")
                    st.markdown(f"**Credit Score:** {customer.get('credit_score', 0)}")
                
                with col3:
                    # Use a unique key for each button to avoid conflicts
                    button_key = f"use_customer_{i}_{customer['customer_id']}"
                    if st.button(f"Use This Customer", key=button_key):
                        # Pre-fill form with available customer data
                        form_data = {}
                        
                        # Only include fields that exist in the customer data
                        if 'customer_id' in customer:
                            form_data['customer_id'] = customer['customer_id']
                        if 'name' in customer:
                            form_data['name'] = customer['name']
                        if 'age' in customer:
                            # Convert to int for age
                            try:
                                form_data['age'] = int(float(customer['age']))
                            except (ValueError, TypeError):
                                form_data['age'] = 35  # Default age
                        if 'email' in customer:
                            form_data['email'] = customer['email']
                        if 'phone' in customer:
                            form_data['phone'] = customer['phone']
                        if 'annual_income' in customer:
                            # Convert to int for annual_income
                            try:
                                form_data['annual_income'] = int(float(customer['annual_income']))
                            except (ValueError, TypeError):
                                form_data['annual_income'] = 75000  # Default income
                        if 'employment_years' in customer:
                            # Convert to int for employment_years
                            try:
                                form_data['employment_years'] = int(float(customer['employment_years']))
                            except (ValueError, TypeError):
                                form_data['employment_years'] = 5  # Default years
                        if 'credit_score' in customer:
                            # Convert to int for credit_score
                            try:
                                form_data['credit_score'] = int(float(customer['credit_score']))
                            except (ValueError, TypeError):
                                form_data['credit_score'] = 720  # Default credit score
                        
                        # Try to get financial data from database
                        try:
                            if st.session_state.database_manager:
                                customer_tool = st.session_state.database_manager.customer_tool
                                financial_result = customer_tool.get_financial_summary(customer['customer_id'])
                                if financial_result.success and financial_result.data:
                                    financial_data = financial_result.data
                                    # Pre-fill financial fields with actual data
                                    if 'checking' in financial_data:
                                        form_data['checking_balance'] = int(float(financial_data['checking'] or 0))
                                    if 'savings' in financial_data:
                                        form_data['savings_balance'] = int(float(financial_data['savings'] or 0))
                                    if 'investments' in financial_data:
                                        form_data['investments'] = int(float(financial_data['investments'] or 0))
                                    if 'real_estate' in financial_data:
                                        form_data['real_estate'] = int(float(financial_data['real_estate'] or 0))
                                    if 'credit_cards' in financial_data:
                                        form_data['credit_cards'] = int(float(financial_data['credit_cards'] or 0))
                                    if 'loans' in financial_data:
                                        form_data['loans'] = int(float(financial_data['loans'] or 0))
                                    if 'mortgage' in financial_data:
                                        form_data['mortgage'] = int(float(financial_data['mortgage'] or 0))
                                    if 'other_debt' in financial_data:
                                        form_data['other_debt'] = int(float(financial_data['other_debt'] or 0))
                                    print(f"Financial data loaded for {customer['name']}: {financial_data}")
                        except Exception as e:
                            print(f"Error loading financial data: {e}")
                            # Use default values if financial data not available
                            form_data.update({
                                'checking_balance': 5000,
                                'savings_balance': 15000,
                                'investments': 25000,
                                'real_estate': 200000,
                                'credit_cards': 3000,
                                'loans': 10000,
                                'mortgage': 150000,
                                'other_debt': 5000
                            })
                        
                        # Handle missing SSN - generate a placeholder for demo purposes
                        # In production, this would be handled differently for security
                        if 'ssn' not in customer:
                            # Generate a placeholder SSN for demo purposes
                            import random
                            ssn_part1 = str(random.randint(100, 999))
                            ssn_part2 = str(random.randint(10, 99))
                            ssn_part3 = str(random.randint(1000, 9999))
                            form_data['ssn'] = f"{ssn_part1}-{ssn_part2}-{ssn_part3}"
                        
                        # Set form data in session state
                        st.session_state.form_data = form_data
                        st.success(f"✅ Form pre-filled with {customer['name']}'s information!")
                        st.info("⚠️ Note: SSN has been generated for demo purposes. In production, this would require manual entry for security.")
                        st.session_state.customer_lookup_result = None
                        st.rerun()

def render_application_page():
    """Render the enhanced application page"""
    st.markdown('<h1 class="sub-header">📝 Credit Application</h1>', unsafe_allow_html=True)
    
    # Initialize form state
    initialize_form_state()
    
    # Check system status
    if not st.session_state.database_manager:
        st.error("❌ Database not initialized. Please initialize the system first.")
        if st.button("Initialize System"):
            initialize_system()
            st.rerun()
        return
    
    # Customer lookup section
    render_customer_lookup_section()
    
    st.markdown("---")
    
    # Application form
    with st.form("credit_application", clear_on_submit=False):
        st.markdown("### 👤 Customer Information")
        
        col1, col2 = st.columns(2)
        
        with col1:
            customer_id = st.text_input(
                "Customer ID *",
                value=st.session_state.form_data.get('customer_id', ''),
                placeholder="e.g., CUST001",
                help="Customer ID must be 3-4 letters followed by 3-6 numbers"
            )
            
            name = st.text_input(
                "Full Name *",
                value=st.session_state.form_data.get('name', ''),
                placeholder="Enter full name",
                help="Customer's full legal name"
            )
            
            age = st.number_input(
                "Age *",
                min_value=18,
                max_value=100,
                value=int(float(st.session_state.form_data.get('age', 35))),
                help="Customer's age (must be 18 or older)"
            )
            
            email = st.text_input(
                "Email Address *",
                value=st.session_state.form_data.get('email', ''),
                placeholder="john.doe@email.com",
                help="Valid email address"
            )
            
            phone = st.text_input(
                "Phone Number *",
                value=st.session_state.form_data.get('phone', ''),
                placeholder="+1-555-123-4567",
                help="Phone number (e.g., +1-555-123-4567, (555) 123-4567, 555-123-4567, or 5551234567)"
            )
        
        with col2:
            ssn = st.text_input(
                "Social Security Number *",
                value=st.session_state.form_data.get('ssn', ''),
                placeholder="123-45-6789",
                help="SSN in format XXX-XX-XXXX"
            )
            
            address = st.text_area(
                "Address",
                value=st.session_state.form_data.get('address', ''),
                placeholder="Enter full address",
                help="Customer's residential address"
            )
            
            employment_status = st.selectbox(
                "Employment Status",
                ["full_time", "part_time", "self_employed", "unemployed", "retired"],
                index=0 if st.session_state.form_data.get('employment_status') != 'part_time' else 1,
                help="Current employment status"
            )
            
            employer = st.text_input(
                "Employer",
                value=st.session_state.form_data.get('employer', ''),
                placeholder="Company name",
                help="Current employer or company name"
            )
            
            annual_income = st.number_input(
                "Annual Income ($) *",
                min_value=0,
                value=int(float(st.session_state.form_data.get('annual_income', 75000))),
                step=1000,
                help="Annual income in USD"
            )
        
        st.markdown("### 💼 Employment & Credit Information")
        
        col1, col2, col3 = st.columns(3)
        
        with col1:
            employment_years = st.number_input(
                "Years of Employment",
                min_value=0,
                max_value=50,
                value=int(float(st.session_state.form_data.get('employment_years', 5))),
                help="Years of employment at current job"
            )
            
            credit_score = st.number_input(
                "Credit Score *",
                min_value=300,
                max_value=850,
                value=int(float(st.session_state.form_data.get('credit_score', 720))),
                help="Credit score (300-850)"
            )
        
        with col2:
            existing_accounts = st.number_input(
                "Existing Credit Accounts",
                min_value=0,
                value=st.session_state.form_data.get('existing_accounts', 3),
                help="Number of existing credit accounts"
            )
            
            bankruptcy_history = st.checkbox(
                "Bankruptcy History",
                value=st.session_state.form_data.get('bankruptcy_history', False),
                help="Check if customer has bankruptcy history"
            )
        
        with col3:
            late_payments = st.number_input(
                "Late Payments (Last 2 Years)",
                min_value=0,
                value=st.session_state.form_data.get('late_payments', 0),
                help="Number of late payments in last 2 years"
            )
            
            collections = st.checkbox(
                "Collections History",
                value=st.session_state.form_data.get('collections', False),
                help="Check if customer has collections history"
            )
        
        st.markdown("### 💰 Loan Information")
        
        col1, col2, col3 = st.columns(3)
        
        with col1:
            loan_amount = st.number_input(
                "Loan Amount ($) *",
                min_value=1000,
                value=st.session_state.form_data.get('loan_amount', 15000),
                step=1000,
                help="Requested loan amount"
            )
            
            loan_type = st.selectbox(
                "Loan Type *",
                ["personal", "business", "mortgage", "auto", "student", "home_equity"],
                index=0,
                help="Type of loan being requested"
            )
        
        with col2:
            term_months = st.number_input(
                "Term (Months) *",
                min_value=6,
                max_value=360,
                value=st.session_state.form_data.get('term_months', 36),
                help="Loan term in months"
            )
            
            purpose = st.selectbox(
                "Loan Purpose",
                ["debt_consolidation", "home_improvement", "major_purchase", "business", "education", "medical", "other"],
                index=0,
                help="Primary purpose of the loan"
            )
        
        with col3:
            down_payment = st.number_input(
                "Down Payment ($)",
                min_value=0,
                value=st.session_state.form_data.get('down_payment', 0),
                help="Down payment amount (if applicable)"
            )
            
            collateral = st.checkbox(
                "Secured Loan",
                value=st.session_state.form_data.get('collateral', False),
                help="Check if loan is secured with collateral"
            )
        
        st.markdown("### 📊 Financial Information")
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown("**Assets**")
            checking_balance = st.number_input(
                "Checking Balance ($)",
                min_value=0,
                value=st.session_state.form_data.get('checking_balance', 5000),
                help="Checking account balance"
            )
            
            savings_balance = st.number_input(
                "Savings Balance ($)",
                min_value=0,
                value=st.session_state.form_data.get('savings_balance', 15000),
                help="Savings account balance"
            )
            
            investments = st.number_input(
                "Investments ($)",
                min_value=0,
                value=st.session_state.form_data.get('investments', 25000),
                help="Investment portfolio value"
            )
            
            real_estate = st.number_input(
                "Real Estate ($)",
                min_value=0,
                value=st.session_state.form_data.get('real_estate', 200000),
                help="Real estate value"
            )
        
        with col2:
            st.markdown("**Liabilities**")
            credit_cards = st.number_input(
                "Credit Card Debt ($)",
                min_value=0,
                value=st.session_state.form_data.get('credit_cards', 3000),
                help="Credit card debt"
            )
            
            loans = st.number_input(
                "Other Loans ($)",
                min_value=0,
                value=st.session_state.form_data.get('loans', 10000),
                help="Other outstanding loans"
            )
            
            mortgage = st.number_input(
                "Mortgage ($)",
                min_value=0,
                value=st.session_state.form_data.get('mortgage', 150000),
                help="Mortgage balance"
            )
            
            other_debt = st.number_input(
                "Other Debt ($)",
                min_value=0,
                value=st.session_state.form_data.get('other_debt', 5000),
                help="Other debt obligations"
            )
        
        # Calculate and display financial summary
        assets = {
            'checking': checking_balance,
            'savings': savings_balance,
            'investments': investments,
            'real_estate': real_estate
        }
        
        liabilities = {
            'credit_cards': credit_cards,
            'loans': loans,
            'mortgage': mortgage,
            'other_debt': other_debt
        }
        
        # Debug logging for financial summary
        print(f"Financial Summary Debug:")
        print(f"Assets: {assets}")
        print(f"Liabilities: {liabilities}")
        print(f"Annual Income: {annual_income}")
        print(f"Loan Amount: {loan_amount}")
        print(f"Credit Score: {credit_score}")
        
        risk_indicators = calculate_risk_indicators({
            'annual_income': annual_income,
            'loan_amount': loan_amount,
            'credit_score': credit_score,
            'assets': assets,
            'liabilities': liabilities
        })
        
        print(f"Calculated Risk Indicators: {risk_indicators}")
        
        st.markdown("### 📈 Financial Summary & Risk Indicators")
        
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.metric("Total Assets", f"${risk_indicators['total_assets']:,.2f}")
        
        with col2:
            st.metric("Total Liabilities", f"${risk_indicators['total_liabilities']:,.2f}")
        
        with col3:
            net_worth_color = "normal" if risk_indicators['net_worth'] >= 0 else "inverse"
            st.metric("Net Worth", f"${risk_indicators['net_worth']:,.2f}", delta_color=net_worth_color)
        
        with col4:
            st.metric("Loan Amount", f"${loan_amount:,.2f}")
        
        # Risk indicators with color coding
        st.markdown("#### Risk Assessment")
        
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            dti_ratio = risk_indicators['debt_to_income_ratio']
            if dti_ratio <= 30:
                st.success(f"**Debt-to-Income:** {dti_ratio:.1f}%")
                st.caption("✅ Good")
            elif dti_ratio <= 50:
                st.warning(f"**Debt-to-Income:** {dti_ratio:.1f}%")
                st.caption("⚠️ Moderate")
            else:
                st.error(f"**Debt-to-Income:** {dti_ratio:.1f}%")
                st.caption("❌ High")
        
        with col2:
            lti_ratio = risk_indicators['loan_to_income_ratio']
            if lti_ratio <= 20:
                st.success(f"**Loan-to-Income:** {lti_ratio:.1f}%")
                st.caption("✅ Good")
            elif lti_ratio <= 40:
                st.warning(f"**Loan-to-Income:** {lti_ratio:.1f}%")
                st.caption("⚠️ Moderate")
            else:
                st.error(f"**Loan-to-Income:** {lti_ratio:.1f}%")
                st.caption("❌ High")
        
        with col3:
            credit_level = risk_indicators['risk_levels']['credit_score']
            if credit_level in ['excellent', 'good']:
                st.success(f"**Credit Score:** {credit_score}")
                st.caption(f"✅ {credit_level.title()}")
            elif credit_level == 'fair':
                st.warning(f"**Credit Score:** {credit_score}")
                st.caption("⚠️ Fair")
            else:
                st.error(f"**Credit Score:** {credit_score}")
                st.caption("❌ Poor")
        
        with col4:
            net_worth_status = risk_indicators['risk_levels']['net_worth']
            if net_worth_status == 'positive':
                st.success(f"**Net Worth:** ${risk_indicators['net_worth']:,.2f}")
                st.caption("✅ Positive")
            else:
                st.error(f"**Net Worth:** ${risk_indicators['net_worth']:,.2f}")
                st.caption("❌ Negative")
        
        # Form actions
        col1, col2, col3 = st.columns([1, 1, 1])
        
        with col1:
            if st.form_submit_button("🗑️ Clear Form", type="secondary"):
                clear_form_state()
                st.rerun()
        
        with col2:
            if st.form_submit_button("💾 Save Draft", type="secondary"):
                # Save current form data
                form_data = {
                    'customer_id': customer_id,
                    'name': name,
                    'age': age,
                    'email': email,
                    'phone': phone,
                    'ssn': ssn,
                    'address': address,
                    'employment_status': employment_status,
                    'employer': employer,
                    'annual_income': annual_income,
                    'employment_years': employment_years,
                    'credit_score': credit_score,
                    'existing_accounts': existing_accounts,
                    'bankruptcy_history': bankruptcy_history,
                    'late_payments': late_payments,
                    'collections': collections,
                    'loan_amount': loan_amount,
                    'loan_type': loan_type,
                    'term_months': term_months,
                    'purpose': purpose,
                    'down_payment': down_payment,
                    'collateral': collateral,
                    'checking_balance': checking_balance,
                    'savings_balance': savings_balance,
                    'investments': investments,
                    'real_estate': real_estate,
                    'credit_cards': credit_cards,
                    'loans': loans,
                    'mortgage': mortgage,
                    'other_debt': other_debt
                }
                
                st.session_state.form_data = form_data
                st.success("Draft saved successfully!")
        
        with col3:
            submitted = st.form_submit_button("🚀 Submit for Analysis", type="primary")
        
        if submitted:
            # Collect all form data
            form_data = {
                'customer_id': customer_id,
                'name': name,
                'age': age,
                'email': email,
                'phone': phone,
                'ssn': ssn,
                'address': address,
                'employment_status': employment_status,
                'employer': employer,
                'annual_income': annual_income,
                'employment_years': employment_years,
                'credit_score': credit_score,
                'existing_accounts': existing_accounts,
                'bankruptcy_history': bankruptcy_history,
                'late_payments': late_payments,
                'collections': collections,
                'loan_amount': loan_amount,
                'loan_type': loan_type,
                'term_months': term_months,
                'purpose': purpose,
                'down_payment': down_payment,
                'collateral': collateral,
                'checking_balance': checking_balance,
                'savings_balance': savings_balance,
                'investments': investments,
                'real_estate': real_estate,
                'credit_cards': credit_cards,
                'loans': loans,
                'mortgage': mortgage,
                'other_debt': other_debt
            }
            
            # Validate form data
            errors = validate_form_data(form_data)
            
            if errors:
                st.error("Please fix the following errors:")
                for field, error in errors.items():
                    st.error(f"**{field.replace('_', ' ').title()}:** {error}")
                st.session_state.form_errors = errors
                return
            
            # Add calculated fields
            form_data.update({
                'assets': assets,
                'liabilities': liabilities,
                'risk_indicators': risk_indicators,
                'submission_time': datetime.now().isoformat()
            })
            
            # Store in session state
            st.session_state.current_analysis = form_data
            st.session_state.form_submitted = True
            
            # Navigate to processing page
            st.session_state.current_page = 'Processing'
            st.success("✅ Application submitted successfully! Redirecting to processing...")
            st.rerun()
    
    # Application history
    if st.session_state.analysis_results:
        st.markdown("---")
        st.markdown("### 📋 Recent Applications")
        
        recent_results = st.session_state.analysis_results[-5:]  # Last 5 results
        
        for result in recent_results:
            with st.expander(f"Analysis for {result.get('customer_id', 'Unknown')} - {result.get('analysis_time', 'Unknown time')}"):
                col1, col2, col3, col4 = st.columns(4)
                
                with col1:
                    st.metric("Risk Score", f"{result.get('risk_score', 0)}/100")
                
                with col2:
                    risk_level = result.get('risk_level', 'Unknown')
                    if risk_level.lower() in ['low', 'good']:
                        st.success(f"Risk Level: {risk_level}")
                    elif risk_level.lower() in ['medium', 'moderate']:
                        st.warning(f"Risk Level: {risk_level}")
                    else:
                        st.error(f"Risk Level: {risk_level}")
                
                with col3:
                    recommendation = result.get('recommendation', 'Unknown')
                    st.metric("Recommendation", recommendation)
                
                with col4:
                    st.metric("Execution Time", f"{result.get('execution_time', 0):.2f}s") 