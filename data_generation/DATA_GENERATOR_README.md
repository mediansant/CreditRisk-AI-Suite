# 🏦 Credit Risk Data Generator

A comprehensive synthetic data generator for the Credit Risk AI Suite. This tool creates realistic customer data, financial records, loan applications, market data, and credit history for testing and development.

## ✨ Features

- **Realistic Customer Data**: Generate customers with realistic names, addresses, employment info, and credit scores
- **Financial Records**: Create transaction history with deposits, withdrawals, payments, and transfers
- **Loan Applications**: Generate various types of loan applications with risk assessments
- **Market Data**: Create synthetic market indicators and economic data
- **Credit History**: Generate comprehensive credit account history
- **Database Integration**: Direct MySQL database integration with proper error handling
- **Data Export**: Export sample data to JSON for external analysis

## 🚀 Quick Start

### 1. Install Dependencies

```bash
# Install required packages
python install_data_generator_deps.py

# Or install manually
pip install mysql-connector-python faker numpy pandas
```

### 2. Configure Database

Ensure your MySQL database is running and configured. The generator uses these environment variables:

```bash
DB_HOST=localhost
DB_PORT=3306
DB_NAME=credit_risk_db
DB_USER=credit_user
DB_PASSWORD=CreditUser2024!
```

### 3. Run Data Generation

```bash
python data_generator.py
```

The script will prompt you for:
- Number of customers to generate (default: 100)
- Days of market data to generate (default: 365)
- Whether to export sample data to JSON

## 📊 Generated Data

### Customers Table
- Customer ID, name, email, phone
- Date of birth, SSN, address information
- Employment status, employer, job title
- Annual income, credit score

### Financial Records Table
- Transaction types: deposits, withdrawals, payments, transfers
- Account types: checking, savings, credit cards, investments
- Realistic transaction amounts and balances
- Multiple financial institutions

### Loan Applications Table
- Loan types: personal, auto, home, business, student, credit card
- Risk scores and interest rates
- Collateral information
- Application status and dates

### Market Data Table
- Economic indicators: Federal Funds Rate, Prime Rate, Mortgage rates
- Market indices: S&P 500, Treasury rates
- Daily data with realistic variations
- Historical trends

### Credit History Table
- Multiple account types per customer
- Payment history (24 months)
- Credit limits and current balances
- Account status and institutions

## 🔧 Configuration

### Database Settings

Edit the `DatabaseConfig` class in `data_generator.py` to customize database connection:

```python
class DatabaseConfig:
    def __init__(self):
        self.host = os.getenv('DB_HOST', 'localhost')
        self.port = int(os.getenv('DB_PORT', 3306))
        self.database = os.getenv('DB_NAME', 'credit_risk_db')
        self.user = os.getenv('DB_USER', 'credit_user')
        self.password = os.getenv('DB_PASSWORD', 'CreditUser2024!')
```

### Data Generation Parameters

Customize the data generation by modifying these methods:

- `generate_credit_score()`: Adjust credit score distribution
- `generate_income()`: Modify income ranges and distribution
- `generate_financial_records()`: Change transaction types and amounts
- `generate_loan_applications()`: Adjust loan types and risk calculations

## 📈 Data Quality Features

### Realistic Distributions
- Credit scores follow real-world distribution (more people in middle ranges)
- Income levels reflect actual economic distribution
- Payment history includes realistic delinquency rates

### Data Relationships
- Customer data influences loan application risk scores
- Financial records maintain consistent account balances
- Credit history affects overall credit scores

### Temporal Consistency
- Transaction dates are chronologically ordered
- Market data shows realistic daily variations
- Application dates align with customer creation dates

## 🛠️ Usage Examples

### Generate Small Dataset for Testing
```bash
python data_generator.py
# Enter: 10 customers, 30 days market data
```

### Generate Large Dataset for Production Testing
```bash
python data_generator.py
# Enter: 1000 customers, 365 days market data
```

### Export Sample Data Only
```python
from data_generator import SyntheticDataGenerator, DatabaseConfig

db_config = DatabaseConfig()
generator = SyntheticDataGenerator(db_config)
generator.export_sample_data("my_sample_data.json")
```

## 🔍 Data Validation

The generator includes built-in validation:

- **Unique IDs**: All customer, application, and record IDs are unique
- **Data Types**: Proper data types for database insertion
- **Constraints**: Respects database constraints and relationships
- **Error Handling**: Graceful handling of insertion errors

## 📊 Sample Output

### Customer Data
```json
{
  "customer_id": "CUST123456",
  "name": "John Smith",
  "email": "john.smith@email.com",
  "annual_income": 75000.00,
  "credit_score": 720,
  "employment_status": "Full-time"
}
```

### Loan Application
```json
{
  "application_id": "APP789012",
  "loan_type": "Auto",
  "loan_amount": 25000.00,
  "risk_score": 685,
  "interest_rate": 5.25,
  "status": "Approved"
}
```

## 🚨 Troubleshooting

### Database Connection Issues
- Verify MySQL server is running
- Check database credentials in environment variables
- Ensure database exists and user has proper permissions

### Memory Issues with Large Datasets
- Generate data in smaller batches
- Increase system memory allocation
- Use database transactions for better performance

### Data Quality Issues
- Review the generation parameters in the code
- Adjust distributions for your specific use case
- Validate generated data against business rules

## 🔄 Integration with Credit Risk AI Suite

The generated data is fully compatible with the Credit Risk AI Suite:

1. **Customer Analysis**: Use generated customer data for risk assessment
2. **Financial Modeling**: Analyze transaction patterns and cash flow
3. **Market Analysis**: Incorporate synthetic market data into risk models
4. **Credit Scoring**: Test credit scoring algorithms with realistic data
5. **Performance Testing**: Validate system performance with large datasets

## 📝 License

This data generator is part of the Credit Risk AI Suite and follows the same license terms.

---

**Status**: ✅ **Ready for Use**  
**Version**: 1.0.0  
**Last Updated**: December 2024 