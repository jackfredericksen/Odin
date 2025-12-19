"""
Trading Journal API Routes
Handles trade logging, performance tracking, and X (Twitter) integration
"""

import logging
from typing import Dict, List, Any, Optional
from datetime import datetime, timedelta
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field
import json
import os
from pathlib import Path

logger = logging.getLogger(__name__)
router = APIRouter()

# Data storage path
DATA_DIR = Path(__file__).parent.parent.parent.parent / "data" / "journal"
DATA_DIR.mkdir(parents=True, exist_ok=True)
TRADES_FILE = DATA_DIR / "trades.json"
NOTES_FILE = DATA_DIR / "notes.json"

# ============================================================================
# Data Models
# ============================================================================

class Trade(BaseModel):
    """Trade entry model"""
    id: Optional[str] = None
    symbol: str = Field(..., description="Trading symbol (e.g., BTC, ETH)")
    side: str = Field(..., description="Trade side: long or short")
    entry_price: float = Field(..., description="Entry price")
    exit_price: Optional[float] = Field(None, description="Exit price")
    size: float = Field(..., description="Position size")
    pnl: Optional[float] = Field(None, description="Profit/Loss")
    pnl_percent: Optional[float] = Field(None, description="P&L percentage")
    status: str = Field(default="open", description="open or closed")
    entry_time: str = Field(default_factory=lambda: datetime.utcnow().isoformat())
    exit_time: Optional[str] = None
    notes: Optional[str] = None
    tags: List[str] = Field(default_factory=list)
    screenshot_url: Optional[str] = None
    posted_to_x: bool = Field(default=False)

class Note(BaseModel):
    """Journal note model"""
    id: Optional[str] = None
    title: str = Field(..., description="Note title")
    content: str = Field(..., description="Note content")
    date: str = Field(default_factory=lambda: datetime.utcnow().isoformat())
    tags: List[str] = Field(default_factory=list)
    category: str = Field(default="general", description="daily, lesson, strategy, general")

class PostToXRequest(BaseModel):
    """Request model for posting to X/Twitter"""
    trade_id: str = Field(..., description="Trade ID to post")
    message: Optional[str] = Field(None, description="Custom message")
    include_screenshot: bool = Field(default=False)

# ============================================================================
# Helper Functions
# ============================================================================

def load_trades() -> List[Dict[str, Any]]:
    """Load trades from JSON file"""
    if not TRADES_FILE.exists():
        return []

    try:
        with open(TRADES_FILE, 'r') as f:
            return json.load(f)
    except Exception as e:
        logger.error(f"Error loading trades: {e}")
        return []

def save_trades(trades: List[Dict[str, Any]]) -> bool:
    """Save trades to JSON file"""
    try:
        with open(TRADES_FILE, 'w') as f:
            json.dump(trades, f, indent=2)
        return True
    except Exception as e:
        logger.error(f"Error saving trades: {e}")
        return False

def load_notes() -> List[Dict[str, Any]]:
    """Load notes from JSON file"""
    if not NOTES_FILE.exists():
        return []

    try:
        with open(NOTES_FILE, 'r') as f:
            return json.load(f)
    except Exception as e:
        logger.error(f"Error loading notes: {e}")
        return []

def save_notes(notes: List[Dict[str, Any]]) -> bool:
    """Save notes to JSON file"""
    try:
        with open(NOTES_FILE, 'w') as f:
            json.dump(notes, f, indent=2)
        return True
    except Exception as e:
        logger.error(f"Error saving notes: {e}")
        return False

def calculate_pnl(entry_price: float, exit_price: float, size: float, side: str) -> tuple[float, float]:
    """Calculate P&L and P&L percentage"""
    if side.lower() == "long":
        pnl = (exit_price - entry_price) * size
        pnl_percent = ((exit_price - entry_price) / entry_price) * 100
    else:  # short
        pnl = (entry_price - exit_price) * size
        pnl_percent = ((entry_price - exit_price) / entry_price) * 100

    return round(pnl, 2), round(pnl_percent, 2)

def generate_id() -> str:
    """Generate unique ID based on timestamp"""
    return f"{int(datetime.utcnow().timestamp() * 1000)}"

