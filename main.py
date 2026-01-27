import streamlit as st
import pandas as pd
import sqlite3
from datetime import date

# ======================================================
# CONFIGURAÇÃO GERAL
# ======================================================
st.set_page_config(
    page_title="Lian Car | Gestão Automotiva",
    page_icon="🧼🚿🚙",
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
    c.execute("CREATE TABLE IF NOT EXISTS servicos (id INTEGER PRIMARY KEY AUTOINCREMENT, Nome TEXT UNIQUE, Valor REAL)")
    c.execute("CREATE TABLE IF NOT EXISTS agendamentos (id INTEGER PRIMARY KEY AUTOINCREMENT, Data TEXT, Cliente TEXT, Placa TEXT, Servico TEXT, Valor REAL, Status TEXT)")
    c.execute("CREATE TABLE IF NOT EXISTS despesas (id INTEGER PRIMARY KEY AUTOINCREMENT, Data TEXT, Descricao TEXT, Valor REAL)")
    c.execute("CREATE TABLE IF NOT EXISTS estoque (id INTEGER PRIMARY KEY AUTOINCREMENT, Item TEXT, Qtd INTEGER)")
    c.execute("CREATE TABLE IF NOT EXISTS fornecedores (id INTEGER PRIMARY KEY AUTOINCREMENT, Nome TEXT, Contato TEXT, Produto TEXT)")
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
    --card: #0f172a;
    --border: #1e293b;
    --primary: #0ea5e9;
    --success: #22c55e;
    --danger: #ef4444;
}
.stApp { background: radial-gradient(circle at top, #020617, #000000); color: #e5e7eb; }
[data-testid="stMetric"] { background: var(--card); padding: 20px; border-radius: 16px; border: 1px solid var(--border); }
.stButton>button { background: linear-gradient(135deg, var(--primary), #38bdf8); color: white; font-weight: bold; border-radius: 12px; width: 100%; }
</style>
""", unsafe_allow_html=True)

# ======================================================
# LOGIN
# ======================================================
if "logado" not in st.session_state:
    st.session_state.logado = False

if not st.session_state.logado:
    st.title("🔐 Acesso Administrativo")
    u, p = st.text_input("Usuário"), st.text_input("Senha", type="password")
    if st.button("Entrar"):
        if u == "admin" and p == "admin123":
            st.session_state.logado = True
            st.rerun()
        else: st.error("Incorreto")
    st.stop()

# ======================================================
# MÓDULOS DE PÁGINAS
# ======================================================

def dashboard():
    st.title("📊 Dashboard")
    conn = get_connection()
    # Entradas são serviços concluídos
    entradas = pd.read_sql("SELECT SUM(Valor) FROM agendamentos WHERE Status='Concluído'", conn).iloc[0,0] or 0
    saidas = pd.read_sql("SELECT SUM(Valor) FROM despesas", conn).iloc[0,0] or 0
    conn.close()

    c1, c2, c3 = st.columns(3)
    c1.metric("💰 Faturamento (Concluído)", f"R$ {entradas:,.2f}")
    c2.metric("📉 Despesas Totais", f"R$ {saidas:,.2f}")
    c3.metric("📈 Lucro Líquido", f"R$ {entradas - saidas:,.2f}")

def servicos():
    st.title("🛠️ Gestão de Serviços")
    conn = get_connection()
    with st.form("cad_serv"):
        n = st.text_input("Nome do Serviço")
        v = st.number_input("Valor Padrão (R$)", min_value=0.0)
        if st.form_submit_button("Salvar Serviço"):
            try:
                conn.execute("INSERT INTO servicos (Nome, Valor) VALUES (?,?)", (n, v))
                conn.commit()
                st.success("Cadastrado!")
                st.rerun()
            except: st.warning("Já cadastrado.")
    st.dataframe(pd.read_sql("SELECT * FROM servicos", conn), use_container_width=True)
    conn.close()

def agendamentos():
    st.title("📅 Agendamentos")
    conn = get_connection()
    df_s = pd.read_sql("SELECT * FROM servicos", conn)
    if df_s.empty: st.warning("Cadastre serviços primeiro."); return

    with st.form("add_ag"):
        cli, pla = st.text_input("Cliente"), st.text_input("Placa")
        serv = st.selectbox("Serviço", df_s["Nome"])
        v_sug = df_s[df_s["Nome"] == serv]["Valor"].values[0]
        val = st.number_input("Valor Final (R$)", value=float(v_sug))
        dt = st.date_input("Data", date.today())
        if st.form_submit_button("Agendar"):
            conn.execute("INSERT INTO agendamentos (Data, Cliente, Placa, Servico, Valor, Status) VALUES (?,?,?,?,?,?)",
                         (dt.isoformat(), cli, pla, serv, val, "Agendado"))
            conn.commit()
            st.rerun()
    conn.close()

def patio():
    st.title("🚗 Pátio Operacional")
    conn = get_connection()
    df = pd.read_sql("SELECT * FROM agendamentos WHERE Status != 'Concluído'", conn)
    for _, row in df.iterrows():
        c1, c2 = st.columns([4, 1])
        c1.info(f"**{row['Placa']}** | {row['Cliente']} | {row['Servico']}")
        novo = c2.selectbox("Mudar Status", ["Agendado", "Lavando", "Concluído"], 
                            index=["Agendado", "Lavando", "Concluído"].index(row["Status"]), key=row["id"])
        if novo != row["Status"]:
            conn.execute("UPDATE agendamentos SET Status=? WHERE id=?", (novo, row["id"]))
            conn.commit()
            st.rerun()
    conn.close()

def financeiro():
    st.title("💰 Fluxo de Caixa")
    col_a, col_b = st.columns(2)
    ini, fim = col_a.date_input("De", date.today().replace(day=1)), col_b.date_input("Até", date.today())

    conn = get_connection()
    # Entradas: Agendamentos concluídos no período
    df_e = pd.read_sql(f"SELECT Data, Cliente || ' (' || Servico || ')' as Descricao, Valor, 'Entrada' as Tipo FROM agendamentos WHERE Status='Concluído' AND Data BETWEEN '{ini.isoformat()}' AND '{fim.isoformat()}'", conn)
    # Saídas: Despesas no período
    df_s = pd.read_sql(f"SELECT Data, Descricao, Valor, 'Saída' as Tipo FROM despesas WHERE Data BETWEEN '{ini.isoformat()}' AND '{fim.isoformat()}'", conn)
    
    fluxo = pd.concat([df_e, df_s]).sort_values("Data", ascending=False)
    
    m1, m2, m3 = st.columns(3)
    m1.metric("Entradas", f"R$ {df_e['Valor'].sum():,.2f}")
    m2.metric("Saídas", f"R$ {df_s['Valor'].sum():,.2f}")
    m3.metric("Saldo", f"R$ {df_e['Valor'].sum() - df_s['Valor'].sum():,.2f}")

    st.divider()
    with st.expander("➕ Registrar Saída Manual"):
        with st.form("add_desp"):
            desc, v_d = st.text_input("Descrição"), st.number_input("Valor (R$)", min_value=0.0)
            if st.form_submit_button("Lançar Saída"):
                conn.execute("INSERT INTO despesas (Data, Descricao, Valor) VALUES (?,?,?)", (date.today().isoformat(), desc, v_d))
                conn.commit()
                st.rerun()

    st.dataframe(fluxo, use_container_width=True)
    conn.close()

def relatorios():
    st.title("📄 Relatórios Exportáveis")
    conn = get_connection()
    df_ag = pd.read_sql("SELECT * FROM agendamentos", conn)
    st.dataframe(df_ag, use_container_width=True)
    st.download_button("Baixar Dados (CSV)", df_ag.to_csv(index=False).encode("utf-8"), "liancar_dados.csv")
    conn.close()

# ======================================================
# MENU E NAVEGAÇÃO
# ======================================================
st.sidebar.image("https://cdn-icons-png.flaticon.com/512/2966/2966480.png", width=100)
st.sidebar.title("Lian Car")
menu = st.sidebar.radio("Navegação", ["Dashboard", "Serviços", "Agendamentos", "Pátio", "Financeiro", "Relatórios"])

paginas = {
    "Dashboard": dashboard, "Serviços": servicos, "Agendamentos": agendamentos,
    "Pátio": patio, "Financeiro": financeiro, "Relatórios": relatorios
}
paginas[menu]()
