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
# FUNÇÕES UTILITÁRIAS
# ======================================================
def formatar_data_br(data_str):
    try:
        return datetime.strptime(data_str, "%Y-%m-%d").strftime("%d/%m/%Y")
    except:
        return data_str

def moeda(valor):
    return f"R$ {valor:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")

# ======================================================
# BANCO DE DADOS
# ======================================================
def get_connection():
    return sqlite3.connect("lian_car.db", check_same_thread=False)

def init_db():
    conn = get_connection()
    c = conn.cursor()

    c.execute("""
    CREATE TABLE IF NOT EXISTS financeiro (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        Data TEXT,
        Tipo TEXT,
        Descricao TEXT,
        Valor REAL
    )
    """)

    c.execute("""
    CREATE TABLE IF NOT EXISTS servicos (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        Nome TEXT,
        Valor REAL
    )
    """)

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

    c.execute("""
    CREATE TABLE IF NOT EXISTS estoque (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        Item TEXT,
        Quantidade INTEGER
    )
    """)

    c.execute("""
    CREATE TABLE IF NOT EXISTS fornecedores (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        Nome TEXT,
        Contato TEXT,
        Produto TEXT
    )
    """)

    conn.commit()
    conn.close()

init_db()

# ======================================================
# CSS
# ======================================================
st.markdown("""
<style>
.stApp {
    background: radial-gradient(circle at top, #020617, #000);
    color: #e5e7eb;
}
[data-testid="stMetric"] {
    background: #020617;
    padding: 20px;
    border-radius: 14px;
    border: 1px solid #1e293b;
}
.stButton>button {
    background: linear-gradient(135deg, #0ea5e9, #38bdf8);
    color: #020617;
    font-weight: bold;
    border-radius: 12px;
    width: 100%;
}
</style>
""", unsafe_allow_html=True)

# ======================================================
# LOGIN
# ======================================================
if "logado" not in st.session_state:
    st.session_state.logado = False

def login():
    st.title("🔐 Acesso Administrativo")
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
    c1.metric("💰 Faturamento", moeda(entradas))
    c2.metric("📉 Despesas", moeda(saidas))
    c3.metric("📈 Lucro", moeda(lucro))

# ======================================================
# FINANCEIRO
# ======================================================
def financeiro():
    st.title("💰 Financeiro")

    conn = get_connection()

    with st.form("lancamento"):
        tipo = st.selectbox("Tipo", ["ENTRADA", "SAIDA"])
        descricao = st.text_input("Descrição")
        valor = st.number_input("Valor (R$)", min_value=0.0)
        data = st.date_input("Data", date.today())

        if st.form_submit_button("Registrar"):
            conn.execute("""
                INSERT INTO financeiro (Data, Tipo, Descricao, Valor)
                VALUES (?,?,?,?)
            """, (data.isoformat(), tipo, descricao, valor))
            conn.commit()
            st.success("Lançamento registrado!")
            st.rerun()

    st.markdown("---")
    st.subheader("📋 Histórico")

    df = pd.read_sql("SELECT * FROM financeiro ORDER BY Data DESC", conn)
    conn.close()

    if df.empty:
        st.info("Nenhum lançamento.")
        return

    df["Data"] = df["Data"].apply(formatar_data_br)
    st.dataframe(df, use_container_width=True)

# ======================================================
# SERVIÇOS
# ======================================================
def servicos():
    st.title("🛠 Serviços")

    conn = get_connection()

    with st.form("novo_servico"):
        nome = st.text_input("Nome do Serviço")
        valor = st.number_input("Valor (R$)", min_value=0.0)
        if st.form_submit_button("Cadastrar"):
            conn.execute(
                "INSERT INTO servicos (Nome, Valor) VALUES (?,?)",
                (nome, valor)
            )
            conn.commit()
            st.rerun()

    st.dataframe(pd.read_sql("SELECT * FROM servicos", conn), use_container_width=True)
    conn.close()

# ======================================================
# MENU
# ======================================================
st.sidebar.title("🧼 Lian Car")
menu = st.sidebar.radio(
    "Menu",
    ["Dashboard", "Financeiro", "Serviços"]
)

pages = {
    "Dashboard": dashboard,
    "Financeiro": financeiro,
    "Serviços": servicos
}

pages[menu]()
