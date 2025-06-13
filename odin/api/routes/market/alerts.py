# odin/api/routes/market/alerts.py
"""
Market alerts and notifications endpoints
"""

import logging
import uuid
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status

from odin.api.dependencies import get_strategy_rate_limiter, require_authentication
from odin.core.data_collector import BitcoinDataCollector

logger = logging.getLogger(__name__)
router = APIRouter()

# In-memory storage for demo (use database in production)
alerts_store = {}
user_alert_configs = {}


@router.get("/", response_model=Dict[str, Any])
async def get_market_alerts(
    active_only: bool = Query(True, description="Show only active alerts"),
    severity: Optional[str] = Query(None, description="Filter by severity"),
    current_user: dict = Depends(require_authentication),
    rate_limiter=Depends(get_strategy_rate_limiter),
):
    """Get current market alerts and notifications"""
    try:
        user_id = current_user["username"]

        # Get current market data for alert evaluation
        data_collector = BitcoinDataCollector()
        current_data = await data_collector.get_current_data()
        recent_data = await data_collector.get_recent_data(limit=50)

        if not current_data:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="Unable to fetch current market data",
            )

        # Generate real-time alerts
        generated_alerts = await generate_market_alerts(current_data, recent_data)

        # Get user's stored alerts
        user_alerts = alerts_store.get(user_id, [])

        # Combine and filter alerts
        all_alerts = generated_alerts + user_alerts

        # Filter by active status
        if active_only:
            all_alerts = [alert for alert in all_alerts if alert.get("active", True)]

        # Filter by severity
        if severity:
            valid_severities = ["low", "medium", "high", "critical"]
            if severity not in valid_severities:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Invalid severity. Must be one of: {valid_severities}",
                )
            all_alerts = [
                alert for alert in all_alerts if alert.get("severity") == severity
            ]

        # Sort by severity and timestamp
        severity_order = {"critical": 4, "high": 3, "medium": 2, "low": 1}
        all_alerts.sort(
            key=lambda x: (
                severity_order.get(x.get("severity", "low"), 1),
                x.get("timestamp", ""),
            ),
            reverse=True,
        )

        # Categorize alerts
        alert_categories = {
            "critical": [a for a in all_alerts if a.get("severity") == "critical"],
            "high": [a for a in all_alerts if a.get("severity") == "high"],
            "medium": [a for a in all_alerts if a.get("severity") == "medium"],
            "low": [a for a in all_alerts if a.get("severity") == "low"],
        }

        # Count urgent alerts requiring action
        urgent_alerts = [
            a
            for a in all_alerts
            if a.get("severity") in ["critical", "high"]
            and a.get("requires_action", False)
        ]

        return {
            "alerts": all_alerts,
            "categories": alert_categories,
            "urgent_alerts": urgent_alerts,
            "total_count": len(all_alerts),
            "urgent_count": len(urgent_alerts),
            "active_only": active_only,
            "severity_filter": severity,
            "timestamp": datetime.utcnow().isoformat(),
            "status": "success",
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting market alerts: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get market alerts",
        )


@router.post("/configure", response_model=Dict[str, Any])
async def configure_alerts(
    alert_config: Dict[str, Any],
    current_user: dict = Depends(require_authentication),
    rate_limiter=Depends(get_strategy_rate_limiter),
):
    """Configure market alert settings"""
    try:
        user_id = current_user["username"]

        # Validate alert configuration
        required_fields = ["alert_type", "conditions"]
        for field in required_fields:
            if field not in alert_config:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Missing required field: {field}",
                )

        valid_alert_types = [
            "price_threshold",
            "price_change",
            "volume_spike",
            "volatility_spike",
            "support_resistance",
            "technical_indicator",
        ]

        if alert_config["alert_type"] not in valid_alert_types:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid alert type. Must be one of: {valid_alert_types}",
            )

        # Validate conditions based on alert type
        conditions = alert_config["conditions"]
        if alert_config["alert_type"] == "price_threshold":
            if "price" not in conditions or "direction" not in conditions:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Price threshold alerts require 'price' and 'direction' conditions",
                )

        # Create alert configuration
        alert_id = str(uuid.uuid4())
        alert_configuration = {
            "id": alert_id,
            "user_id": user_id,
            "alert_type": alert_config["alert_type"],
            "conditions": conditions,
            "enabled": alert_config.get("enabled", True),
            "severity": alert_config.get("severity", "medium"),
            "notification_methods": alert_config.get(
                "notification_methods", ["in_app"]
            ),
            "created_at": datetime.utcnow().isoformat(),
            "triggered_count": 0,
            "last_triggered": None,
        }

        # Store alert configuration
        if user_id not in user_alert_configs:
            user_alert_configs[user_id] = []
        user_alert_configs[user_id].append(alert_configuration)

        logger.info(f"Alert configured for {user_id}: {alert_config['alert_type']}")

        return {
            "alert_id": alert_id,
            "alert_config": alert_configuration,
            "configured_by": user_id,
            "timestamp": datetime.utcnow().isoformat(),
            "status": "success",
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error configuring alert: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to configure alert",
        )


