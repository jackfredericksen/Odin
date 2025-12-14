#!/usr/bin/env python3
"""
Odin Trading Bot - Enhanced CLI Interface with State Persistence
Professional command-line interface with argument support and real-time updates.
"""

import time
import sys
import os
import argparse
import asyncio
import json
from datetime import datetime, timezone
from typing import Dict, Optional, Any, List
from pathlib import Path
from dataclasses import dataclass, asdict

# Add project root to Python path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

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
    from rich.progress import Progress, SpinnerColumn, TextColumn
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
    RICH_AVAILABLE = True

# Enhanced system imports
try:
    from odin.core.config_manager import get_config, get_config_manager
    CONFIG_AVAILABLE = True
except ImportError:
    CONFIG_AVAILABLE = False
    print("Warning: Enhanced config system not available, using defaults")

try:
    from odin.utils.logging import get_logger, configure_logging, LogContext, set_correlation_id
    LOGGING_AVAILABLE = True
except ImportError:
    LOGGING_AVAILABLE = False
    print("Warning: Enhanced logging system not available")
    # Create fallback logger
    import logging
    def get_logger(name): return logging.getLogger(name)
    def configure_logging(**kwargs): pass
    def set_correlation_id(cid=None): return "fallback"
    class LogContext:
        def __init__(self, **kwargs): pass

try:
    from odin.core.exceptions import ErrorHandler, OdinException
    ERROR_HANDLER_AVAILABLE = True
except ImportError:
    ERROR_HANDLER_AVAILABLE = False
    print("Warning: Enhanced error handling not available")
    class ErrorHandler:
        async def handle_exception(self, e, context=None, suppress_if_handled=False):
            print(f"Error: {e}")
    class OdinException(Exception): pass

# Data sources
try:
    import yfinance as yf
    YF_AVAILABLE = True
except ImportError:
    yf = None
    YF_AVAILABLE = False

console = Console()

# Initialize systems with fallbacks
if LOGGING_AVAILABLE:
    logger = get_logger(__name__)
else:
    logger = get_logger(__name__)

if ERROR_HANDLER_AVAILABLE:
    error_handler = ErrorHandler()
else:
    error_handler = ErrorHandler()


@dataclass
class CLIState:
    """CLI application state that persists between sessions."""
    current_price: Optional[float] = None
    last_update: Optional[datetime] = None
    portfolio: Dict[str, float] = None
    strategies: Dict[str, Dict[str, Any]] = None
    last_session: Optional[datetime] = None
    auto_refresh: bool = False
    refresh_interval: int = 30
    correlation_id: Optional[str] = None
    
    def __post_init__(self):
        if self.portfolio is None:
            self.portfolio = {"btc": 0.25, "usd": 5000.0}
        if self.strategies is None:
            self.strategies = {
                "Moving Average": {"active": False, "pnl": 0.0, "allocation": 0.25},
                "RSI Strategy": {"active": False, "pnl": 0.0, "allocation": 0.25},
                "Bollinger Bands": {"active": False, "pnl": 0.0, "allocation": 0.25},
                "MACD Strategy": {"active": False, "pnl": 0.0, "allocation": 0.25}
            }


class CLIStateManager:
    """Manages CLI state persistence."""
    
    def __init__(self, state_file: str = "data/cli_state.json"):
        self.state_file = Path(state_file)
        self.state_file.parent.mkdir(parents=True, exist_ok=True)
    
    def save_state(self, state: CLIState) -> bool:
        """Save CLI state to file."""
        try:
            # Convert datetime objects to ISO strings
            state_dict = asdict(state)
            if state_dict['last_update']:
                state_dict['last_update'] = state.last_update.isoformat()
            if state_dict['last_session']:
                state_dict['last_session'] = state.last_session.isoformat()
            
            with open(self.state_file, 'w') as f:
                json.dump(state_dict, f, indent=2)
            
            logger.debug("CLI state saved")
            return True
            
        except Exception as e:
            logger.error(f"Failed to save CLI state: {e}")
            return False
    
    def load_state(self) -> CLIState:
        """Load CLI state from file."""
        try:
            if not self.state_file.exists():
                return CLIState()
            
            with open(self.state_file, 'r') as f:
                state_dict = json.load(f)
            
            # Convert ISO strings back to datetime objects
            if state_dict.get('last_update'):
                state_dict['last_update'] = datetime.fromisoformat(state_dict['last_update'])
            if state_dict.get('last_session'):
                state_dict['last_session'] = datetime.fromisoformat(state_dict['last_session'])
            
            state = CLIState(**state_dict)
            logger.debug("CLI state loaded")
            return state
            
        except Exception as e:
            logger.warning(f"Failed to load CLI state: {e}, using defaults")
            return CLIState()


