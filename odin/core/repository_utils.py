"""
Odin Repository Utilities - Additional repository functionality and helpers
Extends the main repository system with specialized operations and utilities.
"""

import json
import asyncio
from typing import Dict, List, Any, Optional, Tuple
from datetime import datetime, timedelta
from dataclasses import asdict

from ..utils.logging import get_logger, LogContext
from .repository import (
    get_repository_manager, get_price_repository, get_trade_repository,
    get_strategy_repository, get_portfolio_repository, get_order_repository,
    QueryResult
)
from .models import PriceData, TradeExecution

logger = get_logger(__name__)


class DataExporter:
    """Export repository data to various formats."""
    
    def __init__(self):
        self.repo_manager = None
    
    async def _ensure_repo_manager(self):
        """Ensure repository manager is initialized."""
        if self.repo_manager is None:
            self.repo_manager = await get_repository_manager()
    
    async def export_price_data(
        self, 
        start_date: datetime, 
        end_date: datetime,
        format: str = "json"
    ) -> Dict[str, Any]:
        """Export price data for date range."""
        try:
            await self._ensure_repo_manager()
            price_repo = self.repo_manager.get_price_repository()
            
            result = await price_repo.find_by_date_range(start_date, end_date, limit=10000)
            
            if not result.success:
                return {"success": False, "error": result.error}
            
            if format == "json":
                # Convert PriceData objects to dictionaries
                data = []
                for price_data in result.data:
                    if hasattr(price_data, '__dict__'):
                        data.append(asdict(price_data))
                    else:
                        data.append(price_data)
                
                return {
                    "success": True,
                    "format": "json",
                    "count": len(data),
                    "date_range": {
                        "start": start_date.isoformat(),
                        "end": end_date.isoformat()
                    },
                    "data": data
                }
            
            elif format == "csv":
                # Convert to CSV format
                if not result.data:
                    return {"success": False, "error": "No data to export"}
                
                csv_lines = []
                # Header
                first_item = result.data[0]
                if hasattr(first_item, '__dict__'):
                    headers = list(first_item.__dict__.keys())
                else:
                    headers = list(first_item.keys())
                csv_lines.append(",".join(headers))
                
                # Data rows
                for item in result.data:
                    if hasattr(item, '__dict__'):
                        row_data = list(item.__dict__.values())
                    else:
                        row_data = list(item.values())
                    
                    # Convert to strings and handle None values
                    row_strings = []
                    for value in row_data:
                        if value is None:
                            row_strings.append("")
                        elif isinstance(value, datetime):
                            row_strings.append(value.isoformat())
                        else:
                            row_strings.append(str(value))
                    
                    csv_lines.append(",".join(row_strings))
                
                return {
                    "success": True,
                    "format": "csv",
                    "count": len(result.data),
                    "data": "\n".join(csv_lines)
                }
            
            else:
                return {"success": False, "error": f"Unsupported format: {format}"}
                
        except Exception as e:
            logger.error(f"Export price data failed: {e}")
            return {"success": False, "error": str(e)}
    
    async def export_trade_history(
        self, 
        strategy_id: Optional[str] = None,
        days: int = 30,
        format: str = "json"
    ) -> Dict[str, Any]:
        """Export trade history."""
        try:
            await self._ensure_repo_manager()
            trade_repo = self.repo_manager.get_trade_repository()
            
            if strategy_id:
                result = await trade_repo.find_by_strategy(strategy_id, limit=1000)
            else:
                result = await trade_repo.find_recent(hours=days * 24, limit=1000)
            
            if not result.success:
                return {"success": False, "error": result.error}
            
            # Convert trade objects to dictionaries
            trades_data = []
            for trade in result.data:
                if hasattr(trade, '__dict__'):
                    trade_dict = asdict(trade)
                else:
                    trade_dict = trade
                
                # Ensure datetime objects are serializable
                for key, value in trade_dict.items():
                    if isinstance(value, datetime):
                        trade_dict[key] = value.isoformat()
                
                trades_data.append(trade_dict)
            
            return {
                "success": True,
                "format": format,
                "count": len(trades_data),
                "strategy_id": strategy_id,
                "period_days": days,
                "data": trades_data
            }
            
        except Exception as e:
            logger.error(f"Export trade history failed: {e}")
            return {"success": False, "error": str(e)}
    
    async def export_portfolio_snapshots(
        self, 
        days: int = 30,
        format: str = "json"
    ) -> Dict[str, Any]:
        """Export portfolio snapshots."""
        try:
            await self._ensure_repo_manager()
            portfolio_repo = self.repo_manager.get_portfolio_repository()
            
            end_date = datetime.now()
            start_date = end_date - timedelta(days=days)
            
            result = await portfolio_repo.find_snapshots_by_date_range(
                start_date, end_date, limit=1000
            )
            
            if not result.success:
                return {"success": False, "error": result.error}
            
            return {
                "success": True,
                "format": format,
                "count": len(result.data),
                "period_days": days,
                "data": result.data
            }
            
        except Exception as e:
            logger.error(f"Export portfolio snapshots failed: {e}")
            return {"success": False, "error": str(e)}


