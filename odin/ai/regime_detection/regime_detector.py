# odin/ai/regime_detection/regime_detector.py
"""
Market Regime Detection System for Odin Trading Bot
Uses Hidden Markov Models and clustering to identify Bitcoin market states
"""

import numpy as np
import pandas as pd
from sklearn.mixture import GaussianMixture
from sklearn.cluster import KMeans
from sklearn.preprocessing import StandardScaler
from sklearn.metrics import silhouette_score
from hmmlearn import hmm
import warnings
from typing import Dict, List, Tuple, Optional
from datetime import datetime, timedelta
import logging
import joblib
import os

warnings.filterwarnings('ignore')

class MarketRegimeDetector:
    """
    Advanced market regime detection using multiple ML techniques
    """
    
    def __init__(self, model_path: str = "data/models/regime_models/"):
        self.model_path = model_path
        self.logger = self._setup_logging()
        
        # Regime definitions
        self.regime_map = {
            0: "bull_trending",      # Strong upward momentum
            1: "bear_trending",      # Strong downward momentum  
            2: "sideways",          # Low volatility, range-bound
            3: "high_volatility",   # High volatility, uncertain direction
            4: "crisis"             # Extreme volatility, potential crash
        }
        
        # Model components
        self.hmm_model = None
        self.gmm_model = None
        self.scaler = StandardScaler()
        self.feature_names = []
        
        # Current state
        self.current_regime = None
        self.regime_confidence = 0.0
        self.regime_history = []
        
        # Ensure model directory exists
        os.makedirs(model_path, exist_ok=True)
        
    def _setup_logging(self):
        logging.basicConfig(level=logging.INFO)
        return logging.getLogger(__name__)
    
    def prepare_features(self, data: pd.DataFrame) -> pd.DataFrame:
        """
        Prepare feature set for regime detection
        
        Args:
            data: DataFrame with OHLCV and technical indicators
            
        Returns:
            DataFrame with regime detection features
        """
        try:
            df = data.copy()
            
            # Price-based features
            df['returns_1d'] = df['close'].pct_change(1)
            df['returns_7d'] = df['close'].pct_change(7) 
            df['returns_30d'] = df['close'].pct_change(30)
            
            # Volatility features
            df['volatility_5d'] = df['returns_1d'].rolling(5).std()
            df['volatility_20d'] = df['returns_1d'].rolling(20).std()
            df['volatility_ratio'] = df['volatility_5d'] / df['volatility_20d']
            
            # Momentum features
            df['momentum_5d'] = df['close'] / df['close'].shift(5) - 1
            df['momentum_20d'] = df['close'] / df['close'].shift(20) - 1
            
            # Volume features
            if 'volume' in df.columns:
                df['volume_ma'] = df['volume'].rolling(20).mean()
                df['volume_ratio'] = df['volume'] / df['volume_ma']
                df['volume_volatility'] = df['volume'].rolling(10).std()
            
            # Technical indicator ratios
            if 'rsi_14' in df.columns:
                df['rsi_normalized'] = (df['rsi_14'] - 50) / 50
            
            if 'ma_20' in df.columns and 'ma_50' in df.columns:
                df['ma_ratio'] = df['ma_20'] / df['ma_50'] - 1
                df['price_ma_ratio'] = df['close'] / df['ma_20'] - 1
            
            # Bollinger Band features
            if 'bollinger_upper' in df.columns and 'bollinger_lower' in df.columns:
                bb_width = df['bollinger_upper'] - df['bollinger_lower']
                df['bb_position'] = (df['close'] - df['bollinger_lower']) / bb_width
                df['bb_width'] = bb_width / df['close']
            
            # MACD features
            if 'macd' in df.columns and 'macd_signal' in df.columns:
                df['macd_histogram'] = df['macd'] - df['macd_signal']
                df['macd_normalized'] = df['macd'] / df['close']
            
            # Price level features
            df['price_percentile_20d'] = df['close'].rolling(20).rank(pct=True)
            df['price_percentile_60d'] = df['close'].rolling(60).rank(pct=True)
            
            # Support/Resistance features
            df['distance_to_high_20d'] = df['close'] / df['high'].rolling(20).max() - 1
            df['distance_to_low_20d'] = df['close'] / df['low'].rolling(20).min() - 1
            
            # Select final feature set for regime detection
            regime_features = [
                'returns_1d', 'returns_7d', 'returns_30d',
                'volatility_5d', 'volatility_20d', 'volatility_ratio',
                'momentum_5d', 'momentum_20d',
                'volume_ratio', 'volume_volatility',
                'rsi_normalized', 'ma_ratio', 'price_ma_ratio',
                'bb_position', 'bb_width',
                'macd_histogram', 'macd_normalized',
                'price_percentile_20d', 'price_percentile_60d',
                'distance_to_high_20d', 'distance_to_low_20d'
            ]
            
            # Keep only available features
            available_features = [f for f in regime_features if f in df.columns]
            self.feature_names = available_features
            
            feature_df = df[available_features].copy()
            
            # Remove infinite values and fill NaN
            feature_df = feature_df.replace([np.inf, -np.inf], np.nan)
            feature_df = feature_df.fillna(method='ffill').fillna(0)
            
            return feature_df
            
        except Exception as e:
            self.logger.error(f"Feature preparation failed: {e}")
            return pd.DataFrame()
    
    def train_models(self, feature_data: pd.DataFrame, n_regimes: int = 5) -> bool:
        """
        Train regime detection models
        
        Args:
            feature_data: Prepared feature DataFrame
            n_regimes: Number of regimes to detect
            
        Returns:
            bool: Success status
        """
        try:
            self.logger.info(f"Training regime detection models with {len(feature_data)} samples")
            
            # Scale features
            scaled_features = self.scaler.fit_transform(feature_data)
            
            # 1. Train Gaussian Mixture Model for initial clustering
            self.logger.info("Training Gaussian Mixture Model...")
            self.gmm_model = GaussianMixture(
                n_components=n_regimes,
                covariance_type='full',
                max_iter=200,
                random_state=42
            )
            
            gmm_labels = self.gmm_model.fit_predict(scaled_features)
            
            # Evaluate clustering quality
            silhouette_avg = silhouette_score(scaled_features, gmm_labels)
            self.logger.info(f"GMM Silhouette Score: {silhouette_avg:.3f}")
            
            # 2. Train Hidden Markov Model for temporal dependencies
            self.logger.info("Training Hidden Markov Model...")
            
            # Prepare sequential data for HMM
            X_hmm = scaled_features.reshape(-1, 1, scaled_features.shape[1])
            
            self.hmm_model = hmm.GaussianHMM(
                n_components=n_regimes,
                covariance_type="full",
                n_iter=100,
                random_state=42
            )
            
            self.hmm_model.fit(scaled_features)
            hmm_labels = self.hmm_model.predict(scaled_features)
            
            # 3. Combine models for robust regime detection
            combined_labels = self._combine_predictions(gmm_labels, hmm_labels)
            
            # 4. Map clusters to meaningful regime names
            regime_mapping = self._map_clusters_to_regimes(
                feature_data, combined_labels, scaled_features
            )
            
            self.regime_mapping = regime_mapping
            
            # Save models
            self._save_models()
            
            self.logger.info("Regime detection models trained successfully")
            return True
            
        except Exception as e:
            self.logger.error(f"Model training failed: {e}")
            return False
    
    def _combine_predictions(self, gmm_labels: np.ndarray, hmm_labels: np.ndarray) -> np.ndarray:
        """Combine GMM and HMM predictions for robust regime detection"""
        
        # Weight HMM more heavily due to temporal awareness
        combined = []
        
        for i in range(len(gmm_labels)):
            # Use HMM as primary, GMM as secondary
            if i > 10:  # After sufficient history
                # Check recent stability in HMM predictions
                recent_hmm = hmm_labels[max(0, i-5):i+1]
                if len(set(recent_hmm)) == 1:  # Stable regime
                    combined.append(hmm_labels[i])
                else:  # Transitional period, blend
                    combined.append(gmm_labels[i])
            else:
                combined.append(gmm_labels[i])
        
        return np.array(combined)
    
    def _map_clusters_to_regimes(self, feature_data: pd.DataFrame, 
                                labels: np.ndarray, scaled_features: np.ndarray) -> Dict[int, str]:
        """Map cluster labels to meaningful regime names based on characteristics"""
        
        regime_characteristics = {}
        
        for cluster_id in np.unique(labels):
            cluster_mask = labels == cluster_id
            cluster_features = feature_data[cluster_mask]
            
            # Calculate regime characteristics
            avg_returns = cluster_features['returns_1d'].mean() if 'returns_1d' in cluster_features.columns else 0
            avg_volatility = cluster_features['volatility_20d'].mean() if 'volatility_20d' in cluster_features.columns else 0
            
            # Determine regime type based on characteristics
            if avg_volatility > 0.05:  # High volatility threshold
                if abs(avg_returns) > 0.03:  # Extreme movements
                    regime_type = "crisis"
                else:
                    regime_type = "high_volatility"
            elif avg_returns > 0.01:  # Positive momentum
                regime_type = "bull_trending"
            elif avg_returns < -0.01:  # Negative momentum
                regime_type = "bear_trending"
            else:  # Low volatility, neutral returns
                regime_type = "sideways"
            
            regime_characteristics[cluster_id] = regime_type
        
        return regime_characteristics
    
    def detect_regime(self, recent_data: pd.DataFrame, lookback_window: int = 20) -> Tuple[str, float]:
        """
        Detect current market regime
        
        Args:
            recent_data: Recent market data
            lookback_window: Number of periods to consider
            
        Returns:
            Tuple of (regime_name, confidence_score)
        """
        try:
            if self.hmm_model is None or self.gmm_model is None:
                self.logger.warning("Models not trained yet")
                return "unknown", 0.0
            
            # Prepare features for the recent data
            features = self.prepare_features(recent_data)
            
            if features.empty or len(features) < lookback_window:
                return "unknown", 0.0
            
            # Get recent window
            recent_features = features.tail(lookback_window)
            
            # Scale features
            scaled_recent = self.scaler.transform(recent_features)
            
            # Get predictions from both models
            gmm_probs = self.gmm_model.predict_proba(scaled_recent)
            hmm_states = self.hmm_model.predict(scaled_recent)
            
            # Focus on most recent prediction
            latest_gmm_probs = gmm_probs[-1]
            latest_hmm_state = hmm_states[-1]
            
            # Combine predictions (weight HMM more heavily)
            final_regime_id = latest_hmm_state
            confidence = latest_gmm_probs[latest_hmm_state]
            
            # Map to regime name
            regime_name = self.regime_mapping.get(final_regime_id, "unknown")
            
            # Update current state
            self.current_regime = regime_name
            self.regime_confidence = float(confidence)
            
            # Update history
            self.regime_history.append({
                'timestamp': datetime.now(),
                'regime': regime_name,
                'confidence': confidence,
                'regime_id': final_regime_id
            })
            
            # Keep only recent history
            if len(self.regime_history) > 1000:
                self.regime_history = self.regime_history[-1000:]
            
            return regime_name, confidence
            
        except Exception as e:
            self.logger.error(f"Regime detection failed: {e}")
            return "unknown", 0.0
    
    def get_regime_confidence(self) -> float:
        """Get confidence score for current regime"""
        return self.regime_confidence
    
    def get_regime_history(self, days: int = 30) -> List[Dict]:
        """Get regime history for specified days"""
        cutoff_date = datetime.now() - timedelta(days=days)
        return [
            entry for entry in self.regime_history 
            if entry['timestamp'] > cutoff_date
        ]
    
    def get_regime_statistics(self) -> Dict:
        """Get statistics about detected regimes"""
        if not self.regime_history:
            return {}
        
        recent_history = self.get_regime_history(30)
        regime_counts = {}
        
        for entry in recent_history:
            regime = entry['regime']
            regime_counts[regime] = regime_counts.get(regime, 0) + 1
        
        total_count = len(recent_history)
        regime_percentages = {
            regime: (count / total_count) * 100 
            for regime, count in regime_counts.items()
        }
        
        return {
            'current_regime': self.current_regime,
            'current_confidence': self.regime_confidence,
            'regime_distribution_30d': regime_percentages,
            'total_detections': total_count
        }
    
    def _save_models(self):
        """Save trained models to disk"""
        try:
            model_files = {
                'hmm_model.pkl': self.hmm_model,
                'gmm_model.pkl': self.gmm_model,
                'scaler.pkl': self.scaler,
                'regime_mapping.pkl': self.regime_mapping,
                'feature_names.pkl': self.feature_names
            }
            
            for filename, model in model_files.items():
                filepath = os.path.join(self.model_path, filename)
                joblib.dump(model, filepath)
            
            self.logger.info(f"Models saved to {self.model_path}")
            
        except Exception as e:
            self.logger.error(f"Model saving failed: {e}")
    
    def load_models(self) -> bool:
        """Load trained models from disk"""
        try:
            model_files = [
                'hmm_model.pkl', 'gmm_model.pkl', 'scaler.pkl', 
                'regime_mapping.pkl', 'feature_names.pkl'
            ]
            
            # Check if all files exist
            for filename in model_files:
                filepath = os.path.join(self.model_path, filename)
                if not os.path.exists(filepath):
                    self.logger.warning(f"Model file not found: {filepath}")
                    return False
            
            # Load models
            self.hmm_model = joblib.load(os.path.join(self.model_path, 'hmm_model.pkl'))
            self.gmm_model = joblib.load(os.path.join(self.model_path, 'gmm_model.pkl'))
            self.scaler = joblib.load(os.path.join(self.model_path, 'scaler.pkl'))
            self.regime_mapping = joblib.load(os.path.join(self.model_path, 'regime_mapping.pkl'))
            self.feature_names = joblib.load(os.path.join(self.model_path, 'feature_names.pkl'))
            
            self.logger.info("Models loaded successfully")
            return True
            
        except Exception as e:
            self.logger.error(f"Model loading failed: {e}")
            return False
    
    def retrain_if_needed(self, recent_performance: Dict) -> bool:
        """
        Check if models need retraining based on performance metrics
        
        Args:
            recent_performance: Dict with recent regime detection performance
            
        Returns:
            bool: Whether retraining was triggered
        """
        # Criteria for retraining
        accuracy_threshold = 0.7
        confidence_threshold = 0.6
        
        recent_accuracy = recent_performance.get('accuracy', 1.0)
        avg_confidence = recent_performance.get('avg_confidence', 1.0)
        
        if recent_accuracy < accuracy_threshold or avg_confidence < confidence_threshold:
            self.logger.info("Performance degraded, retraining recommended")
            return True
        
        return False

# Example usage and testing
if __name__ == "__main__":
    # Example of how to use the regime detector
    detector = MarketRegimeDetector()
    
    # Create sample data for testing
    dates = pd.date_range(start='2023-01-01', end='2024-01-01', freq='D')
    sample_data = pd.DataFrame({
        'close': np.random.randn(len(dates)).cumsum() + 100,
        'volume': np.random.randint(1000, 10000, len(dates)),
        'rsi_14': np.random.uniform(20, 80, len(dates)),
        'ma_20': np.random.randn(len(dates)).cumsum() + 98,
        'ma_50': np.random.randn(len(dates)).cumsum() + 95,
    }, index=dates)
    
    print("Testing regime detector with sample data...")
    
    # Prepare features
    features = detector.prepare_features(sample_data)
    print(f"Prepared {len(features)} feature samples")
    
    # Train models
    if detector.train_models(features):
        print("Models trained successfully")
        
        # Test regime detection
        regime, confidence = detector.detect_regime(sample_data)
        print(f"Detected regime: {regime} (confidence: {confidence:.3f})")
        
        # Get statistics
        stats = detector.get_regime_statistics()
        print(f"Regime statistics: {stats}")
    else:
        print("Model training failed")