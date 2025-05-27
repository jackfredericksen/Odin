# notifications/discord_alerts.py
# Simple Discord notification system for your existing Odin bot

import requests
import json
from datetime import datetime, timedelta
from typing import Dict, Optional
import os

class OdinDiscordNotifier:
    def __init__(self, webhook_url: str = None):
        """
        Simple Discord notifier for Odin trading signals
        
        Args:
            webhook_url: Discord webhook URL (or set DISCORD_WEBHOOK env var)
        """
        self.webhook_url = webhook_url or os.getenv('DISCORD_WEBHOOK')
        self.recent_alerts = {}  # Track recent alerts to avoid spam
        self.cooldown_seconds = 300  # 5 minutes between same signal alerts
        
        # Strategy emojis and names
        self.strategy_info = {
            'ma': {'name': 'Moving Average', 'emoji': '🔄'},
            'rsi': {'name': 'RSI Momentum', 'emoji': '📊'},
            'bb': {'name': 'Bollinger Bands', 'emoji': '📈'},
            'macd': {'name': 'MACD Trend', 'emoji': '⚡'}
        }
    
    def check_and_send_alerts(self, current_price: float):
        """
        Check your existing strategy endpoints and send Discord alerts for new signals
        """
        if not self.webhook_url:
            print("⚠️ Discord webhook URL not configured")
            return
        
        strategies = ['ma', 'rsi', 'bb', 'macd']
        
        for strategy in strategies:
            try:
                # Get strategy analysis from your existing API
                analysis = self._get_strategy_analysis(strategy)
                
                if analysis and 'current_signal' in analysis:
                    signal = analysis['current_signal']
                    
                    if signal and signal.get('type') in ['BUY', 'SELL']:
                        # Check if we should send alert (avoid spam)
                        if self._should_send_alert(strategy, signal):
                            self._send_discord_alert(strategy, signal, current_price, analysis)
                            
            except Exception as e:
                print(f"Error checking {strategy} alerts: {e}")
    
    def _get_strategy_analysis(self, strategy: str) -> Optional[Dict]:
        """Get strategy analysis from your existing Odin API"""
        try:
            url = f"http://localhost:5000/api/strategy/{strategy}/analysis"
            response = requests.get(url, timeout=5)
            
            if response.status_code == 200:
                return response.json()
            return None
            
        except Exception as e:
            print(f"Error fetching {strategy} analysis: {e}")
            return None
    
    def _should_send_alert(self, strategy: str, signal: Dict) -> bool:
        """Check if we should send alert (cooldown to avoid spam)"""
        signal_type = signal.get('type')
        alert_key = f"{strategy}_{signal_type}"
        
        # Check cooldown
        if alert_key in self.recent_alerts:
            time_since_last = (datetime.now() - self.recent_alerts[alert_key]).total_seconds()
            if time_since_last < self.cooldown_seconds:
                return False
        
        return True
    
    def _send_discord_alert(self, strategy: str, signal: Dict, current_price: float, analysis: Dict):
        """Send Discord alert for trading signal"""
        try:
            strategy_info = self.strategy_info.get(strategy, {'name': strategy.upper(), 'emoji': '📊'})
            signal_type = signal.get('type')
            
            # Signal color and emoji
            if signal_type == 'BUY':
                color = 0x00ff88  # Green
                signal_emoji = '🟢'
            else:  # SELL
                color = 0xff4757  # Red
                signal_emoji = '🔴'
            
            # Get strategy-specific details
            details = self._get_strategy_details(strategy, analysis)
            
            # Create Discord embed
            embed = {
                "title": f"{signal_emoji} Odin Trading Signal",
                "description": f"**{strategy_info['emoji']} {strategy_info['name']}** - {signal_type} Signal",
                "color": color,
                "fields": [
                    {
                        "name": "💰 Bitcoin Price",
                        "value": f"${current_price:,.2f}",
                        "inline": True
                    },
                    {
                        "name": "📊 Strategy",
                        "value": strategy_info['name'],
                        "inline": True
                    },
                    {
                        "name": "⏰ Time",
                        "value": datetime.now().strftime('%H:%M:%S'),
                        "inline": True
                    }
                ],
                "footer": {
                    "text": "Odin Trading Bot • Advanced Crypto Trading"
                },
                "timestamp": datetime.now().isoformat()
            }
            
            # Add strategy-specific details if available
            if details:
                embed["fields"].append({
                    "name": "📈 Technical Details",
                    "value": details,
                    "inline": False
                })
            
            # Send to Discord
            payload = {
                "username": "Odin Trading Bot",
                "avatar_url": "https://i.imgur.com/4M34hi2.png",  # Optional: Odin bot avatar
                "embeds": [embed]
            }
            
            response = requests.post(
                self.webhook_url,
                data=json.dumps(payload),
                headers={'Content-Type': 'application/json'},
                timeout=10
            )
            
            if response.status_code in [200, 204]:
                # Update recent alerts to avoid spam
                alert_key = f"{strategy}_{signal_type}"
                self.recent_alerts[alert_key] = datetime.now()
                print(f"✅ Discord alert sent: {strategy_info['name']} {signal_type} at ${current_price:,.2f}")
            else:
                print(f"❌ Discord alert failed: {response.status_code}")
                
        except Exception as e:
            print(f"Error sending Discord alert: {e}")
    
    def _get_strategy_details(self, strategy: str, analysis: Dict) -> str:
        """Get strategy-specific technical details for the alert"""
        try:
            if strategy == 'ma':
                ma_short = analysis.get('ma_short', 0)
                ma_long = analysis.get('ma_long', 0)
                trend = analysis.get('trend', 'Unknown')
                return f"MA(5): ${ma_short:,.2f} | MA(20): ${ma_long:,.2f}\nTrend: {trend}"
                
            elif strategy == 'rsi':
                # Try to get RSI value from signal or analysis
                current_signal = analysis.get('current_signal', {})
                rsi_value = current_signal.get('rsi_value', 'N/A')
                if rsi_value != 'N/A':
                    condition = 'Oversold' if rsi_value < 30 else 'Overbought' if rsi_value > 70 else 'Neutral'
                    return f"RSI: {rsi_value:.1f}\nCondition: {condition}"
                
            elif strategy == 'bb':
                # Bollinger Bands details
                current_signal = analysis.get('current_signal', {})
                return "Bollinger Bands signal confirmed"
                
            elif strategy == 'macd':
                # MACD details
                current_signal = analysis.get('current_signal', {})
                return "MACD crossover detected"
            
            return None
            
        except Exception:
            return None
    
    def send_test_alert(self):
        """Send a test alert to verify Discord webhook is working"""
        if not self.webhook_url:
            return "❌ Discord webhook URL not configured"
        
        try:
            embed = {
                "title": "🧪 Odin Bot Test Alert",
                "description": "Testing Discord notification system",
                "color": 0x3498db,  # Blue
                "fields": [
                    {
                        "name": "🤖 Status",
                        "value": "Online and Ready",
                        "inline": True
                    },
                    {
                        "name": "📊 Strategies",
                        "value": "MA • RSI • BB • MACD",
                        "inline": True
                    },
                    {
                        "name": "⏰ Time",
                        "value": datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                        "inline": False
                    }
                ],
                "footer": {
                    "text": "If you see this message, Discord alerts are working!"
                },
                "timestamp": datetime.now().isoformat()
            }
            
            payload = {
                "username": "Odin Trading Bot",
                "embeds": [embed]
            }
            
            response = requests.post(
                self.webhook_url,
                data=json.dumps(payload),
                headers={'Content-Type': 'application/json'},
                timeout=10
            )
            
            if response.status_code in [200, 204]:
                return "✅ Test alert sent successfully!"
            else:
                return f"❌ Test alert failed: HTTP {response.status_code}"
                
        except Exception as e:
            return f"❌ Test alert error: {e}"
    
    def send_startup_notification(self):
        """Send notification when Odin bot starts up"""
        if not self.webhook_url:
            return
        
        try:
            embed = {
                "title": "🚀 Odin Trading Bot Started",
                "description": "Advanced crypto trading bot is now online and monitoring Bitcoin",
                "color": 0x00ff88,  # Green
                "fields": [
                    {
                        "name": "📊 Active Strategies",
                        "value": "🔄 Moving Average\n📊 RSI Momentum\n📈 Bollinger Bands\n⚡ MACD Trend",
                        "inline": True
                    },
                    {
                        "name": "⚙️ Features",
                        "value": "✅ Real-time signals\n✅ Multi-strategy analysis\n✅ Performance tracking\n✅ Discord alerts",
                        "inline": True
                    }
                ],
                "footer": {
                    "text": "Odin Bot • Ready for trading signals"
                },
                "timestamp": datetime.now().isoformat()
            }
            
            payload = {
                "username": "Odin Trading Bot",
                "embeds": [embed]
            }
            
            response = requests.post(
                self.webhook_url,
                data=json.dumps(payload),
                headers={'Content-Type': 'application/json'},
                timeout=10
            )
            
            if response.status_code in [200, 204]:
                print("✅ Startup notification sent to Discord")
            
        except Exception as e:
            print(f"Error sending startup notification: {e}")


