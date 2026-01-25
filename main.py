import streamlit as st
import pandas as pd
from datetime import datetime
import hashlib
from io import BytesIO

# ======================================================
# CONFIGURAÇÃO DA PÁGINA
# ======================================================
st.set_page_config(
    page_title="Lian Car App",
    page_icon="🧼",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ======================================================
# UTILIDADES
# ======================================================
def hash_password(password: str) -> str:
    return hashlib.sha256(password.encode()).hexdigest()

STATUS_PATIO = ["Agendado", "Lavando", "Concluído"]

USERS = {
    "admin": {"name": "Administrador", "password": hash_password("123456")},
    "lian": {"name": "Lian Car", "password": hash_password("lian123")},
}

# ======================================================
# CSS
# ======================================================
st.markdown("""
<style>
[data-testid="stMetricValue"] {
    color: #00d4ff;
    font-size: 32px;
    font-weight: bold;
}
section[data-testid="stSidebar"] {
    background-color: #0e1117;
}
.card {
    border: 1px solid #2b2b2b;
    border-radius: 12px;
    padding: 10px;
    margin-bottom: 10px;
}
</style>
""", unsafe_allow_html=True)

# ======================================================
# SESSION STATE
# ======================================================
def init_state():
    if "authenticated" not in st.session_state:
        st.session_state.authenticated = False
    if "user" not in st.session_state:
        st.session_state.user = None

    if "db" not in st.session_state:
        st.session_state.db = pd.DataFrame(
            columns=["id", "Data", "Cliente", "Placa", "Serviço", "Valor", "Status"]
        )

    if "estoque" not in st.session_state:
        st.session_state.estoque = pd.DataFrame([
            {"Item": "Shampoo 5L", "Qtd": 80},
            {"Item": "Pretinho", "Qtd": 30},
            {"Item": "Cera", "Qtd": 50},
        ])

    if "fornecedores" not in st.session_state:
        st.session_state.fornecedores = pd.DataFrame(
            columns=["Empresa", "Contato", "Telefone", "Produto"]
        )

init_state()

# ======================================================
# LOGIN
# ======================================================
def login_screen():
    st.title("🔐 Login - Lian Car")

    with st.form("login"):
        user = st.text_input("Usuário")
        pwd = st.text_input("Senha", type="password")
        if st.form_submit_button("Entrar"):
            if user in USERS and hash_password(pwd) == USERS[user]["password"]:
                st.session_state.authenticated = True
                st.session_state.user = USERS[user]["name"]
                st.rerun()
            else:
                st.error("Usuário ou senha inválidos")

# ======================================================
# SIDEBAR
# ======================================================
def sidebar_menu():
    st.sidebar.title("🧼 Lian Car v3.0")
    st.sidebar.markdown(f"👤 **{st.session_state.user}**")

    if st.sidebar.button("🚪 Logout"):
        st.session_state.authenticated = False
        st.session_state.user = None
        st.rerun()

    return st.sidebar.radio(
        "Navegação",
        [
            "Dashboard",
            "Agendamentos",
            "Pátio",
            "Financeiro",
            "Relatórios",
            "Estoque",
            "Fornecedores",
        ]
    )

# ======================================================
# DASHBOARD
# ======================================================
def render_dashboard():
    st.title("📈 Dashboard")

    df = st.session_state.db
    concluido = df[df["Status"] == "Concluído"]

    faturamento = concluido["Valor"].sum()
    total = len(df)
    ticket = faturamento / len(concluido) if len(concluido) else 0

    c1, c2, c3 = st.columns(3)
    c1.metric("💰 Faturamento", f"R$ {faturamento:,.2f}")
    c2.metric("🧽 Serviços", total)
    c3.metric("📊 Ticket Médio", f"R$ {ticket:,.2f}")

    st.dataframe(df.sort_values("Data", ascending=False), use_container_width=True)

# ======================================================
# AGENDAMENTOS
# ======================================================
def render_agendamentos():
    st.title("📅 Novo Agendamento")

    with st.form("agendamento"):
        cliente = st.text_input("Cliente")
        placa = st.text_input("Placa", max_chars=7).upper()
        servico = st.selectbox("Serviço", ["Lavagem Simples", "Lavagem Completa", "Polimento"])
        valor = st.number_input("Valor (R$)", min_value=0.0, step=10.0)

        if st.form_submit_button("Salvar"):
            if not cliente or not placa:
                st.error("Cliente e placa obrigatórios")
                return

            novo = {
                "id": len(st.session_state.db) + 1,
                "Data": datetime.now(),
                "Cliente": cliente,
                "Placa": placa,
                "Serviço": servico,
                "Valor": valor,
                "Status": "Agendado",
            }

            st.session_state.db = pd.concat(
                [st.session_state.db, pd.DataFrame([novo])],
                ignore_index=True
            )
            st.success("Agendamento cadastrado!")

# ======================================================
# PÁTIO
# ======================================================
def render_patio():
    st.title("🚗 Pátio")

    for status in STATUS_PATIO:
        st.subheader(status)
        df = st.session_state.db[st.session_state.db["Status"] == status]

        for idx, row in df.iterrows():
            st.markdown(f"""
            <div class="card">
            <b>{row['Cliente']}</b><br>
            🚘 {row['Placa']}<br>
            🧽 {row['Serviço']}
            </div>
            """, unsafe_allow_html=True)

            if status == "Agendado":
                if st.button("▶️ Iniciar", key=f"i{idx}"):
                    st.session_state.db.at[idx, "Status"] = "Lavando"
                    st.rerun()
            elif status == "Lavando":
                if st.button("✅ Finalizar", key=f"f{idx}"):
                    st.session_state.db.at[idx, "Status"] = "Concluído"
                    st.rerun()

# ======================================================
# FINANCEIRO
# ======================================================
def render_financeiro():
    st.title("💰 Financeiro")

    df = st.session_state.db
    concluido = df[df["Status"] == "Concluído"]

    st.metric("Faturamento Total", f"R$ {concluido['Valor'].sum():,.2f}")
    st.metric("Em Aberto", f"R$ {df[df['Status'] != 'Concluído']['Valor'].sum():,.2f}")

# ======================================================
# RELATÓRIOS
# ======================================================
def render_relatorios():
    st.title("📄 Relatórios")

    df = st.session_state.db
    data_ini = st.date_input("Data inicial")
    data_fim = st.date_input("Data final")

    mask = (df["Data"].dt.date >= data_ini) & (df["Data"].dt.date <= data_fim)
    df_f = df[mask]

    st.dataframe(df_f, use_container_width=True)

    buffer = BytesIO()
    df_f.to_excel(buffer, index=False)
    st.download_button(
        "📥 Baixar Excel",
        buffer.getvalue(),
        "relatorio.xlsx"
    )

# ======================================================
# ESTOQUE
# ======================================================
def render_estoque():
    st.title("📦 Estoque")
    df = st.session_state.estoque
    st.dataframe(df, use_container_width=True)

    item = st.selectbox("Item", df["Item"])
    qtd = st.number_input("Quantidade", min_value=1)
    acao = st.radio("Ação", ["Entrada", "Saída"])

    if st.button("Confirmar"):
        idx = df[df["Item"] == item].index[0]
        if acao == "Saída" and df.at[idx, "Qtd"] < qtd:
            st.error("Estoque insuficiente")
            return
        df.at[idx, "Qtd"] += qtd if acao == "Entrada" else -qtd
        st.rerun()

# ======================================================
# FORNECEDORES
# ======================================================
def render_fornecedores():
    st.title("🚚 Fornecedores")
    st.dataframe(st.session_state.fornecedores, use_container_width=True)

    with st.form("fornecedor"):
        empresa = st.text_input("Empresa")
        contato = st.text_input("Contato")
        telefone = st.text_input("Telefone")
        produto = st.text_input("Produto")

        if st.form_submit_button("Cadastrar"):
            st.session_state.fornecedores = pd.concat(
                [st.session_state.fornecedores, pd.DataFrame([{
                    "Empresa": empresa,
                    "Contato": contato,
                    "Telefone": telefone,
                    "Produto": produto
                }])],
                ignore_index=True
            )
            st.success("Fornecedor cadastrado!")

# ======================================================
# APP
# ======================================================
if not st.session_state.authenticated:
    login_screen()
else:
    menu = sidebar_menu()

    if menu == "Dashboard":
        render_dashboard()
    elif menu == "Agendamentos":
        render_agendamentos()
    elif menu == "Pátio":
        render_patio()
    elif menu == "Financeiro":
        render_financeiro()
    elif menu == "Relatórios":
        render_relatorios()
    elif menu == "Estoque":
        render_estoque()
    elif menu == "Fornecedores":
        render_fornecedores()
