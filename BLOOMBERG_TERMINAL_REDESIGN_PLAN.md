# Bloomberg Terminal-Style Dashboard Redesign Plan

## Executive Summary

Transform the Odin Analytics Dashboard into a professional Bloomberg Terminal-style interface with:
- **Dense, information-rich layout** with multi-panel design
- **Dedicated Social Media Intelligence page** for crypto-wide sentiment analysis
- **Professional styling** with dark theme, cyan accents, and terminal aesthetics
- **Enhanced data visualization** with advanced charts and real-time updates

---

## 1. Dashboard Layout Architecture

### Current State
- 12-column grid system ✅
- Single-page layout with sections stacked vertically
- Basic card system
- Sticky header with coin selector

### New Bloomberg-Style Layout

#### Header Bar (Fixed Top)
```
┌─────────────────────────────────────────────────────────────────────┐
│ [ODIN] BTC $98,234 ▲2.34% | ETH $3,456 ▼1.2% | 🟢 LIVE | 🔔 | ⚙️  │
└─────────────────────────────────────────────────────────────────────┘
```

**Features:**
- Live ticker showing all 7 coins with price + % change
- Status indicator (LIVE/DELAYED)
- Notification bell with count badge
- Settings/profile dropdown
- Current time (HH:MM:SS UTC)

#### Main Dashboard Layout (3-Panel Design)
```
┌──────────────────────────────────────────────────────────────────┐
│                         TICKER BAR                                │
├─────────────┬────────────────────────────────┬───────────────────┤
│             │                                │                   │
│   LEFT      │        MAIN CHART AREA         │   RIGHT PANEL     │
│   PANEL     │                                │                   │
│             │                                │                   │
│  - Markets  │   [PRICE CHART 24H]           │  - Quick Stats    │
│  - Alerts   │                                │  - RSI/MACD       │
│  - Watchlist│   Indicators: MA(20) BB VWAP  │  - Signals        │
│             │                                │  - News Feed      │
│  (280px)    │   Volume Chart Below           │  - Top Movers     │
│             │                                │                   │
│             │                                │  (320px)          │
├─────────────┴────────────────────────────────┴───────────────────┤
│                    BOTTOM PANEL (Tabs)                            │
│  [Market Depth] [Liquidations] [Funding] [Order Flow] [Social]   │
│                                                                    │
│  [Chart visualization for selected tab]                           │
└──────────────────────────────────────────────────────────────────┘
```

**Grid Breakdown:**
- Left Panel: 2 columns (280px fixed)
- Main Chart: 7 columns (fluid)
- Right Panel: 3 columns (320px fixed)
- Bottom Panel: 12 columns (collapsible, 400px height)

---

## 2. Social Intelligence Page Structure

### New Route: `/dashboard/social`

#### Layout Design
```
┌──────────────────────────────────────────────────────────────────┐
│                    SOCIAL INTELLIGENCE DASHBOARD                  │
├──────────────────────────────────────────────────────────────────┤
│  Filters: [All Coins ▼] [All Platforms ▼] [24H ▼] [Sentiment: All]│
├─────────────────────────┬────────────────────────────────────────┤
│                         │                                        │
│  SENTIMENT OVERVIEW     │     TRENDING TOPICS                    │
│                         │                                        │
│  📊 Overall: 72% 🟢    │  #Bitcoin        🔥 15.2K mentions     │
│  ───────────────────    │  #ETF            📈 12.8K mentions     │
│  [Gauge Chart]          │  #Altseason      💬 8.4K mentions      │
│                         │  #DeFi           ⚡ 6.1K mentions      │
│  By Platform:           │  #Regulation     ⚠️  4.9K mentions     │
│  Twitter:  68% 🟡      │                                        │
│  Reddit:   76% 🟢      │  [Trending Chart: 24H mentions]        │
│  News:     65% 🟡      │                                        │
├─────────────────────────┴────────────────────────────────────────┤
│                      SOCIAL FEED (Multi-Column)                   │
├──────────────┬─────────────────┬──────────────┬─────────────────┤
│   TWITTER    │     REDDIT      │     NEWS     │   TOP VOICES    │
│              │                 │              │                 │
│ @whale       │ r/cryptocurrency│ CoinDesk:    │ 1. @CryptoWhale │
│ "Bitcoin to  │ Post: "ETH 2.0  │ "Bitcoin ETF │    Sentiment: 🟢│
│  $100k soon" │  staking..."    │  approval..."│    Followers:   │
│ 👍 2.4K 🔁1K│ ⬆ 1.2K 💬 340  │ 😊 Positive  │    1.2M         │
│ 😊 Positive  │ 😊 Positive     │              │                 │
│              │                 │              │ 2. @VitalikB    │
│ @trader_123  │ r/bitcoin       │ Decrypt:     │    Sentiment: 🟡│
│ "Market dump │ Post: "BTC fear │ "Ethereum... │    Followers:   │
│  incoming"   │  & greed..."    │ 😐 Neutral   │    5.2M         │
│ 👍 892 🔁234 │ ⬆ 890 💬 156   │              │                 │
│ 😞 Negative  │ 😐 Neutral      │              │                 │
└──────────────┴─────────────────┴──────────────┴─────────────────┘
```

