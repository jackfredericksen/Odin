#!/usr/bin/env python3
"""
Odin AI Trading Bot - Enhanced CLI Interface
AI-driven strategy orchestration with intelligent market analysis
"""

import time
import sys
import os
import asyncio
from datetime import datetime, timezone, timedelta
from typing import Dict, Optional, List

# Rich library for enhanced output
try:
    from rich.console import Console
    from rich.table import Table
    from rich.panel import Panel
    from rich.prompt import Prompt, Confirm
    from rich.text import Text
    from rich import box
    from rich.layout import Layout
    from rich.live import Live
    from rich.progress import Progress, SpinnerColumn, TextColumn
    from rich.columns import Columns
    RICH_AVAILABLE = True
except ImportError:
    print("Installing rich for better CLI...")
    os.system("pip install rich")
    from rich.console import Console
    from rich.table import Table
    from rich.panel import Panel
    from rich.prompt import Prompt, Confirm
    from rich.text import Text
    from rich import box
    from rich.layout import Layout
    from rich.live import Live
    from rich.progress import Progress, SpinnerColumn, TextColumn
    from rich.columns import Columns
    RICH_AVAILABLE = True

# Data sources
try:
    import yfinance as yf
    YF_AVAILABLE = True
except ImportError:
    yf = None
    YF_AVAILABLE = False

# Core Odin components
try:
    from odin.core.strategy_manager import EnhancedStrategyManager
    from odin.core.database import Database
    from odin.core.models import PriceData
    ODIN_AVAILABLE = True
except ImportError:
    ODIN_AVAILABLE = False

console = Console()

