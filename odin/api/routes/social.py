"""
Social Media Intelligence API Routes
Aggregates data from Twitter/X, Reddit, and crypto news sources
Provides sentiment analysis and trending topics
"""

import asyncio
import hashlib
import re
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional
from email.utils import parsedate_to_datetime

import aiohttp
import feedparser
from fastapi import APIRouter, HTTPException, Query

from odin.utils.cache import cached
from odin.utils.logging import get_logger

logger = get_logger(__name__)
router = APIRouter()


# Crypto-specific sentiment lexicon
POSITIVE_WORDS = {
    'bullish', 'moon', 'pump', 'breakout', 'rally', 'surge', 'soar', 'gain', 'profit',
    'hodl', 'buy', 'accumulate', 'long', 'bullrun', 'ath', 'rocket', 'lambo', 'green',
    'up', 'rise', 'strong', 'support', 'bounce', 'reversal', 'golden', 'cross',
    'momentum', 'volume', 'adoption', 'institutional', 'etf', 'approved', 'launch',
    'partnership', 'innovation', 'upgrade', 'milestone', 'success', 'winning'
}

NEGATIVE_WORDS = {
    'bearish', 'dump', 'crash', 'collapse', 'plunge', 'drop', 'fall', 'loss', 'rekt',
    'fud', 'sell', 'short', 'capitulation', 'death', 'cross', 'red', 'down', 'weak',
    'resistance', 'rejection', 'fear', 'panic', 'scam', 'rug', 'hack', 'exploit',
    'concern', 'worried', 'delay', 'postponed', 'rejected', 'banned', 'regulation',
    'crackdown', 'lawsuit', 'fraud', 'ponzi', 'bubble', 'overvalued'
}


class SentimentAnalyzer:
    """Simple keyword-based sentiment analyzer for crypto content"""

    @staticmethod
    def analyze(text: str) -> Dict[str, Any]:
        """
        Analyze sentiment of text
        Returns: {score: float (-1 to 1), label: str, confidence: float}
        """
        if not text:
            return {'score': 0.0, 'label': 'neutral', 'confidence': 0.0}

        # Normalize text
        text_lower = text.lower()
        words = re.findall(r'\b\w+\b', text_lower)

        if not words:
            return {'score': 0.0, 'label': 'neutral', 'confidence': 0.0}

        # Count positive and negative words
        positive_count = sum(1 for word in words if word in POSITIVE_WORDS)
        negative_count = sum(1 for word in words if word in NEGATIVE_WORDS)

        # Calculate score
        total_sentiment_words = positive_count + negative_count
        if total_sentiment_words == 0:
            return {'score': 0.0, 'label': 'neutral', 'confidence': 0.0}

        # Score from -1 to 1
        score = (positive_count - negative_count) / len(words)

        # Normalize to -1 to 1 range
        score = max(-1.0, min(1.0, score * 10))  # Amplify for better distribution

        # Determine label
        if score > 0.2:
            label = 'positive'
        elif score < -0.2:
            label = 'negative'
        else:
            label = 'neutral'

        # Confidence based on proportion of sentiment words
        confidence = min(1.0, total_sentiment_words / max(10, len(words) * 0.3))

        return {
            'score': round(score, 3),
            'label': label,
            'confidence': round(confidence, 3),
            'positive_words': positive_count,
            'negative_words': negative_count
        }