### Social Intelligence Features

#### 1. Sentiment Analysis
- **Overall Score**: Aggregate sentiment across all sources (0-100 scale)
- **By Platform**: Breakdown by Twitter, Reddit, News
- **By Coin**: Individual sentiment for each of the 7 coins
- **Trend Visualization**: Line chart showing sentiment over time (24H, 7D, 30D)
- **Sentiment Gauge**: Visual gauge/speedometer showing current sentiment

#### 2. Trending Topics
- **Hashtag Tracking**: Top 10 trending crypto hashtags
- **Mention Volume**: Count of mentions in last 24H
- **Momentum Indicator**: 🔥 (hot), 📈 (rising), 📉 (falling), ⚠️ (controversial)
- **Topic Chart**: Area chart showing mention volume over time

#### 3. Social Feed Aggregation
- **Multi-column layout**: Twitter | Reddit | News | Top Voices
- **Real-time updates**: New posts appear with slide-in animation
- **Sentiment labeling**: Each post tagged with 😊 Positive, 😐 Neutral, 😞 Negative
- **Engagement metrics**: Likes, retweets, comments, upvotes
- **Filtering**: By coin, platform, sentiment, timeframe

#### 4. Top Voices/Influencers
- **Ranked list**: Top 20 crypto influencers
- **Sentiment score**: Overall sentiment of their recent posts
- **Follower count**: Audience size
- **Recent activity**: Latest tweets/posts
- **Influence score**: Custom algorithm based on engagement + accuracy

#### 5. News Sentiment
- **Aggregated sources**: CoinDesk, CoinTelegraph, Decrypt, The Block, etc.
- **AI sentiment analysis**: Positive/Neutral/Negative classification
- **Article preview**: Title, excerpt, thumbnail
- **Source credibility**: Badge for verified/trusted sources

---

## 3. Component Breakdown

### File Structure
```
web/
├── templates/
│   ├── dashboard.html (REDESIGN - Bloomberg main)
│   ├── social-intelligence.html (NEW - Social media page)
│   └── dashboard-backup.html (existing backup)
├── static/
│   ├── js/
│   │   ├── analytics-dashboard.js (ENHANCE - add Bloomberg features)
│   │   ├── social-dashboard.js (NEW - social intelligence logic)
│   │   ├── bloomberg-layout.js (NEW - panel management, resize)
│   │   ├── sentiment-analyzer.js (NEW - client-side sentiment)
│   │   ├── ticker-bar.js (NEW - live multi-coin ticker)
│   │   └── charts-advanced.js (NEW - advanced chart configs)
│   ├── css/
│   │   ├── bloomberg-terminal.css (NEW - main terminal styles)
│   │   ├── social-intelligence.css (NEW - social page styles)
│   │   ├── components.css (NEW - reusable components)
│   │   └── dashboard.css (ENHANCE - keep existing, add to it)
│   └── images/
│       └── platform-icons/ (NEW - Twitter, Reddit, etc. icons)
```

### Key Components

#### Component 1: Live Ticker Bar
**File:** `web/static/js/ticker-bar.js`
```javascript
class LiveTickerBar {
    constructor(coins) {
        this.coins = coins; // ['BTC', 'ETH', 'SOL', ...]
        this.prices = {};
        this.updateInterval = 3000; // 3 seconds
    }

    async fetchAllPrices() {
        // Fetch prices for all coins in parallel
        const promises = this.coins.map(coin =>
            fetch(`/api/data/price?symbol=${coin}`)
        );
        const results = await Promise.allSettled(promises);
        // Update ticker display
    }

    render() {
        // Create ticker HTML with auto-scroll
    }
}
```

#### Component 2: Resizable Panels
**File:** `web/static/js/bloomberg-layout.js`
```javascript
class BloombergLayout {
    constructor() {
        this.panels = {
            left: { width: 280, minWidth: 200, maxWidth: 400 },
            right: { width: 320, minWidth: 250, maxWidth: 500 },
            bottom: { height: 400, minHeight: 200, maxHeight: 600 }
        };
    }

    initResizers() {
        // Add drag handles between panels
        // Save panel sizes to localStorage
    }

    togglePanel(panel) {
        // Collapse/expand panels
    }
}
```

#### Component 3: Social Feed Manager
**File:** `web/static/js/social-dashboard.js`
```javascript
class SocialDashboard {
    constructor() {
        this.feeds = {
            twitter: [],
            reddit: [],
            news: []
        };
        this.sentiment = {
            overall: 0,
            byPlatform: {},
            byCoin: {}
        };
    }

    async loadAllFeeds() {
        await Promise.all([
            this.loadTwitterFeed(),
            this.loadRedditFeed(),
            this.loadNewsFeed()
        ]);
        this.calculateSentiment();
        this.renderFeeds();
    }

    async loadTwitterFeed() {
        // Fetch from /api/social/twitter
        // Parse and analyze sentiment
    }

    calculateSentiment() {
        // Aggregate sentiment from all sources
        // Calculate trending topics
    }

    renderFeeds() {
        // Multi-column feed layout
    }
}
```

