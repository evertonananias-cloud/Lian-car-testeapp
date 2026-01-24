import streamlit as st
import pandas as pd
from datetime import datetime

# Estética Premium
st.set_page_config(page_title="Lian Car App", page_icon="🧼", layout="wide")

# CSS para Vibe Profissional
st.markdown("""
    <style>
    [data-testid="stMetricValue"] { color: #00d4ff; font-size: 32px; }
    .stTabs [data-baseweb="tab-list"] { gap: 20px; }
    .stTabs [data-baseweb="tab"] { height: 50px; border-radius: 10px 10px 0 0; }
    </style>
    """, unsafe_allow_html=True)

# Banco de Dados em Sessão (Reset ao fechar a aba)
if 'db' not in st.session_state:
    st.session_state.db = pd.DataFrame(columns=['id', 'Data', 'Cliente', 'Serviço', 'Valor', 'Status'])
if 'estoque' not in st.session_state:
    st.session_state.estoque = pd.DataFrame([
        {"Item": "Shampoo 5L", "Qtd": 80}, {"Item": "Pretinho", "Qtd": 30}, {"Item": "Cera", "Qtd": 50}
    ])

# Menu Lateral
st.sidebar.title("🧼 Lian Car v2.0")
menu = st.sidebar.radio("Navegação", ["Dashboard", "Agendamentos", "Fornecedores"])

# --- DASHBOARD ---
if menu == "Dashboard":
    st.title("📈 Dashboard de Performance")
    c1, c2, c3 = st.columns(3)
    c1.metric("Faturamento", f"R$ {st.session_state.db['Valor'].sum():,.2f}")
    c2.metric("Serviços", len(st.session_state.db))
    c3.metric("Ticket Médio", f"R$ {st.session_state.db['Valor'].mean() if len(st.session_state.db)>0 else 0:,.2f}")
    
    if not st.session_state.db.empty:
        st.bar_chart(st.session_state.db, x="Serviço", y="Valor", color="#00d4ff")

# --- AGENDAMENTOS (CRUD) ---
elif menu == "Agendamentos":
    st.title("📅 Gestão de Serviços")
    
    with st.expander("➕ Novo / Editar Registro"):
        c1, c2, c3 = st.columns(3)
        cli = c1.text_input("Cliente")
        ser = c2.selectbox("Serviço", ["Lavagem Simples", "Completa", "Polimento"])
        val = c3.number_input("Valor", min_value=0.0, value=50.0)
        
        if st.button("Salvar na Base"):
            new_id = int(datetime.now().timestamp())
            novo = pd.DataFrame([[new_id, datetime.now().strftime("%d/%m"), cli, ser, val, "Pendente"]], 
                                columns=['id', 'Data', 'Cliente', 'Serviço', 'Valor', 'Status'])
            st.session_state.db = pd.concat([st.session_state.db, novo], ignore_index=True)
            st.success("Lançado!")
            st.rerun()

    st.subheader("📋 Lista de Atendimentos")
    # O data_editor permite editar e excluir (clicando na linha e apertando Delete)
    edited_df = st.data_editor(st.session_state.db, num_rows="dynamic", use_container_width=True, key="editor_db")
    if st.button("Atualizar Banco de Dados"):
        st.session_state.db = edited_df
        st.toast("Dados sincronizados!")

# --- FORNECEDORES ---
elif menu == "Fornecedores":
    st.title("📦 Estoque & Compras")
    st.write("Acompanhe seus insumos em tempo real.")
    for i, row in st.session_state.estoque.iterrows():
        st.write(f"**{row['Item']}**")
        st.progress(row['Qtd']/100)
