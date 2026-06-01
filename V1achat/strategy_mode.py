import streamlit as st
import pandas as pd

from market import load_market_data
from strategies import (
    generate_signals_sma_cross,
    generate_signals_rsi,
    generate_signals_macd,
    generate_signals_bollinger,
    backtest_strategy,
    sharpe_ratio,
    max_drawdown,
    generate_signals_hold
)
from db import supabase


def save_custom_strategy(user_id, name, params):
    supabase.table("strategies").insert({
        "user_id": user_id,
        "name": name,
        "params": params
    }).execute()


def load_user_strategies(user_id):
    res = supabase.table("strategies").select("*").eq("user_id", user_id).execute()
    return res.data


def delete_strategy(strategy_id):
    supabase.table("strategies").delete().eq("id", strategy_id).execute()


def generate_custom_signals(prices, params):
    use_sma = params.get("use_sma", True)
    use_rsi = params.get("use_rsi", True)
    use_macd = params.get("use_macd", True)
    use_boll = params.get("use_boll", False)
    use_ichimoku = params.get("use_ichimoku", False)

    sma_short = params.get("sma_short", 20)
    sma_long = params.get("sma_long", 50)
    sma_s = prices.rolling(sma_short).mean()
    sma_l = prices.rolling(sma_long).mean()

    rsi_period = params.get("rsi_period", 14)
    rsi_low = params.get("rsi_low", 30)
    rsi_high = params.get("rsi_high", 70)
    delta = prices.diff()
    gain = delta.clip(lower=0).rolling(rsi_period).mean()
    loss = -delta.clip(upper=0).rolling(rsi_period).mean()
    rs = gain / loss
    rsi = 100 - (100 / (1 + rs))

    macd_fast = params.get("macd_fast", 12)
    macd_slow = params.get("macd_slow", 26)
    macd_signal = params.get("macd_signal", 9)
    ema_fast = prices.ewm(span=macd_fast).mean()
    ema_slow = prices.ewm(span=macd_slow).mean()
    macd = ema_fast - ema_slow
    macd_sig = macd.ewm(span=macd_signal).mean()

    boll_period = params.get("boll_period", 20)
    boll_std = params.get("boll_std", 2)
    mb = prices.rolling(boll_period).mean()
    ub = mb + boll_std * prices.rolling(boll_period).std()
    lb = mb - boll_std * prices.rolling(boll_period).std()

    tenkan = params.get("tenkan", 9)
    kijun = params.get("kijun", 26)
    tenkan_sen = (prices.rolling(tenkan).max() + prices.rolling(tenkan).min()) / 2
    kijun_sen = (prices.rolling(kijun).max() + prices.rolling(kijun).min()) / 2

    signals = pd.Series(index=prices.index, dtype=object)

    buy_conditions = []
    sell_conditions = []

    if use_sma:
        buy_conditions.append(sma_s > sma_l)
        sell_conditions.append(sma_s < sma_l)

    if use_rsi:
        buy_conditions.append(rsi < rsi_low)
        sell_conditions.append(rsi > rsi_high)

    if use_macd:
        buy_conditions.append(macd > macd_sig)
        sell_conditions.append(macd < macd_sig)

    if use_boll:
        buy_conditions.append(prices < lb)
        sell_conditions.append(prices > ub)

    if use_ichimoku:
        buy_conditions.append(tenkan_sen > kijun_sen)
        sell_conditions.append(tenkan_sen < kijun_sen)

    if buy_conditions:
        buy_sum = sum(cond.astype(int) for cond in buy_conditions)
        signals[buy_sum >= 1] = "buy"

    if sell_conditions:
        sell_sum = sum(cond.astype(int) for cond in sell_conditions)
        signals[sell_sum >= 1] = "sell"

    return signals


