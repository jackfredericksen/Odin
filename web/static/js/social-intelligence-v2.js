/**
 * Social Intelligence Module v2 - Enhanced
 * Features: Fear & Greed Index, Whale Alerts, Market Movers, Enhanced Feeds
 */

class SocialIntelligence {
    constructor() {
        this.apiBase = '/api';
        this.data = {
            twitter: [],
            reddit: [],
            news: [],
            sentiment: null,
            trending: [],
            fearGreed: null,
            whaleAlerts: [],
            marketMovers: null
        };
        this.updateInterval = 60000; // 60 seconds
        this.intervalId = null;
        this.currentCoin = null;

        // Load settings from localStorage or use defaults
        this.settings = this.loadSettings();
        this.updateInterval = this.settings.refreshInterval * 1000;
    }

    loadSettings() {
        const savedSettings = localStorage.getItem('odin-social-settings');
        if (savedSettings) {
            return JSON.parse(savedSettings);
        }

        return {
            newsSources: ['coindesk', 'decrypt', 'cointelegraph', 'theblock', 'bitcoinmagazine'],
            subreddits: ['cryptocurrency', 'bitcoin', 'ethtrader', 'solana'],
            twitterKeywords: ['bitcoin', 'crypto', 'btc', 'ethereum'],
            autoRefresh: true,
            refreshInterval: 60
        };
    }

    saveSettings() {
        localStorage.setItem('odin-social-settings', JSON.stringify(this.settings));
        console.log('Settings saved:', this.settings);
    }

    async init() {
        console.log('Initializing Social Intelligence v2...');

        // Get current coin from dashboard
        const coinSelector = document.getElementById('coin-selector');
        this.currentCoin = coinSelector ? coinSelector.value : 'BTC';

        // Listen for coin changes
        if (coinSelector) {
            coinSelector.addEventListener('change', (e) => {
                this.currentCoin = e.target.value;
                this.loadAllData();
            });
        }

        this.renderUI();
        await this.loadAllData();

        if (this.settings.autoRefresh) {
            this.startAutoUpdate();
        }

        console.log('Social Intelligence v2 initialized');
    }

