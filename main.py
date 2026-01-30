import streamlit as st
import pandas as pd
from datetime import date
from streamlit_gsheets import GSheetsConnection

# ======================================================
# CONFIGURAÇÃO E CONEXÃO NUVEM
# ======================================================
st.set_page_config(page_title="Lian Car | Gestão Nuvem", page_icon="🧼", layout="wide")

# Conexão oficial com o Google Sheets
conn = st.connection("gsheets", type=GSheetsConnection)

def carregar_dados(aba):
    try:
        # Tenta ler a aba específica. ttl=0 evita que o Streamlit use cache antigo
        return conn.read(worksheet=aba, ttl=0)
    except Exception:
        # Se a aba estiver vazia ou não existir, cria estrutura padrão
        estruturas = {
            "agendamentos": ["Data", "Cliente", "Placa", "Servico", "Valor", "Status"],
            "despesas": ["Data", "Descricao", "Valor"],
            "estoque": ["Item", "Qtd"],
            "fornecedores": ["Nome", "Contato", "Produto"],
            "servicos": ["Nome", "Valor"]
        }
        return pd.DataFrame(columns=estruturas.get(aba, []))

# ======================================================
# ESTILO CSS
# ======================================================
st.markdown("""
<style>
    .stApp { background: #020617; color: #e5e7eb; }
    [data-testid="stMetric"] { background: #0f172a; border: 1px solid #1e293b; border-radius: 12px; }
    .card-patio { background: #1e293b; padding: 20px; border-radius: 15px; border-left: 6px solid #0ea5e9; margin-bottom: 10px; }
    .stButton>button { background: linear-gradient(135deg, #0ea5e9, #38bdf8); color: white; font-weight: bold; border-radius: 10px; }
</style>
""", unsafe_allow_html=True)

# ======================================================
# LOGIN
# ======================================================
if "logado" not in st.session_state:
    st.session_state.logado = False

if not st.session_state.logado:
    st.title("🔐 Acesso Lian Car")
    u, p = st.text_input("Usuário"), st.text_input("Senha", type="password")
    if st.button("Entrar"):
        if u == "admin" and p == "admin123":
            st.session_state.logado = True
            st.rerun()
        else: st.error("Usuário ou senha inválidos")
    st.stop()

# ======================================================
# MÓDULOS DE PÁGINAS
# ======================================================

def dashboard():
    st.title("📊 Painel de Controle")
    df_ag = carregar_dados("agendamentos")
    df_dp = carregar_dados("despesas")
    
    receita = pd.to_numeric(df_ag[df_ag["Status"] == "Concluído"]["Valor"]).sum() if not df_ag.empty else 0
    gastos = pd.to_numeric(df_dp["Valor"]).sum() if not df_dp.empty else 0
    
    c1, c2, c3 = st.columns(3)
    c1.metric("Receita (Concluído)", f"R$ {receita:,.2f}")
    c2.metric("Despesas Totais", f"R$ {gastos:,.2f}")
    c3.metric("Lucro Líquido", f"R$ {receita - gastos:,.2f}")

def agendamentos():
    st.title("📅 Agendamentos")
    df_s = carregar_dados("servicos")
    
    with st.form("form_ag"):
        c1, c2 = st.columns(2)
        cli = c1.text_input("Cliente")
        pla = c2.text_input("Placa")
        serv = st.selectbox("Serviço", df_s["Nome"] if not df_s.empty else ["Cadastre serviços primeiro"])
        val = st.number_input("Valor Final (R$)", min_value=0.0)
        if st.form_submit_button("Confirmar Agendamento"):
            novo = pd.DataFrame([[date.today().isoformat(), cli, pla, serv, val, "Agendado"]], columns=["Data", "Cliente", "Placa", "Servico", "Valor", "Status"])
            df_atual = carregar_dados("agendamentos")
            df_final = pd.concat([df_atual, novo], ignore_index=True)
            conn.update(worksheet="agendamentos", data=df_final)
            st.success("Salvo no Google Sheets!")
            st.rerun()

