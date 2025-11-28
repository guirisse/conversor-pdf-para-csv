import streamlit as st

st.markdown("<br>" * 5, unsafe_allow_html=True)
col1, col2 = st.columns(2, gap="small", vertical_alignment="center")

with col1:
    st.image("https://cdn-icons-png.flaticon.com/512/337/337946.png", width=230)

    st.title("Extrator NFe AI", anchor=False)
    st.write(
        "Automação inteligente para transformar Notas Fiscais em dados estratégicos."
    )    

with col2:
    st.write("\n")
    st.subheader("O que a ferramenta entrega?", anchor=False)
    st.write(
    """
    - **Economia de Tempo:** Reduza em até 90% o tempo de digitação manual.
    - **Precisão:** Elimine erros humanos de transcrição de valores e impostos.
    - **Alta Performance:** Processe dezenas de notas simultaneamente.
    - **Padronização:** Transforme layouts bagunçados em tabelas padrão.
    """
)

    st.write("\n")
    st.subheader("Como funciona?", anchor=False)
    st.write(
    """
    1. **Upload:** Arraste seus arquivos PDF (um ou vários).
    2. **Processamento:** Nossa IA lê e estrutura os dados em segundos.
    3. **Revisão:** Visualize os dados extraídos na tela antes de baixar.
    4. **Exportação:** Baixe tudo consolidado em uma planilha pronta.
    """
    )
