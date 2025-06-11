#!/bin/bash

# Odin CLI Launcher Script
# Makes it easy to run the trading bot CLI

echo "🚀 Odin Trading Bot CLI Launcher"
echo "================================"

# Check if we're in the right directory
if [ ! -f "odin_cli.py" ]; then
    echo "❌ odin_cli.py not found. Make sure you're in the project root."
    exit 1
fi

# Install dependencies if needed
echo "📦 Checking dependencies..."
python3 -c "import rich, click" 2>/dev/null || {
    echo "Installing CLI dependencies..."
    pip install rich click
}

# Make CLI executable
chmod +x odin_cli.py

# Show available commands
echo ""
echo "✅ Odin CLI Ready! Available commands:"
echo ""
echo "🖥️  Dashboard (real-time):    python3 odin_cli.py dashboard"
echo "📊 System Status:            python3 odin_cli.py status"
echo "💰 Current Price:            python3 odin_cli.py price"
echo "💼 Portfolio:                python3 odin_cli.py portfolio"
echo "🤖 Strategy Control:         python3 odin_cli.py strategy ma_crossover start"
echo "📈 Historical Analysis:      python3 odin_cli.py history --days 30"
echo "💱 Trading Interface:        python3 odin_cli.py trade"
echo "❓ Help:                     python3 odin_cli.py --help"
echo ""

# Quick start options
echo "Quick start options:"
echo "1) Launch dashboard"
echo "2) Check status"
echo "3) View portfolio"
echo "4) Get Bitcoin price"
echo "5) Exit"
echo ""

read -p "Choose option (1-5): " choice

case $choice in
    1)
        echo "🖥️ Starting dashboard..."
        python3 odin_cli.py dashboard
        ;;
    2)
        echo "📊 Checking status..."
        python3 odin_cli.py status
        ;;
    3)
        echo "💼 Showing portfolio..."
        python3 odin_cli.py portfolio
        ;;
    4)
        echo "💰 Getting Bitcoin price..."
        python3 odin_cli.py price
        ;;
    5)
        echo "👋 Goodbye!"
        exit 0
        ;;
    *)
        echo "❓ Invalid option. Run 'python3 odin_cli.py --help' for all commands."
        ;;
esac