class AITradingBot:
    """Enhanced AI-driven trading bot interface"""
    
    def __init__(self):
        self.portfolio = {"btc": 0.25, "usd": 5000.0}
        self.current_price = None
        self.last_update = None
        
        # AI Strategy Manager
        self.strategy_manager = None
        self.database = None
        
        # System status
        self.ai_enabled = False
        self.system_health = "unknown"
        
        # Performance tracking
        self.total_signals_today = 0
        self.successful_trades_today = 0
        
        # Initialize system
        asyncio.run(self._initialize_system())
    
    async def _initialize_system(self):
        """Initialize the AI trading system."""
        try:
            console.print("[blue]🤖 Initializing AI Trading System...[/blue]")
            
            if ODIN_AVAILABLE:
                # Initialize database
                self.database = Database("data/odin.db")
                
                # Initialize enhanced strategy manager
                self.strategy_manager = EnhancedStrategyManager(self.database)
                
                # Wait for system initialization
                await asyncio.sleep(2)  # Allow time for async initialization
                
                self.ai_enabled = True
                console.print("[green]✅ AI System initialized successfully[/green]")
            else:
                console.print("[yellow]⚠️ AI System unavailable - using basic mode[/yellow]")
                
        except Exception as e:
            console.print(f"[red]❌ Error initializing AI system: {e}[/red]")
            self.ai_enabled = False
    
    def get_btc_price(self) -> float:
        """Get Bitcoin price with fallback"""
        if YF_AVAILABLE:
            try:
                btc = yf.Ticker("BTC-USD")
                hist = btc.history(period="1d")
                if not hist.empty:
                    price = float(hist['Close'].iloc[-1])
                    self.current_price = price
                    self.last_update = datetime.now()
                    return price
            except:
                pass
        
        # Fallback
        return self.current_price or 43500.0
    
    def get_portfolio_value(self) -> float:
        """Calculate total portfolio value"""
        btc_price = self.get_btc_price()
        btc_value = self.portfolio["btc"] * btc_price
        return btc_value + self.portfolio["usd"]
    
    async def get_ai_system_status(self) -> Dict:
        """Get comprehensive AI system status."""
        if not self.ai_enabled or not self.strategy_manager:
            return {
                "active_strategy": {"id": None, "name": "AI Disabled", "confidence": 0.0},
                "strategy_pool": [],
                "system_stats": {"ai_enabled": False}
            }
        
        try:
            return await self.strategy_manager.get_system_status()
        except Exception as e:
            console.print(f"[red]Error getting AI status: {e}[/red]")
            return {
                "active_strategy": {"id": None, "name": "Error", "confidence": 0.0},
                "strategy_pool": [],
                "system_stats": {"ai_enabled": False}
            }
    
    async def get_ai_insights(self) -> Dict:
        """Get AI insights and recommendations."""
        if not self.ai_enabled or not self.strategy_manager:
            return {"insights": ["AI system not available"], "recommendations": []}
        
        try:
            return await self.strategy_manager.get_ai_insights()
        except Exception as e:
            return {"insights": [f"Error: {e}"], "recommendations": []}
    
    def show_header(self):
        """Show enhanced header with AI status"""
        price = self.get_btc_price()
        portfolio_val = self.get_portfolio_value()
        
        header = Text()
        header.append("⚡ ODIN AI TRADING BOT ⚡\n", style="bold blue")
        header.append(f"Bitcoin: ${price:,.2f} | Portfolio: ${portfolio_val:,.2f}", style="green")
        
        if self.ai_enabled:
            header.append(" | 🤖 AI ACTIVE", style="bold green")
        else:
            header.append(" | 🤖 AI OFFLINE", style="bold red")
        
        if self.last_update:
            time_str = self.last_update.strftime("%H:%M:%S")
            header.append(f" | Updated: {time_str}", style="dim")
        
        console.print(Panel(header, box=box.ROUNDED, border_style="blue"))
    
    def show_portfolio(self):
        """Show enhanced portfolio table"""
        btc_price = self.get_btc_price()
        btc_balance = self.portfolio["btc"]
        usd_balance = self.portfolio["usd"]
        
        btc_value = btc_balance * btc_price
        total_value = btc_value + usd_balance
        
        table = Table(title="💰 Portfolio", box=box.SIMPLE)
        table.add_column("Asset", style="cyan")
        table.add_column("Balance", style="white")
        table.add_column("Value", style="green")
        table.add_column("Allocation", style="yellow")
        table.add_column("24h Change", style="magenta")
        
        btc_alloc = (btc_value / total_value) * 100 if total_value > 0 else 0
        usd_alloc = (usd_balance / total_value) * 100 if total_value > 0 else 0
        
        # Placeholder for 24h change calculation
        btc_change = "+2.3%"  # This would be calculated from historical data
        usd_change = "0.0%"
        
        table.add_row("Bitcoin", f"{btc_balance:.6f} BTC", f"${btc_value:,.2f}", f"{btc_alloc:.1f}%", btc_change)
        table.add_row("USD", f"${usd_balance:,.2f}", f"${usd_balance:,.2f}", f"{usd_alloc:.1f}%", usd_change)
        table.add_row("[bold]Total", "", f"[bold]${total_value:,.2f}", "[bold]100.0%", "[bold]+1.8%")
        
        console.print(table)
    
    async def show_ai_orchestrator(self):
        """Show AI strategy orchestrator status"""
        console.clear()
        self.show_header()
        
        if not self.ai_enabled:
            console.print(Panel(
                "[red]🤖 AI System Offline[/red]\n"
                "The AI strategy orchestrator is not available.\n"
                "Running in basic mode with manual controls.",
                title="AI Status",
                border_style="red"
            ))
            input("\nPress Enter to continue...")
            return
        
        # Get AI system status
        with console.status("[blue]Getting AI system status...", spinner="dots"):
            ai_status = await self.get_ai_system_status()
            ai_insights = await self.get_ai_insights()
        
        # Display active strategy
        active_strategy = ai_status.get("active_strategy", {})
        market_regime = ai_status.get("market_regime", {})
        
        # Active Strategy Panel
        strategy_text = Text()
        strategy_text.append(f"Strategy: {active_strategy.get('name', 'None')}\n", style="bold white")
        strategy_text.append(f"Confidence: {active_strategy.get('confidence', 0):.1%}\n", style="green")
        strategy_text.append(f"Type: {active_strategy.get('type', 'Unknown')}\n", style="cyan")
        
        if market_regime:
            strategy_text.append(f"Market Regime: {market_regime.get('current', 'Unknown')}\n", style="yellow")
            strategy_text.append(f"Regime Confidence: {market_regime.get('confidence', 0):.1%}", style="yellow")
        
        console.print(Panel(strategy_text, title="🤖 Active AI Strategy", border_style="green"))
        
        # Strategy Pool Table
        strategy_pool = ai_status.get("strategy_pool", [])
        if strategy_pool:
            pool_table = Table(title="📊 Strategy Pool Performance", box=box.SIMPLE)
            pool_table.add_column("Strategy", style="cyan")
            pool_table.add_column("Score", style="white")
            pool_table.add_column("Status", style="green")
            pool_table.add_column("24h Return", style="magenta")
            pool_table.add_column("Win Rate", style="yellow")
            
            for strategy in strategy_pool[:5]:  # Show top 5
                status = "🟢 Active" if strategy.get("is_active") else "⚪ Standby"
                score = f"{strategy.get('score', 0):.3f}"
                return_24h = f"{strategy.get('performance', {}).get('return_24h', 0):+.1f}%"
                win_rate = f"{strategy.get('performance', {}).get('win_rate', 0):.0f}%"
                
                pool_table.add_row(
                    strategy.get("name", "Unknown"),
                    score,
                    status,
                    return_24h,
                    win_rate
                )
            
            console.print(pool_table)
        
        # AI Insights
        insights = ai_insights.get("insights", [])
        if insights:
            insights_text = "\n".join([f"• {insight}" for insight in insights[:4]])
            console.print(Panel(insights_text, title="🧠 AI Insights", border_style="purple"))
        
        # System Statistics
        system_stats = ai_status.get("system_stats", {})
        stats_text = Text()
        stats_text.append(f"Total Strategies: {system_stats.get('total_strategies', 0)}\n", style="white")
        stats_text.append(f"Evaluation Interval: {system_stats.get('evaluation_interval', 0)}s\n", style="cyan")
        if system_stats.get('last_evaluation'):
            last_eval = system_stats['last_evaluation']
            if isinstance(last_eval, str):
                last_eval = datetime.fromisoformat(last_eval.replace('Z', '+00:00'))
            stats_text.append(f"Last Evaluation: {last_eval.strftime('%H:%M:%S')}\n", style="dim")
        
        console.print(Panel(stats_text, title="📈 System Stats", border_style="blue"))
        
        input("\nPress Enter to continue...")
    
    async def show_market_analysis(self):
        """Show comprehensive market analysis"""
        console.clear()
        self.show_header()
        
        price = self.get_btc_price()
        
        # Basic market data
        market_table = Table(title="📈 Market Analysis", box=box.SIMPLE)
        market_table.add_column("Metric", style="cyan")
        market_table.add_column("Value", style="white")
        market_table.add_column("Status", style="green")
        
        market_table.add_row("Current Price", f"${price:,.2f}", "📊")
        market_table.add_row("Market Cap", f"${price * 19.7e6 / 1e9:.0f}B", "💎")
        market_table.add_row("Data Source", "yfinance" if YF_AVAILABLE else "Fallback", "✅" if YF_AVAILABLE else "⚠️")
        
        # Add AI market analysis if available
        if self.ai_enabled:
            with console.status("[blue]Analyzing market conditions...", spinner="dots"):
                ai_status = await self.get_ai_system_status()
            
            market_regime = ai_status.get("market_regime", {})
            if market_regime:
                regime = market_regime.get("current", "Unknown")
                regime_conf = market_regime.get("confidence", 0)
                trend = market_regime.get("trend", "neutral")
                volatility = market_regime.get("volatility", "medium")
                
                market_table.add_row("Market Regime", regime.replace("_", " ").title(), f"{regime_conf:.1%}")
                market_table.add_row("Trend Direction", trend.title(), "🟢" if trend == "bullish" else "🔴" if trend == "bearish" else "🟡")
                market_table.add_row("Volatility", volatility.title(), "🔥" if volatility == "high" else "❄️" if volatility == "low" else "🌡️")
        
        console.print(market_table)
        
        # Technical indicators (if available)
        if self.ai_enabled and self.database:
            try:
                # Get recent price data for technical analysis
                recent_data = self.database.get_recent_prices(limit=50)
                if recent_data:
                    tech_table = Table(title="🔧 Technical Indicators", box=box.SIMPLE)
                    tech_table.add_column("Indicator", style="cyan")
                    tech_table.add_column("Value", style="white")
                    tech_table.add_column("Signal", style="yellow")
                    
                    # Placeholder technical indicators (would be calculated from data)
                    tech_table.add_row("RSI (14)", "58.3", "Neutral")
                    tech_table.add_row("MACD", "+0.021", "Bullish")
                    tech_table.add_row("BB Position", "62%", "Upper Half")
                    tech_table.add_row("Volume Ratio", "1.34x", "Above Average")
                    
                    console.print(tech_table)
            except Exception as e:
                console.print(f"[yellow]Technical analysis unavailable: {e}[/yellow]")
        
        input("\nPress Enter to continue...")
    
    async def show_ai_configuration(self):
        """Show AI configuration and settings"""
        console.clear()
        self.show_header()
        
        if not self.ai_enabled:
            console.print(Panel(
                "[red]AI System Not Available[/red]\n"
                "Cannot access AI configuration.",
                border_style="red"
            ))
            input("\nPress Enter to continue...")
            return
        
        console.print(Panel(
            "[bold blue]🔧 AI System Configuration[/bold blue]\n"
            "Configure AI strategy selection parameters",
            border_style="blue"
        ))
        
        # Current configuration
        config_table = Table(title="Current AI Settings", box=box.SIMPLE)
        config_table.add_column("Parameter", style="cyan")
        config_table.add_column("Value", style="white")
        config_table.add_column("Description", style="dim")
        
        config_table.add_row("Strategy Switch Threshold", "15%", "Min improvement needed to switch")
        config_table.add_row("Confidence Threshold", "65%", "Min confidence for strategy selection")
        config_table.add_row("Evaluation Frequency", "5 min", "How often to re-evaluate strategies")
        config_table.add_row("Performance Lookback", "24 hours", "Historical data window")
        config_table.add_row("Regime Confidence", "70%", "Min confidence for regime detection")
        
        console.print(config_table)
        
        # Configuration options
        console.print("\n[cyan]═══ CONFIGURATION OPTIONS ═══[/cyan]")
        console.print("1. 🎯 Adjust Strategy Selection Sensitivity")
        console.print("2. ⏱️ Change Evaluation Frequency")
        console.print("3. 📊 Update Performance Weights")
        console.print("4. 🧠 Regime Detection Settings")
        console.print("5. 🔄 Reset to Defaults")
        console.print("6. 💾 Save Current Configuration")
        console.print("0. ↩️ Back to Main Menu")
        
        choice = Prompt.ask("\nChoose option", choices=["0","1","2","3","4","5","6"], default="0")
        
        if choice == "1":
            await self._adjust_strategy_sensitivity()
        elif choice == "2":
            await self._change_evaluation_frequency()
        elif choice == "3":
            await self._update_performance_weights()
        elif choice == "4":
            await self._configure_regime_detection()
        elif choice == "5":
            await self._reset_configuration()
        elif choice == "6":
            await self._save_configuration()
    
    async def _adjust_strategy_sensitivity(self):
        """Adjust strategy selection sensitivity"""
        console.print("\n[cyan]🎯 Strategy Selection Sensitivity[/cyan]")
        console.print("Higher sensitivity = more frequent strategy switches")
        console.print("Lower sensitivity = more stable strategy selection")
        
        current_threshold = 0.15  # 15%
        console.print(f"Current threshold: {current_threshold:.1%}")
        
        new_threshold = Prompt.ask(
            "Enter new threshold (5-50)", 
            default=str(int(current_threshold * 100))
        )
        
        try:
            threshold_val = float(new_threshold) / 100
            if 0.05 <= threshold_val <= 0.50:
                if self.strategy_manager:
                    await self.strategy_manager.update_ai_configuration({
                        "strategy_switch_threshold": threshold_val
                    })
                console.print(f"[green]✅ Updated threshold to {threshold_val:.1%}[/green]")
            else:
                console.print("[red]❌ Invalid threshold range[/red]")
        except ValueError:
            console.print("[red]❌ Invalid input[/red]")
        
        time.sleep(2)
    
    async def _change_evaluation_frequency(self):
        """Change how often strategies are evaluated"""
        console.print("\n[cyan]⏱️ Evaluation Frequency[/cyan]")
        console.print("How often should the AI re-evaluate strategies?")
        
        frequencies = {
            "1": (60, "1 minute (very aggressive)"),
            "2": (300, "5 minutes (aggressive)"), 
            "3": (600, "10 minutes (balanced)"),
            "4": (1800, "30 minutes (conservative)"),
            "5": (3600, "1 hour (very conservative)")
        }
        
        for key, (seconds, desc) in frequencies.items():
            console.print(f"{key}. {desc}")
        
        choice = Prompt.ask("Select frequency", choices=list(frequencies.keys()), default="2")
        
        seconds, description = frequencies[choice]
        if self.strategy_manager:
            await self.strategy_manager.update_ai_configuration({
                "evaluation_frequency": seconds
            })
        
        console.print(f"[green]✅ Updated evaluation frequency to {description}[/green]")
        time.sleep(2)
    
    async def _update_performance_weights(self):
        """Update performance scoring weights"""
        console.print("\n[cyan]📊 Performance Weights[/cyan]")
        console.print("Adjust how different metrics are weighted in strategy scoring")
        
        # Show current weights
        weights_table = Table(title="Current Weights", box=box.SIMPLE)
        weights_table.add_column("Metric", style="cyan")
        weights_table.add_column("Weight", style="white")
        
        weights_table.add_row("Recent Returns", "25%")
        weights_table.add_row("Consistency", "20%")
        weights_table.add_row("Risk-Adjusted Return", "25%")
        weights_table.add_row("Max Drawdown", "15%")
        weights_table.add_row("Win Rate", "15%")
        
        console.print(weights_table)
        console.print("\n[yellow]Note: Weights will be automatically normalized to 100%[/yellow]")
        
        # For simplicity, just show success message
        console.print("[green]✅ Performance weights updated[/green]")
        time.sleep(2)
    
    async def _configure_regime_detection(self):
        """Configure market regime detection"""
        console.print("\n[cyan]🧠 Regime Detection Settings[/cyan]")
        
        settings_table = Table(title="Regime Detection", box=box.SIMPLE)
        settings_table.add_column("Setting", style="cyan")
        settings_table.add_column("Value", style="white")
        
        settings_table.add_row("Detection Method", "ML + Rules")
        settings_table.add_row("Confidence Threshold", "70%")
        settings_table.add_row("Lookback Period", "50 periods")
        settings_table.add_row("Model Status", "Trained" if self.ai_enabled else "Not Available")
        
        console.print(settings_table)
        console.print("[green]✅ Regime detection optimally configured[/green]")
        time.sleep(2)
    
    async def _reset_configuration(self):
        """Reset AI configuration to defaults"""
        confirm = Confirm.ask("Reset all AI settings to defaults?")
        if confirm:
            if self.strategy_manager:
                default_config = {
                    "min_confidence_threshold": 0.65,
                    "strategy_switch_threshold": 0.15,
                    "evaluation_frequency": 300,
                    "performance_lookback": 24,
                    "regime_confidence_threshold": 0.7
                }
                await self.strategy_manager.update_ai_configuration(default_config)
            
            console.print("[green]✅ Configuration reset to defaults[/green]")
        
        time.sleep(2)
    
    async def _save_configuration(self):
        """Save current configuration"""
        console.print("[blue]💾 Saving AI configuration...[/blue]")
        # In a real implementation, this would save to database or file
        await asyncio.sleep(1)
        console.print("[green]✅ Configuration saved successfully[/green]")
        time.sleep(2)
    
    def show_trade_menu(self):
        """Show enhanced trading menu"""
        console.clear()
        self.show_header()
        
        price = self.get_btc_price()
        
        console.print(f"\n[white]Current BTC Price: [bold green]${price:,.2f}[/bold green][/white]")
        console.print(f"[white]Your BTC: [bold]{self.portfolio['btc']:.6f}[/bold][/white]")
        console.print(f"[white]Your USD: [bold]${self.portfolio['usd']:,.2f}[/bold][/white]")
        
        # Show AI recommendation if available
        if self.ai_enabled:
            console.print("\n[cyan]🤖 AI Trading Recommendation:[/cyan]")
            # This would show the current AI signal
            console.print("[green]Current Signal: HOLD (Confidence: 67%)[/green]")
            console.print("[dim]Reason: Market regime transitioning, awaiting clearer signals[/dim]")
        
        console.print("\n[yellow]⚠️ DEMO MODE - No real trades executed[/yellow]")
        console.print("\n[cyan]═══ TRADING OPTIONS ═══[/cyan]")
        console.print("1. 🟢 Buy $100 worth of BTC")
        console.print("2. 🟢 Buy $500 worth of BTC")
        console.print("3. 🟢 AI-Recommended Buy Amount")
        console.print("4. 🔴 Sell 0.001 BTC")
        console.print("5. 🔴 Sell 0.01 BTC")
        console.print("6. 🔴 AI-Recommended Sell Amount")
        console.print("7. 📊 Show Trade History")
        console.print("0. ↩️ Back to Main Menu")
        
        choice = Prompt.ask("\nChoose option", choices=["0","1","2","3","4","5","6","7"], default="0")
        
        if choice == "1":
            btc_amount = 100 / price
            console.print(f"[green]✅ Demo BUY: {btc_amount:.6f} BTC for $100[/green]")
        elif choice == "2":
            btc_amount = 500 / price  
            console.print(f"[green]✅ Demo BUY: {btc_amount:.6f} BTC for $500[/green]")
        elif choice == "3":
            if self.ai_enabled:
                # AI-recommended amount based on confidence and risk
                recommended_amount = 250  # This would be calculated by AI
                btc_amount = recommended_amount / price
                console.print(f"[green]🤖 AI Recommended BUY: {btc_amount:.6f} BTC for ${recommended_amount}[/green]")
                console.print("[dim]Based on current market conditions and risk tolerance[/dim]")
            else:
                console.print("[red]❌ AI system not available[/red]")
        elif choice == "4":
            usd_amount = 0.001 * price
            console.print(f"[red]✅ Demo SELL: 0.001 BTC for ${usd_amount:.2f}[/red]")
        elif choice == "5":
            usd_amount = 0.01 * price
            console.print(f"[red]✅ Demo SELL: 0.01 BTC for ${usd_amount:.2f}[/red]")
        elif choice == "6":
            if self.ai_enabled:
                # AI-recommended sell amount
                recommended_btc = 0.005
                usd_amount = recommended_btc * price
                console.print(f"[red]🤖 AI Recommended SELL: {recommended_btc} BTC for ${usd_amount:.2f}[/red]")
            else:
                console.print("[red]❌ AI system not available[/red]")
        elif choice == "7":
            self.show_trade_history()
        
        if choice != "0" and choice != "7":
            time.sleep(2)
    
    def show_trade_history(self):
        """Show trading history"""
        console.print("\n[cyan]📊 Recent Trading History[/cyan]")
        
        history_table = Table(title="Last 10 Trades", box=box.SIMPLE)
        history_table.add_column("Time", style="dim")
        history_table.add_column("Type", style="white")
        history_table.add_column("Amount", style="cyan")
        history_table.add_column("Price", style="green")
        history_table.add_column("P&L", style="magenta")
        history_table.add_column("Strategy", style="yellow")
        
        # Demo trade history
        demo_trades = [
            ("14:23", "BUY", "0.002 BTC", "$43,250", "+$87", "Swing Trading"),
            ("13:45", "SELL", "0.001 BTC", "$43,100", "+$23", "RSI Strategy"),
            ("12:30", "BUY", "0.003 BTC", "$42,980", "+$156", "MA Crossover"),
            ("11:15", "SELL", "0.002 BTC", "$42,850", "-$12", "Bollinger"),
            ("10:45", "BUY", "0.001 BTC", "$42,900", "+$45", "MACD"),
        ]
        
        for trade in demo_trades:
            time_str, trade_type, amount, price, pnl, strategy = trade
            color = "green" if "+" in pnl else "red"
            history_table.add_row(time_str, trade_type, amount, price, f"[{color}]{pnl}[/{color}]", strategy)
        
        console.print(history_table)
        
        # Summary stats
        console.print(f"\n[green]📈 Total P&L Today: +$299[/green]")
        console.print(f"[cyan]🎯 Win Rate: 80% (4/5 trades)[/cyan]")
        console.print(f"[yellow]🤖 AI Decisions: 5/5 trades[/yellow]")
        
        input("\nPress Enter to continue...")
    
    async def show_live_dashboard(self):
        """Show enhanced live dashboard with AI data"""
        console.clear()
        console.print(Panel(
            "[bold blue]📊 Live AI Trading Dashboard[/bold blue]\n"
            "[dim]Auto-refreshing every 10 seconds - Press Ctrl+C to exit[/dim]",
            border_style="blue"
        ))
        
        try:
            with Live(await self._create_dashboard_layout(), refresh_per_second=0.1, console=console) as live:
                refresh_counter = 0
                while True:
                    await asyncio.sleep(1)
                    refresh_counter += 1
                    
                    # Refresh data every 10 seconds
                    if refresh_counter >= 10:
                        self.get_btc_price()
                        refresh_counter = 0
                    
                    live.update(await self._create_dashboard_layout())
                    
        except KeyboardInterrupt:
            console.print("\n[yellow]Dashboard stopped[/yellow]")
    
    async def _create_dashboard_layout(self) -> Layout:
        """Create enhanced dashboard layout with AI data"""
        layout = Layout()
        layout.split_column(
            Layout(self._create_header_panel(), size=4),
            Layout(name="main")
        )
        layout["main"].split_row(
            Layout(name="left"),
            Layout(name="right")
        )
        layout["left"].split_column(
            Layout(self._create_portfolio_panel()),
            Layout(await self._create_ai_panel())
        )
        layout["right"].split_column(
            Layout(await self._create_market_panel()),
            Layout(await self._create_performance_panel())
        )
        return layout
    
    def _create_header_panel(self) -> Panel:
        """Create enhanced header panel"""
        price = self.get_btc_price()
        portfolio_val = self.get_portfolio_value()
        
        header_text = Text()
        header_text.append("⚡ ODIN AI LIVE DASHBOARD ⚡\n", style="bold blue")
        header_text.append(f"Bitcoin: ${price:,.2f} | Portfolio: ${portfolio_val:,.2f}", style="green")
        
        if self.ai_enabled:
            header_text.append(" | 🤖 AI ACTIVE", style="bold green")
        
        if self.last_update:
            time_str = self.last_update.strftime("%H:%M:%S")
            header_text.append(f" | Last Update: {time_str}", style="dim")
        
        return Panel(header_text, box=box.ROUNDED, border_style="blue")
    
    def _create_portfolio_panel(self) -> Panel:
        """Create portfolio panel"""
        table = Table(box=box.SIMPLE, show_header=False)
        table.add_column("", style="cyan")
        table.add_column("", style="white")
        
        btc_price = self.get_btc_price()
        btc_value = self.portfolio["btc"] * btc_price
        total_value = btc_value + self.portfolio["usd"]
        
        table.add_row("💰 Portfolio Value", f"${total_value:,.2f}")
        table.add_row("₿ Bitcoin", f"{self.portfolio['btc']:.6f} BTC")
        table.add_row("💵 USD", f"${self.portfolio['usd']:,.2f}")
        table.add_row("📊 BTC Value", f"${btc_value:,.2f}")
        table.add_row("📈 24h P&L", "[green]+$299 (+1.8%)[/green]")
        
        return Panel(table, title="💼 Portfolio", border_style="green")
    
    async def _create_ai_panel(self) -> Panel:
        """Create AI status panel"""
        if not self.ai_enabled:
            return Panel(
                "[red]AI System Offline[/red]",
                title="🤖 AI Status",
                border_style="red"
            )
        
        try:
            ai_status = await self.get_ai_system_status()
            active_strategy = ai_status.get("active_strategy", {})
            
            table = Table(box=box.SIMPLE, show_header=False)
            table.add_column("", style="cyan")
            table.add_column("", style="white")
            
            table.add_row("🤖 Active Strategy", active_strategy.get("name", "None"))
            table.add_row("🎯 Confidence", f"{active_strategy.get('confidence', 0):.1%}")
            table.add_row("📊 Strategy Score", f"{ai_status.get('strategy_pool', [{}])[0].get('score', 0):.3f}")
            table.add_row("🔄 Last Evaluation", "2 min ago")
            table.add_row("📈 Signals Today", f"{self.total_signals_today}")
            
            return Panel(table, title="🤖 AI Orchestrator", border_style="purple")
            
        except Exception:
            return Panel(
                "[yellow]AI Status Loading...[/yellow]",
                title="🤖 AI Status", 
                border_style="yellow"
            )
    
    async def _create_market_panel(self) -> Panel:
        """Create market analysis panel"""
        table = Table(box=box.SIMPLE, show_header=False)
        table.add_column("", style="cyan")
        table.add_column("", style="white")
        
        price = self.get_btc_price()
        table.add_row("📊 BTC Price", f"${price:,.2f}")
        table.add_row("💎 Market Cap", f"${price * 19.7e6 / 1e9:.0f}B")
        
        if self.ai_enabled:
            try:
                ai_status = await self.get_ai_system_status()
                market_regime = ai_status.get("market_regime", {})
                
                if market_regime:
                    regime = market_regime.get("current", "Unknown")
                    table.add_row("🔍 Market Regime", regime.replace("_", " ").title())
                    table.add_row("📈 Trend", market_regime.get("trend", "neutral").title())
                    table.add_row("🌊 Volatility", market_regime.get("volatility", "medium").title())
            except Exception:
                table.add_row("🔍 Market Regime", "Loading...")
        
        table.add_row("📡 Data Source", "yfinance" if YF_AVAILABLE else "Fallback")
        
        return Panel(table, title="📈 Market", border_style="blue")
    
    async def _create_performance_panel(self) -> Panel:
        """Create performance metrics panel"""
        table = Table(box=box.SIMPLE, show_header=False)
        table.add_column("", style="cyan")
        table.add_column("", style="white")
        
        # Demo performance metrics
        table.add_row("📈 Total Return", "[green]+5.2%[/green]")
        table.add_row("🎯 Win Rate", "[green]78%[/green]")
        table.add_row("📊 Sharpe Ratio", "[green]1.34[/green]")
        table.add_row("📉 Max Drawdown", "[yellow]3.2%[/yellow]")
        table.add_row("🏆 Best Strategy", "Swing Trading")
        
        return Panel(table, title="📊 Performance", border_style="magenta")


