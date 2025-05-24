import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import sqlite3
import os

class MACDStrategy:
    def __init__(self, fast_period=12, slow_period=26, signal_period=9, db_path=None):
        """
        MACD (Moving Average Convergence Divergence) Strategy
        
        Args:
            fast_period (int): Fast EMA period (default: 12)
            slow_period (int): Slow EMA period (default: 26)
            signal_period (int): Signal line EMA period (default: 9)
            db_path (str): Path to the database
        """
        self.fast_period = fast_period
        self.slow_period = slow_period
        self.signal_period = signal_period
        
        # Set up database path
        if db_path is None:
            current_dir = os.path.dirname(os.path.abspath(__file__))
            project_root = os.path.dirname(current_dir)
            db_path = os.path.join(project_root, 'data', 'bitcoin_data.db')
        
        self.db_path = db_path
        self.last_signal = None
        self.position = None  # 'long', 'short', or None
        
    def calculate_macd(self, data):
        """Calculate MACD indicators"""
        # Calculate EMAs
        data['ema_fast'] = data['price'].ewm(span=self.fast_period).mean()
        data['ema_slow'] = data['price'].ewm(span=self.slow_period).mean()
        
        # Calculate MACD line (fast EMA - slow EMA)
        data['macd_line'] = data['ema_fast'] - data['ema_slow']
        
        # Calculate Signal line (EMA of MACD line)
        data['macd_signal'] = data['macd_line'].ewm(span=self.signal_period).mean()
        
        # Calculate MACD Histogram (MACD line - Signal line)
        data['macd_histogram'] = data['macd_line'] - data['macd_signal']
        
        # Calculate momentum indicators
        data['macd_momentum'] = data['macd_histogram'].diff()  # Rate of change of histogram
        data['macd_divergence'] = data['macd_line'] - data['macd_line'].shift(1)  # MACD line momentum
        
        return data
    
    def generate_signals(self, data):
        """Generate buy/sell signals based on MACD"""
        # Calculate MACD
        data = self.calculate_macd(data)
        
        # Initialize signals
        data['signal'] = 0
        data['signal_type'] = ''
        data['signal_strength'] = 0.0
        
        # Generate signals where we have enough data
        min_periods = max(self.slow_period, self.signal_period) + 1
        if len(data) < min_periods:
            return data
        
        for i in range(min_periods, len(data)):
            current_macd = data.iloc[i]['macd_line']
            current_signal = data.iloc[i]['macd_signal']
            current_histogram = data.iloc[i]['macd_histogram']
            
            prev_macd = data.iloc[i-1]['macd_line']
            prev_signal = data.iloc[i-1]['macd_signal']
            prev_histogram = data.iloc[i-1]['macd_histogram']
            
            momentum = data.iloc[i]['macd_momentum']
            
            # Skip if any values are NaN
            if pd.isna(current_macd) or pd.isna(current_signal) or pd.isna(prev_macd) or pd.isna(prev_signal):
                continue
            
            # Primary signal: MACD line crosses above signal line (bullish crossover)
            if (prev_macd <= prev_signal) and (current_macd > current_signal):
                data.iloc[i, data.columns.get_loc('signal')] = 1
                data.iloc[i, data.columns.get_loc('signal_type')] = 'BUY'
                
                # Signal strength based on histogram strength and momentum
                histogram_strength = abs(current_histogram) / abs(current_macd) if current_macd != 0 else 0
                momentum_strength = max(0, momentum) / abs(current_macd) if current_macd != 0 else 0
                strength = min(1.0, (histogram_strength + momentum_strength) / 2)
                data.iloc[i, data.columns.get_loc('signal_strength')] = strength
            
            # Primary signal: MACD line crosses below signal line (bearish crossover)
            elif (prev_macd >= prev_signal) and (current_macd < current_signal):
                data.iloc[i, data.columns.get_loc('signal')] = -1
                data.iloc[i, data.columns.get_loc('signal_type')] = 'SELL'
                
                # Signal strength based on histogram strength and momentum
                histogram_strength = abs(current_histogram) / abs(current_macd) if current_macd != 0 else 0
                momentum_strength = abs(min(0, momentum)) / abs(current_macd) if current_macd != 0 else 0
                strength = min(1.0, (histogram_strength + momentum_strength) / 2)
                data.iloc[i, data.columns.get_loc('signal_strength')] = strength
            
            # Secondary signals: Zero line crossovers (stronger signals)
            # MACD crosses above zero line (bullish)
            elif (prev_macd <= 0) and (current_macd > 0):
                data.iloc[i, data.columns.get_loc('signal')] = 1
                data.iloc[i, data.columns.get_loc('signal_type')] = 'BUY'
                data.iloc[i, data.columns.get_loc('signal_strength')] = 0.8  # Strong signal
            
            # MACD crosses below zero line (bearish)
            elif (prev_macd >= 0) and (current_macd < 0):
                data.iloc[i, data.columns.get_loc('signal')] = -1
                data.iloc[i, data.columns.get_loc('signal_type')] = 'SELL'
                data.iloc[i, data.columns.get_loc('signal_strength')] = 0.8  # Strong signal
            
            # Histogram reversal signals (early momentum change detection)
            # Histogram turns positive (bullish momentum)
            elif (prev_histogram <= 0) and (current_histogram > 0) and current_macd < 0:
                data.iloc[i, data.columns.get_loc('signal')] = 1
                data.iloc[i, data.columns.get_loc('signal_type')] = 'BUY'
                data.iloc[i, data.columns.get_loc('signal_strength')] = 0.6  # Medium signal
            
            # Histogram turns negative (bearish momentum)
            elif (prev_histogram >= 0) and (current_histogram < 0) and current_macd > 0:
                data.iloc[i, data.columns.get_loc('signal')] = -1
                data.iloc[i, data.columns.get_loc('signal_type')] = 'SELL'
                data.iloc[i, data.columns.get_loc('signal_strength')] = 0.6  # Medium signal
        
        return data
    
    def get_historical_data(self, hours=48):
        """Get historical price data from database"""
        try:
            conn = sqlite3.connect(self.db_path)
            
            # Get data from the last N hours
            cutoff_time = (datetime.now() - timedelta(hours=hours)).strftime('%Y-%m-%d %H:%M:%S')
            
            query = '''
                SELECT timestamp, price FROM btc_prices 
                WHERE timestamp >= ? 
                ORDER BY timestamp ASC
            '''
            
            df = pd.read_sql_query(query, conn, params=(cutoff_time,))
            conn.close()
            
            if len(df) == 0:
                return None
            
            # Convert timestamp to datetime
            df['timestamp'] = pd.to_datetime(df['timestamp'])
            df.set_index('timestamp', inplace=True)
            
            return df
            
        except Exception as e:
            print(f"Error getting historical data: {e}")
            return None
    
    def analyze_current_market(self):
        """Analyze current market conditions and generate signals"""
        # Get recent data
        data = self.get_historical_data(hours=24)
        
        min_periods = max(self.slow_period, self.signal_period)
        if data is None or len(data) < min_periods:
            return {
                'error': f'Not enough data. Need at least {min_periods} data points.',
                'data_points': len(data) if data is not None else 0
            }
        
        # Generate signals
        data_with_signals = self.calculate_macd(data)
        
        # Get latest values
        latest = data_with_signals.iloc[-1]
        
        # Check if we have a recent signal (within last 3 data points)
        signals_data = self.generate_signals(data_with_signals.copy())
        recent_signals = signals_data[signals_data['signal'] != 0].tail(1)
        
        current_signal = None
        if len(recent_signals) > 0:
            signal_row = recent_signals.iloc[-1]
            current_signal = {
                'type': signal_row['signal_type'],
                'timestamp': signal_row.name.strftime('%Y-%m-%d %H:%M:%S'),
                'price': signal_row['price'],
                'macd_line': signal_row['macd_line'],
                'macd_signal': signal_row['macd_signal'],
                'macd_histogram': signal_row['macd_histogram'],
                'strength': signal_row['signal_strength']
            }
        
        # Determine market condition based on MACD position
        macd_line = latest['macd_line']
        macd_signal = latest['macd_signal']
        histogram = latest['macd_histogram']
        
        if macd_line > 0 and macd_line > macd_signal:
            condition = 'BULLISH'
        elif macd_line < 0 and macd_line < macd_signal:
            condition = 'BEARISH'
        else:
            condition = 'NEUTRAL'
        
        # Momentum condition based on histogram
        if histogram > 0:
            momentum = 'POSITIVE'
        elif histogram < 0:
            momentum = 'NEGATIVE'
        else:
            momentum = 'NEUTRAL'
        
        return {
            'current_price': latest['price'],
            'macd_line': macd_line,
            'macd_signal': macd_signal,
            'macd_histogram': histogram,
            'market_condition': condition,
            'momentum': momentum,
            'current_signal': current_signal,
            'data_points': len(data_with_signals),
            'strategy': f'MACD({self.fast_period},{self.slow_period},{self.signal_period})'
        }
    
    def backtest(self, hours=168):  # 1 week default
        """Run backtest on historical data"""
        data = self.get_historical_data(hours=hours)
        
        min_periods = max(self.slow_period, self.signal_period)
        if data is None or len(data) < min_periods:
            return {
                'error': f'Not enough data for backtesting. Need at least {min_periods} data points.'
            }
        
        # Generate signals
        data_with_signals = self.generate_signals(data)
        
        # Simulate trading
        initial_balance = 10000  # $10,000 starting balance
        balance = initial_balance
        bitcoin_held = 0
        trades = []
        
        # Use iterrows for safe iteration
        for idx, row in data_with_signals.iterrows():
            if row['signal'] == 1:  # Buy signal
                if bitcoin_held == 0:  # Only buy if we don't have position
                    # Use signal strength to determine position size (30% to 80% of available balance)
                    position_size = 0.3 + (0.5 * row['signal_strength'])
                    investment = balance * position_size
                    bitcoin_to_buy = investment / row['price']
                    bitcoin_held = bitcoin_to_buy
                    balance -= investment
                    
                    trades.append({
                        'type': 'BUY',
                        'timestamp': idx.strftime('%Y-%m-%d %H:%M:%S'),
                        'price': row['price'],
                        'amount': bitcoin_to_buy,
                        'value': investment,
                        'macd_line': row['macd_line'],
                        'macd_histogram': row['macd_histogram'],
                        'signal_strength': row['signal_strength']
                    })
            
            elif row['signal'] == -1:  # Sell signal
                if bitcoin_held > 0:  # Only sell if we have position
                    # Use signal strength to determine how much to sell
                    sell_ratio = 0.3 + (0.5 * row['signal_strength'])
                    bitcoin_to_sell = bitcoin_held * sell_ratio
                    sale_value = bitcoin_to_sell * row['price']
                    balance += sale_value
                    bitcoin_held -= bitcoin_to_sell
                    
                    trades.append({
                        'type': 'SELL',
                        'timestamp': idx.strftime('%Y-%m-%d %H:%M:%S'),
                        'price': row['price'],
                        'amount': bitcoin_to_sell,
                        'value': sale_value,
                        'macd_line': row['macd_line'],
                        'macd_histogram': row['macd_histogram'],
                        'signal_strength': row['signal_strength']
                    })
        
        # Calculate final portfolio value
        final_price = data_with_signals.iloc[-1]['price']
        final_value = balance + (bitcoin_held * final_price)
        
        # Calculate performance metrics
        total_return = ((final_value - initial_balance) / initial_balance) * 100
        
        # Calculate win rate
        profitable_trades = 0
        total_completed_trades = 0
        
        # Match buy/sell pairs
        buy_trades = [t for t in trades if t['type'] == 'BUY']
        sell_trades = [t for t in trades if t['type'] == 'SELL']
        
        for i, buy_trade in enumerate(buy_trades):
            if i < len(sell_trades):
                sell_trade = sell_trades[i]
                if sell_trade['price'] > buy_trade['price']:
                    profitable_trades += 1
                total_completed_trades += 1
        
        win_rate = (profitable_trades / total_completed_trades * 100) if total_completed_trades > 0 else 0
        
        # Calculate average MACD values at trade points
        buy_macd_avg = np.mean([t['macd_line'] for t in trades if t['type'] == 'BUY']) if trades else 0
        sell_macd_avg = np.mean([t['macd_line'] for t in trades if t['type'] == 'SELL']) if trades else 0
        
        return {
            'initial_balance': initial_balance,
            'final_value': final_value,
            'total_return_percent': total_return,
            'total_trades': len(trades),
            'completed_trades': total_completed_trades,
            'win_rate_percent': win_rate,
            'avg_buy_macd': buy_macd_avg,
            'avg_sell_macd': sell_macd_avg,
            'trades': trades[-10:],  # Last 10 trades
            'period_hours': hours,
            'strategy': f'MACD({self.fast_period},{self.slow_period},{self.signal_period})',
            'parameters': {
                'fast_period': self.fast_period,
                'slow_period': self.slow_period,
                'signal_period': self.signal_period
            }
        }
    
    def get_strategy_data_for_chart(self, hours=24):
        """Get strategy data formatted for charting"""
        data = self.get_historical_data(hours=hours)
        
        min_periods = max(self.slow_period, self.signal_period)
        if data is None or len(data) < min_periods:
            return None
        
        data_with_signals = self.generate_signals(data)
        
        # Format for chart
        chart_data = []
        for i, row in data_with_signals.iterrows():
            chart_data.append({
                'timestamp': i.strftime('%Y-%m-%d %H:%M:%S'),
                'price': row['price'],
                'macd_line': row['macd_line'] if not pd.isna(row['macd_line']) else None,
                'macd_signal': row['macd_signal'] if not pd.isna(row['macd_signal']) else None,
                'macd_histogram': row['macd_histogram'] if not pd.isna(row['macd_histogram']) else None,
                'signal': row['signal'],
                'signal_type': row['signal_type'],
                'signal_strength': row['signal_strength']
            })
        
        return chart_data


