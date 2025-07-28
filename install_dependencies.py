#!/usr/bin/env python3
"""
Windows-friendly dependency installer for VoiceAccess
Handles problematic packages gracefully
"""

import subprocess
import sys
import os

def install_package(package):
    """Install a package with error handling"""
    try:
        print(f"Installing {package}...")
        subprocess.check_call([sys.executable, "-m", "pip", "install", package])
        print(f"✅ Successfully installed {package}")
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ Failed to install {package}: {e}")
        return False

def main():
    print("🎤 VoiceAccess Dependency Installer")
    print("=" * 50)
    
    # Essential packages (must install)
    essential_packages = [
        "streamlit==1.29.0",
        "assemblyai==0.21.0",
        "sounddevice==0.4.6",
        "numpy==1.24.3",
        "python-dotenv==1.0.0",
        "pandas==2.1.4",
        "plotly==5.17.0",
        "psutil==5.9.6",
        "requests==2.31.0",
        "click==8.1.7",
        "colorama==0.4.6"
    ]
    
    # Optional packages (nice to have)
    optional_packages = [
        "scipy==1.11.4",
        "librosa==0.10.1", 
        "soundfile==0.12.1",
        "streamlit-webrtc==0.47.1",
        "websockets==12.0",
        "aiohttp==3.9.1",
        "pydantic==2.5.2",
        "altair==5.2.0",
        "loguru==0.7.2",
        "validators==0.22.0",
        "threading-timer==0.1.0"
    ]
    
    # Upgrade pip first
    print("Upgrading pip...")
    try:
        subprocess.check_call([sys.executable, "-m", "pip", "install", "--upgrade", "pip"])
        print("✅ pip upgraded successfully")
    except:
        print("⚠️ Could not upgrade pip, continuing anyway...")
    
    print("\n📦 Installing essential packages...")
    essential_failed = []
    for package in essential_packages:
        if not install_package(package):
            essential_failed.append(package)
    
    print("\n📦 Installing optional packages...")
    optional_failed = []
    for package in optional_packages:
        if not install_package(package):
            optional_failed.append(package)
    
    print("\n" + "=" * 50)
    print("📋 Installation Summary:")
    
    if not essential_failed:
        print("✅ All essential packages installed successfully!")
    else:
        print("❌ Some essential packages failed to install:")
        for package in essential_failed:
            print(f"   - {package}")
    
    if optional_failed:
        print("⚠️ Some optional packages failed to install:")
        for package in optional_failed:
            print(f"   - {package}")
        print("   (The app will still work without these)")
    
    print("\n🚀 Next steps:")
    print("1. Add your AssemblyAI API key to the .env file")
    print("2. Run: streamlit run app.py")
    
    if essential_failed:
        print("\n⚠️ Warning: Essential packages failed. The app may not work properly.")
        return 1
    
    return 0

if __name__ == "__main__":
    sys.exit(main())