def afficher_strategy_mode(user_id):
    st.title("Creation et comparaison de strategies")

    market_data = load_market_data()
    actif = st.selectbox("Actif", market_data.columns)
    prices = market_data[actif].dropna()

    st.subheader("Creer une strategie personnalisee")

    name = st.text_input("Nom de la strategie")

    st.markdown("Activer / Desactiver les conditions")
    use_sma = st.checkbox("Activer condition SMA", value=True)
    use_rsi = st.checkbox("Activer condition RSI", value=True)
    use_macd = st.checkbox("Activer condition MACD", value=True)
    use_boll = st.checkbox("Activer condition Bollinger", value=False)
    use_ichimoku = st.checkbox("Activer condition Ichimoku", value=False)

    st.markdown("Parametres SMA")
    sma_short = st.number_input("SMA courte", min_value=5, max_value=100, value=20)
    sma_long = st.number_input("SMA longue", min_value=10, max_value=200, value=50)

    st.markdown("Parametres RSI")
    rsi_period = st.number_input("RSI periode", min_value=5, max_value=50, value=14)
    rsi_low = st.number_input("RSI bas", min_value=5, max_value=50, value=30)
    rsi_high = st.number_input("RSI haut", min_value=50, max_value=95, value=70)

    st.markdown("Parametres MACD")
    macd_fast = st.number_input("MACD fast", min_value=5, max_value=50, value=12)
    macd_slow = st.number_input("MACD slow", min_value=10, max_value=100, value=26)
    macd_signal = st.number_input("MACD signal", min_value=5, max_value=50, value=9)

    st.markdown("Parametres Bollinger")
    boll_period = st.number_input("Bollinger periode", min_value=5, max_value=100, value=20)
    boll_std = st.number_input("Bollinger ecart-type", min_value=1.0, max_value=4.0, value=2.0)

    st.markdown("Parametres Ichimoku")
    tenkan = st.number_input("Tenkan", min_value=5, max_value=50, value=9)
    kijun = st.number_input("Kijun", min_value=10, max_value=100, value=26)

    st.markdown("Position sizing custom (%)")
    position_size_pct = st.slider("Pourcentage du portefeuille par trade", 1, 100, 20)
    position_size_custom = position_size_pct / 100.0

    params = {
        "use_sma": use_sma,
        "use_rsi": use_rsi,
        "use_macd": use_macd,
        "use_boll": use_boll,
        "use_ichimoku": use_ichimoku,
        "sma_short": sma_short,
        "sma_long": sma_long,
        "rsi_period": rsi_period,
        "rsi_low": rsi_low,
        "rsi_high": rsi_high,
        "macd_fast": macd_fast,
        "macd_slow": macd_slow,
        "macd_signal": macd_signal,
        "boll_period": boll_period,
        "boll_std": boll_std,
        "tenkan": tenkan,
        "kijun": kijun,
        "position_size": position_size_custom
    }

    if st.button("Sauvegarder la strategie"):
        if name.strip() == "":
            st.error("Veuillez entrer un nom.")
        else:
            save_custom_strategy(user_id, name, params)
            st.success("Strategie sauvegardee.")

    st.subheader("Strategies sauvegardees")

    user_strats = load_user_strategies(user_id)

    for strat in user_strats:
        col1, col2 = st.columns([4, 1])
        with col1:
            st.write(f"{strat['name']} — {strat['params']}")
        with col2:
            if st.button("Supprimer", key=f"del_{strat['id']}"):
                delete_strategy(strat["id"])
                st.success("Strategie supprimee.")
                st.rerun()

    strat_names = [s["name"] for s in user_strats]
    selected = st.multiselect("Selectionner des strategies a comparer", strat_names)

    results = {}

    for strat in user_strats:
        if strat["name"] in selected:
            strat_params = strat["params"]
            pos_size = strat_params.get("position_size", position_size_custom)
            signals = generate_custom_signals(prices, strat_params)
            equity = backtest_strategy(prices, signals, position_size=pos_size)
            results[strat["name"]] = equity

    st.subheader("Strategies integrees")

    if st.checkbox("Inclure SMA 20/50"):
        sig = generate_signals_sma_cross(market_data, actif).reindex(prices.index)
        results["SMA 20/50"] = backtest_strategy(prices, sig, position_size=0.2)

    if st.checkbox("Inclure RSI"):
        sig = generate_signals_rsi(market_data, actif).reindex(prices.index)
        results["RSI"] = backtest_strategy(prices, sig, position_size=0.2)

    if st.checkbox("Inclure MACD"):
        sig = generate_signals_macd(market_data, actif).reindex(prices.index)
        results["MACD"] = backtest_strategy(prices, sig, position_size=0.2)

    if st.checkbox("Inclure Bollinger"):
        sig = generate_signals_bollinger(market_data, actif).reindex(prices.index)
        results["Bollinger"] = backtest_strategy(prices, sig, position_size=0.2)

    if st.checkbox("Inclure HOLD 20%"):
        sig = generate_signals_hold(prices)
        results["HOLD 20%"] = backtest_strategy(prices, sig, position_size=0.2)

    if len(results) > 0:
        st.subheader("Comparaison des performances")

        df_equity = pd.DataFrame(results)
        st.line_chart(df_equity)

        st.subheader("Metrics")

        metrics = []
        for name, curve in results.items():
            curve = curve.dropna()
            if len(curve) < 2:
                continue

            total_return = (curve.iloc[-1] / curve.iloc[0]) - 1
            daily_returns = curve.pct_change().dropna()
            sharpe = sharpe_ratio(daily_returns)
            dd = max_drawdown(curve)

            metrics.append({
                "Strategie": name,
                "Rendement (%)": round(total_return * 100, 2),
                "Sharpe": round(sharpe, 2),
                "Max Drawdown (%)": round(dd * 100, 2)
            })

        st.dataframe(pd.DataFrame(metrics))
