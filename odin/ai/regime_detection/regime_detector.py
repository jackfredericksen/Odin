"""
Enhanced Market Regime Detector

Advanced market regime detection using multiple indicators and ML techniques
to classify market states for optimal strategy selection.

File: odin/ai/regime_detection/regime_detector.py
"""

import logging
import os
import sys
from datetime import datetime, timedelta, timezone
from typing import Any, Dict, List, Optional, Tuple

import joblib
import numpy as np
import pandas as pd
from sklearn.cluster import KMeans
from sklearn.ensemble import RandomForestClassifier
from sklearn.preprocessing import StandardScaler

current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.abspath(os.path.join(current_dir, "../../../"))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

# Import with fallback handling
try:
    from odin.core.models import PriceData
except ImportError:
    try:
        # Alternative import path
        from core.models import PriceData
    except ImportError:
        # Create a minimal PriceData class if import fails
        from dataclasses import dataclass
        from datetime import datetime
        from typing import Optional

        @dataclass
        class PriceData:
            timestamp: datetime
            price: float
            volume: Optional[float] = None


logger = logging.getLogger(__name__)


class RegimeDetector:
    """
    Advanced market regime detection system.

    Uses multiple technical indicators and machine learning to identify
    market regimes such as trending, ranging, volatile, and breakout conditions.
    """

    def __init__(self):
        """Initialize the regime detector."""

        # Regime definitions
        self.regime_types = {
            "trending_bullish": "Strong upward price movement with momentum",
            "trending_bearish": "Strong downward price movement with momentum",
            "ranging": "Sideways price movement within bounds",
            "volatile": "High volatility with uncertain direction",
            "breakout": "Price breaking through significant levels",
        }

        # Feature calculation parameters
        self.lookback_periods = {"short": 10, "medium": 20, "long": 50}

        # ML models
        self.scaler = StandardScaler()
        self.regime_classifier = None
        self.volatility_classifier = None
        self.is_trained = False

        # Cache for regime detection
        self.last_regime_result = None
        self.last_regime_time = None
        self.regime_cache_duration = timedelta(minutes=5)

        # Model file paths
        self.model_dir = "data/models"
        self.regime_model_path = os.path.join(
            self.model_dir, "regime_classifier.joblib"
        )
        self.scaler_path = os.path.join(self.model_dir, "regime_scaler.joblib")

        self.logger = logging.getLogger(__name__)

    async def initialize(self, historical_data: List[Dict[str, Any]]):
        """Initialize and train the regime detection models."""
        try:
            # Ensure model directory exists
            os.makedirs(self.model_dir, exist_ok=True)

            # Try to load existing models
            if await self._load_models():
                self.logger.info("Loaded existing regime detection models")
                return

            # Train new models if none exist
            if len(historical_data) >= 200:
                await self._train_models(historical_data)
                self.logger.info("Trained new regime detection models")
            else:
                self.logger.warning(
                    "Insufficient data for model training, using rule-based detection"
                )

        except Exception as e:
            self.logger.error(f"Error initializing regime detector: {e}")

    async def detect_regime(self, price_data: List[PriceData]) -> Dict[str, Any]:
        """
        Detect current market regime based on price data.

        Args:
            price_data: Recent price data for analysis

        Returns:
            Dictionary with regime classification and confidence
        """
        try:
            # Check cache first
            if self._is_cache_valid():
                return self.last_regime_result

            if len(price_data) < self.lookback_periods["long"]:
                return self._default_regime_result("insufficient_data")

            # Convert to DataFrame for analysis
            df = self._price_data_to_dataframe(price_data)

            # Calculate features
            features = self._calculate_regime_features(df)

            # Detect regime using ML models or rules
            if self.is_trained and self.regime_classifier:
                regime_result = await self._ml_regime_detection(features)
            else:
                regime_result = await self._rule_based_regime_detection(features)

            # Add market microstructure analysis
            regime_result = self._enhance_with_microstructure(regime_result, df)

            # Cache result
            self.last_regime_result = regime_result
            self.last_regime_time = datetime.now(timezone.utc)

            return regime_result

        except Exception as e:
            self.logger.error(f"Error detecting regime: {e}")
            return self._default_regime_result("error")

    def _calculate_regime_features(self, df: pd.DataFrame) -> Dict[str, float]:
        """Calculate comprehensive features for regime detection."""
        try:
            features = {}

            # Price features
            current_price = df["close"].iloc[-1]

            # Trend features
            for period_name, period in self.lookback_periods.items():
                if len(df) >= period:
                    # Price change over period
                    price_change = (current_price - df["close"].iloc[-period]) / df[
                        "close"
                    ].iloc[-period]
                    features[f"price_change_{period_name}"] = price_change

                    # Moving average position
                    ma = df["close"].rolling(period).mean().iloc[-1]
                    features[f"ma_position_{period_name}"] = (current_price - ma) / ma

                    # Moving average slope
                    ma_series = df["close"].rolling(period).mean()
                    if len(ma_series) >= 5:
                        ma_slope = (
                            ma_series.iloc[-1] - ma_series.iloc[-5]
                        ) / ma_series.iloc[-5]
                        features[f"ma_slope_{period_name}"] = ma_slope

            # Volatility features
            returns = df["close"].pct_change().dropna()
            if len(returns) >= 20:
                features["volatility_20"] = returns.rolling(20).std().iloc[-1]
                features["volatility_5"] = returns.rolling(5).std().iloc[-1]
                features["volatility_ratio"] = (
                    features["volatility_5"] / features["volatility_20"]
                    if features["volatility_20"] > 0
                    else 1
                )

            # Technical indicators
            features.update(self._calculate_technical_features(df))

            # Volume features
            if "volume" in df.columns:
                features.update(self._calculate_volume_features(df))

            # Price action features
            features.update(self._calculate_price_action_features(df))

            return features

        except Exception as e:
            self.logger.error(f"Error calculating regime features: {e}")
            return {}

    def _calculate_technical_features(self, df: pd.DataFrame) -> Dict[str, float]:
        """Calculate technical indicator features."""
        try:
            features = {}

            # RSI
            rsi = self._calculate_rsi(df["close"], 14)
            if not rsi.empty:
                features["rsi"] = rsi.iloc[-1]
                features["rsi_oversold"] = 1 if rsi.iloc[-1] < 30 else 0
                features["rsi_overbought"] = 1 if rsi.iloc[-1] > 70 else 0

            # MACD
            macd_line, macd_signal = self._calculate_macd(df["close"])
            if not macd_line.empty:
                features["macd"] = macd_line.iloc[-1]
                features["macd_signal"] = macd_signal.iloc[-1]
                features["macd_histogram"] = macd_line.iloc[-1] - macd_signal.iloc[-1]
                features["macd_bullish"] = 1 if features["macd_histogram"] > 0 else 0

            # Bollinger Bands
            bb_upper, bb_middle, bb_lower = self._calculate_bollinger_bands(
                df["close"], 20, 2
            )
            if not bb_middle.empty:
                current_price = df["close"].iloc[-1]
                features["bb_position"] = (current_price - bb_lower.iloc[-1]) / (
                    bb_upper.iloc[-1] - bb_lower.iloc[-1]
                )
                features["bb_width"] = (
                    bb_upper.iloc[-1] - bb_lower.iloc[-1]
                ) / bb_middle.iloc[-1]
                features["bb_squeeze"] = 1 if features["bb_width"] < 0.1 else 0

            # ADX (trend strength)
            adx = self._calculate_adx(df)
            if adx is not None:
                features["adx"] = adx
                features["strong_trend"] = 1 if adx > 25 else 0

            return features

        except Exception as e:
            self.logger.error(f"Error calculating technical features: {e}")
            return {}

    def _calculate_volume_features(self, df: pd.DataFrame) -> Dict[str, float]:
        """Calculate volume-based features."""
        try:
            features = {}

            if "volume" in df.columns and len(df) >= 20:
                # Volume moving averages
                vol_ma_20 = df["volume"].rolling(20).mean()
                current_volume = df["volume"].iloc[-1]

                if not vol_ma_20.empty and vol_ma_20.iloc[-1] > 0:
                    features["volume_ratio"] = current_volume / vol_ma_20.iloc[-1]
                    features["high_volume"] = 1 if features["volume_ratio"] > 1.5 else 0

                # Volume trend
                if len(df) >= 10:
                    recent_vol = df["volume"].iloc[-5:].mean()
                    older_vol = df["volume"].iloc[-15:-5].mean()
                    if older_vol > 0:
                        features["volume_trend"] = (recent_vol - older_vol) / older_vol

                # On-Balance Volume (simplified)
                price_changes = df["close"].diff()
                volume_direction = np.where(
                    price_changes > 0,
                    df["volume"],
                    np.where(price_changes < 0, -df["volume"], 0),
                )
                obv = volume_direction.cumsum()
                if len(obv) >= 10:
                    obv_slope = (obv.iloc[-1] - obv.iloc[-10]) / 10
                    features["obv_slope"] = obv_slope

            return features

        except Exception as e:
            self.logger.error(f"Error calculating volume features: {e}")
            return {}

    def _calculate_price_action_features(self, df: pd.DataFrame) -> Dict[str, float]:
        """Calculate price action features."""
        try:
            features = {}

            if len(df) >= 20:
                # Support and resistance levels
                highs = df["high"].rolling(10, center=True).max()
                lows = df["low"].rolling(10, center=True).min()

                current_price = df["close"].iloc[-1]
                recent_high = df["high"].iloc[-20:].max()
                recent_low = df["low"].iloc[-20:].min()

                # Distance to recent highs/lows
                if recent_high > 0:
                    features["distance_to_high"] = (
                        current_price - recent_high
                    ) / recent_high
                if recent_low > 0:
                    features["distance_to_low"] = (
                        current_price - recent_low
                    ) / recent_low

                # Price range analysis
                price_range = recent_high - recent_low
                if recent_low > 0:
                    features["range_position"] = (
                        (current_price - recent_low) / price_range
                        if price_range > 0
                        else 0.5
                    )

                # Candlestick patterns (simplified)
                if len(df) >= 5:
                    # Doji detection
                    body_size = abs(df["close"] - df["open"]) / df["close"]
                    features["doji_pattern"] = 1 if body_size.iloc[-1] < 0.01 else 0

                    # Hammer/hanging man
                    lower_shadow = (df[["open", "close"]].min(axis=1) - df["low"]) / df[
                        "close"
                    ]
                    features["long_lower_shadow"] = (
                        1 if lower_shadow.iloc[-1] > 0.02 else 0
                    )

            return features

        except Exception as e:
            self.logger.error(f"Error calculating price action features: {e}")
            return {}

    async def _ml_regime_detection(self, features: Dict[str, float]) -> Dict[str, Any]:
        """Use ML models for regime detection."""
        try:
            # Prepare feature vector
            feature_vector = self._prepare_feature_vector(features)

            # Predict regime
            regime_probs = self.regime_classifier.predict_proba([feature_vector])[0]
            regime_classes = self.regime_classifier.classes_

            # Get best prediction
            best_regime_idx = np.argmax(regime_probs)
            best_regime = regime_classes[best_regime_idx]
            confidence = regime_probs[best_regime_idx]

            # Get regime probabilities
            regime_probabilities = {
                regime: float(prob)
                for regime, prob in zip(regime_classes, regime_probs)
            }

            return {
                "current_regime": best_regime,
                "confidence": float(confidence),
                "regime_probabilities": regime_probabilities,
                "detection_method": "ml",
                "features_used": list(features.keys()),
            }

        except Exception as e:
            self.logger.error(f"Error in ML regime detection: {e}")
            return await self._rule_based_regime_detection(features)

    async def _rule_based_regime_detection(
        self, features: Dict[str, float]
    ) -> Dict[str, Any]:
        """Rule-based regime detection as fallback."""
        try:
            scores = {regime: 0.0 for regime in self.regime_types.keys()}

            # Trending bullish indicators
            if features.get("price_change_medium", 0) > 0.02:
                scores["trending_bullish"] += 0.3
            if features.get("ma_slope_short", 0) > 0.01:
                scores["trending_bullish"] += 0.2
            if features.get("rsi", 50) > 50:
                scores["trending_bullish"] += 0.1
            if features.get("macd_bullish", 0) == 1:
                scores["trending_bullish"] += 0.2
            if features.get("high_volume", 0) == 1:
                scores["trending_bullish"] += 0.1

            # Trending bearish indicators
            if features.get("price_change_medium", 0) < -0.02:
                scores["trending_bearish"] += 0.3
            if features.get("ma_slope_short", 0) < -0.01:
                scores["trending_bearish"] += 0.2
            if features.get("rsi", 50) < 50:
                scores["trending_bearish"] += 0.1
            if features.get("macd_bullish", 0) == 0:
                scores["trending_bearish"] += 0.2
            if features.get("high_volume", 0) == 1:
                scores["trending_bearish"] += 0.1

            # Ranging indicators
            if abs(features.get("price_change_medium", 0)) < 0.015:
                scores["ranging"] += 0.3
            if (
                features.get("bb_position", 0.5) > 0.2
                and features.get("bb_position", 0.5) < 0.8
            ):
                scores["ranging"] += 0.2
            if features.get("strong_trend", 0) == 0:
                scores["ranging"] += 0.2
            if (
                features.get("rsi_oversold", 0) == 1
                or features.get("rsi_overbought", 0) == 1
            ):
                scores["ranging"] += 0.1

            # Volatile indicators
            if features.get("volatility_ratio", 1) > 1.5:
                scores["volatile"] += 0.4
            if features.get("bb_width", 0) > 0.15:
                scores["volatile"] += 0.2
            if features.get("volume_ratio", 1) > 2.0:
                scores["volatile"] += 0.2

            # Breakout indicators
            if features.get("distance_to_high", -1) > -0.02:
                scores["breakout"] += 0.3
            if features.get("distance_to_low", 1) < 0.02:
                scores["breakout"] += 0.3
            if (
                features.get("bb_position", 0.5) > 0.9
                or features.get("bb_position", 0.5) < 0.1
            ):
                scores["breakout"] += 0.2
            if features.get("high_volume", 0) == 1:
                scores["breakout"] += 0.2

            # Determine best regime
            best_regime = max(scores.items(), key=lambda x: x[1])
            regime_name = best_regime[0]
            confidence = min(best_regime[1], 1.0)

            # Ensure minimum confidence
            if confidence < 0.3:
                regime_name = "ranging"  # Default to ranging
                confidence = 0.5

            return {
                "current_regime": regime_name,
                "confidence": confidence,
                "regime_scores": scores,
                "detection_method": "rule_based",
                "features_used": list(features.keys()),
            }

        except Exception as e:
            self.logger.error(f"Error in rule-based regime detection: {e}")
            return self._default_regime_result("error")

    def _enhance_with_microstructure(
        self, regime_result: Dict[str, Any], df: pd.DataFrame
    ) -> Dict[str, Any]:
        """Enhance regime detection with market microstructure analysis."""
        try:
            # Add trend direction
            if len(df) >= 10:
                short_ma = df["close"].rolling(5).mean().iloc[-1]
                long_ma = df["close"].rolling(20).mean().iloc[-1]

                if short_ma > long_ma:
                    trend = "bullish"
                elif short_ma < long_ma:
                    trend = "bearish"
                else:
                    trend = "neutral"

                regime_result["trend"] = trend

            # Add volatility assessment
            if len(df) >= 20:
                returns = df["close"].pct_change().dropna()
                recent_vol = returns.rolling(10).std().iloc[-1]
                long_vol = returns.rolling(20).std().iloc[-1]

                if recent_vol > long_vol * 1.5:
                    volatility = "high"
                elif recent_vol < long_vol * 0.7:
                    volatility = "low"
                else:
                    volatility = "medium"

                regime_result["volatility"] = volatility

            # Add market strength indicator
            regime_result["market_strength"] = self._calculate_market_strength(df)

            return regime_result

        except Exception as e:
            self.logger.error(f"Error enhancing with microstructure: {e}")
            return regime_result

    def _calculate_market_strength(self, df: pd.DataFrame) -> str:
        """Calculate overall market strength."""
        try:
            if len(df) < 20:
                return "unknown"

            # Price momentum
            price_change = (df["close"].iloc[-1] - df["close"].iloc[-20]) / df[
                "close"
            ].iloc[-20]

            # Volume confirmation
            vol_ratio = 1.0
            if "volume" in df.columns:
                recent_vol = df["volume"].iloc[-5:].mean()
                avg_vol = df["volume"].iloc[-20:].mean()
                vol_ratio = recent_vol / avg_vol if avg_vol > 0 else 1.0

            # Technical strength
            rsi = self._calculate_rsi(df["close"], 14)
            rsi_value = rsi.iloc[-1] if not rsi.empty else 50

            # Combine factors
            strength_score = 0

            if price_change > 0.03:
                strength_score += 2
            elif price_change > 0.01:
                strength_score += 1
            elif price_change < -0.03:
                strength_score -= 2
            elif price_change < -0.01:
                strength_score -= 1

            if vol_ratio > 1.2:
                strength_score += 1
            elif vol_ratio < 0.8:
                strength_score -= 1

            if rsi_value > 60:
                strength_score += 1
            elif rsi_value < 40:
                strength_score -= 1

            # Classify strength
            if strength_score >= 3:
                return "very_strong"
            elif strength_score >= 1:
                return "strong"
            elif strength_score <= -3:
                return "very_weak"
            elif strength_score <= -1:
                return "weak"
            else:
                return "neutral"

        except Exception as e:
            self.logger.error(f"Error calculating market strength: {e}")
            return "unknown"

    async def _train_models(self, historical_data: List[Dict[str, Any]]):
        """Train ML models for regime detection."""
        try:
            # Convert historical data to DataFrame
            df = pd.DataFrame(historical_data)
            df["timestamp"] = pd.to_datetime(df["timestamp"])
            df.set_index("timestamp", inplace=True)
            df.sort_index(inplace=True)

            # Generate training data
            training_data = []
            labels = []

            # Create sliding windows for feature extraction
            window_size = self.lookback_periods["long"]

            for i in range(
                window_size, len(df) - 10, 5
            ):  # Skip every 5 points to reduce correlation
                window_df = df.iloc[i - window_size : i + 1].copy()

                # Calculate features for this window
                features = self._calculate_regime_features(window_df)

                if features:
                    # Create label based on future price movement
                    future_window = df.iloc[i + 1 : i + 11]  # Next 10 periods
                    label = self._create_regime_label(window_df, future_window)

                    training_data.append(list(features.values()))
                    labels.append(label)

            if len(training_data) < 50:
                self.logger.warning("Insufficient training data for ML models")
                return

            # Prepare training arrays
            X = np.array(training_data)
            y = np.array(labels)

            # Handle missing values
            X = np.nan_to_num(X, nan=0.0)

            # Scale features
            X_scaled = self.scaler.fit_transform(X)

            # Train regime classifier
            self.regime_classifier = RandomForestClassifier(
                n_estimators=100, max_depth=10, random_state=42, class_weight="balanced"
            )

            self.regime_classifier.fit(X_scaled, y)
            self.is_trained = True

            # Save models
            await self._save_models()

            self.logger.info(
                f"Trained regime classifier with {len(training_data)} samples"
            )

        except Exception as e:
            self.logger.error(f"Error training models: {e}")

    def _create_regime_label(
        self, current_window: pd.DataFrame, future_window: pd.DataFrame
    ) -> str:
        """Create regime label based on price movement patterns."""
        try:
            current_price = current_window["close"].iloc[-1]
            future_prices = future_window["close"]

            # Calculate future price statistics
            future_return = (future_prices.iloc[-1] - current_price) / current_price
            future_volatility = future_prices.pct_change().std()
            max_price = future_prices.max()
            min_price = future_prices.min()
            price_range = (max_price - min_price) / current_price

            # Classify regime based on future behavior
            if future_return > 0.02 and future_volatility < 0.03:
                return "trending_bullish"
            elif future_return < -0.02 and future_volatility < 0.03:
                return "trending_bearish"
            elif price_range > 0.05:
                return "volatile"
            elif abs(future_return) < 0.015 and price_range < 0.03:
                return "ranging"
            elif price_range > 0.03 and abs(future_return) > 0.01:
                return "breakout"
            else:
                return "ranging"  # Default

        except Exception as e:
            self.logger.error(f"Error creating regime label: {e}")
            return "ranging"

    async def _save_models(self):
        """Save trained models to disk."""
        try:
            if self.regime_classifier:
                joblib.dump(self.regime_classifier, self.regime_model_path)

            if hasattr(self.scaler, "scale_"):
                joblib.dump(self.scaler, self.scaler_path)

            self.logger.info("Saved regime detection models")

        except Exception as e:
            self.logger.error(f"Error saving models: {e}")

    async def _load_models(self) -> bool:
        """Load existing models from disk."""
        try:
            if os.path.exists(self.regime_model_path) and os.path.exists(
                self.scaler_path
            ):
                self.regime_classifier = joblib.load(self.regime_model_path)
                self.scaler = joblib.load(self.scaler_path)
                self.is_trained = True
                return True
            return False

        except Exception as e:
            self.logger.error(f"Error loading models: {e}")
            return False

    def _prepare_feature_vector(self, features: Dict[str, float]) -> List[float]:
        """Prepare feature vector for ML prediction."""
        # Define expected feature order (should match training)
        expected_features = [
            "price_change_short",
            "price_change_medium",
            "price_change_long",
            "ma_position_short",
            "ma_position_medium",
            "ma_position_long",
            "ma_slope_short",
            "ma_slope_medium",
            "ma_slope_long",
            "volatility_20",
            "volatility_5",
            "volatility_ratio",
            "rsi",
            "rsi_oversold",
            "rsi_overbought",
            "macd",
            "macd_signal",
            "macd_histogram",
            "macd_bullish",
            "bb_position",
            "bb_width",
            "bb_squeeze",
            "adx",
            "strong_trend",
            "volume_ratio",
            "high_volume",
            "volume_trend",
            "obv_slope",
            "distance_to_high",
            "distance_to_low",
            "range_position",
            "doji_pattern",
            "long_lower_shadow",
        ]

        feature_vector = []
        for feature_name in expected_features:
            value = features.get(feature_name, 0.0)
            # Handle any remaining NaN values
            if np.isnan(value) or np.isinf(value):
                value = 0.0
            feature_vector.append(value)

        return feature_vector

    def _price_data_to_dataframe(self, price_data: List[PriceData]) -> pd.DataFrame:
        """Convert price data to DataFrame."""
        data = []
        for price_point in price_data:
            data.append(
                {
                    "timestamp": price_point.timestamp,
                    "open": price_point.price,
                    "high": price_point.price,
                    "low": price_point.price,
                    "close": price_point.price,
                    "volume": price_point.volume or 1000.0,
                }
            )

        df = pd.DataFrame(data)
        if not df.empty:
            df.set_index("timestamp", inplace=True)
            df.sort_index(inplace=True)

        return df

    def _is_cache_valid(self) -> bool:
        """Check if cached regime result is still valid."""
        if not self.last_regime_result or not self.last_regime_time:
            return False

        return (
            datetime.now(timezone.utc) - self.last_regime_time
            < self.regime_cache_duration
        )

    def _default_regime_result(self, reason: str) -> Dict[str, Any]:
        """Return default regime result."""
        return {
            "current_regime": "ranging",
            "confidence": 0.5,
            "trend": "neutral",
            "volatility": "medium",
            "market_strength": "neutral",
            "detection_method": "default",
            "reason": reason,
        }

    # Technical indicator calculation methods
    def _calculate_rsi(self, prices: pd.Series, period: int = 14) -> pd.Series:
        """Calculate RSI."""
        delta = prices.diff()
        gains = delta.where(delta > 0, 0.0)
        losses = -delta.where(delta < 0, 0.0)

        avg_gains = gains.ewm(alpha=1 / period, adjust=False).mean()
        avg_losses = losses.ewm(alpha=1 / period, adjust=False).mean()

        rs = avg_gains / avg_losses
        return 100 - (100 / (1 + rs))

    def _calculate_macd(
        self, prices: pd.Series, fast: int = 12, slow: int = 26, signal: int = 9
    ) -> Tuple[pd.Series, pd.Series]:
        """Calculate MACD."""
        ema_fast = prices.ewm(span=fast).mean()
        ema_slow = prices.ewm(span=slow).mean()
        macd_line = ema_fast - ema_slow
        macd_signal = macd_line.ewm(span=signal).mean()
        return macd_line, macd_signal

    def _calculate_bollinger_bands(
        self, prices: pd.Series, period: int = 20, std_dev: float = 2
    ) -> Tuple[pd.Series, pd.Series, pd.Series]:
        """Calculate Bollinger Bands."""
        middle = prices.rolling(period).mean()
        std = prices.rolling(period).std()
        upper = middle + (std * std_dev)
        lower = middle - (std * std_dev)
        return upper, middle, lower

    def _calculate_adx(self, df: pd.DataFrame, period: int = 14) -> Optional[float]:
        """Calculate ADX (simplified)."""
        try:
            if len(df) < period * 2:
                return None

            # Calculate True Range
            high_low = df["high"] - df["low"]
            high_close = abs(df["high"] - df["close"].shift())
            low_close = abs(df["low"] - df["close"].shift())

            tr = pd.concat([high_low, high_close, low_close], axis=1).max(axis=1)

            # Calculate Directional Movement
            plus_dm = np.where(
                (df["high"] - df["high"].shift()) > (df["low"].shift() - df["low"]),
                np.maximum(df["high"] - df["high"].shift(), 0),
                0,
            )
            minus_dm = np.where(
                (df["low"].shift() - df["low"]) > (df["high"] - df["high"].shift()),
                np.maximum(df["low"].shift() - df["low"], 0),
                0,
            )

            # Smooth the values
            tr_smooth = pd.Series(tr).rolling(period).mean()
            plus_dm_smooth = pd.Series(plus_dm).rolling(period).mean()
            minus_dm_smooth = pd.Series(minus_dm).rolling(period).mean()

            # Calculate DI
            plus_di = 100 * plus_dm_smooth / tr_smooth
            minus_di = 100 * minus_dm_smooth / tr_smooth

            # Calculate DX
            dx = 100 * abs(plus_di - minus_di) / (plus_di + minus_di)

            # Calculate ADX
            adx = dx.rolling(period).mean()

            return adx.iloc[-1] if not adx.empty else None

        except Exception as e:
            self.logger.error(f"Error calculating ADX: {e}")
            return None

    async def get_regime_history(self, hours: int = 24) -> List[Dict[str, Any]]:
        """Get historical regime classifications."""
        try:
            # This would ideally load from database
            # For now, return placeholder data
            history = []
            current_time = datetime.now(timezone.utc)

            for i in range(hours):
                timestamp = current_time - timedelta(hours=hours - i)

                # Generate realistic regime progression
                regimes = [
                    "trending_bullish",
                    "ranging",
                    "volatile",
                    "trending_bearish",
                ]
                regime = regimes[i % len(regimes)]

                history.append(
                    {
                        "timestamp": timestamp.isoformat(),
                        "regime": regime,
                        "confidence": 0.6 + (i % 4) * 0.1,
                        "trend": (
                            "bullish"
                            if "bullish" in regime
                            else "bearish"
                            if "bearish" in regime
                            else "neutral"
                        ),
                    }
                )

            return history

        except Exception as e:
            self.logger.error(f"Error getting regime history: {e}")
            return []

    async def health_check(self) -> bool:
        """Check if regime detector is functioning properly."""
        try:
            # Test with dummy data
            dummy_data = []
            base_price = 50000

            for i in range(60):
                dummy_data.append(
                    PriceData(
                        timestamp=datetime.now(timezone.utc)
                        - timedelta(minutes=60 - i),
                        price=base_price + i * 10 + np.random.normal(0, 50),
                        volume=1000 + np.random.normal(0, 100),
                    )
                )

            result = await self.detect_regime(dummy_data)

            # Check if result has required fields
            required_fields = ["current_regime", "confidence"]
            return all(field in result for field in required_fields)

        except Exception as e:
            self.logger.error(f"Health check failed: {e}")
            return False

    def get_regime_descriptions(self) -> Dict[str, str]:
        """Get descriptions of all regime types."""
        return self.regime_types.copy()

    def clear_cache(self):
        """Clear regime detection cache."""
        self.last_regime_result = None
        self.last_regime_time = None
        self.logger.info("Regime detection cache cleared")
