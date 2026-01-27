import streamlit as st
import pandas as pd
import sqlite3
from datetime import datetime, date

# ======================================================
# CONFIGURAÇÃO GERAL
# ======================================================
st.set_page_config(
    page_title="Lian Car | Gestão Automotiva",
    page_icon="🧼",
    layout="wide"
)

# ======================================================
# BANCO DE DADOS (SQLITE)
# ======================================================
def get_connection():
    return sqlite3.connect("lian_car.db", check_same_thread=False)

def init_db():
    conn = get_connection()
    c = conn.cursor()
    # Tabela Financeira com Tipo (Entrada/Saída)
    c.execute("""
    CREATE TABLE IF NOT EXISTS financeiro (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        Data TEXT,
        Tipo TEXT,
        Categoria TEXT,
        Descricao TEXT,
        Valor REAL
    )
    """)
    # Tabela de Serviços (Tabela de Preços)
    c.execute("CREATE TABLE IF NOT EXISTS servicos (id INTEGER PRIMARY KEY AUTOINCREMENT, Nome TEXT, Valor REAL)")
    
    # Tabela de Agendamentos/Pátio
    c.execute("""
    CREATE TABLE IF NOT EXISTS agendamentos (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        Data TEXT,
        Cliente TEXT,
        Placa TEXT,
        Servico TEXT,
        Valor REAL,
        Status TEXT
    )
    """)
    conn.commit()
    conn.close()

init_db()

# ======================================================
# CSS E ESTILIZAÇÃO
# ======================================================
st.markdown("""
<style>
.stApp { background: radial-gradient(circle at top, #020617, #000); color: #e5e7eb; }
[data-testid="stMetric"] { background: #020617; padding: 20px; border-radius: 14px; border: 1px solid #1e293b; }
.stButton>button { background: linear-gradient(135deg, #0ea5e9, #38bdf8); color: #020617; font-weight: bold; border-radius: 12px; width: 100%; }
.status-entrada { color: #22c55e; font-weight: bold; }
.status-saida { color: #ef4444; font-weight: bold; }
</style>
""", unsafe_allow_html=True)

# ======================================================
# LOGIN
# ======================================================
if "logado" not in st.session_state:
    st.session_state.logado = False

def login():
    st.title("🔐 Acesso Administrativo")
    col1, _ = st.columns([1, 2])
    with col1:
        user = st.text_input("Usuário")
        pwd = st.text_input("Senha", type="password")
        if st.button("Entrar"):
            if user == "admin" and pwd == "admin123":
                st.session_state.logado = True
                st.rerun()
            else:
                st.error("Credenciais inválidas")

if not st.session_state.logado:
    login()
    st.stop()

# ======================================================
# DASHBOARD
# ======================================================
def dashboard():
    st.title("📊 Dashboard")
    conn = get_connection()
    df = pd.read_sql("SELECT Tipo, Valor FROM financeiro", conn)
    conn.close()

    entradas = df[df["Tipo"] == "ENTRADA"]["Valor"].sum() if not df.empty else 0
    saidas = df[df["Tipo"] == "SAIDA"]["Valor"].sum() if not df.empty else 0
    lucro = entradas - saidas

    c1, c2, c3 = st.columns(3)
    c1.metric("💰 Faturamento (Entradas)", f"R$ {entradas:,.2f}")
    c2.metric("📉 Despesas (Saídas)", f"R$ {saidas:,.2f}")
    c3.metric("📈 Lucro Líquido", f"R$ {lucro:,.2f}")

    if not df.empty:
        st.subheader("Fluxo de Caixa")
        resumo = df.groupby("Tipo")["Valor"].sum()
        st.bar_chart(resumo)

# ======================================================
# FINANCEIRO (ENTRADAS E SAÍDAS)
# ======================================================
def financeiro():
    st.title("💰 Gestão Financeira")
    
    col_form, col_hist = st.tabs(["➕ Novo Lançamento", "📜 Histórico"])

    with col_form:
        with st.form("lancamento"):
            c1, c2 = st.columns(2)
            tipo = c1.selectbox("Tipo de Movimentação", ["ENTRADA", "SAIDA"])
            categoria = c1.selectbox("Categoria", ["Serviço", "Aluguel", "Produtos", "Energia/Água", "Pagamento", "Outros"])
            valor = c2.number_input("Valor (R$)", min_value=0.0)
            data = c2.date_input("Data", date.today())
            descricao = st.text_input("Descrição")

            if st.form_submit_button("Registrar no Caixa"):
                conn = get_connection()
                conn.execute("""
                    INSERT INTO financeiro (Data, Tipo, Categoria, Descricao, Valor)
                    VALUES (?,?,?,?,?)
                """, (data.isoformat(), tipo, categoria, descricao, valor))
                conn.commit()
                conn.close()
                st.success(f"Lançamento de {tipo} realizado!")
                st.rerun()

    with col_hist:
        conn = get_connection()
        df = pd.read_sql("SELECT * FROM financeiro ORDER BY Data DESC", conn)
        conn.close()
        if not df.empty:
            st.dataframe(df, use_container_width=True)
            # Botão de Backup CSV
            csv = df.to_csv(index=False).encode('utf-8')
            st.download_button("📥 Baixar Backup Financeiro (CSV)", csv, "financeiro_lian_car.csv", "text/csv")
        else:
            st.info("Nenhum registro encontrado.")

# ======================================================
# AGENDAMENTOS E PÁTIO (SIMPLIFICADO)
# ======================================================
def agendamentos():
    st.title("📅 Agendamentos e Serviços")
    # Aqui você pode reutilizar o código de agendamento que enviamos anteriormente
    st.info("Módulo de agendamentos pronto para integração.")

# ======================================================
# MENU LATERAL
# ======================================================
st.sidebar.title("🧼 Lian Car")
if st.sidebar.button("Sair"):
    st.session_state.logado = False
    st.rerun()

menu = st.sidebar.radio("Navegação", ["Dashboard", "Financeiro", "Agendamentos"])

if menu == "Dashboard":
    dashboard()
elif menu == "Financeiro":
    financeiro()
elif menu == "Agendamentos":
    agendamentos()