    renderUI() {
        const container = document.getElementById('section-social');
        if (!container) return;

        const content = container.querySelector('.section-content');
        if (!content) return;

        content.innerHTML = `
            <!-- Settings Modal -->
            <div id="social-settings-modal" class="modal-overlay" style="display: none;">
                <div class="modal-content">
                    <div class="modal-header">
                        <h2>Social Feed Settings</h2>
                        <button onclick="window.socialIntelligence.closeSettings()" class="modal-close">&times;</button>
                    </div>
                    <div class="modal-body">
                        <!-- News Sources -->
                        <div class="settings-group">
                            <label class="settings-label">News Sources</label>
                            <div class="checkbox-group">
                                <label><input type="checkbox" id="source-coindesk"> CoinDesk</label>
                                <label><input type="checkbox" id="source-decrypt"> Decrypt</label>
                                <label><input type="checkbox" id="source-cointelegraph"> CoinTelegraph</label>
                                <label><input type="checkbox" id="source-theblock"> The Block</label>
                                <label><input type="checkbox" id="source-bitcoinmagazine"> Bitcoin Magazine</label>
                                <label><input type="checkbox" id="source-blockworks"> Blockworks</label>
                            </div>
                        </div>

                        <!-- Subreddits -->
                        <div class="settings-group">
                            <label class="settings-label">Subreddits</label>
                            <input type="text" id="subreddits-input" class="settings-input" placeholder="cryptocurrency, bitcoin, ethtrader">
                            <small>Comma-separated list of subreddit names</small>
                        </div>

                        <!-- Refresh Settings -->
                        <div class="settings-group">
                            <label class="settings-checkbox">
                                <input type="checkbox" id="auto-refresh-toggle">
                                <span>Auto-refresh feeds</span>
                            </label>
                            <div id="refresh-interval-container" style="margin-top: 0.5rem;">
                                <label>Refresh interval (seconds)</label>
                                <input type="number" id="refresh-interval-input" class="settings-input" min="30" max="300" step="10" style="width: 100px;">
                            </div>
                        </div>
                    </div>
                    <div class="modal-footer">
                        <button onclick="window.socialIntelligence.resetSettings()" class="btn btn-secondary">Reset</button>
                        <button onclick="window.socialIntelligence.applySettings()" class="btn btn-primary">Apply</button>
                    </div>
                </div>
            </div>

            <!-- Top Stats Row -->
            <div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(280px, 1fr)); gap: var(--spacing-md); margin-bottom: var(--spacing-lg);">

                <!-- Fear & Greed Index -->
                <div class="terminal-panel">
                    <div class="terminal-panel-header">
                        <span class="terminal-panel-title">Fear & Greed Index</span>
                    </div>
                    <div class="terminal-panel-body" id="fear-greed-container">
                        <div style="text-align: center; padding: 1rem;">
                            <div id="fng-emoji" style="font-size: 3rem; margin-bottom: 0.5rem;">...</div>
                            <div id="fng-value" style="font-size: 2.5rem; font-weight: 700; font-family: var(--font-mono);">--</div>
                            <div id="fng-label" style="font-size: 0.875rem; color: var(--text-secondary); margin-top: 0.25rem;">Loading...</div>
                            <div id="fng-trend" style="font-size: 0.75rem; margin-top: 0.5rem;"></div>
                        </div>
                    </div>
                </div>

                <!-- Sentiment Overview -->
                <div class="terminal-panel">
                    <div class="terminal-panel-header">
                        <span class="terminal-panel-title">Market Sentiment</span>
                        <div style="display: flex; gap: 0.5rem;">
                            <button class="panel-toggle" onclick="window.socialIntelligence.openSettings()" title="Settings">&#9881;</button>
                            <button class="panel-toggle" onclick="window.socialIntelligence.loadAllData()" title="Refresh">&#8635;</button>
                        </div>
                    </div>
                    <div class="terminal-panel-body">
                        <div style="text-align: center; margin-bottom: 1rem;">
                            <div id="sentiment-gauge" style="font-size: 2.5rem;">...</div>
                            <div id="sentiment-score" style="font-size: 2rem; font-weight: 700; font-family: var(--font-mono);">--%</div>
                            <div id="sentiment-label" style="font-size: 0.875rem; color: var(--text-secondary);">Loading...</div>
                        </div>
                        <div style="display: grid; grid-template-columns: repeat(3, 1fr); gap: 0.5rem; font-size: 0.75rem;">
                            <div style="text-align: center;">
                                <div style="color: var(--text-secondary);">Twitter</div>
                                <div id="twitter-sentiment" style="font-family: var(--font-mono); font-weight: 600;">--</div>
                            </div>
                            <div style="text-align: center;">
                                <div style="color: var(--text-secondary);">Reddit</div>
                                <div id="reddit-sentiment" style="font-family: var(--font-mono); font-weight: 600;">--</div>
                            </div>
                            <div style="text-align: center;">
                                <div style="color: var(--text-secondary);">News</div>
                                <div id="news-sentiment" style="font-family: var(--font-mono); font-weight: 600;">--</div>
                            </div>
                        </div>
                    </div>
                </div>

                <!-- Whale Alerts -->
                <div class="terminal-panel">
                    <div class="terminal-panel-header">
                        <span class="terminal-panel-title">Whale Alerts</span>
                    </div>
                    <div class="terminal-panel-body" style="max-height: 200px; overflow-y: auto;" id="whale-alerts-container">
                        <div style="text-align: center; color: var(--text-secondary); padding: 1rem;">Loading whale alerts...</div>
                    </div>
                </div>
            </div>

            <!-- Trending & Market Movers Row -->
            <div style="display: grid; grid-template-columns: 1fr 1fr; gap: var(--spacing-md); margin-bottom: var(--spacing-lg);">

                <!-- Trending Topics -->
                <div class="terminal-panel">
                    <div class="terminal-panel-header">
                        <span class="terminal-panel-title">Trending Topics</span>
                    </div>
                    <div class="terminal-panel-body">
                        <div id="trending-topics" style="display: flex; flex-wrap: wrap; gap: 0.5rem;">
                            <div style="color: var(--text-secondary);">Loading...</div>
                        </div>
                    </div>
                </div>

                <!-- Market Movers -->
                <div class="terminal-panel">
                    <div class="terminal-panel-header">
                        <span class="terminal-panel-title">Market Movers (24h)</span>
                    </div>
                    <div class="terminal-panel-body">
                        <div id="market-movers" style="display: grid; grid-template-columns: 1fr 1fr; gap: 1rem;">
                            <div>
                                <div style="font-size: 0.75rem; color: var(--accent-success); margin-bottom: 0.5rem;">TOP GAINERS</div>
                                <div id="top-gainers" style="font-size: 0.75rem;">Loading...</div>
                            </div>
                            <div>
                                <div style="font-size: 0.75rem; color: var(--accent-danger); margin-bottom: 0.5rem;">TOP LOSERS</div>
                                <div id="top-losers" style="font-size: 0.75rem;">Loading...</div>
                            </div>
                        </div>
                    </div>
                </div>
            </div>

            <!-- Social Feeds Grid -->
            <div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(350px, 1fr)); gap: var(--spacing-md);">

                <!-- Twitter Feed -->
                <div class="terminal-panel">
                    <div class="terminal-panel-header">
                        <span class="terminal-panel-title">Twitter/X</span>
                        <span class="terminal-badge info" id="twitter-count">0</span>
                    </div>
                    <div class="terminal-panel-body" style="max-height: 500px; overflow-y: auto;" id="twitter-feed">
                        <div style="text-align: center; color: var(--text-secondary); padding: 2rem;">Loading tweets...</div>
                    </div>
                </div>

                <!-- Reddit Feed -->
                <div class="terminal-panel">
                    <div class="terminal-panel-header">
                        <span class="terminal-panel-title">Reddit</span>
                        <span class="terminal-badge info" id="reddit-count">0</span>
                    </div>
                    <div class="terminal-panel-body" style="max-height: 500px; overflow-y: auto;" id="reddit-feed">
                        <div style="text-align: center; color: var(--text-secondary); padding: 2rem;">Loading posts...</div>
                    </div>
                </div>

                <!-- News Feed -->
                <div class="terminal-panel">
                    <div class="terminal-panel-header">
                        <span class="terminal-panel-title">Crypto News</span>
                        <span class="terminal-badge info" id="news-count">0</span>
                    </div>
                    <div class="terminal-panel-body" style="max-height: 500px; overflow-y: auto;" id="news-feed">
                        <div style="text-align: center; color: var(--text-secondary); padding: 2rem;">Loading news...</div>
                    </div>
                </div>
            </div>

            <style>
                .modal-overlay {
                    position: fixed;
                    top: 0;
                    left: 0;
                    width: 100%;
                    height: 100%;
                    background: rgba(0,0,0,0.8);
                    z-index: 1000;
                    display: flex;
                    align-items: center;
                    justify-content: center;
                }
                .modal-content {
                    background: var(--bg-panel);
                    border: 1px solid var(--border-primary);
                    border-radius: 8px;
                    max-width: 500px;
                    width: 90%;
                    max-height: 80vh;
                    overflow-y: auto;
                }
                .modal-header {
                    display: flex;
                    justify-content: space-between;
                    align-items: center;
                    padding: 1rem 1.5rem;
                    border-bottom: 1px solid var(--border-primary);
                }
                .modal-header h2 {
                    margin: 0;
                    font-size: 1.125rem;
                }
                .modal-close {
                    background: none;
                    border: none;
                    color: var(--text-secondary);
                    font-size: 1.5rem;
                    cursor: pointer;
                }
                .modal-body {
                    padding: 1.5rem;
                }
                .modal-footer {
                    display: flex;
                    gap: 0.5rem;
                    justify-content: flex-end;
                    padding: 1rem 1.5rem;
                    border-top: 1px solid var(--border-primary);
                }
                .settings-group {
                    margin-bottom: 1.5rem;
                }
                .settings-label {
                    display: block;
                    font-weight: 600;
                    margin-bottom: 0.5rem;
                }
                .settings-input {
                    width: 100%;
                    padding: 0.5rem;
                    background: var(--bg-card);
                    border: 1px solid var(--border-primary);
                    color: var(--text-primary);
                    border-radius: 4px;
                }
                .checkbox-group {
                    display: flex;
                    flex-direction: column;
                    gap: 0.5rem;
                }
                .checkbox-group label {
                    display: flex;
                    align-items: center;
                    gap: 0.5rem;
                    cursor: pointer;
                }
                .settings-checkbox {
                    display: flex;
                    align-items: center;
                    gap: 0.5rem;
                    cursor: pointer;
                }
                .btn {
                    padding: 0.5rem 1rem;
                    border-radius: 4px;
                    cursor: pointer;
                    font-weight: 500;
                }
                .btn-primary {
                    background: var(--accent-primary);
                    color: white;
                    border: none;
                }
                .btn-secondary {
                    background: var(--bg-card);
                    color: var(--text-primary);
                    border: 1px solid var(--border-primary);
                }
                .feed-item {
                    padding: 0.75rem;
                    border-bottom: 1px solid var(--border-subtle);
                }
                .feed-item:last-child {
                    border-bottom: none;
                }
                .feed-item:hover {
                    background: var(--bg-hover);
                }
                .feed-title {
                    font-weight: 600;
                    font-size: 0.875rem;
                    color: var(--text-primary);
                    text-decoration: none;
                    display: block;
                    margin-bottom: 0.25rem;
                }
                .feed-title:hover {
                    color: var(--accent-primary);
                }
                .feed-meta {
                    font-size: 0.75rem;
                    color: var(--text-secondary);
                }
                .feed-stats {
                    font-size: 0.75rem;
                    color: var(--text-tertiary);
                    font-family: var(--font-mono);
                    margin-top: 0.25rem;
                }
                .sentiment-badge {
                    display: inline-block;
                    padding: 0.125rem 0.375rem;
                    border-radius: 3px;
                    font-size: 0.625rem;
                    font-weight: 600;
                    text-transform: uppercase;
                }
                .sentiment-positive { background: rgba(22, 199, 132, 0.2); color: var(--accent-success); }
                .sentiment-negative { background: rgba(234, 57, 67, 0.2); color: var(--accent-danger); }
                .sentiment-neutral { background: rgba(255, 255, 255, 0.1); color: var(--text-secondary); }
                .whale-item {
                    padding: 0.5rem;
                    border-bottom: 1px solid var(--border-subtle);
                    font-size: 0.75rem;
                }
                .whale-amount {
                    font-weight: 700;
                    font-family: var(--font-mono);
                }
                .trending-tag {
                    display: inline-flex;
                    align-items: center;
                    gap: 0.25rem;
                    padding: 0.25rem 0.5rem;
                    background: var(--bg-card);
                    border: 1px solid var(--border-primary);
                    border-radius: 4px;
                    font-size: 0.75rem;
                    cursor: pointer;
                    transition: all 0.2s;
                }
                .trending-tag:hover {
                    border-color: var(--accent-primary);
                    background: var(--bg-hover);
                }
                .trending-tag.hot {
                    border-color: #ff6b35;
                    background: rgba(255, 107, 53, 0.1);
                }
                .mover-item {
                    display: flex;
                    justify-content: space-between;
                    align-items: center;
                    padding: 0.25rem 0;
                    border-bottom: 1px solid var(--border-subtle);
                }
                .mover-symbol {
                    font-weight: 600;
                    font-family: var(--font-mono);
                }
                .mover-change {
                    font-family: var(--font-mono);
                    font-weight: 600;
                }
                .mover-change.positive { color: var(--accent-success); }
                .mover-change.negative { color: var(--accent-danger); }
            </style>
        `;
    }

