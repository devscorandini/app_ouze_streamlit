import streamlit as st
import pandas as pd
import pyecharts.options as opts
from pyecharts.charts import Funnel



st.set_page_config(
    page_title="Funil por faixa",
    layout='centered'
)


@st.cache_data
def load_data():
    # Carregar e processar os dados
    df = pd.read_parquet('https://drive.google.com/uc?id=1If7dvtEtLWU1wwmjzFBUvXvSVk-gJKOc')
    df_ajustes = pd.read_csv('https://drive.google.com/uc?id=1_4rrYDBhTcQffC55XxRUwiPueauhp3KG', encoding='Latin - 1', sep=';', low_memory=False)
    df_acordos = pd.read_csv('https://drive.google.com/uc?id=1QiN_cQgpJsEOKs8aFUmXsDP0w82zl6lo', sep=';', low_memory=False)
    df_carteira = pd.read_parquet('https://drive.google.com/uc?id=1LfEaWdHd3HtykKzQnvGMDwoeQFhWlDt3')

    df_acordos['Data Cadastro Negociação'] = pd.to_datetime(df_acordos['Data Cadastro Negociação'], format='%d/%m/%Y')
    df_carteira['data'] = pd.to_datetime(df_carteira['data'], format='%d/%m/%Y')

    return df, df_ajustes, df_acordos, df_carteira

# Caixa de seleção na lateral
opcao = st.sidebar.radio(
    'Escolha uma opção:',
    ('Único', 'Geral')
)

@st.cache_data
def process_data(df, df_ajustes, df_acordos, df_carteira, data_inicial, data_final, opcao):
    df = df[(df['data'] >= data_inicial) & (df['data'] <= data_final)]
    df_acordos = df_acordos[(df_acordos['Data Cadastro Negociação'] >= data_inicial) & (df_acordos['Data Cadastro Negociação'] <= data_final)]
    df_carteira = df_carteira[(df_carteira['data'] >= data_inicial) & (df_carteira['data'] <= data_final)]

    df_merged = pd.merge(df, df_ajustes, left_on='qualification', right_on='qualificação', how='inner')

    df_merged['atraso'] = pd.to_numeric(df_merged['atraso'], errors='coerce').fillna(0).astype(int)
    df_carteira['Atraso'] = pd.to_numeric(df_carteira['Atraso'], errors='coerce').fillna(0).astype(int)

    def faixa_atraso(valor):
        if valor <= 180:
            return '2.1'
        elif valor <= 360:
            return '2.2'
        else:
            return '3'
        
    df_merged['faixa_atraso'] = df_merged['atraso'].apply(faixa_atraso)
    df_acordos['faixa_atraso'] = df_acordos['Dias em atraso'].apply(faixa_atraso)
    df_carteira['faixa_atraso'] = df_carteira['Atraso'].apply(faixa_atraso)

    if opcao == 'Único':
        df_merged = df_merged.sort_values(by='filtro_cpca', ascending=False).drop_duplicates(subset=['mailing_data.data.Cpf Cnpj'])
        df_carteira = df_carteira.drop_duplicates(subset=['CpfCnpj'])
    else:
        # Para 'Geral', você pode definir a lógica para não remover duplicatas, se necessário
        df_merged = df_merged.copy()
        df_carteira = df_carteira.copy()

    df_merged = pd.pivot_table(df_merged, 
                        values=['mailing_data.data.Cpf Cnpj', 'Alo', 'filtro', 'filtro_cpca'], 
                        index='faixa_atraso', 
                        aggfunc={'mailing_data.data.Cpf Cnpj': 'count', 
                                 'Alo': 'sum', 
                                 'filtro': 'sum', 
                                 'filtro_cpca': 'sum'}).reset_index()

    df = df_merged.rename(columns={
        'mailing_data.data.Cpf Cnpj': 'discados', 
        'Alo': 'alo', 
        'filtro': 'cpc', 
        'filtro_cpca': 'cpca'
    })

    df_cart = pd.pivot_table(df_carteira, 
                             values='CpfCnpj', 
                             index='faixa_atraso', 
                             aggfunc='count').reset_index()

    df_cart = df_cart.rename(columns={'CpfCnpj': 'carteira'})

    df_acd = pd.pivot_table(df_acordos, 
                            values='Cpf/Cnpj', 
                            index='faixa_atraso', 
                            aggfunc='count').reset_index()

    df_acd = df_acd.rename(columns={'Cpf/Cnpj': 'acordos'})

    sintetico = df_cart.merge(df).merge(df_acd)
    table = pd.pivot_table(sintetico, values=['carteira', 'discados', 'alo', 'cpc', 'cpca', 'acordos'], index=['faixa_atraso'], aggfunc='sum').reset_index()

    return table

