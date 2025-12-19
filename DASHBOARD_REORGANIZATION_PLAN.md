# Dashboard Reorganization Plan

## New Information Architecture

Based on user feedback, reorganizing dashboard into 4 clear conceptual sections:

### 1. **Price & Market Data** 📊
**Purpose:** Real-time pricing, volume, market cap, liquidity

**Contains:**
- Live ticker (all 7 coins)
- Current price display (large, prominent)
- 24H High/Low/Volume/Market Cap
- Order book depth
- Market depth visualization
- Bid/Ask spread
- Trading volume breakdown
- Circulating supply
- Price alerts panel

**Layout:** Dense data tables + key metrics cards

---

### 2. **Charts & Analytics** 📈
**Purpose:** Technical analysis, indicators, patterns

**Contains:**
- Main price chart (with timeframes: 1H, 4H, 1D, 7D, 30D)
- Technical indicators panel:
  - RSI with signal
  - MACD with histogram
  - Bollinger Bands
  - Moving Averages (20, 50, 200)
  - VWAP
- Support & Resistance levels
- Fibonacci retracement levels
- Pattern recognition
- Volume profile chart
- Liquidation heatmap
- Funding rate chart
- Open Interest chart
- Correlation matrix (multi-coin)
- Multi-timeframe analysis

**Layout:** Large chart area with indicator panels

---

### 3. **Social Intelligence** 🌐
**Purpose:** Sentiment analysis, news, community feeds

**Contains:**
- **Sentiment Overview:**
  - Overall sentiment gauge (0-100)
  - Sentiment by platform (Twitter, Reddit, News)
  - Sentiment by coin
  - Sentiment trend chart (24H, 7D)

- **Twitter/X Feed:**
  - Crypto Twitter timeline
  - Top influencers
  - Trending hashtags
  - Sentiment-tagged tweets

- **Reddit Feed:**
  - r/cryptocurrency, r/bitcoin, r/ethtrader posts
  - Top discussions
  - Sentiment analysis

- **News Aggregator:**
  - CoinDesk, CoinTelegraph, Decrypt
  - Sentiment-scored articles
  - Breaking news alerts

- **Trending Topics:**
  - Top 20 hashtags/topics
  - Mention volume
  - Momentum indicators (🔥 hot, 📈 rising, 📉 falling)

**Layout:** Multi-column feed with sentiment visualization

---

### 4. **Trading Journal** 📝
**Purpose:** Trade tracking, notes, X posting integration

**Contains:**
- **Trade Log:**
  - Entry/exit prices
  - Position size
  - P&L tracking
  - Trade notes
  - Screenshot attachments

- **X (Twitter) Integration:**
  - Quick post to X
  - Share trade screenshots
  - Post charts
  - Auto-tag trades

- **Performance Analytics:**
  - Win rate
  - Average P&L
  - Best/worst trades
  - Performance chart

- **Trade Ideas:**
  - Watchlist
  - Trade setups
  - Risk/reward calculations

- **Journal Notes:**
  - Daily market notes
  - Lessons learned
  - Strategy refinements

**Layout:** Form-based with list view of past trades

---

## Navigation Structure

### Top Bar (Always Visible)
```
┌─────────────────────────────────────────────────────────────┐
│ [ODIN TERMINAL] 🟢 LIVE  |  ₿ $98,234 +2.3%  | 🔔 ⚙️ 12:34 │
├─────────────────────────────────────────────────────────────┤
│ [📊 Price & Market] [📈 Charts & Analytics]                 │
│ [🌐 Social Intelligence] [📝 Trading Journal]               │
└─────────────────────────────────────────────────────────────┘
```

### Section Tabs
- Large, clear tabs
- Active tab highlighted
- Icon + text labels
- Keyboard shortcuts (Alt+1, Alt+2, Alt+3, Alt+4)

---

## Implementation Changes

### Files to Modify

1. **`dashboard-bloomberg.html`**
   - Remove 3-panel layout
   - Add tabbed section navigation
   - Create 4 distinct section views
   - Each section has its own layout optimized for its content type

2. **`bloomberg-terminal.css`**
   - Add tab navigation styles
   - Create section-specific layouts
   - Keep terminal aesthetic throughout

3. **New Files to Create:**
   - `web/static/js/section-manager.js` - Handle tab switching and section loading
   - `web/static/js/social-feed.js` - Social intelligence functionality
   - `web/static/js/trading-journal.js` - Journal and X integration

### API Endpoints Needed

**Already exist (from data.py):**
- ✅ `/api/data/price?symbol={coin}`
- ✅ `/api/data/indicators?symbol={coin}`
- ✅ `/api/data/history/{hours}?symbol={coin}`
- ✅ `/api/data/depth?symbol={coin}`

**Need to create:**
- `/api/social/twitter` - Twitter feed
- `/api/social/reddit` - Reddit posts
- `/api/social/news` - News articles
- `/api/social/sentiment` - Sentiment scores
- `/api/social/trending` - Trending topics
- `/api/journal/trades` - CRUD for trades
- `/api/journal/notes` - CRUD for notes
- `/api/journal/post-to-x` - Post to Twitter/X

---

## Section Layouts

