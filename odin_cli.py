#!/usr/bin/env python3
"""
Odin Trading Bot - Clean CLI Interface with AI Integration
Simple, functional, and reliable command line interface
"""

import time
import sys
import os
from datetime import datetime, timezone, timedelta
from typing import Dict, Optional

# Rich library for clean output
try:
    from rich.console import Console
    from rich.table import Table
    from rich.panel import Panel
    from rich.prompt import Prompt, Confirm
    from rich.text import Text
    from rich import box
    from rich.layout import Layout
    from rich.live import Live
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
    RICH_AVAILABLE = True

# Data sources
try:
    import yfinance as yf
    YF_AVAILABLE = True
except ImportError:
    yf = None
    YF_AVAILABLE = False

# AI Components with proper error handling
try:
    from odin.core.enhanced_data_collector import EnhancedBitcoinDataCollector
    COLLECTOR_AVAILABLE = True
except ImportError as e:
    print(f"⚠️  Enhanced data collector unavailable: {e}")
    COLLECTOR_AVAILABLE = False

try:
    from odin.strategies.ai_adaptive import AIAdaptiveStrategy
    AI_STRATEGY_AVAILABLE = True
except ImportError as e:
    print(f"⚠️  AI adaptive strategy unavailable: {e}")
    AI_STRATEGY_AVAILABLE = False

try:
    from odin.ai.regime_detection.regime_detector import RegimeDetector
    REGIME_DETECTOR_AVAILABLE = True
except ImportError as e:
    print(f"⚠️  Regime detector unavailable: {e}")
    REGIME_DETECTOR_AVAILABLE = False

# Core models import with fallback
try:
    from odin.core.models import PriceData
    MODELS_AVAILABLE = True
except ImportError:
    try:
        from core.models import PriceData
        MODELS_AVAILABLE = True
    except ImportError:
        # Create minimal PriceData class as fallback
        from dataclasses import dataclass
        from datetime import datetime
        from typing import Optional
        
        @dataclass
        class PriceData:
            timestamp: datetime
            price: float
            volume: Optional[float] = None
            
        MODELS_AVAILABLE = False

console = Console()

class OdinBot:
    """Simple Odin trading bot interface with AI integration"""
    
    def __init__(self):
        self.portfolio = {"btc": 0.25, "usd": 5000.0}
        self.strategies = {
            "Moving Average": {"active": False, "pnl": 0.0},
            "RSI Strategy": {"active": False, "pnl": 0.0},
            "ML Enhanced": {"active": False, "pnl": 0.0}
        }
        self.current_price = None
        self.last_update = None
        self.collector = None
        self.ai_strategy = None
        self.regime_detector = None
        
        # Initialize AI components if available
        self._initialize_ai_components()
    
    def _initialize_ai_components(self):
        """Initialize AI components with proper error handling"""
        try:
            # Initialize data collector
            if COLLECTOR_AVAILABLE:
                try:
                    self.collector = EnhancedBitcoinDataCollector("data/bitcoin_enhanced.db")
                    console.print("[green]✅ Enhanced data collector initialized[/green]")
                except Exception as e:
                    console.print(f"[red]❌ Data collector init failed: {e}[/red]")
                    self.collector = None
            
            # Initialize AI strategy
            if AI_STRATEGY_AVAILABLE:
                try:
                    self.ai_strategy = AIAdaptiveStrategy()
                    console.print("[green]✅ AI adaptive strategy initialized[/green]")
                    self.strategies["AI Adaptive"] = {"active": False, "pnl": 0.0}
                except Exception as e:
                    console.print(f"[red]❌ AI strategy init failed: {e}[/red]")
                    self.ai_strategy = None
            
            # Initialize regime detector
            if REGIME_DETECTOR_AVAILABLE:
                try:
                    self.regime_detector = RegimeDetector()
                    console.print("[green]✅ Regime detector initialized[/green]")
                except Exception as e:
                    console.print(f"[red]❌ Regime detector init failed: {e}[/red]")
                    self.regime_detector = None
                    
        except Exception as e:
            console.print(f"[red]❌ AI initialization failed: {e}[/red]")
    
    def get_btc_price(self) -> float:
        """Get Bitcoin price with simple fallback"""
        try:
            import requests
            response = requests.get("https://api.coingecko.com/api/v3/simple/price?ids=bitcoin&vs_currencies=usd", timeout=5)
            if response.status_code == 200:
                price = float(response.json()['bitcoin']['usd'])
                self.current_price = price
                self.last_update = datetime.now()
                return price
        except:
            pass
        return self.current_price or 50000.0  # Reasonable fallback
    
    def get_portfolio_value(self) -> float:
        """Calculate total portfolio value"""
        btc_price = self.get_btc_price()
        btc_value = self.portfolio["btc"] * btc_price
        return btc_value + self.portfolio["usd"]
    
    def show_header(self):
        """Show clean header"""
        price = self.get_btc_price()
        portfolio_val = self.get_portfolio_value()
        
        header = Text()
        header.append("⚡ ODIN TRADING BOT ⚡\n", style="bold blue")
        header.append(f"Bitcoin: ${price:,.2f} | Portfolio: ${portfolio_val:,.2f}", style="green")
        
        if self.last_update:
            time_str = self.last_update.strftime("%H:%M:%S")
            header.append(f" | Updated: {time_str}", style="dim")
        
        console.print(Panel(header, box=box.ROUNDED, border_style="blue"))
    
    def show_portfolio(self):
        """Show portfolio table"""
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
        
        btc_alloc = (btc_value / total_value) * 100 if total_value > 0 else 0
        usd_alloc = (usd_balance / total_value) * 100 if total_value > 0 else 0
        
        table.add_row("Bitcoin", f"{btc_balance:.6f} BTC", f"${btc_value:,.2f}", f"{btc_alloc:.1f}%")
        table.add_row("USD", f"${usd_balance:,.2f}", f"${usd_balance:,.2f}", f"{usd_alloc:.1f}%")
        table.add_row("[bold]Total", "", f"[bold]${total_value:,.2f}", "[bold]100.0%")
        
        console.print(table)
    
    def show_strategies(self):
        """Show strategy status"""
        table = Table(title="🤖 Trading Strategies", box=box.SIMPLE)
        table.add_column("Strategy", style="cyan")
        table.add_column("Status", style="white")
        table.add_column("P&L", style="green")
        
        for name, data in self.strategies.items():
            status = "🟢 Active" if data["active"] else "⚪ Inactive"
            pnl_color = "green" if data["pnl"] >= 0 else "red"
            pnl_text = f"[{pnl_color}]${data['pnl']:+.2f}[/{pnl_color}]"
            
            table.add_row(name, status, pnl_text)
        
        console.print(table)
    
    def show_market_data(self):
        """Show market information with AI insights"""
        price = self.get_btc_price()
        
        table = Table(title="📈 Market Data", box=box.SIMPLE)
        table.add_column("Metric", style="cyan")
        table.add_column("Value", style="white")
        
        table.add_row("Current Price", f"${price:,.2f}")
        table.add_row("Market Cap", f"${price * 19.7e6 / 1e9:.0f}B")
        table.add_row("Data Source", "yfinance" if YF_AVAILABLE else "Fallback")
        
        # Add AI insights if available
        if self.collector:
            try:
                ml_data = self.collector.get_ml_ready_features(lookback_days=1)
                if not ml_data.empty:
                    latest = ml_data.iloc[-1]
                    if hasattr(latest, 'rsi_14') and latest.rsi_14 is not None:
                        table.add_row("RSI (14)", f"{latest.rsi_14:.1f}")
                    if hasattr(latest, 'volatility_20') and latest.volatility_20 is not None:
                        table.add_row("Volatility", f"{latest.volatility_20:.3f}")
            except Exception as e:
                table.add_row("AI Data", f"Error: {e}")
        
        # Add regime detection if available
        if self.regime_detector and MODELS_AVAILABLE:
            try:
                # Create dummy price data for regime detection
                dummy_data = []
                for i in range(50):
                    dummy_data.append(PriceData(
                        timestamp=datetime.now() - timedelta(minutes=50-i),
                        price=price + (i-25) * 10,
                        volume=1000
                    ))
                
                import asyncio
                regime_result = asyncio.run(self.regime_detector.detect_regime(dummy_data))
                current_regime = regime_result.get("current_regime", "unknown")
                confidence = regime_result.get("confidence", 0)
                
                table.add_row("Market Regime", f"{current_regime} ({confidence:.2f})")
                
            except Exception as e:
                table.add_row("Market Regime", f"Error: {e}")
        
        console.print(table)
    
    def toggle_strategy(self, strategy_name: str):
        """Toggle strategy on/off"""
        if strategy_name in self.strategies:
            current = self.strategies[strategy_name]["active"]
            self.strategies[strategy_name]["active"] = not current
            
            status = "started" if not current else "stopped"
            color = "green" if not current else "red"
            console.print(f"[{color}]✅ {strategy_name} {status}[/{color}]")
        else:
            console.print(f"[red]❌ Strategy '{strategy_name}' not found[/red]")