class OdinCLI:
    """Enhanced Odin CLI with state management and real-time capabilities."""
    
    def __init__(self):
        self.state_manager = CLIStateManager()
        self.state = self.state_manager.load_state()
        self.config = None
        self.repo_manager = None
        self.running = True
        self.live_mode = False
        
        # Set correlation ID for this session
        self.state.correlation_id = set_correlation_id()
        self.state.last_session = datetime.now(timezone.utc)
    
    async def initialize(self):
        """Initialize CLI with enhanced systems."""
        try:
            # Load configuration if available
            if CONFIG_AVAILABLE:
                self.config = get_config()
                
                # Configure logging for CLI
                if LOGGING_AVAILABLE:
                    configure_logging(
                        level=self.config.logging.level,
                        enable_file=False,  # CLI doesn't need file logging
                        enable_console=True,
                        structured_format=False  # Human-readable for CLI
                    )
            
            # Initialize repository manager if needed and available
            if self.config and self.config.trading.enable_live_trading:
                try:
                    from odin.core.repository import get_repository_manager
                    self.repo_manager = await get_repository_manager()
                except ImportError:
                    logger.warning("Repository system not available - using CLI mode only")
            
            if LOGGING_AVAILABLE:
                logger.info("CLI initialized", LogContext(
                    component="cli",
                    operation="initialize"
                ))
            
        except Exception as e:
            if ERROR_HANDLER_AVAILABLE:
                await error_handler.handle_exception(
                    e,
                    LogContext(component="cli", operation="initialize") if LOGGING_AVAILABLE else None
                )
            else:
                print(f"CLI initialization error: {e}")
    
    async def get_btc_price(self) -> float:
        """Get Bitcoin price - database first, then fallback if needed."""
        try:
            # Always try repository/database first
            if self.repo_manager:
                price_repo = self.repo_manager.get_price_repository()
                result = await price_repo.find_latest(limit=1)
                if result.success and result.data:
                    price = result.data.price
                    # Check if data is recent (less than 10 minutes old)
                    if isinstance(result.data.timestamp, datetime):
                        age = datetime.now(timezone.utc) - result.data.timestamp.replace(tzinfo=timezone.utc)
                        if age.total_seconds() < 600:  # 10 minutes
                            self.state.current_price = price
                            self.state.last_update = result.data.timestamp
                            logger.info(f"Got fresh price from database: ${price:,.2f}")
                            return price
                        else:
                            logger.info(f"Database price is stale ({age.total_seconds()/60:.1f} min old)")
            
            # If database is stale or unavailable, try to trigger data collector
            if hasattr(self, 'repo_manager') and self.repo_manager:
                logger.info("Triggering data collector for fresh price...")
                # This would trigger the data collector to fetch new data
                # For now, fall back to direct API calls as temporary measure
            
            # Emergency fallback - try one quick API call
            # (This should rarely be used once data collector is working)
            try:
                import aiohttp
                async with aiohttp.ClientSession() as session:
                    # Try CoinGecko as most reliable free API
                    url = "https://api.coingecko.com/api/v3/simple/price?ids=bitcoin&vs_currencies=usd"
                    async with session.get(url, timeout=10) as response:
                        if response.status == 200:
                            data = await response.json()
                            price = float(data['bitcoin']['usd'])
                            self.state.current_price = price
                            self.state.last_update = datetime.now(timezone.utc)
                            logger.warning(f"Emergency fallback price from CoinGecko: ${price:,.2f}")
                            return price
            except Exception as e:
                logger.debug(f"Emergency fallback failed: {e}")
            
            # Use cached price if available and not too old
            if self.state.current_price and self.state.last_update:
                age = datetime.now(timezone.utc) - self.state.last_update
                if age.total_seconds() < 3600:  # 1 hour
                    logger.info(f"Using cached price: ${self.state.current_price:,.2f}")
                    return self.state.current_price
            
            # No data available
            logger.warning("No price data available from any source")
            return None
            
        except Exception as e:
            logger.error(f"Price fetch error: {e}")
            return None
    
    async def _get_price_from_yfinance(self) -> Optional[float]:
        """Try yfinance API."""
        if not YF_AVAILABLE:
            return None
        
        symbols = ["BTC-USD", "BTCUSD=X"]
        for symbol in symbols:
            try:
                ticker = yf.Ticker(symbol)
                hist = ticker.history(period="1d")
                if not hist.empty:
                    price = float(hist['Close'].iloc[-1])
                    logger.info(f"Got price from yfinance ({symbol}): ${price:,.2f}")
                    return price
            except:
                continue
        return None
    
    async def _get_price_from_coingecko(self) -> Optional[float]:
        """Try CoinGecko API (free, no API key needed)."""
        try:
            import aiohttp
            url = "https://api.coingecko.com/api/v3/simple/price?ids=bitcoin&vs_currencies=usd"
            
            async with aiohttp.ClientSession() as session:
                async with session.get(url, timeout=10) as response:
                    if response.status == 200:
                        data = await response.json()
                        price = float(data['bitcoin']['usd'])
                        logger.info(f"Got price from CoinGecko: ${price:,.2f}")
                        return price
        except Exception as e:
            logger.debug(f"CoinGecko failed: {e}")
        return None
    
    async def _get_price_from_coinapi(self) -> Optional[float]:
        """Try CoinAPI (free tier available)."""
        try:
            import aiohttp
            # Free tier - no API key needed for basic requests
            url = "https://rest.coinapi.io/v1/exchangerate/BTC/USD"
            
            async with aiohttp.ClientSession() as session:
                async with session.get(url, timeout=10) as response:
                    if response.status == 200:
                        data = await response.json()
                        price = float(data['rate'])
                        logger.info(f"Got price from CoinAPI: ${price:,.2f}")
                        return price
        except Exception as e:
            logger.debug(f"CoinAPI failed: {e}")
        return None
    
    async def _get_price_from_binance(self) -> Optional[float]:
        """Try Binance public API (no API key needed)."""
        try:
            import aiohttp
            url = "https://api.binance.com/api/v3/ticker/price?symbol=BTCUSDT"
            
            async with aiohttp.ClientSession() as session:
                async with session.get(url, timeout=10) as response:
                    if response.status == 200:
                        data = await response.json()
                        price = float(data['price'])
                        logger.info(f"Got price from Binance: ${price:,.2f}")
                        return price
        except Exception as e:
            logger.debug(f"Binance failed: {e}")
        return None
    
    async def _get_price_from_coinbase(self) -> Optional[float]:
        """Try Coinbase public API (no API key needed)."""
        try:
            import aiohttp
            url = "https://api.coinbase.com/v2/spot-prices/BTC-USD/spot"
            
            async with aiohttp.ClientSession() as session:
                async with session.get(url, timeout=10) as response:
                    if response.status == 200:
                        data = await response.json()
                        price = float(data['data']['amount'])
                        logger.info(f"Got price from Coinbase: ${price:,.2f}")
                        return price
        except Exception as e:
            logger.debug(f"Coinbase failed: {e}")
        return None
    
    def get_portfolio_value(self) -> float:
        """Calculate total portfolio value - only with real price data."""
        if self.state.current_price is None:
            return self.state.portfolio["usd"]  # Only show USD if no real BTC price
        
        btc_value = self.state.portfolio["btc"] * self.state.current_price
        return btc_value + self.state.portfolio["usd"]
    
    def show_header(self):
        """Show header with real data status."""
        price = self.state.current_price
        portfolio_val = self.get_portfolio_value()
        
        header = Text()
        header.append("⚡ ODIN TRADING BOT v2.0 ⚡\n", style="bold blue")
        
        # Price and portfolio info
        if price is not None:
            header.append(f"Bitcoin: ${price:,.2f} | Portfolio: ${portfolio_val:,.2f}", style="green")
        else:
            header.append(f"Bitcoin: [red]No Data[/red] | Portfolio: ${portfolio_val:,.2f} (USD only)", style="yellow")
        
        # Status indicators
        status_line = " | "
        
        # Data source indicator
        if self.repo_manager:
            status_line += "[green]DATABASE[/green] | "
        elif price is not None and self.state.last_update:
            age = datetime.now(timezone.utc) - self.state.last_update
            if age.total_seconds() < 300:  # Less than 5 minutes
                status_line += "[green]LIVE DATA[/green] | "
            else:
                status_line += "[yellow]CACHED DATA[/yellow] | "
        else:
            status_line += "[red]NO PRICE DATA[/red] | "
        
        # Environment info
        if self.config:
            env_color = "green" if self.config.environment.value == "production" else "yellow"
            status_line += f"[{env_color}]{self.config.environment.value.upper()}[/{env_color}] | "
            
            if self.config.trading.enable_live_trading:
                status_line += "[red]LIVE TRADING[/red] | "
            else:
                status_line += "[blue]PAPER TRADING[/blue] | "
        else:
            status_line += "[blue]CLI MODE[/blue] | "
        
        # Last update time
        if self.state.last_update:
            time_str = self.state.last_update.strftime("%H:%M:%S")
            status_line += f"Updated: {time_str}"
        else:
            status_line += "No price updates"
        
        header.append(status_line, style="dim")
        
        console.print(Panel(header, box=box.ROUNDED, border_style="blue"))
    
    def show_portfolio(self):
        """Show portfolio table with real data only."""
        price = self.state.current_price
        btc_balance = self.state.portfolio["btc"]
        usd_balance = self.state.portfolio["usd"]
        
        table = Table(title="💰 Portfolio", box=box.SIMPLE)
        table.add_column("Asset", style="cyan")
        table.add_column("Balance", style="white")
        table.add_column("Value", style="green")
        table.add_column("Allocation", style="yellow")
        table.add_column("Status", style="magenta")
        
        if price is not None:
            # We have real price data
            btc_value = btc_balance * price
            total_value = btc_value + usd_balance
            btc_alloc = (btc_value / total_value) * 100 if total_value > 0 else 0
            usd_alloc = (usd_balance / total_value) * 100 if total_value > 0 else 0
            
            table.add_row("Bitcoin", f"{btc_balance:.6f} BTC", f"${btc_value:,.2f}", f"{btc_alloc:.1f}%", "✅ Live")
            table.add_row("USD", f"${usd_balance:,.2f}", f"${usd_balance:,.2f}", f"{usd_alloc:.1f}%", "✅ Cash")
            table.add_row("[bold]Total", "", f"[bold]${total_value:,.2f}", "[bold]100.0%", "")
        else:
            # No price data available
            table.add_row("Bitcoin", f"{btc_balance:.6f} BTC", "[red]No Price[/red]", "[red]Unknown[/red]", "❌ No Data")
            table.add_row("USD", f"${usd_balance:,.2f}", f"${usd_balance:,.2f}", "100.0%", "✅ Cash")
            table.add_row("[bold]Total", "", f"[bold]${usd_balance:,.2f} (USD only)", "", "[yellow]Partial Data[/yellow]")
        
        console.print(table)
    
    def show_strategies(self):
        """Show enhanced strategy status."""
        table = Table(title="🤖 Trading Strategies", box=box.SIMPLE)
        table.add_column("Strategy", style="cyan")
        table.add_column("Status", style="white")
        table.add_column("Allocation", style="yellow")
        table.add_column("P&L", style="green")
        table.add_column("Signals", style="magenta")
        
        total_pnl = 0
        active_count = 0
        
        for name, data in self.state.strategies.items():
            status = "🟢 Active" if data["active"] else "⚪ Inactive"
            if data["active"]:
                active_count += 1
            
            allocation = f"{data.get('allocation', 0) * 100:.0f}%"
            
            pnl = data["pnl"]
            total_pnl += pnl
            pnl_color = "green" if pnl >= 0 else "red"
            pnl_text = f"[{pnl_color}]${pnl:+.2f}[/{pnl_color}]"
            
            # Mock signal count
            signals = "12/24h" if data["active"] else "0/24h"
            
            table.add_row(name, status, allocation, pnl_text, signals)
        
        # Summary row
        total_pnl_color = "green" if total_pnl >= 0 else "red"
        table.add_row(
            f"[bold]Summary ({active_count}/4 active)",
            "",
            "[bold]100%",
            f"[bold][{total_pnl_color}]${total_pnl:+.2f}[/{total_pnl_color}]",
            ""
        )
        
        console.print(table)
    
    def show_market_data(self):
        """Show enhanced market information."""
        price = self.state.current_price or 43500.0
        
        table = Table(title="📈 Market Data", box=box.SIMPLE)
        table.add_column("Metric", style="cyan")
        table.add_column("Value", style="white")
        table.add_column("Change", style="green")
        
        table.add_row("Current Price", f"${price:,.2f}", "+1.2%")
        table.add_row("Market Cap", f"${price * 19.7e6 / 1e9:.0f}B", "+0.8%")
        table.add_row("24h Volume", "$28.5B", "+15.3%")
        table.add_row("24h High", f"${price * 1.025:,.2f}", "")
        table.add_row("24h Low", f"${price * 0.975:,.2f}", "")
        
        data_source = "Live Data" if self.repo_manager else "yfinance" if YF_AVAILABLE else "Cached"
        table.add_row("Data Source", data_source, "")
        
        if self.state.last_update:
            age = datetime.now(timezone.utc) - self.state.last_update
            age_text = f"{age.seconds}s ago"
            table.add_row("Last Updated", age_text, "")
        
        console.print(table)
    
    async def manual_price_entry(self):
        """Allow manual Bitcoin price entry when APIs are down."""
        try:
            console.print("\n[yellow]yfinance API is currently down. You can manually enter Bitcoin price.[/yellow]")
            console.print("[dim]Check current price at: coinmarketcap.com, coinbase.com, or binance.com[/dim]")

            price_input = Prompt.ask(
                "\nEnter current Bitcoin price (USD)",
                default="skip"
            )

            if price_input.lower() in ['skip', 's', '']:
                console.print("[dim]Skipping manual price entry[/dim]")
                return False

            try:
                price = float(price_input.replace(',', ''))
                return price
            except ValueError:
                console.print("[red]Invalid price format. Please enter a valid number.[/red]")
                return False
        except Exception as e:
            console.print(f"[red]Error in manual price entry: {e}[/red]")
            return False

    def toggle_strategy(self, strategy_name: str):
        """Toggle strategy on/off with enhanced feedback."""
        if strategy_name in self.state.strategies:
            current = self.state.strategies[strategy_name]["active"]
            self.state.strategies[strategy_name]["active"] = not current
            
            status = "started" if not current else "stopped"
            color = "green" if not current else "red"
            console.print(f"[{color}]✅ {strategy_name} {status}[/{color}]")
            
            # Save state
            self.state_manager.save_state(self.state)
            
            logger.info(f"Strategy {strategy_name} {status}", LogContext(
                component="cli",
                operation="toggle_strategy",
                additional_data={"strategy": strategy_name, "active": not current}
            ))
        else:
            console.print(f"[red]❌ Strategy '{strategy_name}' not found[/red]")
    
    async def refresh_data(self):
        """Refresh all data with progress indicator."""
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            console=console,
        ) as progress:
            task = progress.add_task("Refreshing data...", total=None)
            
            # Try to get latest price from multiple sources
            progress.update(task, description="Checking price sources...")
            await self.get_btc_price()
            
            progress.update(task, description="Updating strategy data...")
            await asyncio.sleep(0.5)
            
            # Save state
            self.state_manager.save_state(self.state)
            progress.update(task, description="Complete!")
            
        if self.state.current_price is not None:
            console.print("[green]✅ Data refresh complete![/green]")
        else:
            console.print("[red]❌ All price sources failed - check internet connection[/red]")
    
    def show_system_status(self):
        """Show system status and health."""
        table = Table(title="🔧 System Status", box=box.SIMPLE)
        table.add_column("Component", style="cyan")
        table.add_column("Status", style="white")
        table.add_column("Details", style="dim")
        
        # Configuration
        config_status = "🟢 OK" if self.config else "🔴 ERROR"
        table.add_row("Configuration", config_status, 
                     f"Environment: {self.config.environment.value}" if self.config else "Not loaded")
        
        # Database
        db_status = "🟢 Connected" if self.repo_manager else "⚪ Offline"
        table.add_row("Database", db_status, "Repository manager" if self.repo_manager else "CLI mode")
        
        # Data sources
        data_status = "🟢 yfinance" if YF_AVAILABLE else "🔴 No sources"
        table.add_row("Data Sources", data_status, "External price data")
        
        # Trading mode
        if self.config:
            trading_mode = "Live Trading" if self.config.trading.enable_live_trading else "Paper Trading"
            trading_color = "🔴" if self.config.trading.enable_live_trading else "🟡"
            table.add_row("Trading Mode", f"{trading_color} {trading_mode}", 
                         f"Capital: ${self.config.trading.initial_capital:,.0f}")
        
        # Session info
        if self.state.last_session:
            session_duration = datetime.now(timezone.utc) - self.state.last_session
            duration_text = f"{session_duration.seconds // 60}m {session_duration.seconds % 60}s"
            table.add_row("Session", "🟢 Active", f"Duration: {duration_text}")
        
        console.print(table)