def patio():
    st.title("🚗 Pátio Operacional")
    df = carregar_dados("agendamentos")
    
    if df.empty:
        st.info("Pátio Vazio")
    else:
        # Filtra apenas os que não estão concluídos
        pendentes = df[df["Status"] != "Concluído"]
        for i, row in pendentes.iterrows():
            with st.container():
                col1, col2 = st.columns([3, 1])
                col1.markdown(f"<div class='card-patio'><b>{row['Placa']}</b><br>{row['Cliente']} - {row['Servico']}</div>", unsafe_allow_html=True)
                
                # Chave única por linha (i) para evitar bugs
                novo_st = col2.selectbox("Status", ["Agendado", "Lavando", "Concluído"], 
                                         index=["Agendado", "Lavando", "Concluído"].index(row["Status"]), 
                                         key=f"st_{i}")
                
                if novo_st != row["Status"]:
                    df.at[i, "Status"] = novo_st
                    conn.update(worksheet="agendamentos", data=df)
                    st.rerun()

def financeiro():
    st.title("💰 Fluxo de Caixa (Entradas e Saídas)")
    df_ag = carregar_dados("agendamentos")
    df_dp = carregar_dados("despesas")
    
    # Entradas Automáticas
    entradas = df_ag[df_ag["Status"] == "Concluído"][["Data", "Cliente", "Valor"]].copy()
    entradas["Tipo"] = "Entrada"
    
    # Saídas Manuais
    saidas = df_dp.copy()
    saidas["Tipo"] = "Saída"
    
    fluxo = pd.concat([entradas, saidas]).sort_values("Data", ascending=False)
    
    st.write("### Lançar Saída")
    with st.form("saida"):
        desc, v_s = st.text_input("Descrição"), st.number_input("Valor", min_value=0.0)
        if st.form_submit_button("Salvar Saída"):
            nova_s = pd.DataFrame([[date.today().isoformat(), desc, v_s]], columns=["Data", "Descricao", "Valor"])
            df_final = pd.concat([df_dp, nova_s], ignore_index=True)
            conn.update(worksheet="despesas", data=df_final)
            st.rerun()
            
    st.subheader("Extrato Detalhado")
    st.dataframe(fluxo, use_container_width=True)

def estoque():
    st.title("📦 Estoque")
    df = carregar_dados("estoque")
    with st.form("est"):
        it, qt = st.text_input("Item"), st.number_input("Qtd", min_value=0)
        if st.form_submit_button("Atualizar"):
            novo = pd.DataFrame([[it, qt]], columns=["Item", "Qtd"])
            df_final = pd.concat([df, novo], ignore_index=True)
            conn.update(worksheet="estoque", data=df_final)
            st.rerun()
    st.dataframe(df, use_container_width=True)

def fornecedores():
    st.title("🏭 Fornecedores")
    df = carregar_dados("fornecedores")
    with st.form("forn"):
        n, c, p = st.text_input("Nome"), st.text_input("Contato"), st.text_input("Produto")
        if st.form_submit_button("Salvar"):
            novo = pd.DataFrame([[n, c, p]], columns=["Nome", "Contato", "Produto"])
            df_final = pd.concat([df, novo], ignore_index=True)
            conn.update(worksheet="fornecedores", data=df_final)
            st.rerun()
    st.dataframe(df, use_container_width=True)

def servicos():
    st.title("🛠️ Configurar Serviços")
    df = carregar_dados("servicos")
    with st.form("serv"):
        n, v = st.text_input("Nome"), st.number_input("Valor", min_value=0.0)
        if st.form_submit_button("Cadastrar"):
            novo = pd.DataFrame([[n, v]], columns=["Nome", "Valor"])
            df_final = pd.concat([df, novo], ignore_index=True)
            conn.update(worksheet="servicos", data=df_final)
            st.rerun()
    st.dataframe(df, use_container_width=True)

# ======================================================
# MENU E NAVEGAÇÃO
# ======================================================
st.sidebar.title("Lian Car")
menu = st.sidebar.radio("Navegação", ["Dashboard", "Serviços", "Agendamentos", "Pátio", "Financeiro", "Estoque", "Fornecedores"])

paginas = {
    "Dashboard": dashboard, "Serviços": servicos, "Agendamentos": agendamentos,
    "Pátio": patio, "Financeiro": financeiro, "Estoque": estoque, "Fornecedores": fornecedores
}
paginas[menu]()
