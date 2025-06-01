# strategies/enhanced_strategies.py

import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import sqlite3
import os
from typing import Dict, List, Tuple, Optional

class MultiTimeframeStrategy:
    def __init__(self, db_path=None):
        """
        Multi-timeframe analysis strategy
        Combines signals from multiple timeframes for better accuracy
        """
        if db_path is None:
            current_dir = os.path.dirname(os.path.abspath(__file__))
            project_root = os.path.dirname(current_dir)
            db_path = os.path.join(project_root, 'data', 'bitcoin_data.db')
        
        self.db_path = db_path
        self.timeframes = {
            '1H': 60,   # 1 hour in minutes
            '4H': 240,  # 4 hours in minutes
            '1D': 1440, # 1 day in minutes
        }
    
    def get_timeframe_data(self, timeframe_minutes: int, hours_back: int = 168) -> pd.DataFrame:
        """Get resampled data for specific timeframe"""
        conn = sqlite3.connect(self.db_path)
        
        cutoff_time = (datetime.now() - timedelta(hours=hours_back)).strftime('%Y-%m-%d %H:%M:%S')
        
        df = pd.read_sql_query('''
            SELECT timestamp, price, volume FROM btc_prices 
            WHERE timestamp >= ? 
            ORDER BY timestamp ASC
        ''', conn, params=(cutoff_time,))
        conn.close()
        
        if len(df) == 0:
            return None
        
        df['timestamp'] = pd.to_datetime(df['timestamp'])
        df.set_index('timestamp', inplace=True)
        
        # Resample to desired timeframe
        timeframe_str = f'{timeframe_minutes}T'
        resampled = df.resample(timeframe_str).agg({
            'price': 'ohlc',
            'volume': 'sum'
        }).dropna()
        
        # Flatten column names
        resampled.columns = ['open', 'high', 'low', 'close', 'volume']
        
        return resampled
    
    def calculate_rsi(self, prices: pd.Series, period: int = 14) -> pd.Series:
        """Calculate RSI indicator"""
        delta = prices.diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=period).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=period).mean()
        rs = gain / loss
        rsi = 100 - (100 / (1 + rs))
        return rsi
    
    def calculate_macd(self, prices: pd.Series, fast: int = 12, slow: int = 26, signal: int = 9) -> Tuple[pd.Series, pd.Series, pd.Series]:
        """Calculate MACD indicator"""
        ema_fast = prices.ewm(span=fast).mean()
        ema_slow = prices.ewm(span=slow).mean()
        macd_line = ema_fast - ema_slow
        signal_line = macd_line.ewm(span=signal).mean()
        histogram = macd_line - signal_line
        return macd_line, signal_line, histogram
    
    def calculate_bollinger_bands(self, prices: pd.Series, period: int = 20, std_dev: float = 2) -> Tuple[pd.Series, pd.Series, pd.Series]:
        """Calculate Bollinger Bands"""
        ma = prices.rolling(window=period).mean()
        std = prices.rolling(window=period).std()
        upper_band = ma + (std * std_dev)
        lower_band = ma - (std * std_dev)
        return upper_band, ma, lower_band
    
    def analyze_timeframe(self, timeframe: str) -> Dict:
        """Analyze single timeframe and generate signals"""
        timeframe_minutes = self.timeframes[timeframe]
        data = self.get_timeframe_data(timeframe_minutes)
        
        if data is None or len(data) < 50:
            return {'error': f'Not enough data for {timeframe}'}
        
        # Calculate indicators
        prices = data['close']
        
        # Moving averages
        ma_short = prices.rolling(window=20).mean()
        ma_long = prices.rolling(window=50).mean()
        
        # RSI
        rsi = self.calculate_rsi(prices)
        
        # MACD
        macd_line, signal_line, histogram = self.calculate_macd(prices)
        
        # Bollinger Bands
        bb_upper, bb_middle, bb_lower = self.calculate_bollinger_bands(prices)
        
        # Get latest values
        latest = data.iloc[-1]
        latest_price = latest['close']
        latest_rsi = rsi.iloc[-1] if not pd.isna(rsi.iloc[-1]) else 50
        latest_ma_short = ma_short.iloc[-1] if not pd.isna(ma_short.iloc[-1]) else latest_price
        latest_ma_long = ma_long.iloc[-1] if not pd.isna(ma_long.iloc[-1]) else latest_price
        latest_macd = macd_line.iloc[-1] if not pd.isna(macd_line.iloc[-1]) else 0
        latest_signal = signal_line.iloc[-1] if not pd.isna(signal_line.iloc[-1]) else 0
        latest_bb_upper = bb_upper.iloc[-1] if not pd.isna(bb_upper.iloc[-1]) else latest_price * 1.02
        latest_bb_lower = bb_lower.iloc[-1] if not pd.isna(bb_lower.iloc[-1]) else latest_price * 0.98
        
        # Generate signals
        signals = []
        
        # MA crossover signal
        if latest_ma_short > latest_ma_long:
            signals.append('MA_BULLISH')
        else:
            signals.append('MA_BEARISH')
        
        # RSI signals
        if latest_rsi > 70:
            signals.append('RSI_OVERBOUGHT')
        elif latest_rsi < 30:
            signals.append('RSI_OVERSOLD')
        else:
            signals.append('RSI_NEUTRAL')
        
        # MACD signals
        if latest_macd > latest_signal:
            signals.append('MACD_BULLISH')
        else:
            signals.append('MACD_BEARISH')
        
        # Bollinger Bands signals
        if latest_price > latest_bb_upper:
            signals.append('BB_OVERBOUGHT')
        elif latest_price < latest_bb_lower:
            signals.append('BB_OVERSOLD')
        else:
            signals.append('BB_NEUTRAL')
        
        return {
            'timeframe': timeframe,
            'price': latest_price,
            'ma_short': latest_ma_short,
            'ma_long': latest_ma_long,
            'rsi': latest_rsi,
            'macd': latest_macd,
            'macd_signal': latest_signal,
            'bb_upper': latest_bb_upper,
            'bb_lower': latest_bb_lower,
            'signals': signals,
            'data_points': len(data)
        }
    
    def get_multi_timeframe_signal(self) -> Dict:
        """Combine signals from all timeframes"""
        timeframe_analyses = {}
        
        for tf in self.timeframes.keys():
            analysis = self.analyze_timeframe(tf)
            if 'error' not in analysis:
                timeframe_analyses[tf] = analysis
        
        if not timeframe_analyses:
            return {'error': 'No timeframe data available'}
        
        # Score each timeframe
        scores = {}
        for tf, analysis in timeframe_analyses.items():
            score = 0
            signals = analysis['signals']
            
            # MA signals (weighted by timeframe)
            tf_weight = {'1H': 1, '4H': 2, '1D': 3}.get(tf, 1)
            
            if 'MA_BULLISH' in signals:
                score += 1 * tf_weight
            if 'MA_BEARISH' in signals:
                score -= 1 * tf_weight
            
            # RSI signals
            if 'RSI_OVERSOLD' in signals:
                score += 1
            if 'RSI_OVERBOUGHT' in signals:
                score -= 1
            
            # MACD signals
            if 'MACD_BULLISH' in signals:
                score += 1
            if 'MACD_BEARISH' in signals:
                score -= 1
            
            # Bollinger Bands
            if 'BB_OVERSOLD' in signals:
                score += 1
            if 'BB_OVERBOUGHT' in signals:
                score -= 1
            
            scores[tf] = score
        
        # Calculate overall signal
        total_score = sum(scores.values())
        signal_strength = abs(total_score) / len(scores) if scores else 0
        
        if total_score > 2:
            overall_signal = 'STRONG_BUY'
        elif total_score > 0:
            overall_signal = 'BUY'
        elif total_score < -2:
            overall_signal = 'STRONG_SELL'
        elif total_score < 0:
            overall_signal = 'SELL'
        else:
            overall_signal = 'HOLD'
        
        return {
            'overall_signal': overall_signal,
            'signal_strength': signal_strength,
            'total_score': total_score,
            'timeframe_scores': scores,
            'timeframe_analyses': timeframe_analyses
        }