@router.delete("/{alert_id}", response_model=Dict[str, Any])
async def delete_alert(
    alert_id: str,
    current_user: dict = Depends(require_authentication),
    rate_limiter=Depends(get_strategy_rate_limiter),
):
    """Delete a specific alert configuration"""
    try:
        user_id = current_user["username"]

        # Find and remove alert
        user_configs = user_alert_configs.get(user_id, [])
        alert_found = False

        for i, config in enumerate(user_configs):
            if config["id"] == alert_id:
                removed_alert = user_configs.pop(i)
                alert_found = True
                break

        if not alert_found:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Alert {alert_id} not found",
            )

        logger.info(f"Alert {alert_id} deleted by {user_id}")

        return {
            "alert_id": alert_id,
            "deleted_by": user_id,
            "timestamp": datetime.utcnow().isoformat(),
            "status": "success",
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting alert {alert_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to delete alert",
        )


@router.get("/history", response_model=Dict[str, Any])
async def get_alert_history(
    hours: int = Query(168, description="Hours of alert history"),
    current_user: dict = Depends(require_authentication),
    rate_limiter=Depends(get_strategy_rate_limiter),
):
    """Get alert history for the user"""
    try:
        user_id = current_user["username"]

        # Get user's alert history (mock data for demo)
        since_time = datetime.utcnow() - timedelta(hours=hours)

        alert_history = [
            {
                "id": "hist_001",
                "alert_type": "price_threshold",
                "message": "Bitcoin price crossed $45,000",
                "severity": "high",
                "triggered_at": (datetime.utcnow() - timedelta(hours=2)).isoformat(),
                "price_at_trigger": 45000,
                "action_taken": "notification_sent",
            },
            {
                "id": "hist_002",
                "alert_type": "volume_spike",
                "message": "Volume spike detected: 300% above average",
                "severity": "medium",
                "triggered_at": (datetime.utcnow() - timedelta(hours=6)).isoformat(),
                "volume_ratio": 3.0,
                "action_taken": "notification_sent",
            },
            {
                "id": "hist_003",
                "alert_type": "volatility_spike",
                "message": "High volatility detected: 95th percentile",
                "severity": "medium",
                "triggered_at": (datetime.utcnow() - timedelta(hours=12)).isoformat(),
                "volatility_percentile": 95,
                "action_taken": "notification_sent",
            },
        ]

        # Filter by time range
        alert_history = [
            alert
            for alert in alert_history
            if datetime.fromisoformat(alert["triggered_at"]) >= since_time
        ]

        # Statistics
        history_stats = {
            "total_alerts": len(alert_history),
            "by_severity": {
                "critical": len(
                    [a for a in alert_history if a["severity"] == "critical"]
                ),
                "high": len([a for a in alert_history if a["severity"] == "high"]),
                "medium": len([a for a in alert_history if a["severity"] == "medium"]),
                "low": len([a for a in alert_history if a["severity"] == "low"]),
            },
            "by_type": {},
            "most_recent": alert_history[0]["triggered_at"] if alert_history else None,
        }

        # Count by type
        for alert in alert_history:
            alert_type = alert["alert_type"]
            history_stats["by_type"][alert_type] = (
                history_stats["by_type"].get(alert_type, 0) + 1
            )

        return {
            "alert_history": alert_history,
            "history_stats": history_stats,
            "hours_requested": hours,
            "timestamp": datetime.utcnow().isoformat(),
            "status": "success",
        }

    except Exception as e:
        logger.error(f"Error getting alert history: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get alert history",
        )


@router.get("/configurations", response_model=Dict[str, Any])
async def get_alert_configurations(
    current_user: dict = Depends(require_authentication),
    rate_limiter=Depends(get_strategy_rate_limiter),
):
    """Get user's alert configurations"""
    try:
        user_id = current_user["username"]
        user_configs = user_alert_configs.get(user_id, [])

        # Statistics about configurations
        config_stats = {
            "total_configs": len(user_configs),
            "enabled_configs": len([c for c in user_configs if c.get("enabled", True)]),
            "by_type": {},
            "by_severity": {},
        }

        for config in user_configs:
            # Count by type
            alert_type = config["alert_type"]
            config_stats["by_type"][alert_type] = (
                config_stats["by_type"].get(alert_type, 0) + 1
            )

            # Count by severity
            severity = config["severity"]
            config_stats["by_severity"][severity] = (
                config_stats["by_severity"].get(severity, 0) + 1
            )

        return {
            "alert_configurations": user_configs,
            "config_stats": config_stats,
            "timestamp": datetime.utcnow().isoformat(),
            "status": "success",
        }

    except Exception as e:
        logger.error(f"Error getting alert configurations: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get alert configurations",
        )


# Helper function to generate real-time market alerts
async def generate_market_alerts(current_data, recent_data) -> List[Dict[str, Any]]:
    """Generate alerts based on current market conditions"""
    alerts = []

    if not current_data or not recent_data:
        return alerts

    try:
        current_price = current_data.price
        prices = [point.price for point in recent_data]

        # Price change alerts
        if hasattr(current_data, "change_24h") and current_data.change_24h:
            if abs(current_data.change_24h) > 0.10:  # 10% change
                alerts.append(
                    {
                        "id": f"price_change_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}",
                        "type": "price_change",
                        "severity": (
                            "high" if abs(current_data.change_24h) > 0.15 else "medium"
                        ),
                        "message": f"Bitcoin price {'increased' if current_data.change_24h > 0 else 'decreased'} by {abs(current_data.change_24h)*100:.1f}% in 24h",
                        "current_price": current_price,
                        "change_percent": current_data.change_24h * 100,
                        "timestamp": datetime.utcnow().isoformat(),
                        "active": True,
                        "requires_action": abs(current_data.change_24h) > 0.15,
                    }
                )

        # Volume alerts
        if (
            hasattr(current_data, "volume_24h")
            and current_data.volume_24h
            and len(recent_data) > 10
        ):
            volumes = [point.volume for point in recent_data if point.volume]
            if volumes:
                avg_volume = sum(volumes) / len(volumes)
                volume_ratio = current_data.volume_24h / avg_volume

                if volume_ratio > 2.0:  # 2x average volume
                    alerts.append(
                        {
                            "id": f"volume_spike_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}",
                            "type": "volume_spike",
                            "severity": "high" if volume_ratio > 3.0 else "medium",
                            "message": f"Volume spike detected: {volume_ratio:.1f}x above average",
                            "current_volume": current_data.volume_24h,
                            "volume_ratio": volume_ratio,
                            "timestamp": datetime.utcnow().isoformat(),
                            "active": True,
                            "requires_action": volume_ratio > 3.0,
                        }
                    )

        # Volatility alerts
        if len(prices) >= 24:
            returns = [(prices[i] / prices[i + 1] - 1) for i in range(23)]
            volatility = (sum([r**2 for r in returns]) / len(returns)) ** 0.5 * (
                365**0.5
            )

            if volatility > 1.0:  # High volatility threshold
                alerts.append(
                    {
                        "id": f"volatility_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}",
                        "type": "volatility_spike",
                        "severity": "medium",
                        "message": f"High volatility detected: {volatility*100:.1f}% annualized",
                        "volatility": volatility,
                        "timestamp": datetime.utcnow().isoformat(),
                        "active": True,
                        "requires_action": False,
                    }
                )

        # Support/Resistance levels (simple implementation)
        if len(prices) >= 50:
            max_price = max(prices[:50])
            min_price = min(prices[:50])

            # Near resistance
            if current_price > max_price * 0.98:
                alerts.append(
                    {
                        "id": f"resistance_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}",
                        "type": "support_resistance",
                        "severity": "medium",
                        "message": f"Price approaching resistance level at ${max_price:,.0f}",
                        "level": max_price,
                        "level_type": "resistance",
                        "distance_percent": ((current_price / max_price) - 1) * 100,
                        "timestamp": datetime.utcnow().isoformat(),
                        "active": True,
                        "requires_action": True,
                    }
                )

            # Near support
            elif current_price < min_price * 1.02:
                alerts.append(
                    {
                        "id": f"support_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}",
                        "type": "support_resistance",
                        "severity": "medium",
                        "message": f"Price approaching support level at ${min_price:,.0f}",
                        "level": min_price,
                        "level_type": "support",
                        "distance_percent": ((current_price / min_price) - 1) * 100,
                        "timestamp": datetime.utcnow().isoformat(),
                        "active": True,
                        "requires_action": True,
                    }
                )

    except Exception as e:
        logger.error(f"Error generating market alerts: {e}")

    return alerts