    async loadAllData() {
        console.log('Loading social intelligence data for', this.currentCoin || 'all coins');

        try {
            await Promise.all([
                this.loadFearGreed(),
                this.loadSentiment(),
                this.loadWhaleAlerts(),
                this.loadTrending(),
                this.loadMarketMovers(),
                this.loadTwitterFeed(),
                this.loadRedditFeed(),
                this.loadNewsFeed()
            ]);
        } catch (error) {
            console.error('Error loading social data:', error);
        }
    }

    async loadFearGreed() {
        try {
            const response = await fetch(`${this.apiBase}/social/fear-greed`);
            const result = await response.json();

            if (result.success) {
                this.data.fearGreed = result.data;
                this.renderFearGreed(result.data);
            }
        } catch (error) {
            console.error('Error loading Fear & Greed:', error);
        }
    }

    renderFearGreed(data) {
        const emojiEl = document.getElementById('fng-emoji');
        const valueEl = document.getElementById('fng-value');
        const labelEl = document.getElementById('fng-label');
        const trendEl = document.getElementById('fng-trend');

        if (emojiEl) emojiEl.textContent = data.emoji;
        if (valueEl) {
            valueEl.textContent = data.value;
            valueEl.style.color = data.color;
        }
        if (labelEl) labelEl.textContent = data.classification;
        if (trendEl) {
            const changeText = data.daily_change >= 0 ? `+${data.daily_change}` : data.daily_change;
            const weeklyText = data.weekly_change >= 0 ? `+${data.weekly_change}` : data.weekly_change;
            trendEl.innerHTML = `
                <span style="color: var(--text-secondary);">24h:</span>
                <span style="color: ${data.daily_change >= 0 ? 'var(--accent-success)' : 'var(--accent-danger)'};">${changeText}</span>
                <span style="margin-left: 0.5rem; color: var(--text-secondary);">7d:</span>
                <span style="color: ${data.weekly_change >= 0 ? 'var(--accent-success)' : 'var(--accent-danger)'};">${weeklyText}</span>
            `;
        }
    }

