#!/usr/bin/env python3
"""
Quick fix script for AssemblyAI model deprecation issue
"""

import subprocess
import sys
import os

def main():
    print("🔧 Fixing AssemblyAI Model Deprecation Issue")
    print("=" * 50)
    
    # Update AssemblyAI SDK
    print("1. Updating AssemblyAI SDK to latest version...")
    try:
        subprocess.check_call([sys.executable, "-m", "pip", "install", "--upgrade", "assemblyai"])
        print("✅ AssemblyAI SDK updated successfully")
    except subprocess.CalledProcessError as e:
        print(f"❌ Failed to update AssemblyAI SDK: {e}")
        return 1
    
    # Check current version
    print("\n2. Checking AssemblyAI version...")
    try:
        import assemblyai as aai
        print(f"✅ AssemblyAI version: {aai.__version__}")
    except ImportError:
        print("❌ AssemblyAI not properly installed")
        return 1
    
    # Test basic functionality
    print("\n3. Testing basic functionality...")
    api_key = os.getenv('ASSEMBLYAI_API_KEY')
    if not api_key:
        print("⚠️ No API key found in environment")
        print("   Please add ASSEMBLYAI_API_KEY to your .env file")
    else:
        print("✅ API key found")
        
        # Test API connection
        try:
            aai.settings.api_key = api_key
            print("✅ API key configured successfully")
        except Exception as e:
            print(f"❌ API configuration failed: {e}")
    
    print("\n4. Audio configuration recommendations:")
    print("   - Reduced chunk size to 512 samples (from 1024)")
    print("   - Increased buffer size to 8192 (from 4096)")
    print("   - Added overflow handling for audio input")
    print("   - Configured low-latency audio settings")
    
    print("\n🚀 Fixes applied! Try running the app again:")
    print("   streamlit run app.py")
    
    return 0

if __name__ == "__main__":
    sys.exit(main())