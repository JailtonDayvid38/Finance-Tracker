
import io
from datetime import date
import pandas as pd
import streamlit as st

from core.finance import build_dashboard, build_category_summary, build_monthly_summary, get_month_key
from core.storage import add_transaction, delete_transaction, load_goals, load_transactions, save_goal, update_transaction

st.set_page_config(page_title="Finance Tracker", page_icon="💰", layout="wide")
st.title("💰 Finance Tracker")
st.caption("Controle Financeiro Pessoal e Dashboard de Despesas")
st.info("Aplicação para organização financeira pessoal. Os dados ficam armazenados localmente na pasta data do projeto.")

def currency_br(value):
    text = f"{float(value):,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
    return f"R$ {text}"

def month_label(month_key):
    year, month = month_key.split("-")
    names = {"01":"Jan","02":"Fev","03":"Mar","04":"Abr","05":"Mai","06":"Jun","07":"Jul","08":"Ago","09":"Set","10":"Out","11":"Nov","12":"Dez"}
    return f"{names.get(month, month)}/{year}"


def safe_text(value):
    """Converte valores vazios/NaN em texto vazio para a interface."""
    if pd.isna(value):
        return ""
    return str(value)

expense_categories = ["Alimentação","Moradia","Transporte","Saúde","Educação","Lazer","Assinaturas","Compras","Impostos","Outros"]
income_categories = ["Salário","Freelance","Investimentos","Venda","Reembolso","Outros"]
payment_methods = ["PIX","Débito","Crédito","Dinheiro","Transferência","Boleto","Outro"]

tab1, tab2, tab3, tab4 = st.tabs(["➕ Nova movimentação","📊 Dashboard","📚 Histórico","🎯 Metas"])

with tab1:
    st.header("Nova movimentação")
    c1, c2, c3 = st.columns(3)
    with c1:
        t_date = st.date_input("Data", value=date.today())
    with c2:
        t_type = st.selectbox("Tipo", ["Receita", "Despesa"])
    with c3:
        amount = st.number_input("Valor (R$)", min_value=0.0, step=10.0, format="%.2f")

    categories = income_categories if t_type == "Receita" else expense_categories
    c4, c5 = st.columns(2)
    with c4:
        category = st.selectbox("Categoria", categories)
    with c5:
        payment = st.selectbox("Forma de pagamento", payment_methods)

    description = st.text_input("Descrição", placeholder="Ex.: Supermercado, salário, combustível...")
    notes = st.text_area("Observações (opcional)", height=90)

    if st.button("💾 Salvar movimentação", type="primary", use_container_width=True):
        if amount <= 0:
            st.warning("Informe um valor maior que zero.")
        else:
            add_transaction({
                "Data": t_date.isoformat(),
                "Tipo": t_type,
                "Categoria": category,
                "Descrição": description.strip(),
                "Valor": round(float(amount), 2),
                "Forma de Pagamento": payment,
                "Observações": notes.strip(),
            })
            st.success("Movimentação salva com sucesso.")
            st.rerun()

with tab2:
    st.header("Dashboard Financeiro")
    transactions = load_transactions()
    goals = load_goals()

    if transactions.empty:
        st.info("Cadastre receitas e despesas para visualizar o dashboard.")
    else:
        transactions["Data"] = pd.to_datetime(transactions["Data"], errors="coerce")
        months = sorted(transactions["Data"].dropna().dt.strftime("%Y-%m").unique().tolist(), reverse=True)
        current = get_month_key(date.today())
        idx = months.index(current) if current in months else 0
        selected_month = st.selectbox("Mês de análise", months, index=idx, format_func=month_label)

        month_df = transactions[transactions["Data"].dt.strftime("%Y-%m") == selected_month].copy()
        dash = build_dashboard(transactions, month_df)

        c1, c2, c3, c4 = st.columns(4)
        c1.metric("Saldo acumulado", currency_br(dash["saldo_acumulado"]))
        c2.metric("Receitas do mês", currency_br(dash["receitas_mes"]))
        c3.metric("Despesas do mês", currency_br(dash["despesas_mes"]))
        c4.metric("Resultado do mês", currency_br(dash["resultado_mes"]))

        st.subheader("🎯 Meta de despesas")
        goal = 0.0
        if not goals.empty and selected_month in goals["Mês"].astype(str).tolist():
            goal = float(goals[goals["Mês"].astype(str) == selected_month].iloc[-1]["Meta de Despesas"])

        if goal > 0:
            used = dash["despesas_mes"]
            pct = (used / goal) * 100
            if used <= goal:
                st.success(f"{pct:.1f}% da meta utilizada. Restam {currency_br(goal-used)}.")
            else:
                st.error(f"Meta ultrapassada em {currency_br(used-goal)} ({pct:.1f}% utilizada).")
            st.progress(min(pct/100, 1.0))
        else:
            st.info("Nenhuma meta definida para este mês.")

        st.subheader("📌 Despesas por categoria")
        cat = build_category_summary(month_df)
        if cat.empty:
            st.write("Nenhuma despesa registrada neste mês.")
        else:
            st.bar_chart(cat.set_index("Categoria")["Valor"])
            top = cat.iloc[0]
            st.write(f"**Categoria com maior despesa:** {top['Categoria']} — {currency_br(top['Valor'])}")

        st.subheader("📊 Receitas x Despesas")
        comp = pd.DataFrame({
            "Tipo": ["Receitas", "Despesas"],
            "Valor": [dash["receitas_mes"], dash["despesas_mes"]]
        }).set_index("Tipo")
        st.bar_chart(comp)

        st.subheader("📈 Evolução mensal")
        monthly = build_monthly_summary(transactions)
        if not monthly.empty:
            chart = monthly.copy()
            chart["Mês"] = chart["Mês"].apply(month_label)
            st.line_chart(chart.set_index("Mês")[["Receitas","Despesas","Resultado"]])