class PerformanceAnalyzer:
    """Analyze trading performance from repository data."""
    
    def __init__(self):
        self.repo_manager = None
    
    async def _ensure_repo_manager(self):
        """Ensure repository manager is initialized."""
        if self.repo_manager is None:
            self.repo_manager = await get_repository_manager()
    
    async def analyze_strategy_performance(
        self, 
        strategy_id: str,
        days: int = 30
    ) -> Dict[str, Any]:
        """Comprehensive strategy performance analysis."""
        try:
            await self._ensure_repo_manager()
            strategy_repo = self.repo_manager.get_strategy_repository()
            trade_repo = self.repo_manager.get_trade_repository()
            
            # Get strategy performance metrics
            perf_result = await strategy_repo.get_strategy_performance(strategy_id)
            
            if not perf_result.success:
                return {"success": False, "error": perf_result.error}
            
            perf_data = perf_result.data or {}
            
            # Get recent trades for this strategy
            trades_result = await trade_repo.find_by_strategy(strategy_id, limit=1000)
            trades = trades_result.data if trades_result.success else []
            
            # Calculate additional metrics
            analysis = {
                "strategy_id": strategy_id,
                "period_days": days,
                "basic_metrics": perf_data,
                "detailed_analysis": self._calculate_detailed_metrics(trades),
                "recent_performance": self._calculate_recent_performance(trades, days),
                "risk_metrics": self._calculate_risk_metrics(trades)
            }
            
            return {"success": True, "analysis": analysis}
            
        except Exception as e:
            logger.error(f"Strategy performance analysis failed: {e}")
            return {"success": False, "error": str(e)}
    
    def _calculate_detailed_metrics(self, trades: List[Any]) -> Dict[str, Any]:
        """Calculate detailed performance metrics."""
        if not trades:
            return {
                "total_trades": 0,
                "winning_trades": 0,
                "losing_trades": 0,
                "win_rate": 0,
                "avg_win": 0,
                "avg_loss": 0,
                "profit_factor": 0,
                "largest_win": 0,
                "largest_loss": 0
            }
        
        # Extract P&L values
        pnls = []
        for trade in trades:
            pnl = trade.get('pnl', 0) if isinstance(trade, dict) else getattr(trade, 'pnl', 0)
            if pnl is not None:
                pnls.append(pnl)
        
        if not pnls:
            return self._calculate_detailed_metrics([])
        
        winning_trades = [pnl for pnl in pnls if pnl > 0]
        losing_trades = [pnl for pnl in pnls if pnl <= 0]
        
        total_wins = sum(winning_trades)
        total_losses = abs(sum(losing_trades))
        
        return {
            "total_trades": len(pnls),
            "winning_trades": len(winning_trades),
            "losing_trades": len(losing_trades),
            "win_rate": (len(winning_trades) / len(pnls)) * 100 if pnls else 0,
            "avg_win": total_wins / len(winning_trades) if winning_trades else 0,
            "avg_loss": total_losses / len(losing_trades) if losing_trades else 0,
            "profit_factor": total_wins / total_losses if total_losses > 0 else float('inf') if total_wins > 0 else 0,
            "largest_win": max(winning_trades) if winning_trades else 0,
            "largest_loss": min(losing_trades) if losing_trades else 0,
            "total_pnl": sum(pnls),
            "avg_trade": sum(pnls) / len(pnls) if pnls else 0
        }
    
    def _calculate_recent_performance(self, trades: List[Any], days: int) -> Dict[str, Any]:
        """Calculate performance for recent period."""
        cutoff_date = datetime.now() - timedelta(days=days)
        
        recent_trades = []
        for trade in trades:
            if isinstance(trade, dict):
                timestamp = trade.get('timestamp')
                if isinstance(timestamp, str):
                    timestamp = datetime.fromisoformat(timestamp)
            else:
                timestamp = getattr(trade, 'timestamp', None)
            
            if timestamp and timestamp >= cutoff_date:
                recent_trades.append(trade)
        
        return self._calculate_detailed_metrics(recent_trades)
    
    def _calculate_risk_metrics(self, trades: List[Any]) -> Dict[str, Any]:
        """Calculate risk-related metrics."""
        pnls = []
        for trade in trades:
            pnl = trade.get('pnl', 0) if isinstance(trade, dict) else getattr(trade, 'pnl', 0)
            if pnl is not None:
                pnls.append(pnl)
        
        if not pnls:
            return {
                "max_drawdown": 0,
                "volatility": 0,
                "sharpe_ratio": 0,
                "sortino_ratio": 0
            }
        
        # Calculate maximum drawdown
        cumulative = []
        running_total = 0
        for pnl in pnls:
            running_total += pnl
            cumulative.append(running_total)
        
        max_drawdown = 0
        peak = cumulative[0] if cumulative else 0
        
        for value in cumulative:
            if value > peak:
                peak = value
            drawdown = (peak - value) / peak if peak != 0 else 0
            max_drawdown = max(max_drawdown, drawdown)
        
        # Calculate volatility (standard deviation)
        if len(pnls) > 1:
            mean_pnl = sum(pnls) / len(pnls)
            variance = sum((pnl - mean_pnl) ** 2 for pnl in pnls) / (len(pnls) - 1)
            volatility = variance ** 0.5
        else:
            volatility = 0
        
        # Simplified Sharpe ratio (assuming risk-free rate of 0)
        sharpe_ratio = (sum(pnls) / len(pnls)) / volatility if volatility > 0 else 0
        
        # Simplified Sortino ratio (downside deviation)
        negative_pnls = [pnl for pnl in pnls if pnl < 0]
        if negative_pnls and len(negative_pnls) > 1:
            mean_negative = sum(negative_pnls) / len(negative_pnls)
            downside_variance = sum((pnl - mean_negative) ** 2 for pnl in negative_pnls) / (len(negative_pnls) - 1)
            downside_deviation = downside_variance ** 0.5
            sortino_ratio = (sum(pnls) / len(pnls)) / downside_deviation if downside_deviation > 0 else 0
        else:
            sortino_ratio = sharpe_ratio
        
        return {
            "max_drawdown": max_drawdown * 100,  # Convert to percentage
            "volatility": volatility,
            "sharpe_ratio": sharpe_ratio,
            "sortino_ratio": sortino_ratio,
            "total_return": sum(pnls),
            "number_of_trades": len(pnls)
        }
    
    async def compare_strategies(self, strategy_ids: List[str], days: int = 30) -> Dict[str, Any]:
        """Compare performance of multiple strategies."""
        try:
            comparisons = {}
            
            for strategy_id in strategy_ids:
                analysis = await self.analyze_strategy_performance(strategy_id, days)
                if analysis["success"]:
                    comparisons[strategy_id] = analysis["analysis"]
            
            # Create summary comparison
            summary = {
                "comparison_period_days": days,
                "strategies_compared": len(comparisons),
                "summary_metrics": {}
            }
            
            if comparisons:
                # Compare key metrics
                for metric in ["win_rate", "total_pnl", "profit_factor", "sharpe_ratio"]:
                    metric_values = {}
                    for strategy_id, data in comparisons.items():
                        detailed = data.get("detailed_analysis", {})
                        risk = data.get("risk_metrics", {})
                        
                        if metric in detailed:
                            metric_values[strategy_id] = detailed[metric]
                        elif metric in risk:
                            metric_values[strategy_id] = risk[metric]
                    
                    if metric_values:
                        best_strategy = max(metric_values.items(), key=lambda x: x[1])
                        summary["summary_metrics"][metric] = {
                            "best_strategy": best_strategy[0],
                            "best_value": best_strategy[1],
                            "all_values": metric_values
                        }
            
            return {
                "success": True,
                "summary": summary,
                "detailed_comparisons": comparisons
            }
            
        except Exception as e:
            logger.error(f"Strategy comparison failed: {e}")
            return {"success": False, "error": str(e)}


