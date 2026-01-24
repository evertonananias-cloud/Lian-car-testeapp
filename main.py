import streamlit as st
import pandas as pd
from datetime import datetime
import hashlib

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

# ======================================================
# USUÁRIOS (TEMPORÁRIO)
# ======================================================
USERS = {
    "admin": {
        "name": "Administrador",
        "password": hash_password("123456")
    },
    "lian": {
        "name": "Lian Car",
        "password": hash_password("lian123")
    }
}

STATUS_PATIO = ["Agendado", "Lavando", "Concluído"]

# ======================================================
# CSS GLOBAL (UI PREMIUM)
# ======================================================
def load_css():
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

        .patio-card {
            border: 1px solid #2b2b2b;
            border-radius: 12px;
            padding: 12px;
            margin-bottom: 10px;
        }
        </style>
    """, unsafe_allow_html=True)

load_css()

# ======================================================
# SESSION STATE
# ======================================================
def init_session_state():
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

init_session_state()

# ======================================================
# AUTENTICAÇÃO
# ======================================================
def login_screen():
    st.title("🔐 Login - Lian Car")

    with st.form("login"):
        username = st.text_input("Usuário")
        password = st.text_input("Senha", type="password")
        submit = st.form_submit_button("Entrar")

        if submit:
            if username in USERS and hash_password(password) == USERS[username]["password"]:
                st.session_state.authenticated = True
                st.session_state.user = USERS[username]["name"]
                st.success("Login realizado com sucesso!")
                st.rerun()
            else:
                st.error("Usuário ou senha inválidos")

# ======================================================
# SIDEBAR
# ======================================================
def sidebar_menu():
    st.sidebar.title("🧼 Lian Car v2.0")
    st.sidebar.markdown(f"👤 **{st.session_state.user}**")

    if st.sidebar.button("🚪 Logout"):
        st.session_state.authenticated = False
        st.session_state.user = None
        st.rerun()

    return st.sidebar.radio(
        "Navegação",
        ["Dashboard", "Agendamentos", "Pátio", "Estoque", "Fornecedores"]
    )

# ======================================================
# DASHBOARD
# ======================================================
def render_dashboard():
    st.title("📈 Dashboard")

    faturamento = st.session_state.db["Valor"].sum()
    total = len(st.session_state.db)
    ticket = faturamento / total if total > 0 else 0

    c1, c2, c3 = st.columns(3)
    c1.metric("💰 Faturamento", f"R$ {faturamento:,.2f}")
    c2.metric("🧽 Serviços", total)
    c3.metric("📊 Ticket Médio", f"R$ {ticket:,.2f}")

    st.divider()
    st.subheader("📋 Últimos Serviços")

    if st.session_state.db.empty:
        st.info("Nenhum registro ainda.")
    else:
        st.dataframe(
            st.session_state.db.sort_values("Data", ascending=False),
            use_container_width=True
        )

# ======================================================
# AGENDAMENTOS
# ======================================================
def render_agendamentos():
    st.title("📅 Novo Agendamento")

    with st.form("agendamento"):
        cliente = st.text_input("Cliente")
        placa = st.text_input("Placa do Veículo", max_chars=7).upper()
        servico = st.selectbox(
            "Serviço",
            ["Lavagem Simples", "Lavagem Completa", "Polimento"]
        )
        valor = st.number_input("Valor (R$)", min_value=0.0, step=10.0)

        submit = st.form_submit_button("Salvar")

        if submit:
            if not cliente or not placa:
                st.error("Cliente e placa são obrigatórios.")
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

            st.success("Agendamento cadastrado com sucesso!")

# ======================================================
# PÁTIO OPERACIONAL
# ======================================================
def render_patio():
    st.title("🚗 Pátio Operacional")

    if st.session_state.db.empty:
        st.info("Nenhum veículo no pátio.")
        return

    col1, col2, col3 = st.columns(3)
    cols = dict(zip(STATUS_PATIO, [col1, col2, col3]))

    for status, coluna in cols.items():
        with coluna:
            st.subheader(status)

            df_status = st.session_state.db[
                st.session_state.db["Status"] == status
            ]

            if df_status.empty:
                st.caption("Sem veículos")
            else:
                for idx, row in df_status.iterrows():
                    st.markdown(f"""
                        <div class="patio-card">
                        <b>{row['Cliente']}</b><br>
                        🚘 {row['Placa']}<br>
                        🧽 {row['Serviço']}
                        </div>
                    """, unsafe_allow_html=True)

                    if status == "Agendado":
                        if st.button("▶️ Iniciar Lavagem", key=f"lavar_{idx}"):
                            st.session_state.db.at[idx, "Status"] = "Lavando"
                            st.rerun()

                    elif status == "Lavando":
                        if st.button("✅ Finalizar", key=f"finalizar_{idx}"):
                            st.session_state.db.at[idx, "Status"] = "Concluído"
                            st.rerun()

# ======================================================
# ESTOQUE
# ======================================================
def render_estoque():
    st.title("📦 Estoque")
    st.dataframe(st.session_state.estoque, use_container_width=True)

# ======================================================
# FORNECEDORES
# ======================================================
def render_fornecedores():
    st.title("🚚 Fornecedores")
    st.info("Módulo em desenvolvimento")

# ======================================================
# APP PRINCIPAL
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
    elif menu == "Estoque":
        render_estoque()
    elif menu == "Fornecedores":
        render_fornecedores()
