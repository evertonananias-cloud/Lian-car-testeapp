import streamlit as st
import pandas as pd
import sqlite3
from datetime import datetime, date

# ======================================================
# CONFIGURAÇÃO E BANCO DE DADOS
# ======================================================
st.set_page_config(
    page_title="Lian Car | Gestão Automotiva",
    page_icon="🧼",
    layout="wide"
)

def get_connection():
    return sqlite3.connect('lian_car_oficial.db', check_same_thread=False)

def init_db():
    conn = get_connection()
    c = conn.cursor()
    # Tabela de Agendamentos/Serviços
    c.execute('''CREATE TABLE IF NOT EXISTS agendamentos 
                 (id INTEGER PRIMARY KEY AUTOINCREMENT, Data TEXT, Cliente TEXT, 
                  Placa TEXT, Servico TEXT, Valor REAL, Status TEXT)''')
    # Tabela de Despesas
    c.execute('''CREATE TABLE IF NOT EXISTS despesas 
                 (id INTEGER PRIMARY KEY AUTOINCREMENT, Data TEXT, Descricao TEXT, Valor REAL)''')
    # Tabela de Estoque
    c.execute('''CREATE TABLE IF NOT EXISTS estoque 
                 (id INTEGER PRIMARY KEY AUTOINCREMENT, Item TEXT, Qtd INTEGER)''')
    # Tabela de Fornecedores
    c.execute('''CREATE TABLE IF NOT EXISTS fornecedores 
                 (id INTEGER PRIMARY KEY AUTOINCREMENT, Nome TEXT, Contato TEXT, Produto TEXT)''')
    conn.commit()
    conn.close()

init_db()

# ======================================================
# CSS PROFISSIONAL
# ======================================================
st.markdown("""
<style>
:root {
    --bg: #020617; --card: #020617; --border: #1e293b;
    --primary: #0ea5e9; --success: #22c55e; --warning: #facc15; --danger: #ef4444;
}
.stApp { background: radial-gradient(circle at top, #020617, #000000); color: #e5e7eb; }
[data-testid="stMetric"] { background: var(--card); padding: 22px; border-radius: 16px; border: 1px solid var(--border); }
.stButton>button { background: linear-gradient(135deg, var(--primary), #38bdf8); color: #020617; border-radius: 12px; }
.status-agendado { color: var(--warning); font-weight: bold; }
.status-lavando { color: var(--primary); font-weight: bold; }
.status-concluido { color: var(--success); font-weight: bold; }
</style>
""", unsafe_allow_html=True)

# ======================================================
# LOGIN
# ======================================================
if "logado" not in st.session_state:
    st.session_state.logado = False

def login():
    st.title("🔐 Acesso ao Sistema")
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
# DASHBOARD
# ======================================================
def dashboard():
    st.title("📊 Visão Geral")
    conn = get_connection()
    df_serv = pd.read_sql("SELECT Valor FROM agendamentos", conn)
    df_desp = pd.read_sql("SELECT Valor FROM despesas", conn)
    conn.close()

    fat = df_serv["Valor"].sum()
    desp = df_desp["Valor"].sum()
    lucro = fat - desp

    c1, c2, c3 = st.columns(3)
    c1.metric("💰 Faturamento", f"R$ {fat:,.2f}")
    c2.metric("📉 Despesas", f"R$ {desp:,.2f}")
    c3.metric("📈 Lucro", f"R$ {lucro:,.2f}")

# ======================================================
# AGENDAMENTOS
# ======================================================
def agendamentos():
    st.title("📅 Agendamentos")
    with st.form("novo_agendamento"):
        cliente = st.text_input("Cliente")
        placa = st.text_input("Placa do Veículo")
        servico = st.text_input("Serviço")
        valor = st.number_input("Valor", min_value=0.0)
        data = st.date_input("Data", date.today())
        if st.form_submit_button("Cadastrar"):
            conn = get_connection()
            c = conn.cursor()
            c.execute("INSERT INTO agendamentos (Data, Cliente, Placa, Servico, Valor, Status) VALUES (?,?,?,?,?,?)",
                      (data.isoformat(), cliente, placa, servico, valor, "Agendado"))
            conn.commit()
            conn.close()
            st.success("Agendamento criado!")
            st.rerun()

    st.divider()
    conn = get_connection()
    df = pd.read_sql("SELECT * FROM agendamentos ORDER BY id DESC", conn)
    conn.close()
    st.dataframe(df, use_container_width=True)

# ======================================================
# PÁTIO
# ======================================================
def patio():
    st.title("🚗 Pátio Operacional")
    conn = get_connection()
    df = pd.read_sql("SELECT * FROM agendamentos WHERE Status != 'Concluído'", conn)
    
    if df.empty:
        st.info("Nenhum veículo em processo")
        return

    for _, row in df.iterrows():
        classe = {"Agendado": "status-agendado", "Lavando": "status-lavando"}.get(row['Status'], "")
        st.markdown(f"<b>{row['Placa']}</b> ({row['Cliente']}) — <span class='{classe}'>● {row['Status']}</span>", unsafe_allow_html=True)
