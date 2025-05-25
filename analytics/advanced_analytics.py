# analytics/advanced_analytics.py

import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import sqlite3
import os
from typing import Dict, List, Tuple, Optional
from scipy import stats
import warnings
warnings.filterwarnings('ignore')

class AdvancedAnalytics:
    def __init__(self, db_path=None):
        """
        Advanced analytics engine for comprehensive trading analysis
        """
        if db_path is None:
            current_dir = os.path.dirname(os.path.abspath(__file__))
            project_root = os.path.dirname(current_dir)
            db_path = os.path.join(project_root, 'data', 'bitcoin_data.db')
        
        self.db_path = db_path
    
    def get_trade_data(self) -> pd.DataFrame:
        """Get all completed trades from database"""
        conn = sqlite3.connect(self.db_path)
        
        try:
            df = pd.read_sql_query('''
                SELECT * FROM trade_history 
                ORDER BY exit_time ASC
            ''', conn)
            
            if len(df) > 0:
                df['entry_time'] = pd.to_datetime(df['entry_time'])
                df['exit_time'] = pd.to_datetime(df['exit_time'])
                df['duration'] = (df['exit_time'] - df['entry_time']).dt.total_seconds() / 3600  # Hours
            
            return df
        except Exception as e:
            print(f"Error getting trade data: {e}")
            return pd.DataFrame()
        finally:
            conn.close()
    
    def get_price_data(self, hours: int = 720) -> pd.DataFrame:
        """Get historical price data"""
        conn = sqlite3.connect(self.db_path)
        
        cutoff_time = (datetime.now() - timedelta(hours=hours)).strftime('%Y-%m-%d %H:%M:%S')
        
        df = pd.read_sql_query('''
            SELECT timestamp, price FROM btc_prices 
            WHERE timestamp >= ? 
            ORDER BY timestamp ASC
        ''', conn, params=(cutoff_time,))
        
        conn.close()
        
        if len(df) > 0:
            df['timestamp'] = pd.to_datetime(df['timestamp'])
            df.set_index('timestamp', inplace=True)
        
        return df
    
    def calculate_sharpe_ratio(self, returns: pd.Series, risk_free_rate: float = 0.02) -> float:
        """Calculate annualized Sharpe ratio"""
        if len(returns) == 0 or returns.std() == 0:
            return 0.0
        
        excess_returns = returns - (risk_free_rate / 252)  # Daily risk-free rate
        return (excess_returns.mean() / returns.std()) * np.sqrt(252)
    
    def calculate_sortino_ratio(self, returns: pd.Series, risk_free_rate: float = 0.02) -> float:
        """Calculate Sortino ratio (downside deviation)"""
        if len(returns) == 0:
            return 0.0
        
        excess_returns = returns - (risk_free_rate / 252)
        downside_returns = excess_returns[excess_returns < 0]
        
        if len(downside_returns) == 0 or downside_returns.std() == 0:
            return 0.0
        
        return (excess_returns.mean() / downside_returns.std()) * np.sqrt(252)
    
    def calculate_calmar_ratio(self, returns: pd.Series) -> float:
        """Calculate Calmar ratio (return/max drawdown)"""
        if len(returns) == 0:
            return 0.0
        
        cumulative_returns = (1 + returns).cumprod()
        peak = cumulative_returns.expanding().max()
        drawdown = (cumulative_returns - peak) / peak
        max_drawdown = abs(drawdown.min())
        
        if max_drawdown == 0:
            return 0.0
        
        annual_return = returns.mean() * 252
        return annual_return / max_drawdown
    
    def calculate_var_cvar(self, returns: pd.Series, confidence: float = 0.05) -> Tuple[float, float]:
        """Calculate Value at Risk and Conditional VaR"""
        if len(returns) == 0:
            return 0.0, 0.0
        
        var = np.percentile(returns, confidence * 100)
        cvar = returns[returns <= var].mean()
        
        return var, cvar
    
    def calculate_maximum_drawdown(self, returns: pd.Series) -> Dict:
        """Calculate maximum drawdown with details"""
        if len(returns) == 0:
            return {'max_drawdown': 0, 'drawdown_duration': 0, 'recovery_time': 0}
        
        cumulative = (1 + returns).cumprod()
        peak = cumulative.expanding().max()
        drawdown = (cumulative - peak) / peak
        
        max_dd = drawdown.min()
        max_dd_idx = drawdown.idxmin()
        
        # Find drawdown duration
        if pd.notna(max_dd_idx):
            # Find when drawdown started
            start_idx = None
            for i in range(len(drawdown)):
                if drawdown.index[i] >= max_dd_idx:
                    break
                if drawdown.iloc[i] == 0:
                    start_idx = drawdown.index[i]
            
            # Find recovery time
            recovery_idx = None
            for i in range(len(drawdown)):
                if drawdown.index[i] > max_dd_idx and drawdown.iloc[i] >= 0:
                    recovery_idx = drawdown.index[i]
                    break
            
            if start_idx and recovery_idx:
                drawdown_duration = (max_dd_idx - start_idx).total_seconds() / 3600  # Hours
                recovery_time = (recovery_idx - max_dd_idx).total_seconds() / 3600  # Hours
            else:
                drawdown_duration = 0
                recovery_time = 0
        else:
            drawdown_duration = 0
            recovery_time = 0
        
        return {
            'max_drawdown': abs(max_dd),
            'drawdown_duration': drawdown_duration,
            'recovery_time': recovery_time,
            'drawdown_start': start_idx,
            'drawdown_bottom': max_dd_idx,
            'recovery_date': recovery_idx
        }
    
    def analyze_win_streaks(self, trades_df: pd.DataFrame) -> Dict:
        """Analyze winning and losing streaks"""
        if len(trades_df) == 0:
            return {'error': 'No trade data available'}
        
        # Create win/loss sequence
        wins = (trades_df['pnl'] > 0).astype(int)
        
        # Find streaks
        streak_changes = wins.diff().fillna(0) != 0
        streak_groups = streak_changes.cumsum()
        
        streaks = []
        for group in streak_groups.unique():
            group_data = wins[streak_groups == group]
            streak_length = len(group_data)
            streak_type = 'win' if group_data.iloc[0] == 1 else 'loss'
            streaks.append({'length': streak_length, 'type': streak_type})
        
        # Analyze streaks
        win_streaks = [s['length'] for s in streaks if s['type'] == 'win']
        loss_streaks = [s['length'] for s in streaks if s['type'] == 'loss']
        
        return {
            'max_win_streak': max(win_streaks) if win_streaks else 0,
            'max_loss_streak': max(loss_streaks) if loss_streaks else 0,
            'avg_win_streak': np.mean(win_streaks) if win_streaks else 0,
            'avg_loss_streak': np.mean(loss_streaks) if loss_streaks else 0,
            'current_streak': streaks[-1] if streaks else {'length': 0, 'type': 'none'},
            'total_streaks': len(streaks)
        }
    
    def analyze_trade_timing(self, trades_df: pd.DataFrame) -> Dict:
        """Analyze trade timing patterns"""
        if len(trades_df) == 0:
            return {'error': 'No trade data available'}
        
        # Extract time features
        trades_df['entry_hour'] = trades_df['entry_time'].dt.hour
        trades_df['entry_day'] = trades_df['entry_time'].dt.day_name()
        trades_df['trade_duration'] = trades_df['duration']
        
        # Analyze by hour
        hourly_performance = trades_df.groupby('entry_hour').agg({
            'pnl': ['mean', 'count'],
            'pnl_percent': 'mean'
        }).round(2)
        
        # Analyze by day of week
        daily_performance = trades_df.groupby('entry_day').agg({
            'pnl': ['mean', 'count'],
            'pnl_percent': 'mean'
        }).round(2)
        
        # Best and worst times
        best_hour = hourly_performance[('pnl', 'mean')].idxmax()
        worst_hour = hourly_performance[('pnl', 'mean')].idxmin()
        best_day = daily_performance[('pnl', 'mean')].idxmax()
        worst_day = daily_performance[('pnl', 'mean')].idxmin()
        
        return {
            'hourly_performance': hourly_performance.to_dict(),
            'daily_performance': daily_performance.to_dict(),
            'best_hour': int(best_hour),
            'worst_hour': int(worst_hour),
            'best_day': str(best_day),
            'worst_day': str(worst_day),
            'avg_trade_duration': trades_df['trade_duration'].mean(),
            'median_trade_duration': trades_df['trade_duration'].median()
        }
    
    def calculate_strategy_correlation(self, trades_df: pd.DataFrame) -> Dict:
        """Calculate correlation between different strategies"""
        if len(trades_df) == 0 or 'strategy_name' not in trades_df.columns:
            return {'error': 'No strategy data available'}
        
        strategies = trades_df['strategy_name'].unique()
        
        if len(strategies) < 2:
            return {'error': 'Need at least 2 strategies for correlation analysis'}
        
        # Create returns matrix by strategy
        strategy_returns = {}
        for strategy in strategies:
            strategy_trades = trades_df[trades_df['strategy_name'] == strategy]
            if len(strategy_trades) > 0:
                strategy_returns[strategy] = strategy_trades['pnl_percent'].values
        
        # Calculate correlations
        correlations = {}
        for i, strategy1 in enumerate(strategies):
            for j, strategy2 in enumerate(strategies):
                if i < j and strategy1 in strategy_returns and strategy2 in strategy_returns:
                    returns1 = strategy_returns[strategy1]
                    returns2 = strategy_returns[strategy2]
                    
                    # Align arrays to same length
                    min_length = min(len(returns1), len(returns2))
                    if min_length > 1:
                        corr, p_value = stats.pearsonr(returns1[:min_length], returns2[:min_length])
                        correlations[f"{strategy1}_vs_{strategy2}"] = {
                            'correlation': corr,
                            'p_value': p_value,
                            'significant': p_value < 0.05
                        }
        
        return {
            'correlations': correlations,
            'strategy_count': len(strategies),
            'total_comparisons': len(correlations)
        }
    
    def benchmark_against_buy_hold(self, trades_df: pd.DataFrame) -> Dict:
        """Compare strategy performance against buy and hold"""
        if len(trades_df) == 0:
            return {'error': 'No trade data available'}
        
        # Get price data for the same period
        start_date = trades_df['entry_time'].min()
        end_date = trades_df['exit_time'].max()
        
        price_data = self.get_price_data(hours=int((end_date - start_date).total_seconds() / 3600) + 24)
        
        if len(price_data) == 0:
            return {'error': 'No price data available for benchmark'}
        
        # Calculate buy and hold return
        start_price = price_data['price'].iloc[0]
        end_price = price_data['price'].iloc[-1]
        buy_hold_return = ((end_price - start_price) / start_price) * 100
        
        # Calculate strategy returns
        strategy_return = trades_df['pnl_percent'].sum()
        
        # Calculate metrics
        outperformance = strategy_return - buy_hold_return
        
        # Calculate volatility comparison
        price_returns = price_data['price'].pct_change().dropna()
        trade_returns = trades_df['pnl_percent'] / 100
        
        buy_hold_volatility = price_returns.std() * np.sqrt(252) * 100  # Annualized %
        strategy_volatility = trade_returns.std() * np.sqrt(len(trade_returns)) * 100 if len(trade_returns) > 1 else 0
        
        return {
            'strategy_return': strategy_return,
            'buy_hold_return': buy_hold_return,
            'outperformance': outperformance,
            'strategy_volatility': strategy_volatility,
            'buy_hold_volatility': buy_hold_volatility,
            'risk_adjusted_outperformance': outperformance / max(strategy_volatility, 0.01),
            'period_days': (end_date - start_date).days,
            'start_price': start_price,
            'end_price': end_price
        }
    
    def generate_comprehensive_report(self) -> Dict:
        """Generate comprehensive analytics report"""
        trades_df = self.get_trade_data()
        
        if len(trades_df) == 0:
            return {'error': 'No trade data available for analysis'}
        
        # Basic statistics
        total_trades = len(trades_df)
        profitable_trades = len(trades_df[trades_df['pnl'] > 0])
        win_rate = (profitable_trades / total_trades) * 100
        
        total_pnl = trades_df['pnl'].sum()
        avg_win = trades_df[trades_df['pnl'] > 0]['pnl_percent'].mean()
        avg_loss = trades_df[trades_df['pnl'] < 0]['pnl_percent'].mean()
        
        # Convert to returns for ratio calculations
        returns = trades_df['pnl_percent'] / 100
        
        # Advanced ratios
        sharpe = self.calculate_sharpe_ratio(returns)
        sortino = self.calculate_sortino_ratio(returns)
        calmar = self.calculate_calmar_ratio(returns)
        
        # Risk metrics
        var_95, cvar_95 = self.calculate_var_cvar(returns, 0.05)
        max_dd_info = self.calculate_maximum_drawdown(returns)
        
        # Pattern analysis
        streak_analysis = self.analyze_win_streaks(trades_df)
        timing_analysis = self.analyze_trade_timing(trades_df)
        correlation_analysis = self.calculate_strategy_correlation(trades_df)
        benchmark_analysis = self.benchmark_against_buy_hold(trades_df)
        
        return {
            'basic_statistics': {
                'total_trades': total_trades,
                'profitable_trades': profitable_trades,
                'win_rate': win_rate,
                'total_pnl': total_pnl,
                'avg_win_percent': avg_win if not pd.isna(avg_win) else 0,
                'avg_loss_percent': avg_loss if not pd.isna(avg_loss) else 0,
                'profit_factor': abs(avg_win / avg_loss) if not pd.isna(avg_loss) and avg_loss != 0 else 0
            },
            'risk_adjusted_metrics': {
                'sharpe_ratio': sharpe,
                'sortino_ratio': sortino,
                'calmar_ratio': calmar,
                'var_95_percent': var_95 * 100,
                'cvar_95_percent': cvar_95 * 100
            },
            'drawdown_analysis': max_dd_info,
            'streak_analysis': streak_analysis,
            'timing_analysis': timing_analysis,
            'correlation_analysis': correlation_analysis,
            'benchmark_comparison': benchmark_analysis,
            'report_generated': datetime.now().isoformat()
        }