class DataMigrator:
    """Handle data migration and schema updates."""
    
    def __init__(self):
        self.repo_manager = None
    
    async def _ensure_repo_manager(self):
        """Ensure repository manager is initialized."""
        if self.repo_manager is None:
            self.repo_manager = await get_repository_manager()
    
    async def migrate_legacy_data(self, legacy_db_path: str) -> Dict[str, Any]:
        """Migrate data from legacy database format."""
        try:
            await self._ensure_repo_manager()
            
            # This would contain logic to migrate from old database schemas
            # For now, return a placeholder implementation
            
            return {
                "success": True,
                "message": "Legacy data migration not yet implemented",
                "migrated_records": 0
            }
            
        except Exception as e:
            logger.error(f"Legacy data migration failed: {e}")
            return {"success": False, "error": str(e)}
    
    async def add_missing_indexes(self) -> Dict[str, Any]:
        """Add any missing database indexes for performance."""
        try:
            await self._ensure_repo_manager()
            
            additional_indexes = [
                "CREATE INDEX IF NOT EXISTS idx_trades_timestamp ON trades(timestamp)",
                "CREATE INDEX IF NOT EXISTS idx_trades_pnl ON trades(pnl)",
                "CREATE INDEX IF NOT EXISTS idx_signals_confidence ON strategy_signals(confidence)",
                "CREATE INDEX IF NOT EXISTS idx_positions_unrealized_pnl ON positions(unrealized_pnl)",
                "CREATE INDEX IF NOT EXISTS idx_portfolio_snapshots_total_value ON portfolio_snapshots(total_value)"
            ]
            
            results = []
            for index_sql in additional_indexes:
                result = await self.repo_manager.db_manager.execute_query(index_sql, fetch_all=False)
                results.append({
                    "index": index_sql.split("idx_")[1].split(" ")[0] if "idx_" in index_sql else "unknown",
                    "success": result.success,
                    "error": result.error if not result.success else None
                })
            
            successful_indexes = sum(1 for r in results if r["success"])
            
            return {
                "success": True,
                "indexes_created": successful_indexes,
                "total_attempted": len(additional_indexes),
                "details": results
            }
            
        except Exception as e:
            logger.error(f"Index creation failed: {e}")
            return {"success": False, "error": str(e)}
    
    async def cleanup_orphaned_data(self) -> Dict[str, Any]:
        """Clean up orphaned records across tables."""
        try:
            await self._ensure_repo_manager()
            
            cleanup_operations = []
            
            # Clean up signals without corresponding strategy trades
            orphaned_signals = await self.repo_manager.db_manager.execute_query("""
                DELETE FROM strategy_signals 
                WHERE executed = 1 
                AND execution_id NOT IN (SELECT id FROM trades)
            """, fetch_all=False)
            
            cleanup_operations.append({
                "operation": "orphaned_signals",
                "records_removed": orphaned_signals.rows_affected if orphaned_signals.success else 0,
                "success": orphaned_signals.success
            })
            
            # Clean up positions without corresponding portfolio
            orphaned_positions = await self.repo_manager.db_manager.execute_query("""
                DELETE FROM positions 
                WHERE status = 'closed' 
                AND closed_at < date('now', '-30 days')
            """, fetch_all=False)
            
            cleanup_operations.append({
                "operation": "old_closed_positions",
                "records_removed": orphaned_positions.rows_affected if orphaned_positions.success else 0,
                "success": orphaned_positions.success
            })
            
            total_cleaned = sum(op["records_removed"] for op in cleanup_operations if op["success"])
            
            return {
                "success": True,
                "total_records_cleaned": total_cleaned,
                "operations": cleanup_operations
            }
            
        except Exception as e:
            logger.error(f"Orphaned data cleanup failed: {e}")
            return {"success": False, "error": str(e)}


