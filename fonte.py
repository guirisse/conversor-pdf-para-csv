import os
import copy
import pandas as pd
import streamlit as st
from google import genai
from google.genai import types
from prompt import prompt_model_json
from dotenv import load_dotenv
import json 

st.set_page_config(
    page_title="Extrator de dados de NFe",
    layout="wide",
    initial_sidebar_state="expanded"
)

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

    if not lista_de_arquivos_pdf:
        return None, None, None

    lista_de_dataframes = []      
    lista_final_jsons = [] 
    barra_progresso = st.progress(0, text="Iniciando o processamento...")

    total_arquivos = len(lista_de_arquivos_pdf)
    
    for idx, file_obj in enumerate(lista_de_arquivos_pdf):
        barra_progresso.progress(idx / total_arquivos, text=f"Processando arquivo {idx + 1}/{total_arquivos}: {file_obj.name}")
            
        pdf_bytes = file_obj.getvalue() 
            
        json_pdf = extrair_dados(pdf_bytes)
        json_pdf_limpo = limpar_json(json_pdf)   
        dados_json = json.loads(json_pdf_limpo)

        base_calculo = float(dados_json.get('subtotal_da_nota') or 0)
        val_icms = float(dados_json.get('icms') or 0)
        val_ipi = float(dados_json.get('ipi') or 0)

        dados_json['icms_valido'] = calcular_icms(base_calculo, val_icms)
        dados_json['ipi_valido'] = calcular_ipi(base_calculo, val_ipi)

        lista_final_jsons.append(dados_json)

        dados_csv = copy.deepcopy(dados_json)

        lista_itens = dados_csv.get('itens')
            
        dados_csv['descricao_do_item'] = ", ".join([str(i.get('descricao_do_item', '')) for i in lista_itens])
        dados_csv['quantidade'] = ", ".join([str(i.get('quantidade', '')) for i in lista_itens])
        dados_csv['v_unitario'] = ", ".join([str(i.get('v_unitario', '')) for i in lista_itens])
            
        dados_csv.pop('itens', None)
            
        df_individual = pd.json_normalize(
        [dados_csv], 
        meta=[ 
            'numero_da_nota',
            'emitente',
            'nome_do_destinatario',
            'icms',
            'ipi',
            'subtotal_da_nota',                
            'total_da_nota',
            'icms_valido',  
            'ipi_valido',
            'descricao_do_item',
            'quantidade',
            'v_unitario'
            ]
        )
        
        lista_de_dataframes.append(df_individual)

        barra_progresso.progress((idx + 1) / total_arquivos, text=f"Concluído: {file_obj.name}")

    barra_progresso.empty()

    df_final_combinado = pd.concat(lista_de_dataframes, ignore_index=True)

    return df_final_combinado, lista_final_jsons

    return None, None