def show_main_menu(bot: OdinBot):
    """Show main menu and handle selection"""
    bot.show_header()
    
    console.print("\n[cyan]═══ MAIN MENU ═══[/cyan]")
    console.print("1. 💰 Show Portfolio")
    console.print("2. 🤖 Strategy Control")
    console.print("3. 📈 Market Data")
    console.print("4. 🔄 Refresh Data")
    console.print("5. 💱 Quick Trade (Demo)")
    console.print("6. 📊 Live Dashboard")
    if bot.ai_strategy:
        console.print("7. 🧠 AI Analytics")
    console.print("0. 🚪 Exit")
    
    choices = ["0","1","2","3","4","5","6"] + (["7"] if bot.ai_strategy else [])
    choice = Prompt.ask("\nChoose option", choices=choices, default="1")
    
    if choice == "1":
        console.clear()
        bot.show_header()
        bot.show_portfolio()
        input("\nPress Enter to continue...")
        
    elif choice == "2":
        show_strategy_menu(bot)
        
    elif choice == "3":
        console.clear()
        bot.show_header()
        bot.show_market_data()
        input("\nPress Enter to continue...")
        
    elif choice == "4":
        console.print("[blue]🔄 Refreshing data...[/blue]")
        bot.get_btc_price()
        console.print("[green]✅ Data refreshed![/green]")
        time.sleep(1)
        
    elif choice == "5":
        show_trade_menu(bot)
        
    elif choice == "6":
        show_live_dashboard(bot)
        
    elif choice == "7" and bot.ai_strategy:
        show_ai_analytics(bot)
        
    elif choice == "0":
        return False
    
    return True

def show_strategy_menu(bot: OdinBot):
    """Show strategy control menu with AI options"""
    while True:
        console.clear()
        bot.show_header()
        bot.show_strategies()
        
        console.print("\n[cyan]═══ STRATEGY CONTROL ═══[/cyan]")
        console.print("1. Toggle Moving Average")
        console.print("2. Toggle RSI Strategy") 
        console.print("3. Toggle ML Enhanced")
        if bot.ai_strategy:
            console.print("4. Toggle AI Adaptive")
            console.print("5. AI Strategy Info")
            console.print("6. Stop All Strategies")
        else:
            console.print("4. Stop All Strategies")
        console.print("0. Back to Main Menu")
        
        choices = ["0","1","2","3","4"] + (["5","6"] if bot.ai_strategy else [])
        choice = Prompt.ask("\nChoose option", choices=choices, default="0")
        
        if choice == "1":
            bot.toggle_strategy("Moving Average")
            time.sleep(1)
        elif choice == "2":
            bot.toggle_strategy("RSI Strategy")
            time.sleep(1)
        elif choice == "3":
            bot.toggle_strategy("ML Enhanced")
            time.sleep(1)
        elif choice == "4" and bot.ai_strategy:
            bot.toggle_strategy("AI Adaptive")
            time.sleep(1)
        elif choice == "5" and bot.ai_strategy:
            show_ai_strategy_info(bot)
        elif choice == "6" and bot.ai_strategy:
            for strategy in bot.strategies:
                bot.strategies[strategy]["active"] = False
            console.print("[red]🛑 All strategies stopped[/red]")
            time.sleep(1)
        elif choice == "4" and not bot.ai_strategy:
            for strategy in bot.strategies:
                bot.strategies[strategy]["active"] = False
            console.print("[red]🛑 All strategies stopped[/red]")
            time.sleep(1)
        elif choice == "0":
            break

