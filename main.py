import streamlit as st
import pandas as pd
from datetime import date
from st_supabase_connection import SupabaseConnection, execute_query

# ======================================================
# CONFIGURAÇÃO
# ======================================================
st.set_page_config(page_title="Lian Car | Gestão Nuvem", page_icon="🧼", layout="wide")

# Conexão com Supabase via st.connection (usa secrets.toml)
supabase = st.connection("supabase", type=SupabaseConnection)


# ======================================================
# FUNÇÕES CENTRALIZADAS DE DADOS
# ======================================================

def carregar_dados(tabela: str) -> pd.DataFrame:
    """Lê todos os dados de uma tabela e retorna como DataFrame."""
    try:
        result = execute_query(
            supabase.table(tabela).select("*").order("id"),
            ttl=0  # sem cache — sempre busca dados frescos
        )
        df = pd.DataFrame(result.data)
        # Remove coluna 'id' da visualização (gerenciada pelo banco)
        if "id" in df.columns:
            df.drop(columns=["id"], inplace=True)
        return df
    except Exception as e:
        st.warning(f"⚠️ Não foi possível carregar '{tabela}': {e}")
        return pd.DataFrame()


def inserir_dado(tabela: str, dados: dict) -> bool:
    """Insere uma linha na tabela especificada com tratamento de erro."""
    try:
        execute_query(
            supabase.table(tabela).insert(dados),
            ttl=None  # writes não são cacheados
        )
        st.success(f"✅ Registro salvo em '{tabela}' com sucesso!")
        return True
    except Exception as e:
        st.error(f"❌ Erro ao inserir em '{tabela}': {e}")
        return False


def atualizar_dado(tabela: str, filtro: dict, dados: dict) -> bool:
    """Atualiza linhas na tabela que correspondem ao filtro."""
    try:
        query = supabase.table(tabela).update(dados)
        # Aplica filtros dinamicamente (ex: {"id": 5} → .eq("id", 5))
        for coluna, valor in filtro.items():
            query = query.eq(coluna, valor)
        execute_query(query, ttl=None)
        st.success(f"✅ Registro atualizado em '{tabela}'!")
        return True
    except Exception as e:
        st.error(f"❌ Erro ao atualizar '{tabela}': {e}")
        return False


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
        else:
            st.error("Usuário ou senha inválidos")
    st.stop()


# ======================================================
# MÓDULOS DE PÁGINAS
# ======================================================

def dashboard():
    st.title("📊 Painel de Controle")
    df_ag = carregar_dados("agendamentos")
    df_dp = carregar_dados("despesas")

    receita = (
        pd.to_numeric(df_ag.loc[df_ag["status"] == "Concluído", "valor"], errors="coerce").sum()
        if not df_ag.empty else 0
    )
    gastos = (
        pd.to_numeric(df_dp["valor"], errors="coerce").sum()
        if not df_dp.empty else 0
    )

    c1, c2, c3 = st.columns(3)
    c1.metric("Receita (Concluído)",  f"R$ {receita:,.2f}")
    c2.metric("Despesas Totais",      f"R$ {gastos:,.2f}")
    c3.metric("Lucro Líquido",        f"R$ {receita - gastos:,.2f}")


def agendamentos():
    st.title("📅 Agendamentos")
    df_s = carregar_dados("servicos")

    with st.form("form_ag"):
        c1, c2 = st.columns(2)
        cli  = c1.text_input("Cliente")
        pla  = c2.text_input("Placa")
        serv = st.selectbox("Serviço", df_s["nome"] if not df_s.empty else ["Cadastre serviços primeiro"])
        val  = st.number_input("Valor Final (R$)", min_value=0.0)

        if st.form_submit_button("Confirmar Agendamento"):
            if not cli or not pla:
                st.warning("⚠️ Cliente e Placa são obrigatórios.")
            else:
                if inserir_dado("agendamentos", {
                    "data":    date.today().isoformat(),
                    "cliente": cli,
                    "placa":   pla,
                    "servico": serv,
                    "valor":   val,
                    "status":  "Agendado"
                }):
                    st.rerun()

    st.subheader("Lista de Agendamentos")
    df = carregar_dados("agendamentos")
    if not df.empty:
        st.dataframe(df, use_container_width=True)
    else:
        st.info("Nenhum agendamento cadastrado.")