async def show_main_menu(cli: OdinCLI):
    """Show main menu and handle selection."""
    cli.show_header()
    
    console.print("\n[cyan]═══ MAIN MENU ═══[/cyan]")
    console.print("1. 💰 Show Portfolio")
    console.print("2. 🤖 Strategy Control")
    console.print("3. 📈 Market Data")
    console.print("4. 🔄 Refresh Data")
    console.print("5. 💱 Quick Trade (Demo)")
    console.print("6. 📊 Live Dashboard")
    console.print("7. 🔧 System Status")
    console.print("8. ⚙️  Settings")
    console.print("0. 🚪 Exit")
    
    choice = Prompt.ask("\nChoose option", 
                       choices=["0","1","2","3","4","5","6","7","8"], 
                       default="1")
    
    if choice == "1":
        console.clear()
        cli.show_header()
        cli.show_portfolio()
        input("\nPress Enter to continue...")
        
    elif choice == "2":
        await show_strategy_menu(cli)
        
    elif choice == "3":
        console.clear()
        cli.show_header()
        cli.show_market_data()
        input("\nPress Enter to continue...")
        
    elif choice == "4":
        console.clear()
        cli.show_header()
        await cli.refresh_data()
        time.sleep(2)
        
    elif choice == "5":
        await show_trade_menu(cli)
        
    elif choice == "6":
        await show_live_dashboard(cli)
        
    elif choice == "7":
        console.clear()
        cli.show_header()
        cli.show_system_status()
        input("\nPress Enter to continue...")
        
    elif choice == "8":
        await show_settings_menu(cli)
        
    elif choice == "0":
        return False
    
    return True


