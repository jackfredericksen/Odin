#!/usr/bin/env python3
"""
Odin Trading Bot - Clean CLI Interface
Simple, functional, and reliable command line interface
"""

import time
import sys
import os
from datetime import datetime, timezone
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

try:
    from odin.core.enhanced_data_collector import EnhancedBitcoinDataCollector
    COLLECTOR_AVAILABLE = True
except ImportError:
    COLLECTOR_AVAILABLE = False

console = Console()

class OdinBot:
    """Simple Odin trading bot interface"""
    
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
        
        # Try to initialize data collector
        if COLLECTOR_AVAILABLE:
            try:
                self.collector = EnhancedBitcoinDataCollector("data/bitcoin_enhanced.db")
            except:
                pass
    
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
        """Show market information"""
        price = self.get_btc_price()
        
        table = Table(title="📈 Market Data", box=box.SIMPLE)
        table.add_column("Metric", style="cyan")
        table.add_column("Value", style="white")
        
        table.add_row("Current Price", f"${price:,.2f}")
        table.add_row("Market Cap", f"${price * 19.7e6 / 1e9:.0f}B")
        table.add_row("Data Source", "yfinance" if YF_AVAILABLE else "Fallback")
        
        # Add technical data if available
        if self.collector:
            try:
                ml_data = self.collector.get_ml_ready_features(lookback_days=1)
                if not ml_data.empty:
                    latest = ml_data.iloc[-1]
                    if hasattr(latest, 'rsi_14') and latest.rsi_14 is not None:
                        table.add_row("RSI (14)", f"{latest.rsi_14:.1f}")
            except:
                pass
        
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
    console.print("0. 🚪 Exit")
    
    choice = Prompt.ask("\nChoose option", choices=["0","1","2","3","4","5","6"], default="1")
    
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
        
    elif choice == "0":
        return False
    
    return True

def show_strategy_menu(bot: OdinBot):
    """Show strategy control menu"""
    while True:
        console.clear()
        bot.show_header()
        bot.show_strategies()
        
        console.print("\n[cyan]═══ STRATEGY CONTROL ═══[/cyan]")
        console.print("1. Toggle Moving Average")
        console.print("2. Toggle RSI Strategy") 
        console.print("3. Toggle ML Enhanced")
        console.print("4. Stop All Strategies")
        console.print("0. Back to Main Menu")
        
        choice = Prompt.ask("\nChoose option", choices=["0","1","2","3","4"], default="0")
        
        if choice == "1":
            bot.toggle_strategy("Moving Average")
            time.sleep(1)
        elif choice == "2":
            bot.toggle_strategy("RSI Strategy")
            time.sleep(1)
        elif choice == "3":
            bot.toggle_strategy("ML Enhanced")
            time.sleep(1)
        elif choice == "4":
            for strategy in bot.strategies:
                bot.strategies[strategy]["active"] = False
            console.print("[red]🛑 All strategies stopped[/red]")
            time.sleep(1)
        elif choice == "0":
            break

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
    console.print("""
[bold blue]
⚡⚡⚡⚡⚡⚡⚡⚡⚡⚡⚡⚡⚡⚡⚡⚡⚡⚡⚡⚡⚡⚡⚡⚡⚡⚡⚡⚡⚡⚡⚡⚡
⚡                                              ⚡
⚡      ██████╗ ██████╗ ██╗███╗   ██╗          ⚡
⚡     ██╔═══██╗██╔══██╗██║████╗  ██║          ⚡
⚡     ██║   ██║██║  ██║██║██╔██╗ ██║          ⚡
⚡     ██║   ██║██║  ██║██║██║╚██╗██║          ⚡
⚡     ╚██████╔╝██████╔╝██║██║ ╚████║          ⚡
⚡      ╚═════╝ ╚═════╝ ╚═╝╚═╝  ╚═══╝          ⚡
⚡                                              ⚡
⚡         BITCOIN TRADING BOT                  ⚡
⚡            CLEAN CLI v1.0                    ⚡
⚡                                              ⚡
⚡⚡⚡⚡⚡⚡⚡⚡⚡⚡⚡⚡⚡⚡⚡⚡⚡⚡⚡⚡⚡⚡⚡⚡⚡⚡⚡⚡⚡⚡⚡⚡
[/bold blue]
""")

def main():
    """Main application loop"""
    show_banner()
    
    # Show system status
    console.print(f"[dim]yfinance: {'✅ Available' if YF_AVAILABLE else '❌ Not Available'}[/dim]")
    console.print(f"[dim]Enhanced Collector: {'✅ Available' if COLLECTOR_AVAILABLE else '❌ Not Available'}[/dim]")
    
    bot = OdinBot()
    
    # Initial data fetch
    console.print("[blue]🔄 Fetching initial data...[/blue]")
    bot.get_btc_price()
    console.print("[green]✅ Ready![/green]")
    
    time.sleep(1)
    
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
    
    console.print("\n[yellow]👋 Thanks for using Odin![/yellow]")

if __name__ == "__main__":
    main()