def patio():
    st.title("🚗 Pátio Operacional")

    # Busca com id para poder atualizar depois
    try:
        result = execute_query(
            supabase.table("agendamentos").select("*").neq("status", "Concluído").order("id"),
            ttl=0
        )
        pendentes = result.data
    except Exception as e:
        st.error(f"❌ Erro ao carregar pátio: {e}")
        pendentes = []

    if not pendentes:
        st.info("Pátio Vazio")
    else:
        for row in pendentes:
            with st.container():
                col1, col2 = st.columns([3, 1])
                col1.markdown(
                    f"<div class='card-patio'><b>{row['placa']}</b><br>{row['cliente']} - {row['servico']}</div>",
                    unsafe_allow_html=True
                )

                novo_st = col2.selectbox(
                    "Status",
                    ["Agendado", "Lavando", "Concluído"],
                    index=["Agendado", "Lavando", "Concluído"].index(row["status"]),
                    key=f"st_{row['id']}"
                )

                if novo_st != row["status"]:
                    if atualizar_dado("agendamentos", {"id": row["id"]}, {"status": novo_st}):
                        st.rerun()


def financeiro():
    st.title("💰 Fluxo de Caixa (Entradas e Saídas)")
    df_ag = carregar_dados("agendamentos")
    df_dp = carregar_dados("despesas")

    # Entradas automáticas
    if not df_ag.empty:
        entradas = df_ag[df_ag["status"] == "Concluído"][["data", "cliente", "valor"]].copy()
        entradas.rename(columns={"cliente": "Descrição"}, inplace=True)
        entradas["Tipo"] = "Entrada"
    else:
        entradas = pd.DataFrame(columns=["data", "Descrição", "valor", "Tipo"])

    # Saídas manuais
    if not df_dp.empty:
        saidas = df_dp[["data", "descricao", "valor"]].copy()
        saidas.rename(columns={"descricao": "Descrição"}, inplace=True)
        saidas["Tipo"] = "Saída"
    else:
        saidas = pd.DataFrame(columns=["data", "Descrição", "valor", "Tipo"])

    fluxo = pd.concat([entradas, saidas]).sort_values("data", ascending=False)

    st.write("### Lançar Saída")
    with st.form("saida"):
        desc = st.text_input("Descrição")
        v_s  = st.number_input("Valor", min_value=0.0)

        if st.form_submit_button("Salvar Saída"):
            if not desc or v_s <= 0:
                st.warning("⚠️ Descrição e Valor (maior que zero) são obrigatórios.")
            else:
                if inserir_dado("despesas", {
                    "data":      date.today().isoformat(),
                    "descricao": desc,
                    "valor":     v_s
                }):
                    st.rerun()

    st.subheader("Extrato Detalhado")
    if not fluxo.empty:
        st.dataframe(fluxo, use_container_width=True)
    else:
        st.info("Nenhum lançamento ainda.")


def estoque():
    st.title("📦 Estoque")

    with st.form("est"):
        it = st.text_input("Item")
        qt = st.number_input("Qtd", min_value=0)

        if st.form_submit_button("Adicionar ao Estoque"):
            if not it:
                st.warning("⚠️ Nome do item é obrigatório.")
            else:
                if inserir_dado("estoque", {"item": it, "qtd": qt}):
                    st.rerun()

    df = carregar_dados("estoque")
    if not df.empty:
        st.dataframe(df, use_container_width=True)
    else:
        st.info("Estoque vazio.")


def fornecedores():
    st.title("🏭 Fornecedores")

    with st.form("forn"):
        n = st.text_input("Nome")
        c = st.text_input("Contato")
        p = st.text_input("Produto")

        if st.form_submit_button("Salvar Fornecedor"):
            if not n or not c:
                st.warning("⚠️ Nome e Contato são obrigatórios.")
            else:
                if inserir_dado("fornecedores", {"nome": n, "contato": c, "produto": p}):
                    st.rerun()

    df = carregar_dados("fornecedores")
    if not df.empty:
        st.dataframe(df, use_container_width=True)
    else:
        st.info("Nenhum fornecedor cadastrado.")


def servicos():
    st.title("🛠️ Configurar Serviços")

    with st.form("serv"):
        n = st.text_input("Nome do Serviço")
        v = st.number_input("Valor (R$)", min_value=0.0)

        if st.form_submit_button("Cadastrar Serviço"):
            if not n:
                st.warning("⚠️ Nome do serviço é obrigatório.")
            else:
                if inserir_dado("servicos", {"nome": n, "valor": v}):
                    st.rerun()

    df = carregar_dados("servicos")
    if not df.empty:
        st.dataframe(df, use_container_width=True)
    else:
        st.info("Nenhum serviço cadastrado.")


# ======================================================
# MENU E NAVEGAÇÃO
# ======================================================
st.sidebar.title("Lian Car")
menu = st.sidebar.radio("Navegação", [
    "Dashboard", "Serviços", "Agendamentos",
    "Pátio", "Financeiro", "Estoque", "Fornecedores"
])

paginas = {
    "Dashboard":     dashboard,
    "Serviços":      servicos,
    "Agendamentos":  agendamentos,
    "Pátio":         patio,
    "Financeiro":    financeiro,
    "Estoque":       estoque,
    "Fornecedores":  fornecedores
}

paginas[menu]()