#### Component 4: Sentiment Analyzer
**File:** `web/static/js/sentiment-analyzer.js`
```javascript
class SentimentAnalyzer {
    constructor() {
        this.positiveWords = ['bullish', 'moon', 'pump', 'up', 'gains', ...];
        this.negativeWords = ['bearish', 'dump', 'crash', 'down', 'rekt', ...];
    }

    analyze(text) {
        // Simple keyword-based sentiment
        // Returns score from -1 (negative) to 1 (positive)
        let score = 0;
        const words = text.toLowerCase().split(/\s+/);

        words.forEach(word => {
            if (this.positiveWords.includes(word)) score += 1;
            if (this.negativeWords.includes(word)) score -= 1;
        });

        const normalized = score / words.length;
        return {
            score: normalized,
            label: normalized > 0.1 ? 'positive' :
                   normalized < -0.1 ? 'negative' : 'neutral'
        };
    }
}
```

#### Component 5: Advanced Charts
**File:** `web/static/js/charts-advanced.js`
```javascript
class AdvancedCharts {
    createVolumeProfile(data) {
        // Horizontal volume bars at price levels
    }

    createOrderFlow(data) {
        // Buy/sell volume delta chart
    }

    createSentimentGauge(score) {
        // Speedometer-style gauge chart
        // Uses Chart.js doughnut with custom styling
    }

    createTrendingChart(topics) {
        // Stacked area chart for trending topics over time
    }
}
```

---

## 4. Data Flow Architecture

### Main Dashboard Data Flow
```
User loads /dashboard
    ↓
analytics-dashboard.js initializes
    ↓
AnalyticsDashboard class:
    - initializeCharts() → Creates all Chart.js instances
    - loadAllData() → Fetches from 18 API endpoints
    ↓
Promise.allSettled([
    /api/data/price?symbol=BTC
    /api/data/indicators?symbol=BTC
    /api/data/history/24?symbol=BTC
    /api/data/depth?symbol=BTC
    /api/data/funding?symbol=BTC
    ... (13 more endpoints)
])
    ↓
Data returned → Update charts and UI
    ↓
Start auto-refresh (every 30s)
```

### Social Intelligence Data Flow
```
User loads /dashboard/social
    ↓
social-dashboard.js initializes
    ↓
SocialDashboard class:
    - loadAllFeeds() → Parallel fetch from 3 sources
    ↓
Promise.all([
    /api/social/twitter?coins=all
    /api/social/reddit?coins=all
    /api/social/news?coins=all
])
    ↓
For each post/article:
    - SentimentAnalyzer.analyze(text) → Get sentiment
    - Tag with sentiment label
    - Calculate engagement score
    ↓
Aggregate data:
    - Overall sentiment score
    - Trending topics (hashtag frequency)
    - Top influencers (by engagement)
    ↓
Render:
    - Sentiment gauge
    - Trending topics list
    - Multi-column feeds
    - Top voices panel
    ↓
Start real-time updates (every 60s)
```

---

## 5. Styling Strategy

### Color Palette (Bloomberg-Inspired)
```css
:root {
    /* Backgrounds */
    --bg-terminal: #000000;
    --bg-panel: #0a0e1a;
    --bg-card: #131820;
    --bg-header: #0d1117;

    /* Accents */
    --accent-primary: #00d4ff;    /* Cyan - primary actions */
    --accent-secondary: #0099ff;  /* Blue - secondary */
    --accent-success: #00ff88;    /* Green - positive */
    --accent-danger: #ff3366;     /* Red - negative */
    --accent-warning: #ffaa00;    /* Orange - warning */

    /* Text */
    --text-primary: #ffffff;
    --text-secondary: #8b92b0;
    --text-tertiary: #5a5f7a;

    /* Borders */
    --border-primary: #1f2937;
    --border-accent: #00d4ff33;   /* 20% opacity cyan */

    /* Status Colors */
    --status-live: #00ff88;
    --status-delayed: #ffaa00;
    --status-offline: #ff3366;

    /* Sentiment Colors */
    --sentiment-positive: #00ff88;
    --sentiment-neutral: #8b92b0;
    --sentiment-negative: #ff3366;

    /* Chart Colors */
    --chart-up: #00ff88;
    --chart-down: #ff3366;
    --chart-grid: #1f293744;      /* Subtle grid lines */

    /* Fonts */
    --font-primary: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif;
    --font-mono: 'JetBrains Mono', 'Fira Code', 'Courier New', monospace;

    /* Spacing (8px base) */
    --spacing-xs: 4px;
    --spacing-sm: 8px;
    --spacing-md: 16px;
    --spacing-lg: 24px;
    --spacing-xl: 32px;

    /* Shadows */
    --shadow-sm: 0 1px 2px rgba(0, 0, 0, 0.5);
    --shadow-md: 0 4px 8px rgba(0, 0, 0, 0.6);
    --shadow-lg: 0 8px 16px rgba(0, 0, 0, 0.7);
    --shadow-glow: 0 0 20px rgba(0, 212, 255, 0.3);
}
```

