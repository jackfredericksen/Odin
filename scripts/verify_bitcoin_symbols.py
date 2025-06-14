#!/usr/bin/env python3
"""
Bitcoin Symbol and API Verification Script
Tests all available APIs and symbols to find working ones
"""

import requests
import json
from datetime import datetime, timedelta

def test_coingecko_api():
    """Test CoinGecko API"""
    print("🔍 Testing CoinGecko API...")
    
    try:
        # Test current price
        url = "https://api.coingecko.com/api/v3/simple/price"
        params = {'ids': 'bitcoin', 'vs_currencies': 'usd'}
        
        response = requests.get(url, params=params, timeout=10)
        print(f"   Status Code: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            price = data.get('bitcoin', {}).get('usd')
            print(f"   ✅ Current Bitcoin price: ${price:,.2f}")
            
            # Test historical data
            hist_url = "https://api.coingecko.com/api/v3/coins/bitcoin/market_chart"
            hist_params = {'vs_currency': 'usd', 'days': '7', 'interval': 'daily'}
            
            hist_response = requests.get(hist_url, params=hist_params, timeout=10)
            if hist_response.status_code == 200:
                hist_data = hist_response.json()
                prices = hist_data.get('prices', [])
                print(f"   ✅ Historical data: {len(prices)} data points")
                return True, "coingecko", price
            else:
                print(f"   ❌ Historical data failed: {hist_response.status_code}")
        else:
            print(f"   ❌ Failed: {response.text[:100]}")
            
    except Exception as e:
        print(f"   ❌ Exception: {e}")
    
    return False, None, None

def test_coindesk_api():
    """Test CoinDesk API"""
    print("🔍 Testing CoinDesk API...")
    
    try:
        # Test current price
        url = "https://api.coindesk.com/v1/bpi/currentprice/USD.json"
        
        response = requests.get(url, timeout=10)
        print(f"   Status Code: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            price = data['bpi']['USD']['rate_float']
            print(f"   ✅ Current Bitcoin price: ${price:,.2f}")
            
            # Test historical data
            end_date = datetime.now()
            start_date = end_date - timedelta(days=7)
            
            hist_url = "https://api.coindesk.com/v1/bpi/historical/close.json"
            hist_params = {
                'start': start_date.strftime('%Y-%m-%d'),
                'end': end_date.strftime('%Y-%m-%d')
            }
            
            hist_response = requests.get(hist_url, params=hist_params, timeout=10)
            if hist_response.status_code == 200:
                hist_data = hist_response.json()
                bpi_data = hist_data.get('bpi', {})
                print(f"   ✅ Historical data: {len(bpi_data)} data points")
                return True, "coindesk", price
            else:
                print(f"   ❌ Historical data failed: {hist_response.status_code}")
        else:
            print(f"   ❌ Failed: {response.text[:100]}")
            
    except Exception as e:
        print(f"   ❌ Exception: {e}")
    
    return False, None, None

def test_coinbase_api():
    """Test Coinbase API"""
    print("🔍 Testing Coinbase API...")
    
    try:
        # Test current price
        url = "https://api.coinbase.com/v2/exchange-rates"
        params = {'currency': 'BTC'}
        
        response = requests.get(url, params=params, timeout=10)
        print(f"   Status Code: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            price = float(data['data']['rates']['USD'])
            print(f"   ✅ Current Bitcoin price: ${price:,.2f}")
            return True, "coinbase", price
        else:
            print(f"   ❌ Failed: {response.text[:100]}")
            
    except Exception as e:
        print(f"   ❌ Exception: {e}")
    
    return False, None, None

def test_kraken_api():
    """Test Kraken API"""
    print("🔍 Testing Kraken API...")
    
    try:
        # Test current price
        url = "https://api.kraken.com/0/public/Ticker"
        params = {'pair': 'XBTUSD'}
        
        response = requests.get(url, params=params, timeout=10)
        print(f"   Status Code: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            if 'result' in data and 'XXBTZUSD' in data['result']:
                price = float(data['result']['XXBTZUSD']['c'][0])
                print(f"   ✅ Current Bitcoin price: ${price:,.2f}")
                return True, "kraken", price
            else:
                print(f"   ❌ Unexpected response format: {data}")
        else:
            print(f"   ❌ Failed: {response.text[:100]}")
            
    except Exception as e:
        print(f"   ❌ Exception: {e}")
    
    return False, None, None

def test_binance_api():
    """Test Binance API"""
    print("🔍 Testing Binance API...")
    
    try:
        # Test current price
        url = "https://api.binance.com/api/v3/ticker/price"
        params = {'symbol': 'BTCUSDT'}
        
        response = requests.get(url, params=params, timeout=10)
        print(f"   Status Code: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            price = float(data['price'])
            print(f"   ✅ Current Bitcoin price: ${price:,.2f}")
            return True, "binance", price
        else:
            print(f"   ❌ Failed: {response.text[:100]}")
            
    except Exception as e:
        print(f"   ❌ Exception: {e}")
    
    return False, None, None

def test_yfinance_symbols():
    """Test various yfinance symbols"""
    print("🔍 Testing yfinance symbols...")
    
    try:
        import yfinance as yf
        
        # Test multiple Bitcoin symbols
        symbols_to_test = [
            "BTC-USD",
            "BTCUSD=X", 
            "BTC-EUR",
            "BTCGBP=X",
            "BTCJPY=X",
            "BTC=F",
            "BTCUSDT-USD"
        ]
        
        for symbol in symbols_to_test:
            try:
                print(f"   Testing {symbol}...")
                ticker = yf.Ticker(symbol)
                
                # Try to get recent data
                hist = ticker.history(period="5d")
                
                if not hist.empty:
                    latest_price = hist['Close'].iloc[-1]
                    print(f"   ✅ {symbol}: ${latest_price:,.2f} ({len(hist)} days)")
                    return True, f"yfinance_{symbol}", latest_price
                else:
                    print(f"   ❌ {symbol}: No data")
                    
            except Exception as e:
                print(f"   ❌ {symbol}: {e}")
                
    except ImportError:
        print("   ❌ yfinance not installed")
    except Exception as e:
        print(f"   ❌ yfinance error: {e}")
    
    return False, None, None

def test_yahoo_finance_direct():
    """Test Yahoo Finance API directly"""
    print("🔍 Testing Yahoo Finance API directly...")
    
    try:
        # Direct Yahoo Finance API call
        url = "https://query1.finance.yahoo.com/v8/finance/chart/BTC-USD"
        
        response = requests.get(url, timeout=10)
        print(f"   Status Code: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            if 'chart' in data and 'result' in data['chart'] and data['chart']['result']:
                result = data['chart']['result'][0]
                if 'meta' in result and 'regularMarketPrice' in result['meta']:
                    price = result['meta']['regularMarketPrice']
                    print(f"   ✅ Current Bitcoin price: ${price:,.2f}")
                    return True, "yahoo_direct", price
                else:
                    print(f"   ❌ No price in response: {data}")
            else:
                print(f"   ❌ Unexpected response: {data}")
        else:
            print(f"   ❌ Failed: {response.text[:100]}")
            
    except Exception as e:
        print(f"   ❌ Exception: {e}")
    
    return False, None, None

def test_alternative_crypto_apis():
    """Test alternative crypto APIs"""
    print("🔍 Testing alternative crypto APIs...")
    
    apis_to_test = [
        {
            "name": "CryptoCurrency API",
            "url": "https://api.coinlore.net/api/ticker/?id=90",
            "price_field": ["0", "price_usd"]
        },
        {
            "name": "CoinCap API", 
            "url": "https://api.coincap.io/v2/assets/bitcoin",
            "price_field": ["data", "priceUsd"]
        },
        {
            "name": "CoinAPI",
            "url": "https://rest.coinapi.io/v1/exchangerate/BTC/USD",
            "price_field": ["rate"]
        }
    ]
    
    for api in apis_to_test:
        try:
            print(f"   Testing {api['name']}...")
            response = requests.get(api["url"], timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                
                # Navigate to price field
                price_data = data
                for field in api["price_field"]:
                    if isinstance(price_data, list) and field.isdigit():
                        price_data = price_data[int(field)]
                    else:
                        price_data = price_data.get(field, {})
                
                if price_data:
                    price = float(price_data)
                    print(f"   ✅ {api['name']}: ${price:,.2f}")
                    return True, api['name'].lower().replace(' ', '_'), price
                else:
                    print(f"   ❌ {api['name']}: No price found")
            else:
                print(f"   ❌ {api['name']}: Status {response.status_code}")
                
        except Exception as e:
            print(f"   ❌ {api['name']}: {e}")
    
    return False, None, None

def main():
    """Test all APIs and find working ones"""
    print("🚀 Bitcoin API and Symbol Verification")
    print("=" * 50)
    
    working_apis = []
    prices = []
    
    # Test all APIs
    apis_to_test = [
        test_coingecko_api,
        test_coindesk_api, 
        test_coinbase_api,
        test_kraken_api,
        test_binance_api,
        test_yfinance_symbols,
        test_yahoo_finance_direct,
        test_alternative_crypto_apis
    ]
    
    for test_func in apis_to_test:
        print()
        try:
            success, api_name, price = test_func()
            if success:
                working_apis.append(api_name)
                prices.append(price)
        except Exception as e:
            print(f"   ❌ Test function failed: {e}")
    
    # Summary
    print("\n" + "=" * 50)
    print("📊 VERIFICATION RESULTS")
    print("=" * 50)
    
    if working_apis:
        print(f"✅ Working APIs found: {len(working_apis)}")
        
        for i, (api, price) in enumerate(zip(working_apis, prices)):
            print(f"   {i+1}. {api}: ${price:,.2f}")
        
        # Check price consistency
        if len(prices) > 1:
            avg_price = sum(prices) / len(prices)
            max_diff = max(abs(p - avg_price) for p in prices)
            consistency = max_diff / avg_price * 100
            
            print(f"\n📈 Price Analysis:")
            print(f"   Average: ${avg_price:,.2f}")
            print(f"   Max difference: {consistency:.1f}%")
            
            if consistency < 2:
                print("   ✅ Prices are consistent")
            else:
                print("   ⚠️ Prices vary significantly - check for errors")
        
        print(f"\n💡 Recommended API order for scripts:")
        for i, api in enumerate(working_apis[:3], 1):
            print(f"   {i}. {api}")
        
    else:
        print("❌ No working APIs found!")
        print("   This could indicate:")
        print("   - Network connectivity issues")
        print("   - Firewall blocking financial APIs")
        print("   - Geographic API restrictions")
        print("   - All APIs are currently down")
    
    print("\n🔧 Next steps:")
    if working_apis:
        print("   1. Update your scripts to use the working APIs above")
        print("   2. Implement fallback order based on reliability")
        print("   3. Test with your specific network/location")
    else:
        print("   1. Check your internet connection")
        print("   2. Try running from a different network")
        print("   3. Use synthetic data generation as fallback")

if __name__ == "__main__":
    main()