import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import sqlite3
import os

class RSIStrategy:
    def __init__(self, rsi_period=14, oversold_threshold=30, overbought_threshold=70, db_path=None):
        """
        RSI (Relative Strength Index) Strategy
        
        Args:
            rsi_period (int): Period for RSI calculation (default: 14)
            oversold_threshold (float): RSI level considered oversold (default: 30)
            overbought_threshold (float): RSI level considered overbought (default: 70)
            db_path (str): Path to the database
        """
        self.rsi_period = rsi_period
        self.oversold_threshold = oversold_threshold
        self.overbought_threshold = overbought_threshold
        
        # Set up database path
        if db_path is None:
            current_dir = os.path.dirname(os.path.abspath(__file__))
            project_root = os.path.dirname(current_dir)
            db_path = os.path.join(project_root, 'data', 'bitcoin_data.db')
        
        self.db_path = db_path
        self.last_signal = None
        self.position = None  # 'long', 'short', or None
        
    def calculate_rsi(self, data, period=None):
        """Calculate RSI (Relative Strength Index)"""
        if period is None:
            period = self.rsi_period
            
        # Calculate price changes
        delta = data['price'].diff()
        
        # Separate gains and losses
        gain = delta.where(delta > 0, 0)
        loss = -delta.where(delta < 0, 0)
        
        # Calculate average gain and loss using exponential moving average
        avg_gain = gain.ewm(span=period, adjust=False).mean()
        avg_loss = loss.ewm(span=period, adjust=False).mean()
        
        # Calculate RS (Relative Strength)
        rs = avg_gain / avg_loss
        
        # Calculate RSI
        rsi = 100 - (100 / (1 + rs))
        
        data['rsi'] = rsi
        return data
    
    def generate_signals(self, data):
        """Generate buy/sell signals based on RSI"""
        # Calculate RSI
        data = self.calculate_rsi(data)
        
        # Initialize signals
        data['signal'] = 0
        data['signal_type'] = ''
        data['signal_strength'] = 0.0  # How strong the signal is (0-1)
        
        # Generate signals where we have enough data
        if len(data) < self.rsi_period + 1:
            return data
        
        for i in range(self.rsi_period, len(data)):
            current_rsi = data.iloc[i]['rsi']
            prev_rsi = data.iloc[i-1]['rsi']
            
            # Skip if RSI is NaN
            if pd.isna(current_rsi) or pd.isna(prev_rsi):
                continue
            
            # Buy signal: RSI crosses above oversold threshold from below
            if (prev_rsi <= self.oversold_threshold) and (current_rsi > self.oversold_threshold):
                data.iloc[i, data.columns.get_loc('signal')] = 1
                data.iloc[i, data.columns.get_loc('signal_type')] = 'BUY'
                # Signal strength based on how oversold it was
                strength = max(0, (self.oversold_threshold - prev_rsi) / self.oversold_threshold)
                data.iloc[i, data.columns.get_loc('signal_strength')] = min(1.0, strength)
            
            # Sell signal: RSI crosses below overbought threshold from above
            elif (prev_rsi >= self.overbought_threshold) and (current_rsi < self.overbought_threshold):
                data.iloc[i, data.columns.get_loc('signal')] = -1
                data.iloc[i, data.columns.get_loc('signal_type')] = 'SELL'
                # Signal strength based on how overbought it was
                strength = max(0, (prev_rsi - self.overbought_threshold) / (100 - self.overbought_threshold))
                data.iloc[i, data.columns.get_loc('signal_strength')] = min(1.0, strength)
        
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
        
        if data is None or len(data) < self.rsi_period:
            return {
                'error': f'Not enough data. Need at least {self.rsi_period} data points.',
                'data_points': len(data) if data is not None else 0
            }
        
        # Generate signals
        data_with_signals = self.generate_signals(data)
        
        # Get latest values
        latest = data_with_signals.iloc[-1]
        
        # Check if we have a recent signal (within last 3 data points)
        recent_signals = data_with_signals[data_with_signals['signal'] != 0].tail(1)
        
        current_signal = None
        if len(recent_signals) > 0:
            signal_row = recent_signals.iloc[-1]
            current_signal = {
                'type': signal_row['signal_type'],
                'timestamp': signal_row.name.strftime('%Y-%m-%d %H:%M:%S'),
                'price': signal_row['price'],
                'rsi': signal_row['rsi'],
                'strength': signal_row['signal_strength']
            }
        
        # Determine market condition based on RSI
        current_rsi = latest['rsi']
        if current_rsi > self.overbought_threshold:
            condition = 'OVERBOUGHT'
        elif current_rsi < self.oversold_threshold:
            condition = 'OVERSOLD'
        else:
            condition = 'NEUTRAL'
        
        return {
            'current_price': latest['price'],
            'current_rsi': current_rsi,
            'market_condition': condition,
            'oversold_threshold': self.oversold_threshold,
            'overbought_threshold': self.overbought_threshold,
            'current_signal': current_signal,
            'data_points': len(data_with_signals),
            'strategy': f'RSI({self.rsi_period})'
        }
    
    def backtest(self, hours=168):  # 1 week default
        """Run backtest on historical data"""
        data = self.get_historical_data(hours=hours)
        
        if data is None or len(data) < self.rsi_period:
            return {
                'error': f'Not enough data for backtesting. Need at least {self.rsi_period} data points.'
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
                    # Use signal strength to determine position size (50% to 100% of available balance)
                    position_size = 0.5 + (0.5 * row['signal_strength'])
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
                        'rsi': row['rsi'],
                        'signal_strength': row['signal_strength']
                    })
            
            elif row['signal'] == -1:  # Sell signal
                if bitcoin_held > 0:  # Only sell if we have position
                    # Use signal strength to determine how much to sell
                    sell_ratio = 0.5 + (0.5 * row['signal_strength'])
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
                        'rsi': row['rsi'],
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
        
        # Calculate average RSI at buy/sell points
        buy_rsi_avg = np.mean([t['rsi'] for t in trades if t['type'] == 'BUY']) if trades else 0
        sell_rsi_avg = np.mean([t['rsi'] for t in trades if t['type'] == 'SELL']) if trades else 0
        
        return {
            'initial_balance': initial_balance,
            'final_value': final_value,
            'total_return_percent': total_return,
            'total_trades': len(trades),
            'completed_trades': total_completed_trades,
            'win_rate_percent': win_rate,
            'avg_buy_rsi': buy_rsi_avg,
            'avg_sell_rsi': sell_rsi_avg,
            'trades': trades[-10:],  # Last 10 trades
            'period_hours': hours,
            'strategy': f'RSI({self.rsi_period})',
            'thresholds': {
                'oversold': self.oversold_threshold,
                'overbought': self.overbought_threshold
            }
        }
    
    def get_strategy_data_for_chart(self, hours=24):
        """Get strategy data formatted for charting"""
        data = self.get_historical_data(hours=hours)
        
        if data is None or len(data) < self.rsi_period:
            return None
        
        data_with_signals = self.generate_signals(data)
        
        # Format for chart
        chart_data = []
        for i, row in data_with_signals.iterrows():
            chart_data.append({
                'timestamp': i.strftime('%Y-%m-%d %H:%M:%S'),
                'price': row['price'],
                'rsi': row['rsi'] if not pd.isna(row['rsi']) else None,
                'signal': row['signal'],
                'signal_type': row['signal_type'],
                'signal_strength': row['signal_strength']
            })
        
        return chart_data
    
    def get_rsi_signals_summary(self, hours=24):
        """Get a summary of recent RSI signals"""
        data = self.get_historical_data(hours=hours)
        
        if data is None or len(data) < self.rsi_period:
            return None
        
        data_with_signals = self.generate_signals(data)
        
        # Get all signals
        signals = data_with_signals[data_with_signals['signal'] != 0]
        
        summary = {
            'total_signals': len(signals),
            'buy_signals': len(signals[signals['signal'] == 1]),
            'sell_signals': len(signals[signals['signal'] == -1]),
            'avg_signal_strength': signals['signal_strength'].mean() if len(signals) > 0 else 0,
            'recent_signals': []
        }
        
        # Get last 5 signals
        for _, signal in signals.tail(5).iterrows():
            summary['recent_signals'].append({
                'type': signal['signal_type'],
                'timestamp': signal.name.strftime('%Y-%m-%d %H:%M:%S'),
                'price': signal['price'],
                'rsi': signal['rsi'],
                'strength': signal['signal_strength']
            })
        
        return summary


