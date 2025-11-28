import streamlit as st
from fonte import processar_pdfs_para_csv 
import fitz
from PIL import Image

st.title("Upload e Processamento")

uploads = st.file_uploader("Selecione PDFs", type=["pdf"], accept_multiple_files=True)

if uploads:
    st.markdown("### Galeria")
    cols = st.columns(4)
    for idx, file in enumerate(uploads):
        with cols[idx % 4]:
            doc = fitz.open(stream=file.getvalue(), filetype="pdf")
            pix = doc.load_page(0).get_pixmap(matrix=fitz.Matrix(1, 1), alpha=False)
            img = Image.frombytes("RGB", [pix.width, pix.height], pix.samples)
            st.image(img, caption=file.name, use_container_width=True)
    
    st.markdown("---")

    col_processar, col_download = st.columns([1, 1])
    
    with col_processar:
        if st.button("INICIAR EXTRAÇÃO", type="primary"):
            df, jsons = processar_pdfs_para_csv(uploads)       
            st.session_state['df_resultado'] = df
            st.session_state['json_resultado'] = jsons
        
            if df is not None:
                st.success(f"Sucesso! {len(df)} notas extraídas.")
    with col_download:
        if st.session_state.get('df_resultado') is not None:
            
            csv = st.session_state['df_resultado'].to_csv(index=False, sep=';').encode('utf-8-sig')
            
            st.download_button(
                label="BAIXAR CSV",
                data=csv,
                file_name="notas_consolidadas.csv",
                mime="text/csv"
            )