    async loadSentiment() {
        try {
            const coinParam = this.currentCoin ? `?coin=${this.currentCoin}` : '';
            const response = await fetch(`${this.apiBase}/social/sentiment${coinParam}`);
            const result = await response.json();

            if (result.success) {
                this.data.sentiment = result.data;
                this.renderSentiment(result.data);
            }
        } catch (error) {
            console.error('Error loading sentiment:', error);
        }
    }

    renderSentiment(data) {
        const gaugeEl = document.getElementById('sentiment-gauge');
        const scoreEl = document.getElementById('sentiment-score');
        const labelEl = document.getElementById('sentiment-label');

        if (gaugeEl) gaugeEl.textContent = data.overall_emoji || '...';
        if (scoreEl) scoreEl.textContent = `${data.overall_score}%`;
        if (labelEl) {
            const trendText = data.trend ? ` (${data.trend.replace('_', ' ')})` : '';
            labelEl.textContent = (data.overall_label || 'Neutral') + trendText;
        }

        // Platform scores
        ['twitter', 'reddit', 'news'].forEach(platform => {
            const el = document.getElementById(`${platform}-sentiment`);
            if (el && data.by_platform) {
                const score = data.by_platform[platform] || 50;
                el.textContent = `${score}%`;
                el.style.color = this.getSentimentColor(score);
            }
        });
    }

