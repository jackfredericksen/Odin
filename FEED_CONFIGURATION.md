# Social Feed Configuration Guide ⚙️

## Overview

The ODIN Terminal now includes a **manual configuration system** for all social media and news feeds! You can customize which news sources, subreddits, and keywords to track, and control auto-refresh settings.

---

## Features

### ✅ Customizable News Sources
- Choose which news outlets to follow:
  - **CoinDesk** - Major crypto news and market updates
  - **Decrypt** - Web3 and crypto tech news
  - **CoinTelegraph** - Blockchain and cryptocurrency news
- Select one, two, or all three sources
- Changes apply immediately when saved

### ✅ Custom Subreddit Tracking
- Track any subreddits you want
- Default: `cryptocurrency, bitcoin, ethtrader`
- Examples of popular crypto subreddits:
  - `CryptoCurrency` - General crypto discussions
  - `Bitcoin` - Bitcoin-specific news and discussions
  - `ethereum` or `ethtrader` - Ethereum community
  - `solana` - Solana ecosystem
  - `CryptoMoonShots` - Small cap gems
  - `cryptocurrency`, `defi`, `nfts`, `web3` - Various topics

### ✅ Twitter Keywords Configuration
- Customize keywords for Twitter feed tracking
- Default: `bitcoin, crypto, btc, ethereum`
- Examples:
  - Coins: `btc, eth, sol, xrp, ada`
  - Topics: `defi, nft, web3, blockchain`
  - Hashtags: `#bitcoin, #ethereum, #crypto`

### ✅ Auto-Refresh Control
- Enable/disable automatic feed refreshing
- Configurable refresh interval (30-300 seconds)
- Default: 60 seconds
- Stops auto-refresh when disabled to save bandwidth

### ✅ Persistent Settings
- All settings saved to browser localStorage
- Settings persist across sessions
- Each browser/device has independent settings

---

## How to Use

### Accessing Settings

1. Navigate to the **🌐 Social Intelligence** section (Alt+3)
2. Click the **⚙️ Settings** button in the top-right corner
3. The settings modal will appear

### Configuring News Sources

1. In the settings modal, find the **📰 News Sources** section
2. Check/uncheck the news outlets you want to follow:
   - ☑️ CoinDesk
   - ☑️ Decrypt
   - ☑️ CoinTelegraph
3. At least one source must be selected
4. Click **"Apply & Reload"** to save

### Configuring Subreddits

1. Find the **📱 Subreddits** section
2. Enter a comma-separated list of subreddit names
   - Example: `cryptocurrency, bitcoin, ethtrader, solana`
3. **Do not** include "r/" prefix - just the subreddit name
4. Click **"Apply & Reload"** to save

**Tips:**
- Use lowercase for subreddit names
- Separate with commas
- Spaces after commas are optional (automatically trimmed)
- Invalid subreddits will simply not load data

### Configuring Twitter Keywords

1. Find the **🐦 Twitter Keywords** section
2. Enter a comma-separated list of keywords or hashtags
   - Example: `bitcoin, ethereum, btc, eth, #crypto`
3. Click **"Apply & Reload"** to save

**Note:** Twitter feed currently uses simulated data. Real Twitter integration requires API credentials.

### Auto-Refresh Settings

1. Find the **🔄 Auto-refresh feeds** section
2. Check the box to enable auto-refresh
3. When enabled, set the refresh interval (in seconds)
   - Minimum: 30 seconds
   - Maximum: 300 seconds (5 minutes)
   - Recommended: 60 seconds
4. Click **"Apply & Reload"** to save

**Benefits of Auto-Refresh:**
- Always see the latest posts and news
- No need to manually click refresh
- Configurable to balance freshness vs. bandwidth

### Resetting to Defaults

1. Click the **"Reset to Defaults"** button
2. Confirm the reset
3. Settings will revert to:
   - News: All 3 sources (CoinDesk, Decrypt, CoinTelegraph)
   - Subreddits: `cryptocurrency, bitcoin, ethtrader`
   - Twitter: `bitcoin, crypto, btc, ethereum`
   - Auto-refresh: Enabled (60 seconds)

---

## Technical Details

### Data Storage

**LocalStorage Key:** `odin-social-settings`

**Storage Format:**
```json
{
  "newsSources": ["coindesk", "decrypt", "cointelegraph"],
  "subreddits": ["cryptocurrency", "bitcoin", "ethtrader"],
  "twitterKeywords": ["bitcoin", "crypto", "btc", "ethereum"],
  "autoRefresh": true,
  "refreshInterval": 60
}
```

**Storage Location:**
- Browser localStorage (per-domain)
- Settings persist even after closing browser
- Each device/browser has independent settings
- Clearing browser data will reset settings

### API Integration

**News Feed:**
```javascript
GET /api/social/news?sources=coindesk,decrypt,cointelegraph
```

**Reddit Feed:**
```javascript
GET /api/social/reddit?subreddits=cryptocurrency,bitcoin,ethtrader
```

**Twitter Feed:**
```javascript
GET /api/social/twitter?keywords=bitcoin,crypto,btc,ethereum
```

### Refresh Behavior

**When settings are applied:**
1. Settings saved to localStorage
2. Auto-refresh timer restarted (if enabled)
3. All feeds immediately reloaded with new parameters
4. Modal closes automatically
5. Console logs confirmation

**Console Output:**
```
💾 Settings saved: {newsSources: Array(3), subreddits: Array(3), ...}
⏹️ Social Intelligence auto-update stopped
🔄 Social Intelligence auto-update started (60s interval)
📥 Loading social intelligence data...
✅ Settings applied and feeds reloaded
```

