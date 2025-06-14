#!/usr/bin/env python3
"""
Quick diagnostic script for Odin AI components
Run this to identify what's broken
"""

import sys
import os

def check_dependencies():
    """Check if required dependencies are installed"""
    print("🔍 Checking dependencies...")
    
    required_deps = [
        "yfinance", "scikit-learn", "sklearn", "joblib", 
        "pandas", "numpy", "requests"
    ]
    
    missing = []
    for dep in required_deps:
        try:
            __import__(dep)
            print(f"✅ {dep}")
        except ImportError:
            print(f"❌ {dep} - MISSING")
            missing.append(dep)
    
    return missing

def check_file_structure():
    """Check if required files exist"""
    print("\n📁 Checking file structure...")
    
    required_files = [
        "odin_cli.py",
        "odin/core/enhanced_data_collector.py",
        "odin/strategies/ai_adaptive.py", 
        "odin/ai/regime_detection/regime_detector.py",
        "odin/ai/strategy_selection/adaptive_manager.py"
    ]
    
    missing = []
    for file_path in required_files:
        if os.path.exists(file_path):
            print(f"✅ {file_path}")
        else:
            print(f"❌ {file_path} - MISSING")
            missing.append(file_path)
    
    return missing

def check_imports():
    """Test imports of AI components"""
    print("\n🔧 Testing imports...")
    
    # Add project root to path
    sys.path.insert(0, os.getcwd())
    
    imports_to_test = [
        ("yfinance", "import yfinance as yf"),
        ("Enhanced Data Collector", "from odin.core.enhanced_data_collector import EnhancedBitcoinDataCollector"),
        ("AI Strategy", "from odin.strategies.ai_adaptive import AIAdaptiveStrategy"),
        ("Regime Detector", "from odin.ai.regime_detection.regime_detector import RegimeDetector"),
        ("Adaptive Manager", "from odin.ai.strategy_selection.adaptive_manager import AdaptiveStrategyManager")
    ]
    
    failed = []
    for name, import_statement in imports_to_test:
        try:
            exec(import_statement)
            print(f"✅ {name}")
        except Exception as e:
            print(f"❌ {name} - ERROR: {e}")
            failed.append((name, str(e)))
    
    return failed

def check_data_directories():
    """Check if data directories exist"""
    print("\n📂 Checking data directories...")
    
    required_dirs = [
        "data",
        "data/models",
        "data/strategy_configs",
        "logs"
    ]
    
    missing = []
    for dir_path in required_dirs:
        if os.path.exists(dir_path):
            print(f"✅ {dir_path}")
        else:
            print(f"❌ {dir_path} - MISSING")
            missing.append(dir_path)
    
    return missing

def main():
    print("🤖 Odin AI Diagnostic Tool")
    print("=" * 50)
    
    # Run all checks
    missing_deps = check_dependencies()
    missing_files = check_file_structure()
    failed_imports = check_imports()
    missing_dirs = check_data_directories()
    
    # Summary
    print("\n📊 DIAGNOSTIC SUMMARY")
    print("=" * 50)
    
    if not any([missing_deps, missing_files, failed_imports, missing_dirs]):
        print("🎉 ALL CHECKS PASSED! Your AI setup should work.")
    else:
        print("⚠️  Issues found:")
        
        if missing_deps:
            print(f"   📦 Missing dependencies: {', '.join(missing_deps)}")
            print(f"      Fix: pip install {' '.join(missing_deps)}")
        
        if missing_files:
            print(f"   📄 Missing files: {len(missing_files)} files")
            for file in missing_files:
                print(f"      - {file}")
        
        if failed_imports:
            print(f"   🔧 Import failures: {len(failed_imports)} imports")
            for name, error in failed_imports:
                print(f"      - {name}: {error}")
        
        if missing_dirs:
            print(f"   📂 Missing directories: {', '.join(missing_dirs)}")
            print(f"      Fix: Run setup_ai_environment.py")
    
    print("\n💡 RECOMMENDED ACTIONS:")
    if missing_deps:
        print("1. Install missing dependencies:")
        print(f"   pip install {' '.join(missing_deps)}")
    
    if missing_dirs:
        print("2. Create missing directories:")
        print("   python setup_ai_environment.py")
    
    if failed_imports:
        print("3. Fix import issues in AI modules")
        print("   Apply the import fixes from the troubleshooting guide")
    
    if missing_files:
        print("4. Ensure all AI module files exist")
        print("   Check your repository structure")

if __name__ == "__main__":
    main()