@router.get("/api/social/reddit")
@cached(ttl=300)  # Cache for 5 minutes
async def get_reddit_feed(
    subreddits: str = Query("cryptocurrency,bitcoin,ethtrader", description="Comma-separated subreddits"),
    limit: int = Query(50, ge=1, le=100, description="Number of posts to fetch")
):
    """
    Fetch Reddit posts from crypto subreddits
    Uses Reddit JSON API (no auth required for public posts)
    """
    try:
        subreddit_list = [s.strip() for s in subreddits.split(',')]
        all_posts = []

        async with aiohttp.ClientSession() as session:
            for subreddit in subreddit_list:
                try:
                    url = f"https://www.reddit.com/r/{subreddit}/hot.json?limit={limit}"
                    headers = {'User-Agent': 'ODIN Terminal/1.0'}

                    async with session.get(url, headers=headers, timeout=10) as response:
                        if response.status == 200:
                            data = await response.json()
                            posts = data.get('data', {}).get('children', [])

                            for post in posts[:limit]:
                                post_data = post.get('data', {})

                                # Combine title and selftext for sentiment analysis
                                full_text = f"{post_data.get('title', '')} {post_data.get('selftext', '')}"
                                sentiment = SentimentAnalyzer.analyze(full_text)

                                all_posts.append({
                                    'id': post_data.get('id'),
                                    'subreddit': subreddit,
                                    'title': post_data.get('title'),
                                    'author': post_data.get('author'),
                                    'score': post_data.get('score', 0),
                                    'num_comments': post_data.get('num_comments', 0),
                                    'created_utc': post_data.get('created_utc'),
                                    'url': f"https://reddit.com{post_data.get('permalink', '')}",
                                    'selftext': post_data.get('selftext', '')[:200],  # Limit text length
                                    'sentiment': sentiment,
                                    'platform': 'reddit'
                                })
                        else:
                            logger.warning(f"Reddit API returned status {response.status} for r/{subreddit}")

                except asyncio.TimeoutError:
                    logger.warning(f"Timeout fetching r/{subreddit}")
                except Exception as e:
                    logger.error(f"Error fetching r/{subreddit}: {e}")

        # Sort by score (popularity)
        all_posts.sort(key=lambda x: x['score'], reverse=True)

        return {
            'success': True,
            'data': all_posts[:limit],
            'count': len(all_posts),
            'subreddits': subreddit_list,
            'timestamp': datetime.utcnow().isoformat()
        }

    except Exception as e:
        logger.error(f"Error in get_reddit_feed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/api/social/news")
@cached(ttl=600)  # Cache for 10 minutes
async def get_news_feed(
    sources: str = Query("all", description="News sources: all, coindesk, cointelegraph, decrypt"),
    limit: int = Query(30, ge=1, le=100, description="Number of articles to fetch")
):
    """
    Fetch crypto news from RSS feeds
    Sources: CoinDesk, CoinTelegraph, Decrypt
    """
    try:
        # RSS feed URLs
        feed_urls = {
            'coindesk': 'https://www.coindesk.com/arc/outboundfeeds/rss/',
            'cointelegraph': 'https://cointelegraph.com/rss',
            'decrypt': 'https://decrypt.co/feed'
        }

        # Determine which sources to fetch
        if sources == 'all':
            sources_to_fetch = list(feed_urls.keys())
        else:
            sources_to_fetch = [s.strip() for s in sources.split(',') if s.strip() in feed_urls]

        all_articles = []

        async with aiohttp.ClientSession() as session:
            for source in sources_to_fetch:
                try:
                    url = feed_urls[source]
                    headers = {'User-Agent': 'ODIN Terminal/1.0'}

                    async with session.get(url, headers=headers, timeout=15) as response:
                        if response.status == 200:
                            # Parse RSS feed
                            content = await response.text()
                            feed = feedparser.parse(content)

                            # Extract articles from feed
                            for entry in feed.entries[:10]:  # Limit to 10 per source
                                # Extract publication date
                                pub_date = None
                                if hasattr(entry, 'published_parsed') and entry.published_parsed:
                                    try:
                                        pub_date = datetime(*entry.published_parsed[:6]).isoformat()
                                    except:
                                        pass

                                if not pub_date and hasattr(entry, 'published'):
                                    try:
                                        pub_date = parsedate_to_datetime(entry.published).isoformat()
                                    except:
                                        pass

                                if not pub_date:
                                    pub_date = datetime.utcnow().isoformat()

                                # Extract description
                                description = ""
                                if hasattr(entry, 'summary'):
                                    description = entry.summary[:300]  # Limit length
                                elif hasattr(entry, 'description'):
                                    description = entry.description[:300]

                                # Remove HTML tags from description
                                description = re.sub(r'<[^>]+>', '', description)

                                # Analyze sentiment
                                sentiment_text = f"{entry.title} {description}"
                                sentiment = SentimentAnalyzer.analyze(sentiment_text)

                                article = {
                                    'id': hashlib.md5(f"{source}-{entry.link}".encode()).hexdigest()[:16],
                                    'source': source,
                                    'title': entry.title,
                                    'description': description.strip(),
                                    'url': entry.link,
                                    'published_at': pub_date,
                                    'sentiment': sentiment,
                                    'platform': 'news'
                                }
                                all_articles.append(article)

                except asyncio.TimeoutError:
                    logger.warning(f"Timeout fetching {source}")
                except Exception as e:
                    logger.error(f"Error fetching {source}: {e}")

        # Sort by published date
        all_articles.sort(key=lambda x: x['published_at'], reverse=True)

        return {
            'success': True,
            'data': all_articles[:limit],
            'count': len(all_articles),
            'sources': sources_to_fetch,
            'timestamp': datetime.utcnow().isoformat(),
            'note': 'Full RSS parsing will be implemented with feedparser library'
        }

    except Exception as e:
        logger.error(f"Error in get_news_feed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/api/social/sentiment")