def test_rsi_strategy():
    """Test the RSI strategy with current data"""
    print("🚀 Testing RSI Strategy")
    print("=" * 50)
    
    # Initialize strategy
    strategy = RSIStrategy(rsi_period=14, oversold_threshold=30, overbought_threshold=70)
    
    # Check how much data we have
    data = strategy.get_historical_data(hours=24)
    if data is not None:
        print(f"📊 Available data points: {len(data)}")
        print(f"   Strategy needs: {strategy.rsi_period} minimum")
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
    print(f"   Current RSI: {analysis['current_rsi']:.1f}")
    print(f"   Market Condition: {analysis['market_condition']}")
    print(f"   Strategy: {analysis['strategy']}")
    print(f"   Thresholds: Oversold < {analysis['oversold_threshold']}, Overbought > {analysis['overbought_threshold']}")
    
    if analysis['current_signal']:
        signal = analysis['current_signal']
        print(f"\n🚨 ACTIVE SIGNAL:")
        print(f"   Type: {signal['type']}")
        print(f"   Price: ${signal['price']:,.2f}")
        print(f"   RSI: {signal['rsi']:.1f}")
        print(f"   Strength: {signal['strength']:.2f}")
        print(f"   Time: {signal['timestamp']}")
    else:
        print(f"\n⏳ No recent signals")
    
    # Get signals summary
    signals_summary = strategy.get_rsi_signals_summary(hours=24)
    if signals_summary:
        print(f"\n📈 24h Signals Summary:")
        print(f"   Total Signals: {signals_summary['total_signals']}")
        print(f"   Buy Signals: {signals_summary['buy_signals']}")
        print(f"   Sell Signals: {signals_summary['sell_signals']}")
        print(f"   Avg Strength: {signals_summary['avg_signal_strength']:.2f}")
    
    # Run backtest only if we have enough data
    if analysis.get('data_points', 0) >= strategy.rsi_period:
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
            print(f"   Avg Buy RSI: {backtest_results['avg_buy_rsi']:.1f}")
            print(f"   Avg Sell RSI: {backtest_results['avg_sell_rsi']:.1f}")
            
            if backtest_results['trades']:
                print(f"\n📋 Recent Trades:")
                for trade in backtest_results['trades'][-3:]:
                    print(f"   {trade['type']}: ${trade['price']:,.2f} (RSI: {trade['rsi']:.1f}, Strength: {trade['signal_strength']:.2f}) at {trade['timestamp']}")
    else:
        print(f"\n📈 Not enough data for backtesting yet")
        print(f"   Need {strategy.rsi_period} points, have {analysis.get('data_points', 0)}")
        print(f"   💡 Generate sample data: python scripts/generate_sample_data.py")


if __name__ == "__main__":
    test_rsi_strategy()