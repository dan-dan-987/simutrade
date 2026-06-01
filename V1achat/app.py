import streamlit as st
from db import supabase
from arcade import afficher_arcade_mode
from strategy_mode import afficher_strategy_mode


st.set_page_config(page_title="Trading Simulator", layout="wide")

st.sidebar.title("Compte Trading")

if "sb_access" in st.session_state and "sb_refresh" in st.session_state:
    try:
        supabase.auth.set_session({
            "access_token": st.session_state.sb_access,
            "refresh_token": st.session_state.sb_refresh
        })
    except Exception:
        pass

if "user" not in st.session_state:
    menu = st.sidebar.selectbox("Menu", ["Connexion", "Inscription"])
    email = st.sidebar.text_input("Email")
    password = st.sidebar.text_input("Mot de passe", type="password")

    if menu == "Inscription":
        if st.sidebar.button("Créer mon compte"):
            try:
                supabase.auth.sign_up({"email": email, "password": password})
                st.sidebar.success("Compte créé, connectez-vous.")
            except Exception as e:
                st.sidebar.error(f"Erreur : {e}")

    if menu == "Connexion":
        if st.sidebar.button("Se connecter"):
            try:
                res = supabase.auth.sign_in_with_password({"email": email, "password": password})
                st.session_state.user = res.user
                st.session_state.sb_access = res.session.access_token
                st.session_state.sb_refresh = res.session.refresh_token
                st.rerun()
            except Exception:
                st.sidebar.error("Identifiants incorrects.")
else:
    mode = st.sidebar.radio("Navigation", ["Arcade", "Stratégie", "Déconnexion"])

    if mode == "Déconnexion":
        supabase.auth.sign_out()
        st.session_state.clear()
        st.rerun()

    if mode == "Arcade":
        afficher_arcade_mode(st.session_state.user.id)

    if mode == "Stratégie":
        afficher_strategy_mode(st.session_state.user.id)