---

## Examples

### Example 1: Track Only Bitcoin Communities

**Configuration:**
- News Sources: CoinDesk only
- Subreddits: `bitcoin, bitcoinbeginners`
- Twitter Keywords: `btc, bitcoin, #bitcoin`
- Auto-refresh: Enabled, 120 seconds

**Result:** Focused feed showing only Bitcoin-related content from CoinDesk, Bitcoin subreddits, and Bitcoin tweets.

### Example 2: DeFi-Focused Setup

**Configuration:**
- News Sources: Decrypt, CoinTelegraph
- Subreddits: `defi, ethereum, Uniswap, aave`
- Twitter Keywords: `defi, #DeFi, ethereum, uniswap, aave`
- Auto-refresh: Enabled, 90 seconds

**Result:** DeFi-centric news and discussions from relevant sources.

### Example 3: Minimal Bandwidth Usage

**Configuration:**
- News Sources: CoinDesk only
- Subreddits: `cryptocurrency`
- Twitter Keywords: `bitcoin`
- Auto-refresh: Disabled

**Result:** Single news source, one subreddit, manual refresh only - minimal data usage.

### Example 4: Maximum Coverage

**Configuration:**
- News Sources: All 3 (CoinDesk, Decrypt, CoinTelegraph)
- Subreddits: `cryptocurrency, bitcoin, ethereum, solana, defi, nfts`
- Twitter Keywords: `bitcoin, ethereum, crypto, blockchain, defi, nft, web3`
- Auto-refresh: Enabled, 30 seconds

**Result:** Comprehensive coverage with maximum freshness (high bandwidth usage).

---

##FAQ

### Q: Why don't I see my custom subreddits?

**A:** Check these common issues:
- Subreddit name spelled correctly?
- Subreddit exists and is public?
- No "r/" prefix in the name
- Separated by commas

### Q: How long does it take for settings to apply?

**A:** Settings apply immediately when you click "Apply & Reload". The feeds will reload with new parameters within 1-2 seconds.

### Q: Can I add custom news sources?

**A:** Currently limited to CoinDesk, Decrypt, and CoinTelegraph. Custom RSS feeds require backend updates.

### Q: Will my settings sync across devices?

**A:** No, settings are stored in browser localStorage and are device/browser-specific. You'll need to configure each device separately.

### Q: What happens if I disable auto-refresh?

**A:** The automatic timer stops, but you can still manually refresh feeds by clicking the 🔄 button in the Sentiment Overview panel.

### Q: Can I track non-crypto subreddits?

**A:** Technically yes, but the sentiment analysis is optimized for crypto keywords. Non-crypto content may show as "neutral" sentiment.

### Q: How do I see my current settings?

**A:** Click the ⚙️ Settings button - the modal will show all current values. You can also check localStorage in browser DevTools.

### Q: What if I enter invalid data?

**A:** Invalid subreddits won't load data (will show "No posts found"). Invalid refresh intervals are constrained to 30-300 seconds automatically.

---

## Keyboard Shortcuts

| Shortcut | Action |
|----------|--------|
| `Alt+3` | Navigate to Social Intelligence section |
| Click ⚙️ | Open settings modal |
| Click ✕ | Close settings modal |
| Click 🔄 | Manually refresh all feeds |

---

## Privacy & Security

**Data Stored Locally:**
- News source preferences
- Subreddit list
- Twitter keywords
- Auto-refresh settings

**NOT Stored:**
- No personal information
- No API keys or tokens
- No feed content (content is fetched fresh each time)
- No tracking or analytics

**Data Security:**
- All settings stored in browser localStorage
- Settings never leave your device
- API requests use configured parameters but don't expose settings
- Clearing browser data removes all settings

---

## Troubleshooting

### Settings Not Saving

1. Check browser allows localStorage
2. Ensure you clicked "Apply & Reload" (not just close)
3. Check browser console for errors (F12)
4. Try clearing site data and reconfiguring

### Feeds Not Loading

1. Check internet connection
2. Verify subreddit names are valid
3. Check browser console for API errors
4. Try refreshing the page (Ctrl+R)

### Auto-Refresh Not Working

1. Verify auto-refresh is enabled in settings
2. Check refresh interval is valid (30-300 seconds)
3. Look for console logs showing refresh activity
4. Try disabling and re-enabling

### Settings Reset After Page Reload

1. Ensure localStorage is enabled in browser
2. Check if browser is in private/incognito mode
3. Verify site permissions allow storage
4. Try a different browser to test

---

## Future Enhancements

Planned features for future releases:

- [ ] Custom RSS feed URLs
- [ ] Import/export settings as JSON
- [ ] Settings presets (Bitcoin-focused, DeFi-focused, etc.)
- [ ] Per-feed refresh intervals
- [ ] Notification settings
- [ ] Feed prioritization
- [ ] Dark mode per-feed
- [ ] Feed search and filtering

---

## Server Information

**Settings Feature Version:** 5.0.0
**Server Running:** http://localhost:8000
**Settings File:** `web/static/js/social-intelligence-v2.js`

**API Endpoints:**
- `GET /api/social/news?sources=...`
- `GET /api/social/reddit?subreddits=...`
- `GET /api/social/twitter?keywords=...`
- `GET /api/social/sentiment`
- `GET /api/social/trending`

---

## Getting Started

**Quick Start:**
1. Open ODIN Terminal: http://localhost:8000
2. Press `Alt+3` to go to Social Intelligence
3. Click ⚙️ Settings
4. Customize your preferences
5. Click **"Apply & Reload"**
6. Enjoy your personalized feed!

**Happy trading! 🚀**