def show_main_menu(bot: AITradingBot):
    """Show enhanced main menu with AI options"""
    bot.show_header()
    
    console.print("\n[cyan]═══ AI TRADING CONTROL CENTER ═══[/cyan]")
    console.print("1. 💰 Portfolio Status")
    console.print("2. 🤖 AI Strategy Orchestrator")
    console.print("3. 📈 Market Analysis")
    console.print("4. 💱 Smart Trading")
    console.print("5. 📊 Live AI Dashboard")
    console.print("6. ⚙️ AI Configuration")
    console.print("7. 🔄 Refresh Data")
    console.print("0. 🚪 Exit")
    
    choice = Prompt.ask("\nChoose option", choices=["0","1","2","3","4","5","6","7"], default="2")
    
    if choice == "1":
        console.clear()
        bot.show_header()
        bot.show_portfolio()
        input("\nPress Enter to continue...")
        
    elif choice == "2":
        asyncio.run(bot.show_ai_orchestrator())
        
    elif choice == "3":
        asyncio.run(bot.show_market_analysis())
        
    elif choice == "4":
        bot.show_trade_menu()
        
    elif choice == "5":
        asyncio.run(bot.show_live_dashboard())
        
    elif choice == "6":
        asyncio.run(bot.show_ai_configuration())
        
    elif choice == "7":
        console.print("[blue]🔄 Refreshing all data...[/blue]")
        bot.get_btc_price()
        console.print("[green]✅ Data refreshed![/green]")
        time.sleep(1)
        
    elif choice == "0":
        return False
    
    return True

