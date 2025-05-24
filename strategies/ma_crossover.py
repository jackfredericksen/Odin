import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import sqlite3
import os

class MovingAverageCrossoverStrategy:
    def __init__(self, short_window=5, long_window=20, db_path=None):
        """
        Moving Average Crossover Strategy
        
        Args:
            short_window (int): Period for short-term moving average (default: 5)
            long_window (int): Period for long-term moving average (default: 20)
            db_path (str): Path to the database
        """
        self.short_window = short_window
        self.long_window = long_window
        
        # Set up database path
        if db_path is None:
            current_dir = os.path.dirname(os.path.abspath(__file__))
            project_root = os.path.dirname(current_dir)
            db_path = os.path.join(project_root, 'data', 'bitcoin_data.db')
        
        self.db_path = db_path
        self.last_signal = None
        self.position = None  # 'long', 'short', or None
        
    def calculate_moving_averages(self, data):
        """Calculate short and long moving averages"""
        data['ma_short'] = data['price'].rolling(window=self.short_window).mean()
        data['ma_long'] = data['price'].rolling(window=self.long_window).mean()
        return data
    
    def generate_signals(self, data):
        """Generate buy/sell signals based on MA crossover"""
        # Calculate moving averages
        data = self.calculate_moving_averages(data)
        
        # Initialize signals
        data['signal'] = 0
        data['signal_type'] = ''
        
        # Generate signals where we have enough data
        # Use iloc for integer-based indexing instead of index arithmetic
        if len(data) < self.long_window + 1:
            return data
        
        for i in range(self.long_window, len(data)):
            current_short = data.iloc[i]['ma_short']
            current_long = data.iloc[i]['ma_long']
            prev_short = data.iloc[i-1]['ma_short']
            prev_long = data.iloc[i-1]['ma_long']
            
            # Skip if any values are NaN
            if pd.isna(current_short) or pd.isna(current_long) or pd.isna(prev_short) or pd.isna(prev_long):
                continue
            
            # Buy signal: short MA crosses above long MA
            if (prev_short <= prev_long) and (current_short > current_long):
                data.iloc[i, data.columns.get_loc('signal')] = 1
                data.iloc[i, data.columns.get_loc('signal_type')] = 'BUY'
            
            # Sell signal: short MA crosses below long MA
            elif (prev_short >= prev_long) and (current_short < current_long):
                data.iloc[i, data.columns.get_loc('signal')] = -1
                data.iloc[i, data.columns.get_loc('signal_type')] = 'SELL'
        
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
        
        if data is None or len(data) < self.long_window:
            return {
                'error': f'Not enough data. Need at least {self.long_window} data points.',
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
                'ma_short': signal_row['ma_short'],
                'ma_long': signal_row['ma_long']
            }
        
        return {
            'current_price': latest['price'],
            'ma_short': latest['ma_short'],
            'ma_long': latest['ma_long'],
            'trend': 'BULLISH' if latest['ma_short'] > latest['ma_long'] else 'BEARISH',
            'current_signal': current_signal,
            'data_points': len(data_with_signals),
            'strategy': f'MA({self.short_window},{self.long_window})'
        }
    
    def backtest(self, hours=168):  # 1 week default
        """Run backtest on historical data"""
        data = self.get_historical_data(hours=hours)
        
        if data is None or len(data) < self.long_window:
            return {
                'error': f'Not enough data for backtesting. Need at least {self.long_window} data points.'
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
                    bitcoin_to_buy = balance / row['price']
                    bitcoin_held = bitcoin_to_buy
                    balance = 0
                    trades.append({
                        'type': 'BUY',
                        'timestamp': idx.strftime('%Y-%m-%d %H:%M:%S'),
                        'price': row['price'],
                        'amount': bitcoin_to_buy,
                        'value': bitcoin_to_buy * row['price']
                    })
            
            elif row['signal'] == -1:  # Sell signal
                if bitcoin_held > 0:  # Only sell if we have position
                    balance = bitcoin_held * row['price']
                    trades.append({
                        'type': 'SELL',
                        'timestamp': idx.strftime('%Y-%m-%d %H:%M:%S'),
                        'price': row['price'],
                        'amount': bitcoin_held,
                        'value': balance
                    })
                    bitcoin_held = 0
        
        # Calculate final portfolio value
        final_price = data_with_signals.iloc[-1]['price']
        final_value = balance + (bitcoin_held * final_price)
        
        # Calculate performance metrics
        total_return = ((final_value - initial_balance) / initial_balance) * 100
        
        # Calculate win rate
        profitable_trades = 0
        total_completed_trades = 0
        
        for i in range(1, len(trades), 2):  # Pairs of buy/sell
            if i < len(trades):
                buy_price = trades[i-1]['price']
                sell_price = trades[i]['price']
                if sell_price > buy_price:
                    profitable_trades += 1
                total_completed_trades += 1
        
        win_rate = (profitable_trades / total_completed_trades * 100) if total_completed_trades > 0 else 0
        
        return {
            'initial_balance': initial_balance,
            'final_value': final_value,
            'total_return_percent': total_return,
            'total_trades': len(trades),
            'completed_trades': total_completed_trades,
            'win_rate_percent': win_rate,
            'trades': trades[-10:],  # Last 10 trades
            'period_hours': hours,
            'strategy': f'MA({self.short_window},{self.long_window})'
        }
    
    def get_strategy_data_for_chart(self, hours=24):
        """Get strategy data formatted for charting"""
        data = self.get_historical_data(hours=hours)
        
        if data is None or len(data) < self.long_window:
            return None
        
        data_with_signals = self.generate_signals(data)
        
        # Format for chart
        chart_data = []
        for i, row in data_with_signals.iterrows():
            chart_data.append({
                'timestamp': i.strftime('%Y-%m-%d %H:%M:%S'),
                'price': row['price'],
                'ma_short': row['ma_short'] if not pd.isna(row['ma_short']) else None,
                'ma_long': row['ma_long'] if not pd.isna(row['ma_long']) else None,
                'signal': row['signal'],
                'signal_type': row['signal_type']
            })
        
        return chart_data


def test_strategy():
    """Test the strategy with current data"""
    print("🚀 Testing Moving Average Crossover Strategy")
    print("=" * 50)
    
    # Initialize strategy with traditional MA values
    strategy = MovingAverageCrossoverStrategy(short_window=5, long_window=20)
    
    # Check how much data we have
    data = strategy.get_historical_data(hours=24)
    if data is not None:
        print(f"📊 Available data points: {len(data)}")
        print(f"   Strategy needs: {strategy.long_window} minimum")
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
        print(f"   💡 Tip: Generate sample data with: python scripts/generate_sample_data.py")
        return
    
    print(f"   Current Price: ${analysis['current_price']:,.2f}")
    print(f"   Short MA (5): ${analysis['ma_short']:,.2f}")
    print(f"   Long MA (20): ${analysis['ma_long']:,.2f}")
    print(f"   Trend: {analysis['trend']}")
    print(f"   Strategy: {analysis['strategy']}")
    
    if analysis['current_signal']:
        signal = analysis['current_signal']
        print(f"\n🚨 ACTIVE SIGNAL:")
        print(f"   Type: {signal['type']}")
        print(f"   Price: ${signal['price']:,.2f}")
        print(f"   Time: {signal['timestamp']}")
    else:
        print(f"\n⏳ No recent signals")
    
    # Run backtest only if we have enough data
    if analysis.get('data_points', 0) >= strategy.long_window:
        print(f"\n📈 Backtesting (Available data):")
        backtest_results = strategy.backtest(hours=24)  # Just use available data
        
        if 'error' in backtest_results:
            print(f"❌ {backtest_results['error']}")
        else:
            print(f"   Strategy: {backtest_results['strategy']}")
            print(f"   Initial Balance: ${backtest_results['initial_balance']:,.2f}")
            print(f"   Final Value: ${backtest_results['final_value']:,.2f}")
            print(f"   Total Return: {backtest_results['total_return_percent']:+.2f}%")
            print(f"   Total Trades: {backtest_results['total_trades']}")
            print(f"   Win Rate: {backtest_results['win_rate_percent']:.1f}%")
            
            if backtest_results['trades']:
                print(f"\n📋 Recent Trades:")
                for trade in backtest_results['trades'][-3:]:
                    print(f"   {trade['type']}: ${trade['price']:,.2f} at {trade['timestamp']}")
    else:
        print(f"\n📈 Not enough data for backtesting yet")
        print(f"   Need {strategy.long_window} points, have {analysis.get('data_points', 0)}")
        print(f"   💡 Generate sample data: python scripts/generate_sample_data.py")

if __name__ == "__main__":
    test_strategy()