class MarketRegimeDetector:
    def __init__(self, db_path=None):
        """
        Detect market regimes (bull/bear/sideways) and adapt strategies
        """
        if db_path is None:
            current_dir = os.path.dirname(os.path.abspath(__file__))
            project_root = os.path.dirname(current_dir)
            db_path = os.path.join(project_root, 'data', 'bitcoin_data.db')
        
        self.db_path = db_path
    
    def get_historical_data(self, hours: int = 720) -> pd.DataFrame:  # 30 days
        """Get historical data for regime analysis"""
        conn = sqlite3.connect(self.db_path)
        
        cutoff_time = (datetime.now() - timedelta(hours=hours)).strftime('%Y-%m-%d %H:%M:%S')
        
        df = pd.read_sql_query('''
            SELECT timestamp, price FROM btc_prices 
            WHERE timestamp >= ? 
            ORDER BY timestamp ASC
        ''', conn, params=(cutoff_time,))
        conn.close()
        
        if len(df) == 0:
            return None
        
        df['timestamp'] = pd.to_datetime(df['timestamp'])
        df.set_index('timestamp', inplace=True)
        
        return df
    
    def calculate_volatility(self, prices: pd.Series, window: int = 20) -> float:
        """Calculate rolling volatility"""
        returns = prices.pct_change().dropna()
        volatility = returns.rolling(window=window).std().iloc[-1]
        return volatility * np.sqrt(252)  # Annualized
    
    def detect_trend(self, prices: pd.Series) -> Dict:
        """Detect trend direction and strength"""
        # Calculate various moving averages
        ma_5 = prices.rolling(window=5).mean()
        ma_20 = prices.rolling(window=20).mean()
        ma_50 = prices.rolling(window=50).mean()
        ma_200 = prices.rolling(window=200).mean()
        
        current_price = prices.iloc[-1]
        
        # Count bullish conditions
        bullish_conditions = 0
        total_conditions = 0
        
        if not pd.isna(ma_5.iloc[-1]):
            total_conditions += 1
            if current_price > ma_5.iloc[-1]:
                bullish_conditions += 1
        
        if not pd.isna(ma_20.iloc[-1]):
            total_conditions += 1
            if current_price > ma_20.iloc[-1]:
                bullish_conditions += 1
        
        if not pd.isna(ma_50.iloc[-1]):
            total_conditions += 1
            if current_price > ma_50.iloc[-1]:
                bullish_conditions += 1
        
        if not pd.isna(ma_200.iloc[-1]):
            total_conditions += 1
            if current_price > ma_200.iloc[-1]:
                bullish_conditions += 1
        
        trend_strength = bullish_conditions / total_conditions if total_conditions > 0 else 0.5
        
        if trend_strength >= 0.75:
            trend = 'STRONG_BULL'
        elif trend_strength >= 0.6:
            trend = 'BULL'
        elif trend_strength <= 0.25:
            trend = 'STRONG_BEAR'
        elif trend_strength <= 0.4:
            trend = 'BEAR'
        else:
            trend = 'SIDEWAYS'
        
        return {
            'trend': trend,
            'trend_strength': trend_strength,
            'ma_5': ma_5.iloc[-1] if not pd.isna(ma_5.iloc[-1]) else current_price,
            'ma_20': ma_20.iloc[-1] if not pd.isna(ma_20.iloc[-1]) else current_price,
            'ma_50': ma_50.iloc[-1] if not pd.isna(ma_50.iloc[-1]) else current_price,
            'ma_200': ma_200.iloc[-1] if not pd.isna(ma_200.iloc[-1]) else current_price
        }
    
    def detect_market_regime(self) -> Dict:
        """Detect current market regime"""
        data = self.get_historical_data()
        
        if data is None or len(data) < 200:
            return {'error': 'Not enough data for regime detection'}
        
        prices = data['price']
        
        # Calculate volatility
        volatility = self.calculate_volatility(prices)
        
        # Detect trend
        trend_info = self.detect_trend(prices)
        
        # Calculate price momentum
        returns_1d = prices.pct_change(24).iloc[-1] if len(prices) > 24 else 0
        returns_7d = prices.pct_change(168).iloc[-1] if len(prices) > 168 else 0
        returns_30d = prices.pct_change(720).iloc[-1] if len(prices) > 720 else 0
        
        # Determine regime
        if volatility > 0.8:  # High volatility
            if trend_info['trend'] in ['STRONG_BULL', 'BULL']:
                regime = 'VOLATILE_BULL'
            elif trend_info['trend'] in ['STRONG_BEAR', 'BEAR']:
                regime = 'VOLATILE_BEAR'
            else:
                regime = 'HIGH_VOLATILITY'
        elif volatility < 0.3:  # Low volatility
            regime = 'LOW_VOLATILITY'
        else:  # Normal volatility
            if trend_info['trend'] in ['STRONG_BULL', 'BULL']:
                regime = 'BULL_MARKET'
            elif trend_info['trend'] in ['STRONG_BEAR', 'BEAR']:
                regime = 'BEAR_MARKET'
            else:
                regime = 'SIDEWAYS_MARKET'
        
        return {
            'regime': regime,
            'volatility': volatility,
            'trend_info': trend_info,
            'returns_1d': returns_1d * 100,
            'returns_7d': returns_7d * 100,
            'returns_30d': returns_30d * 100,
            'current_price': prices.iloc[-1]
        }


