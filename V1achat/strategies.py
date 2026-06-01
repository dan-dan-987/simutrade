import pandas as pd
import numpy as np


def generate_signals_sma_cross(market_data, actif, short=20, long=50):
    prices = market_data[actif].dropna()
    sma_s = prices.rolling(short).mean()
    sma_l = prices.rolling(long).mean()

    signals = pd.Series(index=prices.index, dtype=object)
    signals[(sma_s.shift(1) < sma_l.shift(1)) & (sma_s > sma_l)] = "buy"
    signals[(sma_s.shift(1) > sma_l.shift(1)) & (sma_s < sma_l)] = "sell"
    return signals


def generate_signals_rsi(market_data, actif, period=14, low=30, high=70):
    prices = market_data[actif].dropna()
    delta = prices.diff()
    gain = delta.clip(lower=0).rolling(period).mean()
    loss = -delta.clip(upper=0).rolling(period).mean()
    rs = gain / loss
    rsi = 100 - (100 / (1 + rs))

    signals = pd.Series(index=prices.index, dtype=object)
    signals[rsi < low] = "buy"
    signals[rsi > high] = "sell"
    return signals


def generate_signals_macd(market_data, actif, fast=12, slow=26, signal=9):
    prices = market_data[actif].dropna()
    ema_fast = prices.ewm(span=fast).mean()
    ema_slow = prices.ewm(span=slow).mean()
    macd = ema_fast - ema_slow
    macd_sig = macd.ewm(span=signal).mean()

    signals = pd.Series(index=prices.index, dtype=object)
    signals[(macd.shift(1) < macd_sig.shift(1)) & (macd > macd_sig)] = "buy"
    signals[(macd.shift(1) > macd_sig.shift(1)) & (macd < macd_sig)] = "sell"
    return signals


def generate_signals_bollinger(market_data, actif, period=20, std=2):
    prices = market_data[actif].dropna()
    mb = prices.rolling(period).mean()
    ub = mb + std * prices.rolling(period).std()
    lb = mb - std * prices.rolling(period).std()

    signals = pd.Series(index=prices.index, dtype=object)
    signals[prices < lb] = "buy"
    signals[prices > ub] = "sell"
    return signals


def backtest_strategy(prices, signals, position_size=0.2, fee=0.0, initial_capital=10000):
    prices = prices.reindex(signals.index).dropna()
    signals = signals.reindex(prices.index)

    cash = initial_capital
    position = 0.0
    equity_curve = []

    for date, price in prices.items():
        signal = signals.loc[date]

        equity = cash + position * price

        if signal == "buy":
            target_invest = equity * position_size
            current_invest = position * price
            to_invest = max(0.0, target_invest - current_invest)

            if to_invest > 0 and cash > 0:
                qty = to_invest / price
                cost = qty * price * (1 + fee)
                if cost > cash:
                    cost = cash
                    qty = cost / (price * (1 + fee))
                cash -= cost
                position += qty

        elif signal == "sell":
            if position > 0:
                proceeds = position * price * (1 - fee)
                cash += proceeds
                position = 0.0

        equity = cash + position * price
        equity_curve.append(equity)

    equity_series = pd.Series(equity_curve, index=prices.index)
    return equity_series


def sharpe_ratio(daily_returns, risk_free=0.0):
    if daily_returns.std() == 0 or len(daily_returns) == 0:
        return 0.0
    excess = daily_returns - risk_free
    return np.sqrt(252) * excess.mean() / excess.std()


def max_drawdown(equity_curve):
    roll_max = equity_curve.cummax()
    drawdown = (equity_curve - roll_max) / roll_max
    return drawdown.min()

def strategy_sma_cross(market_data, actif):
    return generate_signals_sma_cross(market_data, actif)

def generate_signals_hold(prices):
    signals = pd.Series(index=prices.index, dtype=object)
    first_date = prices.index[0]
    signals[first_date] = "buy"
    return signals