### Typography Scale
```css
/* Headers */
.text-xs { font-size: 11px; line-height: 16px; } /* Labels */
.text-sm { font-size: 13px; line-height: 20px; } /* Body small */
.text-base { font-size: 14px; line-height: 22px; } /* Body */
.text-lg { font-size: 16px; line-height: 24px; } /* Subheadings */
.text-xl { font-size: 20px; line-height: 28px; } /* Headings */
.text-2xl { font-size: 24px; line-height: 32px; } /* Large headings */
.text-3xl { font-size: 32px; line-height: 40px; } /* Hero text */
.text-4xl { font-size: 48px; line-height: 56px; } /* Price display */

/* Monospace (for data) */
.mono { font-family: var(--font-mono); font-variant-numeric: tabular-nums; }
```

### Component Styles

#### Terminal Panel
```css
.terminal-panel {
    background: var(--bg-panel);
    border: 1px solid var(--border-primary);
    border-radius: 4px;
    box-shadow: var(--shadow-md);
    overflow: hidden;
}

.terminal-panel-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    padding: 8px 12px;
    background: var(--bg-header);
    border-bottom: 1px solid var(--border-primary);
    font-size: 12px;
    font-weight: 600;
    color: var(--text-secondary);
}

.terminal-panel-body {
    padding: 12px;
}
```

#### Data Table
```css
.terminal-table {
    width: 100%;
    border-collapse: collapse;
    font-family: var(--font-mono);
    font-size: 12px;
}

.terminal-table th {
    text-align: left;
    padding: 8px 12px;
    color: var(--text-secondary);
    font-weight: 600;
    border-bottom: 1px solid var(--border-primary);
    background: var(--bg-header);
}

.terminal-table td {
    padding: 6px 12px;
    border-bottom: 1px solid var(--border-primary);
    color: var(--text-primary);
}

.terminal-table tr:hover {
    background: rgba(0, 212, 255, 0.05);
}

/* Numeric columns */
.terminal-table td.numeric {
    text-align: right;
    font-variant-numeric: tabular-nums;
}

/* Status colors */
.terminal-table .positive { color: var(--accent-success); }
.terminal-table .negative { color: var(--accent-danger); }
```

#### Ticker Bar
```css
.ticker-bar {
    display: flex;
    overflow-x: auto;
    background: var(--bg-header);
    border-bottom: 1px solid var(--border-primary);
    padding: 8px 0;
    gap: 24px;
    font-family: var(--font-mono);
    font-size: 13px;
    scrollbar-width: none; /* Hide scrollbar */
}

.ticker-bar::-webkit-scrollbar {
    display: none;
}

.ticker-item {
    display: flex;
    align-items: center;
    gap: 8px;
    padding: 0 16px;
    white-space: nowrap;
    border-right: 1px solid var(--border-primary);
}

.ticker-symbol {
    font-weight: 700;
    color: var(--text-primary);
}

.ticker-price {
    font-variant-numeric: tabular-nums;
}

.ticker-change.positive {
    color: var(--accent-success);
}

.ticker-change.negative {
    color: var(--accent-danger);
}
```

#### Sentiment Indicator
```css
.sentiment-badge {
    display: inline-flex;
    align-items: center;
    gap: 4px;
    padding: 4px 8px;
    border-radius: 12px;
    font-size: 11px;
    font-weight: 600;
}

.sentiment-badge.positive {
    background: rgba(0, 255, 136, 0.15);
    color: var(--sentiment-positive);
}

.sentiment-badge.neutral {
    background: rgba(139, 146, 176, 0.15);
    color: var(--sentiment-neutral);
}

.sentiment-badge.negative {
    background: rgba(255, 51, 102, 0.15);
    color: var(--sentiment-negative);
}
```

### Responsive Design
```css
/* Desktop (1920px+) - Full Bloomberg layout */
@media (min-width: 1920px) {
    .dashboard-grid {
        grid-template-columns: 280px 1fr 400px;
    }
}

/* Large Desktop (1440px - 1919px) - Standard layout */
@media (min-width: 1440px) and (max-width: 1919px) {
    .dashboard-grid {
        grid-template-columns: 250px 1fr 350px;
    }
}

/* Desktop (1024px - 1439px) - Compact layout */
@media (min-width: 1024px) and (max-width: 1439px) {
    .dashboard-grid {
        grid-template-columns: 220px 1fr 300px;
    }
}

/* Tablet (768px - 1023px) - 2-column layout */
@media (min-width: 768px) and (max-width: 1023px) {
    .dashboard-grid {
        grid-template-columns: 1fr 1fr;
    }
    .left-panel,
    .right-panel {
        grid-column: span 1;
    }
    .main-chart {
        grid-column: span 2;
    }
}

/* Mobile (< 768px) - Single column */
@media (max-width: 767px) {
    .dashboard-grid {
        grid-template-columns: 1fr;
    }
    .ticker-bar {
        font-size: 11px;
    }
}
```

