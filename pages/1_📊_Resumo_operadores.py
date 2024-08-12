import pandas as pd
import streamlit as st
from streamlit_echarts import st_echarts

# Função para carregar os dados com cache
@st.cache_data
def carregar_dados():
    df1 = pd.read_csv('https://drive.google.com/uc?id=1QiN_cQgpJsEOKs8aFUmXsDP0w82zl6lo', sep=';', low_memory=False)
    return df1

# Carregar os dados
df1 = carregar_dados()

# Dicionário de correção de operadores
operadores_correcao = {
    'Andressa': 'Andressa',
    'Bruna Evelyn': 'Bruna',
    'Bruno Gabriel': 'Bruno',
    'Carlos Eduardo': 'Carlos',
    'Eduardo Petriu': 'Eduardo',
    'Felipe Plantes': 'Felipe',
    'Higor Oliveira': 'Higor',
    'Isabelly': 'Isabelly',
    'Julia': 'Julia',
    'Jully Cristina': 'Jully',
    'Leonado Souza': 'Leonado',
    'Mayck Henrique': 'Mayck',
    'Pedro Domingos': 'Pedro',
    'Raissa Gonçaves': 'Raissa',
    'Sergio Gustavo': 'Sergio',
    'Sérgio Gustavo': 'Sergio',
    'Wendy': 'Wendy',
    'Yasmin Silva': 'Yasmin',
    'bruna.corandini': 'Bruna',
    'bruno.corandini': 'Bruno',
    'eduardo.corandini': 'Eduardo',
    'higor.corandini': 'Higor',
    'sérgio.corandini': 'Sergio',
    'wendy.corandini': 'Wendy'
}

def semana_do_mes(data):
    dia_do_mes = data.day
    semana = (dia_do_mes - 1) // 7 + 1
    return f'Semana {semana}'

def faixa_atraso(valor):
    if valor <= 180:
        return '2.1'
    elif valor <= 360:
        return '2.2'
    else:
        return '3'


df1['Data Cadastro Negociação'] = pd.to_datetime(df1['Data Cadastro Negociação'], dayfirst=True)

# Filtros de data na barra lateral
data_inicial = st.sidebar.date_input("Data Inicial", value=pd.to_datetime("2024-01-01").date())
data_final = st.sidebar.date_input("Data Final", value=pd.to_datetime("2024-12-31").date())

# Converter dates para datetime
data_inicial = pd.Timestamp(data_inicial)
data_final = pd.Timestamp(data_final)

# Filtragem do DataFrame com base nas datas selecionadas
df1 = df1[(df1['Data Cadastro Negociação'] >= data_inicial) & (df1['Data Cadastro Negociação'] <= data_final)]

# Aplicar as transformações
df1['Colaborador'] = df1['Colaborador'].replace(operadores_correcao)
df1['Data Cadastro Negociação'] = pd.to_datetime(df1['Data Cadastro Negociação'], format='%d/%m/%Y')
df1['faixa_atraso'] = df1['Dias em atraso'].apply(faixa_atraso)
df1['semana'] = df1['Data Cadastro Negociação'].apply(semana_do_mes)
df1['Valor Entrada'] = df1['Valor Entrada'].str.replace('.', '').str.replace(',', '.').astype(float)
df1['Valor Acordo'] = df1['Valor Acordo'].str.replace('.', '').str.replace(',', '.').astype(float)
df1['Acordos gerados'] = df1['Cpf/Cnpj']

# Criar a tabela dinâmica
table = pd.pivot_table(df1, values=['Acordos gerados', 'Valor Entrada'], index=['Colaborador'], columns=['semana'], aggfunc={'Acordos gerados': "count", 'Valor Entrada': "sum"})

# Exibir a tabela no Streamlit
st.title("Análise de Acordos")
st.dataframe(table) 

df_grafico = df1[['faixa_atraso', 'semana']]
grafico_dumies = pd.get_dummies(df_grafico['semana'], dtype=float)
table_grafico = pd.concat([df_grafico, grafico_dumies], axis=1)
table_grafico.drop('semana', axis=1, inplace=True)
grafico = table_grafico.groupby('faixa_atraso').sum().reset_index()

linhas = {}

for i, row in grafico.iterrows():
    key = str(row['faixa_atraso'])
    linhas[key] = row[1:].tolist()

titulos_colunas = grafico.columns[grafico.columns != 'faixa_atraso'].tolist()

linha_2_1 = linhas["2.1"]
linha_2_2 = linhas["2.2"]
linha_3 = linhas["3"]



options = {
    "title": {"text": "Acordos por semana/faixa"},
    "tooltip": {"trigger": "axis"},
    "legend": {"data": ["2.1", "2.2", "3"]},
    "grid": {"left": "3%", "right": "4%", "bottom": "3%", "containLabel": True},
    "toolbox": {"feature": {"saveAsImage": {}}},
    "xAxis": {
        "type": "category",
        "boundaryGap": False,
        "data": titulos_colunas,
    },
    "yAxis": {"type": "value"},
    "series": [
        {
            "name": "2.1",
            "type": "line",
            "stack": "Total",
            "data": linha_2_1,
        },
        {
            "name": "2.2",
            "type": "line",
            "stack": "Total",
            "data": linha_2_2,
        },
        {
            "name": "3",
            "type": "line",
            "stack": "Total",
            "data": linha_3,
        },
    ],
}
st_echarts(options=options, height="400px")