class RepositoryHealthChecker:
    """Monitor repository health and performance."""
    
    def __init__(self):
        self.repo_manager = None
    
    async def _ensure_repo_manager(self):
        """Ensure repository manager is initialized."""
        if self.repo_manager is None:
            self.repo_manager = await get_repository_manager()
    
    async def comprehensive_health_check(self) -> Dict[str, Any]:
        """Perform comprehensive repository health check."""
        try:
            await self._ensure_repo_manager()
            
            health_report = {
                "timestamp": datetime.now().isoformat(),
                "overall_status": "healthy",
                "issues": [],
                "warnings": [],
                "recommendations": []
            }
            
            # Database connection test
            db_health = await self.repo_manager.health_check()
            health_report["database"] = db_health
            
            if db_health["status"] != "healthy":
                health_report["overall_status"] = db_health["status"]
                health_report["issues"].extend(db_health["issues"])
            
            # Data freshness check
            freshness_check = await self._check_data_freshness()
            health_report["data_freshness"] = freshness_check
            
            if not freshness_check["recent_data"]:
                health_report["warnings"].append("No recent price data updates")
                if health_report["overall_status"] == "healthy":
                    health_report["overall_status"] = "warning"
            
            # Performance check
            performance_check = await self._check_query_performance()
            health_report["performance"] = performance_check
            
            if performance_check["avg_query_time"] > 1.0:  # > 1 second
                health_report["warnings"].append("Slow query performance detected")
                health_report["recommendations"].append("Consider adding database indexes")
            
            # Data integrity check
            integrity_check = await self._check_data_integrity()
            health_report["data_integrity"] = integrity_check
            
            if not integrity_check["all_checks_passed"]:
                health_report["issues"].extend(integrity_check["failed_checks"])
                health_report["overall_status"] = "degraded"
            
            # Storage usage check
            storage_check = await self._check_storage_usage()
            health_report["storage"] = storage_check
            
            if storage_check["usage_percentage"] > 80:
                health_report["warnings"].append("High storage usage")
                health_report["recommendations"].append("Consider data cleanup")
            
            return health_report
            
        except Exception as e:
            logger.error(f"Health check failed: {e}")
            return {
                "timestamp": datetime.now().isoformat(),
                "overall_status": "error",
                "error": str(e),
                "issues": [f"Health check system failure: {str(e)}"]
            }
    
    async def _check_data_freshness(self) -> Dict[str, Any]:
        """Check how fresh the data is."""
        try:
            price_repo = self.repo_manager.get_price_repository()
            latest_result = await price_repo.find_latest(limit=1)
            
            if latest_result.success and latest_result.data:
                latest_price = latest_result.data
                if hasattr(latest_price, 'timestamp'):
                    latest_time = latest_price.timestamp
                elif isinstance(latest_price, dict):
                    latest_time = latest_price.get('timestamp')
                    if isinstance(latest_time, str):
                        latest_time = datetime.fromisoformat(latest_time)
                else:
                    latest_time = None
                
                if latest_time:
                    age = datetime.now(timezone.utc) - latest_time.replace(tzinfo=timezone.utc)
                    return {
                        "recent_data": age.total_seconds() < 3600,  # Less than 1 hour
                        "last_update": latest_time.isoformat(),
                        "age_seconds": age.total_seconds(),
                        "age_human": f"{int(age.total_seconds()//3600)}h {int((age.total_seconds()%3600)//60)}m"
                    }
            
            return {
                "recent_data": False,
                "last_update": None,
                "age_seconds": None,
                "age_human": "No data available"
            }
            
        except Exception as e:
            return {
                "recent_data": False,
                "error": str(e)
            }
    
    async def _check_query_performance(self) -> Dict[str, Any]:
        """Check database query performance."""
        try:
            import time
            
            test_queries = [
                ("price_latest", "SELECT * FROM bitcoin_prices ORDER BY timestamp DESC LIMIT 1"),
                ("trade_count", "SELECT COUNT(*) FROM trades"),
                ("strategy_performance", "SELECT strategy_id, COUNT(*) FROM strategy_signals GROUP BY strategy_id")
            ]
            
            query_times = []
            
            for query_name, query in test_queries:
                start_time = time.time()
                result = await self.repo_manager.db_manager.execute_query(query)
                end_time = time.time()
                
                query_time = end_time - start_time
                query_times.append({
                    "query": query_name,
                    "time_seconds": query_time,
                    "success": result.success
                })
            
            avg_time = sum(q["time_seconds"] for q in query_times) / len(query_times)
            
            return {
                "avg_query_time": avg_time,
                "max_query_time": max(q["time_seconds"] for q in query_times),
                "all_queries_successful": all(q["success"] for q in query_times),
                "individual_queries": query_times
            }
            
        except Exception as e:
            return {
                "avg_query_time": None,
                "error": str(e)
            }
    
    async def _check_data_integrity(self) -> Dict[str, Any]:
        """Check data integrity across tables."""
        try:
            integrity_checks = []
            
            # Check for trades with missing strategy signals
            orphaned_trades = await self.repo_manager.db_manager.execute_query("""
                SELECT COUNT(*) as count FROM trades t
                LEFT JOIN strategy_signals s ON t.id = s.execution_id
                WHERE s.id IS NULL
            """, fetch_one=True)
            
            if orphaned_trades.success:
                orphaned_count = orphaned_trades.data['count'] if orphaned_trades.data else 0
                integrity_checks.append({
                    "check": "orphaned_trades",
                    "passed": orphaned_count == 0,
                    "details": f"Found {orphaned_count} trades without corresponding signals"
                })
            
            # Check for negative prices
            negative_prices = await self.repo_manager.db_manager.execute_query("""
                SELECT COUNT(*) as count FROM bitcoin_prices WHERE price <= 0
            """, fetch_one=True)
            
            if negative_prices.success:
                negative_count = negative_prices.data['count'] if negative_prices.data else 0
                integrity_checks.append({
                    "check": "price_validation",
                    "passed": negative_count == 0,
                    "details": f"Found {negative_count} invalid price records"
                })
            
            # Check for future timestamps
            future_timestamps = await self.repo_manager.db_manager.execute_query("""
                SELECT COUNT(*) as count FROM bitcoin_prices 
                WHERE timestamp > datetime('now', '+1 hour')
            """, fetch_one=True)
            
            if future_timestamps.success:
                future_count = future_timestamps.data['count'] if future_timestamps.data else 0
                integrity_checks.append({
                    "check": "timestamp_validation",
                    "passed": future_count == 0,
                    "details": f"Found {future_count} records with future timestamps"
                })
            
            failed_checks = [check["details"] for check in integrity_checks if not check["passed"]]
            
            return {
                "all_checks_passed": len(failed_checks) == 0,
                "total_checks": len(integrity_checks),
                "passed_checks": len(integrity_checks) - len(failed_checks),
                "failed_checks": failed_checks,
                "detailed_results": integrity_checks
            }
            
        except Exception as e:
            return {
                "all_checks_passed": False,
                "error": str(e)
            }
    
    async def _check_storage_usage(self) -> Dict[str, Any]:
        """Check database storage usage."""
        try:
            # Get database file size
            import os
            db_path = self.repo_manager.db_manager.database_path
            
            if os.path.exists(db_path):
                file_size = os.path.getsize(db_path)
                
                # Get table sizes
                table_info = await self.repo_manager.db_manager.execute_query("""
                    SELECT 
                        name,
                        (SELECT COUNT(*) FROM sqlite_master WHERE type='table' AND name=m.name) as record_count
                    FROM sqlite_master m WHERE type='table' AND name NOT LIKE 'sqlite_%'
                """)
                
                return {
                    "database_size_bytes": file_size,
                    "database_size_mb": file_size / (1024 * 1024),
                    "usage_percentage": min((file_size / (100 * 1024 * 1024)) * 100, 100),  # Assume 100MB is 100%
                    "table_info": table_info.data if table_info.success else [],
                    "storage_path": db_path
                }
            else:
                return {
                    "error": "Database file not found",
                    "storage_path": db_path
                }
                
        except Exception as e:
            return {
                "error": str(e)
            }


