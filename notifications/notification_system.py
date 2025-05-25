# notifications/notification_system.py

import smtplib
import ssl
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import datetime
import json
import os
from typing import Dict, List, Optional
import requests
from twilio.rest import Client  # pip install twilio
import logging

class NotificationSystem:
    def __init__(self, config_path=None):
        """
        Professional notification system for trading alerts
        Supports email, SMS, Discord, Slack, and more
        """
        if config_path is None:
            current_dir = os.path.dirname(os.path.abspath(__file__))
            project_root = os.path.dirname(current_dir)
            config_path = os.path.join(project_root, 'config', 'notifications.json')
        
        self.config_path = config_path
        self.config = self.load_config()
        
        # Setup logging
        logging.basicConfig(level=logging.INFO)
        self.logger = logging.getLogger(__name__)
        
        # Alert thresholds
        self.alert_thresholds = {
            'price_change_percent': 5.0,
            'position_loss_percent': 3.0,
            'portfolio_drawdown_percent': 10.0,
            'consecutive_losses': 3,
            'daily_volume_change': 50.0
        }
        
        # Cooldown periods (minutes)
        self.cooldown_periods = {
            'price_alert': 30,
            'signal_alert': 15,
            'risk_alert': 60,
            'system_alert': 5
        }
        
        # Track last alert times
        self.last_alerts = {}
    
    def load_config(self) -> Dict:
        """Load notification configuration"""
        default_config = {
            "email": {
                "enabled": False,
                "smtp_server": "smtp.gmail.com",
                "smtp_port": 587,
                "sender_email": "",
                "sender_password": "",
                "recipient_emails": []
            },
            "sms": {
                "enabled": False,
                "twilio_sid": "",
                "twilio_token": "",
                "from_number": "",
                "to_numbers": []
            },
            "discord": {
                "enabled": False,
                "webhook_url": ""
            },
            "slack": {
                "enabled": False,
                "webhook_url": ""
            },
            "telegram": {
                "enabled": False,
                "bot_token": "",
                "chat_ids": []
            }
        }
        
        try:
            if os.path.exists(self.config_path):
                with open(self.config_path, 'r') as f:
                    config = json.load(f)
                    # Merge with defaults
                    for key in default_config:
                        if key not in config:
                            config[key] = default_config[key]
                    return config
            else:
                # Create default config file
                os.makedirs(os.path.dirname(self.config_path), exist_ok=True)
                with open(self.config_path, 'w') as f:
                    json.dump(default_config, f, indent=2)
                return default_config
        except Exception as e:
            self.logger.error(f"Error loading config: {e}")
            return default_config
    
    def save_config(self):
        """Save current configuration"""
        try:
            with open(self.config_path, 'w') as f:
                json.dump(self.config, f, indent=2)
        except Exception as e:
            self.logger.error(f"Error saving config: {e}")
    
    def can_send_alert(self, alert_type: str) -> bool:
        """Check if enough time has passed since last alert of this type"""
        now = datetime.now()
        last_alert = self.last_alerts.get(alert_type)
        
        if last_alert is None:
            return True
        
        cooldown = self.cooldown_periods.get(alert_type, 30)
        time_diff = (now - last_alert).total_seconds() / 60
        
        return time_diff >= cooldown
    
    def mark_alert_sent(self, alert_type: str):
        """Mark that an alert of this type was sent"""
        self.last_alerts[alert_type] = datetime.now()
    
    def send_email(self, subject: str, message: str, html_message: str = None) -> bool:
        """Send email notification"""
        if not self.config['email']['enabled']:
            return False
        
        try:
            # Create message
            msg = MIMEMultipart('alternative')
            msg['Subject'] = subject
            msg['From'] = self.config['email']['sender_email']
            msg['To'] = ', '.join(self.config['email']['recipient_emails'])
            
            # Add text version
            text_part = MIMEText(message, 'plain')
            msg.attach(text_part)
            
            # Add HTML version if provided
            if html_message:
                html_part = MIMEText(html_message, 'html')
                msg.attach(html_part)
            
            # Send email
            context = ssl.create_default_context()
            with smtplib.SMTP(self.config['email']['smtp_server'], self.config['email']['smtp_port']) as server:
                server.starttls(context=context)
                server.login(self.config['email']['sender_email'], self.config['email']['sender_password'])
                server.sendmail(
                    self.config['email']['sender_email'],
                    self.config['email']['recipient_emails'],
                    msg.as_string()
                )
            
            self.logger.info("Email sent successfully")
            return True
            
        except Exception as e:
            self.logger.error(f"Error sending email: {e}")
            return False
    
    def send_sms(self, message: str) -> bool:
        """Send SMS notification via Twilio"""
        if not self.config['sms']['enabled']:
            return False
        
        try:
            client = Client(self.config['sms']['twilio_sid'], self.config['sms']['twilio_token'])
            
            for number in self.config['sms']['to_numbers']:
                message_obj = client.messages.create(
                    body=message,
                    from_=self.config['sms']['from_number'],
                    to=number
                )
                self.logger.info(f"SMS sent to {number}: {message_obj.sid}")
            
            return True
            
        except Exception as e:
            self.logger.error(f"Error sending SMS: {e}")
            return False
    
    def send_discord(self, message: str, embed_data: Dict = None) -> bool:
        """Send Discord notification"""
        if not self.config['discord']['enabled']:
            return False
        
        try:
            payload = {'content': message}
            
            if embed_data:
                payload['embeds'] = [embed_data]
            
            response = requests.post(self.config['discord']['webhook_url'], json=payload)
            response.raise_for_status()
            
            self.logger.info("Discord message sent successfully")
            return True
            
        except Exception as e:
            self.logger.error(f"Error sending Discord message: {e}")
            return False
    
    def send_slack(self, message: str, blocks: List = None) -> bool:
        """Send Slack notification"""
        if not self.config['slack']['enabled']:
            return False
        
        try:
            payload = {'text': message}
            
            if blocks:
                payload['blocks'] = blocks
            
            response = requests.post(self.config['slack']['webhook_url'], json=payload)
            response.raise_for_status()
            
            self.logger.info("Slack message sent successfully")
            return True
            
        except Exception as e:
            self.logger.error(f"Error sending Slack message: {e}")
            return False
    
    def send_telegram(self, message: str) -> bool:
        """Send Telegram notification"""
        if not self.config['telegram']['enabled']:
            return False
        
        try:
            bot_token = self.config['telegram']['bot_token']
            
            for chat_id in self.config['telegram']['chat_ids']:
                url = f"https://api.telegram.org/bot{bot_token}/sendMessage"
                payload = {
                    'chat_id': chat_id,
                    'text': message,
                    'parse_mode': 'Markdown'
                }
                
                response = requests.post(url, json=payload)
                response.raise_for_status()
            
            self.logger.info("Telegram message sent successfully")
            return True
            
        except Exception as e:
            self.logger.error(f"Error sending Telegram message: {e}")
            return False
    
    def send_notification(self, message: str, alert_type: str = 'general', 
                         subject: str = None, priority: str = 'normal') -> Dict:
        """Send notification via all enabled channels"""
        if not self.can_send_alert(alert_type):
            return {'success': False, 'reason': 'Cooldown period active'}
        
        results = {}
        
        # Prepare subject
        if subject is None:
            subject = f"Bitcoin Trading Bot Alert - {alert_type.title()}"
        
        # Add timestamp to message
        timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        full_message = f"[{timestamp}] {message}"
        
        # Send via all enabled channels
        if priority in ['high', 'critical']:
            # High priority alerts go to all channels
            results['email'] = self.send_email(subject, full_message)
            results['sms'] = self.send_sms(full_message)
            results['discord'] = self.send_discord(full_message)
            results['slack'] = self.send_slack(full_message)
            results['telegram'] = self.send_telegram(full_message)
        else:
            # Normal priority - email and Discord only
            results['email'] = self.send_email(subject, full_message)
            results['discord'] = self.send_discord(full_message)
        
        # Mark alert as sent
        self.mark_alert_sent(alert_type)
        
        # Count successful sends
        successful_sends = sum(1 for result in results.values() if result)
        
        return {
            'success': successful_sends > 0,
            'successful_channels': successful_sends,
            'total_channels': len(results),
            'results': results
        }
    
    def send_trade_signal_alert(self, signal_data: Dict) -> Dict:
        """Send alert for new trading signals"""
        signal = signal_data.get('ensemble_signal', 'UNKNOWN')
        confidence = signal_data.get('confidence', 0)
        
        message = f"""
🚨 **TRADING SIGNAL ALERT** 🚨

**Signal:** {signal}
**Confidence:** {confidence:.2f}
**Market Regime:** {signal_data.get('market_regime', {}).get('regime', 'Unknown')}

**Strategy Breakdown:**
"""
        
        individual_signals = signal_data.get('individual_signals', {})
        for strategy, signal_info in individual_signals.items():
            if 'error' not in signal_info:
                message += f"• {strategy}: {signal_info.get('signal', 'N/A')} ({signal_info.get('confidence', 0):.2f})\n"
        
        priority = 'high' if confidence > 0.7 else 'normal'
        
        return self.send_notification(
            message=message,
            alert_type='signal_alert',
            subject=f"Trading Signal: {signal}",
            priority=priority
        )
    
    def send_risk_alert(self, risk_data: Dict) -> Dict:
        """Send risk management alerts"""
        drawdown = risk_data.get('current_drawdown_pct', 0)
        consecutive_losses = risk_data.get('consecutive_losses', 0)
        
        message = f"""
⚠️ **RISK MANAGEMENT ALERT** ⚠️

**Current Drawdown:** {drawdown:.2f}%
**Consecutive Losses:** {consecutive_losses}
**Total Balance:** ${risk_data.get('total_balance', 0):,.2f}
**Open Positions:** {risk_data.get('open_positions', 0)}

"""
        
        if drawdown > 15:
            message += "🔴 **HIGH DRAWDOWN WARNING** - Consider reducing position sizes\n"
        
        if consecutive_losses >= 4:
            message += "🔴 **CONSECUTIVE LOSSES** - Review strategy performance\n"
        
        priority = 'high' if drawdown > 10 or consecutive_losses >= 3 else 'normal'
        
        return self.send_notification(
            message=message,
            alert_type='risk_alert',
            subject="Risk Management Alert",
            priority=priority
        )
    
    def send_trade_execution_alert(self, trade_data: Dict) -> Dict:
        """Send alert for trade executions"""
        action = trade_data.get('action', 'UNKNOWN')
        symbol = trade_data.get('symbol', 'BTC')
        price = trade_data.get('price', 0)
        quantity = trade_data.get('quantity', 0)
        strategy = trade_data.get('strategy', 'Unknown')
        
        if action.upper() == 'OPEN':
            message = f"""
📈 **POSITION OPENED** 📈

**Symbol:** {symbol}
**Strategy:** {strategy}
**Entry Price:** ${price:,.2f}
**Quantity:** {quantity:.6f}
**Position Value:** ${price * quantity:,.2f}
**Stop Loss:** ${trade_data.get('stop_loss', 0):,.2f}
**Take Profit:** ${trade_data.get('take_profit', 0):,.2f}
"""
        else:  # CLOSE
            pnl = trade_data.get('pnl', 0)
            pnl_pct = trade_data.get('pnl_percent', 0)
            exit_reason = trade_data.get('exit_reason', 'Unknown')
            
            emoji = "🟢" if pnl > 0 else "🔴"
            message = f"""
{emoji} **POSITION CLOSED** {emoji}

**Symbol:** {symbol}
**Strategy:** {strategy}
**Exit Price:** ${price:,.2f}
**P&L:** ${pnl:,.2f} ({pnl_pct:+.2f}%)
**Exit Reason:** {exit_reason}
**Duration:** {trade_data.get('duration', 0):.1f} hours
"""
        
        priority = 'high' if abs(trade_data.get('pnl_percent', 0)) > 5 else 'normal'
        
        return self.send_notification(
            message=message,
            alert_type='trade_alert',
            subject=f"Trade {action.title()}: {symbol}",
            priority=priority
        )
    
    def send_price_alert(self, price_data: Dict) -> Dict:
        """Send price movement alerts"""
        current_price = price_data.get('current_price', 0)
        change_24h = price_data.get('change_24h', 0)
        
        if abs(change_24h) < self.alert_thresholds['price_change_percent']:
            return {'success': False, 'reason': 'Price change below threshold'}
        
        emoji = "🚀" if change_24h > 0 else "📉"
        direction = "up" if change_24h > 0 else "down"
        
        message = f"""
{emoji} **SIGNIFICANT PRICE MOVEMENT** {emoji}

**Current Price:** ${current_price:,.2f}
**24h Change:** {change_24h:+.2f}%
**Direction:** {direction.upper()}

**Market Data:**
• High 24h: ${price_data.get('high_24h', 0):,.2f}
• Low 24h: ${price_data.get('low_24h', 0):,.2f}
• Volume 24h: ${price_data.get('volume_24h', 0):,.0f}
"""
        
        priority = 'high' if abs(change_24h) > 10 else 'normal'
        
        return self.send_notification(
            message=message,
            alert_type='price_alert',
            subject=f"Bitcoin {direction.title()} {abs(change_24h):.1f}%",
            priority=priority
        )
    
    def send_system_alert(self, message: str, alert_level: str = 'info') -> Dict:
        """Send system status alerts"""
        level_emojis = {
            'info': 'ℹ️',
            'warning': '⚠️',
            'error': '🔴',
            'critical': '🚨'
        }
        
        emoji = level_emojis.get(alert_level, 'ℹ️')
        
        formatted_message = f"""
{emoji} **SYSTEM {alert_level.upper()}** {emoji}

{message}

**Timestamp:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
"""
        
        priority = 'high' if alert_level in ['error', 'critical'] else 'normal'
        
        return self.send_notification(
            message=formatted_message,
            alert_type='system_alert',
            subject=f"System {alert_level.title()}",
            priority=priority
        )


