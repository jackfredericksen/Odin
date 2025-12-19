/**
 * Trading Journal Module
 * Handles trade logging, performance tracking, and X (Twitter) integration
 */

class TradingJournal {
    constructor() {
        this.apiBase = '/api';
        this.data = {
            trades: [],
            performance: null,
            notes: []
        };
        this.currentView = 'trades'; // trades, performance, notes
        this.editingTradeId = null;
    }

    /**
     * Initialize trading journal module
     */
    async init() {
        console.log('📝 Initializing Trading Journal...');

        // Render UI structure
        this.renderUI();

        // Load all data
        await this.loadAllData();

        console.log('✅ Trading Journal initialized');
    }

    /**
     * Render the Trading Journal UI
     */
    renderUI() {
        const container = document.getElementById('section-journal');
        if (!container) return;

        const content = container.querySelector('.section-content');
        if (!content) return;

        content.innerHTML = `
            <!-- View Tabs -->
            <div style="display: flex; gap: var(--spacing-sm); margin-bottom: var(--spacing-lg); border-bottom: 1px solid var(--border-primary);">
                <button class="journal-tab active" data-view="trades" onclick="window.tradingJournal.switchView('trades')">
                    Trades
                </button>
                <button class="journal-tab" data-view="performance" onclick="window.tradingJournal.switchView('performance')">
                    Performance
                </button>
                <button class="journal-tab" data-view="notes" onclick="window.tradingJournal.switchView('notes')">
                    Notes
                </button>
            </div>

            <!-- Trades View -->
            <div id="view-trades" class="journal-view active">
                <!-- Trade Entry Form -->
                <div class="terminal-panel" style="margin-bottom: var(--spacing-lg);">
                    <div class="terminal-panel-header">
                        <span class="terminal-panel-title" id="trade-form-title">New Trade Entry</span>
                        <button class="panel-toggle" onclick="window.tradingJournal.clearForm()">Clear</button>
                    </div>
                    <div class="terminal-panel-body">
                        <form id="trade-form" style="display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap: var(--spacing-md);">
                            <div>
                                <label style="font-size: 0.75rem; color: var(--text-secondary); display: block; margin-bottom: 0.25rem;">Symbol</label>
                                <select id="trade-symbol" style="width: 100%; padding: 0.5rem; background: var(--bg-card); border: 1px solid var(--border-primary); color: var(--text-primary); border-radius: 4px;">
                                    <option value="BTC">BTC</option>
                                    <option value="ETH">ETH</option>
                                    <option value="SOL">SOL</option>
                                    <option value="XRP">XRP</option>
                                    <option value="BNB">BNB</option>
                                    <option value="SUI">SUI</option>
                                    <option value="HYPE">HYPE</option>
                                </select>
                            </div>

                            <div>
                                <label style="font-size: 0.75rem; color: var(--text-secondary); display: block; margin-bottom: 0.25rem;">Side</label>
                                <select id="trade-side" style="width: 100%; padding: 0.5rem; background: var(--bg-card); border: 1px solid var(--border-primary); color: var(--text-primary); border-radius: 4px;">
                                    <option value="long">Long</option>
                                    <option value="short">Short</option>
                                </select>
                            </div>

                            <div>
                                <label style="font-size: 0.75rem; color: var(--text-secondary); display: block; margin-bottom: 0.25rem;">Entry Price</label>
                                <input type="number" id="trade-entry-price" step="0.01" placeholder="0.00" style="width: 100%; padding: 0.5rem; background: var(--bg-card); border: 1px solid var(--border-primary); color: var(--text-primary); border-radius: 4px;">
                            </div>

                            <div>
                                <label style="font-size: 0.75rem; color: var(--text-secondary); display: block; margin-bottom: 0.25rem;">Exit Price (optional)</label>
                                <input type="number" id="trade-exit-price" step="0.01" placeholder="0.00" style="width: 100%; padding: 0.5rem; background: var(--bg-card); border: 1px solid var(--border-primary); color: var(--text-primary); border-radius: 4px;">
                            </div>

                            <div>
                                <label style="font-size: 0.75rem; color: var(--text-secondary); display: block; margin-bottom: 0.25rem;">Position Size</label>
                                <input type="number" id="trade-size" step="0.001" placeholder="0.0" style="width: 100%; padding: 0.5rem; background: var(--bg-card); border: 1px solid var(--border-primary); color: var(--text-primary); border-radius: 4px;">
                            </div>

                            <div>
                                <label style="font-size: 0.75rem; color: var(--text-secondary); display: block; margin-bottom: 0.25rem;">Status</label>
                                <select id="trade-status" style="width: 100%; padding: 0.5rem; background: var(--bg-card); border: 1px solid var(--border-primary); color: var(--text-primary); border-radius: 4px;">
                                    <option value="open">Open</option>
                                    <option value="closed">Closed</option>
                                </select>
                            </div>

                            <div style="grid-column: 1 / -1;">
                                <label style="font-size: 0.75rem; color: var(--text-secondary); display: block; margin-bottom: 0.25rem;">Notes</label>
                                <textarea id="trade-notes" rows="3" placeholder="Trade notes..." style="width: 100%; padding: 0.5rem; background: var(--bg-card); border: 1px solid var(--border-primary); color: var(--text-primary); border-radius: 4px; resize: vertical;"></textarea>
                            </div>

                            <div style="grid-column: 1 / -1; display: flex; gap: var(--spacing-sm);">
                                <button type="submit" style="flex: 1; padding: 0.75rem; background: var(--accent-primary); color: white; border: none; border-radius: 4px; cursor: pointer; font-weight: 600;">
                                    <span id="submit-btn-text">Save Trade</span>
                                </button>
                                <button type="button" onclick="window.tradingJournal.clearForm()" style="padding: 0.75rem 1.5rem; background: var(--bg-card); color: var(--text-primary); border: 1px solid var(--border-primary); border-radius: 4px; cursor: pointer;">
                                    Cancel
                                </button>
                            </div>
                        </form>
                    </div>
                </div>

                <!-- Trades List -->
                <div class="terminal-panel">
                    <div class="terminal-panel-header">
                        <span class="terminal-panel-title">Recent Trades</span>
                        <div style="display: flex; gap: var(--spacing-sm);">
                            <button class="panel-toggle" onclick="window.tradingJournal.loadTrades('open')">Open</button>
                            <button class="panel-toggle" onclick="window.tradingJournal.loadTrades('closed')">Closed</button>
                            <button class="panel-toggle" onclick="window.tradingJournal.loadTrades()">All</button>
                        </div>
                    </div>
                    <div class="terminal-panel-body">
                        <div id="trades-list" style="max-height: 600px; overflow-y: auto;">
                            <div style="text-align: center; color: var(--text-secondary); padding: 2rem;">Loading trades...</div>
                        </div>
                    </div>
                </div>
            </div>

            <!-- Performance View -->
            <div id="view-performance" class="journal-view" style="display: none;">
                <div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(300px, 1fr)); gap: var(--spacing-md); margin-bottom: var(--spacing-lg);">
                    <!-- Timeframe Selector -->
                    <div style="grid-column: 1 / -1;">
                        <div style="display: flex; gap: var(--spacing-sm); justify-content: center;">
                            <button class="panel-toggle" onclick="window.tradingJournal.loadPerformance('1d')">1 Day</button>
                            <button class="panel-toggle" onclick="window.tradingJournal.loadPerformance('7d')">7 Days</button>
                            <button class="panel-toggle" onclick="window.tradingJournal.loadPerformance('30d')">30 Days</button>
                            <button class="panel-toggle active" onclick="window.tradingJournal.loadPerformance('all')">All Time</button>
                        </div>
                    </div>

                    <!-- Performance Stats -->
                    <div class="terminal-panel">
                        <div class="terminal-panel-header">
                            <span class="terminal-panel-title">Overview</span>
                        </div>
                        <div class="terminal-panel-body">
                            <div class="quick-stat">
                                <div class="quick-stat-label">Total Trades</div>
                                <div class="quick-stat-value" id="perf-total-trades">0</div>
                            </div>
                            <div class="quick-stat">
                                <div class="quick-stat-label">Win Rate</div>
                                <div class="quick-stat-value" id="perf-win-rate">0%</div>
                            </div>
                            <div class="quick-stat">
                                <div class="quick-stat-label">Total P&L</div>
                                <div class="quick-stat-value" id="perf-total-pnl">$0.00</div>
                            </div>
                        </div>
                    </div>

                    <div class="terminal-panel">
                        <div class="terminal-panel-header">
                            <span class="terminal-panel-title">Trade Breakdown</span>
                        </div>
                        <div class="terminal-panel-body">
                            <div class="quick-stat">
                                <div class="quick-stat-label">Winning Trades</div>
                                <div class="quick-stat-value" style="color: var(--accent-success);" id="perf-winning-trades">0</div>
                            </div>
                            <div class="quick-stat">
                                <div class="quick-stat-label">Losing Trades</div>
                                <div class="quick-stat-value" style="color: var(--accent-danger);" id="perf-losing-trades">0</div>
                            </div>
                            <div class="quick-stat">
                                <div class="quick-stat-label">Profit Factor</div>
                                <div class="quick-stat-value" id="perf-profit-factor">0.00</div>
                            </div>
                        </div>
                    </div>

                    <div class="terminal-panel">
                        <div class="terminal-panel-header">
                            <span class="terminal-panel-title">Best & Worst</span>
                        </div>
                        <div class="terminal-panel-body">
                            <div class="quick-stat">
                                <div class="quick-stat-label">Best Trade</div>
                                <div class="quick-stat-value" style="color: var(--accent-success);" id="perf-best-trade">--</div>
                            </div>
                            <div class="quick-stat">
                                <div class="quick-stat-label">Worst Trade</div>
                                <div class="quick-stat-value" style="color: var(--accent-danger);" id="perf-worst-trade">--</div>
                            </div>
                            <div class="quick-stat">
                                <div class="quick-stat-label">Avg P&L</div>
                                <div class="quick-stat-value" id="perf-avg-pnl">$0.00</div>
                            </div>
                        </div>
                    </div>
                </div>
            </div>

            <!-- Notes View -->
            <div id="view-notes" class="journal-view" style="display: none;">
                <div class="terminal-panel" style="margin-bottom: var(--spacing-lg);">
                    <div class="terminal-panel-header">
                        <span class="terminal-panel-title">New Note</span>
                    </div>
                    <div class="terminal-panel-body">
                        <form id="note-form">
                            <div style="margin-bottom: var(--spacing-md);">
                                <label style="font-size: 0.75rem; color: var(--text-secondary); display: block; margin-bottom: 0.25rem;">Title</label>
                                <input type="text" id="note-title" placeholder="Note title..." style="width: 100%; padding: 0.5rem; background: var(--bg-card); border: 1px solid var(--border-primary); color: var(--text-primary); border-radius: 4px;">
                            </div>
                            <div style="margin-bottom: var(--spacing-md);">
                                <label style="font-size: 0.75rem; color: var(--text-secondary); display: block; margin-bottom: 0.25rem;">Category</label>
                                <select id="note-category" style="width: 100%; padding: 0.5rem; background: var(--bg-card); border: 1px solid var(--border-primary); color: var(--text-primary); border-radius: 4px;">
                                    <option value="general">General</option>
                                    <option value="daily">Daily Journal</option>
                                    <option value="lesson">Lesson Learned</option>
                                    <option value="strategy">Strategy Notes</option>
                                </select>
                            </div>
                            <div style="margin-bottom: var(--spacing-md);">
                                <label style="font-size: 0.75rem; color: var(--text-secondary); display: block; margin-bottom: 0.25rem;">Content</label>
                                <textarea id="note-content" rows="5" placeholder="Write your notes here..." style="width: 100%; padding: 0.5rem; background: var(--bg-card); border: 1px solid var(--border-primary); color: var(--text-primary); border-radius: 4px; resize: vertical;"></textarea>
                            </div>
                            <button type="submit" style="padding: 0.75rem 1.5rem; background: var(--accent-primary); color: white; border: none; border-radius: 4px; cursor: pointer; font-weight: 600;">
                                Save Note
                            </button>
                        </form>
                    </div>
                </div>

                <div class="terminal-panel">
                    <div class="terminal-panel-header">
                        <span class="terminal-panel-title">Notes</span>
                    </div>
                    <div class="terminal-panel-body">
                        <div id="notes-list" style="max-height: 600px; overflow-y: auto;">
                            <div style="text-align: center; color: var(--text-secondary); padding: 2rem;">Loading notes...</div>
                        </div>
                    </div>
                </div>
            </div>
        `;

        // Add tab styles
        const style = document.createElement('style');
        style.textContent = `
            .journal-tab {
                padding: 1rem 2rem;
                background: transparent;
                border: none;
                border-bottom: 2px solid transparent;
                color: var(--text-secondary);
                cursor: pointer;
                font-weight: 600;
                transition: all 0.2s;
            }

            .journal-tab:hover {
                color: var(--text-primary);
            }

            .journal-tab.active {
                color: var(--accent-primary);
                border-bottom-color: var(--accent-primary);
            }

            .journal-view {
                display: none;
            }

            .journal-view.active {
                display: block;
            }
        `;
        document.head.appendChild(style);

        // Attach form handlers
        this.attachFormHandlers();
    }

