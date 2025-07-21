#!/usr/bin/env python3
"""
Environment Setup Script for CreditRisk AI Suite
Interactive script to generate .env file with user inputs
"""

import os
import sys
from pathlib import Path

def create_env_file():
    """Create .env file from template"""
    
    # Check if .env already exists
    if os.path.exists('.env'):
        print("⚠️  .env file already exists!")
        response = input("Do you want to overwrite it? (y/N): ")
        if response.lower() != 'y':
            print("Setup cancelled.")
            return False
    
    # Check if env_example.txt exists
    if not os.path.exists('env_example.txt'):
        print("❌ env_example.txt not found!")
        print("Please make sure the template file exists.")
        return False
    
    # Read the template
    with open('env_example.txt', 'r') as f:
        template_content = f.read()
    
    print("🔧 Setting up environment configuration...")
    print("Please provide the following information:")
    print()
    
    # Get user input for required settings
    config = {}
    
    # Database settings
    print("📊 DATABASE CONFIGURATION")
    config['DB_HOST'] = input("Database host (default: localhost): ") or "localhost"
    config['DB_PORT'] = input("Database port (default: 3306): ") or "3306"
    config['DB_NAME'] = input("Database name (default: credit_risk_analysis): ") or "credit_risk_analysis"
    config['DB_USER'] = input("Database username: ")
    config['DB_PASSWORD'] = input("Database password: ")
    
    print()
    print("🤖 AI CONFIGURATION")
    config['OPENAI_API_KEY'] = input("OpenAI API Key: ")
    
    print()
    print("🔐 SECURITY")
    import secrets
    config['SECRET_KEY'] = input(f"Secret key (default: {secrets.token_urlsafe(32)}): ") or secrets.token_urlsafe(32)
    
    print()
    print("⚙️  OPTIONAL SETTINGS")
    config['APP_ENVIRONMENT'] = input("Environment (development/staging/production, default: development): ") or "development"
    config['LOG_LEVEL'] = input("Log level (DEBUG/INFO/WARNING/ERROR, default: INFO): ") or "INFO"
    
    # Replace placeholders in template
    content = template_content
    
    # Replace database settings
    content = content.replace('your_mysql_username', config['DB_USER'])
    content = content.replace('your_mysql_password', config['DB_PASSWORD'])
    content = content.replace('your_openai_api_key_here', config['OPENAI_API_KEY'])
    content = content.replace('your_secret_key_here', config['SECRET_KEY'])
    
    # Replace other settings
    content = content.replace('APP_ENVIRONMENT=development', f'APP_ENVIRONMENT={config["APP_ENVIRONMENT"]}')
    content = content.replace('LOG_LEVEL=INFO', f'LOG_LEVEL={config["LOG_LEVEL"]}')
    
    # Write .env file
    with open('.env', 'w') as f:
        f.write(content)
    
    print()
    print("✅ Environment configuration created successfully!")
    print("📁 File: .env")
    print()
    print("🔒 Security Notes:")
    print("- Keep your .env file secure and never commit it to version control")
    print("- Your API keys and passwords are now stored in the .env file")
    print("- Make sure .env is listed in your .gitignore file")
    
    return True

def check_requirements():
    """Check if required packages are installed"""
    print("📦 Checking required packages...")
    
    required_packages = [
        'streamlit',
        'crewai',
        'openai',
        'pandas',
        'plotly',
        'mysql-connector-python'
    ]
    
    missing_packages = []
    
    for package in required_packages:
        try:
            __import__(package.replace('-', '_'))
            print(f"✅ {package}")
        except ImportError:
            print(f"❌ {package}")
            missing_packages.append(package)
    
    if missing_packages:
        print()
        print("⚠️  Missing packages detected!")
        print("Please install the missing packages:")
        print(f"pip install {' '.join(missing_packages)}")
        return False
    else:
        print()
        print("✅ All required packages are installed!")
        return True

def create_directories():
    """Create necessary directories"""
    print("📁 Creating necessary directories...")
    
    directories = [
        'logs',
        'templates',
        'exports',
        'data'
    ]
    
    for directory in directories:
        Path(directory).mkdir(exist_ok=True)
        print(f"✅ Created: {directory}/")

def main():
    """Main setup function"""
    print("🏦 CreditRisk AI Suite - Environment Setup")
    print("=" * 50)
    print()
    
    # Check requirements
    if not check_requirements():
        print()
        print("❌ Setup cannot continue. Please install missing packages.")
        return
    
    print()
    
    # Create directories
    create_directories()
    
    print()
    
    # Create .env file
    if create_env_file():
        print()
        print("🎉 Setup completed successfully!")
        print()
        print("🚀 Next steps:")
        print("1. Review your .env file and adjust settings if needed")
        print("2. Start the application: streamlit run app.py")
        print("3. Open your browser to: http://localhost:8501")
        print()
        print("📚 For more information, see the documentation files:")
        print("- README.md")
        print("- APPLICATION_DOCUMENTATION.md")
    else:
        print("❌ Setup failed. Please check the errors above.")

if __name__ == "__main__":
    main() 