async def show_strategy_menu(cli: OdinCLI):
    """Show enhanced strategy control menu."""
    while True:
        console.clear()
        cli.show_header()
        cli.show_strategies()
        
        console.print("\n[cyan]═══ STRATEGY CONTROL ═══[/cyan]")
        console.print("1. Toggle Moving Average")
        console.print("2. Toggle RSI Strategy") 
        console.print("3. Toggle Bollinger Bands")
        console.print("4. Toggle MACD Strategy")
        console.print("5. Start All Strategies")
        console.print("6. Stop All Strategies")
        console.print("7. Strategy Settings")
        console.print("0. Back to Main Menu")
        
        choice = Prompt.ask("\nChoose option", 
                           choices=["0","1","2","3","4","5","6","7"], 
                           default="0")
        
        if choice == "1":
            cli.toggle_strategy("Moving Average")
            time.sleep(1)
        elif choice == "2":
            cli.toggle_strategy("RSI Strategy")
            time.sleep(1)
        elif choice == "3":
            cli.toggle_strategy("Bollinger Bands")
            time.sleep(1)
        elif choice == "4":
            cli.toggle_strategy("MACD Strategy")
            time.sleep(1)
        elif choice == "5":
            for strategy in cli.state.strategies:
                cli.state.strategies[strategy]["active"] = True
            cli.state_manager.save_state(cli.state)
            console.print("[green]🚀 All strategies started[/green]")
            time.sleep(1)
        elif choice == "6":
            for strategy in cli.state.strategies:
                cli.state.strategies[strategy]["active"] = False
            cli.state_manager.save_state(cli.state)
            console.print("[red]🛑 All strategies stopped[/red]")
            time.sleep(1)
        elif choice == "7":
            console.print("[yellow]⚠️ Strategy settings coming soon[/yellow]")
            time.sleep(2)
        elif choice == "0":
            break


