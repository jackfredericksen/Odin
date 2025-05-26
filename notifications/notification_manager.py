"""
Basic Notification Manager
"""

from typing import Dict, List
import logging

logger = logging.getLogger(__name__)

class NotificationManager:
    """Centralized notification system"""
    
    def __init__(self, config: Dict = None):
        self.config = config or {}
        self.enabled = self.config.get('enabled', True)
        self.notifications_sent = []
        
    def send_trade_notification(self, trade_result: Dict):
        """Send trade execution notification"""
        try:
            if not self.enabled:
                return
            
            message = f"Trade executed: {trade_result.get('action', 'Unknown')} at ${trade_result.get('price', 0):,.2f}"
            logger.info(f"📧 Notification: {message}")
            
            # Store notification
            self.notifications_sent.append({
                'message': message,
                'timestamp': pd.Timestamp.now(),
                'type': 'trade'
            })
            
        except Exception as e:
            logger.error(f"Error sending trade notification: {e}")
    
    def send_alert(self, title: str, message: str, level: str = 'info'):
        """Send general alert"""
        try:
            if not self.enabled:
                return
                
            logger.info(f"🚨 Alert [{level}]: {title} - {message}")
            
            self.notifications_sent.append({
                'title': title,
                'message': message,
                'level': level,
                'timestamp': pd.Timestamp.now(),
                'type': 'alert'
            })
            
        except Exception as e:
            logger.error(f"Error sending alert: {e}")
    
    def get_notification_history(self) -> List[Dict]:
        """Get notification history"""
        return self.notifications_sent[-50:]  # Last 50 notifications
