/**
 * Technical Indicators Calculator
 * Client-side calculation of advanced technical indicators
 */

class TechnicalIndicators {
    /**
     * Calculate RSI (Relative Strength Index)
     */
    static calculateRSI(prices, period = 14) {
        if (prices.length < period + 1) return { value: 50, signal: 'neutral' };
        
        const changes = [];
        for (let i = 1; i < prices.length; i++) {
            changes.push(prices[i] - prices[i - 1]);
        }
        
        const gains = changes.map(c => c > 0 ? c : 0);
        const losses = changes.map(c => c < 0 ? -c : 0);
        
        const avgGain = gains.slice(-period).reduce((a, b) => a + b, 0) / period;
        const avgLoss = losses.slice(-period).reduce((a, b) => a + b, 0) / period;
        
        if (avgLoss === 0) return { value: 100, signal: 'overbought' };
        
        const rs = avgGain / avgLoss;
        const rsi = 100 - (100 / (1 + rs));
        
        let signal = 'neutral';
        if (rsi < 30) signal = 'oversold';
        else if (rsi > 70) signal = 'overbought';
        
        return {
            value: rsi,
            signal,
            strength: Math.abs(rsi - 50) / 50
        };
    }
    
    /**
     * Calculate MACD (Moving Average Convergence Divergence)
     */
    static calculateMACD(prices, fastPeriod = 12, slowPeriod = 26, signalPeriod = 9) {
        const emaFast = this.calculateEMA(prices, fastPeriod);
        const emaSlow = this.calculateEMA(prices, slowPeriod);
        
        const macdLine = emaFast - emaSlow;
        const signalLine = macdLine * 0.9; // Simplified
        const histogram = macdLine - signalLine;
        
        return {
            macd: macdLine,
            signal: signalLine,
            histogram,
            trend: macdLine > signalLine ? 'bullish' : 'bearish',
            crossover: histogram > 0 ? 'buy' : 'sell'
        };
    }
    
    /**
     * Calculate EMA (Exponential Moving Average)
     */
    static calculateEMA(prices, period) {
        if (prices.length < period) {
            return prices.reduce((a, b) => a + b, 0) / prices.length;
        }
        
        const multiplier = 2 / (period + 1);
        let ema = prices.slice(0, period).reduce((a, b) => a + b, 0) / period;
        
        for (let i = period; i < prices.length; i++) {
            ema = (prices[i] * multiplier) + (ema * (1 - multiplier));
        }
        
        return ema;
    }
    
    /**
     * Calculate SMA (Simple Moving Average)
     */
    static calculateSMA(prices, period) {
        if (prices.length < period) period = prices.length;
        const slice = prices.slice(-period);
        return slice.reduce((a, b) => a + b, 0) / period;
    }
    
    /**
     * Calculate Bollinger Bands
     */
    static calculateBollingerBands(prices, period = 20, stdDev = 2) {
        const sma = this.calculateSMA(prices, period);
        const slice = prices.slice(-Math.min(period, prices.length));
        
        const squaredDiffs = slice.map(p => Math.pow(p - sma, 2));
        const variance = squaredDiffs.reduce((a, b) => a + b, 0) / slice.length;
        const std = Math.sqrt(variance);
        
        const upper = sma + (stdDev * std);
        const lower = sma - (stdDev * std);
        const current = prices[prices.length - 1];
        
        let position = 'middle';
        if (current > upper) position = 'above_upper';
        else if (current < lower) position = 'below_lower';
        else if (current > sma) position = 'upper_half';
        else position = 'lower_half';
        
        return {
            upper,
            middle: sma,
            lower,
            position,
            bandwidth: ((upper - lower) / sma * 100),
            percentB: ((current - lower) / (upper - lower))
        };
    }
    
    /**
     * Calculate Stochastic Oscillator
     */
    static calculateStochastic(prices, period = 14) {
        const slice = prices.slice(-Math.min(period, prices.length));
        const highest = Math.max(...slice);
        const lowest = Math.min(...slice);
        const current = prices[prices.length - 1];
        
        let kValue = 50;
        if (highest !== lowest) {
            kValue = ((current - lowest) / (highest - lowest)) * 100;
        }
        
        const dValue = kValue * 0.9; // Simplified %D
        
        let signal = 'neutral';
        if (kValue < 20) signal = 'oversold';
        else if (kValue > 80) signal = 'overbought';
        
        return {
            k: kValue,
            d: dValue,
            signal
        };
    }
    
    /**
     * Calculate ATR (Average True Range)
     */
    static calculateATR(prices, period = 14) {
        if (prices.length < 2) return { value: 0, volatility: 'low' };
        
        const ranges = [];
        for (let i = 1; i < prices.length; i++) {
            ranges.push(Math.abs(prices[i] - prices[i - 1]));
        }
        
        const slice = ranges.slice(-Math.min(period, ranges.length));
        const atr = slice.reduce((a, b) => a + b, 0) / slice.length;
        
        const current = prices[prices.length - 1];
        const volatilityPercent = (atr / current) * 100;
        
        return {
            value: atr,
            volatility: volatilityPercent > 5 ? 'high' : volatilityPercent > 2 ? 'medium' : 'low',
            percent: volatilityPercent
        };
    }
    
    /**
     * Calculate ADX (Average Directional Index) - Simplified
     */
    static calculateADX(prices, period = 14) {
        if (prices.length < period + 1) return { value: 25, strength: 'weak' };
        
        const changes = [];
        for (let i = 1; i < prices.length; i++) {
            changes.push(prices[i] - prices[i - 1]);
        }
        
        const plusDM = changes.map(c => c > 0 ? c : 0);
        const minusDM = changes.map(c => c < 0 ? -c : 0);
        
        const atr = this.calculateATR(prices, period).value;
        if (atr === 0) return { value: 25, strength: 'weak' };
        
        const plusDI = (plusDM.slice(-period).reduce((a, b) => a + b, 0) / period / atr) * 100;
        const minusDI = (minusDM.slice(-period).reduce((a, b) => a + b, 0) / period / atr) * 100;
        
        const dx = (plusDI + minusDI) > 0 
            ? Math.abs(plusDI - minusDI) / (plusDI + minusDI) * 100 
            : 25;
        
        return {
            value: dx,
            strength: dx > 25 ? 'strong' : 'weak',
            plusDI,
            minusDI,
            trend: plusDI > minusDI ? 'bullish' : 'bearish'
        };
    }
    
    /**
     * Generate trading signals from all indicators
     */
    static generateSignals(indicators, currentPrice) {
        const signals = {};
        
        // RSI Signal
        if (indicators.rsi.signal === 'oversold') signals.rsi = 'BUY';
        else if (indicators.rsi.signal === 'overbought') signals.rsi = 'SELL';
        else signals.rsi = 'HOLD';
        
        // MACD Signal
        signals.macd = indicators.macd.crossover === 'buy' ? 'BUY' : 'SELL';
        
        // MA Signal
        signals.ma = indicators.moving_averages.golden_cross ? 'BUY' : 'SELL';
        
        // BB Signal
        const bbPos = indicators.bollinger_bands.position;
        if (bbPos === 'below_lower') signals.bb = 'BUY';
        else if (bbPos === 'above_upper') signals.bb = 'SELL';
        else signals.bb = 'HOLD';
        
        // Stochastic Signal
        if (indicators.stochastic.signal === 'oversold') signals.stoch = 'BUY'