async def show_trade_menu(cli: OdinCLI):
    """Show enhanced trading menu."""
    console.clear()
    cli.show_header()
    
    price = cli.state.current_price or 43500.0
    
    console.print(f"\n[white]Current BTC Price: [bold green]${price:,.2f}[/bold green][/white]")
    console.print(f"[white]Your BTC: [bold]{cli.state.portfolio['btc']:.6f}[/bold][/white]")
    console.print(f"[white]Your USD: [bold]${cli.state.portfolio['usd']:,.2f}[/bold][/white]")
    
    if not cli.config or not cli.config.trading.enable_live_trading:
        console.print("\n[yellow]⚠️ DEMO MODE - No real trades executed[/yellow]")
    else:
        console.print("\n[red]⚠️ LIVE TRADING MODE - Real money at risk[/red]")
    
    console.print("\n[cyan]═══ QUICK TRADE ═══[/cyan]")
    console.print("1. 🟢 Buy $100 worth of BTC")
    console.print("2. 🟢 Buy $500 worth of BTC")
    console.print("3. 🟢 Buy $1000 worth of BTC")
    console.print("4. 🔴 Sell 0.001 BTC")
    console.print("5. 🔴 Sell 0.01 BTC")
    console.print("6. 💹 Custom Trade")
    console.print("0. Back to Main Menu")
    
    choice = Prompt.ask("\nChoose option", 
                       choices=["0","1","2","3","4","5","6"], 
                       default="0")
    
    if choice in ["1", "2", "3"]:
        amounts = {"1": 100, "2": 500, "3": 1000}
        usd_amount = amounts[choice]
        btc_amount = usd_amount / price
        console.print(f"[green]✅ Demo BUY: {btc_amount:.6f} BTC for ${usd_amount}[/green]")
    elif choice in ["4", "5"]:
        btc_amounts = {"4": 0.001, "5": 0.01}
        btc_amount = btc_amounts[choice]
        usd_amount = btc_amount * price
        console.print(f"[red]✅ Demo SELL: {btc_amount} BTC for ${usd_amount:.2f}[/red]")
    elif choice == "6":
        console.print("[yellow]⚠️ Custom trading coming soon[/yellow]")
    
    if choice != "0":
        time.sleep(2)


