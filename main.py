import streamlit as st
import pandas as pd
from datetime import datetime, date

# =========================
# CONFIG
# =========================
st.set_page_config("🧼 Lian Car v3.2", "🧼", layout="wide")

st.markdown("""
<style>
[data-testid="stMetricValue"] { color:#00d4ff; font-size:28px; }
</style>
""", unsafe_allow_html=True)

# =========================
# LOGIN
# =========================
USUARIOS = {"admin": "1234"}

def login():
    st.title("🔐 Login - Lian Car")
    u = st.text_input("Usuário")
    s = st.text_input("Senha", type="password")
    if st.button("Entrar"):
        if u in USUARIOS and USUARIOS[u] == s:
            st.session_state.logado = True
            st.session_state.usuario = u
            st.rerun()
        else:
            st.error("Credenciais inválidas")

if "logado" not in st.session_state:
    st.session_state.logado = False

if not st.session_state.logado:
    login()
    st.stop()

# =========================
# STATE
# =========================
def init():
    if "db" not in st.session_state:
        st.session_state.db = pd.DataFrame(
            columns=["Data","Cliente","Placa","Servico","Valor","Status"]
        )
    if "estoque" not in st.session_state:
        st.session_state.estoque = pd.DataFrame(columns=["Item","Qtd"])
    if "fornecedores" not in st.session_state:
        st.session_state.fornecedores = pd.DataFrame(
            columns=["Empresa","Contato","Telefone","Produto"]
        )

init()

# =========================
# MENU
# =========================
st.sidebar.title("🧼 Lian Car v3.2")
st.sidebar.write(f"👤 {st.session_state.usuario}")

menu = st.sidebar.radio(
    "Navegação",
    ["Dashboard","Agendamentos","Pátio","Financeiro","Relatórios","Estoque","Fornecedores"]
)

# =========================
# DASHBOARD
# =========================
def dashboard():
    st.title("📊 Dashboard")
    df = st.session_state.db.copy()
    df["Data"] = pd.to_datetime(df["Data"], errors="coerce")

    c1,c2,c3 = st.columns(3)
    c1.metric("Faturamento", f"R$ {df['Valor'].sum():,.2f}")
    c2.metric("Serviços", len(df))
    c3.metric("Ticket Médio", f"R$ {df['Valor'].mean() if len(df) else 0:,.2f}")

# =========================
# AGENDAMENTOS
# =========================
def agendamentos():
    st.title("📅 Agendamentos")

    with st.form("novo"):
        cliente = st.text_input("Cliente")
        placa = st.text_input("Placa")
        servico = st.text_input("Serviço")
        valor = st.number_input("Valor", 0.0, step=10.0)
        status = st.selectbox("Status", ["Agendado","Lavando","Concluído"])

        if st.form_submit_button("Cadastrar"):
            novo = {
                "Data": datetime.now(),
                "Cliente": cliente,
                "Placa": placa,
                "Servico": servico,
                "Valor": valor,
                "Status": status
            }
            st.session_state.db = pd.concat(
                [st.session_state.db, pd.DataFrame([novo])],
                ignore_index=True
            )
            st.success("Serviço cadastrado")
            st.rerun()

    st.dataframe(st.session_state.db, use_container_width=True)

# =========================
# PÁTIO
# =========================
def patio():
    st.title("🚗 Pátio")
    df = st.session_state.db
    for s in ["Agendado","Lavando","Concluído"]:
        st.subheader(s)
        st.dataframe(df[df["Status"] == s], use_container_width=True)

# =========================
# FINANCEIRO
# =========================
def financeiro():
    st.title("💰 Financeiro")
    df = st.session_state.db.copy()
    df["Data"] = pd.to_datetime(df["Data"], errors="coerce")
    st.metric("Total Geral", f"R$ {df['Valor'].sum():,.2f}")
    st.dataframe(df[["Data","Cliente","Servico","Valor"]])

