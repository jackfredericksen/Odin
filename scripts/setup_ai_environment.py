#!/usr/bin/env python3
"""
Setup script to initialize AI environment for Odin Trading Bot
Run this before using AI features
"""

import os
import sqlite3
from pathlib import Path

def setup_ai_environment():
    """Setup necessary directories and files for AI functionality"""
    
    print("🤖 Setting up Odin AI Environment...")
    
    # 1. Create necessary directories
    directories = [
        "data",
        "data/models", 
        "data/strategy_configs",
        "data/backtest_results",
        "logs"
    ]
    
    for directory in directories:
        Path(directory).mkdir(parents=True, exist_ok=True)
        print(f"✅ Created directory: {directory}")
    
    # 2. Create __init__.py files for AI packages
    init_files = [
        "odin/ai/__init__.py",
        "odin/ai/regime_detection/__init__.py", 
        "odin/ai/strategy_selection/__init__.py"
    ]
    
    for init_file in init_files:
        Path(init_file).touch(exist_ok=True)
        print(f"✅ Created: {init_file}")
    
    # 3. Initialize enhanced data collector database
    db_path = "data/bitcoin_enhanced.db"
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Create enhanced table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS bitcoin_enhanced (
                timestamp DATETIME PRIMARY KEY,
                open REAL,
                high REAL,
                low REAL,
                close REAL,
                volume REAL,
                market_cap REAL,
                total_volume_24h REAL,
                rsi_14 REAL,
                ma_20 REAL,
                ma_50 REAL,
                bollinger_upper REAL,
                bollinger_lower REAL,
                macd REAL,
                macd_signal REAL,
                price_change_24h REAL,
                price_change_percentage_24h REAL,
                market_cap_rank INTEGER,
                volume_ma_20 REAL,
                volume_ratio REAL,
                data_source TEXT,
                quality_score REAL,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_timestamp ON bitcoin_enhanced(timestamp)')
        conn.commit()
        conn.close()
        print(f"✅ Initialized database: {db_path}")
        
    except Exception as e:
        print(f"❌ Database setup failed: {e}")
    
    # 4. Create basic config files
    config_files = {
        "data/strategy_configs/regime_mappings.json": {
            "bull_trending": {
                "risk_multiplier": 1.2,
                "max_exposure": 0.9,
                "preferred_strategies": ["MovingAverage", "MACD"]
            },
            "bear_trending": {
                "risk_multiplier": 0.6,
                "max_exposure": 0.5,  
                "preferred_strategies": ["RSI", "MovingAverage"]
            },
            "sideways": {
                "risk_multiplier": 0.8,
                "max_exposure": 0.7,
                "preferred_strategies": ["RSI", "BollingerBands"]
            },
            "high_volatility": {
                "risk_multiplier": 0.5,
                "max_exposure": 0.4,
                "preferred_strategies": ["BollingerBands"]
            },
            "crisis": {
                "risk_multiplier": 0.0,
                "max_exposure": 0.1,
                "preferred_strategies": []
            }
        }
    }
    
    import json
    for file_path, content in config_files.items():
        try:
            with open(file_path, 'w') as f:
                json.dump(content, f, indent=2)
            print(f"✅ Created config: {file_path}")
        except Exception as e:
            print(f"❌ Config creation failed for {file_path}: {e}")
    
    # 5. Test imports
    print("\n🧪 Testing AI imports...")
    
    try:
        import yfinance as yf
        print("✅ yfinance available")
    except ImportError:
        print("❌ yfinance missing - install with: pip install yfinance")
    
    try:
        import sklearn
        print("✅ scikit-learn available") 
    except ImportError:
        print("❌ scikit-learn missing - install with: pip install scikit-learn")
    
    try:
        import joblib
        print("✅ joblib available")
    except ImportError:
        print("❌ joblib missing - install with: pip install joblib")
    
    try:
        from odin.core.enhanced_data_collector import EnhancedBitcoinDataCollector
        print("✅ Enhanced data collector importable")
    except ImportError as e:
        print(f"❌ Enhanced data collector import failed: {e}")
    
    print("\n🎯 Setup complete! You can now run the CLI with AI features.")
    print("💡 Run: python odin_cli.py")

if __name__ == "__main__":
    setup_ai_environment()