import streamlit as st
import yfinance as yf
import pandas as pd

st.title("Simulation des marchés avec Trading")

# -----------------------------
# Chargement des données
# -----------------------------
@st.cache_data
def load_data():
    tickers = {
        "Bitcoin": "BTC-USD",
        "Ethereum": "ETH-USD",
        "Solana": "SOL-USD",
        "CAC40": "^FCHI",
        "S&P500": "^GSPC",
        "Apple": "AAPL",
        "Google": "GOOGL",
        "LVMH": "MC.PA",
        "Or": "GC=F",
        "Argent": "SI=F"
    }

    raw = yf.download(list(tickers.values()), period="5y")["Close"]
    raw.columns = tickers.keys()
    raw = raw.dropna(axis=1, how="all")
    return raw

data = load_data()

# -----------------------------
# Initialisation du portefeuille
# -----------------------------
if "cash" not in st.session_state:
    st.session_state.cash = 10_000  # capital initial
if "positions" not in st.session_state:
    st.session_state.positions = {asset: 0 for asset in data.columns}
if "history" not in st.session_state:
    st.session_state.history = []

# -----------------------------
# Interface utilisateur
# -----------------------------
st.write("Aperçu des données :", data.head())

actifs = st.multiselect("Choisis les actifs", data.columns.tolist(), default=["Bitcoin"])
jour = st.slider("Avancer dans le temps", 0, len(data)-1, 10)

data_filtre = data.iloc[:jour+1]

st.subheader("Évolution des prix")
st.line_chart(data_filtre[actifs])

st.subheader("Valeurs actuelles")
current_prices = data_filtre.iloc[-1]
st.dataframe(current_prices[actifs])

# -----------------------------
# Trading
# -----------------------------
st.header("Trading")

actif_trade = st.selectbox("Actif à trader", data.columns)
quantite = st.number_input("Quantité", min_value=1, value=1)

prix = current_prices[actif_trade]

col1, col2 = st.columns(2)

with col1:
    if st.button("Acheter"):
        coût = prix * quantite
        if st.session_state.cash >= coût:
            st.session_state.cash -= coût
            st.session_state.positions[actif_trade] += quantite
            st.session_state.history.append(
                ("Achat", actif_trade, quantite, prix)
            )
            st.success(f"Acheté {quantite} {actif_trade} à {prix:.2f}")
        else:
            st.error("Pas assez de cash !")

with col2:
    if st.button("Vendre"):
        if st.session_state.positions[actif_trade] >= quantite:
            st.session_state.positions[actif_trade] -= quantite
            gain = prix * quantite
            st.session_state.cash += gain
            st.session_state.history.append(
                ("Vente", actif_trade, quantite, prix)
            )
            st.success(f"Vendu {quantite} {actif_trade} à {prix:.2f}")
        else:
            st.error("Pas assez de quantité à vendre !")

# -----------------------------
# Valeur du portefeuille
# -----------------------------
st.header("Portefeuille")

positions_df = pd.DataFrame({
    "Actif": data.columns,
    "Quantité": [st.session_state.positions[a] for a in data.columns],
    "Prix actuel": [current_prices[a] for a in data.columns],
})

positions_df["Valeur"] = positions_df["Quantité"] * positions_df["Prix actuel"]

st.subheader("Positions")
st.dataframe(positions_df)

valeur_positions = positions_df["Valeur"].sum()
valeur_totale = valeur_positions + st.session_state.cash

st.metric("Cash disponible", f"{st.session_state.cash:,.2f} $")
st.metric("Valeur totale du portefeuille", f"{valeur_totale:,.2f} $")

# -----------------------------
# Historique des transactions
# -----------------------------
st.header("Historique des transactions")
if len(st.session_state.history) > 0:
    hist_df = pd.DataFrame(st.session_state.history, columns=["Type", "Actif", "Quantité", "Prix"])
    st.dataframe(hist_df)
else:
    st.write("Aucune transaction pour le moment.")