    /**
     * Attach form submit handlers
     */
    attachFormHandlers() {
        // Trade form
        const tradeForm = document.getElementById('trade-form');
        if (tradeForm) {
            tradeForm.addEventListener('submit', async (e) => {
                e.preventDefault();
                await this.saveTrade();
            });
        }

        // Note form
        const noteForm = document.getElementById('note-form');
        if (noteForm) {
            noteForm.addEventListener('submit', async (e) => {
                e.preventDefault();
                await this.saveNote();
            });
        }
    }

    /**
     * Switch between views
     */
    switchView(view) {
        this.currentView = view;

        // Update tab states
        document.querySelectorAll('.journal-tab').forEach(tab => {
            if (tab.dataset.view === view) {
                tab.classList.add('active');
            } else {
                tab.classList.remove('active');
            }
        });

        // Show/hide views
        document.querySelectorAll('.journal-view').forEach(viewEl => {
            viewEl.style.display = 'none';
        });

        const activeView = document.getElementById(`view-${view}`);
        if (activeView) {
            activeView.style.display = 'block';
        }

        // Load data for the active view
        if (view === 'performance') {
            this.loadPerformance('all');
        } else if (view === 'notes') {
            this.loadNotes();
        }
    }

    /**
     * Load all data
     */
    async loadAllData() {
        await Promise.all([
            this.loadTrades(),
            this.loadPerformance('all')
        ]);
    }