# Integration code for your existing btc_api_server.py
"""
ADD THIS TO YOUR EXISTING btc_api_server.py:

# Import at the top
from notifications.discord_alerts import OdinDiscordNotifier

# Initialize after your other components (add after collector, strategy setup)
# Set your Discord webhook URL here or in environment variable
discord_notifier = OdinDiscordNotifier(webhook_url="YOUR_DISCORD_WEBHOOK_URL_HERE")

# Add this function to start alert monitoring
def start_discord_alerts():
    import threading
    import time
    
    def alert_loop():
        print("🚨 Starting Discord alert monitoring...")
        
        # Send startup notification
        discord_notifier.send_startup_notification()
        
        while True:
            try:
                if collector.latest_data:
                    current_price = collector.latest_data['price']
                    discord_notifier.check_and_send_alerts(current_price)
                
                # Check every 2 minutes for new signals
                time.sleep(120)
                
            except Exception as e:
                print(f"Error in Discord alert monitoring: {e}")
                time.sleep(60)
    
    # Start background thread
    thread = threading.Thread(target=alert_loop, daemon=True)
    thread.start()
    return thread

# Add new API endpoint for testing alerts
@app.route('/api/discord/test', methods=['POST'])
def test_discord_alert():
    try:
        result = discord_notifier.send_test_alert()
        return jsonify({'status': 'success', 'message': result})
    except Exception as e:
        return jsonify({'error': str(e), 'status': 'error'}), 500

# Add this line in your main() function after starting the collector:
discord_thread = start_discord_alerts()
print("🚨 Discord alerts enabled")
"""