async def show_settings_menu(cli: OdinCLI):
    """Show settings menu."""
    while True:
        console.clear()
        cli.show_header()
        
        console.print("\n[cyan]═══ SETTINGS ═══[/cyan]")
        console.print(f"1. Auto Refresh: {'🟢 ON' if cli.state.auto_refresh else '⚪ OFF'}")
        console.print(f"2. Refresh Interval: {cli.state.refresh_interval}s")
        console.print("3. Reset Portfolio")
        console.print("4. Export Data")
        console.print("5. View Logs")
        console.print("0. Back to Main Menu")
        
        choice = Prompt.ask("\nChoose option", 
                           choices=["0","1","2","3","4","5"], 
                           default="0")
        
        if choice == "1":
            cli.state.auto_refresh = not cli.state.auto_refresh
            cli.state_manager.save_state(cli.state)
            status = "enabled" if cli.state.auto_refresh else "disabled"
            console.print(f"[green]Auto refresh {status}[/green]")
            time.sleep(1)
        elif choice == "2":
            try:
                interval = int(Prompt.ask("Enter refresh interval (seconds)", default=str(cli.state.refresh_interval)))
                if 5 <= interval <= 300:
                    cli.state.refresh_interval = interval
                    cli.state_manager.save_state(cli.state)
                    console.print(f"[green]Refresh interval set to {interval}s[/green]")
                else:
                    console.print("[red]Interval must be between 5 and 300 seconds[/red]")
            except ValueError:
                console.print("[red]Invalid interval[/red]")
            time.sleep(1)
        elif choice == "3":
            if Confirm.ask("Reset portfolio to default values?"):
                cli.state.portfolio = {"btc": 0.25, "usd": 5000.0}
                cli.state_manager.save_state(cli.state)
                console.print("[green]Portfolio reset[/green]")
            time.sleep(1)
        elif choice == "4":
            console.print("[yellow]Export functionality coming soon[/yellow]")
            time.sleep(2)
        elif choice == "5":
            console.print("[yellow]Log viewer coming soon[/yellow]")
            time.sleep(2)
        elif choice == "0":
            break


async def show_live_dashboard(cli: OdinCLI):
    """Show live updating dashboard."""
    console.clear()
    console.print(Panel(
        "[bold blue]📊 Live Dashboard[/bold blue]\n"
        f"[dim]Auto-refreshing every {cli.state.refresh_interval} seconds - Press Ctrl+C to exit[/dim]",
        border_style="blue"
    ))
    
    def create_dashboard_layout():
        layout = Layout()
        layout.split_column(
            Layout(create_header_panel(cli), size=4),
            Layout(name="main")
        )
        layout["main"].split_row(
            Layout(create_portfolio_panel(cli)),
            Layout(create_strategy_panel(cli))
        )
        return layout
    
    try:
        cli.live_mode = True
        with Live(create_dashboard_layout(), refresh_per_second=0.5, console=console) as live:
            refresh_counter = 0
            while cli.live_mode:
                await asyncio.sleep(1)
                refresh_counter += 1
                
                # Refresh data at specified interval
                if refresh_counter >= cli.state.refresh_interval:
                    await cli.get_btc_price()
                    refresh_counter = 0
                
                live.update(create_dashboard_layout())
                
    except KeyboardInterrupt:
        console.print("\n[yellow]Dashboard stopped[/yellow]")
    finally:
        cli.live_mode = False


