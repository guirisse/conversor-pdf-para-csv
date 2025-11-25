import os
import pandas as pd
import gradio as gr
from google import genai
from google.genai import types
from prompt import prompt_model_json
from dotenv import load_dotenv
import json 
import fitz
from PIL import Image

load_dotenv()

client = genai.Client(
    api_key=os.getenv("GEMINI_API_KEY")
)
model='gemini-2.5-flash-lite'

def extrair_dados(pdf_em_bytes):
  response = client.models.generate_content(
    model=model,
    contents=[
        types.Part.from_bytes(
          data=pdf_em_bytes,
          mime_type='application/pdf',
        ),
        prompt_model_json])
  return response.text

def limpar_json(json_sujo):
    if "```json" in json_sujo:
        json_sujo = json_sujo.split("```json", 1)[1]
    
    if "```" in json_sujo:
        json_sujo = json_sujo.rsplit("```", 1)[0]
        
    return json_sujo.strip()

def calcular_icms(subtotal, valor_icms):
    base1 = subtotal * 0.12
    if abs(base1-valor_icms) < 0.01:
        return 'Correto'
    else:    
        return 'Incorreto'

def calcular_ipi(subtotal, valor_ipi):
    base2 = subtotal * 0.04
    if abs(base2 - valor_ipi) < 0.01:
        return 'Correto'
    else:
        return 'Incorreto'

def processar_pdfs_para_csv(lista_de_arquivos_pdf):

    lista_de_dataframes = []      
    json_gradio = []
    
    for file_obj in lista_de_arquivos_pdf:
        pdf_path = file_obj.name
        
        with open(pdf_path, "rb") as f:
            pdf_bytes = f.read()
        
        json_pdf = extrair_dados(pdf_bytes)
        json_pdf_limpo = limpar_json(json_pdf)   

        dados_json = json.loads(json_pdf_limpo)

        json_gradio.append(dados_json)

        base_calculo = float(dados_json.get('subtotal_da_nota', '0'))
        val_icms = float(dados_json.get('icms', '0'))
        val_ipi = float(dados_json.get('ipi', '0'))

        dados_json['icms_valido'] = calcular_icms(base_calculo, val_icms)
        dados_json['ipi_valido'] = calcular_ipi(base_calculo, val_ipi)

        lista_itens = dados_json.get('itens')

        descricoes = [str(i.get('descricao_do_item', '')) for i in lista_itens]
        quantidades = [str(i.get('quantidade', '')) for i in lista_itens]
        valores = [str(i.get('v_unitario', '')) for i in lista_itens]
        
        dados_json['descricao_do_item'] = ", ".join(descricoes)
        dados_json['quantidade'] = ", ".join(quantidades)
        dados_json['v_unitario'] = ", ".join(valores)
        
        dados_json.pop('itens', None)
        
        df_individual = pd.json_normalize(
            [dados_json], 
            meta=[ 
                'numero_da_nota',
                'emitente',
                'nome_do_destinatario',
                'descricao_do_item',
                'quantidade',
                'v_unitario',
                'subtotal_da_nota',
                'icms',
                'ipi',
                'total_da_nota',
                'icms_valido',  
                'ipi_valido',
            ],
            errors='ignore'  
        )
        
        lista_de_dataframes.append(df_individual)

    df_final_combinado = pd.concat(lista_de_dataframes, ignore_index=True)
    
    csv_file_path = "bases_csv/base_consolidada_nfe.csv"
    df_final_combinado.to_csv(
        csv_file_path, 
        index=False, 
        encoding='utf-8-sig',
        sep=';' 
    )
        
    return csv_file_path, df_final_combinado, json_gradio

def gerar_previews(lista_de_arquivos):

    carrossel = []
    
    for arquivo in lista_de_arquivos:
        doc = fitz.open(arquivo.name) # Seleção do pdf
        pagina = doc.load_page(0) # Load da primeira pagina do pdf anexado
        pix = pagina.get_pixmap(dpi=300) # Mapeamento da pagina pra criação de uma imagem
        img = Image.frombytes("RGB", [pix.width, pix.height], pix.samples) # Criação da imagem
        
        nome_pdf = os.path.basename(arquivo.name) # Definicação do nome do PDF pra legenda abaixo da imagem
        carrossel.append((img, nome_pdf)) # Junção da imagem + nome
            
        doc.close()
    return carrossel

with gr.Blocks(gr.themes.Soft(primary_hue=gr.themes.colors.red,secondary_hue=gr.themes.colors.red,font=gr.themes.GoogleFont("Roboto"))) as demo:
    
    gr.Markdown("# Extrator de dados de Notas Fiscais")
    
    with gr.Tabs():
            
        with gr.TabItem("Upload e Processamento"):               
            with gr.Row():
                galeria_output = gr.Gallery(
                        label="Pré-visualização dos arquivos",
                        show_label=True, # Fica mais limpo sem label repetida
                        columns=[4],
                        rows=[1],
                        object_fit="contain", # Zoom para leitura do cabeçalho
                        height="auto",
                        allow_preview=True,
                        preview=True
                    )
            with gr.Row():
                with gr.Column(scale=1):
                    pdf_input = gr.File(
                        label="Insira seus PDFs aqui",
                        file_types=[".pdf"],
                        file_count="multiple",
                        height=250
                        )                                          
                    botao_processar = gr.Button("Processar PDFs", variant="primary")    

                with gr.Column(scale=1):
                    csv_output = gr.File(
                        label="Baixar Planilha Consolidada",
                        interactive=False,
                        height=250
                        )

        with gr.TabItem("Visualização Detalhada"):             
            with gr.Row():
                with gr.Column(scale=1):
                        json_output = gr.JSON(
                            label="JSON Estruturado",
                        )                   
                with gr.Column(scale=1):
                        dataframe_output = gr.Dataframe(
                            label="Tabela de Dados",
                            interactive=False
                        )

            pdf_input.change(
                fn=gerar_previews,
                inputs=[pdf_input],
                outputs=[galeria_output]
        )
        
            botao_processar.click(
                fn=processar_pdfs_para_csv,
                inputs=[pdf_input],
                outputs=[csv_output, dataframe_output, json_output]
        )
    demo.launch(share=False)   