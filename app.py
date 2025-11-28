import streamlit as st

home_page = st.Page(
    "views/home.py",
    title="Início",
    icon=":material/home:",
    default=True,
)

extrator_page = st.Page(
    "views/extrator.py",
    title="Extrator de NFe",
    icon=":material/upload_file:",
)

dashboard_page = st.Page(
    "views/detalhes.py",
    title="Análise de Dados",
    icon=":material/analytics:",
)

pg = st.navigation(
    {
        "Principal": [home_page],
        "Ferramentas": [extrator_page, dashboard_page],
    }
)

st.set_page_config(page_title="Extrator de dados de NFe", page_icon="", layout="wide")


if 'df_resultado' not in st.session_state:
    st.session_state['df_resultado'] = None
if 'json_resultado' not in st.session_state:
    st.session_state['json_resultado'] = None

st.sidebar.markdown("Feito por **Rox Partner**")

pg.run()