# notifications/trade_scheduler.py

import schedule
import time
import threading
from datetime import datetime, timedelta
from typing import Dict, List, Callable
import sqlite3
import os

class TradeScheduler:
    def __init__(self, db_path=None):
        """
        Professional trade scheduling system
        """
        if db_path is None:
            current_dir = os.path.dirname(os.path.abspath(__file__))
            project_root = os.path.dirname(current_dir)
            db_path = os.path.join(project_root, 'data', 'bitcoin_data.db')
        
        self.db_path = db_path
        self.scheduled_jobs = {}
        self.running = False
        self.scheduler_thread = None
        
        self.setup_scheduler_database()
    
    def setup_scheduler_database(self):
        """Setup database for scheduled tasks"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS scheduled_tasks (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                task_name TEXT UNIQUE,
                task_type TEXT,
                schedule_pattern TEXT,
                parameters TEXT,
                last_run TEXT,
                next_run TEXT,
                status TEXT,
                created_at TEXT
            )
        ''')
        
        conn.commit()
        conn.close()
    
    def add_recurring_task(self, task_name: str, task_function: Callable, 
                          schedule_pattern: str, **kwargs) -> bool:
        """
        Add a recurring scheduled task
        
        Args:
            task_name: Unique name for the task
            task_function: Function to execute
            schedule_pattern: Schedule pattern (e.g., 'daily', 'hourly', 'weekly')
            **kwargs: Additional parameters for the task
        """
        try:
            # Schedule the task
            if schedule_pattern == 'daily':
                time_str = kwargs.get('time', '09:00')
                schedule.every().day.at(time_str).do(self._execute_task, task_name, task_function, **kwargs)
            elif schedule_pattern == 'hourly':
                schedule.every().hour.do(self._execute_task, task_name, task_function, **kwargs)
            elif schedule_pattern == 'weekly':
                day = kwargs.get('day', 'monday')
                time_str = kwargs.get('time', '09:00')
                getattr(schedule.every(), day).at(time_str).do(self._execute_task, task_name, task_function, **kwargs)
            elif 'minutes' in schedule_pattern:
                minutes = int(schedule_pattern.split()[0])
                schedule.every(minutes).minutes.do(self._execute_task, task_name, task_function, **kwargs)
            
            # Store in database
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute('''
                INSERT OR REPLACE INTO scheduled_tasks 
                (task_name, task_type, schedule_pattern, parameters, status, created_at)
                VALUES (?, ?, ?, ?, ?, ?)
            ''', (
                task_name, 'recurring', schedule_pattern, 
                str(kwargs), 'active', datetime.now().isoformat()
            ))
            
            conn.commit()
            conn.close()
            
            return True
            
        except Exception as e:
            print(f"Error adding scheduled task: {e}")
            return False
    
    def _execute_task(self, task_name: str, task_function: Callable, **kwargs):
        """Execute a scheduled task"""
        try:
            print(f"Executing scheduled task: {task_name}")
            result = task_function(**kwargs)
            
            # Update database
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute('''
                UPDATE scheduled_tasks 
                SET last_run = ? 
                WHERE task_name = ?
            ''', (datetime.now().isoformat(), task_name))
            
            conn.commit()
            conn.close()
            
            return result
            
        except Exception as e:
            print(f"Error executing scheduled task {task_name}: {e}")
    
    def start_scheduler(self):
        """Start the scheduler in a background thread"""
        if self.running:
            return
        
        self.running = True
        
        def run_scheduler():
            while self.running:
                schedule.run_pending()
                time.sleep(60)  # Check every minute
        
        self.scheduler_thread = threading.Thread(target=run_scheduler, daemon=True)
        self.scheduler_thread.start()
        print("Trade scheduler started")
    
    def stop_scheduler(self):
        """Stop the scheduler"""
        self.running = False
        if self.scheduler_thread:
            self.scheduler_thread.join()
        print("Trade scheduler stopped")
    
    def get_scheduled_tasks(self) -> List[Dict]:
        """Get all scheduled tasks"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('SELECT * FROM scheduled_tasks ORDER BY created_at DESC')
        tasks = []
        
        for row in cursor.fetchall():
            tasks.append({
                'id': row[0],
                'task_name': row[1],
                'task_type': row[2],
                'schedule_pattern': row[3],
                'parameters': row[4],
                'last_run': row[5],
                'next_run': row[6],
                'status': row[7],
                'created_at': row[8]
            })
        
        conn.close()
        return tasks