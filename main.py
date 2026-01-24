import streamlit as st
import pandas as pd
from datetime import datetime

# --- CONFIGURAÇÃO VISUAL ---
st.set_page_config(page_title="Lian Car | Gestão", page_icon="🧼", layout="wide")

# Estilização Dark Mode Premium
st.markdown("""
    <style>
    .stApp { background-color: #0e1117; color: white; }
    .stMetric { background-color: #1f2937; padding: 15px; border-radius: 10px; border-left: 5px solid #00d4ff; }
    </style>
    """, unsafe_allow_stdio=True)

# --- INICIALIZAÇÃO DO BANCO DE DADOS ---
if 'db' not in st.session_state:
    st.session_state.db = pd.DataFrame(columns=['id', 'Data', 'Cliente', 'Serviço', 'Valor', 'Status'])

# --- MENU LATERAL ---
st.sidebar.title("🧼 Lian Car Control")
menu = st.sidebar.radio("Navegação", ["📊 Dashboard", "🚗 Agendamentos", "📦 Fornecedores"])

# --- FUNÇÕES ---
def adicionar_servico(cli, ser, val):
    new_id = int(datetime.now().timestamp())
    data_atual = datetime.now().strftime("%d/%m %H:%M")
    nova_linha = pd.DataFrame([[new_id, data_atual, cli, ser, val, "Pendente"]], 
                             columns=['id', 'Data', 'Cliente', 'Serviço', 'Valor', 'Status'])
    st.session_state.db = pd.concat([st.session_state.db, nova_linha], ignore_index=True)

# --- MÓDULO: DASHBOARD ---
if menu == "📊 Dashboard":
    st.title("📊 Painel de Performance")
    if not st.session_state.db.empty:
        c1, c2, c3 = st.columns(3)
        c1.metric("Receita Total", f"R$ {st.session_state.db['Valor'].sum():,.2f}")
        c2.metric("Serviços", len(st.session_state.db))
        c3.metric("Ticket Médio", f"R$ {st.session_state.db['Valor'].mean():,.2f}")
        st.bar_chart(st.session_state.db, x="Serviço", y="Valor")
    else:
        st.info("Nenhum dado registrado ainda.")

# --- MÓDULO: AGENDAMENTOS (CRUD COMPLETO) ---
elif menu == "🚗 Agendamentos":
    st.title("🚗 Gestão de Serviços")
    
    # Formulário de Cadastro
    with st.expander("➕ Novo Agendamento"):
        c1, c2, c3 = st.columns(3)
        u_cli = c1.text_input("Nome do Cliente")
        u_ser = c2.selectbox("Serviço", ["Geral", "Lavagem Simples", "Polimento", "Higienização"])
        u_val = c3.number_input("Valor (R$)", min_value=0.0, value=100.0)
        if st.button("Lançar Serviço"):
            adicionar_servico(u_cli, u_ser, u_val)
            st.success("Registrado com sucesso!")
            st.rerun()

    st.divider()
    
    # Tabela Interativa (Edição e Exclusão)
    st.subheader("📋 Pátio e Histórico")
    st.write("Dica: Para **deletar**, selecione a linha e aperte 'Delete' no teclado.")
    
    edited_df = st.data_editor(
        st.session_state.db,
        num_rows="dynamic", # Permite excluir e adicionar linhas manualmente
        use_container_width=True,
        column_config={
            "id": None, # Esconde o ID técnico
            "Status": st.column_config.SelectboxColumn("Status", options=["Pendente", "Lavando", "Finalizado"]),
            "Valor": st.column_config.NumberColumn("Valor R$", format="R$ %.2f")
        },
        key="editor_tabela"
    )
    
    if st.button("💾 Salvar Alterações da Tabela"):
        st.session_state.db = edited_df
        st.toast("Banco de dados atualizado!")

# --- MÓDULO: FORNECEDORES ---
elif menu == "📦 Fornecedores":
    st.title("📦 Insumos & Fornecedores")
    st.info("Módulo de estoque em desenvolvimento. Aqui você poderá cadastrar seus fornecedores de produtos químicos.")
