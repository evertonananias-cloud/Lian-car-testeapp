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
    c.execute('''CREATE TABLE IF NOT EXISTS agendamentos 
                 (id INTEGER PRIMARY KEY AUTOINCREMENT, Data TEXT, Cliente TEXT, 
                  Placa TEXT, Servico TEXT, Valor REAL, Status TEXT)''')
    c.execute('''CREATE TABLE IF NOT EXISTS despesas 
                 (id INTEGER PRIMARY KEY AUTOINCREMENT, Data TEXT, Descricao TEXT, Valor REAL)''')
    c.execute('''CREATE TABLE IF NOT EXISTS estoque 
                 (id INTEGER PRIMARY KEY AUTOINCREMENT, Item TEXT, Qtd INTEGER)''')
    c.execute('''CREATE TABLE IF NOT EXISTS fornecedores 
                 (id INTEGER PRIMARY KEY AUTOINCREMENT, Nome TEXT, Contato TEXT, Produto TEXT)''')
    conn.commit()
    conn.close()

init_db()

# ======================================================
# CSS PROFISSIONAL (FRONT-END)
# ======================================================
st.markdown("""
<style>
:root {
    --bg: #020617; --card: #020617; --border: #1e293b;
    --primary: #0ea5e9; --success: #22c55e; --warning: #facc15; --danger: #ef4444;
}
.stApp { background: radial-gradient(circle at top, #020617, #000000); color: #e5e7eb; }
[data-testid="stMetric"] { background: var(--card); padding: 22px; border-radius: 16px; border: 1px solid var(--border); box-shadow: 0 10px 30px rgba(0,0,0,.4); }
.stButton>button { background: linear-gradient(135deg, var(--primary), #38bdf8); color: #020617; border-radius: 12px; font-weight: bold; width: 100%; }
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
    col1, col2 = st.columns([1,1])
    with col1:
        usuario = st.text_input("Usuário")
        senha = st.text_input("Senha", type="password")
        if st.button("Entrar"):
            if usuario == "admin" and senha == "admin123":
                st.session_state.logado = True
                st.rerun()
            else:
                st.error("Credenciais Inválidas")

if not st.session_state.logado:
    login()
    st.stop()

# ======================================================
# FUNÇÕES DE PÁGINAS
# ======================================================
def dashboard():
    st.title("📊 Visão Geral")
    conn = get_connection()
    df_serv = pd.read_sql("SELECT Valor FROM agendamentos", conn)
    df_desp = pd.read_sql("SELECT Valor FROM despesas", conn)
    conn.close()
    
    fat = df_serv["Valor"].sum()
    desp = df_desp["Valor"].sum()
    
    c1, c2, c3 = st.columns(3)
    c1.metric("💰 Faturamento", f"R$ {fat:,.2f}")
    c2.metric("📉 Despesas", f"R$ {desp:,.2f}")
    c3.metric("📈 Lucro", f"R$ {fat-desp:,.2f}")

def agendamentos():
    st.title("📅 Novo Agendamento")
    with st.form("form_agend"):
        c1, c2 = st.columns(2)
        cliente = c1.text_input("Nome do Cliente")
        placa = c2.text_input("Placa")
        servico = st.selectbox("Serviço", ["Lavagem Simples", "Lavagem Completa", "Higienização", "Polimento"])
        valor = st.number_input("Valor Cobrado (R$)", min_value=0.0)
        data = st.date_input("Data", date.today())
        if st.form_submit_button("Confirmar Agendamento"):
            conn = get_connection()
            conn.execute("INSERT INTO agendamentos (Data, Cliente, Placa, Servico, Valor, Status) VALUES (?,?,?,?,?,?)",
                         (data.isoformat(), cliente, placa, servico, valor, "Agendado"))
            conn.commit()
            conn.close()
            st.success("Cadastrado com sucesso!")
            st.rerun()

def patio():
    st.title("🚗 Pátio Operacional")
    conn = get_connection()
    df = pd.read_sql("SELECT * FROM agendamentos WHERE Status != 'Concluído'", conn)
    if df.empty:
        st.info("Pátio vazio.")
    else:
        for _, row in df.iterrows():
            with st.container():
                col_info, col_status = st.columns([3, 1])
                col_info.markdown(f"**{row['Placa']}** | {row['Cliente']} | {row['Servico']}")
                novo = col_status.selectbox("Status", ["Agendado", "Lavando", "Concluído"], index=["Agendado", "Lavando", "Concluído"].index(row['Status']), key=f"p_{row['id']}")
                if novo != row['Status']:
                    conn.execute("UPDATE agendamentos SET Status = ? WHERE id = ?", (novo, row['id']))
                    conn.commit()
                    st.rerun()
    conn.close()

def financeiro():
    st.title("💰 Gestão Financeira")
    with st.expander("💸 Registrar Nova Despesa"):
        with st.form("desp"):
            desc = st.text_input("Descrição da Despesa")
            v = st.number_input("Valor (R$)", min_value=0.0)
            d = st.date_input("Data", date.today())
            if st.form_submit_button("Salvar Despesa"):
                conn = get_connection()
                conn.execute("INSERT INTO despesas (Data, Descricao, Valor) VALUES (?,?,?)", (d.isoformat(), desc, v))
                conn.commit()
                conn.close()
                st.rerun()
    
    st.subheader("Histórico de Gastos")
    conn = get_connection()
    st.dataframe(pd.read_sql("SELECT * FROM despesas ORDER BY id DESC", conn), use_container_width=True)
    conn.close()

def relatorios():
    st.title("📄 Relatórios e Backup")
    conn = get_connection()
    df_serv = pd.read_sql("SELECT * FROM agendamentos", conn)
    df_desp = pd.read_sql("SELECT * FROM despesas", conn)
    conn.close()

    st.subheader("Todos os Serviços")
    st.dataframe(df_serv, use_container_width=True)

    # --- SEÇÃO DE BACKUP ---
    st.markdown("---")
    st.subheader("💾 Backup de Segurança (Baixar Dados)")
    st.info("Recomenda-se baixar estes ficheiros semanalmente para manter uma cópia fora do sistema.")
    
    col_b1, col_b2 = st.columns(2)
    with col_b1:
        csv_s = df_serv.to_csv(index=False).encode('utf-8')
        st.download_button("📥 Baixar Serviços (CSV)", data=csv_s, file_name=f"liancar_servicos_{date.today()}.csv", mime='text/csv')
    with col_b2:
        csv_d = df_desp.to_csv(index=False).encode('utf-8')
        st.download_button("📥 Baixar Despesas (CSV)", data=csv_d, file_name=f"liancar_despesas_{date.today()}.csv", mime='text/csv')

def estoque_fornecedores():
    st.title("📦 Stock e Fornecedores")
    tab1, tab2 = st.tabs(["Produtos", "Fornecedores"])
    conn = get_connection()
    
    with tab1:
        with st.form("add_stock"):
            item = st.text_input("Nome do Produto")
            q = st.number_input("Qtd", min_value=0)
            if st.form_submit_button("Adicionar"):
                conn.execute("INSERT INTO estoque (Item, Qtd) VALUES (?,?)", (item, q))
                conn.commit()
                st.rerun()
        st.dataframe(pd.read_sql("SELECT * FROM estoque", conn), use_container_width=True)

    with tab2:
        with st.form("add_forn"):
            f = st.text_input("Fornecedor")
            c = st.text_input("Contacto")
            p = st.text_input("O que fornece?")
            if st.form_submit_button("Cadastrar"):
                conn.execute("INSERT INTO fornecedores (Nome, Contato, Produto) VALUES (?,?,?)", (f, c, p))
                conn.commit()
                st.rerun()
        st.dataframe(pd.read_sql("SELECT * FROM fornecedores", conn), use_container_width=True)
    conn.close()

# ======================================================
# MENU E NAVEGAÇÃO
# ======================================================
st.sidebar.title("Lian Car")
menu = st.sidebar.radio("Navegação", ["Dashboard", "Agendamentos", "Pátio", "Financeiro", "Relatórios", "Stock"])

paginas = {
    "Dashboard": dashboard, "Agendamentos": agendamentos, "Pátio": patio,
    "Financeiro": financeiro, "Relatórios": relatorios, "Stock": estoque_fornecedores
}
paginas[menu]()