def show_ai_strategy_info(bot: OdinBot):
    """Show AI strategy information"""
    console.clear()
    bot.show_header()
    
    if not bot.ai_strategy:
        console.print("[red]❌ AI strategy not available[/red]")
        input("\nPress Enter to continue...")
        return
    
    try:
        console.print("\n[cyan]═══ AI STRATEGY INFO ═══[/cyan]")
        
        # Show basic AI strategy status
        ai_active = bot.strategies.get("AI Adaptive", {}).get("active", False)
        console.print(f"[bold]Status:[/bold] {'🟢 Active' if ai_active else '⚪ Inactive'}")
        
        # Try to get AI analytics
        try:
            analytics = bot.ai_strategy.get_ai_analytics()
            
            # System status
            system_status = analytics.get("system_status", {})
            console.print(f"[bold]Initialization:[/bold] {'✅ Complete' if system_status.get('initialization_complete', False) else '⚠️ Incomplete'}")
            console.print(f"[bold]Data Points Processed:[/bold] {system_status.get('data_points_processed', 0)}")
            
            # Regime detection
            regime_info = analytics.get("regime_detection", {})
            current_regime = regime_info.get("current_regime", "unknown")
            confidence = regime_info.get("confidence", 0)
            console.print(f"[bold]Current Regime:[/bold] {current_regime} ({confidence:.2%})")
            
            # Strategy management
            strategy_mgmt = analytics.get("strategy_management", {})
            active_strategies = strategy_mgmt.get("active_strategies", [])
            console.print(f"[bold]Active AI Sub-strategies:[/bold] {len(active_strategies)}")
            
            # Performance
            performance = analytics.get("performance", {})
            if performance and performance != {"status": "insufficient_data"}:
                total_signals = performance.get("total_signals", 0)
                avg_confidence = performance.get("avg_confidence", 0)
                console.print(f"[bold]Total Signals Generated:[/bold] {total_signals}")
                console.print(f"[bold]Average Confidence:[/bold] {avg_confidence:.2%}")
            
        except Exception as e:
            console.print(f"[yellow]⚠️ Analytics unavailable: {e}[/yellow]")
        
    except Exception as e:
        console.print(f"[red]❌ AI strategy info error: {e}[/red]")
    
    input("\nPress Enter to continue...")

def show_ai_analytics(bot: OdinBot):
    """Show comprehensive AI analytics"""
    console.clear()
    bot.show_header()
    
    if not bot.ai_strategy:
        console.print("[red]❌ AI strategy not available[/red]")
        input("\nPress Enter to continue...")
        return
    
    try:
        analytics = bot.ai_strategy.get_ai_analytics()
        
        console.print("\n[cyan]═══ AI ANALYTICS DASHBOARD ═══[/cyan]")
        
        # Create analytics table
        table = Table(title="🧠 AI Performance Metrics", box=box.SIMPLE)
        table.add_column("Category", style="cyan")
        table.add_column("Metric", style="white")
        table.add_column("Value", style="green")
        
        # Regime Detection Metrics
        regime_info = analytics.get("regime_detection", {})
        table.add_row("Regime Detection", "Current Regime", regime_info.get("current_regime", "unknown"))
        table.add_row("", "Confidence", f"{regime_info.get('confidence', 0):.2%}")
        table.add_row("", "Total Detections", str(regime_info.get("detection_count", 0)))
        
        # Strategy Management
        strategy_info = analytics.get("strategy_management", {})
        table.add_row("Strategy Mgmt", "Active Strategies", str(strategy_info.get("strategy_count", 0)))
        
        # Performance Metrics
        performance = analytics.get("performance", {})
        if performance and performance != {"status": "insufficient_data"}:
            table.add_row("Performance", "Total Signals", str(performance.get("total_signals", 0)))
            table.add_row("", "Avg Confidence", f"{performance.get('avg_confidence', 0):.2%}")
            table.add_row("", "Avg Strength", f"{performance.get('avg_strength', 0):.2%}")
            
            # Signal distribution
            signal_dist = performance.get("signal_distribution", {})
            table.add_row("", "Buy Signals", str(signal_dist.get("buy_signals", 0)))
            table.add_row("", "Sell Signals", str(signal_dist.get("sell_signals", 0)))
            table.add_row("", "Hold Signals", str(signal_dist.get("hold_signals", 0)))
        
        # Model Health
        health = analytics.get("model_health", {})
        if health and "error" not in health:
            health_score = health.get("overall_health_score", 0)
            health_status = health.get("health_status", "unknown")
            table.add_row("Model Health", "Overall Score", f"{health_score:.1%}")
            table.add_row("", "Status", health_status)
            table.add_row("", "Regime Model", "✅ Loaded" if health.get("regime_model_loaded", False) else "❌ Missing")
            table.add_row("", "Strategy Manager", "✅ Active" if health.get("strategy_manager_active", False) else "❌ Inactive")
        
        console.print(table)
        
        # Show regime distribution if available
        regime_dist = regime_info.get("regime_distribution_30d", {})
        if regime_dist:
            console.print("\n[bold]📊 Regime Distribution (30 days):[/bold]")
            for regime, percentage in regime_dist.items():
                console.print(f"  {regime}: {percentage:.1%}")
        
        # Show strategy recommendations if available
        try:
            recommendations = bot.ai_strategy.get_strategy_recommendations()
            if recommendations and "error" not in recommendations:
                console.print(f"\n[bold]💡 Current Regime:[/bold] {recommendations.get('current_regime', 'unknown')}")
                console.print(f"[bold]🎯 Regime Confidence:[/bold] {recommendations.get('regime_confidence', 0):.2%}")
        except:
            pass
        
    except Exception as e:
        console.print(f"[red]❌ Analytics error: {e}[/red]")
    
    input("\nPress Enter to continue...")

def show_trade_menu(bot: OdinBot):
    """Show trading menu"""
    console.clear()
    bot.show_header()
    
    price = bot.get_btc_price()
    
    console.print(f"\n[white]Current BTC Price: [bold green]${price:,.2f}[/bold green][/white]")
    console.print(f"[white]Your BTC: [bold]{bot.portfolio['btc']:.6f}[/bold][/white]")
    console.print(f"[white]Your USD: [bold]${bot.portfolio['usd']:,.2f}[/bold][/white]")
    
    console.print("\n[yellow]⚠️ DEMO MODE - No real trades executed[/yellow]")
    console.print("\n[cyan]═══ QUICK TRADE ═══[/cyan]")
    console.print("1. 🟢 Buy $100 worth of BTC")
    console.print("2. 🟢 Buy $500 worth of BTC")
    console.print("3. 🔴 Sell 0.001 BTC")
    console.print("4. 🔴 Sell 0.01 BTC")
    console.print("0. Back to Main Menu")
    
    choice = Prompt.ask("\nChoose option", choices=["0","1","2","3","4"], default="0")
    
    if choice == "1":
        btc_amount = 100 / price
        console.print(f"[green]✅ Demo BUY: {btc_amount:.6f} BTC for $100[/green]")
    elif choice == "2":
        btc_amount = 500 / price  
        console.print(f"[green]✅ Demo BUY: {btc_amount:.6f} BTC for $500[/green]")
    elif choice == "3":
        usd_amount = 0.001 * price
        console.print(f"[red]✅ Demo SELL: 0.001 BTC for ${usd_amount:.2f}[/red]")
    elif choice == "4":
        usd_amount = 0.01 * price
        console.print(f"[red]✅ Demo SELL: 0.01 BTC for ${usd_amount:.2f}[/red]")
    
    if choice != "0":
        time.sleep(2)

