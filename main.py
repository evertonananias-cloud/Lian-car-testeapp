import streamlit as st
import pandas as pd
from datetime import datetime, date

# ======================================================
# CONFIGURAÇÃO
# ======================================================
st.set_page_config(
    page_title="Lian Car v3.4",
    page_icon="🧼",
    layout="wide"
)

# ======================================================
# CSS PREMIUM (CORRIGIDA E ESTÁVEL)
# ======================================================
st.markdown("""
<style>

/* Fonte global */
html, body, [class*="css"] {
    font-family: 'Segoe UI', 'Inter', sans-serif;
}

/* Fundo geral */
.stApp {
    background: linear-gradient(135deg, #0f172a, #020617);
    color: #e5e7eb;
}

/* Sidebar */
section[data-testid="stSidebar"] {
    background: linear-gradient(180deg, #020617, #020617);
    border-right: 1px solid #1e293b;
}
section[data-testid="stSidebar"] * {
    color: #e5e7eb !important;
}

/* Títulos */
h1, h2, h3 {
    font-weight: 600;
    letter-spacing: 0.4px;
}

/* Métricas */
[data-testid="stMetric"] {
    background: rgba(2, 6, 23, 0.85);
    padding: 20px;
    border-radius: 14px;
    border: 1px solid #1e293b;
    box-shadow: 0 10px 25px rgba(0,0,0,0.45);
}
[data-testid="stMetricValue"] {
    color: #38bdf8;
    font-size: 30px;
}

/* Botões */
.stButton > button {
    background: linear-gradient(135deg, #0284c7, #38bdf8);
    color: #020617;
    border-radius: 10px;
    padding: 10px 22px;
    font-weight: 600;
    border: none;
    transition: all 0.2s ease-in-out;
}
.stButton > button:hover {
    transform: scale(1.03);
    box-shadow: 0 8px 25px rgba(56,189,248,0.45);
}

/* Inputs */
input, textarea, select {
    background-color: #020617 !important;
    color: #e5e7eb !important;
    border-radius: 8px !important;
    border: 1px solid #1e293b !important;
}

/* Tabelas */
[data-testid="stDataFrame"] {
    background-color: #020617;
    border-radius: 14px;
    border: 1px solid #1e293b;
    padding: 10px;
}

/* Abas */
.stTabs [data-baseweb="tab"] {
    background-color: #020617;
    border-radius: 12px 12px 0 0;
    padding: 10px 18px;
    font-weight: 500;
}
.stTabs [aria-selected="true"] {
    background: linear-gradient(135deg, #0284c7, #38bdf8);
    color: #020617;
}

/* Alertas */
.stAlert {
    border-radius: 12px;
}

/* Divisor */
hr {
    border: none;
    height: 1px;
    background: linear-gradient(to right, transparent, #1e293b, transparent);
    margin: 30px 0;
}

</style>
""", unsafe_allow_html=True)

# ======================================================
# LOGIN
# ======================================================
USUARIOS = {"admin": "1234"}

def tela_login():
    st.title("🔐 Login - Lian Car")
    usuario = st.text_input("Usuário")
    senha = st.text_input("Senha", type="password")

    if st.button("Entrar"):
        if usuario in USUARIOS and USUARIOS[usuario] == senha:
            st.session_state.logado = True
            st.session_state.usuario = usuario
            st.rerun()
        else:
            st.error("Usuário ou senha inválidos")

if "logado" not in st.session_state:
    st.session_state.logado = False

if not st.session_state.logado:
    tela_login()
    st.stop()

# ======================================================
# ESTADO GLOBAL
# ======================================================
def init_state():
    if "db" not in st.session_state:
        st.session_state.db = pd.DataFrame(
            columns=["Data", "Cliente", "Placa", "Servico", "Valor", "Status"]
        )
    if "estoque" not in st.session_state:
        st.session_state.estoque = pd.DataFrame(columns=["Item", "Qtd"])
    if "fornecedores" not in st.session_state:
        st.session_state.fornecedores = pd.DataFrame(
            columns=["Empresa", "Contato", "Telefone", "Produto"]
        )

init_state()

# ======================================================
# MENU
# ======================================================
st.sidebar.title("🧼 Lian Car v3.4")
st.sidebar.write(f"👤 {st.session_state.usuario}")

menu = st.sidebar.radio(
    "Navegação",
    ["Dashboard", "Agendamentos", "Pátio", "Financeiro", "Relatórios", "Estoque", "Fornecedores"]
)

# ======================================================
# DASHBOARD
# ======================================================
def dashboard():
    st.title("📊 Dashboard")
    df = st.session_state.db.copy()
    df["Data"] = pd.to_datetime(df["Data"], errors="coerce")

    c1, c2, c3 = st.columns(3)
    c1.metric("Faturamento", f"R$ {df['Valor'].sum():,.2f}")
    c2.metric("Serviços", len(df))
    c3.metric("Ticket Médio", f"R$ {df['Valor'].mean() if len(df) else 0:,.2f}")