    /**
     * Load trades
     */
    async loadTrades(status = null) {
        try {
            const url = status
                ? `${this.apiBase}/journal/trades?status=${status}`
                : `${this.apiBase}/journal/trades`;

            const response = await fetch(url);
            const result = await response.json();

            if (result.success) {
                this.data.trades = result.data;
                this.renderTrades(result.data);
            }
        } catch (error) {
            console.error('Error loading trades:', error);
        }
    }

    /**
     * Render trades list
     */
    renderTrades(trades) {
        const container = document.getElementById('trades-list');
        if (!container) return;

        if (!trades || trades.length === 0) {
            container.innerHTML = '<div style="text-align: center; color: var(--text-secondary); padding: 2rem;">No trades found</div>';
            return;
        }

        container.innerHTML = trades.map(trade => {
            const pnlClass = trade.pnl > 0 ? 'success' : trade.pnl < 0 ? 'danger' : 'info';
            const pnlEmoji = trade.pnl > 0 ? '🟢' : trade.pnl < 0 ? '🔴' : '🟡';
            const sideEmoji = trade.side === 'long' ? '📈' : '📉';

            return `
                <div style="padding: 1rem; border-bottom: 1px solid var(--border-subtle); display: flex; justify-content: space-between; align-items: start;">
                    <div style="flex: 1;">
                        <div style="display: flex; align-items: center; gap: 0.5rem; margin-bottom: 0.5rem;">
                            <span style="font-size: 1.25rem;">${pnlEmoji} ${sideEmoji}</span>
                            <span style="font-weight: 600; font-size: 1rem;">${trade.symbol} ${trade.side.toUpperCase()}</span>
                            <span class="terminal-badge ${pnlClass}">${trade.status.toUpperCase()}</span>
                        </div>
                        <div style="font-size: 0.875rem; color: var(--text-secondary); font-family: var(--font-mono);">
                            Entry: $${trade.entry_price} ${trade.exit_price ? `→ Exit: $${trade.exit_price}` : ''}
                        </div>
                        ${trade.pnl !== null && trade.pnl !== undefined ? `
                            <div style="font-size: 0.875rem; margin-top: 0.25rem;">
                                P&L: <span style="color: var(--accent-${pnlClass}); font-weight: 600;">$${trade.pnl} (${trade.pnl_percent}%)</span>
                            </div>
                        ` : ''}
                        ${trade.notes ? `
                            <div style="font-size: 0.75rem; color: var(--text-tertiary); margin-top: 0.5rem;">
                                ${trade.notes}
                            </div>
                        ` : ''}
                    </div>
                    <div style="display: flex; gap: 0.5rem;">
                        <button class="panel-toggle" onclick="window.tradingJournal.editTrade('${trade.id}')" title="Edit">✏️</button>
                        ${trade.status === 'closed' ? `
                            <button class="panel-toggle" onclick="window.tradingJournal.postToX('${trade.id}')" title="Post to X">🐦</button>
                        ` : ''}
                        <button class="panel-toggle" onclick="window.tradingJournal.deleteTrade('${trade.id}')" title="Delete">🗑️</button>
                    </div>
                </div>
            `;
        }).join('');
    }