def show_live_dashboard(bot: OdinBot):
    """Show live updating dashboard"""
    console.clear()
    console.print(Panel(
        "[bold blue]📊 Live Dashboard[/bold blue]\n"
        "[dim]Auto-refreshing every 10 seconds - Press Ctrl+C to exit[/dim]",
        border_style="blue"
    ))
    
    def create_dashboard_layout():
        layout = Layout()
        layout.split_column(
            Layout(create_header_panel(bot), size=4),
            Layout(name="main")
        )
        layout["main"].split_row(
            Layout(create_portfolio_panel(bot)),
            Layout(create_strategy_panel(bot))
        )
        return layout
    
    try:
        with Live(create_dashboard_layout(), refresh_per_second=0.1, console=console) as live:
            refresh_counter = 0
            while True:
                time.sleep(1)
                refresh_counter += 1
                
                # Refresh data every 10 seconds
                if refresh_counter >= 10:
                    bot.get_btc_price()
                    refresh_counter = 0
                
                live.update(create_dashboard_layout())
                
    except KeyboardInterrupt:
        console.print("\n[yellow]Dashboard stopped[/yellow]")

def create_header_panel(bot: OdinBot) -> Panel:
    """Create header panel for dashboard"""
    price = bot.get_btc_price()
    portfolio_val = bot.get_portfolio_value()
    
    header_text = Text()
    header_text.append("⚡ ODIN LIVE DASHBOARD ⚡\n", style="bold blue")
    header_text.append(f"Bitcoin: ${price:,.2f} | Portfolio: ${portfolio_val:,.2f}", style="green")
    
    if bot.last_update:
        time_str = bot.last_update.strftime("%H:%M:%S")
        header_text.append(f" | Last Update: {time_str}", style="dim")
    
    return Panel(header_text, box=box.ROUNDED, border_style="blue")

def create_portfolio_panel(bot: OdinBot) -> Panel:
    """Create portfolio panel for dashboard"""
    table = Table(box=box.SIMPLE, show_header=False)
    table.add_column("", style="cyan")
    table.add_column("", style="white")
    
    btc_price = bot.get_btc_price()
    btc_value = bot.portfolio["btc"] * btc_price
    total_value = btc_value + bot.portfolio["usd"]
    
    table.add_row("💰 Portfolio Value", f"${total_value:,.2f}")
    table.add_row("₿ Bitcoin", f"{bot.portfolio['btc']:.6f} BTC")
    table.add_row("💵 USD", f"${bot.portfolio['usd']:,.2f}")
    table.add_row("📊 BTC Value", f"${btc_value:,.2f}")
    
    return Panel(table, title="💼 Portfolio", border_style="green")

def create_strategy_panel(bot: OdinBot) -> Panel:
    """Create strategy panel for dashboard"""
    table = Table(box=box.SIMPLE, show_header=False)
    table.add_column("", style="cyan")
    table.add_column("", style="white")
    
    active_count = sum(1 for s in bot.strategies.values() if s["active"])
    total_pnl = sum(s["pnl"] for s in bot.strategies.values())
    
    table.add_row("🤖 Active Strategies", f"{active_count}/{len(bot.strategies)}")
    table.add_row("📈 Total P&L", f"${total_pnl:+.2f}")
    
    for name, data in bot.strategies.items():
        status = "🟢" if data["active"] else "⚪"
        table.add_row(f"{status} {name}", f"${data['pnl']:+.2f}")
    
    return Panel(table, title="🤖 Strategies", border_style="purple")

def show_banner():
    """Show startup banner"""
    banner_text = """
⚡⚡⚡⚡⚡⚡⚡⚡⚡⚡⚡⚡⚡⚡⚡⚡⚡⚡⚡⚡
⚡                                             ⚡
⚡      ██████╗ ██████╗ ██╗███╗   ██╗          ⚡
⚡     ██╔═══██╗██╔══██╗██║████╗  ██║          ⚡
⚡     ██║   ██║██║  ██║██║██╔██╗ ██║          ⚡
⚡     ██║   ██║██║  ██║██║██║╚██╗██║          ⚡
⚡     ╚██████╔╝██████╔╝██║██║ ╚████║          ⚡
⚡      ╚═════╝ ╚═════╝ ╚═╝╚═╝  ╚═══╝          ⚡
⚡                                             ⚡
⚡         BITCOIN TRADING BOT                 ⚡
⚡            AI-ENHANCED CLI v2.0             ⚡
⚡                                             ⚡
⚡⚡⚡⚡⚡⚡⚡⚡⚡⚡⚡⚡⚡⚡⚡⚡⚡⚡⚡⚡
"""
    console.print(banner_text, style="bold blue")

def main():
    """Main application loop with AI status"""
    show_banner()
    
    # Show system status with AI components
    console.print(f"[dim]yfinance: {'✅ Available' if YF_AVAILABLE else '❌ Not Available'}[/dim]")
    console.print(f"[dim]Enhanced Collector: {'✅ Available' if COLLECTOR_AVAILABLE else '❌ Not Available'}[/dim]")
    console.print(f"[dim]AI Strategy: {'✅ Available' if AI_STRATEGY_AVAILABLE else '❌ Not Available'}[/dim]")
    console.print(f"[dim]Regime Detector: {'✅ Available' if REGIME_DETECTOR_AVAILABLE else '❌ Not Available'}[/dim]")
    console.print(f"[dim]Core Models: {'✅ Available' if MODELS_AVAILABLE else '❌ Using Fallback'}[/dim]")
    
    # Show AI readiness status
    ai_components_ready = sum([COLLECTOR_AVAILABLE, AI_STRATEGY_AVAILABLE, REGIME_DETECTOR_AVAILABLE])
    if ai_components_ready >= 2:
        console.print("[green]🤖 AI Features: Ready[/green]")
    elif ai_components_ready >= 1:
        console.print("[yellow]🤖 AI Features: Partially Available[/yellow]")
    else:
        console.print("[red]🤖 AI Features: Unavailable[/red]")
    
    bot = OdinBot()
    
    # Initial data fetch
    console.print("[blue]🔄 Fetching initial data...[/blue]")
    bot.get_btc_price()
    console.print("[green]✅ Ready![/green]")
    
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
            console.print("[dim]Press Enter to continue or Ctrl+C to exit...[/dim]")
            try:
                input()
            except KeyboardInterrupt:
                break
    
    console.print("\n[yellow]👋 Thanks for using Odin![/yellow]")
    console.print("[dim]AI-Enhanced Bitcoin Trading Bot v2.0[/dim]")