    getSentimentColor(score) {
        if (score >= 60) return 'var(--accent-success)';
        if (score <= 40) return 'var(--accent-danger)';
        return 'var(--text-secondary)';
    }

    async loadWhaleAlerts() {
        try {
            const coin = this.currentCoin || 'BTC';
            const response = await fetch(`${this.apiBase}/social/whale-alerts?coin=${coin}`);
            const result = await response.json();

            if (result.success) {
                this.data.whaleAlerts = result.data;
                this.renderWhaleAlerts(result.data);
            }
        } catch (error) {
            console.error('Error loading whale alerts:', error);
        }
    }

    renderWhaleAlerts(alerts) {
        const container = document.getElementById('whale-alerts-container');
        if (!container) return;

        if (!alerts || alerts.length === 0) {
            container.innerHTML = '<div style="text-align: center; color: var(--text-secondary); padding: 1rem;">No recent whale alerts</div>';
            return;
        }

        container.innerHTML = alerts.slice(0, 5).map(alert => {
            const timeAgo = this.formatTimeAgo(alert.timestamp * 1000);
            const amountFormatted = alert.amount.toLocaleString();
            const usdFormatted = alert.amount_usd.toLocaleString();

            return `
                <div class="whale-item">
                    <div style="display: flex; justify-content: space-between; align-items: center;">
                        <span class="whale-amount">${amountFormatted} ${alert.coin}</span>
                        <span style="color: var(--text-secondary);">${timeAgo}</span>
                    </div>
                    <div style="color: var(--text-tertiary); margin-top: 0.25rem;">
                        $${usdFormatted} USD | ${alert.from} &rarr; ${alert.to}
                    </div>
                </div>
            `;
        }).join('');
    }