# ======================================================
# AGENDAMENTOS
# ======================================================
def agendamentos():
    st.title("📅 Agendamentos")

    with st.form("form_agendamento"):
        cliente = st.text_input("Cliente")
        placa = st.text_input("Placa do Veículo")
        servico = st.text_input("Serviço")
        valor = st.number_input("Valor", min_value=0.0, step=10.0)
        status = st.selectbox("Status", ["Agendado", "Lavando", "Concluído"])

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

# ======================================================
# PÁTIO
# ======================================================
def patio():
    st.title("🚗 Pátio")
    df = st.session_state.db

    for status in ["Agendado", "Lavando", "Concluído"]:
        st.subheader(status)
        st.dataframe(df[df["Status"] == status], use_container_width=True)

# ======================================================
# FINANCEIRO
# ======================================================
def financeiro():
    st.title("💰 Financeiro")
    df = st.session_state.db.copy()
    df["Data"] = pd.to_datetime(df["Data"], errors="coerce")

    st.metric("Total Geral", f"R$ {df['Valor'].sum():,.2f}")
    st.dataframe(df[["Data", "Cliente", "Servico", "Valor"]], use_container_width=True)

# ======================================================
# RELATÓRIOS
# ======================================================
def relatorios():
    st.title("📄 Relatórios")
    df = st.session_state.db.copy()
    df["Data"] = pd.to_datetime(df["Data"], errors="coerce")

    c1, c2 = st.columns(2)
    ini = c1.date_input("Data inicial", date.today())
    fim = c2.date_input("Data final", date.today())

    filtro = (df["Data"].dt.date >= ini) & (df["Data"].dt.date <= fim)
    df_f = df.loc[filtro]

    st.dataframe(df_f, use_container_width=True)
    st.metric("Faturamento", f"R$ {df_f['Valor'].sum():,.2f}")

# ======================================================
# ESTOQUE
# ======================================================
def estoque():
    st.title("📦 Gestão de Estoque")
    df = st.session_state.estoque

    st.subheader("📋 Estoque Atual")
    if df.empty:
        st.info("Sem produtos cadastrados")
    else:
        st.dataframe(df, use_container_width=True)

    st.divider()
    st.subheader("➕➖ Cadastrar ou Editar Produto")

    col1, col2, col3 = st.columns(3)
    modo = col1.radio("Modo", ["Novo Produto", "Editar Produto"])

    if modo == "Novo Produto":
        nome = col2.text_input("Produto")
        qtd = col3.number_input("Quantidade Inicial", min_value=0, step=1)

        if st.button("Cadastrar Produto"):
            if not nome:
                st.error("Informe o nome do produto")
                return
            if nome in df["Item"].values:
                st.error("Produto já cadastrado")
                return

            st.session_state.estoque = pd.concat(
                [df, pd.DataFrame([{"Item": nome, "Qtd": qtd}])],
                ignore_index=True
            )
            st.success("Produto cadastrado")
            st.rerun()

    else:
        if df.empty:
            st.warning("Nenhum produto para editar")
            return

        produto = col2.selectbox("Produto", df["Item"])
        idx = df[df["Item"] == produto].index[0]
        nova_qtd = col3.number_input(
            "Nova Quantidade",
            min_value=0,
            step=1,
            value=int(df.at[idx, "Qtd"])
        )

        if st.button("Atualizar Produto"):
            df.at[idx, "Qtd"] = nova_qtd
            st.success("Produto atualizado")
            st.rerun()

    st.divider()
    st.subheader("🔄 Movimentação de Estoque")

    if df.empty:
        st.warning("Cadastre produtos antes de movimentar o estoque")
        return

    c4, c5, c6 = st.columns(3)
    produto = c4.selectbox("Produto", df["Item"])
    quantidade = c5.number_input("Quantidade", min_value=1, step=1)
    acao = c6.radio("Ação", ["Entrada", "Saída"])

    if st.button("Confirmar Movimentação"):
        idx = df[df["Item"] == produto].index[0]

        if acao == "Saída" and df.at[idx, "Qtd"] < quantidade:
            st.error("Estoque insuficiente")
            return

        df.at[idx, "Qtd"] += quantidade if acao == "Entrada" else -quantidade
        st.success("Movimentação realizada")
        st.rerun()

# ======================================================
# FORNECEDORES
# ======================================================
def fornecedores():
    st.title("🚚 Fornecedores")
    st.dataframe(st.session_state.fornecedores, use_container_width=True)

    with st.form("form_fornecedor"):
        empresa = st.text_input("Empresa")
        contato = st.text_input("Contato")
        telefone = st.text_input("Telefone")
        produto = st.text_input("Produto fornecido")

        if st.form_submit_button("Cadastrar"):
            st.session_state.fornecedores = pd.concat(
                [
                    st.session_state.fornecedores,
                    pd.DataFrame([{
                        "Empresa": empresa,
                        "Contato": contato,
                        "Telefone": telefone,
                        "Produto": produto
                    }])
                ],
                ignore_index=True
            )
            st.success("Fornecedor cadastrado")
            st.rerun()

# ======================================================
# ROTEAMENTO
# ======================================================
{
    "Dashboard": dashboard,
    "Agendamentos": agendamentos,
    "Pátio": patio,
    "Financeiro": financeiro,
    "Relatórios": relatorios,
    "Estoque": estoque,
    "Fornecedores": fornecedores
}[menu]()