@cached(ttl=300)  # Cache for 5 minutes
async def get_sentiment_overview(
    coins: str = Query("all", description="Coins to analyze: all, BTC, ETH, etc."),
    timeframe: str = Query("24h", description="Timeframe: 1h, 24h, 7d")
):
    """
    Get aggregated sentiment across all social sources
    """
    try:
        # Fetch data from Reddit and News
        reddit_task = get_reddit_feed()
        news_task = get_news_feed()

        reddit_data, news_data = await asyncio.gather(reddit_task, news_task, return_exceptions=True)

        # Calculate overall sentiment
        all_sentiments = []
        platform_sentiments = {'reddit': [], 'news': [], 'twitter': []}

        # Process Reddit sentiments
        if isinstance(reddit_data, dict) and reddit_data.get('success'):
            for post in reddit_data.get('data', []):
                score = post.get('sentiment', {}).get('score', 0)
                all_sentiments.append(score)
                platform_sentiments['reddit'].append(score)

        # Process News sentiments
        if isinstance(news_data, dict) and news_data.get('success'):
            for article in news_data.get('data', []):
                score = article.get('sentiment', {}).get('score', 0)
                all_sentiments.append(score)
                platform_sentiments['news'].append(score)

        # Calculate averages
        def calculate_sentiment_percentage(scores):
            """Convert -1 to 1 score to 0-100 percentage"""
            if not scores:
                return 50  # Neutral
            avg_score = sum(scores) / len(scores)
            # Map -1 to 1 range to 0 to 100
            return int((avg_score + 1) * 50)

        overall_score = calculate_sentiment_percentage(all_sentiments)

        platform_scores = {
            platform: calculate_sentiment_percentage(scores)
            for platform, scores in platform_sentiments.items()
        }

        # Determine trend
        if overall_score > 60:
            trend = 'rising'
        elif overall_score < 40:
            trend = 'falling'
        else:
            trend = 'stable'

        # Determine label
        if overall_score > 65:
            label = 'positive'
            emoji = '🟢'
        elif overall_score < 35:
            label = 'negative'
            emoji = '🔴'
        else:
            label = 'neutral'
            emoji = '🟡'

        return {
            'success': True,
            'data': {
                'overall_score': overall_score,
                'overall_label': label,
                'overall_emoji': emoji,
                'by_platform': platform_scores,
                'trend': trend,
                'sample_size': len(all_sentiments),
                'timeframe': timeframe,
                'coins': coins
            },
            'timestamp': datetime.utcnow().isoformat()
        }

    except Exception as e:
        logger.error(f"Error in get_sentiment_overview: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/api/social/trending")