    async loadTrending() {
        try {
            const response = await fetch(`${this.apiBase}/social/trending`);
            const result = await response.json();

            if (result.success) {
                this.data.trending = result.data;
                this.renderTrending(result.data);
            }
        } catch (error) {
            console.error('Error loading trending:', error);
        }
    }

    renderTrending(topics) {
        const container = document.getElementById('trending-topics');
        if (!container) return;

        if (!topics || topics.length === 0) {
            container.innerHTML = '<div style="color: var(--text-secondary);">No trending topics</div>';
            return;
        }

        container.innerHTML = topics.slice(0, 15).map(topic => {
            const isHot = topic.momentum === 'hot';
            return `
                <div class="trending-tag ${isHot ? 'hot' : ''}">
                    <span>${topic.emoji}</span>
                    <span>${topic.topic}</span>
                    <span style="color: var(--text-tertiary); font-family: var(--font-mono);">${topic.mentions}</span>
                    <span>${topic.sentiment_emoji}</span>
                </div>
            `;
        }).join('');
    }

    async loadMarketMovers() {
        try {
            const response = await fetch(`${this.apiBase}/social/market-movers`);
            const result = await response.json();

            if (result.success) {
                this.data.marketMovers = result.data;
                this.renderMarketMovers(result.data);
            }
        } catch (error) {
            console.error('Error loading market movers:', error);
        }
    }

    renderMarketMovers(data) {
        const gainersEl = document.getElementById('top-gainers');
        const losersEl = document.getElementById('top-losers');

        if (gainersEl && data.gainers) {
            gainersEl.innerHTML = data.gainers.slice(0, 5).map(coin => `
                <div class="mover-item">
                    <span class="mover-symbol">${coin.symbol}</span>
                    <span class="mover-change positive">+${coin.price_change_24h?.toFixed(1)}%</span>
                </div>
            `).join('');
        }

        if (losersEl && data.losers) {
            losersEl.innerHTML = data.losers.slice(0, 5).map(coin => `
                <div class="mover-item">
                    <span class="mover-symbol">${coin.symbol}</span>
                    <span class="mover-change negative">${coin.price_change_24h?.toFixed(1)}%</span>
                </div>
            `).join('');
        }
    }

    async loadTwitterFeed() {
        try {
            const keywords = this.settings.twitterKeywords.join(',');
            const coinParam = this.currentCoin ? `&coin=${this.currentCoin}` : '';
            const response = await fetch(`${this.apiBase}/social/twitter?keywords=${keywords}${coinParam}`);
            const result = await response.json();

            if (result.success) {
                this.data.twitter = result.data;
                this.renderTwitterFeed(result.data);
                const countEl = document.getElementById('twitter-count');
                if (countEl) countEl.textContent = result.data.length;
            }
        } catch (error) {
            console.error('Error loading Twitter feed:', error);
        }
    }

