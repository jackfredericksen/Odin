import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import sqlite3
import os

class BollingerBandsStrategy:
    def __init__(self, period=20, std_dev=2, db_path=None):
        """
        Bollinger Bands Strategy
        
        Args:
            period (int): Period for moving average and standard deviation (default: 20)
            std_dev (float): Number of standard deviations for bands (default: 2)
            db_path (str): Path to the database
        """
        self.period = period
        self.std_dev = std_dev
        
        # Set up database path
        if db_path is None:
            current_dir = os.path.dirname(os.path.abspath(__file__))
            project_root = os.path.dirname(current_dir)
            db_path = os.path.join(project_root, 'data', 'bitcoin_data.db')
        
        self.db_path = db_path
        self.last_signal = None
        self.position = None  # 'long', 'short', or None
        
    def calculate_bollinger_bands(self, data):
        """Calculate Bollinger Bands"""
        # Calculate moving average (middle band)
        data['bb_middle'] = data['price'].rolling(window=self.period).mean()
        
        # Calculate standard deviation
        data['bb_std'] = data['price'].rolling(window=self.period).std()
        
        # Calculate upper and lower bands
        data['bb_upper'] = data['bb_middle'] + (data['bb_std'] * self.std_dev)
        data['bb_lower'] = data['bb_middle'] - (data['bb_std'] * self.std_dev)
        
        # Calculate %B (where price is within the bands)
        # %B = (Price - Lower Band) / (Upper Band - Lower Band)
        data['bb_percent'] = (data['price'] - data['bb_lower']) / (data['bb_upper'] - data['bb_lower'])
        
        # Calculate Bandwidth (volatility measure)
        data['bb_bandwidth'] = (data['bb_upper'] - data['bb_lower']) / data['bb_middle']
        
        return data
    
    def generate_signals(self, data):
        """Generate buy/sell signals based on Bollinger Bands"""
        # Calculate Bollinger Bands
        data = self.calculate_bollinger_bands(data)
        
        # Initialize signals
        data['signal'] = 0
        data['signal_type'] = ''
        data['signal_strength'] = 0.0
        
        # Generate signals where we have enough data
        if len(data) < self.period + 1:
            return data
        
        for i in range(self.period, len(data)):
            current_price = data.iloc[i]['price']
            prev_price = data.iloc[i-1]['price']
            
            upper_band = data.iloc[i]['bb_upper']
            lower_band = data.iloc[i]['bb_lower']
            middle_band = data.iloc[i]['bb_middle']
            
            prev_upper = data.iloc[i-1]['bb_upper']
            prev_lower = data.iloc[i-1]['bb_lower']
            
            bb_percent = data.iloc[i]['bb_percent']
            bandwidth = data.iloc[i]['bb_bandwidth']
            
            # Skip if any values are NaN
            if pd.isna(upper_band) or pd.isna(lower_band) or pd.isna(bb_percent):
                continue
            
            # Buy signal: Price touches or goes below lower band
            if (prev_price >= prev_lower) and (current_price <= lower_band):
                data.iloc[i, data.columns.get_loc('signal')] = 1
                data.iloc[i, data.columns.get_loc('signal_type')] = 'BUY'
                # Signal strength based on how far below lower band
                strength = max(0, min(1, (lower_band - current_price) / (middle_band * 0.02)))
                data.iloc[i, data.columns.get_loc('signal_strength')] = strength
            
            # Sell signal: Price touches or goes above upper band
            elif (prev_price <= prev_upper) and (current_price >= upper_band):
                data.iloc[i, data.columns.get_loc('signal')] = -1
                data.iloc[i, data.columns.get_loc('signal_type')] = 'SELL'
                # Signal strength based on how far above upper band
                strength = max(0, min(1, (current_price - upper_band) / (middle_band * 0.02)))
                data.iloc[i, data.columns.get_loc('signal_strength')] = strength
            
            # Mean reversion signals (additional)
            # Strong buy when %B < 0 (price below lower band)
            elif bb_percent < 0:
                data.iloc[i, data.columns.get_loc('signal')] = 1
                data.iloc[i, data.columns.get_loc('signal_type')] = 'BUY'
                data.iloc[i, data.columns.get_loc('signal_strength')] = min(1, abs(bb_percent))
            
            # Strong sell when %B > 1 (price above upper band)
            elif bb_percent > 1:
                data.iloc[i, data.columns.get_loc('signal')] = -1
                data.iloc[i, data.columns.get_loc('signal_type')] = 'SELL'
                data.iloc[i, data.columns.get_loc('signal_strength')] = min(1, bb_percent - 1)
        
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
        
        if data is None or len(data) < self.period:
            return {
                'error': f'Not enough data. Need at least {self.period} data points.',
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
                'bb_percent': signal_row['bb_percent'],
                'strength': signal_row['signal_strength']
            }
        
        # Determine market condition based on %B
        bb_percent = latest['bb_percent']
        if bb_percent > 0.8:
            condition = 'OVERBOUGHT'
        elif bb_percent < 0.2:
            condition = 'OVERSOLD'
        else:
            condition = 'NEUTRAL'
        
        # Volatility condition based on bandwidth
        bandwidth = latest['bb_bandwidth']
        if bandwidth > 0.1:
            volatility = 'HIGH'
        elif bandwidth < 0.05:
            volatility = 'LOW'
        else:
            volatility = 'NORMAL'
        
        return {
            'current_price': latest['price'],
            'bb_upper': latest['bb_upper'],
            'bb_middle': latest['bb_middle'],
            'bb_lower': latest['bb_lower'],
            'bb_percent': bb_percent,
            'bb_bandwidth': bandwidth,
            'market_condition': condition,
            'volatility': volatility,
            'current_signal': current_signal,
            'data_points': len(data_with_signals),
            'strategy': f'BB({self.period},{self.std_dev})'
        }
    
    def backtest(self, hours=168):  # 1 week default
        """Run backtest on historical data"""
        data = self.get_historical_data(hours=hours)
        
        if data is None or len(data) < self.period:
            return {
                'error': f'Not enough data for backtesting. Need at least {self.period} data points.'
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
                    # Use signal strength to determine position size (25% to 75% of available balance)
                    position_size = 0.25 + (0.5 * row['signal_strength'])
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
                        'bb_percent': row['bb_percent'],
                        'signal_strength': row['signal_strength']
                    })
            
            elif row['signal'] == -1:  # Sell signal
                if bitcoin_held > 0:  # Only sell if we have position
                    # Use signal strength to determine how much to sell
                    sell_ratio = 0.25 + (0.5 * row['signal_strength'])
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
                        'bb_percent': row['bb_percent'],
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
        
        # Calculate average %B at buy/sell points
        buy_bb_avg = np.mean([t['bb_percent'] for t in trades if t['type'] == 'BUY']) if trades else 0
        sell_bb_avg = np.mean([t['bb_percent'] for t in trades if t['type'] == 'SELL']) if trades else 0
        
        return {
            'initial_balance': initial_balance,
            'final_value': final_value,
            'total_return_percent': total_return,
            'total_trades': len(trades),
            'completed_trades': total_completed_trades,
            'win_rate_percent': win_rate,
            'avg_buy_bb_percent': buy_bb_avg,
            'avg_sell_bb_percent': sell_bb_avg,
            'trades': trades[-10:],  # Last 10 trades
            'period_hours': hours,
            'strategy': f'BB({self.period},{self.std_dev})',
            'parameters': {
                'period': self.period,
                'std_dev': self.std_dev
            }
        }
    
    def get_strategy_data_for_chart(self, hours=24):
        """Get strategy data formatted for charting"""
        data = self.get_historical_data(hours=hours)
        
        if data is None or len(data) < self.period:
            return None
        
        data_with_signals = self.generate_signals(data)
        
        # Format for chart
        chart_data = []
        for i, row in data_with_signals.iterrows():
            chart_data.append({
                'timestamp': i.strftime('%Y-%m-%d %H:%M:%S'),
                'price': row['price'],
                'bb_upper': row['bb_upper'] if not pd.isna(row['bb_upper']) else None,
                'bb_middle': row['bb_middle'] if not pd.isna(row['bb_middle']) else None,
                'bb_lower': row['bb_lower'] if not pd.isna(row['bb_lower']) else None,
                'bb_percent': row['bb_percent'] if not pd.isna(row['bb_percent']) else None,
                'signal': row['signal'],
                'signal_type': row['signal_type'],
                'signal_strength': row['signal_strength']
            })
        
        return chart_data


