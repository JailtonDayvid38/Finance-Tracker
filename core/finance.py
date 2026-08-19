
from datetime import date
import pandas as pd

def get_month_key(value) -> str:
    if isinstance(value, date):
        return value.strftime("%Y-%m")
    return pd.to_datetime(value).strftime("%Y-%m")

def build_dashboard(transactions: pd.DataFrame, month_transactions: pd.DataFrame) -> dict:
    all_df = transactions.copy()
    month_df = month_transactions.copy()
    for df in (all_df, month_df):
        df["Valor"] = pd.to_numeric(df["Valor"], errors="coerce").fillna(0)

    total_income = all_df.loc[all_df["Tipo"] == "Receita", "Valor"].sum()
    total_expense = all_df.loc[all_df["Tipo"] == "Despesa", "Valor"].sum()
    month_income = month_df.loc[month_df["Tipo"] == "Receita", "Valor"].sum()
    month_expense = month_df.loc[month_df["Tipo"] == "Despesa", "Valor"].sum()

    return {
        "saldo_acumulado": float(total_income - total_expense),
        "receitas_mes": float(month_income),
        "despesas_mes": float(month_expense),
        "resultado_mes": float(month_income - month_expense),
    }

def build_category_summary(month_transactions: pd.DataFrame) -> pd.DataFrame:
    if month_transactions.empty:
        return pd.DataFrame(columns=["Categoria", "Valor"])
    df = month_transactions[month_transactions["Tipo"] == "Despesa"].copy()
    if df.empty:
        return pd.DataFrame(columns=["Categoria", "Valor"])
    df["Valor"] = pd.to_numeric(df["Valor"], errors="coerce").fillna(0)
    return (
        df.groupby("Categoria", dropna=False)["Valor"]
        .sum().sort_values(ascending=False).reset_index()
    )

def build_monthly_summary(transactions: pd.DataFrame) -> pd.DataFrame:
    if transactions.empty:
        return pd.DataFrame(columns=["Mês", "Receitas", "Despesas", "Resultado"])

    df = transactions.copy()
    df["Data"] = pd.to_datetime(df["Data"], errors="coerce")
    df["Valor"] = pd.to_numeric(df["Valor"], errors="coerce").fillna(0)
    df = df.dropna(subset=["Data"])
    df["Mês"] = df["Data"].dt.strftime("%Y-%m")

    grouped = (
        df.groupby(["Mês", "Tipo"])["Valor"]
        .sum().unstack(fill_value=0).reset_index()
    )
    if "Receita" not in grouped.columns:
        grouped["Receita"] = 0.0
    if "Despesa" not in grouped.columns:
        grouped["Despesa"] = 0.0

    grouped = grouped.rename(columns={"Receita": "Receitas", "Despesa": "Despesas"})
    grouped["Resultado"] = grouped["Receitas"] - grouped["Despesas"]
    return grouped.sort_values("Mês")