def test_macd_strategy():
    """Test the MACD strategy with current data"""
    print("🚀 Testing MACD Strategy")
    print("=" * 50)
    
    # Initialize strategy
    strategy = MACDStrategy(fast_period=12, slow_period=26, signal_period=9)
    
    # Check how much data we have
    data = strategy.get_historical_data(hours=24)
    min_periods = max(strategy.slow_period, strategy.signal_period)
    
    if data is not None:
        print(f"📊 Available data points: {len(data)}")
        print(f"   Strategy needs: {min_periods} minimum")
        print(f"   Data range: {data.index[0]} to {data.index[-1]}")
    else:
        print("❌ No data available in database")
        print("   Make sure your API server has been collecting data")
        return
    
    # Analyze current market
    print(f"\n📊 Current Market Analysis:")
    analysis = strategy.analyze_current_market()
    
    if 'error' in analysis:
        print(f"❌ {analysis['error']}")
        print(f"   Data points available: {analysis.get('data_points', 0)}")
        print(f"   💡 Generate sample data: python scripts/generate_sample_data.py")
        return
    
    print(f"   Current Price: ${analysis['current_price']:,.2f}")
    print(f"   MACD Line: {analysis['macd_line']:.4f}")
    print(f"   Signal Line: {analysis['macd_signal']:.4f}")
    print(f"   Histogram: {analysis['macd_histogram']:.4f}")
    print(f"   Market Condition: {analysis['market_condition']}")
    print(f"   Momentum: {analysis['momentum']}")
    print(f"   Strategy: {analysis['strategy']}")
    
    if analysis['current_signal']:
        signal = analysis['current_signal']
        print(f"\n🚨 ACTIVE SIGNAL:")
        print(f"   Type: {signal['type']}")
        print(f"   Price: ${signal['price']:,.2f}")
        print(f"   MACD: {signal['macd_line']:.4f}")
        print(f"   Signal: {signal['macd_signal']:.4f}")
        print(f"   Histogram: {signal['macd_histogram']:.4f}")
        print(f"   Strength: {signal['strength']:.2f}")
        print(f"   Time: {signal['timestamp']}")
    else:
        print(f"\n⏳ No recent signals")
    
    # Run backtest only if we have enough data
    if analysis.get('data_points', 0) >= min_periods:
        print(f"\n📈 Backtesting (Available data):")
        backtest_results = strategy.backtest(hours=48)  # 2 days of data
        
        if 'error' in backtest_results:
            print(f"❌ {backtest_results['error']}")
        else:
            print(f"   Strategy: {backtest_results['strategy']}")
            print(f"   Initial Balance: ${backtest_results['initial_balance']:,.2f}")
            print(f"   Final Value: ${backtest_results['final_value']:,.2f}")
            print(f"   Total Return: {backtest_results['total_return_percent']:+.2f}%")
            print(f"   Total Trades: {backtest_results['total_trades']}")
            print(f"   Win Rate: {backtest_results['win_rate_percent']:.1f}%")
            print(f"   Avg Buy MACD: {backtest_results['avg_buy_macd']:.4f}")
            print(f"   Avg Sell MACD: {backtest_results['avg_sell_macd']:.4f}")
            
            if backtest_results['trades']:
                print(f"\n📋 Recent Trades:")
                for trade in backtest_results['trades'][-3:]:
                    print(f"   {trade['type']}: ${trade['price']:,.2f} (MACD: {trade['macd_line']:.4f}, Strength: {trade['signal_strength']:.2f}) at {trade['timestamp']}")
    else:
        print(f"\n📈 Not enough data for backtesting yet")
        print(f"   Need {min_periods} points, have {analysis.get('data_points', 0)}")
        print(f"   💡 Generate sample data: python scripts/generate_sample_data.py")


if __name__ == "__main__":
    test_macd_strategy()