with tab3:
    st.header("Histórico de movimentações")
    transactions = load_transactions()

    if transactions.empty:
        st.info("Nenhuma movimentação salva.")
    else:
        df = transactions.copy()
        df["Data"] = pd.to_datetime(df["Data"], errors="coerce")

        f1, f2 = st.columns(2)
        with f1:
            type_filter = st.multiselect("Filtrar por tipo", ["Receita","Despesa"], default=["Receita","Despesa"])
        with f2:
            cats = sorted(df["Categoria"].dropna().astype(str).unique().tolist())
            cat_filter = st.multiselect("Filtrar por categoria", cats, default=cats)

        filtered = df[df["Tipo"].isin(type_filter) & df["Categoria"].isin(cat_filter)].copy()
        display = filtered.copy()
        display["Data"] = display["Data"].dt.strftime("%d/%m/%Y")
        display["Valor (R$)"] = display["Valor"].apply(currency_br)
        display = display.drop(columns=["Valor"], errors="ignore")
        st.dataframe(display, use_container_width=True, hide_index=True)

        if not filtered.empty:
            st.subheader("✏️ Editar ou excluir")
            selected_id = st.selectbox("Selecione o ID", filtered["ID"].astype(str).tolist())
            row = transactions[transactions["ID"].astype(str) == selected_id].iloc[-1]

            e1, e2, e3 = st.columns(3)
            with e1:
                edit_date = st.date_input("Data da movimentação", value=pd.to_datetime(row["Data"]).date(), key="edit_date")
            with e2:
                edit_type = st.selectbox("Tipo da movimentação", ["Receita","Despesa"], index=0 if row["Tipo"]=="Receita" else 1)
            with e3:
                edit_amount = st.number_input("Novo valor (R$)", min_value=0.01, value=float(row["Valor"]), step=10.0, format="%.2f")

            edit_categories = income_categories if edit_type == "Receita" else expense_categories
            edit_category = st.selectbox(
                "Nova categoria",
                edit_categories,
                index=edit_categories.index(row["Categoria"]) if row["Categoria"] in edit_categories else 0
            )
            edit_description = st.text_input("Nova descrição", value=safe_text(row.get("Descrição", "")))
            current_payment = safe_text(row.get("Forma de Pagamento", ""))
            payment_index = (
                payment_methods.index(current_payment)
                if current_payment in payment_methods
                else 0
            )

            edit_payment = st.selectbox(
                "Nova forma de pagamento",
                payment_methods,
                index=payment_index
            )

            edit_notes = st.text_area(
                "Novas observações",
                value=safe_text(row.get("Observações", ""))
            )

            b1, b2 = st.columns(2)
            with b1:
                if st.button("💾 Atualizar movimentação", use_container_width=True):
                    update_transaction(selected_id, {
                        "Data": edit_date.isoformat(),
                        "Tipo": edit_type,
                        "Categoria": edit_category,
                        "Descrição": edit_description.strip(),
                        "Valor": round(float(edit_amount), 2),
                        "Forma de Pagamento": edit_payment,
                        "Observações": edit_notes.strip(),
                    })
                    st.success("Movimentação atualizada.")
                    st.rerun()
            with b2:
                if st.button("🗑️ Excluir movimentação", use_container_width=True):
                    delete_transaction(selected_id)
                    st.success("Movimentação excluída.")
                    st.rerun()

        st.divider()
        e1, e2 = st.columns(2)
        with e1:
            csv_data = transactions.to_csv(index=False).encode("utf-8-sig")
            st.download_button("📄 Baixar CSV", csv_data, "finance_tracker_historico.csv", "text/csv", use_container_width=True)
        with e2:
            buffer = io.BytesIO()
            with pd.ExcelWriter(buffer, engine="openpyxl") as writer:
                transactions.to_excel(writer, index=False, sheet_name="Movimentacoes")
            st.download_button(
                "📊 Baixar Excel",
                buffer.getvalue(),
                "finance_tracker_historico.xlsx",
                "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                use_container_width=True
            )

with tab4:
    st.header("Metas mensais de despesas")
    goal_month = st.text_input("Mês", value=get_month_key(date.today()), help="Formato AAAA-MM")
    goal_value = st.number_input("Meta de despesas (R$)", min_value=0.0, step=100.0, format="%.2f")

    if st.button("🎯 Salvar meta", type="primary", use_container_width=True):
        if len(goal_month) != 7 or goal_month[4] != "-":
            st.warning("Informe o mês no formato AAAA-MM.")
        elif goal_value <= 0:
            st.warning("Informe uma meta maior que zero.")
        else:
            save_goal(goal_month, goal_value)
            st.success("Meta salva com sucesso.")
            st.rerun()

    goals = load_goals()
    if not goals.empty:
        show = goals.copy()
        show["Meta de Despesas"] = show["Meta de Despesas"].apply(currency_br)
        st.dataframe(show, use_container_width=True, hide_index=True)