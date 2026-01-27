import streamlit as st
import pandas as pd
import sqlite3
from datetime import date

# ======================================================
# CONFIGURAÇÃO GERAL
# ======================================================
st.set_page_config(
    page_title="Lian Car | Gestão Automotiva",
    page_icon="🧼",
    layout="wide"
)

DB_NAME = "lian_car.db"

# ======================================================
# BANCO DE DADOS
# ======================================================
def get_connection():
    return sqlite3.connect(DB_NAME, check_same_thread=False)

def init_db():
    conn = get_connection()
    c = conn.cursor()

    c.execute("""
        CREATE TABLE IF NOT EXISTS servicos (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            Nome TEXT UNIQUE,
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
        CREATE TABLE IF NOT EXISTS despesas (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            Data TEXT,
            Descricao TEXT,
            Valor REAL
        )
    """)

    c.execute("""
        CREATE TABLE IF NOT EXISTS estoque (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            Item TEXT,
            Qtd INTEGER
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
# ESTILO (CSS)
# ======================================================
st.markdown("""
<style>
:root {
    --bg: #020617;
    --card: #020617;
    --border: #1e293b;
    --primary: #0ea5e9;
    --success: #22c55e;
    --warning: #facc15;
}
.stApp {
    background: radial-gradient(circle at top, #020617, #000000);
    color: #e5e7eb;
}
[data-testid="stMetric"] {
    background: var(--card);
    padding: 20px;
    border-radius: 16px;
    border: 1px solid var(--border);
}
.stButton>button {
    background: linear-gradient(135deg, var(--primary), #38bdf8);
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
    usuario = st.text_input("Usuário")
    senha = st.text_input("Senha", type="password")

    if st.button("Entrar"):
        if usuario == "admin" and senha == "admin123":
            st.session_state.logado = True
            st.rerun()
        else:
            st.error("Usuário ou senha inválidos")

if not st.session_state.logado:
    login()
    st.stop()

# ======================================================
# PÁGINAS
# ======================================================
def dashboard():
    st.title("📊 Dashboard")

    conn = get_connection()
    fat = pd.read_sql("SELECT SUM(Valor) AS total FROM agendamentos", conn)["total"][0] or 0
    desp = pd.read_sql("SELECT SUM(Valor) AS total FROM despesas", conn)["total"][0] or 0
    conn.close()

    c1, c2, c3 = st.columns(3)
    c1.metric("💰 Faturamento", f"R$ {fat:,.2f}")
    c2.metric("📉 Despesas", f"R$ {desp:,.2f}")
    c3.metric("📈 Lucro", f"R$ {fat - desp:,.2f}")

def servicos():
    st.title("🛠️ Serviços")

    conn = get_connection()

    with st.form("novo_servico"):
        nome = st.text_input("Nome do Serviço")
        valor = st.number_input("Valor (R$)", min_value=0.0)
        if st.form_submit_button("Cadastrar Serviço"):
            try:
                conn.execute("INSERT INTO servicos (Nome, Valor) VALUES (?,?)", (nome, valor))
                conn.commit()
                st.success("Serviço cadastrado")
                st.rerun()
            except:
                st.warning("Serviço já existe")

    st.subheader("Serviços Cadastrados")
    st.dataframe(pd.read_sql("SELECT * FROM servicos", conn), use_container_width=True)
    conn.close()

def agendamentos():
    st.title("📅 Agendamentos")

    conn = get_connection()
    df_serv = pd.read_sql("SELECT * FROM servicos", conn)

    if df_serv.empty:
        st.warning("Cadastre serviços antes de agendar")
        return

    with st.form("novo_agendamento"):
        cliente = st.text_input("Cliente")
        placa = st.text_input("Placa do Veículo")
        servico = st.selectbox("Serviço", df_serv["Nome"])
        valor_padrao = df_serv[df_serv["Nome"] == servico]["Valor"].values[0]
        valor = st.number_input("Valor (R$)", value=float(valor_padrao))
        data = st.date_input("Data", date.today())

        if st.form_submit_button("Confirmar"):
            conn.execute("""
                INSERT INTO agendamentos (Data, Cliente, Placa, Servico, Valor, Status)
                VALUES (?,?,?,?,?,?)
            """, (data.isoformat(), cliente, placa, servico, valor, "Agendado"))
            conn.commit()
            st.success("Agendamento realizado")
            st.rerun()

    conn.close()

def patio():
    st.title("🚗 Pátio")

    conn = get_connection()
    df = pd.read_sql("SELECT * FROM agendamentos WHERE Status != 'Concluído'", conn)

    for _, row in df.iterrows():
        col1, col2 = st.columns([4, 1])
        col1.markdown(f"**{row['Placa']}** | {row['Cliente']} | {row['Servico']}")
        novo = col2.selectbox(
            "Status",
            ["Agendado", "Lavando", "Concluído"],
            index=["Agendado", "Lavando", "Concluído"].index(row["Status"]),
            key=row["id"]
        )
        if novo != row["Status"]:
            conn.execute("UPDATE agendamentos SET Status=? WHERE id=?", (novo, row["id"]))
            conn.commit()
            st.rerun()

    conn.close()

def financeiro():
    st.title("💰 Financeiro")

    with st.form("despesa"):
        desc = st.text_input("Descrição")
        valor = st.number_input("Valor (R$)", min_value=0.0)
        data = st.date_input("Data", date.today())
        if st.form_submit_button("Salvar"):
            conn = get_connection()
            conn.execute(
                "INSERT INTO despesas (Data, Descricao, Valor) VALUES (?,?,?)",
                (data.isoformat(), desc, valor)
            )
            conn.commit()
            conn.close()
            st.rerun()

    conn = get_connection()
    st.dataframe(pd.read_sql("SELECT * FROM despesas", conn), use_container_width=True)
    conn.close()

def relatorios():
    st.title("📄 Relatórios")

    conn = get_connection()
    df_ag = pd.read_sql("SELECT * FROM agendamentos", conn)
    df_dp = pd.read_sql("SELECT * FROM despesas", conn)
    conn.close()

    st.subheader("Agendamentos")
    st.dataframe(df_ag, use_container_width=True)

    st.download_button(
        "📥 Baixar Agendamentos (CSV)",
        df_ag.to_csv(index=False).encode("utf-8"),
        "agendamentos.csv"
    )

    st.download_button(
        "📥 Baixar Despesas (CSV)",
        df_dp.to_csv(index=False).encode("utf-8"),
        "despesas.csv"
    )

# ======================================================
# MENU
# ======================================================
st.sidebar.title("Lian Car")
menu = st.sidebar.radio(
    "Menu",
    ["Dashboard", "Serviços", "Agendamentos", "Pátio", "Financeiro", "Relatórios"]
)

paginas = {
    "Dashboard": dashboard,
    "Serviços": servicos,
    "Agendamentos": agendamentos,
    "Pátio": patio,
    "Financeiro": financeiro,
    "Relatórios": relatorios
}

paginas[menu]()
