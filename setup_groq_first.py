#!/usr/bin/env python3
"""
Quick setup script to switch your application to use the Groq-first fallback system.
This will backup your current setup and update the imports.
"""

import os
import shutil
from datetime import datetime

def backup_current_setup():
    """Backup current LLM utils files"""
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_dir = f"backup_{timestamp}"
    
    print(f"📁 Creating backup directory: {backup_dir}")
    os.makedirs(backup_dir, exist_ok=True)
    
    # Files to backup
    files_to_backup = [
        "app/llm_utils.py",
        "app/llm_utils_round_robin.py", 
        "app/main.py"
    ]
    
    for file_path in files_to_backup:
        if os.path.exists(file_path):
            backup_path = os.path.join(backup_dir, os.path.basename(file_path))
            shutil.copy2(file_path, backup_path)
            print(f"✅ Backed up: {file_path} → {backup_path}")
    
    return backup_dir

def update_main_py():
    """Update main.py to use the new Groq-first system"""
    main_py_path = "app/main.py"
    
    if not os.path.exists(main_py_path):
        print(f"❌ {main_py_path} not found")
        return False
    
    print(f"📝 Updating {main_py_path}...")
    
    # Read current content
    with open(main_py_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Replace the import lines
    old_imports = [
        "from app.llm_utils_round_robin import DocumentReasoningLLM",
        "from llm_utils_round_robin import DocumentReasoningLLM"
    ]
    
    new_imports = [
        "from app.llm_utils_groq_together import DocumentReasoningLLM",
        "from llm_utils_groq_together import DocumentReasoningLLM"
    ]
    
    updated = False
    for old_import, new_import in zip(old_imports, new_imports):
        if old_import in content:
            content = content.replace(old_import, new_import)
            updated = True
            print(f"✅ Updated import: {old_import} → {new_import}")
    
    if updated:
        # Write updated content
        with open(main_py_path, 'w', encoding='utf-8') as f:
            f.write(content)
        print(f"✅ {main_py_path} updated successfully")
        return True
    else:
        print(f"⚠️ No import changes needed in {main_py_path}")
        return False

def check_api_keys():
    """Check if required API keys are available"""
    print("\n🔑 Checking API keys...")
    
    groq_key = os.getenv("GROQ_API_KEY")
    together_key = os.getenv("TOGETHER_API_KEY")
    
    status = []
    
    if groq_key and groq_key not in ["your_actual_groq_api_key_here", "your_groq_api_key"]:
        print("✅ GROQ_API_KEY found")
        status.append("groq")
    else:
        print("❌ GROQ_API_KEY not found or invalid")
    
    if together_key and together_key not in ["your_together_api_key", "your_actual_api_key"]:
        print("✅ TOGETHER_API_KEY found")
        status.append("together")
    else:
        print("❌ TOGETHER_API_KEY not found or invalid")
    
    if not status:
        print("\n⚠️ Warning: No valid API keys found!")
        print("Please set your API keys in the .env file:")
        print("GROQ_API_KEY=your_actual_groq_key")
        print("TOGETHER_API_KEY=your_actual_together_key")
        return False
    else:
        print(f"\n✅ Available providers: {', '.join(status).upper()}")
        return True

def test_new_setup():
    """Run a quick test of the new system"""
    print("\n🧪 Testing new Groq-first system...")
    
    try:
        # Import the test function
        import subprocess
        import sys
        
        # Run the test script
        result = subprocess.run([sys.executable, "test_groq_together.py"], 
                              capture_output=True, text=True, timeout=60)
        
        if result.returncode == 0:
            print("✅ Test completed successfully!")
            print("📊 Check the test output above for detailed results")
            return True
        else:
            print("❌ Test failed!")
            print("Error:", result.stderr)
            return False
    
    except subprocess.TimeoutExpired:
        print("⏰ Test timed out - this might be normal if API keys are not set")
        return False
    except Exception as e:
        print(f"❌ Test error: {e}")
        return False

def show_integration_summary():
    """Show summary of changes and next steps"""
    print("\n" + "="*60)
    print("🎉 GROQ-FIRST FALLBACK SYSTEM SETUP COMPLETE!")
    print("="*60)
    
    print("\n📋 What Changed:")
    print("✅ Backed up original files")
    print("✅ Updated app/main.py to use Groq-first system")
    print("✅ New system prioritizes Groq → Together AI fallback")
    
    print("\n🚀 System Behavior:")
    print("1. 🥇 Groq processes requests first (fast & efficient)")
    print("2. 🔄 If Groq hits rate limits → Together AI takes over")
    print("3. 🔁 Cycle repeats: Groq → Together → Groq → Together")
    print("4. ⏰ Rate-limited providers get 60-second cooldown")
    print("5. 🛡️ Graceful fallback with document content if both fail")
    
    print("\n💡 Next Steps:")
    print("1. Test your application:")
    print("   python test_groq_together.py")
    print("2. Start your server:")
    print("   python -m uvicorn app.main:app --reload")
    print("3. Monitor logs for fallback behavior")
    
    print("\n🔧 Environment Variables Needed:")
    print("GROQ_API_KEY=your_actual_groq_key")
    print("TOGETHER_API_KEY=your_actual_together_key")
    print("GROQ_MODEL=llama3-8b-8192")
    print("TOGETHER_MODEL=moonshotai/kimi-k2-instruct")

def main():
    """Main setup function"""
    print("🚀 GROQ-FIRST FALLBACK SYSTEM SETUP")
    print("="*50)
    print("This will switch your app to use Groq first, then Together AI fallback")
    
    # Ask for confirmation
    response = input("\nProceed with setup? (y/N): ").strip().lower()
    if response not in ['y', 'yes']:
        print("Setup cancelled.")
        return
    
    print("\n🔄 Starting setup process...\n")
    
    # Step 1: Backup
    backup_dir = backup_current_setup()
    print(f"📦 Backup created: {backup_dir}")
    
    # Step 2: Update main.py
    print("\n" + "-"*50)
    if update_main_py():
        print("✅ Application updated successfully")
    
    # Step 3: Check API keys
    print("\n" + "-"*50)
    has_keys = check_api_keys()
    
    # Step 4: Test if keys are available
    if has_keys:
        print("\n" + "-"*50)
        test_new_setup()
    
    # Step 5: Show summary
    show_integration_summary()
    
    if not has_keys:
        print("\n⚠️ IMPORTANT: Set your API keys in .env file before testing!")

if __name__ == "__main__":
    main()
