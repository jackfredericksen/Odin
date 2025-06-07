# odin/main.py
"""
Enhanced Odin Main Application with AI Features
Integrates regime detection and adaptive strategies with existing trading bot
"""

import asyncio
import logging
import sys
import os
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse
import uvicorn

# Add the project root to Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Import Odin components
from config import get_config
from api.app import create_app
from core.data_collector import DataCollector
from core.database import Database
from core.trading_engine import TradingEngine
from core.portfolio_manager import PortfolioManager
from core.risk_manager import RiskManager

# Import AI components
from ai.regime_detection.regime_detector import MarketRegimeDetector
from ai.strategy_selection.adaptive_manager import AdaptiveStrategyManager
from strategies.ai_adaptive import AIAdaptiveStrategy

# Global configuration
config = get_config()
logger = logging.getLogger(__name__)

class OdinAIManager:
    """
    Manager for AI components initialization and coordination
    Handles regime detection and adaptive strategy management
    """
    
    def __init__(self):
        self.regime_detector = None
        self.strategy_manager = None
        self.ai_strategy = None
        self.data_collector = None
        self.initialized = False
        self.update_task = None
        
    async def initialize(self, data_collector: DataCollector):
        """Initialize AI components with dependencies"""
        try:
            logger.info("🤖 Initializing Odin AI components...")
            
            self.data_collector = data_collector
            
            # Initialize regime detector
            self.regime_detector = MarketRegimeDetector(config.ai.regime_model_path)
            logger.info("✓ Regime detector initialized")
            
            # Initialize adaptive strategy manager
            self.strategy_manager = AdaptiveStrategyManager(config.ai.strategy_config_path)
            logger.info("✓ Adaptive strategy manager initialized")
            
            # Initialize AI adaptive strategy
            self.ai_strategy = AIAdaptiveStrategy(
                regime_update_frequency=config.ai.regime_update_frequency,
                min_regime_confidence=config.ai.min_regime_confidence,
                strategy_rebalance_frequency=config.ai.strategy_rebalance_frequency
            )
            logger.info("✓ AI adaptive strategy initialized")
            
            # Try to load existing models
            models_loaded = self.regime_detector.load_models()
            if models_loaded:
                logger.info("✓ Loaded existing AI models")
                # Test model with recent data
                await self._test_models()
            else:
                logger.info("⚠️  No existing models found - will train on first data batch")
                # Try to train models with available data
                await self._initial_training()
            
            # Set up background AI update loop
            if config.ai.adaptive_strategy_enabled:
                self.update_task = asyncio.create_task(self._ai_update_loop())
                logger.info("✓ AI update loop started")
            
            self.initialized = True
            logger.info("🚀 Odin AI initialization complete")
            
        except Exception as e:
            logger.error(f"❌ AI initialization failed: {e}")
            self.initialized = False
            raise
    
    async def _initial_training(self):
        """Attempt initial model training with available data"""
        try:
            logger.info("🎯 Attempting initial AI model training...")
            
            # Get historical data for training
            historical_data = await self.data_collector.get_historical_data(
                start_date=None,  # Get all available data
                end_date=None
            )
            
            if historical_data.empty or len(historical_data) < config.ai.min_training_samples:
                logger.warning(f"⚠️  Insufficient data for training: {len(historical_data)} samples")
                logger.info("💡 Models will be trained when sufficient data is collected")
                return False
            
            # Prepare features
            features = self.regime_detector.prepare_features(historical_data)
            
            if features.empty or len(features) < config.ai.min_training_samples:
                logger.warning("⚠️  Feature preparation failed or insufficient features")
                return False
            
            # Train models
            training_success = self.regime_detector.train_models(features)
            
            if training_success:
                logger.info(f"✅ Initial model training successful with {len(features)} samples")
                return True
            else:
                logger.error("❌ Initial model training failed")
                return False
                
        except Exception as e:
            logger.error(f"❌ Initial training error: {e}")
            return False
    
    async def _test_models(self):
        """Test loaded models with recent data"""
        try:
            # Get recent data
            recent_data = await self.data_collector.get_recent_data(hours=24)
            
            if not recent_data.empty:
                regime, confidence = self.regime_detector.detect_regime(recent_data)
                logger.info(f"✓ Model test successful: {regime} (confidence: {confidence:.3f})")
                
                # Update strategy manager with detected regime
                if confidence >= config.ai.min_regime_confidence:
                    self.strategy_manager.update_regime(regime, confidence)
                    logger.info(f"✓ Strategy manager updated for {regime}")
                
        except Exception as e:
            logger.warning(f"⚠️  Model testing failed: {e}")
    
    async def _ai_update_loop(self):
        """Background task for periodic AI updates"""
        update_interval = 300  # 5 minutes
        
        logger.info(f"🔄 Starting AI update loop (interval: {update_interval}s)")
        
        while True:
            try:
                await asyncio.sleep(update_interval)
                
                if self.initialized and self.data_collector:
                    await self._perform_ai_update()
                
            except asyncio.CancelledError:
                logger.info("🛑 AI update loop cancelled")
                break
            except Exception as e:
                logger.error(f"❌ AI update loop error: {e}")
                await asyncio.sleep(60)  # Wait before retrying
    
    async def _perform_ai_update(self):
        """Perform a single AI update cycle"""
        try:
            # Get recent data
            recent_data = await self.data_collector.get_recent_data(hours=24)
            
            if recent_data.empty:
                logger.debug("⚠️  No recent data for AI update")
                return
            
            # Update regime detection
            regime, confidence = self.regime_detector.detect_regime(recent_data)
            
            # Update strategy manager if confidence is sufficient
            if confidence >= config.ai.min_regime_confidence:
                regime_changed = self.strategy_manager.update_regime(regime, confidence)
                
                if regime_changed:
                    logger.info(f"📊 Regime change detected: {regime} (confidence: {confidence:.3f})")
                else:
                    logger.debug(f"📊 Regime confirmed: {regime} (confidence: {confidence:.3f})")
            else:
                logger.debug(f"⚠️  Low regime confidence: {confidence:.3f}")
            
            # Check if models need retraining based on performance
            await self._check_retraining_needed()
            
        except Exception as e:
            logger.error(f"❌ AI update cycle failed: {e}")
    
    async def _check_retraining_needed(self):
        """Check if AI models need retraining based on performance"""
        try:
            # Get recent performance metrics
            recent_performance = {
                'accuracy': 0.8,  # Would be calculated from actual performance
                'avg_confidence': self.strategy_manager.current_confidence
            }
            
            # Check if retraining is needed
            needs_retraining = self.regime_detector.retrain_if_needed(recent_performance)
            
            if needs_retraining:
                logger.info("🔄 AI models need retraining due to performance degradation")
                # Could trigger automatic retraining here
                
        except Exception as e:
            logger.error(f"❌ Retraining check failed: {e}")
    
    async def shutdown(self):
        """Shutdown AI components gracefully"""
        try:
            logger.info("🛑 Shutting down AI components...")
            
            if self.update_task:
                self.update_task.cancel()
                try:
                    await self.update_task
                except asyncio.CancelledError:
                    pass
            
            # Save any pending data or models here
            logger.info("✓ AI components shutdown complete")
            
        except Exception as e:
            logger.error(f"❌ AI shutdown error: {e}")