---

## 6. Backend Integration

### New API Endpoints Needed

#### Social Media Endpoints

**1. Twitter/X Feed**
```python
# odin/api/routes/social.py

@router.get("/api/social/twitter")
async def get_twitter_feed(
    coins: str = "all",  # "all" or "BTC,ETH,SOL"
    limit: int = 50
):
    """
    Fetch Twitter posts about crypto

    Options:
    - Use Twitter API v2 (requires API key)
    - Use Nitter RSS (free, no auth)
    - Use pre-scraped data from database
    """
    tweets = await twitter_service.fetch_timeline(coins, limit)

    # Add sentiment analysis
    for tweet in tweets:
        tweet['sentiment'] = sentiment_analyzer.analyze(tweet['text'])

    return {"success": True, "data": tweets}
```

**2. Reddit Feed**
```python
@router.get("/api/social/reddit")
async def get_reddit_feed(
    subreddits: str = "cryptocurrency,bitcoin,ethtrader",
    limit: int = 50
):
    """
    Fetch Reddit posts from crypto subreddits
    Uses Reddit JSON API (no auth required)
    """
    posts = await reddit_service.fetch_posts(subreddits, limit)

    for post in posts:
        post['sentiment'] = sentiment_analyzer.analyze(
            f"{post['title']} {post['selftext']}"
        )

    return {"success": True, "data": posts}
```

**3. News Feed**
```python
@router.get("/api/social/news")
async def get_news_feed(
    sources: str = "all",  # "coindesk,cointelegraph,decrypt"
    limit: int = 30
):
    """
    Fetch crypto news from RSS feeds
    Sources: CoinDesk, CoinTelegraph, Decrypt, The Block
    """
    articles = await news_service.fetch_articles(sources, limit)

    for article in articles:
        article['sentiment'] = sentiment_analyzer.analyze(
            f"{article['title']} {article['description']}"
        )

    return {"success": True, "data": articles}
```

**4. Trending Topics**
```python
@router.get("/api/social/trending")
async def get_trending_topics(
    timeframe: str = "24h"  # "1h", "24h", "7d"
):
    """
    Get trending hashtags/topics across all sources
    """
    trends = await social_aggregator.get_trending(timeframe)

    return {
        "success": True,
        "data": {
            "topics": trends['topics'],  # [{tag, count, momentum}]
            "timeframe": timeframe,
            "updated_at": datetime.utcnow().isoformat()
        }
    }
```

**5. Sentiment Overview**
```python
@router.get("/api/social/sentiment")
async def get_sentiment_overview(
    coins: str = "all",
    timeframe: str = "24h"
):
    """
    Get aggregated sentiment across all sources
    """
    sentiment = await sentiment_aggregator.calculate_overall(coins, timeframe)

    return {
        "success": True,
        "data": {
            "overall_score": sentiment['overall'],  # 0-100
            "by_platform": {
                "twitter": sentiment['twitter'],
                "reddit": sentiment['reddit'],
                "news": sentiment['news']
            },
            "by_coin": sentiment['by_coin'],  # {BTC: 72, ETH: 68, ...}
            "trend": sentiment['trend']  # "rising", "falling", "stable"
        }
    }
```

#### Multi-Coin Price Endpoint
```python
@router.get("/api/data/prices/all")
async def get_all_prices():
    """
    Get current prices for all 7 coins in one request
    For ticker bar updates
    """
    coins = ['BTC', 'ETH', 'SOL', 'XRP', 'BNB', 'SUI', 'HYPE']
    prices = await price_service.fetch_multiple(coins)

    return {
        "success": True,
        "data": prices,  # {BTC: {price, change_24h, ...}, ...}
        "timestamp": datetime.utcnow().isoformat()
    }
```

### Backend Services to Create

**1. Twitter Service** (`odin/services/twitter_service.py`)
```python
class TwitterService:
    def __init__(self):
        # Option A: Use Nitter (free)
        self.nitter_instance = "https://nitter.net"

        # Option B: Use Twitter API (paid)
        # self.api_key = os.getenv("TWITTER_API_KEY")

    async def fetch_timeline(self, keywords, limit=50):
        # Fetch tweets about crypto keywords
        # Parse RSS or use API
        # Return structured data
        pass
```

**2. Reddit Service** (`odin/services/reddit_service.py`)
```python
class RedditService:
    async def fetch_posts(self, subreddits, limit=50):
        # Use Reddit JSON API
        # https://www.reddit.com/r/cryptocurrency/top.json?limit=50
        # No auth required for public posts
        pass
```

**3. News Service** (`odin/services/news_service.py`)
```python
class NewsService:
    def __init__(self):
        self.feeds = {
            'coindesk': 'https://www.coindesk.com/arc/outboundfeeds/rss/',
            'cointelegraph': 'https://cointelegraph.com/rss',
            'decrypt': 'https://decrypt.co/feed'
        }

    async def fetch_articles(self, sources="all", limit=30):
        # Parse RSS feeds
        # Extract title, description, link, pubDate
        # Return structured articles
        pass
```

