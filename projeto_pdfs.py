import os
import pandas as pd
import gradio as gr
from google import genai
from google.genai import types
from dotenv import load_dotenv
import json 
import fitz
from PIL import Image

prompt_model_json = """
Você é um assistente de IA especializado em extração de dados de notas fiscais.

Entrada: Você receberá um arquivo PDF de uma nota fiscal.

INSTRUÇOES GERAIS: Você deve processar o arquivo PDF e extrair as informações,
estruturando-as exatamente como descrito abaixo em formato JSON.

CAMPOS A EXTRAIR (Manter a ordem e os nomes exatos):
    'numero_da_nota',
    'emitente',
    'nome_do_destinatario',
    'icms',
    'ipi',
    'total_da_nota',
    'subtotal_da_nota',
    'itens'

CAMPOS DE ITENS (Nível de Linha):
A nota pode ter um ou mais itens. Você deve criar um ARRAY JSON chamado 'itens'.
Para cada item listado na nota, crie um objeto dentro desse array com:
    'descricao_do_item',
    'quantidade',
    'v_unitario'

INSTRUÇÕES DE PARSING E REGRAS:
*Formato de Saída Obrigatório*: A saída deve ser um **único objeto JSON**.
NÃO o coloque dentro de um array []. Siga o exemplo rigorosamente.

*NUMERO DA NOTA*: não incluir a série da nota após o número.

*REMOÇÃO DE PRONOME DE TRATAMENTO*: Caso o nome possua um pronome de tratamento
em seu inicio (ex: "sra, sr, senhor, dr, etc."), considere apenas o nome.

*INSTRUÇÕES DE EMITENTE*: NUNCA insira o CNPJ no nome do emitente, apenas o nome da empresa

*UNIDADES* Não incluir unidades nas moedas, exemplos "R$".

*DECIMAIS*: USE "." COMO SEPARADOR DECIMAL DOS VALORES DE MOEDA, CASO ESTEJA COM "," VOCê PRECISA SUBSTITUIR

Se um campo não for encontrado, retorne o valor como null.

Se uma nota não tiver itens, retorne o array 'itens' como uma lista vazia [].

"""

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
    
    for file_obj in lista_de_arquivos_pdf:
        pdf_path = file_obj.name
        
        with open(pdf_path, "rb") as f:
            pdf_bytes = f.read()
        
        json_pdf = extrair_dados(pdf_bytes)
        json_pdf_limpo = limpar_json(json_pdf)   

        dados_json = json.loads(json_pdf_limpo)

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
                'icms',
                'ipi',
                'total_da_nota',
                'subtotal_da_nota',
                'icms_valido',  
                'ipi_valido',
                'descricao_do_item',
                'quantidade',
                'v_unitario'
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
        
    return csv_file_path

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
    
    with gr.Row():
        galeria_output = gr.Gallery(
            label="Pré-visualização dos arquivos",
            show_label=True,
            columns=[3],      # Quantas miniaturas por linha
            rows=[1],
            object_fit="contain", # Garante que a nota apareça inteira
            height="auto",
            allow_preview=True,   # Permite clicar para ver grande
            preview=True          # Já tenta mostrar um destaque se possível
        )

    with gr.Row():
        
        with gr.Column(scale=1):
            pdf_input = gr.File(
                label="Faça o upload dos PDFs aqui",
                file_types=[".pdf"],
                file_count="multiple",
                height=250
            )
            
            botao = gr.Button("Processar PDFs", variant="primary")

        with gr.Column(scale=1):   
            csv_output = gr.File(
                label="Baixar planilha consolidada",
                interactive=False,
                height=250
            )

    pdf_input.change(
        fn=gerar_previews,
        inputs=[pdf_input],
        outputs=[galeria_output]
    )
    
    botao.click(
        fn=processar_pdfs_para_csv,
        inputs=[pdf_input],
        outputs=[csv_output]
    )