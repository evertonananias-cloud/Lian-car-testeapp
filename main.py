import streamlit as st
import pandas as pd
from datetime import datetime, date

# ======================================================
# CONFIGURAÇÃO
# ======================================================
st.set_page_config(
    page_title="Lian Car | Gestão Automotiva",
    page_icon="🧼",
    layout="wide"
)

# ======================================================
# CSS PROFISSIONAL (FRONT-END NOVO)
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
    --danger: #ef4444;
}

.stApp {
    background: radial-gradient(circle at top, #020617, #000000);
    color: #e5e7eb;
    font-family: 'Inter', 'Segoe UI', sans-serif;
}

section[data-testid="stSidebar"] {
    background: linear-gradient(180deg, #020617, #020617);
    border-right: 1px solid var(--border);
}

h1 { font-size: 32px; font-weight: 600; }
h2 { font-size: 24px; }

[data-testid="stMetric"] {
    background: var(--card);
    padding: 22px;
    border-radius: 16px;
    border: 1px solid var(--border);
    box-shadow: 0 10px 30px rgba(0,0,0,.4);
}

[data-testid="stMetricValue"] {
    color: var(--primary);
    font-size: 30px;
}

.stButton>button {
    background: linear-gradient(135deg, var(--primary), #38bdf8);
    color: #020617;
    font-weight: 600;
    border-radius: 12px;
    padding: 10px 22px;
    border: none;
    transition: .25s;
}

.stButton>button:hover {
    transform: translateY(-2px);
    box-shadow: 0 10px 25px rgba(14,165,233,.4);
}

input, textarea, select {
    background-color: #020617 !important;
    color: #e5e7eb !important;
    border-radius: 10px !important;
    border: 1px solid var(--border) !important;
}

[data-testid="stDataFrame"] {
    border-radius: 16px;
    border: 1px solid var(--border);
}

.status-agendado { color: var(--warning); font-weight: 600; }
.status-lavando { color: var(--primary); font-weight: 600; }
.status-concluido { color: var(--success); font-weight: 600; }

hr {
    border: none;
    height: 1px;
    background: linear-gradient(to right, transparent, var(--border), transparent);
    margin: 30px 0;
}
</style>
""", unsafe_allow_html=True)

# ======================================================
# ESTADO GLOBAL
# ======================================================
def init_state():
    if "logado" not in st.session_state:
        st.session_state.logado = False

    if "db" not in st.session_state:
        st.session_state.db = pd.DataFrame(
            columns=["Data", "Cliente", "Placa", "Servico", "Valor", "Status"]
        )

    if "despesas" not in st.session_state:
        st.session_state.despesas = pd.DataFrame(
            columns=["Data", "Descricao", "Valor"]
        )

    if "estoque" not in st.session_state:
        st.session_state.estoque = pd.DataFrame(
            columns=["Item", "Qtd"]
        )

    if "fornecedores" not in st.session_state:
        st.session_state.fornecedores = pd.DataFrame(
            columns=["Nome", "Contato", "Produto"]
        )

init_state()

# ======================================================
# LOGIN
# ======================================================
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

    fat = st.session_state.db["Valor"].sum()
    desp = st.session_state.despesas["Valor"].sum()
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
            novo = {
                "Data": datetime.combine(data, datetime.min.time()),
                "Cliente": cliente,
                "Placa": placa,
                "Servico": servico,
                "Valor": valor,
                "Status": "Agendado"
            }
            st.session_state.db = pd.concat(
                [st.session_state.db, pd.DataFrame([novo])],
                ignore_index=True
            )
            st.success("Agendamento criado")
            st.rerun()

    st.divider()

    if st.session_state.db.empty:
        st.info("Nenhum agendamento")
    else:
        st.dataframe(st.session_state.db, use_container_width=True)

# ======================================================
# PÁTIO
# ======================================================
def patio():
    st.title("🚗 Pátio Operacional")

    df = st.session_state.db
    if df.empty:
        st.info("Nenhum veículo no pátio")
        return

    for i in df.index:
        status = df.at[i, "Status"]
        classe = {
            "Agendado": "status-agendado",
            "Lavando": "status-lavando",
            "Concluído": "status-concluido"
        }[status]

        st.markdown(
            f"<b>{df.at[i,'Placa']}</b> — "
            f"<span class='{classe}'>● {status}</span>",
            unsafe_allow_html=True
        )

        novo = st.selectbox(
            "Alterar status",
            ["Agendado", "Lavando", "Concluído"],
            index=["Agendado","Lavando","Concluído"].index(status),
            key=f"patio_{i}"
        )
        df.at[i, "Status"] = novo

# ======================================================
# FINANCEIRO
# ======================================================
def financeiro():
    st.title("💰 Financeiro")

    col1, col2 = st.columns(2)
    ini = col1.date_input("Data inicial", date.today())
    fim = col2.date_input("Data final", date.today())

    serv = st.session_state.db.copy()
    desp = st.session_state.despesas.copy()

    serv["Data"] = pd.to_datetime(serv["Data"], errors="coerce")
    desp["Data"] = pd.to_datetime(desp["Data"], errors="coerce")

    serv = serv[(serv["Data"].dt.date >= ini) & (serv["Data"].dt.date <= fim)]
    desp = desp[(desp["Data"].dt.date >= ini) & (desp["Data"].dt.date <= fim)]

    fat = serv["Valor"].sum()
    des = desp["Valor"].sum()

    c1, c2, c3 = st.columns(3)
    c1.metric("Faturamento", f"R$ {fat:,.2f}")
    c2.metric("Despesas", f"R$ {des:,.2f}")
    c3.metric("Lucro", f"R$ {fat-des:,.2f}")

    st.divider()

    with st.form("nova_despesa"):
        desc = st.text_input("Descrição")
        val = st.number_input("Valor", min_value=0.0)
        data = st.date_input("Data", date.today())

        if st.form_submit_button("Cadastrar Despesa"):
            st.session_state.despesas = pd.concat(
                [st.session_state.despesas,
                 pd.DataFrame([{
                     "Data": datetime.combine(data, datetime.min.time()),
                     "Descricao": desc,
                     "Valor": val
                 }])],
                ignore_index=True
            )
            st.success("Despesa registrada")
            st.rerun()

# ======================================================
# RELATÓRIOS
# ======================================================
def relatorios():
    st.title("📄 Relatórios")

    df = st.session_state.db.copy()
    if df.empty:
        st.info("Sem dados")
        return

    df["Data"] = pd.to_datetime(df["Data"], errors="coerce")

    col1, col2 = st.columns(2)
    ini = col1.date_input("Data inicial", date.today())
    fim = col2.date_input("Data final", date.today())

    df = df[(df["Data"].dt.date >= ini) & (df["Data"].dt.date <= fim)]

    if df.empty:
        st.warning("Nenhum registro no período")
        return

    st.dataframe(
        df[["Data","Cliente","Placa","Servico","Valor","Status"]],
        use_container_width=True
    )

    st.metric("Faturamento do período", f"R$ {df['Valor'].sum():,.2f}")

# ======================================================
# ESTOQUE
# ======================================================
def estoque():
    st.title("📦 Estoque")

    df = st.session_state.estoque
    if df.empty:
        st.info("Sem produtos")
    else:
        st.dataframe(df, use_container_width=True)

    st.divider()
    nome = st.text_input("Produto")
    qtd = st.number_input("Quantidade", min_value=0, step=1)

    if st.button("Salvar Produto"):
        st.session_state.estoque = pd.concat(
            [df, pd.DataFrame([{"Item": nome, "Qtd": qtd}])],
            ignore_index=True
        )
        st.success("Produto salvo")
        st.rerun()

# ======================================================
# FORNECEDORES
# ======================================================
def fornecedores():
    st.title("🏭 Fornecedores")

    with st.form("novo_fornecedor"):
        nome = st.text_input("Nome")
        contato = st.text_input("Contato")
        produto = st.text_input("Produto")

        if st.form_submit_button("Cadastrar"):
            st.session_state.fornecedores = pd.concat(
                [st.session_state.fornecedores,
                 pd.DataFrame([{
                     "Nome": nome,
                     "Contato": contato,
                     "Produto": produto
                 }])],
                ignore_index=True
            )
            st.success("Fornecedor cadastrado")
            st.rerun()

    if st.session_state.fornecedores.empty:
        st.info("Nenhum fornecedor")
    else:
        st.dataframe(st.session_state.fornecedores, use_container_width=True)

# ======================================================
# MENU
# ======================================================
menu = st.sidebar.radio(
    "Navegação",
    [
        "Dashboard",
        "Agendamentos",
        "Pátio",
        "Financeiro",
        "Relatórios",
        "Estoque",
        "Fornecedores"
    ]
)

{
    "Dashboard": dashboard,
    "Agendamentos": agendamentos,
    "Pátio": patio,
    "Financeiro": financeiro,
    "Relatórios": relatorios,
    "Estoque": estoque,
    "Fornecedores": fornecedores
}[menu]()