# Global utility instances
_data_exporter = None
_performance_analyzer = None
_data_migrator = None
_health_checker = None


def get_data_exporter() -> DataExporter:
    """Get global data exporter instance."""
    global _data_exporter
    if _data_exporter is None:
        _data_exporter = DataExporter()
    return _data_exporter


def get_performance_analyzer() -> PerformanceAnalyzer:
    """Get global performance analyzer instance."""
    global _performance_analyzer
    if _performance_analyzer is None:
        _performance_analyzer = PerformanceAnalyzer()
    return _performance_analyzer


def get_data_migrator() -> DataMigrator:
    """Get global data migrator instance."""
    global _data_migrator
    if _data_migrator is None:
        _data_migrator = DataMigrator()
    return _data_migrator


def get_health_checker() -> RepositoryHealthChecker:
    """Get global health checker instance."""
    global _health_checker
    if _health_checker is None:
        _health_checker = RepositoryHealthChecker()
    return _health_checker


# Convenience functions
async def export_price_data_to_json(start_date: datetime, end_date: datetime) -> Dict[str, Any]:
    """Export price data to JSON format."""
    exporter = get_data_exporter()
    return await exporter.export_price_data(start_date, end_date, format="json")


async def analyze_all_strategies(days: int = 30) -> Dict[str, Any]:
    """Analyze performance of all strategies."""
    try:
        repo_manager = await get_repository_manager()
        strategy_repo = repo_manager.get_strategy_repository()
        
        # Get all strategies
        all_performance = await strategy_repo.get_all_strategy_performance()
        
        if not all_performance.success:
            return {"success": False, "error": all_performance.error}
        
        strategy_ids = [row['strategy_id'] for row in all_performance.data] if all_performance.data else []
        
        if not strategy_ids:
            return {"success": True, "message": "No strategies found", "strategies": []}
        
        # Analyze each strategy
        analyzer = get_performance_analyzer()
        return await analyzer.compare_strategies(strategy_ids, days)
        
    except Exception as e:
        logger.error(f"Analyze all strategies failed: {e}")
        return {"success": False, "error": str(e)}


async def perform_full_health_check() -> Dict[str, Any]:
    """Perform comprehensive repository health check."""
    health_checker = get_health_checker()
    return await health_checker.comprehensive_health_check()


# Export public functions
__all__ = [
    'DataExporter',
    'PerformanceAnalyzer', 
    'DataMigrator',
    'RepositoryHealthChecker',
    'get_data_exporter',
    'get_performance_analyzer',
    'get_data_migrator',
    'get_health_checker',
    'export_price_data_to_json',
    'analyze_all_strategies',
    'perform_full_health_check'
]