def calculate_performance_stats(trades: List[Dict[str, Any]]) -> Dict[str, Any]:
    """Calculate performance statistics"""
    closed_trades = [t for t in trades if t.get('status') == 'closed']

    if not closed_trades:
        return {
            'total_trades': 0,
            'winning_trades': 0,
            'losing_trades': 0,
            'win_rate': 0,
            'total_pnl': 0,
            'avg_pnl': 0,
            'best_trade': None,
            'worst_trade': None,
            'avg_win': 0,
            'avg_loss': 0
        }

    winning_trades = [t for t in closed_trades if t.get('pnl', 0) > 0]
    losing_trades = [t for t in closed_trades if t.get('pnl', 0) < 0]

    total_pnl = sum(t.get('pnl', 0) for t in closed_trades)
    avg_pnl = total_pnl / len(closed_trades)

    best_trade = max(closed_trades, key=lambda t: t.get('pnl', 0))
    worst_trade = min(closed_trades, key=lambda t: t.get('pnl', 0))

    avg_win = sum(t.get('pnl', 0) for t in winning_trades) / len(winning_trades) if winning_trades else 0
    avg_loss = sum(t.get('pnl', 0) for t in losing_trades) / len(losing_trades) if losing_trades else 0

    return {
        'total_trades': len(closed_trades),
        'winning_trades': len(winning_trades),
        'losing_trades': len(losing_trades),
        'win_rate': round((len(winning_trades) / len(closed_trades)) * 100, 2),
        'total_pnl': round(total_pnl, 2),
        'avg_pnl': round(avg_pnl, 2),
        'best_trade': {
            'symbol': best_trade.get('symbol'),
            'pnl': best_trade.get('pnl'),
            'date': best_trade.get('entry_time')
        },
        'worst_trade': {
            'symbol': worst_trade.get('symbol'),
            'pnl': worst_trade.get('pnl'),
            'date': worst_trade.get('entry_time')
        },
        'avg_win': round(avg_win, 2),
        'avg_loss': round(avg_loss, 2),
        'profit_factor': round(abs(avg_win / avg_loss), 2) if avg_loss != 0 else 0
    }

# ============================================================================
# Trade Routes
# ============================================================================

@router.get("/api/journal/trades")
async def get_trades(
    status: Optional[str] = None,
    symbol: Optional[str] = None,
    limit: int = 100
):
    """
    Get all trades

    Query params:
    - status: Filter by status (open/closed)
    - symbol: Filter by symbol
    - limit: Max number of trades to return
    """
    try:
        trades = load_trades()

        # Apply filters
        if status:
            trades = [t for t in trades if t.get('status') == status]

        if symbol:
            trades = [t for t in trades if t.get('symbol', '').upper() == symbol.upper()]

        # Sort by entry time (newest first)
        trades.sort(key=lambda t: t.get('entry_time', ''), reverse=True)

        # Limit results
        trades = trades[:limit]

        return {
            'success': True,
            'data': trades,
            'count': len(trades)
        }
    except Exception as e:
        logger.error(f"Error getting trades: {e}")
        return {
            'success': False,
            'error': str(e)
        }

@router.post("/api/journal/trades")
async def create_trade(trade: Trade):
    """Create new trade"""
    try:
        trades = load_trades()

        # Generate ID
        trade.id = generate_id()

        # Add to list
        trade_dict = trade.dict()
        trades.append(trade_dict)

        # Save
        if save_trades(trades):
            return {
                'success': True,
                'data': trade_dict,
                'message': 'Trade created successfully'
            }
        else:
            raise HTTPException(status_code=500, detail="Failed to save trade")

    except Exception as e:
        logger.error(f"Error creating trade: {e}")
        return {
            'success': False,
            'error': str(e)
        }

@router.put("/api/journal/trades/{trade_id}")
async def update_trade(trade_id: str, trade: Trade):
    """Update existing trade"""
    try:
        trades = load_trades()

        # Find trade
        trade_index = None
        for i, t in enumerate(trades):
            if t.get('id') == trade_id:
                trade_index = i
                break

        if trade_index is None:
            raise HTTPException(status_code=404, detail="Trade not found")

        # Update trade
        trade_dict = trade.dict()
        trade_dict['id'] = trade_id  # Preserve ID

        # Calculate P&L if closing trade
        if trade.exit_price and trade.status == 'closed':
            pnl, pnl_percent = calculate_pnl(
                trade.entry_price,
                trade.exit_price,
                trade.size,
                trade.side
            )
            trade_dict['pnl'] = pnl
            trade_dict['pnl_percent'] = pnl_percent
            trade_dict['exit_time'] = datetime.utcnow().isoformat()

        trades[trade_index] = trade_dict

        # Save
        if save_trades(trades):
            return {
                'success': True,
                'data': trade_dict,
                'message': 'Trade updated successfully'
            }
        else:
            raise HTTPException(status_code=500, detail="Failed to update trade")

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating trade: {e}")
        return {
            'success': False,
            'error': str(e)
        }

@router.delete("/api/journal/trades/{trade_id}")
async def delete_trade(trade_id: str):
    """Delete trade"""
    try:
        trades = load_trades()

        # Filter out the trade
        new_trades = [t for t in trades if t.get('id') != trade_id]

        if len(new_trades) == len(trades):
            raise HTTPException(status_code=404, detail="Trade not found")

        # Save
        if save_trades(new_trades):
            return {
                'success': True,
                'message': 'Trade deleted successfully'
            }
        else:
            raise HTTPException(status_code=500, detail="Failed to delete trade")

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting trade: {e}")
        return {
            'success': False,
            'error': str(e)
        }

# ============================================================================
# Performance Routes
# ============================================================================

