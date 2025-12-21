// Technical Indicator Calculation Methods
// Add these to AnalyticsDashboard class

calculateRSI(prices, period = 14) {
    if (prices.length < period + 1) return 50;
    const changes = [];
    for (let i = 1; i < prices.length; i++) {
        changes.push(prices[i] - prices[i - 1]);
    }
    const gains = changes.map(c => c > 0 ? c : 0);
    const losses = changes.map(c => c < 0 ? -c : 0);
    const avgGain = gains.slice(-period).reduce((a, b) => a + b, 0) / period;
    const avgLoss = losses.slice(-period).reduce((a, b) => a + b, 0) / period;
    if (avgLoss === 0) return 100;
    const rs = avgGain / avgLoss;
    return 100 - (100 / (1 + rs));
}

calculateSMA(prices, period) {
    if (prices.length < period) period = prices.length;
    const slice = prices.slice(-period);
    return slice.reduce((a, b) => a + b, 0) / period;
}

calculateEMA(prices, period) {
    if (prices.length < period) return this.calculateSMA(prices, prices.length);
    const multiplier = 2 / (period + 1);
    let ema = this.calculateSMA(prices.slice(0, period), period);
    for (let i = period; i < prices.length; i++) {
        ema = (prices[i] * multiplier) + (ema * (1 - multiplier));
    }
    return ema;
}

calculateMACD(prices, fast = 12, slow = 26, signal = 9) {
    const emaFast = this.calculateEMA(prices, fast);
    const emaSlow = this.calculateEMA(prices, slow);
    const macdLine = emaFast - emaSlow;
    const signalLine = macdLine * 0.9;
    const histogram = macdLine - signalLine;
    return { macd: macdLine, signal: signalLine, histogram };
}

calculateBollingerBands(prices, period = 20, stdDev = 2) {
    const sma = this.calculateSMA(prices, period);
    const slice = prices.slice(-Math.min(period, prices.length));
    const squaredDiffs = slice.map(p => Math.pow(p - sma, 2));
    const variance = squaredDiffs.reduce((a, b) => a + b, 0) / slice.length;
    const std = Math.sqrt(variance);
    return {
        upper: sma + (stdDev * std),
        middle: sma,
        lower: sma - (stdDev * std),
        std: std
    };
}

calculateStochastic(prices, period = 14) {
    const slice = prices.slice(-Math.min(period, prices.length));
    const highest = Math.max(...slice);
    const lowest = Math.min(...slice);
    const current = prices[prices.length - 1];
    let k = 50;
    if (highest !== lowest) {
        k = ((current - lowest) / (highest - lowest)) * 100;
    }
    const d = k * 0.9;
    return { k, d };
}

calculateATR(prices, period = 14) {
    if (prices.length < 2) return 0;
    const ranges = [];
    for (let i = 1; i < prices.length; i++) {
        ranges.push(Math.abs(prices[i] - prices[i - 1]));
    }
    const slice = ranges.slice(-Math.min(period, ranges.length));
    return slice.reduce((a, b) => a + b, 0) / slice.length;
}

calculateAllIndicators(prices) {
    const current = prices[prices.length - 1];
    
    // RSI
    const rsi = this.calculateRSI(prices, 14);
    const rsiSignal = rsi < 30 ? 'BUY' : rsi > 70 ? 'SELL' : 'HOLD';
    
    // MACD
    const macd = this.calculateMACD(prices);
    const macdSignal = macd.histogram > 0 ? 'BUY' : 'SELL';
    
    // Moving Averages
    const sma20 = this.calculateSMA(prices, 20);
    const sma50 = this.calculateSMA(prices, 50);
    const ema12 = this.calculateEMA(prices, 12);
    const ema26 = this.calculateEMA(prices, 26);
    const goldenCross = ema12 > ema26;
    const maSignal = goldenCross ? 'BUY' : 'SELL';
    
    // Bollinger Bands
    const bb = this.calculateBollingerBands(prices);
    let bbSignal = 'HOLD';
    if (current < bb.lower) bbSignal = 'BUY';
    else if (current > bb.upper) bbSignal = 'SELL';
    
    // Stochastic
    const stoch = this.calculateStochastic(prices);
    const stochSignal = stoch.k < 20 ? 'BUY' : stoch.k > 80 ? 'SELL' : 'HOLD';
    
    // ATR
    const atr = this.calculateATR(prices);
    const atrPercent = (atr / current) * 100;
    
    return {
        rsi: { value: rsi, signal: rsiSignal },
        macd: { value: macd.macd, signal: macdSignal, histogram: macd.histogram },
        ma: { value: sma20, sma50, ema12, ema26, signal: maSignal, goldenCross },
        bb: { value: bb.middle, upper: bb.upper, lower: bb.lower, signal: bbSignal },
        stoch: { k: stoch.k, d: stoch.d, signal: stochSignal },
        atr: { value: atr, percent: atrPercent }
    };
}
