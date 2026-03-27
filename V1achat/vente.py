import streamlit as st
import yfinance as yf
import pandas as pd

st.title("Simulation des marchés")

# Chargement des données
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

    data = yf.download(list(tickers.values()), period="5y")["Close"]
    data.columns = tickers.keys()
    return data

data = load_data()

# Sélection des actifs
actifs = st.multiselect(
    "Choisis les actifs",
    data.columns.tolist(),
    default=["Bitcoin"]
)

# Slider temporel
jour = st.slider(
    "Avancer dans le temps",
    min_value=0,
    max_value=len(data) - 1,
    value=100
)

# Données filtrées
data_filtre = data.iloc[:jour + 1]

# Affichage du graphique
st.subheader("Évolution des prix")
st.line_chart(data_filtre[actifs])
