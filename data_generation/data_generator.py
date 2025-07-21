#!/usr/bin/env python3
"""
Credit Risk Analysis - Synthetic Data Generator
Generates realistic synthetic data for testing and development of the credit risk analysis system.
"""

import json
import logging
import random
import string
import time
from datetime import datetime, timedelta, date
from typing import Dict, List, Any, Optional
import mysql.connector
from mysql.connector import pooling
import os
import numpy as np
import pandas as pd
from faker import Faker

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Initialize Faker for realistic data generation
fake = Faker()

class DatabaseConfig:
    """Database configuration"""
    
    def __init__(self):
        self.host = os.getenv('DB_HOST', 'localhost')
        self.port = int(os.getenv('DB_PORT', 3306))
        self.database = os.getenv('DB_NAME', 'credit_risk_db')
        self.user = os.getenv('DB_USER', 'credit_user')
        self.password = os.getenv('DB_PASSWORD', 'CreditUser2024!')
        self.charset = 'utf8mb4'

class SyntheticDataGenerator:
    """Generates synthetic data for credit risk analysis"""
    
    def __init__(self, db_config: DatabaseConfig):
        self.db_config = db_config
        self.connection = None
        self.logger = logging.getLogger(self.__class__.__name__)
        
    def connect_database(self):
        """Connect to MySQL database"""
        try:
            self.connection = mysql.connector.connect(
                host=self.db_config.host,
                port=self.db_config.port,
                database=self.db_config.database,
                user=self.db_config.user,
                password=self.db_config.password,
                charset=self.db_config.charset,
                autocommit=True
            )
            self.logger.info("Connected to database successfully")
        except mysql.connector.Error as e:
            self.logger.error(f"Database connection failed: {str(e)}")
            raise
    
    def create_tables(self):
        """Create necessary database tables"""
        tables = {
            'customers': """
                CREATE TABLE IF NOT EXISTS customers (
                    customer_id VARCHAR(50) PRIMARY KEY,
                    name VARCHAR(100) NOT NULL,
                    email VARCHAR(100) UNIQUE NOT NULL,
                    phone VARCHAR(20),
                    date_of_birth DATE,
                    ssn VARCHAR(11),
                    address TEXT,
                    city VARCHAR(50),
                    state VARCHAR(2),
                    zip_code VARCHAR(10),
                    employment_status VARCHAR(50),
                    employer VARCHAR(100),
                    job_title VARCHAR(100),
                    annual_income DECIMAL(12,2),
                    credit_score INT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
                )
            """,
            'financial_records': """
                CREATE TABLE IF NOT EXISTS financial_records (
                    record_id VARCHAR(50) PRIMARY KEY,
                    customer_id VARCHAR(50),
                    record_type VARCHAR(50),
                    amount DECIMAL(12,2),
                    description TEXT,
                    transaction_date DATE,
                    balance DECIMAL(12,2),
                    account_type VARCHAR(50),
                    institution VARCHAR(100),
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (customer_id) REFERENCES customers(customer_id)
                )
            """,
            'loan_applications': """
                CREATE TABLE IF NOT EXISTS loan_applications (
                    application_id VARCHAR(50) PRIMARY KEY,
                    customer_id VARCHAR(50),
                    loan_type VARCHAR(50),
                    loan_amount DECIMAL(12,2),
                    term_months INT,
                    purpose VARCHAR(100),
                    collateral_value DECIMAL(12,2),
                    collateral_type VARCHAR(50),
                    application_date DATE,
                    status VARCHAR(50),
                    risk_score INT,
                    interest_rate DECIMAL(5,2),
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (customer_id) REFERENCES customers(customer_id)
                )
            """,
            'market_data': """
                CREATE TABLE IF NOT EXISTS market_data (
                    data_id VARCHAR(50) PRIMARY KEY,
                    date DATE,
                    indicator VARCHAR(50),
                    value DECIMAL(10,4),
                    change_percent DECIMAL(5,2),
                    source VARCHAR(100),
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """,
            'credit_history': """
                CREATE TABLE IF NOT EXISTS credit_history (
                    history_id VARCHAR(50) PRIMARY KEY,
                    customer_id VARCHAR(50),
                    account_type VARCHAR(50),
                    account_number VARCHAR(50),
                    institution VARCHAR(100),
                    credit_limit DECIMAL(12,2),
                    current_balance DECIMAL(12,2),
                    payment_history TEXT,
                    open_date DATE,
                    status VARCHAR(50),
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (customer_id) REFERENCES customers(customer_id)
                )
            """
        }
        
        cursor = self.connection.cursor()
        for table_name, create_sql in tables.items():
            try:
                cursor.execute(create_sql)
                self.logger.info(f"Created table: {table_name}")
            except mysql.connector.Error as e:
                self.logger.warning(f"Table {table_name} might already exist: {str(e)}")
        
        cursor.close()
    
    def generate_customer_id(self) -> str:
        """Generate unique customer ID"""
        return f"CUST{random.randint(100000, 999999)}"
    
    def generate_ssn(self) -> str:
        """Generate realistic SSN"""
        return f"{random.randint(100, 999)}-{random.randint(10, 99)}-{random.randint(1000, 9999)}"
    
    def generate_phone(self) -> str:
        """Generate realistic phone number"""
        return f"({random.randint(200, 999)}) {random.randint(100, 999)}-{random.randint(1000, 9999)}"
    
    def generate_credit_score(self) -> int:
        """Generate realistic credit score"""
        # Weighted distribution: more people in middle ranges
        weights = [0.05, 0.1, 0.2, 0.3, 0.2, 0.1, 0.05]
        ranges = [(300, 499), (500, 599), (600, 649), (650, 699), (700, 749), (750, 799), (800, 850)]
        chosen_range = random.choices(ranges, weights=weights)[0]
        return random.randint(chosen_range[0], chosen_range[1])
    
    def generate_income(self) -> float:
        """Generate realistic annual income"""
        # Weighted distribution for realistic income distribution
        weights = [0.3, 0.4, 0.2, 0.08, 0.02]
        ranges = [(20000, 50000), (50001, 80000), (80001, 120000), (120001, 200000), (200001, 500000)]
        chosen_range = random.choices(ranges, weights=weights)[0]
        return round(random.uniform(chosen_range[0], chosen_range[1]), 2)
    
    def generate_customer_data(self, count: int = 100) -> List[Dict[str, Any]]:
        """Generate synthetic customer data"""
        customers = []
        
        for i in range(count):
            customer = {
                'customer_id': self.generate_customer_id(),
                'name': fake.name(),
                'email': fake.email(),
                'phone': self.generate_phone(),
                'date_of_birth': fake.date_of_birth(minimum_age=18, maximum_age=80),
                'ssn': self.generate_ssn(),
                'address': fake.street_address(),
                'city': fake.city(),
                'state': fake.state_abbr(),
                'zip_code': fake.zipcode(),
                'employment_status': random.choice(['Full-time', 'Part-time', 'Self-employed', 'Retired', 'Unemployed']),
                'employer': fake.company() if random.random() > 0.1 else None,
                'job_title': fake.job() if random.random() > 0.1 else None,
                'annual_income': self.generate_income(),
                'credit_score': self.generate_credit_score()
            }
            customers.append(customer)
        
        return customers
    
    def generate_financial_records(self, customer_ids: List[str], records_per_customer: int = 10) -> List[Dict[str, Any]]:
        """Generate synthetic financial records"""
        records = []
        record_types = ['Deposit', 'Withdrawal', 'Payment', 'Transfer', 'Fee', 'Interest']
        account_types = ['Checking', 'Savings', 'Credit Card', 'Investment', 'Loan']
        institutions = ['Bank of America', 'Chase', 'Wells Fargo', 'Citibank', 'US Bank', 'PNC Bank']
        
        for customer_id in customer_ids:
            balance = random.uniform(1000, 50000)
            
            for i in range(records_per_customer):
                record_type = random.choice(record_types)
                amount = random.uniform(10, 5000)
                
                # Adjust balance based on transaction type
                if record_type in ['Deposit', 'Payment']:
                    balance += amount
                else:
                    balance = max(0, balance - amount)
                
                record = {
                    'record_id': f"REC{random.randint(100000, 999999)}",
                    'customer_id': customer_id,
                    'record_type': record_type,
                    'amount': round(amount, 2),
                    'description': fake.sentence(),
                    'transaction_date': fake.date_between(start_date='-1y', end_date='today'),
                    'balance': round(balance, 2),
                    'account_type': random.choice(account_types),
                    'institution': random.choice(institutions)
                }
                records.append(record)
        
        return records
    
    def generate_loan_applications(self, customer_ids: List[str], applications_per_customer: int = 2) -> List[Dict[str, Any]]:
        """Generate synthetic loan applications"""
        applications = []
        loan_types = ['Personal', 'Auto', 'Home', 'Business', 'Student', 'Credit Card']
        purposes = ['Debt Consolidation', 'Home Improvement', 'Vehicle Purchase', 'Education', 'Business Expansion', 'Emergency']
        collateral_types = ['Vehicle', 'Property', 'Investment', 'Equipment', 'None']
        statuses = ['Pending', 'Approved', 'Denied', 'Under Review', 'Conditional']
        
        for customer_id in customer_ids:
            for i in range(applications_per_customer):
                loan_type = random.choice(loan_types)
                loan_amount = random.uniform(5000, 500000)
                term_months = random.choice([12, 24, 36, 48, 60, 72, 84, 120, 180, 360])
                
                # Generate risk score based on loan characteristics
                base_risk = random.randint(300, 850)
                if loan_amount > 100000:
                    base_risk -= 50
                if term_months > 60:
                    base_risk += 30
                
                risk_score = max(300, min(850, base_risk))
                
                # Calculate interest rate based on risk score
                base_rate = 3.5
                risk_adjustment = (850 - risk_score) * 0.1
                interest_rate = round(base_rate + risk_adjustment, 2)
                
                application = {
                    'application_id': f"APP{random.randint(100000, 999999)}",
                    'customer_id': customer_id,
                    'loan_type': loan_type,
                    'loan_amount': round(loan_amount, 2),
                    'term_months': term_months,
                    'purpose': random.choice(purposes),
                    'collateral_value': round(loan_amount * random.uniform(0.8, 1.2), 2) if random.random() > 0.3 else 0,
                    'collateral_type': random.choice(collateral_types),
                    'application_date': fake.date_between(start_date='-6m', end_date='today'),
                    'status': random.choice(statuses),
                    'risk_score': risk_score,
                    'interest_rate': interest_rate
                }
                applications.append(application)
        
        return applications
    
    def generate_market_data(self, days: int = 365) -> List[Dict[str, Any]]:
        """Generate synthetic market data"""
        market_data = []
        indicators = ['Federal Funds Rate', 'Prime Rate', '30-Year Fixed Mortgage', '5-Year Treasury', 'S&P 500', 'Unemployment Rate']
        
        start_date = datetime.now() - timedelta(days=days)
        
        for i in range(days):
            current_date = start_date + timedelta(days=i)
            
            for indicator in indicators:
                # Generate realistic values for each indicator
                if 'Rate' in indicator:
                    base_value = random.uniform(2.0, 8.0)
                elif 'Mortgage' in indicator:
                    base_value = random.uniform(3.0, 7.0)
                elif 'Treasury' in indicator:
                    base_value = random.uniform(1.0, 5.0)
                elif 'S&P' in indicator:
                    base_value = random.uniform(3000, 5000)
                else:
                    base_value = random.uniform(3.0, 8.0)
                
                # Add some daily variation
                daily_change = random.uniform(-0.1, 0.1)
                value = round(base_value + daily_change, 4)
                change_percent = round(daily_change / base_value * 100, 2)
                
                data_point = {
                    'data_id': f"MRK{random.randint(100000, 999999)}",
                    'date': current_date.date(),
                    'indicator': indicator,
                    'value': value,
                    'change_percent': change_percent,
                    'source': 'Synthetic Market Data'
                }
                market_data.append(data_point)
        
        return market_data
    
    def generate_credit_history(self, customer_ids: List[str], accounts_per_customer: int = 3) -> List[Dict[str, Any]]:
        """Generate synthetic credit history"""
        credit_history = []
        account_types = ['Credit Card', 'Auto Loan', 'Personal Loan', 'Mortgage', 'Student Loan']
        institutions = ['Chase', 'Bank of America', 'Wells Fargo', 'Citibank', 'American Express', 'Discover']
        statuses = ['Open', 'Closed', 'Delinquent', 'Paid Off']
        
        for customer_id in customer_ids:
            for i in range(accounts_per_customer):
                account_type = random.choice(account_types)
                credit_limit = random.uniform(1000, 50000)
                current_balance = random.uniform(0, credit_limit * 0.8)
                
                # Generate payment history (24 months)
                payment_history = []
                for month in range(24):
                    payment_status = random.choices(['On Time', 'Late', 'Missed'], weights=[0.85, 0.12, 0.03])[0]
                    payment_history.append(payment_status)
                
                history = {
                    'history_id': f"CRD{random.randint(100000, 999999)}",
                    'customer_id': customer_id,
                    'account_type': account_type,
                    'account_number': f"****{random.randint(1000, 9999)}",
                    'institution': random.choice(institutions),
                    'credit_limit': round(credit_limit, 2),
                    'current_balance': round(current_balance, 2),
                    'payment_history': json.dumps(payment_history),
                    'open_date': fake.date_between(start_date='-5y', end_date='-6m'),
                    'status': random.choice(statuses)
                }
                credit_history.append(history)
        
        return credit_history
    
    def insert_customers(self, customers: List[Dict[str, Any]]):
        """Insert customers into database"""
        cursor = self.connection.cursor()
        
        insert_sql = """
            INSERT INTO customers (
                customer_id, name, email, phone, date_of_birth, ssn, address, 
                city, state, zip_code, employment_status, employer, job_title, 
                annual_income, credit_score
            ) VALUES (
                %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s
            )
        """
        
        for customer in customers:
            try:
                cursor.execute(insert_sql, (
                    customer['customer_id'], customer['name'], customer['email'],
                    customer['phone'], customer['date_of_birth'], customer['ssn'],
                    customer['address'], customer['city'], customer['state'],
                    customer['zip_code'], customer['employment_status'],
                    customer['employer'], customer['job_title'],
                    customer['annual_income'], customer['credit_score']
                ))
            except mysql.connector.Error as e:
                self.logger.warning(f"Could not insert customer {customer['customer_id']}: {str(e)}")
        
        self.connection.commit()
        cursor.close()
        self.logger.info(f"Inserted {len(customers)} customers")
    
    def insert_financial_records(self, records: List[Dict[str, Any]]):
        """Insert financial records into database"""
        cursor = self.connection.cursor()
        
        insert_sql = """
            INSERT INTO financial_records (
                record_id, customer_id, record_type, amount, description,
                transaction_date, balance, account_type, institution
            ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
        """
        
        for record in records:
            try:
                cursor.execute(insert_sql, (
                    record['record_id'], record['customer_id'], record['record_type'],
                    record['amount'], record['description'], record['transaction_date'],
                    record['balance'], record['account_type'], record['institution']
                ))
            except mysql.connector.Error as e:
                self.logger.warning(f"Could not insert record {record['record_id']}: {str(e)}")
        
        self.connection.commit()
        cursor.close()
        self.logger.info(f"Inserted {len(records)} financial records")
    
    def insert_loan_applications(self, applications: List[Dict[str, Any]]):
        """Insert loan applications into database"""
        cursor = self.connection.cursor()
        
        insert_sql = """
            INSERT INTO loan_applications (
                application_id, customer_id, loan_type, loan_amount, term_months,
                purpose, collateral_value, collateral_type, application_date,
                status, risk_score, interest_rate
            ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
        """
        
        for application in applications:
            try:
                cursor.execute(insert_sql, (
                    application['application_id'], application['customer_id'],
                    application['loan_type'], application['loan_amount'],
                    application['term_months'], application['purpose'],
                    application['collateral_value'], application['collateral_type'],
                    application['application_date'], application['status'],
                    application['risk_score'], application['interest_rate']
                ))
            except mysql.connector.Error as e:
                self.logger.warning(f"Could not insert application {application['application_id']}: {str(e)}")
        
        self.connection.commit()
        cursor.close()
        self.logger.info(f"Inserted {len(applications)} loan applications")
    
    def insert_market_data(self, market_data: List[Dict[str, Any]]):
        """Insert market data into database"""
        cursor = self.connection.cursor()
        
        insert_sql = """
            INSERT INTO market_data (
                data_id, date, indicator, value, change_percent, source
            ) VALUES (%s, %s, %s, %s, %s, %s)
        """
        
        for data_point in market_data:
            try:
                cursor.execute(insert_sql, (
                    data_point['data_id'], data_point['date'],
                    data_point['indicator'], data_point['value'],
                    data_point['change_percent'], data_point['source']
                ))
            except mysql.connector.Error as e:
                self.logger.warning(f"Could not insert market data {data_point['data_id']}: {str(e)}")
        
        self.connection.commit()
        cursor.close()
        self.logger.info(f"Inserted {len(market_data)} market data points")
    
    def insert_credit_history(self, credit_history: List[Dict[str, Any]]):
        """Insert credit history into database"""
        cursor = self.connection.cursor()
        
        insert_sql = """
            INSERT INTO credit_history (
                history_id, customer_id, account_type, account_number,
                institution, credit_limit, current_balance, payment_history,
                open_date, status
            ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
        """
        
        for history in credit_history:
            try:
                cursor.execute(insert_sql, (
                    history['history_id'], history['customer_id'],
                    history['account_type'], history['account_number'],
                    history['institution'], history['credit_limit'],
                    history['current_balance'], history['payment_history'],
                    history['open_date'], history['status']
                ))
            except mysql.connector.Error as e:
                self.logger.warning(f"Could not insert credit history {history['history_id']}: {str(e)}")
        
        self.connection.commit()
        cursor.close()
        self.logger.info(f"Inserted {len(credit_history)} credit history records")
    
    def generate_all_data(self, customer_count: int = 100, days_of_market_data: int = 365):
        """Generate and insert all synthetic data"""
        self.logger.info("Starting synthetic data generation...")
        
        try:
            # Connect to database
            self.connect_database()
            
            # Create tables
            self.create_tables()
            
            # Generate customers
            self.logger.info(f"Generating {customer_count} customers...")
            customers = self.generate_customer_data(customer_count)
            self.insert_customers(customers)
            
            customer_ids = [c['customer_id'] for c in customers]
            
            # Generate financial records
            self.logger.info("Generating financial records...")
            financial_records = self.generate_financial_records(customer_ids, records_per_customer=15)
            self.insert_financial_records(financial_records)
            
            # Generate loan applications
            self.logger.info("Generating loan applications...")
            loan_applications = self.generate_loan_applications(customer_ids, applications_per_customer=3)
            self.insert_loan_applications(loan_applications)
            
            # Generate market data
            self.logger.info(f"Generating {days_of_market_data} days of market data...")
            market_data = self.generate_market_data(days_of_market_data)
            self.insert_market_data(market_data)
            
            # Generate credit history
            self.logger.info("Generating credit history...")
            credit_history = self.generate_credit_history(customer_ids, accounts_per_customer=4)
            self.insert_credit_history(credit_history)
            
            self.logger.info("Synthetic data generation completed successfully!")
            
        except Exception as e:
            self.logger.error(f"Error generating data: {str(e)}")
            raise
        finally:
            if self.connection:
                self.connection.close()
    
    def export_sample_data(self, filename: str = "sample_data.json"):
        """Export a sample of generated data to JSON file"""
        try:
            self.connect_database()
            cursor = self.connection.cursor(dictionary=True)
            
            # Get sample data from each table
            sample_data = {}
            
            # Sample customers
            cursor.execute("SELECT * FROM customers LIMIT 5")
            sample_data['customers'] = cursor.fetchall()
            
            # Sample financial records
            cursor.execute("SELECT * FROM financial_records LIMIT 10")
            sample_data['financial_records'] = cursor.fetchall()
            
            # Sample loan applications
            cursor.execute("SELECT * FROM loan_applications LIMIT 5")
            sample_data['loan_applications'] = cursor.fetchall()
            
            # Sample market data
            cursor.execute("SELECT * FROM market_data LIMIT 20")
            sample_data['market_data'] = cursor.fetchall()
            
            # Sample credit history
            cursor.execute("SELECT * FROM credit_history LIMIT 10")
            sample_data['credit_history'] = cursor.fetchall()
            
            cursor.close()
            
            # Convert datetime objects to strings for JSON serialization
            def convert_datetime(obj):
                if isinstance(obj, datetime):
                    return obj.isoformat()
                elif isinstance(obj, date):
                    return obj.isoformat()
                return obj
            
            # Export to JSON
            with open(filename, 'w') as f:
                json.dump(sample_data, f, default=convert_datetime, indent=2)
            
            self.logger.info(f"Sample data exported to {filename}")
            
        except Exception as e:
            self.logger.error(f"Error exporting sample data: {str(e)}")
            raise
        finally:
            if self.connection:
                self.connection.close()

def main():
    """Main function to run data generation"""
    print("🏦 Credit Risk Analysis - Synthetic Data Generator")
    print("=" * 50)
    
    # Get user input
    try:
        customer_count = int(input("Number of customers to generate (default 100): ") or "100")
        market_days = int(input("Days of market data to generate (default 365): ") or "365")
        
        # Initialize generator
        db_config = DatabaseConfig()
        generator = SyntheticDataGenerator(db_config)
        
        # Generate data
        generator.generate_all_data(customer_count, market_days)
        
        # Export sample data
        export_sample = input("Export sample data to JSON? (y/n, default y): ").lower() != 'n'
        if export_sample:
            generator.export_sample_data()
        
        print("\n✅ Data generation completed successfully!")
        print(f"Generated {customer_count} customers with associated data")
        print(f"Generated {market_days} days of market data")
        
    except KeyboardInterrupt:
        print("\n❌ Data generation cancelled by user")
    except Exception as e:
        print(f"\n❌ Error: {str(e)}")
        logger.error(f"Data generation failed: {str(e)}")

if __name__ == "__main__":
    main() 