# Data Generation Module

This directory contains all scripts and documentation related to synthetic data generation for the Credit Risk AI Suite.

## 📁 Contents

### Core Scripts
- **`data_generator.py`** - Main synthetic data generation script
- **`install_data_generator_deps.py`** - Dependency installation script
- **`DATA_GENERATOR_README.md`** - Detailed documentation for data generation

## 🚀 Quick Start

1. **Install Dependencies:**
   ```bash
   python install_data_generator_deps.py
   ```

2. **Configure Database:**
   - Set up MySQL database connection
   - Update environment variables in `env_example.txt`

3. **Generate Data:**
   ```bash
   python data_generator.py
   ```

## 📊 Generated Data Types

The data generator creates synthetic data for:

- **Customer Information** - Personal details, contact info, employment
- **Financial Records** - Income, expenses, assets, liabilities
- **Loan Applications** - Application details, requested amounts, terms
- **Market Data** - Interest rates, economic indicators, market conditions
- **Credit History** - Credit scores, payment history, utilization

## 🔧 Configuration

### Database Settings
```bash
# MySQL Configuration
DB_HOST=localhost
DB_PORT=3306
DB_NAME=credit_risk_analysis
DB_USER=your_username
DB_PASSWORD=your_password
```

### Data Generation Settings
```python
# Default settings in data_generator.py
CUSTOMER_COUNT = 1000
FINANCIAL_RECORDS_PER_CUSTOMER = 5
LOAN_APPLICATIONS_PER_CUSTOMER = 2
MARKET_DATA_POINTS = 100
CREDIT_HISTORY_ENTRIES = 10
```

## 📈 Features

- **Realistic Data Generation** - Uses Faker library for authentic-looking data
- **Database Integration** - Direct MySQL connection with error handling
- **Configurable Volumes** - Adjustable data generation amounts
- **Data Export** - JSON export for testing and development
- **Validation** - Data integrity checks and validation
- **Logging** - Comprehensive logging for debugging

## 🛠️ Customization

### Adding New Data Types
1. Create new table schema in `data_generator.py`
2. Add generation function following existing patterns
3. Update main generation loop
4. Add validation and export functions

### Modifying Data Patterns
- Edit generation functions to change data distributions
- Adjust ranges for numerical values
- Modify categorical data options
- Update correlation patterns between fields

## 🔍 Troubleshooting

### Common Issues
1. **Database Connection Failed**
   - Check MySQL service is running
   - Verify connection credentials
   - Ensure database exists

2. **Permission Errors**
   - Check file write permissions
   - Verify database user privileges

3. **Memory Issues**
   - Reduce batch sizes for large datasets
   - Use smaller customer counts for testing

### Logs
- Check console output for detailed error messages
- Review generated log files for debugging information

## 📋 Data Schema

### Customers Table
```sql
CREATE TABLE customers (
    customer_id VARCHAR(50) PRIMARY KEY,
    first_name VARCHAR(50),
    last_name VARCHAR(50),
    email VARCHAR(100),
    phone VARCHAR(20),
    date_of_birth DATE,
    ssn VARCHAR(11),
    address TEXT,
    city VARCHAR(50),
    state VARCHAR(2),
    zip_code VARCHAR(10),
    employment_type VARCHAR(50),
    annual_income DECIMAL(12,2),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

### Financial Records Table
```sql
CREATE TABLE financial_records (
    record_id VARCHAR(50) PRIMARY KEY,
    customer_id VARCHAR(50),
    record_type VARCHAR(50),
    amount DECIMAL(12,2),
    description TEXT,
    record_date DATE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (customer_id) REFERENCES customers(customer_id)
);
```

### Loan Applications Table
```sql
CREATE TABLE loan_applications (
    application_id VARCHAR(50) PRIMARY KEY,
    customer_id VARCHAR(50),
    loan_type VARCHAR(50),
    requested_amount DECIMAL(12,2),
    term_months INTEGER,
    purpose VARCHAR(100),
    status VARCHAR(20),
    application_date DATE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (customer_id) REFERENCES customers(customer_id)
);
```

### Market Data Table
```sql
CREATE TABLE market_data (
    data_id VARCHAR(50) PRIMARY KEY,
    data_type VARCHAR(50),
    value DECIMAL(10,4),
    date_recorded DATE,
    source VARCHAR(100),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

### Credit History Table
```sql
CREATE TABLE credit_history (
    history_id VARCHAR(50) PRIMARY KEY,
    customer_id VARCHAR(50),
    credit_score INTEGER,
    payment_history VARCHAR(50),
    credit_utilization DECIMAL(5,2),
    record_date DATE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (customer_id) REFERENCES customers(customer_id)
);
```

## 🔄 Data Refresh

To regenerate all data:
```bash
# Drop and recreate tables
python data_generator.py --reset

# Generate new data
python data_generator.py
```

## 📊 Data Quality

The generated data includes:
- **Realistic Distributions** - Income, age, credit scores follow real-world patterns
- **Correlated Data** - Related fields maintain logical relationships
- **Temporal Consistency** - Dates and timestamps are chronologically valid
- **Referential Integrity** - Foreign key relationships are maintained

## 🎯 Use Cases

- **Development & Testing** - Consistent test data for development
- **Demo Environments** - Realistic data for presentations
- **Performance Testing** - Large datasets for load testing
- **Training Data** - Synthetic data for AI model training
- **Research** - Anonymized data for analysis

## 📞 Support

For issues with data generation:
1. Check the troubleshooting section above
2. Review `DATA_GENERATOR_README.md` for detailed documentation
3. Check console logs for specific error messages
4. Verify database connectivity and permissions

---

**Note**: This module generates synthetic data for development and testing purposes only. Do not use this data in production environments. 