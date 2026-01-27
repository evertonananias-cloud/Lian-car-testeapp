import streamlit as st
import pandas as pd
import sqlite3
from datetime import date

# ======================================================
# CONFIGURAÇÃO GERAL
# ======================================================
st.set_page_config(
    page_title="Lian Car | Gestão 360",
    page_icon="🧼🚘🚿✨️",
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
            Fabricante TEXT,
            Modelo TEXT,
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
# CSS
# ======================================================
st.markdown("""
<style>
.stApp { background: radial-gradient(circle at top, #020617, #000); color: #e5e7eb; }
[data-testid="stMetric"] { background: #0f172a; border-radius: 14px; padding: 18px; }
.stButton>button { background: linear-gradient(135deg, #0ea5e9, #38bdf8); border-radius: 10px; font-weight: bold; width: 100%; }
.card-veiculo { background:#1e293b; padding:1.2rem; border-radius:12px; border-left:6px solid #0ea5e9; }
</style>
""", unsafe_allow_html=True)

# ======================================================
# LOGIN
# ======================================================
if "logado" not in st.session_state:
    st.session_state.logado = False

if not st.session_state.logado:
    st.title("🔐 Acesso Lian Car")
    usuario = st.text_input("Usuário")
    senha = st.text_input("Senha", type="password")

    if st.button("Entrar"):
        if usuario == "admin" and senha == "admin123":
            st.session_state.logado = True
            st.rerun()
        else:
            st.error("Credenciais inválidas")
    st.stop()

# ======================================================
# DASHBOARD
# ======================================================
def dashboard():
    st.title("📊 Painel de Controle")
    conn = get_connection()

    entradas = pd.read_sql(
        "SELECT SUM(Valor) FROM agendamentos WHERE Status='Concluído'", conn
    ).iloc[0, 0] or 0

    saidas = pd.read_sql(
        "SELECT SUM(Valor) FROM despesas", conn
    ).iloc[0, 0] or 0

    conn.close()

    c1, c2, c3 = st.columns(3)
    c1.metric("💰 Faturamento", f"R$ {entradas:,.2f}")
    c2.metric("📉 Despesas", f"R$ {saidas:,.2f}")
    c3.metric("📈 Lucro", f"R$ {entradas - saidas:,.2f}")

# ======================================================
# SERVIÇOS
# ======================================================
def servicos():
    st.title("🛠 Serviços")
    conn = get_connection()

    with st.form("cad_serv"):
        nome = st.text_input("Nome do Serviço")
        valor = st.number_input("Valor (R$)", min_value=0.0)
        if st.form_submit_button("Salvar"):
            try:
                conn.execute(
                    "INSERT INTO servicos (Nome, Valor) VALUES (?,?)",
                    (nome, valor)
                )
                conn.commit()
                st.success("Serviço cadastrado!")
                st.rerun()
            except:
                st.warning("Serviço já existe.")

    st.dataframe(pd.read_sql("SELECT * FROM servicos", conn), use_container_width=True)
    conn.close()

# ======================================================
# AGENDAMENTOS (CORRIGIDO)
# ======================================================
def agendamentos():
    st.title("📅 Novo Agendamento")
    conn = get_connection()
    df_s = pd.read_sql("SELECT * FROM servicos", conn)

    if df_s.empty:
        st.warning("Cadastre serviços antes de agendar.")
        conn.close()
        return

    with st.form("add_ag"):
        col1, col2 = st.columns(2)

        with col1:
            cli = st.text_input("Cliente")
            pla = st.text_input("Placa")

        with col2:
            fabricante = st.text_input("Fabricante")
            modelo = st.text_input("Modelo do Veículo")

        serv = st.selectbox("Serviço", df_s["Nome"])
        valor_padrao = float(df_s[df_s["Nome"] == serv]["Valor"].values[0])
        val = st.number_input("Valor Cobrado (R$)", value=valor_padrao)
        dt = st.date_input("Data", date.today())

        if st.form_submit_button("Confirmar Agendamento"):
            conn.execute("""
                INSERT INTO agendamentos
                (Data, Cliente, Placa, Fabricante, Modelo, Servico, Valor, Status)
                VALUES (?,?,?,?,?,?,?,?)
            """, (
                dt.isoformat(),
                cli,
                pla,
                fabricante,
                modelo,
                serv,
                val,
                "Agendado"
            ))
            conn.commit()
            st.success("Agendamento realizado!")
            st.rerun()

    conn.close()

# ======================================================
# PÁTIO
# ======================================================
def patio():
    st.title("🚗 Pátio")
    conn = get_connection()
    df = pd.read_sql(
        "SELECT * FROM agendamentos WHERE Status!='Concluído' ORDER BY id DESC",
        conn
    )

    if df.empty:
        st.info("Nenhum veículo no pátio.")
    else:
        for _, row in df.iterrows():
            col1, col2 = st.columns([3, 1])
            with col1:
                st.markdown(
                    f"<div class='card-veiculo'><b>{row['Placa']}</b><br>"
                    f"{row['Cliente']} — {row['Servico']}</div>",
                    unsafe_allow_html=True
                )
            with col2:
                novo = st.selectbox(
                    "Status",
                    ["Agendado", "Lavando", "Concluído"],
                    index=["Agendado", "Lavando", "Concluído"].index(row["Status"]),
                    key=row["id"]
                )
                if novo != row["Status"]:
                    conn.execute(
                        "UPDATE agendamentos SET Status=? WHERE id=?",
                        (novo, row["id"])
                    )
                    conn.commit()
                    st.rerun()

    conn.close()

# ======================================================
# FINANCEIRO
# ======================================================
def financeiro():
    st.title("💰 Financeiro")
    conn = get_connection()

    entradas = pd.read_sql(
        "SELECT SUM(Valor) FROM agendamentos WHERE Status='Concluído'", conn
    ).iloc[0, 0] or 0

    saidas = pd.read_sql(
        "SELECT SUM(Valor) FROM despesas", conn
    ).iloc[0, 0] or 0

    c1, c2, c3 = st.columns(3)
    c1.metric("Entradas", f"R$ {entradas:,.2f}")
    c2.metric("Saídas", f"R$ {saidas:,.2f}")
    c3.metric("Saldo", f"R$ {entradas - saidas:,.2f}")

    with st.form("nova_saida"):
        desc = st.text_input("Descrição")
        val = st.number_input("Valor", min_value=0.0)
        if st.form_submit_button("Registrar Saída"):
            conn.execute(
                "INSERT INTO despesas (Data, Descricao, Valor) VALUES (?,?,?)",
                (date.today().isoformat(), desc, val)
            )
            conn.commit()
            st.rerun()

    conn.close()

# ======================================================
# ESTOQUE / FORNECEDORES
# ======================================================
def estoque():
    st.title("📦 Estoque")
    conn = get_connection()
    with st.form("estoque"):
        it = st.text_input("Produto")
        qt = st.number_input("Quantidade", min_value=0)
        if st.form_submit_button("Salvar"):
            conn.execute("INSERT INTO estoque (Item, Qtd) VALUES (?,?)", (it, qt))
            conn.commit()
            st.rerun()
    st.dataframe(pd.read_sql("SELECT * FROM estoque", conn))
    conn.close()

def fornecedores():
    st.title("🏭 Fornecedores")
    conn = get_connection()
    with st.form("forn"):
        n = st.text_input("Nome")
        c = st.text_input("Contato")
        p = st.text_input("Produto")
        if st.form_submit_button("Cadastrar"):
            conn.execute(
                "INSERT INTO fornecedores (Nome, Contato, Produto) VALUES (?,?,?)",
                (n, c, p)
            )
            conn.commit()
            st.rerun()
    st.dataframe(pd.read_sql("SELECT * FROM fornecedores", conn))
    conn.close()

# ======================================================
# MENU
# ======================================================
menu = st.sidebar.radio(
    "Menu",
    ["Dashboard", "Serviços", "Agendamentos", "Pátio", "Financeiro", "Estoque", "Fornecedores"]
)

pages = {
    "Dashboard": dashboard,
    "Serviços": servicos,
    "Agendamentos": agendamentos,
    "Pátio": patio,
    "Financeiro": financeiro,
    "Estoque": estoque,
    "Fornecedores": fornecedores
}

pages[menu]()
