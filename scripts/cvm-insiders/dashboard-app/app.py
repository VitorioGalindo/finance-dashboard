# dashboard-app/app.py

import streamlit as st
import pandas as pd
import sqlalchemy
import plotly.express as px
from datetime import date, timedelta

# --- 1. Configurações da Página e Título ---
st.set_page_config(layout="wide", page_title="Dashboard de Transações de Insiders")
st.title("📊 Dashboard de Análise de Transações de Insiders")

# --- 2. Conexão Segura com o Banco de Dados ---
# O Streamlit lê automaticamente o arquivo .streamlit/secrets.toml
try:
    db_url = st.secrets["DATABASE_URL"]
    engine = sqlalchemy.create_engine(db_url)
except Exception as e:
    st.error(f"Erro ao ler o segredo do banco de dados. Verifique seu arquivo .streamlit/secrets.toml. Detalhes: {e}")
    st.stop()

# --- 3. Carregamento e Cache dos Dados ---
# Esta função usa cache para que a consulta SQL pesada não seja executada a cada interação.
@st.cache_data(ttl=3600)
def load_data():
    """Carrega e une os dados de transações, insiders e companhias do banco."""
    query = """
    SELECT
        t.transaction_date,
        t.operation_type,
        t.quantity,
        t.price,
        t.volume,
        c.name AS company_name,
        i.name AS insider_name
    FROM transactions t
    JOIN insiders i ON t.insider_id = i.id
    JOIN companies c ON i.company_cnpj = c.cnpj;
    """
    try:
        with engine.connect() as connection:
            df = pd.read_sql(query, connection)
        df['transaction_date'] = pd.to_datetime(df['transaction_date'])
        return df
    except Exception as e:
        st.error(f"Erro ao carregar dados do banco: {e}")
        return pd.DataFrame()

# Executa a função para carregar os dados
df_full = load_data()

if df_full.empty:
    st.warning("Nenhum dado encontrado no banco de dados. Execute o pipeline de ETL primeiro.")
    st.stop()

# --- 4. Barra Lateral com Filtros Interativos ---
st.sidebar.header("Filtros")

# Filtro por Empresa
company_list = sorted(df_full['company_name'].unique())
selected_companies = st.sidebar.multiselect(
    "Empresa(s):",
    options=company_list,
    default=company_list[:3] if len(company_list) > 3 else company_list # Seleciona as 3 primeiras
)

# Filtro por Data
min_date = df_full['transaction_date'].min().date()
max_date = df_full['transaction_date'].max().date()
selected_dates = st.sidebar.date_input(
    "Período:",
    value=(max_date - timedelta(days=180), max_date),
    min_value=min_date,
    max_value=max_date,
)

# Aplica os filtros
if not selected_companies or len(selected_dates) != 2:
    st.warning("Por favor, selecione ao menos uma empresa e um período válido.")
    st.stop()

df_filtered = df_full[
    (df_full['company_name'].isin(selected_companies)) &
    (df_full['transaction_date'].dt.date >= selected_dates[0]) &
    (df_full['transaction_date'].dt.date <= selected_dates[1])
]

# --- 5. Visualizações: KPIs, Gráficos e Tabelas ---
if df_filtered.empty:
    st.info("Nenhum dado encontrado para os filtros selecionados.")
else:
    # Colunas de Métricas
    st.header("Resumo do Período")
    col1, col2, col3 = st.columns(3)
    
    total_volume = df_filtered['volume'].sum()
    insider_count = df_filtered['insider_name'].nunique()
    transaction_count = len(df_filtered)
    
    col1.metric("Volume Total (R$)", f"{total_volume:,.2f}")
    col2.metric("Insiders Ativos", f"{insider_count}")
    col3.metric("Nº de Transações", f"{transaction_count}")
    
    st.markdown("---")

    # Gráfico de Volume por Insider
    st.header("Top Insiders por Volume")
    df_insider_volume = df_filtered.groupby('insider_name')['volume'].sum().sort_values(ascending=False).head(15)
    fig = px.bar(
        df_insider_volume,
        x=df_insider_volume.values,
        y=df_insider_volume.index,
        orientation='h',
        title="Top 15 Insiders por Volume Transacionado (R$)",
        labels={'x': 'Volume (R$)', 'y': 'Insider'},
    )
    fig.update_layout(yaxis={'categoryorder':'total ascending'})
    st.plotly_chart(fig, use_container_width=True)

    # Tabela com dados detalhados
    st.header("Dados Detalhados")
    st.dataframe(df_filtered[['transaction_date', 'company_name', 'insider_name', 'operation_type', 'quantity', 'price', 'volume']].sort_values('transaction_date', ascending=False).reset_index(drop=True))