import streamlit as st
import pandas as pd
import numpy as np

# Configuração da página do Streamlit
st.set_page_config(
    page_title="Estimativa de Geração Solar",
    page_icon="☀️",
    layout="wide"
)

# Título do aplicativo
st.title("Estimativas de Geração de Energia Solar")
st.markdown("---")

# Função para carregar os dados
@st.cache_data
def load_data(file_path):
    """Carrega o arquivo CSV e realiza o pré-processamento necessário."""
    try:
        df = pd.read_csv(file_path, sep=',')
        # A unidade no CSV é Wh/m²/dia, vamos convertê-la para kWh/m²/dia
        radiation_columns = ['00_ANNUAL', '01_JAN', '02_FEB', '03_MAR', '04_APR', '05_MAY', '06_JUN',
                             '07_JUL', '08_AUG', '09_SEP', '10_OCT', '11_NOV', '12_DEZ']
        for col in radiation_columns:
            if col in df.columns:
                df[col] = df[col].astype(str).str.replace(',', '.', regex=True)
                df[col] = pd.to_numeric(df[col], errors='coerce')
                # Converter de Wh/m²/dia para kWh/m²/dia
                df[col] = df[col] / 1000
        return df
    except FileNotFoundError:
        st.error(f"Erro: O arquivo '{file_path}' não foi encontrado.")
        return None

# Carregando o arquivo de dados
file_path = "radiation.csv"
df = load_data(file_path)

if df is not None:
    
    # Pré-processamento e seleção de dados
    cidades = df['MUNICIPIO'].unique()
    
    st.sidebar.header("Parâmetros do Sistema Solar")
    
    # Parâmetros de entrada do usuário
    selected_city = st.sidebar.selectbox("Selecione a Cidade:", cidades)
    
    # Obter os dados de radiação para a cidade selecionada
    rad_data = df[df['MUNICIPIO'] == selected_city].iloc[0]
    
    # Coletar os parâmetros técnicos da usina
    num_placas = st.sidebar.number_input("Número de Placas:", min_value=1, value=12, step=1)
    dimensao_placa = st.sidebar.number_input("Dimensão da Placa (m²):", min_value=0.1, value=1.74, step=0.1)
    eficiencia = st.sidebar.number_input("Eficiência do Módulo (%):", min_value=1.0, max_value=100.0, value=16.2, step=0.1)
    performance_ratio = st.sidebar.slider("Performance Ratio (PR):", min_value=0.5, max_value=1.0, value=0.75, step=0.01)

    # Fórmulas de cálculo
    
    # 1. Área Total do Painel (m²)
    area_total = num_placas * dimensao_placa
    
    # Radiação anual em kWh/m²/dia (já convertida na função de carregamento)
    rad_anual_kwh_m2_dia = rad_data['00_ANNUAL']
    
    # 2. Geração de Energia Teórica (kWh/ano)
    geracao_diaria_teorica = rad_anual_kwh_m2_dia * area_total * (eficiencia / 100)
    geracao_anual_teorica = geracao_diaria_teorica * 365
    
    # 3. Geração de Energia Real Estimada (kWh/ano)
    geracao_anual_real_estimada = geracao_anual_teorica * performance_ratio
    
    # Exibição dos resultados
    st.header(f"Resultados da Estimativa para {selected_city}")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.metric(
            label="Radiação Média Anual",
            value=f"{rad_anual_kwh_m2_dia:.2f} kWh/m²/dia"
        )
        st.metric(
            label="Geração de Energia Anual Teórica",
            value=f"{geracao_anual_teorica:,.2f} kWh/ano"
        )
        
    with col2:
        st.metric(
            label="Área Total dos Painéis",
            value=f"{area_total:.2f} m²"
        )
        
        st.metric(
            label="Geração de Energia Anual Estimada",
            value=f"{geracao_anual_real_estimada:,.2f} kWh/ano"
        )
    
    with col3:
        st.metric(
            label="Geração de Energia Média Mensal Estimada",
            value=f"{(geracao_anual_real_estimada / 12):,.2f} kWh/mês"
        )

    st.markdown("---")
    st.markdown("### Análise Mensal da Geração")
    
    # Calcular a geração mensal baseada nos dados do CSV (já convertidos)
    monthly_radiation = rad_data[['01_JAN', '02_FEB', '03_MAR', '04_APR', '05_MAY', '06_JUN',
                                  '07_JUL', '08_AUG', '09_SEP', '10_OCT', '11_NOV', '12_DEZ']]
    
    # Geração diária * dias do mês * pr
    monthly_geration = monthly_radiation * area_total * (eficiencia / 100) * 30.4375 * performance_ratio # Média de dias no mês
    
    monthly_geration_df = pd.DataFrame({
        'Mês': ['Jan', 'Fev', 'Mar', 'Abr', 'Mai', 'Jun', 'Jul', 'Ago', 'Set', 'Out', 'Nov', 'Dez'],
        'Geração Estimada (kWh)': monthly_geration.values
    })
    
    st.bar_chart(monthly_geration_df, x='Mês', y='Geração Estimada (kWh)')
    
    st.markdown("---")
    st.markdown(f"""
    <div style='text-align: justify; font-size: 0.9em; color: gray;'>
    **Observações:**
    - A radiação de referência é a média anual ou mensal extraída diretamente do arquivo CSV e convertida para kWh/m²/dia.
    - O Performance Ratio (PR) é um fator de perdas do sistema que considera fatores como temperatura, sujeira, sombreamento e perdas no inversor. Um valor típico varia de 0.70 a 0.85.
    - O cálculo da geração de energia é uma estimativa simplificada.
    </div>
    """, unsafe_allow_html=True)