def test_bollinger_bands_strategy():
    """Test the Bollinger Bands strategy with current data"""
    print("🚀 Testing Bollinger Bands Strategy")
    print("=" * 50)
    
    # Initialize strategy
    strategy = BollingerBandsStrategy(period=20, std_dev=2)
    
    # Check how much data we have
    data = strategy.get_historical_data(hours=24)
    if data is not None:
        print(f"📊 Available data points: {len(data)}")
        print(f"   Strategy needs: {strategy.period} minimum")
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
    print(f"   Upper Band: ${analysis['bb_upper']:,.2f}")
    print(f"   Middle Band: ${analysis['bb_middle']:,.2f}")
    print(f"   Lower Band: ${analysis['bb_lower']:,.2f}")
    print(f"   %B: {analysis['bb_percent']:.3f}")
    print(f"   Bandwidth: {analysis['bb_bandwidth']:.3f}")
    print(f"   Market Condition: {analysis['market_condition']}")
    print(f"   Volatility: {analysis['volatility']}")
    print(f"   Strategy: {analysis['strategy']}")
    
    if analysis['current_signal']:
        signal = analysis['current_signal']
        print(f"\n🚨 ACTIVE SIGNAL:")
        print(f"   Type: {signal['type']}")
        print(f"   Price: ${signal['price']:,.2f}")
        print(f"   %B: {signal['bb_percent']:.3f}")
        print(f"   Strength: {signal['strength']:.2f}")
        print(f"   Time: {signal['timestamp']}")
    else:
        print(f"\n⏳ No recent signals")
    
    # Run backtest only if we have enough data
    if analysis.get('data_points', 0) >= strategy.period:
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
            print(f"   Avg Buy %B: {backtest_results['avg_buy_bb_percent']:.3f}")
            print(f"   Avg Sell %B: {backtest_results['avg_sell_bb_percent']:.3f}")
            
            if backtest_results['trades']:
                print(f"\n📋 Recent Trades:")
                for trade in backtest_results['trades'][-3:]:
                    print(f"   {trade['type']}: ${trade['price']:,.2f} (%B: {trade['bb_percent']:.3f}, Strength: {trade['signal_strength']:.2f}) at {trade['timestamp']}")
    else:
        print(f"\n📈 Not enough data for backtesting yet")
        print(f"   Need {strategy.period} points, have {analysis.get('data_points', 0)}")
        print(f"   💡 Generate sample data: python scripts/generate_sample_data.py")


if __name__ == "__main__":
    test_bollinger_bands_strategy()