if __name__ == "__main__":
    main()#!/usr/bin/env python3
"""
Odin Trading Bot - Clean CLI Interface with AI Integration
Simple, functional, and reliable command line interface
"""

import time
import sys
import os
from datetime import datetime, timezone, timedelta
from typing import Dict, Optional

# Rich library for clean output
try:
    from rich.console import Console
    from rich.table import Table
    from rich.panel import Panel
    from rich.prompt import Prompt, Confirm
    from rich.text import Text
    from rich import box
    from rich.layout import Layout
    from rich.live import Live
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
    RICH_AVAILABLE = True

# Data sources
try:
    import yfinance as yf
    YF_AVAILABLE = True
except ImportError:
    yf = None
    YF_AVAILABLE = False

# AI Components with proper error handling
try:
    from odin.core.enhanced_data_collector import EnhancedBitcoinDataCollector
    COLLECTOR_AVAILABLE = True
except ImportError as e:
    print(f"⚠️  Enhanced data collector unavailable: {e}")
    COLLECTOR_AVAILABLE = False

try:
    from odin.strategies.ai_adaptive import AIAdaptiveStrategy
    AI_STRATEGY_AVAILABLE = True
except ImportError as e:
    print(f"⚠️  AI adaptive strategy unavailable: {e}")
    AI_STRATEGY_AVAILABLE = False

try:
    from odin.ai.regime_detection.regime_detector import RegimeDetector
    REGIME_DETECTOR_AVAILABLE = True
except ImportError as e:
    print(f"⚠️  Regime detector unavailable: {e}")
    REGIME_DETECTOR_AVAILABLE = False

# Core models import with fallback
try:
    from odin.core.models import PriceData
    MODELS_AVAILABLE = True
except ImportError:
    try:
        from core.models import PriceData
        MODELS_AVAILABLE = True
    except ImportError:
        # Create minimal PriceData class as fallback
        from dataclasses import dataclass
        from datetime import datetime
        from typing import Optional
        
        @dataclass
        class PriceData:
            timestamp: datetime
            price: float
            volume: Optional[float] = None
            
        MODELS_AVAILABLE = False

console = Console()

class OdinBot:
    """Simple Odin trading bot interface with AI integration"""
    
    def __init__(self):
        self.portfolio = {"btc": 0.25, "usd": 5000.0}
        self.strategies = {
            "Moving Average": {"active": False, "pnl": 0.0},
            "RSI Strategy": {"active": False, "pnl": 0.0},
            "ML Enhanced": {"active": False, "pnl": 0.0}
        }
        self.current_price = None
        self.last_update = None
        self.collector = None
        self.ai_strategy = None
        self.regime_detector = None
        
        # Initialize AI components if available
        self._initialize_ai_components()
    
    def _initialize_ai_components(self):
        """Initialize AI components with proper error handling"""
        try:
            # Initialize data collector
            if COLLECTOR_AVAILABLE:
                try:
                    self.collector = EnhancedBitcoinDataCollector("data/bitcoin_enhanced.db")
                    console.print("[green]✅ Enhanced data collector initialized[/green]")
                except Exception as e:
                    console.print(f"[red]❌ Data collector init failed: {e}[/red]")
                    self.collector = None
            
            # Initialize AI strategy
            if AI_STRATEGY_AVAILABLE:
                try:
                    self.ai_strategy = AIAdaptiveStrategy()
                    console.print("[green]✅ AI adaptive strategy initialized[/green]")
                    self.strategies["AI Adaptive"] = {"active": False, "pnl": 0.0}
                except Exception as e:
                    console.print(f"[red]❌ AI strategy init failed: {e}[/red]")
                    self.ai_strategy = None
            
            # Initialize regime detector
            if REGIME_DETECTOR_AVAILABLE:
                try:
                    self.regime_detector = RegimeDetector()
                    console.print("[green]✅ Regime detector initialized[/green]")
                except Exception as e:
                    console.print(f"[red]❌ Regime detector init failed: {e}[/red]")
                    self.regime_detector = None
                    
        except Exception as e:
            console.print(f"[red]❌ AI initialization failed: {e}[/red]")
    
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
    
    def show_header(self):
        """Show clean header"""
        price = self.get_btc_price()
        portfolio_val = self.get_portfolio_value()
        
        header = Text()
        header.append("⚡ ODIN TRADING BOT ⚡\n", style="bold blue")
        header.append(f"Bitcoin: ${price:,.2f} | Portfolio: ${portfolio_val:,.2f}", style="green")
        
        if self.last_update:
            time_str = self.last_update.strftime("%H:%M:%S")
            header.append(f" | Updated: {time_str}", style="dim")
        
        console.print(Panel(header, box=box.ROUNDED, border_style="blue"))
    
    def show_portfolio(self):
        """Show portfolio table"""
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
        
        btc_alloc = (btc_value / total_value) * 100 if total_value > 0 else 0
        usd_alloc = (usd_balance / total_value) * 100 if total_value > 0 else 0
        
        table.add_row("Bitcoin", f"{btc_balance:.6f} BTC", f"${btc_value:,.2f}", f"{btc_alloc:.1f}%")
        table.add_row("USD", f"${usd_balance:,.2f}", f"${usd_balance:,.2f}", f"{usd_alloc:.1f}%")
        table.add_row("[bold]Total", "", f"[bold]${total_value:,.2f}", "[bold]100.0%")
        
        console.print(table)
    
    def show_strategies(self):
        """Show strategy status"""
        table = Table(title="🤖 Trading Strategies", box=box.SIMPLE)
        table.add_column("Strategy", style="cyan")
        table.add_column("Status", style="white")
        table.add_column("P&L", style="green")
        
        for name, data in self.strategies.items():
            status = "🟢 Active" if data["active"] else "⚪ Inactive"
            pnl_color = "green" if data["pnl"] >= 0 else "red"
            pnl_text = f"[{pnl_color}]${data['pnl']:+.2f}[/{pnl_color}]"
            
            table.add_row(name, status, pnl_text)
        
        console.print(table)
    
    def show_market_data(self):
        """Show market information with AI insights"""
        price = self.get_btc_price()
        
        table = Table(title="📈 Market Data", box=box.SIMPLE)
        table.add_column("Metric", style="cyan")
        table.add_column("Value", style="white")
        
        table.add_row("Current Price", f"${price:,.2f}")
        table.add_row("Market Cap", f"${price * 19.7e6 / 1e9:.0f}B")
        table.add_row("Data Source", "yfinance" if YF_AVAILABLE else "Fallback")
        
        # Add AI insights if available
        if self.collector:
            try:
                ml_data = self.collector.get_ml_ready_features(lookback_days=1)
                if not ml_data.empty:
                    latest = ml_data.iloc[-1]
                    if hasattr(latest, 'rsi_14') and latest.rsi_14 is not None:
                        table.add_row("RSI (14)", f"{latest.rsi_14:.1f}")
                    if hasattr(latest, 'volatility_20') and latest.volatility_20 is not None:
                        table.add_row("Volatility", f"{latest.volatility_20:.3f}")
            except Exception as e:
                table.add_row("AI Data", f"Error: {e}")
        
        # Add regime detection if available
        if self.regime_detector and MODELS_AVAILABLE:
            try:
                # Create dummy price data for regime detection
                dummy_data = []
                for i in range(50):
                    dummy_data.append(PriceData(
                        timestamp=datetime.now() - timedelta(minutes=50-i),
                        price=price + (i-25) * 10,
                        volume=1000
                    ))
                
                import asyncio
                regime_result = asyncio.run(self.regime_detector.detect_regime(dummy_data))
                current_regime = regime_result.get("current_regime", "unknown")
                confidence = regime_result.get("confidence", 0)
                
                table.add_row("Market Regime", f"{current_regime} ({confidence:.2f})")
                
            except Exception as e:
                table.add_row("Market Regime", f"Error: {e}")
        
        console.print(table)
    
    def toggle_strategy(self, strategy_name: str):
        """Toggle strategy on/off"""
        if strategy_name in self.strategies:
            current = self.strategies[strategy_name]["active"]
            self.strategies[strategy_name]["active"] = not current
            
            status = "started" if not current else "stopped"
            color = "green" if not current else "red"
            console.print(f"[{color}]✅ {strategy_name} {status}[/{color}]")
        else:
            console.print(f"[red]❌ Strategy '{strategy_name}' not found[/red]")


