import streamlit as st
import pandas as pd
from datetime import datetime

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
# CSS GLOBAL (UI PREMIUM)
# ======================================================
def load_css():
    st.markdown("""
        <style>
        /* Métricas */
        [data-testid="stMetricValue"] {
            color: #00d4ff;
            font-size: 32px;
            font-weight: bold;
        }

        /* Tabs */
        .stTabs [data-baseweb="tab-list"] {
            gap: 20px;
        }

        .stTabs [data-baseweb="tab"] {
            height: 50px;
            border-radius: 10px 10px 0 0;
            padding: 10px 20px;
            font-weight: 600;
        }

        /* Sidebar */
        section[data-testid="stSidebar"] {
            background-color: #0e1117;
        }

        /* Títulos */
        h1, h2, h3 {
            font-weight: 700;
        }
        </style>
    """, unsafe_allow_html=True)

load_css()

# ======================================================
# ESTADO GLOBAL (SESSION STATE)
# ======================================================
def init_session_state():
    if "db" not in st.session_state:
        st.session_state.db = pd.DataFrame(
            columns=["id", "Data", "Cliente", "Serviço", "Valor", "Status"]
        )

    if "estoque" not in st.session_state:
        st.session_state.estoque = pd.DataFrame([
            {"Item": "Shampoo 5L", "Qtd": 80},
            {"Item": "Pretinho", "Qtd": 30},
            {"Item": "Cera", "Qtd": 50},
        ])

init_session_state()

# ======================================================
# COMPONENTES DE UI
# ======================================================
def sidebar_menu():
    st.sidebar.title("🧼 Lian Car v2.0")
    return st.sidebar.radio(
        "Navegação",
        ["Dashboard", "Agendamentos", "Estoque", "Fornecedores"]
    )

# ======================================================
# DASHBOARD
# ======================================================
def render_dashboard():
    st.title("📈 Dashboard de Performance")

    faturamento = st.session_state.db["Valor"].sum()
    total_servicos = len(st.session_state.db)
    ticket_medio = (
        faturamento / total_servicos if total_servicos > 0 else 0
    )

    c1, c2, c3 = st.columns(3)
    c1.metric("💰 Faturamento", f"R$ {faturamento:,.2f}")
    c2.metric("🧽 Serviços", total_servicos)
    c3.metric("📊 Ticket Médio", f"R$ {ticket_medio:,.2f}")

    st.divider()
    st.subheader("📋 Últimos Serviços")

    if total_servicos == 0:
        st.info("Nenhum serviço registrado ainda.")
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

    with st.form("form_agendamento"):
        cliente = st.text_input("Cliente")
        servico = st.selectbox("Serviço", ["Lavagem Simples", "Lavagem Completa", "Polimento"])
        valor = st.number_input("Valor (R$)", min_value=0.0, step=10.0)
        status = st.selectbox("Status", ["Agendado", "Concluído", "Cancelado"])

        submitted = st.form_submit_button("Salvar")

        if submitted:
            novo = {
                "id": len(st.session_state.db) + 1,
                "Data": datetime.now(),
                "Cliente": cliente,
                "Serviço": servico,
                "Valor": valor,
                "Status": status,
            }

            st.session_state.db = pd.concat(
                [st.session_state.db, pd.DataFrame([novo])],
                ignore_index=True
            )

            st.success("✅ Agendamento salvo com sucesso!")

# ======================================================
# ESTOQUE
# ======================================================
def render_estoque():
    st.title("📦 Controle de Estoque")
    st.dataframe(st.session_state.estoque, use_container_width=True)

# ======================================================
# FORNECEDORES (PLACEHOLDER)
# ======================================================
def render_fornecedores():
    st.title("🚚 Fornecedores")
    st.info("Módulo em desenvolvimento.")

# ======================================================
# ROUTER PRINCIPAL
# ======================================================
menu = sidebar_menu()

if menu == "Dashboard":
    render_dashboard()
elif menu == "Agendamentos":
    render_agendamentos()
elif menu == "Estoque":
    render_estoque()
elif menu == "Fornecedores":
    render_fornecedores()
