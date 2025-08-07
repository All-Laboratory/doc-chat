#!/usr/bin/env python3
"""
Prepare requirements for Railway deployment
"""
import shutil
import os

def prepare_requirements():
    """Copy Railway requirements to main requirements.txt for deployment"""
    try:
        # Check if railway requirements file exists
        if os.path.exists('requirements.railway.txt'):
            # Copy railway requirements to main requirements
            shutil.copy2('requirements.railway.txt', 'requirements.txt')
            print("✅ Copied requirements.railway.txt to requirements.txt")
        else:
            print("❌ requirements.railway.txt not found")
            return False
        
        # Display the requirements that will be used
        with open('requirements.txt', 'r') as f:
            content = f.read()
            print("\n📋 Requirements that will be installed:")
            print(content)
        
        return True
        
    except Exception as e:
        print(f"❌ Error preparing requirements: {e}")
        return False

if __name__ == "__main__":
    success = prepare_requirements()
    if success:
        print("\n🚀 Ready for Railway deployment!")
    else:
        print("\n❌ Failed to prepare for deployment")