**4. Sentiment Analyzer** (`odin/services/sentiment_analyzer.py`)
```python
class SentimentAnalyzer:
    def __init__(self):
        # Load crypto-specific sentiment lexicon
        self.positive_words = set(['bullish', 'moon', 'pump', ...])
        self.negative_words = set(['bearish', 'dump', 'crash', ...])

    def analyze(self, text: str) -> dict:
        # Basic keyword-based sentiment
        # Returns: {score: float, label: str, confidence: float}
        pass

    def analyze_batch(self, texts: list) -> list:
        # Analyze multiple texts efficiently
        pass
```

---

## 7. Implementation Phases

### Phase 1: Main Dashboard Bloomberg Layout (4-6 hours)

#### Step 1.1: Create Bloomberg Layout Structure
**File:** `web/templates/dashboard.html`

- [ ] Replace current grid with 3-panel layout
- [ ] Add ticker bar at top
- [ ] Create left panel (markets, watchlist, alerts)
- [ ] Expand main chart area
- [ ] Create right panel (stats, indicators, signals)
- [ ] Add bottom tabbed panel (market depth, liquidations, etc.)

#### Step 1.2: Implement Layout JavaScript
**File:** `web/static/js/bloomberg-layout.js`

- [ ] Create `BloombergLayout` class
- [ ] Implement panel resizing with drag handles
- [ ] Add panel collapse/expand functionality
- [ ] Save panel sizes to localStorage
- [ ] Add keyboard shortcuts (Ctrl+1/2/3 to toggle panels)

#### Step 1.3: Create Ticker Bar
**File:** `web/static/js/ticker-bar.js`

- [ ] Create `LiveTickerBar` class
- [ ] Fetch all 7 coin prices in parallel
- [ ] Display scrolling ticker with price + % change
- [ ] Color code positive (green) / negative (red)
- [ ] Auto-update every 3 seconds
- [ ] Add click to switch coin

#### Step 1.4: Style Bloomberg Theme
**File:** `web/static/css/bloomberg-terminal.css`

- [ ] Define terminal color palette
- [ ] Create panel styles with subtle borders
- [ ] Add monospace font for data
- [ ] Style ticker bar with scroll
- [ ] Create data table styles
- [ ] Add subtle grid lines to charts
- [ ] Implement dark theme with cyan accents

**Deliverables:**
- ✅ 3-panel Bloomberg-style layout
- ✅ Live ticker bar with all coins
- ✅ Resizable panels
- ✅ Professional terminal styling

---

### Phase 2: Enhanced Chart System (3-4 hours)

#### Step 2.1: Improve Main Price Chart
**File:** `web/static/js/analytics-dashboard.js`

- [ ] Add multiple timeframe selector (1h, 4h, 1d, 7d, 30d)
- [ ] Enhance chart with:
  - Volume bars below price
  - Moving averages overlay (MA 20, 50, 200)
  - Bollinger Bands overlay
  - VWAP overlay
- [ ] Add drawing tools (trendlines, support/resistance)
- [ ] Add zoom and pan functionality

#### Step 2.2: Create Advanced Charts
**File:** `web/static/js/charts-advanced.js`

- [ ] Volume Profile chart (horizontal bars at price levels)
- [ ] Order Flow / CVD chart (cumulative volume delta)
- [ ] Enhanced liquidation heatmap (if API available)
- [ ] Funding rate chart with historical data
- [ ] Open Interest chart

#### Step 2.3: Organize Bottom Panel Tabs
**File:** `web/templates/dashboard.html`

- [ ] Create tabbed interface in bottom panel
- [ ] Tabs: Market Depth | Liquidations | Funding | Order Flow | Social
- [ ] Each tab shows relevant chart
- [ ] Social tab shows quick social feed preview

**Deliverables:**
- ✅ Enhanced price chart with indicators
- ✅ Advanced chart types (volume profile, order flow)
- ✅ Organized bottom panel with tabs

---

### Phase 3: Social Intelligence Page (6-8 hours)

#### Step 3.1: Create Social Page Template
**File:** `web/templates/social-intelligence.html`

- [ ] Create new HTML page with header
- [ ] Add filter bar (coins, platforms, timeframe, sentiment)
- [ ] Create sentiment overview section (gauge + breakdown)
- [ ] Add trending topics section
- [ ] Create 4-column feed layout (Twitter | Reddit | News | Top Voices)

#### Step 3.2: Backend - Reddit Integration
**File:** `odin/services/reddit_service.py`

- [ ] Create `RedditService` class
- [ ] Implement `fetch_posts()` using Reddit JSON API
- [ ] Parse subreddit data (r/cryptocurrency, r/bitcoin, etc.)
- [ ] Extract: title, author, score, comments, url, timestamp
- [ ] Handle rate limiting and errors

**File:** `odin/api/routes/social.py`
- [ ] Create `/api/social/reddit` endpoint
- [ ] Return posts with metadata
- [ ] Add pagination support

#### Step 3.3: Backend - News Integration
**File:** `odin/services/news_service.py`

