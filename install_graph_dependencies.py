#!/usr/bin/env python3
"""
Script to install Microsoft Graph dependencies
Run this if you see "Microsoft Graph SDK not available" errors
"""
import subprocess
import sys
import os

def install_graph_dependencies():
    """Install Microsoft Graph SDK and dependencies"""
    
    print("🔧 Installing Microsoft Graph Dependencies...")
    
    dependencies = [
        "msgraph-sdk==1.5.4",
        "azure-identity==1.19.0", 
        "msgraph-core==1.1.5",
        "azure-core==1.29.5"
    ]
    
    for dep in dependencies:
        print(f"Installing {dep}...")
        try:
            subprocess.check_call([sys.executable, "-m", "pip", "install", dep])
            print(f"✅ {dep} installed successfully")
        except subprocess.CalledProcessError as e:
            print(f"❌ Failed to install {dep}: {e}")
            return False
    
    print("\n🧪 Testing import...")
    try:
        from msgraph import GraphServiceClient
        from azure.identity import ClientSecretCredential
        print("✅ Microsoft Graph SDK import successful!")
        return True
    except ImportError as e:
        print(f"❌ Import test failed: {e}")
        return False

if __name__ == "__main__":
    success = install_graph_dependencies()
    if success:
        print("\n🎉 All dependencies installed successfully!")
        print("You can now restart your agent to use Microsoft Graph API.")
    else:
        print("\n❌ Some dependencies failed to install.")
        print("Please check your Python environment and try again.")