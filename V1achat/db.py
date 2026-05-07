from supabase import create_client, Client
import pandas as pd

URL = "https://qppzcnuysrztxgcaherb.supabase.co"
KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InFwcHpjbnV5c3J6dHhnY2FoZXJiIiwicm9sZSI6ImFub24iLCJpYXQiOjE3NzgwNDc1ODYsImV4cCI6MjA5MzYyMzU4Nn0.MCa5luBCFD3lGiUwQ8RnSvLU_2ENspnbdlzQQnQ1V_A"

supabase: Client = create_client(URL, KEY)


def get_user_data(user_id: str) -> float:
    res = supabase.table("profiles").select("cash").eq("id", user_id).execute()
    if len(res.data) == 0:
        supabase.table("profiles").insert({"id": user_id, "cash": 10000.0}).execute()
        return 10000.0
    return res.data[0]["cash"]


def get_history(user_id: str) -> pd.DataFrame:
    res = supabase.table("transactions").select("*").eq("user_id", user_id).order("created_at").execute()
    return pd.DataFrame(res.data)


def save_transaction(user_id: str, type_t: str, actif: str, qte: int, prix: float, nouveau_cash: float) -> None:
    supabase.table("transactions").insert({
        "user_id": user_id,
        "type": type_t,
        "actif": actif,
        "quantite": qte,
        "prix": prix
    }).execute()
    supabase.table("profiles").update({"cash": nouveau_cash}).eq("id", user_id).execute()


def calculate_positions(df: pd.DataFrame, all_tickers) -> dict:
    positions = {name: 0 for name in all_tickers}
    if not df.empty:
        for _, row in df.iterrows():
            if row["type"] == "Achat":
                positions[row["actif"]] += row["quantite"]
            else:
                positions[row["actif"]] -= row["quantite"]
    return positions