    /**
     * Save trade
     */
    async saveTrade() {
        try {
            const trade = {
                symbol: document.getElementById('trade-symbol').value,
                side: document.getElementById('trade-side').value,
                entry_price: parseFloat(document.getElementById('trade-entry-price').value),
                exit_price: document.getElementById('trade-exit-price').value ? parseFloat(document.getElementById('trade-exit-price').value) : null,
                size: parseFloat(document.getElementById('trade-size').value),
                status: document.getElementById('trade-status').value,
                notes: document.getElementById('trade-notes').value
            };

            const url = this.editingTradeId
                ? `${this.apiBase}/journal/trades/${this.editingTradeId}`
                : `${this.apiBase}/journal/trades`;

            const method = this.editingTradeId ? 'PUT' : 'POST';

            const response = await fetch(url, {
                method: method,
                headers: {'Content-Type': 'application/json'},
                body: JSON.stringify(trade)
            });

            const result = await response.json();

            if (result.success) {
                this.clearForm();
                await this.loadTrades();
            } else {
                alert('Error saving trade: ' + result.error);
            }
        } catch (error) {
            console.error('Error saving trade:', error);
            alert('Error saving trade');
        }
    }

    /**
     * Edit trade
     */
    editTrade(tradeId) {
        const trade = this.data.trades.find(t => t.id === tradeId);
        if (!trade) return;

        this.editingTradeId = tradeId;

        document.getElementById('trade-symbol').value = trade.symbol;
        document.getElementById('trade-side').value = trade.side;
        document.getElementById('trade-entry-price').value = trade.entry_price;
        document.getElementById('trade-exit-price').value = trade.exit_price || '';
        document.getElementById('trade-size').value = trade.size;
        document.getElementById('trade-status').value = trade.status;
        document.getElementById('trade-notes').value = trade.notes || '';

        document.getElementById('trade-form-title').textContent = 'Edit Trade';
        document.getElementById('submit-btn-text').textContent = 'Update Trade';

        // Scroll to form
        document.getElementById('trade-form').scrollIntoView({ behavior: 'smooth' });
    }