def show_main_menu(bot: OdinBot):
    """Show main menu and handle selection"""
    bot.show_header()
    
    console.print("\n[cyan]═══ MAIN MENU ═══[/cyan]")
    console.print("1. 💰 Show Portfolio")
    console.print("2. 🤖 Strategy Control")
    console.print("3. 📈 Market Data")
    console.print("4. 🔄 Refresh Data")
    console.print("5. 💱 Quick Trade (Demo)")
    console.print("6. 📊 Live Dashboard")
    if bot.ai_strategy:
        console.print("7. 🧠 AI Analytics")
    console.print("0. 🚪 Exit")
    
    choices = ["0","1","2","3","4","5","6"] + (["7"] if bot.ai_strategy else [])
    choice = Prompt.ask("\nChoose option", choices=choices, default="1")
    
    if choice == "1":
        console.clear()
        bot.show_header()
        bot.show_portfolio()
        input("\nPress Enter to continue...")
        
    elif choice == "2":
        show_strategy_menu(bot)
        
    elif choice == "3":
        console.clear()
        bot.show_header()
        bot.show_market_data()
        input("\nPress Enter to continue...")
        
    elif choice == "4":
        console.print("[blue]🔄 Refreshing data...[/blue]")
        bot.get_btc_price()
        console.print("[green]✅ Data refreshed![/green]")
        time.sleep(1)
        
    elif choice == "5":
        show_trade_menu(bot)
        
    elif choice == "6":
        show_live_dashboard(bot)
        
    elif choice == "7" and bot.ai_strategy:
        show_ai_analytics(bot)
        
    elif choice == "0":
        return False
    
    return True

def show_strategy_menu(bot: OdinBot):
    """Show strategy control menu with AI options"""
    while True:
        console.clear()
        bot.show_header()
        bot.show_strategies()
        
        console.print("\n[cyan]═══ STRATEGY CONTROL ═══[/cyan]")
        console.print("1. Toggle Moving Average")
        console.print("2. Toggle RSI Strategy") 
        console.print("3. Toggle ML Enhanced")
        if bot.ai_strategy:
            console.print("4. Toggle AI Adaptive")
            console.print("5. AI Strategy Info")
            console.print("6. Stop All Strategies")
        else:
            console.print("4. Stop All Strategies")
        console.print("0. Back to Main Menu")
        
        choices = ["0","1","2","3","4"] + (["5","6"] if bot.ai_strategy else [])
        choice = Prompt.ask("\nChoose option", choices=choices, default="0")
        
        if choice == "1":
            bot.toggle_strategy("Moving Average")
            time.sleep(1)
        elif choice == "2":
            bot.toggle_strategy("RSI Strategy")
            time.sleep(1)
        elif choice == "3":
            bot.toggle_strategy("ML Enhanced")
            time.sleep(1)
        elif choice == "4" and bot.ai_strategy:
            bot.toggle_strategy("AI Adaptive")
            time.sleep(1)
        elif choice == "5" and bot.ai_strategy:
            show_ai_strategy_info(bot)
        elif choice == "6" and bot.ai_strategy:
            for strategy in bot.strategies:
                bot.strategies[strategy]["active"] = False
            console.print("[red]🛑 All strategies stopped[/red]")
            time.sleep(1)
        elif choice == "4" and not bot.ai_strategy:
            for strategy in bot.strategies:
                bot.strategies[strategy]["active"] = False
            console.print("[red]🛑 All strategies stopped[/red]")
            time.sleep(1)
        elif choice == "0":
            break

