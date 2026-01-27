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
# CSS PROFISSIONAL
# ======================================================
st.markdown("""
<style>
.stApp {
    background: radial-gradient(circle at top, #020617, #000000);
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
    border-radius: 12px;
    font-weight: bold;
    width: 100%;
}
</style>
""", unsafe_allow_html=True)

# ======================================================
# LOGIN SIMPLES
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
# DASHBOARD
# ======================================================
def dashboard():
    st.title("📊 Dashboard")

    conn = get_connection()
    df_fat = pd.read_sql("SELECT Valor FROM agendamentos", conn)
    df_desp = pd.read_sql("SELECT Valor FROM despesas", conn)
    conn.close()

    faturamento = df_fat["Valor"].sum() if not df_fat.empty else 0
    despesas = df_desp["Valor"].sum() if not df_desp.empty else 0
    lucro = faturamento - despesas

    c1, c2, c3 = st.columns(3)
    c1.metric("💰 Faturamento", moeda(faturamento))
    c2.metric("📉 Despesas", moeda(despesas))
    c3.metric("📈 Lucro", moeda(lucro))

# ======================================================
# SERVIÇOS (CADASTRO)
# ======================================================
def servicos():
    st.title("🛠 Serviços")

    conn = get_connection()

    with st.form("novo_servico"):
        nome = st.text_input("Nome do Serviço")
        valor = st.number_input("Valor (R$)", min_value=0.0)
        if st.form_submit_button("Cadastrar Serviço"):
            conn.execute(
                "INSERT INTO servicos (Nome, Valor) VALUES (?,?)",
                (nome, valor)
            )
            conn.commit()
            st.success("Serviço cadastrado!")
            st.rerun()

    df = pd.read_sql("SELECT * FROM servicos", conn)
    conn.close()
    st.dataframe(df, use_container_width=True)

# ======================================================
# AGENDAMENTOS
# ======================================================
def agendamentos():
    st.title("📅 Agendamentos")

    conn = get_connection()
    df_serv = pd.read_sql("SELECT * FROM servicos", conn)

    if df_serv.empty:
        st.warning("Cadastre serviços antes de agendar.")
        return

    with st.form("novo_agendamento"):
        cliente = st.text_input("Cliente")
        placa = st.text_input("Placa")
        servico = st.selectbox("Serviço", df_serv["Nome"])
        valor = float(df_serv[df_serv["Nome"] == servico]["Valor"].values[0])
        data = st.date_input("Data", date.today())

        if st.form_submit_button("Confirmar"):
            conn.execute("""
                INSERT INTO agendamentos 
                (Data, Cliente, Placa, Servico, Valor, Status)
                VALUES (?,?,?,?,?,?)
            """, (data.isoformat(), cliente, placa, servico, valor, "Agendado"))
            conn.commit()
            st.success("Agendamento criado!")
            st.rerun()

    df = pd.read_sql("SELECT * FROM agendamentos", conn)
    conn.close()
    df["Data"] = df["Data"].apply(formatar_data_br)
    st.dataframe(df, use_container_width=True)

# ======================================================
# PÁTIO
# ======================================================
def patio():
    st.title("🚗 Pátio")

    conn = get_connection()
    df = pd.read_sql("SELECT * FROM agendamentos WHERE Status != 'Concluído'", conn)

    if df.empty:
        st.info("Nenhum veículo no pátio.")
        return

    for _, row in df.iterrows():
        col1, col2 = st.columns([3,1])
        col1.markdown(
            f"**{row['Placa']}** | {row['Cliente']} | {row['Servico']} | 📅 {formatar_data_br(row['Data'])}"
        )
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

# ======================================================
# FINANCEIRO
# ======================================================
def financeiro():
    st.title("💰 Financeiro")

    with st.form("nova_despesa"):
        desc = st.text_input("Descrição")
        valor = st.number_input("Valor", min_value=0.0)
        data = st.date_input("Data", date.today())
        if st.form_submit_button("Registrar"):
            conn = get_connection()
            conn.execute(
                "INSERT INTO despesas (Data, Descricao, Valor) VALUES (?,?,?)",
                (data.isoformat(), desc, valor)
            )
            conn.commit()
            conn.close()
            st.rerun()

    conn = get_connection()
    df = pd.read_sql("SELECT * FROM despesas", conn)
    conn.close()
    df["Data"] = df["Data"].apply(formatar_data_br)
    st.dataframe(df, use_container_width=True)

# ======================================================
# ESTOQUE E FORNECEDORES
# ======================================================
def estoque_fornecedores():
    st.title("📦 Estoque & Fornecedores")
    tab1, tab2 = st.tabs(["Estoque", "Fornecedores"])
    conn = get_connection()

    with tab1:
        with st.form("estoque"):
            item = st.text_input("Produto")
            qtd = st.number_input("Quantidade", min_value=0)
            if st.form_submit_button("Adicionar"):
                conn.execute(
                    "INSERT INTO estoque (Item, Quantidade) VALUES (?,?)",
                    (item, qtd)
                )
                conn.commit()
                st.rerun()
        st.dataframe(pd.read_sql("SELECT * FROM estoque", conn), use_container_width=True)

    with tab2:
        with st.form("fornecedor"):
            nome = st.text_input("Fornecedor")
            contato = st.text_input("Contato")
            produto = st.text_input("Produto fornecido")
            if st.form_submit_button("Cadastrar"):
                conn.execute(
                    "INSERT INTO fornecedores (Nome, Contato, Produto) VALUES (?,?,?)",
                    (nome, contato, produto)
                )
                conn.commit()
                st.rerun()
        st.dataframe(pd.read_sql("SELECT * FROM fornecedores", conn), use_container_width=True)

    conn.close()

# ======================================================
# RELATÓRIOS
# ======================================================
def relatorios():
    st.title("📄 Relatórios")

    conn = get_connection()
    df = pd.read_sql("SELECT * FROM agendamentos", conn)
    conn.close()

    df["Data"] = df["Data"].apply(formatar_data_br)
    st.dataframe(df, use_container_width=True)

    csv = df.to_csv(index=False).encode("utf-8")
    st.download_button(
        "📥 Baixar CSV",
        data=csv,
        file_name=f"relatorio_{date.today()}.csv",
        mime="text/csv"
    )

# ======================================================
# MENU
# ======================================================
st.sidebar.title("🧼 Lian Car")
menu = st.sidebar.radio(
    "Menu",
    ["Dashboard", "Serviços", "Agendamentos", "Pátio", "Financeiro", "Estoque", "Relatórios"]
)

pages = {
    "Dashboard": dashboard,
    "Serviços": servicos,
    "Agendamentos": agendamentos,
    "Pátio": patio,
    "Financeiro": financeiro,
    "Estoque": estoque_fornecedores,
    "Relatórios": relatorios
}

pages[menu]()