@router.get("/api/journal/performance")
async def get_performance(
    timeframe: str = "all"  # all, 30d, 7d, 1d
):
    """
    Get performance statistics

    Query params:
    - timeframe: all, 30d, 7d, 1d
    """
    try:
        trades = load_trades()

        # Filter by timeframe
        if timeframe != "all":
            cutoff_days = {
                "30d": 30,
                "7d": 7,
                "1d": 1
            }.get(timeframe, 0)

            if cutoff_days > 0:
                cutoff_date = datetime.utcnow() - timedelta(days=cutoff_days)
                trades = [
                    t for t in trades
                    if datetime.fromisoformat(t.get('entry_time', '')) >= cutoff_date
                ]

        # Calculate stats
        stats = calculate_performance_stats(trades)

        return {
            'success': True,
            'data': stats,
            'timeframe': timeframe
        }

    except Exception as e:
        logger.error(f"Error calculating performance: {e}")
        return {
            'success': False,
            'error': str(e)
        }

# ============================================================================
# Notes Routes
# ============================================================================

@router.get("/api/journal/notes")
async def get_notes(
    category: Optional[str] = None,
    limit: int = 50
):
    """
    Get journal notes

    Query params:
    - category: Filter by category
    - limit: Max number of notes
    """
    try:
        notes = load_notes()

        # Filter by category
        if category:
            notes = [n for n in notes if n.get('category') == category]

        # Sort by date (newest first)
        notes.sort(key=lambda n: n.get('date', ''), reverse=True)

        # Limit
        notes = notes[:limit]

        return {
            'success': True,
            'data': notes,
            'count': len(notes)
        }

    except Exception as e:
        logger.error(f"Error getting notes: {e}")
        return {
            'success': False,
            'error': str(e)
        }

@router.post("/api/journal/notes")
async def create_note(note: Note):
    """Create new note"""
    try:
        notes = load_notes()

        # Generate ID
        note.id = generate_id()

        # Add to list
        note_dict = note.dict()
        notes.append(note_dict)

        # Save
        if save_notes(notes):
            return {
                'success': True,
                'data': note_dict,
                'message': 'Note created successfully'
            }
        else:
            raise HTTPException(status_code=500, detail="Failed to save note")

    except Exception as e:
        logger.error(f"Error creating note: {e}")
        return {
            'success': False,
            'error': str(e)
        }

@router.put("/api/journal/notes/{note_id}")
async def update_note(note_id: str, note: Note):
    """Update existing note"""
    try:
        notes = load_notes()

        # Find note
        note_index = None
        for i, n in enumerate(notes):
            if n.get('id') == note_id:
                note_index = i
                break

        if note_index is None:
            raise HTTPException(status_code=404, detail="Note not found")

        # Update note
        note_dict = note.dict()
        note_dict['id'] = note_id  # Preserve ID
        notes[note_index] = note_dict

        # Save
        if save_notes(notes):
            return {
                'success': True,
                'data': note_dict,
                'message': 'Note updated successfully'
            }
        else:
            raise HTTPException(status_code=500, detail="Failed to update note")

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating note: {e}")
        return {
            'success': False,
            'error': str(e)
        }

@router.delete("/api/journal/notes/{note_id}")
async def delete_note(note_id: str):
    """Delete note"""
    try:
        notes = load_notes()

        # Filter out the note
        new_notes = [n for n in notes if n.get('id') != note_id]

        if len(new_notes) == len(notes):
            raise HTTPException(status_code=404, detail="Note not found")

        # Save
        if save_notes(new_notes):
            return {
                'success': True,
                'message': 'Note deleted successfully'
            }
        else:
            raise HTTPException(status_code=500, detail="Failed to delete note")

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting note: {e}")
        return {
            'success': False,
            'error': str(e)
        }

# ============================================================================
# X/Twitter Integration Routes
# ============================================================================

@router.post("/api/journal/post-to-x")
async def post_to_x(request: PostToXRequest):
    """
    Post trade to X/Twitter

    NOTE: This is a placeholder implementation
    Real implementation requires Twitter API v2 credentials
    """
    try:
        trades = load_trades()

        # Find trade
        trade = None
        for t in trades:
            if t.get('id') == request.trade_id:
                trade = t
                break

        if not trade:
            raise HTTPException(status_code=404, detail="Trade not found")

        # Generate tweet message
        if request.message:
            message = request.message
        else:
            # Auto-generate message
            pnl_emoji = "🟢" if trade.get('pnl', 0) > 0 else "🔴"
            side_emoji = "📈" if trade.get('side') == 'long' else "📉"

            message = f"""{pnl_emoji} {side_emoji} {trade.get('symbol')} {trade.get('side').upper()}

Entry: ${trade.get('entry_price')}
Exit: ${trade.get('exit_price')}
P&L: ${trade.get('pnl')} ({trade.get('pnl_percent')}%)

#crypto #trading #{trade.get('symbol')}"""

        # NOTE: Actual Twitter API integration would go here
        # For now, just mark as posted
        for t in trades:
            if t.get('id') == request.trade_id:
                t['posted_to_x'] = True
                break

        save_trades(trades)

        return {
            'success': True,
            'message': 'Trade marked as posted (Twitter API integration pending)',
            'preview': message,
            'note': 'Twitter API v2 credentials required for actual posting'
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error posting to X: {e}")
        return {
            'success': False,
            'error': str(e)
        }

# ============================================================================
# End of file
# ============================================================================