    /**
     * Delete trade
     */
    async deleteTrade(tradeId) {
        if (!confirm('Are you sure you want to delete this trade?')) return;

        try {
            const response = await fetch(`${this.apiBase}/journal/trades/${tradeId}`, {
                method: 'DELETE'
            });

            const result = await response.json();

            if (result.success) {
                await this.loadTrades();
            } else {
                alert('Error deleting trade: ' + result.error);
            }
        } catch (error) {
            console.error('Error deleting trade:', error);
            alert('Error deleting trade');
        }
    }

    /**
     * Clear form
     */
    clearForm() {
        this.editingTradeId = null;
        document.getElementById('trade-form').reset();
        document.getElementById('trade-form-title').textContent = 'New Trade Entry';
        document.getElementById('submit-btn-text').textContent = 'Save Trade';
    }

    /**
     * Load performance stats
     */
    async loadPerformance(timeframe = 'all') {
        try {
            const response = await fetch(`${this.apiBase}/journal/performance?timeframe=${timeframe}`);
            const result = await response.json();

            if (result.success) {
                this.data.performance = result.data;
                this.renderPerformance(result.data);
            }
        } catch (error) {
            console.error('Error loading performance:', error);
        }
    }

    /**
     * Render performance stats
     */
    renderPerformance(stats) {
        document.getElementById('perf-total-trades').textContent = stats.total_trades;
        document.getElementById('perf-win-rate').textContent = `${stats.win_rate}%`;
        document.getElementById('perf-total-pnl').textContent = `$${stats.total_pnl}`;
        document.getElementById('perf-total-pnl').style.color = stats.total_pnl >= 0 ? 'var(--accent-success)' : 'var(--accent-danger)';

        document.getElementById('perf-winning-trades').textContent = stats.winning_trades;
        document.getElementById('perf-losing-trades').textContent = stats.losing_trades;
        document.getElementById('perf-profit-factor').textContent = stats.profit_factor;

        if (stats.best_trade) {
            document.getElementById('perf-best-trade').textContent = `${stats.best_trade.symbol} $${stats.best_trade.pnl}`;
        }

        if (stats.worst_trade) {
            document.getElementById('perf-worst-trade').textContent = `${stats.worst_trade.symbol} $${stats.worst_trade.pnl}`;
        }

        document.getElementById('perf-avg-pnl').textContent = `$${stats.avg_pnl}`;
        document.getElementById('perf-avg-pnl').style.color = stats.avg_pnl >= 0 ? 'var(--accent-success)' : 'var(--accent-danger)';
    }

