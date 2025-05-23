
import backtrader as bt
import yfinance as yf

class MovingAverageStrategy(bt.Strategy):
    def __init__(self):
        self.ma20 = bt.indicators.SimpleMovingAverage(self.data.close, period=20)
        self.ma50 = bt.indicators.SimpleMovingAverage(self.data.close, period=50)

    def next(self):
        if not self.position:
            if self.ma20[0] > self.ma50[0]:
                self.buy()
        elif self.ma20[0] < self.ma50[0]:
            self.sell()

cerebro = bt.Cerebro()
data = bt.feeds.PandasData(dataname=yf.download('BTC-USD', start='2023-01-01', end='2024-01-01'))
cerebro.adddata(data)
cerebro.addstrategy(MovingAverageStrategy)
cerebro.run()
cerebro.plot()