def create_funnel_chart(data, title):
    return (
        Funnel()
        .add(
            series_name="",
            data_pair=data,
            gap=2,
            tooltip_opts=opts.TooltipOpts(trigger="item", formatter="{a} <br/>{b} : {c}%"),
            label_opts=opts.LabelOpts(is_show=True, position="inside"),
            itemstyle_opts=opts.ItemStyleOpts(border_color="#fff", border_width=1),
        )
        .set_global_opts(title_opts=opts.TitleOpts(title=title, subtitle=""))
    )

# Inputs da sidebar
st.sidebar.header('Configurações de Data')

# Carregar e processar os dados com cache
df, df_ajustes, df_acordos, df_carteira = load_data()

data_minima = df_carteira['data'].min()
data_maxima = df_carteira['data'].max()

input1 = st.sidebar.date_input('Data Inicial', value=pd.to_datetime('2024-08-01'), min_value=data_minima)
input2 = st.sidebar.date_input('Data Final', value=pd.to_datetime('2024-08-07'), max_value=data_maxima)

data_inicial = pd.to_datetime(input1, format='%Y-%m-%d')
data_final = pd.to_datetime(input2, format='%Y-%m-%d')

funil = process_data(df, df_ajustes, df_acordos, df_carteira, data_inicial, data_final, opcao)


# Preparar os dados
linhas = {}
for i, row in funil.iterrows():
    key = str(row['faixa_atraso'])
    linhas[key] = row[1:].tolist()

titulos_colunas = funil.columns[funil.columns != 'faixa_atraso'].tolist()

linha_2_1 = linhas.get("2.1", [0] * len(titulos_colunas))
linha_2_2 = linhas.get("2.2", [0] * len(titulos_colunas))
linha_3 = linhas.get("3", [0] * len(titulos_colunas))

data_2_1 = [[titulos_colunas[i], linha_2_1[i]] for i in range(len(titulos_colunas))]
data_2_2 = [[titulos_colunas[i], linha_2_2[i]] for i in range(len(titulos_colunas))]
data_3 = [[titulos_colunas[i], linha_3[i]] for i in range(len(titulos_colunas))]

rotulo_2_1 = [f"{titulos_colunas[i]} - {linha_2_1[i]}" for i in range(len(titulos_colunas))]
rotulo_2_2 = [f"{titulos_colunas[i]} - {linha_2_2[i]}" for i in range(len(titulos_colunas))]
rotulo_3 = [f"{titulos_colunas[i]} - {linha_3[i]}" for i in range(len(titulos_colunas))]

percentuais = [20, 68, 100, 52, 36, 84]

data_2_1 = [[rotulo_2_1[i], percentuais[i]] for i in range(len(rotulo_2_1))]
data_2_2 = [[rotulo_2_2[i], percentuais[i]] for i in range(len(rotulo_2_2))]
data_3 = [[rotulo_3[i], percentuais[i]] for i in range(len(rotulo_3))]

# Criar os gráficos de funil
funnel_2_1 = create_funnel_chart(data_2_1, "Faixa 2.1")
funnel_2_2 = create_funnel_chart(data_2_2, "Faixa 2.2")
funnel_3 = create_funnel_chart(data_3, "Faixa 3")

# Renderizar os gráficos como HTML
funnel_2_1_html = funnel_2_1.render_embed()
funnel_2_2_html = funnel_2_2.render_embed()
funnel_3_html = funnel_3.render_embed()

# Exibir os gráficos um embaixo do outro no Streamlit
st.title('Gráficos de Funil')

# Centralizar os gráficos
st.markdown(
    """
    <style>
    .centered {
        display: flex;
        flex-direction: column;
        align-items: center;
        margin: 0 auto;
    }
    </style>
    """,
    unsafe_allow_html=True
)

st.markdown('<div class="centered">', unsafe_allow_html=True)

st.components.v1.html(funnel_2_1_html, height=600, width=1000)
st.components.v1.html(funnel_2_2_html, height=600, width=1000)
st.components.v1.html(funnel_3_html, height=600, width=1000)
