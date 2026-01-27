def financeiro():
    st.title("💰 Financeiro")

    conn = get_connection()

    # ===============================
    # ENTRADAS (SERVIÇOS CONCLUÍDOS)
    # ===============================
    df_entradas = pd.read_sql("""
        SELECT Data, Cliente, Servico, Valor
        FROM agendamentos
        WHERE Status = 'Concluído'
    """, conn)

    total_entradas = df_entradas["Valor"].sum() if not df_entradas.empty else 0

    # ===============================
    # SAÍDAS (DESPESAS)
    # ===============================
    df_saidas = pd.read_sql("""
        SELECT Data, Descricao, Valor
        FROM despesas
    """, conn)

    total_saidas = df_saidas["Valor"].sum() if not df_saidas.empty else 0

    # ===============================
    # INDICADORES
    # ===============================
    c1, c2, c3 = st.columns(3)
    c1.metric("📥 Entradas", moeda(total_entradas))
    c2.metric("📤 Saídas", moeda(total_saidas))
    c3.metric("📈 Lucro", moeda(total_entradas - total_saidas))

    st.markdown("---")

    # ===============================
    # LANÇAMENTO DE SAÍDA
    # ===============================
    st.subheader("📤 Lançar Nova Saída")

    with st.form("nova_saida"):
        descricao = st.text_input("Descrição da Despesa")
        valor = st.number_input("Valor (R$)", min_value=0.0)
        data = st.date_input("Data", date.today())

        if st.form_submit_button("Registrar Saída"):
            conn.execute("""
                INSERT INTO despesas (Data, Descricao, Valor)
                VALUES (?,?,?)
            """, (data.isoformat(), descricao, valor))
            conn.commit()
            st.success("Despesa registrada com sucesso!")
            st.rerun()

    st.markdown("---")

    # ===============================
    # TABELA DE ENTRADAS
    # ===============================
    st.subheader("📥 Entradas (Serviços Concluídos)")
    if df_entradas.empty:
        st.info("Nenhuma entrada registrada.")
    else:
        df_entradas["Data"] = df_entradas["Data"].apply(formatar_data_br)
        st.dataframe(df_entradas, use_container_width=True)

    # ===============================
    # TABELA DE SAÍDAS
    # ===============================
    st.subheader("📤 Saídas (Despesas)")
    if df_saidas.empty:
        st.info("Nenhuma despesa registrada.")
    else:
        df_saidas["Data"] = df_saidas["Data"].apply(formatar_data_br)
        st.dataframe(df_saidas, use_container_width=True)

    conn.close()