# Global instances
ai_manager = OdinAIManager()
data_collector = None
trading_engine = None
portfolio_manager = None
risk_manager = None

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan manager with AI initialization"""
    global data_collector, trading_engine, portfolio_manager, risk_manager
    
    # Startup
    logger.info("🚀 Starting Odin Trading Bot with AI features...")
    
    try:
        # Initialize database
        logger.info("📊 Initializing database...")
        database = Database(config.DATABASE_URL)
        await database.initialize()
        logger.info("✓ Database initialized")
        
        # Initialize core components
        logger.info("⚙️  Initializing core components...")
        
        # Data collector
        data_collector = DataCollector()
        await data_collector.start()
        logger.info("✓ Data collector started")
        
        # Risk manager
        risk_manager = RiskManager(
            max_position_size=config.MAX_POSITION_SIZE,
            risk_per_trade=config.RISK_PER_TRADE
        )
        logger.info("✓ Risk manager initialized")
        
        # Portfolio manager
        portfolio_manager = PortfolioManager(risk_manager=risk_manager)
        logger.info("✓ Portfolio manager initialized")
        
        # Trading engine
        trading_engine = TradingEngine(
            portfolio_manager=portfolio_manager,
            risk_manager=risk_manager,
            live_trading_enabled=config.ENABLE_LIVE_TRADING
        )
        logger.info("✓ Trading engine initialized")
        
        # Initialize AI components
        await ai_manager.initialize(data_collector)
        
        # Store instances in app state for access by routes
        app.state.data_collector = data_collector
        app.state.trading_engine = trading_engine
        app.state.portfolio_manager = portfolio_manager
        app.state.risk_manager = risk_manager
        app.state.ai_manager = ai_manager
        
        logger.info("🎉 Odin startup complete - Ready for trading!")
        
        yield
        
    except Exception as e:
        logger.error(f"❌ Startup failed: {e}")
        raise
    
    # Shutdown
    logger.info("🛑 Shutting down Odin...")
    
    try:
        # Shutdown AI components first
        await ai_manager.shutdown()
        
        # Shutdown core components
        if trading_engine:
            await trading_engine.stop()
            logger.info("✓ Trading engine stopped")
        
        if data_collector:
            await data_collector.stop()
            logger.info("✓ Data collector stopped")
        
        if database:
            await database.close()
            logger.info("✓ Database closed")
        
        logger.info("✅ Odin shutdown complete")
        
    except Exception as e:
        logger.error(f"❌ Shutdown error: {e}")

def setup_logging():
    """Setup comprehensive logging configuration"""
    
    # Create logs directory
    os.makedirs("data/logs", exist_ok=True)
    
    # Configure logging
    logging_config = {
        'version': 1,
        'disable_existing_loggers': False,
        'formatters': {
            'detailed': {
                'format': '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
            },
            'simple': {
                'format': '%(levelname)s - %(message)s'
            }
        },
        'handlers': {
            'file': {
                'level': 'INFO',
                'class': 'logging.handlers.RotatingFileHandler',
                'filename': 'data/logs/odin.log',
                'maxBytes': 10485760,  # 10MB
                'backupCount': 5,
                'formatter': 'detailed'
            },
            'console': {
                'level': 'INFO',
                'class': 'logging.StreamHandler',
                'formatter': 'simple'
            },
            'trading': {
                'level': 'INFO',
                'class': 'logging.handlers.RotatingFileHandler',
                'filename': 'data/logs/trading.log',
                'maxBytes': 10485760,
                'backupCount': 3,
                'formatter': 'detailed'
            },
            'ai': {
                'level': 'INFO',
                'class': 'logging.handlers.RotatingFileHandler',
                'filename': 'data/logs/ai.log',
                'maxBytes': 10485760,
                'backupCount': 3,
                'formatter': 'detailed'
            }
        },
        'loggers': {
            '': {  # Root logger
                'handlers': ['file', 'console'],
                'level': 'INFO',
                'propagate': False
            },
            'odin.core.trading_engine': {
                'handlers': ['trading'],
                'level': 'INFO',
                'propagate': True
            },
            'odin.ai': {
                'handlers': ['ai'],
                'level': 'INFO',
                'propagate': True
            }
        }
    }
    
    import logging.config
    logging.config.dictConfig(logging_config)

def create_enhanced_app() -> FastAPI:
    """Create FastAPI application with AI enhancements"""
    
    app = create_app(lifespan=lifespan)
    
    # Mount static files for web interface
    if os.path.exists("web/static"):
        app.mount("/static", StaticFiles(directory="web/static"), name="static")
    
    # Add dashboard route
    @app.get("/dashboard", response_class=HTMLResponse)
    async def dashboard():
        """Serve the trading dashboard"""
        dashboard_path = "web/templates/dashboard.html"
        if os.path.exists(dashboard_path):
            with open(dashboard_path, 'r') as f:
                return HTMLResponse(content=f.read())
        else:
            return HTMLResponse(content="<h1>Dashboard not found</h1><p>Please ensure web/templates/dashboard.html exists</p>")
    
    # Enhanced root endpoint with AI status
    @app.get("/")
    async def root():
        ai_status = "active" if ai_manager.initialized else "initializing"
        
        return {
            "message": "Odin Bitcoin Trading Bot with AI",
            "version": "2.0.0",
            "ai_status": ai_status,
            "features": [
                "Real-time Bitcoin trading",
                "Advanced technical analysis", 
                "AI-powered regime detection",
                "Adaptive strategy selection",
                "Risk management",
                "Portfolio optimization",
                "Live trading execution"
            ],
            "endpoints": {
                "documentation": "/docs",
                "dashboard": "/dashboard",
                "health": "/api/v1/health",
                "ai_health": "/api/v1/ai/health",
                "current_regime": "/api/v1/ai/regime/current"
            }
        }
    
    return app

async def main():
    """Main application entry point"""
    
    # Setup logging first
    setup_logging()
    logger = logging.getLogger(__name__)
    
    logger.info("🚀 Starting Odin Bitcoin Trading Bot v2.0.0")
    logger.info(f"📁 Working directory: {os.getcwd()}")
    logger.info(f"🐍 Python version: {sys.version}")
    
    try:
        # Create application
        app = create_enhanced_app()
        
        # Configure uvicorn
        uvicorn_config = uvicorn.Config(
            app,
            host=config.API_HOST,
            port=config.API_PORT,
            log_level="info" if config.API_DEBUG else "warning",
            access_log=True,
            reload=config.API_DEBUG
        )
        
        # Start server
        server = uvicorn.Server(uvicorn_config)
        
        logger.info(f"🌐 Server starting on http://{config.API_HOST}:{config.API_PORT}")
        logger.info(f"📊 Dashboard available at http://{config.API_HOST}:{config.API_PORT}/dashboard")
        logger.info(f"📚 API docs at http://{config.API_HOST}:{config.API_PORT}/docs")
        
        await server.serve()
        
    except KeyboardInterrupt:
        logger.info("👋 Received shutdown signal")
    except Exception as e:
        logger.error(f"❌ Application failed to start: {e}")
        raise
    finally:
        logger.info("🛑 Application shutdown")

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n👋 Goodbye!")
    except Exception as e:
        print(f"❌ Fatal error: {e}")
        sys.exit(1)