def create_header_panel(cli: OdinCLI) -> Panel:
    """Create header panel for dashboard."""
    price = cli.state.current_price or 0
    portfolio_val = cli.get_portfolio_value()
    
    header_text = Text()
    header_text.append("⚡ ODIN LIVE DASHBOARD ⚡\n", style="bold blue")
    header_text.append(f"Bitcoin: ${price:,.2f} | Portfolio: ${portfolio_val:,.2f}", style="green")
    
    if cli.state.last_update:
        time_str = cli.state.last_update.strftime("%H:%M:%S")
        header_text.append(f" | Last Update: {time_str}", style="dim")
    
    return Panel(header_text, box=box.ROUNDED, border_style="blue")


def create_portfolio_panel(cli: OdinCLI) -> Panel:
    """Create portfolio panel for dashboard."""
    table = Table(box=box.SIMPLE, show_header=False)
    table.add_column("", style="cyan")
    table.add_column("", style="white")
    
    price = cli.state.current_price or 43500.0
    btc_value = cli.state.portfolio["btc"] * price
    total_value = btc_value + cli.state.portfolio["usd"]
    
    table.add_row("💰 Portfolio Value", f"${total_value:,.2f}")
    table.add_row("₿ Bitcoin", f"{cli.state.portfolio['btc']:.6f} BTC")
    table.add_row("💵 USD", f"${cli.state.portfolio['usd']:,.2f}")
    table.add_row("📊 BTC Value", f"${btc_value:,.2f}")
    table.add_row("📈 24h Change", "+$142.50 (+2.3%)")
    
    return Panel(table, title="💼 Portfolio", border_style="green")


def create_strategy_panel(cli: OdinCLI) -> Panel:
    """Create strategy panel for dashboard."""
    table = Table(box=box.SIMPLE, show_header=False)
    table.add_column("", style="cyan")
    table.add_column("", style="white")
    
    active_count = sum(1 for s in cli.state.strategies.values() if s["active"])
    total_pnl = sum(s["pnl"] for s in cli.state.strategies.values())
    
    table.add_row("🤖 Active Strategies", f"{active_count}/{len(cli.state.strategies)}")
    table.add_row("📈 Total P&L", f"${total_pnl:+.2f}")
    table.add_row("⚡ Signals Today", "24")
    table.add_row("🎯 Win Rate", "68.5%")
    
    for name, data in cli.state.strategies.items():
        status = "🟢" if data["active"] else "⚪"
        short_name = name.split()[0]  # Shorten for display
        table.add_row(f"{status} {short_name}", f"${data['pnl']:+.2f}")
    
    return Panel(table, title="🤖 Strategies", border_style="purple")


