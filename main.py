import streamlit as st
import pandas as pd
import sqlite3
from datetime import date

# ======================================================
# CONFIGURAÇÃO E BANCO DE DADOS
# ======================================================
st.set_page_config(page_title="Lian Car | Gestão 360", page_icon="🧼🚘🚿✨️", layout="wide")

DB_NAME = "lian_car.db"

def get_connection():
    return sqlite3.connect(DB_NAME, check_same_thread=False)

def init_db():
    conn = get_connection()
    c = conn.cursor()
    # Tabelas Essenciais
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
    :root { --primary: #0ea5e9; --bg-card: #1e293b; }
    .stApp { background: radial-gradient(circle at top, #020617, #000000); color: #e5e7eb; }
    .card-veiculo { background: var(--bg-card); padding: 1.5rem; border-radius: 12px; border-left: 6px solid var(--primary); margin-bottom: 1rem; }
    [data-testid="stMetric"] { background: #0f172a; border: 1px solid #334155; border-radius: 15px; }
    .stButton>button { background: linear-gradient(135deg, var(--primary), #38bdf8); color: white; border-radius: 10px; width: 100%; font-weight: bold; }
</style>
""", unsafe_allow_html=True)

# ======================================================
# SISTEMA DE LOGIN
# ======================================================
if "logado" not in st.session_state:
    st.session_state.logado = False

if not st.session_state.logado:
    st.title("🔐 Acesso Lian Car")
    col_l, col_r = st.columns([1,1])
    with col_l:
        u = st.text_input("Usuário")
        p = st.text_input("Senha", type="password")
        if st.button("Entrar"):
            if u == "admin" and p == "admin123":
                st.session_state.logado = True
                st.rerun()
            else: st.error("Credenciais inválidas")
    st.stop()

# ======================================================
# MÓDULOS DE PÁGINAS
# ======================================================

def dashboard():
    st.title("📊 Painel de Controle")
    conn = get_connection()
    entradas = pd.read_sql("SELECT SUM(Valor) FROM agendamentos WHERE Status='Concluído'", conn).iloc[0,0] or 0
    saidas = pd.read_sql("SELECT SUM(Valor) FROM despesas", conn).iloc[0,0] or 0
    conn.close()
    
    c1, c2, c3 = st.columns(3)
    c1.metric("Faturamento (Total)", f"R$ {entradas:,.2f}")
    c2.metric("Despesas Totais", f"R$ {saidas:,.2f}")
    c3.metric("Lucro Líquido", f"R$ {entradas - saidas:,.2f}")

def servicos():
    st.title("🛠️ Configuração de Serviços")
    conn = get_connection()
    with st.form("cad_serv"):
        n, v = st.text_input("Nome do Serviço"), st.number_input("Valor Padrão (R$)", min_value=0.0)
        if st.form_submit_button("Gravar Serviço"):
            try:
                conn.execute("INSERT INTO servicos (Nome, Valor) VALUES (?,?)", (n, v)); conn.commit()
                st.success("Serviço adicionado!"); st.rerun()
            except: st.warning("Serviço já existente.")
    st.dataframe(pd.read_sql("SELECT * FROM servicos", conn), use_container_width=True)
    conn.close()

def agendamentos():
    st.title("📅 Novo Agendamento")
    conn = get_connection()
    df_s = pd.read_sql("SELECT * FROM servicos", conn)
    if df_s.empty: st.warning("Por favor, cadastre serviços antes de agendar."); return
    
    with st.form("add_ag"):
        cli, pla = st.text_input("Cliente"), st.text_input("Placa")
        serv = st.selectbox("Serviço", df_s["Nome"])
        v_sug = df_s[df_s["Nome"] == serv]["Valor"].values[0]
        val = st.number_input("Valor Cobrado (R$)", value=float(v_sug))
        dt = st.date_input("Data", date.today())
        if st.form_submit_button("Confirmar Agendamento"):
            conn.execute("INSERT INTO agendamentos (Data, Cliente, Placa, Servico, Valor, Status) VALUES (?,?,?,?,?,?)",
                         (dt.isoformat(), cli, pla, serv, val, "Agendado"))
            conn.commit(); st.success("Agendado com sucesso!"); st.rerun()
    conn.close()

def patio():
    st.title("🚗 Pátio Operacional")
    conn = get_connection()
    df = pd.read_sql("SELECT * FROM agendamentos WHERE Status != 'Concluído' ORDER BY id DESC", conn)
    
    if df.empty:
        st.info("O pátio está limpo. Nenhum serviço pendente.")
    else:
        for i, row in df.iterrows():
            with st.container():
                col1, col2 = st.columns([3, 1])
                with col1:
                    st.markdown(f"""<div class="card-veiculo">
                        <span style="font-size: 22px; font-weight: bold;">{row['Placa']}</span><br>
                        {row['Cliente']} — <b>{row['Servico']}</b></div>""", unsafe_allow_html=True)
                with col2:
                    novo = st.selectbox("Status", ["Agendado", "Lavando", "Concluído"], 
                                       index=["Agendado", "Lavando", "Concluído"].index(row["Status"]), 
                                       key=f"p_{row['id']}")
                    if novo != row["Status"]:
                        conn.execute("UPDATE agendamentos SET Status=? WHERE id=?", (novo, row["id"]))
                        conn.commit(); st.rerun()
    conn.close()

def financeiro():
    st.title("💰 Fluxo de Caixa")
    conn = get_connection()
    col_a, col_b = st.columns(2)
    ini, fim = col_a.date_input("Início", date.today().replace(day=1)), col_b.date_input("Fim", date.today())
    
    # Unificando Entradas e Saídas
    df_e = pd.read_sql(f"SELECT Data, Cliente || ' (' || Servico || ')' as Descricao, Valor, 'Entrada' as Tipo FROM agendamentos WHERE Status='Concluído' AND Data BETWEEN '{ini}' AND '{fim}'", conn)
    df_s = pd.read_sql(f"SELECT Data, Descricao, Valor, 'Saída' as Tipo FROM despesas WHERE Data BETWEEN '{ini}' AND '{fim}'", conn)
    
    resumo = pd.concat([df_e, df_s]).sort_values("Data", ascending=False)
    
    c1, c2, c3 = st.columns(3)
    c1.metric("Entradas", f"R$ {df_e['Valor'].sum():,.2f}")
    c2.metric("Saídas", f"R$ {df_s['Valor'].sum():,.2f}")
    c3.metric("Saldo Período", f"R$ {df_e['Valor'].sum() - df_s['Valor'].sum():,.2f}")

    with st.expander("💸 Registar Nova Despesa (Saída)"):
        with st.form("f_des"):
            d, v = st.text_input("Descrição"), st.number_input("Valor R$", min_value=0.0)
            if st.form_submit_button("Lançar"):
                conn.execute("INSERT INTO despesas (Data, Descricao, Valor) VALUES (?,?,?)", (date.today().isoformat(), d, v))
                conn.commit(); st.rerun()
    
    st.dataframe(resumo, use_container_width=True)
    conn.close()

def estoque():
    st.title("📦 Inventário de Produtos")
    conn = get_connection()
    with st.form("f_est"):
        it, qt = st.text_input("Nome do Produto (ex: Shampoo)"), st.number_input("Qtd em Stock", min_value=0)
        if st.form_submit_button("Atualizar Stock"):
            conn.execute("INSERT INTO estoque (Item, Qtd) VALUES (?,?)", (it, qt)); conn.commit(); st.rerun()
    st.dataframe(pd.read_sql("SELECT * FROM estoque", conn), use_container_width=True)
    conn.close()

def fornecedores():
    st.title("🏭 Parceiros e Fornecedores")
    conn = get_connection()
    with st.form("f_for"):
        n, c, p = st.text_input("Empresa"), st.text_input("Contacto"), st.text_input("Produto Fornecido")
        if st.form_submit_button("Cadastrar Parceiro"):
            conn.execute("INSERT INTO fornecedores (Nome, Contato, Produto) VALUES (?,?,?)", (n, c, p)); conn.commit(); st.rerun()
    st.dataframe(pd.read_sql("SELECT * FROM fornecedores", conn), use_container_width=True)
    conn.close()

# ======================================================
# NAVEGAÇÃO
# ======================================================
st.sidebar.title("Lian Car")
menu = st.sidebar.radio("Navegação", ["Dashboard", "Serviços", "Agendamentos", "Pátio", "Financeiro", "Estoque", "Fornecedores"])

paginas = {
    "Dashboard": dashboard, "Serviços": servicos, "Agendamentos": agendamentos,
    "Pátio": patio, "Financeiro": financeiro, "Estoque": estoque, "Fornecedores": fornecedores
}
paginas[menu]()