    /**
     * Load notes
     */
    async loadNotes() {
        try {
            const response = await fetch(`${this.apiBase}/journal/notes`);
            const result = await response.json();

            if (result.success) {
                this.data.notes = result.data;
                this.renderNotes(result.data);
            }
        } catch (error) {
            console.error('Error loading notes:', error);
        }
    }

    /**
     * Render notes
     */
    renderNotes(notes) {
        const container = document.getElementById('notes-list');
        if (!container) return;

        if (!notes || notes.length === 0) {
            container.innerHTML = '<div style="text-align: center; color: var(--text-secondary); padding: 2rem;">No notes found</div>';
            return;
        }

        container.innerHTML = notes.map(note => `
            <div style="padding: 1rem; border-bottom: 1px solid var(--border-subtle);">
                <div style="display: flex; justify-content: space-between; align-items: start; margin-bottom: 0.5rem;">
                    <div>
                        <div style="font-weight: 600;">${note.title}</div>
                        <div style="font-size: 0.75rem; color: var(--text-secondary);">
                            ${new Date(note.date).toLocaleDateString()} • ${note.category}
                        </div>
                    </div>
                    <button class="panel-toggle" onclick="window.tradingJournal.deleteNote('${note.id}')" title="Delete">🗑️</button>
                </div>
                <div style="font-size: 0.875rem; color: var(--text-tertiary);">
                    ${note.content}
                </div>
            </div>
        `).join('');
    }

    /**
     * Save note
     */
    async saveNote() {
        try {
            const note = {
                title: document.getElementById('note-title').value,
                content: document.getElementById('note-content').value,
                category: document.getElementById('note-category').value
            };

            const response = await fetch(`${this.apiBase}/journal/notes`, {
                method: 'POST',
                headers: {'Content-Type': 'application/json'},
                body: JSON.stringify(note)
            });

            const result = await response.json();

            if (result.success) {
                document.getElementById('note-form').reset();
                await this.loadNotes();
            } else {
                alert('Error saving note: ' + result.error);
            }
        } catch (error) {
            console.error('Error saving note:', error);
            alert('Error saving note');
        }
    }

    /**
     * Delete note
     */
    async deleteNote(noteId) {
        if (!confirm('Are you sure you want to delete this note?')) return;

        try {
            const response = await fetch(`${this.apiBase}/journal/notes/${noteId}`, {
                method: 'DELETE'
            });

            const result = await response.json();

            if (result.success) {
                await this.loadNotes();
            } else {
                alert('Error deleting note: ' + result.error);
            }
        } catch (error) {
            console.error('Error deleting note:', error);
            alert('Error deleting note');
        }
    }

    /**
     * Post trade to X/Twitter
     */
    async postToX(tradeId) {
        try {
            const response = await fetch(`${this.apiBase}/journal/post-to-x`, {
                method: 'POST',
                headers: {'Content-Type': 'application/json'},
                body: JSON.stringify({ trade_id: tradeId })
            });

            const result = await response.json();

            if (result.success) {
                alert(`Trade posted to X!\n\nPreview:\n${result.preview}\n\n${result.note || ''}`);
                await this.loadTrades();
            } else {
                alert('Error posting to X: ' + result.error);
            }
        } catch (error) {
            console.error('Error posting to X:', error);
            alert('Error posting to X');
        }
    }
}

// Auto-initialize on window load
if (typeof window !== 'undefined') {
    window.TradingJournal = TradingJournal;
}
