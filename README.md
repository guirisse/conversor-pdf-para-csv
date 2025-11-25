# Extrator Inteligente de Notas Fiscais (NFe) com Gemini AI

## Sobre o Projeto

Este projeto é uma solução de automação de processos desenvolvida para extrair dados estruturados de notas fiscais eletrônicas em PDF. 

Utilizando a API do Google Gemini 2.5 flash-lite, o sistema é capaz de ler e interpretar os documentos visualmente, extraindo informações chave como número da nota, emitente, impostos e lista de itens. O resultado é consolidado em uma base de dados CSV pronta para análise ou inserção em banco de dados SQL.

## Funcionalidades

- Extração via GenAI: Utiliza LLMs para interpretar o contexto da nota.
- Processamento em Lote Capacidade de ler múltiplos arquivos PDF de uma pasta simultaneamente.
- Tratamento de Dados:
  - Normalização de valores monetários.
  - Validação básica de impostos (ICMS/IPI).
- Exportação: Gera um arquivo .csv formatado.

## Tecnologias Utilizadas

- Linguagem: Python
- IA / LLM: Google Generative AI (Gemini 2.5 Flash-Lite)
- Manipulação de Dados: Pandas