class StrategyEnsemble:
    def __init__(self, db_path=None):
        """
        Ensemble of multiple strategies with dynamic weighting
        """
        if db_path is None:
            current_dir = os.path.dirname(os.path.abspath(__file__))
            project_root = os.path.dirname(current_dir)
            db_path = os.path.join(project_root, 'data', 'bitcoin_data.db')
        
        self.db_path = db_path
        self.mtf_strategy = MultiTimeframeStrategy(db_path)
        self.regime_detector = MarketRegimeDetector(db_path)
        
        # Strategy weights (can be dynamically adjusted)
        self.strategy_weights = {
            'ma_crossover': 0.3,
            'multi_timeframe': 0.4,
            'mean_reversion': 0.3
        }
        
        # Performance tracking for dynamic weighting
        self.strategy_performance = {
            'ma_crossover': {'trades': [], 'win_rate': 0.5, 'avg_return': 0.0},
            'multi_timeframe': {'trades': [], 'win_rate': 0.5, 'avg_return': 0.0},
            'mean_reversion': {'trades': [], 'win_rate': 0.5, 'avg_return': 0.0}
        }
    
    def get_ma_crossover_signal(self) -> Dict:
        """Simple MA crossover signal"""
        from ma_crossover import MovingAverageCrossoverStrategy
        
        ma_strategy = MovingAverageCrossoverStrategy(db_path=self.db_path)
        analysis = ma_strategy.analyze_current_market()
        
        if 'error' in analysis:
            return {'signal': 'HOLD', 'confidence': 0.0, 'error': analysis['error']}
        
        # Convert to standardized signal
        if analysis.get('current_signal'):
            signal_type = analysis['current_signal']['type']
            if signal_type == 'BUY':
                return {'signal': 'BUY', 'confidence': 0.7}
            elif signal_type == 'SELL':
                return {'signal': 'SELL', 'confidence': 0.7}
        
        # Check trend
        if analysis['trend'] == 'BULLISH':
            return {'signal': 'BUY', 'confidence': 0.4}
        elif analysis['trend'] == 'BEARISH':
            return {'signal': 'SELL', 'confidence': 0.4}
        
        return {'signal': 'HOLD', 'confidence': 0.0}
    
    def get_mean_reversion_signal(self) -> Dict:
        """Mean reversion strategy signal"""
        conn = sqlite3.connect(self.db_path)
        
        # Get recent data
        cutoff_time = (datetime.now() - timedelta(hours=24)).strftime('%Y-%m-%d %H:%M:%S')
        
        df = pd.read_sql_query('''
            SELECT timestamp, price FROM btc_prices 
            WHERE timestamp >= ? 
            ORDER BY timestamp ASC
        ''', conn, params=(cutoff_time,))
        conn.close()
        
        if len(df) < 50:
            return {'signal': 'HOLD', 'confidence': 0.0, 'error': 'Not enough data'}
        
        prices = df['price']
        
        # Calculate Bollinger Bands
        ma = prices.rolling(window=20).mean()
        std = prices.rolling(window=20).std()
        upper_band = ma + (std * 2)
        lower_band = ma - (std * 2)
        
        current_price = prices.iloc[-1]
        current_upper = upper_band.iloc[-1]
        current_lower = lower_band.iloc[-1]
        current_ma = ma.iloc[-1]
        
        # Generate signals
        if not pd.isna(current_upper) and not pd.isna(current_lower):
            if current_price > current_upper:
                # Price above upper band - expect reversion down
                return {'signal': 'SELL', 'confidence': 0.6}
            elif current_price < current_lower:
                # Price below lower band - expect reversion up
                return {'signal': 'BUY', 'confidence': 0.6}
            elif abs(current_price - current_ma) / current_ma < 0.01:
                # Price near middle - low confidence
                return {'signal': 'HOLD', 'confidence': 0.2}
        
        return {'signal': 'HOLD', 'confidence': 0.0}
    
    def update_strategy_performance(self, strategy_name: str, trade_result: Dict):
        """Update performance tracking for dynamic weighting"""
        if strategy_name not in self.strategy_performance:
            return
        
        perf = self.strategy_performance[strategy_name]
        perf['trades'].append(trade_result)
        
        # Keep only last 50 trades
        if len(perf['trades']) > 50:
            perf['trades'] = perf['trades'][-50:]
        
        # Recalculate metrics
        if len(perf['trades']) > 0:
            returns = [t.get('return_pct', 0) for t in perf['trades']]
            perf['win_rate'] = sum(1 for r in returns if r > 0) / len(returns)
            perf['avg_return'] = np.mean(returns)
    
    def adjust_strategy_weights(self):
        """Dynamically adjust strategy weights based on performance"""
        total_score = 0
        scores = {}
        
        for strategy_name, perf in self.strategy_performance.items():
            if len(perf['trades']) >= 5:
                # Score based on win rate and average return
                score = (perf['win_rate'] * 0.6) + (max(0, perf['avg_return'] / 10) * 0.4)
                scores[strategy_name] = max(0.1, score)  # Minimum weight
            else:
                scores[strategy_name] = 0.33  # Default equal weight
            
            total_score += scores[strategy_name]
        
        # Normalize weights
        if total_score > 0:
            for strategy_name in scores:
                self.strategy_weights[strategy_name] = scores[strategy_name] / total_score
    
    def get_ensemble_signal(self) -> Dict:
        """Get weighted ensemble signal from all strategies"""
        # Get market regime first
        regime_info = self.regime_detector.detect_market_regime()
        
        # Adjust weights based on market regime
        regime_weights = self.strategy_weights.copy()
        
        if 'regime' in regime_info:
            if regime_info['regime'] in ['VOLATILE_BULL', 'VOLATILE_BEAR', 'HIGH_VOLATILITY']:
                # Reduce mean reversion in high volatility
                regime_weights['mean_reversion'] *= 0.5
                regime_weights['multi_timeframe'] *= 1.3
            elif regime_info['regime'] == 'SIDEWAYS_MARKET':
                # Favor mean reversion in sideways markets
                regime_weights['mean_reversion'] *= 1.5
                regime_weights['ma_crossover'] *= 0.7
        
        # Normalize weights
        total_weight = sum(regime_weights.values())
        if total_weight > 0:
            for key in regime_weights:
                regime_weights[key] /= total_weight
        
        # Get signals from all strategies
        signals = {}
        
        # MA Crossover
        try:
            signals['ma_crossover'] = self.get_ma_crossover_signal()
        except Exception as e:
            signals['ma_crossover'] = {'signal': 'HOLD', 'confidence': 0.0, 'error': str(e)}
        
        # Multi-timeframe
        try:
            mtf_result = self.mtf_strategy.get_multi_timeframe_signal()
            if 'error' not in mtf_result:
                overall_signal = mtf_result['overall_signal']
                if overall_signal in ['STRONG_BUY', 'BUY']:
                    signals['multi_timeframe'] = {'signal': 'BUY', 'confidence': mtf_result['signal_strength']}
                elif overall_signal in ['STRONG_SELL', 'SELL']:
                    signals['multi_timeframe'] = {'signal': 'SELL', 'confidence': mtf_result['signal_strength']}
                else:
                    signals['multi_timeframe'] = {'signal': 'HOLD', 'confidence': 0.0}
            else:
                signals['multi_timeframe'] = {'signal': 'HOLD', 'confidence': 0.0, 'error': mtf_result['error']}
        except Exception as e:
            signals['multi_timeframe'] = {'signal': 'HOLD', 'confidence': 0.0, 'error': str(e)}
        
        # Mean Reversion
        try:
            signals['mean_reversion'] = self.get_mean_reversion_signal()
        except Exception as e:
            signals['mean_reversion'] = {'signal': 'HOLD', 'confidence': 0.0, 'error': str(e)}
        
        # Calculate weighted ensemble signal
        buy_score = 0
        sell_score = 0
        total_confidence = 0
        
        for strategy_name, signal_data in signals.items():
            if 'error' in signal_data:
                continue
                
            weight = regime_weights.get(strategy_name, 0)
            confidence = signal_data.get('confidence', 0)
            signal = signal_data.get('signal', 'HOLD')
            
            weighted_confidence = weight * confidence
            
            if signal == 'BUY':
                buy_score += weighted_confidence
            elif signal == 'SELL':
                sell_score += weighted_confidence
            
            total_confidence += weighted_confidence
        
        # Determine final signal
        if buy_score > sell_score and buy_score > 0.4:
            final_signal = 'BUY'
            final_confidence = buy_score
        elif sell_score > buy_score and sell_score > 0.4:
            final_signal = 'SELL'
            final_confidence = sell_score
        else:
            final_signal = 'HOLD'
            final_confidence = total_confidence
        
        return {
            'ensemble_signal': final_signal,
            'confidence': final_confidence,
            'buy_score': buy_score,
            'sell_score': sell_score,
            'individual_signals': signals,
            'strategy_weights': regime_weights,
            'market_regime': regime_info,
            'total_strategies': len([s for s in signals.values() if 'error' not in s])
        }