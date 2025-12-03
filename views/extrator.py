import streamlit as st
from fonte import processar_pdfs_para_csv 
import fitz
from PIL import Image
from fonte import resetar_tudo

st.title("Upload e Processamento")

if 'arquivos_cache' not in st.session_state:
    st.session_state['arquivos_cache'] = None
if 'uploader_key' not in st.session_state:
    st.session_state['uploader_key'] = 0

uploads = st.session_state['arquivos_cache']

if uploads:
    col_info, col_btn = st.columns([3, 1])
    col_info.info(f"{len(uploads)} arquivos carregados na memória.")
    col_btn.button("Limpar arquivos armazenados", on_click=resetar_tudo, type="secondary", width='content')

if st.session_state['arquivos_cache'] is None:
    uploads = st.file_uploader(
        "Selecione PDFs", 
        type=["pdf"], 
        accept_multiple_files=True,
        key=f"uploader_{st.session_state['uploader_key']}" 
    )
    
    if uploads:
        st.session_state['arquivos_cache'] = uploads
        st.rerun()

if uploads:
    col_processar, col_download = st.columns([1, 1])
    
    with col_processar:
        if st.button("INICIAR EXTRAÇÃO", type="primary", width='stretch'):
            for f in uploads: f.seek(0)
            
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
                width='stretch',
                file_name="notas_consolidadas.csv",
                mime="text/csv"
            )

    st.markdown("### Galeria")
    cols = st.columns(4)
    for i, file in enumerate(uploads):
        with cols[i % 4]:
            file.seek(0)    
            doc = fitz.open(stream=file.read(), filetype="pdf")
            pix = doc.load_page(0).get_pixmap(matrix=fitz.Matrix(1, 1), alpha=False)
            img = Image.frombytes("RGB", [pix.width, pix.height], pix.samples)
            st.image(img, caption=file.name, width='stretch')
