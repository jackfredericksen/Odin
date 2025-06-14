#!/usr/bin/env python3
"""
Quick patch script to fix data processing errors in Odin
Run this to patch the immediate errors
"""

import os
import shutil
from datetime import datetime

def backup_file(file_path):
    """Create a backup of the original file"""
    if os.path.exists(file_path):
        backup_path = f"{file_path}.backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        shutil.copy2(file_path, backup_path)
        print(f"📁 Backed up {file_path} to {backup_path}")
        return True
    return False

def patch_enhanced_data_collector():
    """Patch the enhanced data collector"""
    file_path = "odin/core/enhanced_data_collector.py"
    
    if not os.path.exists(file_path):
        print(f"❌ File not found: {file_path}")
        return False
    
    backup_file(file_path)
    
    try:
        with open(file_path, 'r') as f:
            content = f.read()
        
        # Add safety check for get_ml_ready_features
        safety_check = '''
        # Safety check for empty data
        if df.empty:
            self.logger.warning("No data found in database for ML features")
            return pd.DataFrame()
        
        # Ensure we have minimum data
        if len(df) < 5:
            self.logger.warning("Insufficient data for ML processing")
            return df
        '''
        
        # Find and patch the get_ml_ready_features method
        if 'def get_ml_ready_features' in content:
            # Add safety checks after the SQL query
            content = content.replace(
                'df = pd.read_sql_query(query, conn, params=[start_date, end_date])',
                f'df = pd.read_sql_query(query, conn, params=[start_date, end_date]){safety_check}'
            )
            
            # Add safe dropna
            content = content.replace(
                'df = df.dropna()',
                '''# Safe dropna - only if we won't lose too much data
        original_length = len(df)
        df_clean = df.dropna()
        if len(df_clean) < max(5, original_length * 0.3):
            self.logger.warning(f"Would lose too much data in dropna: {original_length} -> {len(df_clean)}")
            df = df.fillna(method='ffill').fillna(0)
        else:
            df = df_clean'''
            )
        
        with open(file_path, 'w') as f:
            f.write(content)
        
        print(f"✅ Patched {file_path}")
        return True
        
    except Exception as e:
        print(f"❌ Failed to patch {file_path}: {e}")
        return False

def patch_regime_detector():
    """Patch the regime detector"""
    file_path = "odin/ai/regime_detection/regime_detector.py"
    
    if not os.path.exists(file_path):
        print(f"❌ File not found: {file_path}")
        return False
    
    backup_file(file_path)
    
    try:
        with open(file_path, 'r') as f:
            content = f.read()
        
        # Find and patch the volume features method
        if '_calculate_volume_features' in content:
            # Add type checking at the start of the method
            volume_fix = '''    def _calculate_volume_features(self, df: pd.DataFrame) -> Dict[str, float]:
        """Calculate volume-based features - PATCHED VERSION"""
        try:
            features = {}

            # Safety checks
            if not isinstance(df, pd.DataFrame):
                self.logger.warning("Expected DataFrame for volume features")
                return features
                
            if "volume" not in df.columns or len(df) < 5:
                return features
            
            volume_series = df["volume"]
            
            # Basic volume ratio calculation with safety
            try:
                if len(df) >= 20:
                    vol_ma = volume_series.rolling(window=20, min_periods=1).mean()
                    current_vol = volume_series.iloc[-1]
                    avg_vol = vol_ma.iloc[-1]
                    
                    if avg_vol > 0:
                        features["volume_ratio"] = current_vol / avg_vol
                        features["high_volume"] = 1 if features["volume_ratio"] > 1.5 else 0
            except Exception as e:
                self.logger.warning(f"Volume calculation failed: {e}")

            return features

        except Exception as e:
            self.logger.error(f"Error calculating volume features: {e}")
            return {}'''
            
            # Replace the entire method
            import re
            pattern = r'def _calculate_volume_features\(self, df: pd\.DataFrame\) -> Dict\[str, float\]:.*?(?=\n    def|\nclass|\n\n|\Z)'
            
            if re.search(pattern, content, re.DOTALL):
                content = re.sub(pattern, volume_fix.replace('    def _calculate_volume_features', 'def _calculate_volume_features'), content, flags=re.DOTALL)
            else:
                print("⚠️  Could not find volume features method to patch")
        
        with open(file_path, 'w') as f:
            f.write(content)
        
        print(f"✅ Patched {file_path}")
        return True
        
    except Exception as e:
        print(f"❌ Failed to patch {file_path}: {e}")
        return False

def patch_cli_market_data():
    """Patch the CLI market data display"""
    file_path = "odin_cli.py"
    
    if not os.path.exists(file_path):
        print(f"❌ File not found: {file_path}")
        return False
    
    backup_file(file_path)
    
    try:
        with open(file_path, 'r') as f:
            content = f.read()
        
        # Add better error handling around AI data fetching
        if 'ml_data = self.collector.get_ml_ready_features' in content:
            content = content.replace(
                'ml_data = self.collector.get_ml_ready_features(lookback_days=1)',
                '''# Safer AI data fetching
                try:
                    ml_data = self.collector.get_ml_ready_features(lookback_days=7)
                except Exception as fetch_error:
                    console.print(f"[dim red]AI data fetch failed: {fetch_error}[/dim red]")
                    ml_data = pd.DataFrame()'''
            )
        
        # Add better error handling for regime detection
        if 'regime_result = asyncio.run(self.regime_detector.detect_regime(dummy_data))' in content:
            content = content.replace(
                'regime_result = asyncio.run(self.regime_detector.detect_regime(dummy_data))',
                '''try:
                        regime_result = asyncio.run(self.regime_detector.detect_regime(dummy_data))
                    except Exception as regime_error:
                        console.print(f"[dim red]Regime detection failed: {regime_error}[/dim red]")
                        regime_result = {"current_regime": "unknown", "confidence": 0}'''
            )
        
        with open(file_path, 'w') as f:
            f.write(content)
        
        print(f"✅ Patched {file_path}")
        return True
        
    except Exception as e:
        print(f"❌ Failed to patch {file_path}: {e}")
        return False

def main():
    """Apply all patches"""
    print("🔧 Odin Data Processing Error Patches")
    print("=" * 40)
    
    patches = [
        ("Enhanced Data Collector", patch_enhanced_data_collector),
        ("Regime Detector", patch_regime_detector),
        ("CLI Market Data", patch_cli_market_data),
    ]
    
    success_count = 0
    for patch_name, patch_func in patches:
        print(f"\n📝 Applying {patch_name} patch...")
        if patch_func():
            success_count += 1
    
    print("\n" + "=" * 40)
    print(f"✅ Applied {success_count}/{len(patches)} patches successfully")
    
    if success_count == len(patches):
        print("\n🎉 All patches applied! Try running the CLI again:")
        print("python odin_cli.py")
    else:
        print("\n⚠️  Some patches failed. Check the errors above.")
        print("You may need to apply the fixes manually.")

if __name__ == "__main__":
    main()