def show_ai_strategy_info(bot: OdinBot):
    """Show AI strategy information"""
    console.clear()
    bot.show_header()
    
    if not bot.ai_strategy:
        console.print("[red]❌ AI strategy not available[/red]")
        input("\nPress Enter to continue...")
        return
    
    try:
        console.print("\n[cyan]═══ AI STRATEGY INFO ═══[/cyan]")
        
        # Show basic AI strategy status
        ai_active = bot.strategies.get("AI Adaptive", {}).get("active", False)
        console.print(f"[bold]Status:[/bold] {'🟢 Active' if ai_active else '⚪ Inactive'}")
        
        # Try to get AI analytics
        try:
            analytics = bot.ai_strategy.get_ai_analytics()
            
            # System status
            system_status = analytics.get("system_status", {})
            console.print(f"[bold]Initialization:[/bold] {'✅ Complete' if system_status.get('initialization_complete', False) else '⚠️ Incomplete'}")
            console.print(f"[bold]Data Points Processed:[/bold] {system_status.get('data_points_processed', 0)}")
            
            # Regime detection
            regime_info = analytics.get("regime_detection", {})
            current_regime = regime_info.get("current_regime", "unknown")
            confidence = regime_info.get("confidence", 0)
            console.print(f"[bold]Current Regime:[/bold] {current_regime} ({confidence:.2%})")
            
            # Strategy management
            strategy_mgmt = analytics.get("strategy_management", {})
            active_strategies = strategy_mgmt.get("active_strategies", [])
            console.print(f"[bold]Active AI Sub-strategies:[/bold] {len(active_strategies)}")
            
            # Performance
            performance = analytics.get("performance", {})
            if performance and performance != {"status": "insufficient_data"}:
                total_signals = performance.get("total_signals", 0)
                avg_confidence = performance.get("avg_confidence", 0)
                console.print(f"[bold]Total Signals Generated:[/bold] {total_signals}")
                console.print(f"[bold]Average Confidence:[/bold] {avg_confidence:.2%}")
            
        except Exception as e:
            console.print(f"[yellow]⚠️ Analytics unavailable: {e}[/yellow]")
        
    except Exception as e:
        console.print(f"[red]❌ AI strategy info error: {e}[/red]")
    
    input("\nPress Enter to continue...")

def show_ai_analytics(bot: OdinBot):
    """Show comprehensive AI analytics"""
    console.clear()
    bot.show_header()
    
    if not bot.ai_strategy:
        console.print("[red]❌ AI strategy not available[/red]")
        input("\nPress Enter to continue...")
        return
    
    try:
        analytics = bot.ai_strategy.get_ai_analytics()
        
        console.print("\n[cyan]═══ AI ANALYTICS DASHBOARD ═══[/cyan]")
        
        # Create analytics table
        table = Table(title="🧠 AI Performance Metrics", box=box.SIMPLE)
        table.add_column("Category", style="cyan")
        table.add_column("Metric", style="white")
        table.add_column("Value", style="green")
        
        # Regime Detection Metrics
        regime_info = analytics.get("regime_detection", {})
        table.add_row("Regime Detection", "Current Regime", regime_info.get("current_regime", "unknown"))
        table.add_row("", "Confidence", f"{regime_info.get('confidence', 0):.2%}")
        table.add_row("", "Total Detections", str(regime_info.get("detection_count", 0)))
        
        # Strategy Management
        strategy_info = analytics.get("strategy_management", {})
        table.add_row("Strategy Mgmt", "Active Strategies", str(strategy_info.get("strategy_count", 0)))
        
        # Performance Metrics
        performance = analytics.get("performance", {})
        if performance and performance != {"status": "insufficient_data"}:
            table.add_row("Performance", "Total Signals", str(performance.get("total_signals", 0)))
            table.add_row("", "Avg Confidence", f"{performance.get('avg_confidence', 0):.2%}")
            table.add_row("", "Avg Strength", f"{performance.get('avg_strength', 0):.2%}")
            
            # Signal distribution
            signal_dist = performance.get("signal_distribution", {})
            table.add_row("", "Buy Signals", str(signal_dist.get("buy_signals", 0)))
            table.add_row("", "Sell Signals", str(signal_dist.get("sell_signals", 0)))
            table.add_row("", "Hold Signals", str(signal_dist.get("hold_signals", 0)))
        
        # Model Health
        health = analytics.get("model_health", {})
        if health and "error" not in health:
            health_score = health.get("overall_health_score", 0)
            health_status = health.get("health_status", "unknown")
            table.add_row("Model Health", "Overall Score", f"{health_score:.1%}")
            table.add_row("", "Status", health_status)
            table.add_row("", "Regime Model", "✅ Loaded" if health.get("regime_model_loaded", False) else "❌ Missing")
            table.add_row("", "Strategy Manager", "✅ Active" if health.get("strategy_manager_active", False) else "❌ Inactive")
        
        console.print(table)
        
        # Show regime distribution if available
        regime_dist = regime_info.get("regime_distribution_30d", {})
        if regime_dist:
            console.print("\n[bold]📊 Regime Distribution (30 days):[/bold]")
            for regime, percentage in regime_dist.items():
                console.print(f"  {regime}: {percentage:.1%}")
        
        # Show strategy recommendations if available
        try:
            recommendations = bot.ai_strategy.get_strategy_recommendations()
            if recommendations and "error" not in recommendations:
                console.print(f"\n[bold]💡 Current Regime:[/bold] {recommendations.get('current_regime', 'unknown')}")
                console.print(f"[bold]🎯 Regime Confidence:[/bold] {recommendations.get('regime_confidence', 0):.2%}")
        except:
            pass
        
    except Exception as e:
        console.print(f"[red]❌ Analytics error: {e}[/red]")
    
    input("\nPress Enter to continue...")

def show_trade_menu(bot: OdinBot):
    """Show trading menu"""
    console.clear()
    bot.show_header()
    
    price = bot.get_btc_price()
    
    console.print(f"\n[white]Current BTC Price: [bold green]${price:,.2f}[/bold green][/white]")
    console.print(f"[white]Your BTC: [bold]{bot.portfolio['btc']:.6f}[/bold][/white]")
    console.print(f"[white]Your USD: [bold]${bot.portfolio['usd']:,.2f}[/bold][/white]")
    
    console.print("\n[yellow]⚠️ DEMO MODE - No real trades executed[/yellow]")
    console.print("\n[cyan]═══ QUICK TRADE ═══[/cyan]")
    console.print("1. 🟢 Buy $100 worth of BTC")
    console.print("2. 🟢 Buy $500 worth of BTC")
    console.print("3. 🔴 Sell 0.001 BTC")
    console.print("4. 🔴 Sell 0.01 BTC")
    console.print("0. Back to Main Menu")
    
    choice = Prompt.ask("\nChoose option", choices=["0","1","2","3","4"], default="0")
    
    if choice == "1":
        btc_amount = 100 / price
        console.print(f"[green]✅ Demo BUY: {btc_amount:.6f} BTC for $100[/green]")
    elif choice == "2":
        btc_amount = 500 / price  
        console.print(f"[green]✅ Demo BUY: {btc_amount:.6f} BTC for $500[/green]")
    elif choice == "3":
        usd_amount = 0.001 * price
        console.print(f"[red]✅ Demo SELL: 0.001 BTC for ${usd_amount:.2f}[/red]")
    elif choice == "4":
        usd_amount = 0.01 * price
        console.print(f"[red]✅ Demo SELL: 0.01 BTC for ${usd_amount:.2f}[/red]")
    
    if choice != "0":
        time.sleep(2)

