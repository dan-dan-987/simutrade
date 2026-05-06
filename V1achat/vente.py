import streamlit as st
import yfinance as yf
import pandas as pd
from supabase import create_client, Client

# SUPABASE avec compte créer par Malo
URL = "https://qppzcnuysrztxgcaherb.supabase.co"
KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InFwcHpjbnV5c3J6dHhnY2FoZXJiIiwicm9sZSI6ImFub24iLCJpYXQiOjE3NzgwNDc1ODYsImV4cCI6MjA5MzYyMzU4Nn0.MCa5luBCFD3lGiUwQ8RnSvLU_2ENspnbdlzQQnQ1V_A"
supabase: Client = create_client(URL, KEY)

# FONCTIONS DE LA BASE DE DONNÉES 

def get_user_data(user_id):
    """Récupère le cash de l'utilisateur ou crée son profil s'il est nouveau."""
    res = supabase.table("profiles").select("cash").eq("id", user_id).execute()
    if len(res.data) == 0:
        #  Création du profil avec 10 000$
        supabase.table("profiles").insert({"id": user_id, "cash": 10000.0}).execute()
        return 10000.0
    return res.data[0]["cash"]

def get_history(user_id):
    """Récupère l'historique des transactions depuis Supabase."""
    res = supabase.table("transactions").select("*").eq("user_id", user_id).order("created_at").execute()
    return pd.DataFrame(res.data)

def save_transaction(user_id, type_t, actif, qte, prix, nouveau_cash):
    """Enregistre l'achat/vente et met à jour le solde cash."""
    # Enregistrement de la transaction
    supabase.table("transactions").insert({
        "user_id": user_id, "type": type_t, "actif": actif, "quantite": qte, "prix": prix
    }).execute()
    # Mise à jour du cash dans le profil
    supabase.table("profiles").update({"cash": nouveau_cash}).eq("id", user_id).execute()

def calculate_positions(df, all_tickers):
    """Calcule le nombre de titres détenus à partir de l'historique."""
    positions = {name: 0 for name in all_tickers}
    if not df.empty:
        for _, row in df.iterrows():
            if row['type'] == 'Achat':
                positions[row['actif']] += row['quantite']
            else:
                positions[row['actif']] -= row['quantite']
    return positions

# DONNÉES BOURSIÈRES 
@st.cache_data
def load_market_data():
    tickers = {
        "Bitcoin": "BTC-USD", "Ethereum": "ETH-USD", "Solana": "SOL-USD",
        "CAC40": "^FCHI", "S&P500": "^GSPC", "Apple": "AAPL",
        "Google": "GOOGL", "LVMH": "MC.PA", "Or": "GC=F", "Argent": "SI=F"
    }
    data = yf.download(list(tickers.values()), period="5y")["Close"]
    data.columns = tickers.keys()
    return data.ffill().dropna(axis=1, how="all")

# AUTHENTIFICATION 

st.sidebar.title("Compte Trading")

if "user" not in st.session_state:
    menu = ["Connexion", "Inscription"]
    choice = st.sidebar.selectbox("Menu", menu)
    email = st.sidebar.text_input("Email")
    password = st.sidebar.text_input("Mot de passe", type="password")

    if choice == "Inscription":
        if st.sidebar.button("Créer mon compte"):
            try:
                supabase.auth.sign_up({"email": email, "password": password})
                st.sidebar.success("Compte créé ! Connectez-vous.")
            except Exception as e:
                st.sidebar.error(f"Erreur : {e}")
    else:
        if st.sidebar.button("Se connecter"):
            try:
                res = supabase.auth.sign_in_with_password({"email": email, "password": password})
                st.session_state.user = res.user
                st.rerun()
            except Exception as e:
                st.sidebar.error("Identifiants incorrects.")
else:
    if st.sidebar.button("Se déconnecter"):
        supabase.auth.sign_out()
        del st.session_state.user
        st.rerun()

if "user" in st.session_state:
    u_id = st.session_state.user.id
    st.title("Simulation de marché et trading virtuel")

    # Récupération des données si l'utilisateur a deja un compte
    current_cash = get_user_data(u_id)
    history_df = get_history(u_id)
    market_data = load_market_data()
    positions = calculate_positions(history_df, market_data.columns)

    actifs = st.multiselect("Actifs à afficher", market_data.columns.tolist(), default=["Bitcoin"])
    jour = st.slider("Position dans le temps", 0, len(market_data) - 1, len(market_data) - 1)
    
    subset = market_data.iloc[:jour + 1]
    prix_actuels = subset.iloc[-1]

    st.line_chart(subset[actifs])

    st.header("Trading")
    col_t1, col_t2 = st.columns(2)
    with col_t1:
        actif_sel = st.selectbox("Sélectionne un actif", market_data.columns)
        quantite = st.number_input("Quantité", min_value=1, value=1)
    
    prix_unitaire = prix_actuels[actif_sel]
    
    with col_t2:
        st.write(f"Prix actuel : **{prix_unitaire:.2f} $**")
        st.write(f"Total opération : **{(prix_unitaire * quantite):,.2f} $**")

    c1, c2 = st.columns(2)
    with c1:
        if st.button("ACHETER", use_container_width=True):
            cout = prix_unitaire * quantite
            if current_cash >= cout:
                save_transaction(u_id, "Achat", actif_sel, quantite, prix_unitaire, current_cash - cout)
                st.success("Achat effectué !")
                st.rerun()
            else:
                st.error("Fonds insuffisants.")
    
    with c2:
        if st.button("VENDRE", use_container_width=True):
            if positions.get(actif_sel, 0) >= quantite:
                gain = prix_unitaire * quantite
                save_transaction(u_id, "Vente", actif_sel, quantite, prix_unitaire, current_cash + gain)
                st.success("Vente effectuée !")
                st.rerun()
            else:
                st.error("Pas assez de titres.")

    st.header("Mon Portefeuille")
    df_p = pd.DataFrame({
        "Actif": market_data.columns,
        "Quantité": [positions[a] for a in market_data.columns],
        "Prix": [prix_actuels[a] for a in market_data.columns]
    })
    df_p["Valeur ($)"] = df_p["Quantité"] * df_p["Prix"]
    
    st.dataframe(df_p[df_p["Quantité"] > 0]) # On n'affiche que ce qu'on possède

    val_totale = df_p["Valeur ($)"].sum() + current_cash
    st.metric("Cash disponible", f"{current_cash:,.2f} $")
    st.metric("Valeur Totale", f"{val_totale:,.2f} $")

else:
    st.info("Veuillez vous connecter via la barre latérale pour accéder à votre portefeuille.")