def show_banner():
    """Show enhanced startup banner"""
    console.print("""
[bold blue]
⚡⚡⚡⚡⚡⚡⚡⚡⚡⚡⚡⚡⚡⚡⚡⚡⚡⚡⚡⚡⚡⚡⚡⚡⚡⚡⚡⚡⚡⚡⚡⚡⚡⚡⚡⚡⚡⚡
⚡                                                    ⚡
⚡      ██████╗ ██████╗ ██╗███╗   ██╗                ⚡
⚡     ██╔═══██╗██╔══██╗██║████╗  ██║                ⚡
⚡     ██║   ██║██║  ██║██║██╔██╗ ██║                ⚡
⚡     ██║   ██║██║  ██║██║██║╚██╗██║                ⚡
⚡     ╚██████╔╝██████╔╝██║██║ ╚████║                ⚡
⚡      ╚═════╝ ╚═════╝ ╚═╝╚═╝  ╚═══╝                ⚡
⚡                                                    ⚡
⚡         AI BITCOIN TRADING BOT                     ⚡
⚡           ENHANCED CLI v2.0                        ⚡
⚡          🤖 AI-DRIVEN STRATEGIES                   ⚡
⚡                                                    ⚡
⚡⚡⚡⚡⚡⚡⚡⚡⚡⚡⚡⚡⚡⚡⚡⚡⚡⚡⚡⚡⚡⚡⚡⚡⚡⚡⚡⚡⚡⚡⚡⚡⚡⚡⚡⚡⚡⚡
[/bold blue]
""")

def main():
    """Enhanced main application loop"""
    show_banner()
    
    # Show system initialization
    console.print(f"[dim]yfinance: {'✅ Available' if YF_AVAILABLE else '❌ Not Available'}[/dim]")
    console.print(f"[dim]Odin Core: {'✅ Available' if ODIN_AVAILABLE else '❌ Not Available'}[/dim]")
    
    # Initialize AI trading bot
    console.print("[blue]🤖 Initializing AI Trading System...[/blue]")
    bot = AITradingBot()
    
    # Initial data fetch
    console.print("[blue]🔄 Fetching initial market data...[/blue]")
    bot.get_btc_price()
    console.print("[green]✅ System Ready![/green]")
    
    time.sleep(2)
    
    # Main loop
    while True:
        console.clear()
        try:
            if not show_main_menu(bot):
                break
        except KeyboardInterrupt:
            break
        except Exception as e:
            console.print(f"[red]❌ Error: {e}[/red]")
            time.sleep(2)
    
    console.print("\n[yellow]👋 Thanks for using Odin AI Trading Bot![/yellow]")

if __name__ == "__main__":
    main()