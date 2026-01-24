import streamlit as st
import pandas as pd
from datetime import datetime

# --- CONFIGURAÇÃO BÁSICA ---
st.set_page_config(page_title="Lian Car | Gestão", layout="wide")

# Inicialização do Banco de Dados
if 'db' not in st.session_state:
    st.session_state.db = pd.DataFrame(columns=['id', 'Data', 'Cliente', 'Serviço', 'Valor', 'Status'])

st.title("🧼 Lian Car - Sistema de Gestão")

# --- MENU ---
menu = st.sidebar.selectbox("Menu", ["Dashboard", "Agendamentos"])

if menu == "Dashboard":
    st.header("📊 Resumo do Dia")
    if not st.session_state.db.empty:
        st.metric("Faturamento", f"R$ {st.session_state.db['Valor'].sum():,.2f}")
        st.bar_chart(st.session_state.db, x="Serviço", y="Valor")
    else:
        st.info("Nenhum dado registrado.")

elif menu == "Agendamentos":
    st.header("🚗 Novo Serviço")
    with st.form("add_form"):
        cli = st.text_input("Cliente")
        ser = st.selectbox("Serviço", ["Geral", "Simples", "Polimento"])
        val = st.number_input("Valor", min_value=0.0, value=100.0)
        if st.form_submit_button("Lançar"):
            new_id = int(datetime.now().timestamp())
            nova_linha = pd.DataFrame([[new_id, datetime.now().strftime("%d/%m"), cli, ser, val, "Pendente"]], 
                                     columns=['id', 'Data', 'Cliente', 'Serviço', 'Valor', 'Status'])
            st.session_state.db = pd.concat([st.session_state.db, nova_linha], ignore_index=True)
            st.success("Registrado!")
            st.rerun()

    st.divider()
    st.subheader("📋 Pátio")
    st.data_editor(st.session_state.db, num_rows="dynamic", use_container_width=True)