- [ ] Create `NewsService` class
- [ ] Add RSS feed URLs for major crypto news sites
- [ ] Implement `fetch_articles()` to parse RSS feeds
- [ ] Extract: title, description, link, pubDate, source
- [ ] Cache articles in database to avoid re-fetching

**File:** `odin/api/routes/social.py`
- [ ] Create `/api/social/news` endpoint
- [ ] Return articles with sentiment analysis

#### Step 3.4: Backend - Twitter Integration (Optional)
**File:** `odin/services/twitter_service.py`

**Option A: Nitter (Free, easier)**
- [ ] Use Nitter RSS feeds
- [ ] Parse XML/RSS data
- [ ] Extract tweets without API

**Option B: Twitter API (Better, requires key)**
- [ ] Set up Twitter API v2 credentials
- [ ] Implement OAuth flow
- [ ] Fetch timeline by keywords
- [ ] Handle rate limits (450 requests per 15 min)

**File:** `odin/api/routes/social.py`
- [ ] Create `/api/social/twitter` endpoint

#### Step 3.5: Backend - Sentiment Analysis
**File:** `odin/services/sentiment_analyzer.py`

- [ ] Create `SentimentAnalyzer` class
- [ ] Build crypto-specific keyword lexicon:
  - Positive: bullish, moon, pump, breakout, rally, hodl, etc.
  - Negative: bearish, dump, crash, rekt, fud, panic, etc.
- [ ] Implement `analyze(text)` method
- [ ] Calculate sentiment score (-1 to 1)
- [ ] Return label (positive, neutral, negative)

**File:** `odin/api/routes/social.py`
- [ ] Create `/api/social/sentiment` endpoint
- [ ] Aggregate sentiment from all sources
- [ ] Calculate overall score, by platform, by coin

#### Step 3.6: Backend - Trending Topics
**File:** `odin/services/social_aggregator.py`

- [ ] Create `SocialAggregator` class
- [ ] Extract hashtags from Twitter posts
- [ ] Extract keywords from Reddit titles
- [ ] Count mentions over timeframe (24h, 7d)
- [ ] Calculate momentum (rising, falling, stable)
- [ ] Rank top 20 trending topics

**File:** `odin/api/routes/social.py`
- [ ] Create `/api/social/trending` endpoint

#### Step 3.7: Frontend - Social Dashboard JavaScript
**File:** `web/static/js/social-dashboard.js`

- [ ] Create `SocialDashboard` class
- [ ] Implement `loadAllFeeds()` to fetch Twitter, Reddit, News
- [ ] Implement `calculateSentiment()` to aggregate scores
- [ ] Implement `renderFeeds()` for multi-column layout
- [ ] Add real-time updates (every 60 seconds)
- [ ] Add filtering by coin, platform, sentiment
- [ ] Add infinite scroll for feeds

#### Step 3.8: Frontend - Sentiment Visualization
**File:** `web/static/js/charts-advanced.js`

- [ ] Create sentiment gauge chart (speedometer style)
- [ ] Create sentiment trend line chart (24H, 7D, 30D)
- [ ] Create trending topics bar chart
- [ ] Create platform comparison chart

#### Step 3.9: Style Social Intelligence Page
**File:** `web/static/css/social-intelligence.css`

- [ ] Style filter bar
- [ ] Style sentiment overview section
- [ ] Style 4-column feed layout
- [ ] Style individual post cards
- [ ] Add sentiment badge styling
- [ ] Add platform icons
- [ ] Make responsive (collapse columns on mobile)

**Deliverables:**
- ✅ Dedicated social intelligence page at `/dashboard/social`
- ✅ Reddit feed integration
- ✅ News feed aggregation
- ✅ Twitter feed (Nitter or API)
- ✅ Sentiment analysis across all sources
- ✅ Trending topics tracker
- ✅ Multi-column feed layout
- ✅ Sentiment visualization charts

---

### Phase 4: Polish & Optimization (2-3 hours)

#### Step 4.1: Performance Optimization
- [ ] Implement efficient data caching
- [ ] Add loading skeletons for all charts
- [ ] Optimize API calls (batch requests where possible)
- [ ] Add error boundaries and retry logic
- [ ] Lazy load bottom panel charts (only when tab active)

#### Step 4.2: Responsive Design
- [ ] Test on various screen sizes (1920px, 1440px, 1024px, 768px)
- [ ] Adjust panel sizes for smaller screens
- [ ] Make ticker bar scrollable on mobile
- [ ] Stack feed columns on mobile
- [ ] Add touch gestures for panel resizing on tablets

#### Step 4.3: Keyboard Shortcuts
- [ ] Ctrl+1/2/3: Toggle left/right/bottom panels
- [ ] Ctrl+T: Focus ticker bar
- [ ] Ctrl+S: Open social intelligence page
- [ ] Ctrl+R: Refresh all data
- [ ] Escape: Close modals/panels

#### Step 4.4: Notifications System
- [ ] Add price alert notifications
- [ ] Add sentiment shift notifications
- [ ] Add news alert notifications
- [ ] Implement browser notifications (with permission)
- [ ] Show notification count in header