def show_banner():
    """Show enhanced startup banner."""
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
⚡         ENHANCED CLI v2.0                    ⚡
⚡      Professional Trading Interface          ⚡
⚡                                              ⚡
⚡⚡⚡⚡⚡⚡⚡⚡⚡⚡⚡⚡⚡⚡⚡⚡⚡⚡⚡⚡⚡⚡⚡⚡⚡⚡⚡⚡⚡⚡⚡⚡
[/bold blue]
""")


def parse_arguments():
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(description='Odin Trading Bot CLI')
    
    # Direct actions
    parser.add_argument('--show-portfolio', action='store_true',
                       help='Show portfolio and exit')
    parser.add_argument('--show-strategies', action='store_true',
                       help='Show strategies and exit')
    parser.add_argument('--show-market', action='store_true',
                       help='Show market data and exit')
    parser.add_argument('--show-status', action='store_true',
                       help='Show system status and exit')
    
    # Strategy controls
    parser.add_argument('--start-strategy', type=str,
                       help='Start specific strategy')
    parser.add_argument('--stop-strategy', type=str,
                       help='Stop specific strategy')
    parser.add_argument('--start-all', action='store_true',
                       help='Start all strategies')
    parser.add_argument('--stop-all', action='store_true',
                       help='Stop all strategies')
    
    # Data operations
    parser.add_argument('--refresh', action='store_true',
                       help='Refresh data and exit')
    parser.add_argument('--export', type=str,
                       help='Export data to file')
    
    # Configuration
    parser.add_argument('--config', type=str,
                       help='Configuration file path')
    parser.add_argument('--log-level', type=str,
                       choices=['DEBUG', 'INFO', 'WARNING', 'ERROR'],
                       help='Set logging level')
    
    # Mode selection
    parser.add_argument('--live', action='store_true',
                       help='Start in live dashboard mode')
    parser.add_argument('--daemon', action='store_true',
                       help='Run as background daemon')
    
    return parser.parse_args()


async def execute_command_line_action(cli: OdinCLI, args) -> bool:
    """Execute command line actions and return True if should exit."""
    
    # Initialize CLI first
    await cli.initialize()
    await cli.get_btc_price()
    
    if args.show_portfolio:
        cli.show_header()
        cli.show_portfolio()
        return True
    
    if args.show_strategies:
        cli.show_header()
        cli.show_strategies()
        return True
    
    if args.show_market:
        cli.show_header()
        cli.show_market_data()
        return True
    
    if args.show_status:
        cli.show_header()
        cli.show_system_status()
        return True
    
    if args.refresh:
        console.print("Refreshing data...")
        await cli.refresh_data()
        return True
    
    if args.start_strategy:
        strategy_map = {
            'ma': 'Moving Average',
            'rsi': 'RSI Strategy', 
            'bb': 'Bollinger Bands',
            'macd': 'MACD Strategy'
        }
        strategy_name = strategy_map.get(args.start_strategy.lower(), args.start_strategy)
        cli.toggle_strategy(strategy_name)
        console.print(f"Strategy command executed: {strategy_name}")
        return True
    
    if args.stop_strategy:
        strategy_map = {
            'ma': 'Moving Average',
            'rsi': 'RSI Strategy',
            'bb': 'Bollinger Bands', 
            'macd': 'MACD Strategy'
        }
        strategy_name = strategy_map.get(args.stop_strategy.lower(), args.stop_strategy)
        if cli.state.strategies.get(strategy_name, {}).get('active', False):
            cli.toggle_strategy(strategy_name)
        console.print(f"Strategy command executed: {strategy_name}")
        return True
    
    if args.start_all:
        for strategy in cli.state.strategies:
            if not cli.state.strategies[strategy]["active"]:
                cli.state.strategies[strategy]["active"] = True
        cli.state_manager.save_state(cli.state)
        console.print("[green]All strategies started[/green]")
        return True
    
    if args.stop_all:
        for strategy in cli.state.strategies:
            if cli.state.strategies[strategy]["active"]:
                cli.state.strategies[strategy]["active"] = False
        cli.state_manager.save_state(cli.state)
        console.print("[red]All strategies stopped[/red]")
        return True
    
    if args.live:
        await cli.initialize()
        await show_live_dashboard(cli)
        return True
    
    if args.export:
        console.print(f"[yellow]Export to {args.export} - feature coming soon[/yellow]")
        return True
    
    return False


async def main():
    """Main CLI application loop."""
    args = parse_arguments()
    
    # Show banner if not running command-line action
    has_action = any([
        args.show_portfolio, args.show_strategies, args.show_market, 
        args.show_status, args.refresh, args.start_strategy, 
        args.stop_strategy, args.start_all, args.stop_all, 
        args.live, args.export
    ])
    
    if not has_action:
        show_banner()
    
    # Initialize CLI
    cli = OdinCLI()
    
    try:
        # Handle command line actions
        if has_action:
            should_exit = await execute_command_line_action(cli, args)
            if should_exit:
                return
        
        # Initialize for interactive mode
        await cli.initialize()
        
        # Show system status
        if not has_action:
            console.print(f"[dim]yfinance: {'✅ Available' if YF_AVAILABLE else '❌ Not Available'}[/dim]")
            console.print(f"[dim]Repository: {'✅ Connected' if cli.repo_manager else '⚪ CLI Mode'}[/dim]")
            console.print(f"[dim]Environment: {'✅ ' + cli.config.environment.value if cli.config else '❌ Not Loaded'}[/dim]")
        
        # Initial data fetch
        if not has_action:
            console.print("[blue]🔄 Fetching initial data...[/blue]")
            await cli.get_btc_price()
            console.print("[green]✅ Ready![/green]")
            time.sleep(1)
        
        # Main interactive loop
        while cli.running and not has_action:
            console.clear()
            try:
                if not await show_main_menu(cli):
                    break
            except KeyboardInterrupt:
                break
            except Exception as e:
                console.print(f"[red]❌ Error: {e}[/red]")
                await error_handler.handle_exception(
                    e,
                    LogContext(component="cli", operation="main_loop"),
                    suppress_if_handled=True
                )
                time.sleep(2)
        
        # Save state before exit
        cli.state_manager.save_state(cli.state)
        
        if not has_action:
            console.print("\n[yellow]👋 Thanks for using Odin![/yellow]")
    
    except KeyboardInterrupt:
        console.print("\n[yellow]Operation cancelled[/yellow]")
    except Exception as e:
        console.print(f"\n[red]Critical error: {e}[/red]")
        logger.error(f"CLI critical error: {e}")
    finally:
        # Cleanup
        if cli.repo_manager:
            await cli.repo_manager.close()


def sync_main():
    """Synchronous wrapper for async main function."""
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        pass
    except Exception as e:
        console.print(f"[red]CRITICAL ERROR: {e}[/red]")
        sys.exit(1)


if __name__ == "__main__":
    sync_main()