# Quick setup instructions
setup_instructions = '''
🚀 DISCORD SETUP INSTRUCTIONS:

1. Create Discord Webhook:
   • Go to your Discord server
   • Server Settings → Integrations → Webhooks
   • Click "New Webhook"
   • Choose channel (e.g., #trading-alerts)
   • Copy the webhook URL

2. Add to your Odin bot:
   • Save this file as: notifications/discord_alerts.py
   • Add the integration code to your btc_api_server.py
   • Replace "YOUR_DISCORD_WEBHOOK_URL_HERE" with your actual webhook URL

3. Test the setup:
   • Start your Odin bot: python src/btc_api_server.py
   • Test endpoint: curl -X POST http://localhost:5000/api/discord/test
   • You should see a test message in Discord

4. What you'll get:
   ✅ Real-time BUY/SELL alerts for all 4 strategies
   ✅ Beautiful Discord embeds with Bitcoin price
   ✅ Technical details for each strategy
   ✅ Anti-spam (5-minute cooldown per strategy)
   ✅ Startup notification when bot starts
   ✅ Color-coded alerts (green=BUY, red=SELL)

🎯 Your Discord channel will now receive live trading signals from Odin!
'''

if __name__ == "__main__":
    print("🚨 Odin Discord Notifier")
    print("=" * 50)
    
    # Test with example webhook (won't work without real webhook)
    notifier = OdinDiscordNotifier()
    
    if notifier.webhook_url:
        print("✅ Discord webhook configured")
        result = notifier.send_test_alert()
        print(f"Test result: {result}")
    else:
        print("⚠️ Discord webhook not configured")
        print("\nSet your webhook URL:")
        print("1. Environment variable: DISCORD_WEBHOOK=your_url")
        print("2. Or pass directly: OdinDiscordNotifier('your_webhook_url')")
    
    print("\n" + setup_instructions)