def show_live_dashboard(bot: OdinBot):
    """Show live updating dashboard"""
    console.clear()
    console.print(Panel(
        "[bold blue]📊 Live Dashboard[/bold blue]\n"
        "[dim]Auto-refreshing every 10 seconds - Press Ctrl+C to exit[/dim]",
        border_style="blue"
    ))
    
    def create_dashboard_layout():
        layout = Layout()
        layout.split_column(
            Layout(create_header_panel(bot), size=4),
            Layout(name="main")
        )
        layout["main"].split_row(
            Layout(create_portfolio_panel(bot)),
            Layout(create_strategy_panel(bot))
        )
        return layout
    
    try:
        with Live(create_dashboard_layout(), refresh_per_second=0.1, console=console) as live:
            refresh_counter = 0
            while True:
                time.sleep(1)
                refresh_counter += 1
                
                # Refresh data every 10 seconds
                if refresh_counter >= 10:
                    bot.get_btc_price()
                    refresh_counter = 0
                
                live.update(create_dashboard_layout())
                
    except KeyboardInterrupt:
        console.print("\n[yellow]Dashboard stopped[/yellow]")

def create_header_panel(bot: OdinBot) -> Panel:
    """Create header panel for dashboard"""
    price = bot.get_btc_price()
    portfolio_val = bot.get_portfolio_value()
    
    header_text = Text()
    header_text.append("⚡ ODIN LIVE DASHBOARD ⚡\n", style="bold blue")
    header_text.append(f"Bitcoin: ${price:,.2f} | Portfolio: ${portfolio_val:,.2f}", style="green")
    
    if bot.last_update:
        time_str = bot.last_update.strftime("%H:%M:%S")
        header_text.append(f" | Last Update: {time_str}", style="dim")
    
    return Panel(header_text, box=box.ROUNDED, border_style="blue")

def create_portfolio_panel(bot: OdinBot) -> Panel:
    """Create portfolio panel for dashboard"""
    table = Table(box=box.SIMPLE, show_header=False)
    table.add_column("", style="cyan")
    table.add_column("", style="white")
    
    btc_price = bot.get_btc_price()
    btc_value = bot.portfolio["btc"] * btc_price
    total_value = btc_value + bot.portfolio["usd"]
    
    table.add_row("💰 Portfolio Value", f"${total_value:,.2f}")
    table.add_row("₿ Bitcoin", f"{bot.portfolio['btc']:.6f} BTC")
    table.add_row("💵 USD", f"${bot.portfolio['usd']:,.2f}")
    table.add_row("📊 BTC Value", f"${btc_value:,.2f}")
    
    return Panel(table, title="💼 Portfolio", border_style="green")

def create_strategy_panel(bot: OdinBot) -> Panel:
    """Create strategy panel for dashboard"""
    table = Table(box=box.SIMPLE, show_header=False)
    table.add_column("", style="cyan")
    table.add_column("", style="white")
    
    active_count = sum(1 for s in bot.strategies.values() if s["active"])
    total_pnl = sum(s["pnl"] for s in bot.strategies.values())
    
    table.add_row("🤖 Active Strategies", f"{active_count}/{len(bot.strategies)}")
    table.add_row("📈 Total P&L", f"${total_pnl:+.2f}")
    
    for name, data in bot.strategies.items():
        status = "🟢" if data["active"] else "⚪"
        table.add_row(f"{status} {name}", f"${data['pnl']:+.2f}")
    
    return Panel(table, title="🤖 Strategies", border_style="purple")

def show_banner():
    """Show startup banner"""
    banner_text = """
⚡⚡⚡⚡⚡⚡⚡⚡⚡⚡⚡⚡⚡⚡⚡⚡⚡⚡⚡⚡
⚡                                             ⚡
⚡      ██████╗ ██████╗ ██╗███╗   ██╗          ⚡
⚡     ██╔═══██╗██╔══██╗██║████╗  ██║          ⚡
⚡     ██║   ██║██║  ██║██║██╔██╗ ██║          ⚡
⚡     ██║   ██║██║  ██║██║██║╚██╗██║          ⚡
⚡     ╚██████╔╝██████╔╝██║██║ ╚████║          ⚡
⚡      ╚═════╝ ╚═════╝ ╚═╝╚═╝  ╚═══╝          ⚡
⚡                                             ⚡
⚡         BITCOIN TRADING BOT                 ⚡
⚡            AI-ENHANCED CLI v2.0             ⚡
⚡                                             ⚡
⚡⚡⚡⚡⚡⚡⚡⚡⚡⚡⚡⚡⚡⚡⚡⚡⚡⚡⚡⚡
"""
    console.print(banner_text, style="bold blue")

def main():
    """Main application loop with AI status"""
    show_banner()
    
    # Show system status with AI components
    console.print(f"[dim]yfinance: {'✅ Available' if YF_AVAILABLE else '❌ Not Available'}[/dim]")
    console.print(f"[dim]Enhanced Collector: {'✅ Available' if COLLECTOR_AVAILABLE else '❌ Not Available'}[/dim]")
    console.print(f"[dim]AI Strategy: {'✅ Available' if AI_STRATEGY_AVAILABLE else '❌ Not Available'}[/dim]")
    console.print(f"[dim]Regime Detector: {'✅ Available' if REGIME_DETECTOR_AVAILABLE else '❌ Not Available'}[/dim]")
    console.print(f"[dim]Core Models: {'✅ Available' if MODELS_AVAILABLE else '❌ Using Fallback'}[/dim]")
    
    # Show AI readiness status
    ai_components_ready = sum([COLLECTOR_AVAILABLE, AI_STRATEGY_AVAILABLE, REGIME_DETECTOR_AVAILABLE])
    if ai_components_ready >= 2:
        console.print("[green]🤖 AI Features: Ready[/green]")
    elif ai_components_ready >= 1:
        console.print("[yellow]🤖 AI Features: Partially Available[/yellow]")
    else:
        console.print("[red]🤖 AI Features: Unavailable[/red]")
    
    bot = OdinBot()
    
    # Initial data fetch
    console.print("[blue]🔄 Fetching initial data...[/blue]")
    bot.get_btc_price()
    console.print("[green]✅ Ready![/green]")
    
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
            console.print("[dim]Press Enter to continue or Ctrl+C to exit...[/dim]")
            try:
                input()
            except KeyboardInterrupt:
                break
    
    console.print("\n[yellow]👋 Thanks for using Odin![/yellow]")
    console.print("[dim]AI-Enhanced Bitcoin Trading Bot v2.0[/dim]")

if __name__ == "__main__":
    main()