    renderTwitterFeed(tweets) {
        const container = document.getElementById('twitter-feed');
        if (!container) return;

        if (!tweets || tweets.length === 0) {
            container.innerHTML = '<div style="text-align: center; color: var(--text-secondary); padding: 2rem;">No tweets found</div>';
            return;
        }

        container.innerHTML = tweets.map(tweet => `
            <div class="feed-item">
                <div style="display: flex; justify-content: space-between; align-items: start; margin-bottom: 0.25rem;">
                    <div>
                        <a href="${tweet.url}" target="_blank" class="feed-title" style="font-size: 0.8rem;">
                            @${tweet.author.username}
                            ${tweet.author.verified ? '<span style="color: #1DA1F2;">&#10003;</span>' : ''}
                        </a>
                        <div class="feed-meta">${this.formatTimeAgo(tweet.created_at)}</div>
                    </div>
                    ${this.renderSentimentBadge(tweet.sentiment)}
                </div>
                <div style="font-size: 0.8rem; margin: 0.5rem 0;">${tweet.text}</div>
                <div class="feed-stats">
                    &#9829; ${this.formatNumber(tweet.metrics.likes)}
                    &#8634; ${this.formatNumber(tweet.metrics.retweets)}
                    &#128172; ${this.formatNumber(tweet.metrics.replies)}
                    ${tweet.metrics.views ? `&#128065; ${this.formatNumber(tweet.metrics.views)}` : ''}
                </div>
            </div>
        `).join('');
    }

    async loadRedditFeed() {
        try {
            const subreddits = this.settings.subreddits.join(',');
            const coinParam = this.currentCoin ? `&coin=${this.currentCoin}` : '';
            const response = await fetch(`${this.apiBase}/social/reddit?subreddits=${subreddits}${coinParam}`);
            const result = await response.json();

            if (result.success) {
                this.data.reddit = result.data;
                this.renderRedditFeed(result.data);
                const countEl = document.getElementById('reddit-count');
                if (countEl) countEl.textContent = result.data.length;
            }
        } catch (error) {
            console.error('Error loading Reddit feed:', error);
        }
    }

    renderRedditFeed(posts) {
        const container = document.getElementById('reddit-feed');
        if (!container) return;

        if (!posts || posts.length === 0) {
            container.innerHTML = '<div style="text-align: center; color: var(--text-secondary); padding: 2rem;">No posts found</div>';
            return;
        }

        container.innerHTML = posts.map(post => `
            <div class="feed-item">
                <div style="display: flex; justify-content: space-between; align-items: start;">
                    <div style="flex: 1; min-width: 0;">
                        <a href="${post.url}" target="_blank" class="feed-title">${this.truncate(post.title, 80)}</a>
                        <div class="feed-meta">r/${post.subreddit} | u/${post.author}</div>
                    </div>
                    ${this.renderSentimentBadge(post.sentiment)}
                </div>
                <div class="feed-stats">
                    &#9650; ${this.formatNumber(post.score)} | &#128172; ${post.num_comments}
                    ${post.awards > 0 ? `| &#127942; ${post.awards}` : ''}
                </div>
            </div>
        `).join('');
    }

    async loadNewsFeed() {
        try {
            const sources = this.settings.newsSources.join(',');
            const coinParam = this.currentCoin ? `&coin=${this.currentCoin}` : '';
            const response = await fetch(`${this.apiBase}/social/news?sources=${sources}${coinParam}`);
            const result = await response.json();

            if (result.success) {
                this.data.news = result.data;
                this.renderNewsFeed(result.data);
                const countEl = document.getElementById('news-count');
                if (countEl) countEl.textContent = result.data.length;
            }
        } catch (error) {
            console.error('Error loading news feed:', error);
        }
    }

    renderNewsFeed(articles) {
        const container = document.getElementById('news-feed');
        if (!container) return;

        if (!articles || articles.length === 0) {
            container.innerHTML = '<div style="text-align: center; color: var(--text-secondary); padding: 2rem;">No articles found</div>';
            return;
        }

        container.innerHTML = articles.map(article => `
            <div class="feed-item">
                <div style="display: flex; justify-content: space-between; align-items: start;">
                    <div style="flex: 1; min-width: 0;">
                        <a href="${article.url}" target="_blank" class="feed-title">${this.truncate(article.title, 70)}</a>
                        <div class="feed-meta">${article.source_name} | ${this.formatTimeAgo(article.published_at)}</div>
                    </div>
                    ${this.renderSentimentBadge(article.sentiment)}
                </div>
                ${article.description ? `<div style="font-size: 0.75rem; color: var(--text-tertiary); margin-top: 0.25rem;">${this.truncate(article.description, 120)}</div>` : ''}
            </div>
        `).join('');
    }

    renderSentimentBadge(sentiment) {
        if (!sentiment) return '';
        const label = sentiment.label || 'neutral';
        return `<span class="sentiment-badge sentiment-${label}">${label}</span>`;
    }

    formatTimeAgo(timestamp) {
        const now = new Date();
        const then = new Date(timestamp);
        const seconds = Math.floor((now - then) / 1000);

        if (isNaN(seconds) || seconds < 0) return 'now';
        if (seconds < 60) return 'now';
        if (seconds < 3600) return `${Math.floor(seconds / 60)}m`;
        if (seconds < 86400) return `${Math.floor(seconds / 3600)}h`;
        return `${Math.floor(seconds / 86400)}d`;
    }

    formatNumber(num) {
        if (!num) return '0';
        if (num >= 1000000) return (num / 1000000).toFixed(1) + 'M';
        if (num >= 1000) return (num / 1000).toFixed(1) + 'K';
        return num.toString();
    }

    truncate(str, len) {
        if (!str) return '';
        return str.length > len ? str.substring(0, len) + '...' : str;
    }

    startAutoUpdate() {
        if (this.intervalId) clearInterval(this.intervalId);
        this.intervalId = setInterval(() => this.loadAllData(), this.updateInterval);
        console.log(`Auto-update started (${this.updateInterval / 1000}s)`);
    }

    stopAutoUpdate() {
        if (this.intervalId) {
            clearInterval(this.intervalId);
            this.intervalId = null;
        }
    }

    destroy() {
        this.stopAutoUpdate();
    }

    openSettings() {
        const modal = document.getElementById('social-settings-modal');
        if (!modal) return;

        // Populate settings
        ['coindesk', 'decrypt', 'cointelegraph', 'theblock', 'bitcoinmagazine', 'blockworks'].forEach(source => {
            const checkbox = document.getElementById(`source-${source}`);
            if (checkbox) checkbox.checked = this.settings.newsSources.includes(source);
        });

        document.getElementById('subreddits-input').value = this.settings.subreddits.join(', ');
        document.getElementById('auto-refresh-toggle').checked = this.settings.autoRefresh;
        document.getElementById('refresh-interval-input').value = this.settings.refreshInterval;

        modal.style.display = 'flex';
    }

    closeSettings() {
        const modal = document.getElementById('social-settings-modal');
        if (modal) modal.style.display = 'none';
    }

    resetSettings() {
        this.settings = {
            newsSources: ['coindesk', 'decrypt', 'cointelegraph', 'theblock', 'bitcoinmagazine'],
            subreddits: ['cryptocurrency', 'bitcoin', 'ethtrader', 'solana'],
            twitterKeywords: ['bitcoin', 'crypto', 'btc', 'ethereum'],
            autoRefresh: true,
            refreshInterval: 60
        };
        this.saveSettings();
        this.openSettings();
    }

    async applySettings() {
        // Get news sources
        const sources = [];
        ['coindesk', 'decrypt', 'cointelegraph', 'theblock', 'bitcoinmagazine', 'blockworks'].forEach(source => {
            const checkbox = document.getElementById(`source-${source}`);
            if (checkbox && checkbox.checked) sources.push(source);
        });
        this.settings.newsSources = sources;

        // Get subreddits
        const subredditsInput = document.getElementById('subreddits-input').value;
        this.settings.subreddits = subredditsInput.split(',').map(s => s.trim()).filter(s => s);

        // Get refresh settings
        this.settings.autoRefresh = document.getElementById('auto-refresh-toggle').checked;
        this.settings.refreshInterval = parseInt(document.getElementById('refresh-interval-input').value) || 60;

        this.saveSettings();
        this.updateInterval = this.settings.refreshInterval * 1000;

        if (this.settings.autoRefresh) {
            this.startAutoUpdate();
        } else {
            this.stopAutoUpdate();
        }

        this.closeSettings();
        await this.loadAllData();
    }
}

// Export
if (typeof window !== 'undefined') {
    window.SocialIntelligence = SocialIntelligence;
}
