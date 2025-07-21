#!/usr/bin/env python3
"""
Install dependencies for the data generator
"""

import subprocess
import sys

def install_package(package):
    """Install a package using pip"""
    try:
        subprocess.check_call([sys.executable, "-m", "pip", "install", package])
        print(f"✅ Installed {package}")
        return True
    except subprocess.CalledProcessError:
        print(f"❌ Failed to install {package}")
        return False

def main():
    """Install required packages for data generator"""
    print("📦 Installing dependencies for Credit Risk Data Generator...")
    
    required_packages = [
        "mysql-connector-python",
        "faker",
        "numpy",
        "pandas"
    ]
    
    success_count = 0
    for package in required_packages:
        if install_package(package):
            success_count += 1
    
    print(f"\n📊 Installation Summary:")
    print(f"Successfully installed: {success_count}/{len(required_packages)} packages")
    
    if success_count == len(required_packages):
        print("✅ All dependencies installed successfully!")
        print("You can now run: python data_generator.py")
    else:
        print("⚠️  Some packages failed to install. Please check your internet connection and try again.")

if __name__ == "__main__":
    main() 