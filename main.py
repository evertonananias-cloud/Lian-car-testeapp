import streamlit as st
import pandas as pd
import sqlite3
import hashlib
import urllib.parse
from datetime import datetime, time

# --- CONFIGURAÇÕES E ESTILO ---
st.set_page_config(page_title="Lian Car - Gestão Profissional", layout="wide")

# --- BANCO DE DADOS ---
def init_db():
    conn = sqlite3.connect('lian_car.db')
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS clientes \
                 (id INTEGER PRIMARY KEY AUTOINCREMENT, nome TEXT, contato TEXT, placa TEXT UNIQUE)''')
    c.execute('''CREATE TABLE IF NOT EXISTS agendamentos \
                 (id INTEGER PRIMARY KEY AUTOINCREMENT, cliente_id INTEGER, servico TEXT, \
                  data TEXT, horario TEXT, valor REAL, status TEXT, \
                  FOREIGN KEY(cliente_id) REFERENCES clientes(id))''')
    c.execute('''CREATE TABLE IF NOT EXISTS despesas \
                 (id INTEGER PRIMARY KEY AUTOINCREMENT, descricao TEXT, categoria TEXT, valor REAL, data TEXT)''')
    conn.commit()
    conn.close()

init_db()

# --- SEGURANÇA ---
USUARIOS = {
    "admin": {"senha": hashlib.sha256("admin123".encode()).hexdigest(), "nivel": "admin"},
    "equipe": {"senha": hashlib.sha256("lian2024".encode()).hexdigest(), "nivel": "operacional"}
}

def login():
    if 'logado' not in st.session_state:
        st.sidebar.title("🔐 Acesso Lian Car")
        user = st.sidebar.text_input("Usuário")
        pw = st.sidebar.text_input("Senha", type="password")
        if st.sidebar.button("Entrar"):
            pw_hash = hashlib.sha256(pw.encode()).hexdigest()
            if user in USUARIOS and USUARIOS[user]["senha"] == pw_hash:
                st.session_state['logado'] = True
                st.session_state['nivel'] = USUARIOS[user]["nivel"]
                st.session_state['user'] = user
                st.rerun()
            else:
                st.sidebar.error("Credenciais inválidas")
        return False
    return True

# --- FUNÇÕES DE APOIO ---
SERVICOS = {
    "Lavagem Simples": 35.0,
    "Lavagem Completa": 60.0,
    "Higienização": 150.0,
    "Polimento": 250.0
}

def salvar_agendamento(nome, contato, placa, servico, data, hora, valor):
    conn = sqlite3.connect('lian_car.db')
    c = conn.cursor()
    c.execute("INSERT OR IGNORE INTO clientes (nome, contato, placa) VALUES (?,?,?)", (nome, contato, placa))
    c.execute("SELECT id FROM clientes WHERE placa=?", (placa,))
    c_id = c.fetchone()[0]
    c.execute("INSERT INTO agendamentos (cliente_id, servico, data, horario, valor, status) VALUES (?,?,?,?,?,?)",
              (c_id, servico, str(data), str(hora), valor, "Agendado"))
    conn.commit()
    conn.close()

# --- INTERFACE PRINCIPAL ---
if login():
    st.sidebar.success(f"Logado: {st.session_state['user']}")
    if st.sidebar.button("Sair"):
        del st.session_state['logado']
        st.rerun()

    menu = ["Dashboard", "Novo Agendamento", "Controle de Pátio", "Financeiro"]
    if st.session_state['nivel'] == "operacional":
        menu = ["Novo Agendamento", "Controle de Pátio"]
    
    choice = st.sidebar.radio("Navegar", menu)

    # --- MÓDULO: DASHBOARD ---
    if choice == "Dashboard":
        st.title("📊 Painel de Performance - Lian Car")
        conn = sqlite3.connect('lian_car.db')
        df_vendas = pd.read_sql_query("SELECT * FROM agendamentos WHERE status='Finalizado'", conn)
        df_gastos = pd.read_sql_query("SELECT * FROM despesas", conn)
        
        c1, c2, c3 = st.columns(3)
        receita = df_vendas['valor'].sum()
        gastos = df_gastos['valor'].sum()
        c1.metric("Faturamento Total", f"R$ {receita:.2f}")
        c2.metric("Despesas", f"R$ {gastos:.2f}")
        c3.metric("Lucro Líquido", f"R$ {receita - gastos:.2f}")
        
        st.subheader("Serviços Realizados")
        if not df_vendas.empty:
            st.bar_chart(df_vendas['servico'].value_counts())

    # --- MÓDULO: NOVO AGENDAMENTO ---
    elif choice == "Novo Agendamento":
        st.title("📅 Agendar Cliente")
        with st.form("agendar"):
            c1, c2 = st.columns(2)
            nome = c1.text_input("Nome do Cliente")
            placa = c1.text_input("Placa")
            contato = c2.text_input("WhatsApp (com DDD)")
            servico = c2.selectbox("Serviço", list(SERVICOS.keys()))
            data = st.date_input("Data")
            hora = st.time_input("Horário", time(8, 0))
            
            if st.form_submit_button("Confirmar e Gerar Comprovante"):
                salvar_agendamento(nome, contato, placa, servico, data, hora, SERVICOS[servico])
                msg = urllib.parse.quote(f"Olá {nome}! Confirmamos seu serviço {servico} na Lian Car dia {data} às {hora}. Valor: R$ {SERVICOS[servico]:.2f}")
                st.success("✅ Agendado!")
                st.markdown(f"[Enviar WhatsApp](https://wa.me/55{contato}?text={msg})")

    # --- MÓDULO: CONTROLE DE PÁTIO ---
    elif choice == "Controle de Pátio":
        st.title("🧼 Operação em Tempo Real")
        conn = sqlite3.connect('lian_car.db')
        df = pd.read_sql_query("SELECT a.id, c.nome, a.servico, a.status FROM agendamentos a JOIN clientes c ON a.cliente_id = c.id WHERE a.status != 'Finalizado'", conn)
        
        col1, col2, col3 = st.columns(3)
        for status, col in zip(["Agendado", "Em Lavagem", "Pronto"], [col1, col2, col3]):
            with col:
                st.subheader(status)
                items = df[df['status'] == status]
                for _, item in items.iterrows():
                    with st.expander(f"{item['nome']}"):
                        st.write(item['servico'])
                        if status == "Agendado":
                            if st.button("Iniciar", key=f"btn_{item['id']}"):
                                conn.execute("UPDATE agendamentos SET status='Em Lavagem' WHERE id=?", (item['id'],))
                                conn.commit()
                                st.rerun()
                        elif status == "Em Lavagem":
                            if st.button("Finalizar", key=f"btn_{item['id']}"):
                                conn.execute("UPDATE agendamentos SET status='Pronto' WHERE id=?", (item['id'],))
                                conn.commit()
                                st.rerun()
                        elif status == "Pronto":
                            if st.button("Entregue/Pago", key=f"btn_{item['id']}"):
                                conn.execute("UPDATE agendamentos SET status='Finalizado' WHERE id=?", (item['id'],))
                                conn.commit()
                                st.rerun()
        conn.close()

    # --- MÓDULO: FINANCEIRO ---
    elif choice == "Financeiro":
        st.title("💰 Caixa e Despesas")
        with st.expander("Registrar Nova Despesa"):
            desc = st.text_input("Descrição")
            valor_d = st.number_input("Valor R$", min_value=0.0)
            if st.button("Salvar Despesa"):
                conn = sqlite3.connect('lian_car.db')
                conn.execute("INSERT INTO despesas (descricao, valor, data) VALUES (?,?,?)", (desc, valor_d, str(datetime.now().date())))
                conn.commit()
                st.success("Gasto registrado!")
        
        conn = sqlite3.connect('lian_car.db')
        st.dataframe(pd.read_sql_query("SELECT * FROM despesas ORDER BY data DESC", conn), use_container_width=True)

else:
    st.title("🚿 Lian Car")
    st.info("Acesse com suas credenciais para gerenciar o lava-jato.")