### 1. Price & Market Data Layout
```
┌─────────────────────────────────────────────────────────────┐
│                    CURRENT PRICE                             │
│              $98,234.56  ▲ +2,345 (+2.45%)                  │
├──────────────────┬──────────────────┬──────────────────────┤
│  24H HIGH        │  24H LOW         │  24H VOLUME          │
│  $99,123.45      │  $96,789.12      │  45.2B USDT         │
├──────────────────┴──────────────────┴──────────────────────┤
│                    ORDER BOOK DEPTH                          │
│  [Bids visualization]    [Current]    [Asks visualization] │
├──────────────────────────────────────────────────────────────┤
│  MARKET STATS TABLE                    │  PRICE ALERTS      │
│  Market Cap:      $1.85T               │  Alert @$100K ✓   │
│  Circulating:     19.7M BTC            │  Alert @$95K      │
│  Total Supply:    21M BTC              │  [Add Alert +]    │
│  Dominance:       48.2%                │                    │
└──────────────────────────────────────────────────────────────┘
```

### 2. Charts & Analytics Layout
```
┌─────────────────────────────────────────────────────────────┐
│  MAIN CHART  [1H] [4H] [24H] [7D] [30D]                     │
│                                                               │
│  [Large price chart with indicators overlay]                 │
│  Volume bars below                                           │
│                                                               │
├───────────────────┬──────────────────────────────────────────┤
│  INDICATORS       │  SUPPORT & RESISTANCE                    │
│  RSI: 65 (BUY)    │  R3: $101,234                           │
│  MACD: Bullish    │  R2: $99,876                            │
│  BB: Middle       │  R1: $98,543                            │
│                   │  Current: $98,234                        │
│  PATTERNS         │  S1: $96,789                            │
│  Bull Flag        │  S2: $95,432                            │
│  Higher Lows      │  S3: $94,123                            │
└───────────────────┴──────────────────────────────────────────┘
```

### 3. Social Intelligence Layout
```
┌─────────────────────────────────────────────────────────────┐
│  SENTIMENT OVERVIEW                                          │
│  Overall: 72% 🟢  [Gauge visualization]                     │
│  Twitter: 68% 🟡  Reddit: 76% 🟢  News: 65% 🟡            │
├────────────────┬────────────────┬────────────────┬──────────┤
│  TWITTER       │  REDDIT        │  NEWS          │ TRENDING │
│                │                │                │          │
│  @whale        │  r/crypto      │  CoinDesk:     │ #Bitcoin │
│  "BTC to       │  "ETH staking  │  "BTC ETF..."  │ 15.2K    │
│   $100K soon"  │   guide..."    │  😊 Positive   │          │
│  😊 Positive   │  😊 Positive   │                │ #ETF     │
│  👍 2.4K       │  ⬆ 1.2K       │  Decrypt:      │ 12.8K    │
│                │                │  "Ethereum..." │          │
│  @trader       │  r/bitcoin     │  😐 Neutral    │ #DeFi    │
│  "Dump soon"   │  "Fear index"  │                │ 8.4K     │
│  😞 Negative   │  😐 Neutral    │                │          │
└────────────────┴────────────────┴────────────────┴──────────┘
```

### 4. Trading Journal Layout
```
┌─────────────────────────────────────────────────────────────┐
│  NEW TRADE ENTRY                          [Post to X ✓]     │
│  Symbol: [BTC▼]  Side: [⚪Long ⚪Short]                     │
│  Entry: [$98,234] Exit: [$102,000] Size: [0.5 BTC]         │
│  Notes: [Breakout from bull flag pattern...]               │
│  [Attach Screenshot] [Save Trade]                           │
├─────────────────────────────────────────────────────────────┤
│  RECENT TRADES                         │  PERFORMANCE       │
│  Dec 18 - BTC Long  +$2,345  🟢       │  Win Rate: 65%     │
│  Dec 17 - ETH Short -$432    🔴       │  Avg P&L: +$1,234  │
│  Dec 16 - SOL Long  +$1,876  🟢       │  Best: +$5,678     │
│  Dec 15 - BTC Long  +$987    🟢       │  Worst: -$1,234    │
│                                        │  [Performance 📊]  │
└─────────────────────────────────────────────────────────────┘
```

---

## Benefits of This Organization

### ✅ Improved User Experience
- **Clear mental model**: Each section has a specific purpose
- **Reduced cognitive load**: Related information grouped together
- **Faster navigation**: Tab-based switching between contexts
- **Less clutter**: Each section optimized for its content type

### ✅ Better Performance
- **Lazy loading**: Only load active section's data
- **Reduced API calls**: Don't fetch unused data
- **Faster initial load**: Load Price & Market first, others on demand

### ✅ Scalability
- **Easy to extend**: Add new sections without affecting others
- **Independent updates**: Each section can evolve separately
- **Modular codebase**: Clean separation of concerns

---

## Implementation Timeline

### Step 1: Create Section Navigation (30 min)
- Tab-based navigation component
- Section routing/switching
- Active state management
- Keyboard shortcuts

### Step 2: Reorganize Price & Market Section (45 min)
- Move order book, market stats, price display
- Create dense data layout
- Add price alerts panel

### Step 3: Reorganize Charts & Analytics Section (1 hour)
- Keep existing chart functionality
- Add indicators panel
- Organize S/R levels, patterns

### Step 4: Create Social Intelligence Section (3-4 hours)
- Build sentiment overview
- Create multi-column feed layout
- Implement sentiment visualization
- Add trending topics panel

### Step 5: Create Trading Journal Section (2-3 hours)
- Trade entry form
- Trade list view
- Performance analytics
- X integration (post functionality)

### Step 6: Fix 404 Errors & Polish (1 hour)
- Ensure all API endpoints work
- Add error handling
- Loading states
- Final testing

**Total Time:** ~8-10 hours

---

## Next Steps

1. **Create section navigation HTML/CSS**
2. **Reorganize existing content into sections**
3. **Build Social Intelligence section**
4. **Build Trading Journal section**
5. **Fix all 404 errors**
6. **Polish and test**

Ready to proceed? 🚀