#### Step 4.5: Testing
- [ ] Test all 7 coins on main dashboard
- [ ] Test all API endpoints
- [ ] Test social feeds load correctly
- [ ] Test sentiment analysis accuracy
- [ ] Test responsive layouts
- [ ] Test keyboard shortcuts
- [ ] Test error handling

**Deliverables:**
- ✅ Optimized performance
- ✅ Fully responsive design
- ✅ Keyboard shortcuts
- ✅ Notification system
- ✅ Comprehensive testing

---

## 8. File Changes Summary

### Files to CREATE (New)

**Templates:**
1. `web/templates/social-intelligence.html` - Social media intelligence page

**JavaScript:**
2. `web/static/js/bloomberg-layout.js` - Panel management and resizing
3. `web/static/js/ticker-bar.js` - Live multi-coin ticker
4. `web/static/js/social-dashboard.js` - Social intelligence page logic
5. `web/static/js/sentiment-analyzer.js` - Client-side sentiment analysis
6. `web/static/js/charts-advanced.js` - Advanced chart configurations

**CSS:**
7. `web/static/css/bloomberg-terminal.css` - Main terminal styling
8. `web/static/css/social-intelligence.css` - Social page styling
9. `web/static/css/components.css` - Reusable component styles

**Backend Services:**
10. `odin/services/reddit_service.py` - Reddit API integration
11. `odin/services/news_service.py` - RSS news aggregation
12. `odin/services/twitter_service.py` - Twitter/Nitter integration
13. `odin/services/sentiment_analyzer.py` - Backend sentiment analysis
14. `odin/services/social_aggregator.py` - Social data aggregation

**Backend Routes:**
15. `odin/api/routes/social.py` - Social media API endpoints

### Files to MODIFY (Enhance)

**Templates:**
1. `web/templates/dashboard.html` - Redesign with Bloomberg layout

**JavaScript:**
2. `web/static/js/analytics-dashboard.js` - Add Bloomberg features, enhance charts

**CSS:**
3. `web/static/css/dashboard.css` - Add to existing styles (keep for compatibility)

**Backend:**
4. `odin/api/app.py` - Register new social routes
5. `odin/main.py` - Initialize new services

---

## 9. Estimated Timeline

| Phase | Tasks | Time Estimate |
|-------|-------|---------------|
| **Phase 1** | Bloomberg Layout | 4-6 hours |
| **Phase 2** | Enhanced Charts | 3-4 hours |
| **Phase 3** | Social Intelligence | 6-8 hours |
| **Phase 4** | Polish & Testing | 2-3 hours |
| **TOTAL** | Complete Redesign | **15-21 hours** |

### Breakdown by File Type:
- Frontend (HTML/CSS/JS): ~12 hours
- Backend (Python APIs): ~6 hours
- Testing & Polish: ~3 hours

---

## 10. Success Metrics

### Main Dashboard
✅ Bloomberg-style 3-panel layout implemented
✅ Live ticker showing all 7 coins
✅ Resizable/collapsible panels
✅ Enhanced charts with indicators
✅ Professional terminal styling
✅ Responsive design (desktop + mobile)
✅ All existing features still work

### Social Intelligence Page
✅ Dedicated `/dashboard/social` route
✅ Reddit feed integration
✅ News feed aggregation
✅ Twitter feed (Nitter or API)
✅ Sentiment analysis with visualization
✅ Trending topics tracker
✅ 4-column feed layout
✅ Filtering by coin/platform/sentiment
✅ Real-time updates (60s refresh)

### Performance
✅ Page load < 2 seconds
✅ API response < 500ms
✅ Smooth 60fps animations
✅ No memory leaks (24h test)

---

## 11. Next Steps After Implementation

### Future Enhancements (Post-MVP)
1. **WebSocket Integration** - True real-time updates instead of polling
2. **Advanced Sentiment** - Use ML models (BERT, FinBERT) for better accuracy
3. **Influencer Tracking** - Track specific crypto influencers
4. **Alert System** - Price alerts, sentiment alerts, news alerts
5. **Export/Reporting** - Export charts, generate reports
6. **AI Insights** - GPT-powered analysis of market sentiment
7. **Backtesting** - Test strategies against historical data
8. **Portfolio Tracking** - Track user's crypto portfolio
9. **Trading Integration** - Connect to exchanges for live trading
10. **Mobile App** - React Native app for mobile

---

## Conclusion

This plan provides a comprehensive roadmap to transform the Odin Analytics Dashboard into a professional Bloomberg Terminal-style interface with advanced social media intelligence. The implementation is structured in 4 phases over 15-21 hours of development time, with clear deliverables and success metrics at each stage.

The redesign will provide:
- **Professional Bloomberg aesthetic** with dense information display
- **Enhanced data visualization** with advanced charts and indicators
- **Dedicated social intelligence** for crypto-wide sentiment analysis
- **Multi-source integration** (Twitter, Reddit, news)
- **Real-time updates** and live price ticker
- **Responsive design** that works on all devices

Ready to implement! 🚀