@cached(ttl=300)  # Cache for 5 minutes
async def get_trending_topics(
    timeframe: str = Query("24h", description="Timeframe: 1h, 24h, 7d"),
    limit: int = Query(20, ge=1, le=50, description="Number of topics to return")
):
    """
    Get trending hashtags and topics across crypto social media
    """
    try:
        # Fetch Reddit data to extract topics
        reddit_data = await get_reddit_feed()

        # Extract hashtags and keywords
        topic_counts = {}

        if isinstance(reddit_data, dict) and reddit_data.get('success'):
            for post in reddit_data.get('data', []):
                title = post.get('title', '').lower()

                # Extract hashtags (words starting with #)
                hashtags = re.findall(r'#(\w+)', title)

                # Extract common crypto keywords
                keywords = ['bitcoin', 'btc', 'ethereum', 'eth', 'crypto', 'defi',
                           'nft', 'altcoin', 'bullish', 'bearish', 'hodl', 'etf',
                           'regulation', 'sec', 'mining', 'staking', 'web3']

                # Count hashtags
                for tag in hashtags:
                    topic = f"#{tag}"
                    topic_counts[topic] = topic_counts.get(topic, 0) + 1

                # Count keywords
                for keyword in keywords:
                    if keyword in title:
                        topic = f"#{keyword}"
                        topic_counts[topic] = topic_counts.get(topic, 0) + 1

        # Sort by count
        trending = sorted(topic_counts.items(), key=lambda x: x[1], reverse=True)

        # Format results
        trending_topics = []
        for i, (topic, count) in enumerate(trending[:limit]):
            # Determine momentum
            if i < 5:
                momentum = 'hot'
                emoji = '🔥'
            elif i < 10:
                momentum = 'rising'
                emoji = '📈'
            else:
                momentum = 'stable'
                emoji = '💬'

            trending_topics.append({
                'topic': topic,
                'mentions': count,
                'momentum': momentum,
                'emoji': emoji,
                'rank': i + 1
            })

        return {
            'success': True,
            'data': trending_topics,
            'count': len(trending_topics),
            'timeframe': timeframe,
            'timestamp': datetime.utcnow().isoformat()
        }

    except Exception as e:
        logger.error(f"Error in get_trending_topics: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/api/social/twitter")
@cached(ttl=300)  # Cache for 5 minutes
async def get_twitter_feed(
    keywords: str = Query("bitcoin,crypto,btc", description="Keywords to search"),
    limit: int = Query(50, ge=1, le=100, description="Number of tweets to fetch")
):
    """
    Fetch Twitter/X feed about crypto
    NOTE: This is a placeholder. Real implementation would require:
    - Twitter API v2 credentials
    - OAuth authentication
    - Rate limit handling

    For now, returns simulated data based on current trends
    """
    try:
        # Placeholder Twitter data
        # In production, this would use Twitter API v2

        simulated_tweets = [
            {
                'id': f'tweet-{i}',
                'author': {
                    'username': f'cryptotrader{i}',
                    'name': f'Crypto Trader {i}',
                    'followers': 10000 + (i * 1000),
                    'verified': i < 5
                },
                'text': "Bitcoin breaking new resistance levels! #BTC #Crypto #Bullish",
                'created_at': (datetime.utcnow() - timedelta(hours=i)).isoformat(),
                'metrics': {
                    'likes': 100 + (i * 10),
                    'retweets': 50 + (i * 5),
                    'replies': 20 + (i * 2)
                },
                'sentiment': SentimentAnalyzer.analyze("Bitcoin breaking new resistance levels! Bullish"),
                'platform': 'twitter'
            }
            for i in range(min(limit, 20))
        ]

        return {
            'success': True,
            'data': simulated_tweets,
            'count': len(simulated_tweets),
            'keywords': keywords.split(','),
            'timestamp': datetime.utcnow().isoformat(),
            'note': 'Twitter API integration requires API credentials. This is simulated data.'
        }

    except Exception as e:
        logger.error(f"Error in get_twitter_feed: {e}")
        raise HTTPException(status_code=500, detail=str(e))
