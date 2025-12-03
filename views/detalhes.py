import streamlit as st

st.title("Painel de Dados")

if 'df_resultado' not in st.session_state or st.session_state['df_resultado'] is None:
    st.warning("Nenhum dado disponível. Processe arquivos na aba 'Extrator'.")
else:
    tab1, tab2 = st.tabs(["Tabela", "JSON"])
    with tab1:
        st.dataframe(st.session_state['df_resultado'], width='stretch')
    with tab2:
        st.json(st.session_state['json_resultado'])