# =========================
# RELATÓRIOS (CORRIGIDO)
# =========================
def relatorios():
    st.title("📄 Relatórios")
    df = st.session_state.db.copy()
    df["Data"] = pd.to_datetime(df["Data"], errors="coerce")

    c1,c2 = st.columns(2)
    ini = c1.date_input("Data inicial", date.today())
    fim = c2.date_input("Data final", date.today())

    filtro = (df["Data"].dt.date >= ini) & (df["Data"].dt.date <= fim)
    df_f = df.loc[filtro]

    st.dataframe(df_f, use_container_width=True)
    st.metric("Faturamento", f"R$ {df_f['Valor'].sum():,.2f}")

# =========================
# ESTOQUE (COMPLETO)
# =========================
def estoque():
    st.title("📦 Gestão de Estoque")
    df = st.session_state.estoque

    st.subheader("📋 Estoque Atual")
    st.dataframe(df, use_container_width=True) if not df.empty else st.info("Sem produtos")

    st.divider()
    st.subheader("➕➖ Cadastrar / Editar Produto")

    col1,col2,col3 = st.columns(3)
    modo = col1.radio("Modo", ["Novo Produto","Editar Produto"])

    if modo == "Novo Produto":
        nome = col2.text_input("Produto")
        qtd = col3.number_input("Quantidade", 0, step=1)
        if st.button("Cadastrar"):
            if nome in df["Item"].values:
                st.error("Produto já existe")
            else:
                st.session_state.estoque = pd.concat(
                    [df, pd.DataFrame([{"Item":nome,"Qtd":qtd}])],
                    ignore_index=True
                )
                st.success("Produto cadastrado")
                st.rerun()
    else:
        if df.empty:
            st.warning("Nenhum produto para editar")
            return
        prod = col2.selectbox("Produto", df["Item"])
        idx = df[df["Item"] == prod].index[0]
        nova = col3.number_input("Nova quantidade", 0, step=1, value=int(df.at[idx,"Qtd"]))
        if st.button("Atualizar"):
            df.at[idx,"Qtd"] = nova
            st.success("Atualizado")
            st.rerun()

    st.divider()
    st.subheader("🔄 Movimentação")

    if df.empty:
        return

    c4,c5,c6 = st.columns(3)
    prod = c4.selectbox("Produto", df["Item"])
    qtd = c5.number_input("Quantidade", 1, step=1)
    acao = c6.radio("Ação", ["Entrada","Saída"])

    if st.button("Confirmar"):
        idx = df[df["Item"] == prod].index[0]
        if acao == "Saída" and df.at[idx,"Qtd"] < qtd:
            st.error("Estoque insuficiente")
        else:
            df.at[idx,"Qtd"] += qtd if acao == "Entrada" else -qtd
            st.success("Movimentação realizada")
            st.rerun()

# =========================
# FORNECEDORES
# =========================
def fornecedores():
    st.title("🚚 Fornecedores")
    st.dataframe(st.session_state.fornecedores, use_container_width=True)

    with st.form("forn"):
        emp = st.text_input("Empresa")
        cont = st.text_input("Contato")
        tel = st.text_input("Telefone")
        prod = st.text_input("Produto")
        if st.form_submit_button("Cadastrar"):
            st.session_state.fornecedores = pd.concat(
                [st.session_state.fornecedores,
                 pd.DataFrame([{
                     "Empresa":emp,"Contato":cont,
                     "Telefone":tel,"Produto":prod
                 }])],
                ignore_index=True
            )
            st.success("Fornecedor cadastrado")
            st.rerun()

# =========================
# ROTEAMENTO
# =========================
{
    "Dashboard": dashboard,
    "Agendamentos": agendamentos,
    "Pátio": patio,
    "Financeiro": financeiro,
    "Relatórios": relatorios,
    "Estoque": estoque,
    "Fornecedores": fornecedores
}[menu]()
