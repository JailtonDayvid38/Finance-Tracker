
from pathlib import Path
import uuid
import pandas as pd

DATA_DIR = Path("data")
TRANSACTIONS_FILE = DATA_DIR / "transactions.csv"
GOALS_FILE = DATA_DIR / "goals.csv"

TRANSACTION_COLUMNS = [
    "ID", "Data", "Tipo", "Categoria", "Descrição", "Valor",
    "Forma de Pagamento", "Observações"
]
GOAL_COLUMNS = ["Mês", "Meta de Despesas"]

def _ensure():
    DATA_DIR.mkdir(parents=True, exist_ok=True)

def load_transactions():
    _ensure()
    if not TRANSACTIONS_FILE.exists():
        return pd.DataFrame(columns=TRANSACTION_COLUMNS)
    try:
        df = pd.read_csv(TRANSACTIONS_FILE, encoding="utf-8-sig")
        for c in TRANSACTION_COLUMNS:
            if c not in df.columns:
                df[c] = ""
        return df[TRANSACTION_COLUMNS]
    except Exception:
        return pd.DataFrame(columns=TRANSACTION_COLUMNS)

def _save_transactions(df):
    _ensure()
    df.to_csv(TRANSACTIONS_FILE, index=False, encoding="utf-8-sig")

def add_transaction(record):
    df = load_transactions()
    row = {"ID": uuid.uuid4().hex[:8].upper(), **record}
    _save_transactions(pd.concat([df, pd.DataFrame([row])], ignore_index=True))

def update_transaction(transaction_id, updates):
    df = load_transactions()
    mask = df["ID"].astype(str) == str(transaction_id)
    for c, v in updates.items():
        if c in df.columns:
            df.loc[mask, c] = v
    _save_transactions(df)

def delete_transaction(transaction_id):
    df = load_transactions()
    df = df[df["ID"].astype(str) != str(transaction_id)].copy()
    _save_transactions(df)

def load_goals():
    _ensure()
    if not GOALS_FILE.exists():
        return pd.DataFrame(columns=GOAL_COLUMNS)
    try:
        df = pd.read_csv(GOALS_FILE, encoding="utf-8-sig")
        for c in GOAL_COLUMNS:
            if c not in df.columns:
                df[c] = ""
        return df[GOAL_COLUMNS]
    except Exception:
        return pd.DataFrame(columns=GOAL_COLUMNS)

def save_goal(month, amount):
    df = load_goals()
    month = str(month)
    if month in df["Mês"].astype(str).tolist():
        df.loc[df["Mês"].astype(str) == month, "Meta de Despesas"] = round(float(amount), 2)
    else:
        df = pd.concat([
            df,
            pd.DataFrame([{"Mês": month, "Meta de Despesas": round(float(amount), 2)}])
        ], ignore_index=True)
    _ensure()
    df.to_csv(GOALS_FILE, index=False, encoding="utf-8-sig")
