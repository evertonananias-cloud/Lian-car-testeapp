import streamlit as st
import pandas as pd
from datetime import datetime

# --- CONFIGURAÇÃO VISUAL DA LIAN CAR ---
st.set_page_config(page_title="Lian Car | Gestão 2.0", page_icon="🧼", layout="wide")

st.markdown("""
    <style>
    .stApp { background-color: #0e1117; color: white; }
    .stMetric { background-color: #1f2937; padding: 20px; border-radius: 12px; border-bottom: 4px solid #00d4ff; }
    .stTabs [data-baseweb="tab-list"] { gap: 10px; }
    .stTabs [data-baseweb="tab"] { 
        background-color: #1f2937; border-radius: 5px; padding: 10px 20px; color: white;
    }
    </style>
    """, unsafe_allow_stdio=True)

# --- INICIALIZAÇÃO DO BANCO DE DADOS (SESSION STATE) ---
if 'db' not in st.session_state:
    st.session_state.db = pd.DataFrame(columns=['id', 'Data', 'Cliente', 'Serviço', 'Valor', 'Status'])

if 'estoque' not in st.session_state:
    st.session_state.estoque = pd.DataFrame([
        {"Item": "Shampoo Ativado (L)", "Qtd": 85, "Fornecedor": "QuimicClean"},
        {"Item": "Cera de Carnaúba", "Qtd": 40, "Fornecedor": "AutoBrilho"},
        {"Item": "Pretinho Premium", "Qtd": 15, "Fornecedor": "SulQuimica"}
    ])

# --- BARRA LATERAL ---
st.sidebar.image("https://cdn-icons-png.flaticon.com/512/2966/2966480.png", width=100)
st.sidebar.title("Lian Car Control")
menu = st.sidebar.selectbox("Ir para:", ["📊 Dashboard", "🚗 Agendamentos & Fluxo", "📦 Estoque & Fornecedores"])

# --- MÓDULO: DASHBOARD ---
if menu == "📊 Dashboard":
    st.title("📈 Performance Lian Car")
    
    if not st.session_state.db.empty:
        c1, c2, c3 = st.columns(3)
        receita = st.session_state.db['Valor'].sum()
        servicos = len(st.session_state.db)
        ticket = receita / servicos if servicos > 0 else 0
        
        c1.metric("Faturamento Bruto", f"R$ {receita:,.2f}")
        c2.metric("Total de Lavagens", servicos)
        c3.metric("Ticket Médio", f"R$ {ticket:,.2f}")
        
        st.divider()
        st.subheader("Volume de Vendas por Serviço")
        st.bar_chart(st.session_state.db, x="Serviço", y="Valor", color="#00d4ff")
    else:
        st.info("Aguardando os primeiros dados para gerar o dashboard. Comece pelos agendamentos!")

# --- MÓDULO: AGENDAMENTOS (CRUD) ---
elif menu == "🚗 Agendamentos & Fluxo":
    st.title("📅 Gestão do Pátio")
    
    with st.expander("➕ Novo Agendamento / Edição Rápida", expanded=False):
        c1, c2, c3 = st.columns([2, 2, 1])
        cli = c1.text_input("Nome do Cliente")
        ser = c2.selectbox("Tipo de Serviço", ["Lavagem Simples", "Completa", "Polimento", "Higienização Interna"])
        val = c3.number_input("Valor (R$)", min_value=0.0, step=10.0, value=50.0)
        
        if st.button("Confirmar Entrada 🚀"):
            new_id = int(datetime.now().timestamp())
            nova_entrada = pd.DataFrame([[new_id, datetime.now().strftime("%d/%m %H:%M"), cli, ser, val, "Na Fila"]], 
                                       columns=['id', 'Data', 'Cliente', 'Serviço', 'Valor', 'Status'])
            st.session_state.db = pd.concat([st.session_state.db, nova_entrada], ignore_index=True)
            st.success(f"Veículo de {cli} registrado!")
            st.rerun()

    st.divider()
    
    st.subheader("📋 Tabela de Controle (Edite ou Exclua aqui)")
    # O data_editor permite editar valores e excluir linhas (selecionando e apertando Del)
    edited_df = st.data_editor(
        st.session_state.db, 
        num_rows="dynamic", # Permite excluir linhas
        use_container_width=True,
        column_config={
            "id": None, # Oculta o ID
            "Status": st.column_config.SelectboxColumn("Status", options=["Na Fila", "Lavando", "Finalizado", "Entregue"]),
            "Valor": st.column_config.NumberColumn("Valor R$", format="R$ %.2f")
        }
    )
    
    if st.button("💾 Salvar Alterações"):
        st.session_state.db = edited_df
        st.toast("Banco de dados atualizado!")

# --- MÓDULO: FORNECEDORES & ESTOQUE ---
elif menu == "📦 Estoque & Fornecedores":
    st.title("📦 Insumos e Parceiros")
    
    col_e, col_f = st.columns([2, 1])
    
    with col_e:
        st.subheader("Níveis de Estoque")
        for i, row in st.session_state.estoque.iterrows():
            st.write(f"**{row['Item']}** ({row['Fornecedor']})")
            cor = "red" if row['Qtd'] < 30 else "green"
            st.progress(row['Qtd'] / 100)
            
    with col_f:
        st.subheader("Ações")
        if st.button("Simular Pedido de Compra"):
            st.warning("Gerando lista de necessidades...")
            st.info("Shampoo - Pedir 10L\nPretinho - Pedir 5L")

st.sidebar.divider()
st.sidebar.caption("Lian Car v2.1 | Powered by Vibe Coding")
