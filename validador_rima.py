import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime

import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime

# Aircraft capacity dictionary
AIRCRAFT_CAPACITY = {
    'C208': 9,
    'E295': 136,
    'A319': 144,
    'A320': 180,
    'A321': 224,
    'A20N': 180,
    '32Q': 180,
    'A332': 268,
    '339': 298,
    'AT72': 72,
    'E195': 118,
    'B738': 186,
    'B737': 138,
    'B738W': 186,
    'AT76': 72,
    'A21N': 224
}

def validate_passenger_count(df):
    """Validate passenger counts and add necessary columns for analysis."""
    # Add capacity column based on aircraft type
    df['AIRCRAFT_CAPACITY'] = df['AERONAVE_TIPO'].map(AIRCRAFT_CAPACITY)
    
    # Calculate total passengers
    df['TOTAL_PAX'] = df['PAX_LOCAL'] + df['PAX_CONEXAO_DOMESTICO'] + df['PAX_CONEXAO_INTERNACIONAL']
    
    # Calculate occupancy rate
    df['OCCUPANCY_RATE'] = df.apply(
        lambda row: (row['TOTAL_PAX'] / row['AIRCRAFT_CAPACITY'] * 100) 
        if pd.notnull(row['AIRCRAFT_CAPACITY']) and row['AIRCRAFT_CAPACITY'] > 0 
        else None, 
        axis=1
    )
    
    # Check for capacity violations
    df['EXCEEDS_CAPACITY'] = False
    df.loc[df['AIRCRAFT_CAPACITY'].notna(), 'EXCEEDS_CAPACITY'] = \
        df.loc[df['AIRCRAFT_CAPACITY'].notna(), 'TOTAL_PAX'] > df.loc[df['AIRCRAFT_CAPACITY'].notna(), 'AIRCRAFT_CAPACITY']
    
    # Validate GERAL flights
    df['GERAL_PAX_VIOLATION'] = (df['AERONAVE_OPERADOR'] == 'GERAL') & (df['TOTAL_PAX'] > 0)
    
    # Create operation type column
    df['OPERATION_TYPE'] = df['AERONAVE_OPERADOR'].apply(
        lambda x: 'Aviação Geral' if x == 'GERAL' else 'Aviação Comercial'
    )
    
    return df

def validate_passenger_count(df):
    """Validate passenger counts and add necessary columns for analysis."""
    # Add capacity column based on aircraft type
    df['AIRCRAFT_CAPACITY'] = df['AERONAVE_TIPO'].map(AIRCRAFT_CAPACITY)
    
    # Calculate total passengers
    df['TOTAL_PAX'] = df['PAX_LOCAL'] + df['PAX_CONEXAO_DOMESTICO'] + df['PAX_CONEXAO_INTERNACIONAL']
    
    # Calculate occupancy rate
    df['OCCUPANCY_RATE'] = df.apply(
        lambda row: (row['TOTAL_PAX'] / row['AIRCRAFT_CAPACITY'] * 100) 
        if pd.notnull(row['AIRCRAFT_CAPACITY']) and row['AIRCRAFT_CAPACITY'] > 0 
        else None, 
        axis=1
    )
    
    # Check for capacity violations
    df['EXCEEDS_CAPACITY'] = False
    df.loc[df['AIRCRAFT_CAPACITY'].notna(), 'EXCEEDS_CAPACITY'] = \
        df.loc[df['AIRCRAFT_CAPACITY'].notna(), 'TOTAL_PAX'] > df.loc[df['AIRCRAFT_CAPACITY'].notna(), 'AIRCRAFT_CAPACITY']
    
    # Validate GERAL flights
    df['GERAL_PAX_VIOLATION'] = (df['AERONAVE_OPERADOR'] == 'GERAL') & (df['TOTAL_PAX'] > 0)
    
    # Validate RPE em Branco (commercial flights with zero passengers)
    # Exclude flights with SERVICE_TYPE 'F' or 'M'
    df['RPE_BRANCO_VIOLATION'] = (
        (df['AERONAVE_OPERADOR'] != 'GERAL') & 
        (df['TOTAL_PAX'] == 0) & 
        (~df['SERVICE_TYPE'].isin(['F', 'M','P','A','X']))
    )
    
    # Create operation type column
    df['OPERATION_TYPE'] = df['AERONAVE_OPERADOR'].apply(
        lambda x: 'Aviação Geral' if x == 'GERAL' else 'Aviação Comercial'
    )
    
    return df


def process_flight_data(df):
    """Process flight data and create necessary groupings for visualization."""
    # Função auxiliar para converter datas
    def convert_date(date_str):
        try:
            # Primeiro tenta o formato padrão dd/mm/yyyy
            return pd.to_datetime(date_str, format='%d/%m/%Y')
        except ValueError:
            try:
                # Tenta o formato dd/mm/yy
                return pd.to_datetime(date_str, format='%d/%m/%y')
            except ValueError:
                try:
                    # Tenta com dayfirst=True para resolver ambiguidades
                    return pd.to_datetime(date_str, dayfirst=True)
                except Exception as e:
                    st.error(f"Erro ao converter a data: {date_str}. Erro: {str(e)}")
                    return None

    # Converte a coluna de data usando a função auxiliar
    df['CALCO_DATA'] = df['CALCO_DATA'].apply(convert_date)
    
    # Verifica se há alguma data inválida
    invalid_dates = df[df['CALCO_DATA'].isna()]
    if not invalid_dates.empty:
        st.warning("Atenção: Foram encontradas datas inválidas nos seguintes registros:")
        st.dataframe(invalid_dates[['CALCO_DATA', 'VOO_NUMERO', 'AERONAVE_MARCAS']])
    
    # Remove registros com datas inválidas para não afetar as análises
    df = df.dropna(subset=['CALCO_DATA'])
    
    # Group by date and operation type for operations count
    operations_by_date = df.groupby(['CALCO_DATA', 'OPERATION_TYPE']).size().reset_index(name='OPERATIONS_COUNT')
    
    # Group by date for passenger count
    passengers_by_date = df.groupby('CALCO_DATA')['TOTAL_PAX'].sum().reset_index()
    
    # Calculate average occupancy by aircraft type
    occupancy_by_aircraft = df[df['AIRCRAFT_CAPACITY'].notna()].groupby('AERONAVE_TIPO').agg({
        'OCCUPANCY_RATE': 'mean',
        'TOTAL_PAX': 'sum',
        'AIRCRAFT_CAPACITY': 'first'
    }).reset_index()
    
    occupancy_by_aircraft = occupancy_by_aircraft.sort_values('OCCUPANCY_RATE', ascending=True)
    
    return operations_by_date, passengers_by_date, occupancy_by_aircraft

def create_operations_chart(operations_by_date):
    """Create the operations chart with separated operation types."""
    fig = px.bar(
        operations_by_date,
        x='CALCO_DATA',
        y='OPERATIONS_COUNT',
        color='OPERATION_TYPE',
        title='Operações Diárias por Tipo',
        template="plotly_white",
        barmode='stack',
        color_discrete_map={
            'Aviação Comercial': '#2E86C1',
            'Aviação Geral': '#E67E22'
        }
    )
    
    fig.update_layout(
        plot_bgcolor='rgba(0,0,0,0)',
        paper_bgcolor='rgba(0,0,0,0)',
        font=dict(color='#2C3E50'),
        title_font_color='#2C3E50',
        legend_title_text='Tipo de Operação',
        xaxis_title="Data",
        yaxis_title="Número de Operações"
    )
    
    return fig



def create_passengers_chart(passengers_by_date):
    """Create the passengers chart."""
    fig = px.bar(
        passengers_by_date,
        x='CALCO_DATA',
        y='TOTAL_PAX',
        title='Total Diário de Passageiros',
        template="plotly_white"
    )
    fig.update_traces(marker_color='#27AE60')
    fig.update_layout(
        plot_bgcolor='rgba(0,0,0,0)',
        paper_bgcolor='rgba(0,0,0,0)',
        font=dict(color='#2C3E50'),
        title_font_color='#2C3E50',
        xaxis_title="Data",
        yaxis_title="Total de Passageiros"
    )
    
    return fig

def create_occupancy_chart(occupancy_by_aircraft):
    """Create the occupancy rate chart."""
    fig = px.bar(
        occupancy_by_aircraft,
        x='AERONAVE_TIPO',
        y='OCCUPANCY_RATE',
        title='Taxa Média de Ocupação por Tipo de Aeronave',
        template="plotly_white",
        text=occupancy_by_aircraft['OCCUPANCY_RATE'].round(1).astype(str) + '%'
    )
    fig.update_traces(
        marker_color='#8E44AD',
        textposition='outside'
    )
    fig.update_layout(
        plot_bgcolor='rgba(0,0,0,0)',
        paper_bgcolor='rgba(0,0,0,0)',
        font=dict(color='#2C3E50'),
        title_font_color='#2C3E50',
        xaxis_title="Tipo de Aeronave",
        yaxis_title="Taxa Média de Ocupação (%)",
        yaxis_range=[0, max(100, occupancy_by_aircraft['OCCUPANCY_RATE'].max() + 5)]
    )
    
    return fig

def create_geral_validation_chart(df):
    """Create the GERAL validation chart and get invalid flights."""
    geral_flights = df[df['AERONAVE_OPERADOR'] == 'GERAL'].copy()
    geral_flights['VALIDATION_STATUS'] = geral_flights['TOTAL_PAX'].apply(
        lambda x: 'Inválido (PAX > 0)' if x > 0 else 'Válido (PAX = 0)'
    )
    
    validation_counts = geral_flights['VALIDATION_STATUS'].value_counts().reset_index()
    validation_counts.columns = ['Status', 'Count']
    
    colors = {'Válido (PAX = 0)': '#27AE60', 'Inválido (PAX > 0)': '#E74C3C'}
    
    fig = px.pie(
        validation_counts,
        values='Count',
        names='Status',
        title='Validação de Passageiros em Voos da Aviação Geral',
        color='Status',
        color_discrete_map=colors
    )
    
    fig.update_layout(
        plot_bgcolor='rgba(0,0,0,0)',
        paper_bgcolor='rgba(0,0,0,0)',
        font=dict(color='#2C3E50'),
        title_font_color='#2C3E50'
    )
    
    return fig, geral_flights[geral_flights['TOTAL_PAX'] > 0]


def main():
    st.title('Análise de Operações e Passageiros')
    
    # File upload
    uploaded_file = st.file_uploader("Escolha um arquivo CSV", type="csv")
    
    if uploaded_file is not None:
        # Read CSV with specific encoding and separator
        df = pd.read_csv(uploaded_file, sep=';', encoding='utf-8')
        
        # Validate passenger counts
        df = validate_passenger_count(df)
        
        # Process the data
        operations_by_date, passengers_by_date, occupancy_by_aircraft = process_flight_data(df)
        
        # Create GERAL validation chart
        geral_validation_fig, invalid_geral_flights = create_geral_validation_chart(df)
        
        # Create tabs for different visualizations
        tab1, tab2, tab3, tab4 = st.tabs([
            "Operações & Passageiros", 
            "Análise de Ocupação", 
            "Validação Aviação Geral",
            "Detalhes das Violações"
        ])
        
        with tab1:
            # Add summary metrics for operations
            col1, col2 = st.columns(2)
            with col1:
                total_commercial = len(df[df['OPERATION_TYPE'] == 'Aviação Comercial'])
                st.metric(
                    "Total Operações Comerciais",
                    total_commercial,
                    delta=None
                )
            with col2:
                total_general = len(df[df['OPERATION_TYPE'] == 'Aviação Geral'])
                st.metric(
                    "Total Operações Aviação Geral",
                    total_general,
                    delta=None
                )
            
            # Display operations and passengers charts
            st.plotly_chart(create_operations_chart(operations_by_date), use_container_width=True)
            st.plotly_chart(create_passengers_chart(passengers_by_date), use_container_width=True)
        
        with tab2:
            # Display occupancy chart
            st.plotly_chart(create_occupancy_chart(occupancy_by_aircraft), use_container_width=True)
            
            # Add occupancy metrics
            avg_occupancy = df[df['OCCUPANCY_RATE'].notna()]['OCCUPANCY_RATE'].mean()
            st.metric(
                "Taxa Média de Ocupação",
                f"{avg_occupancy:.1f}%",
                delta=None,
            )
        
        with tab3:
            # Display GERAL validation chart and details
            st.plotly_chart(geral_validation_fig, use_container_width=True)
            
            if not invalid_geral_flights.empty:
                st.subheader('Voos da Aviação Geral Inválidos (PAX > 0)')
                invalid_geral_flights['CALCO_DATA'] = invalid_geral_flights['CALCO_DATA'].dt.strftime('%d/%m/%Y')
                st.dataframe(
                    invalid_geral_flights[[
                        'CALCO_DATA', 'VOO_NUMERO', 'AERONAVE_TIPO', 
                        'TOTAL_PAX', 'PAX_LOCAL', 'PAX_CONEXAO_DOMESTICO', 'PAX_CONEXAO_INTERNACIONAL'
                    ]].sort_values('TOTAL_PAX', ascending=False),
                    hide_index=True
                )

        with tab4:
            st.subheader('Detalhes das Violações')
            
            # Capacity violations details
            st.write("### Violações de Capacidade da Aeronave")
            capacity_violations = df[df['EXCEEDS_CAPACITY']].copy()
            if not capacity_violations.empty:
                capacity_violations['CALCO_DATA'] = capacity_violations['CALCO_DATA'].dt.strftime('%d/%m/%Y')
                capacity_violations['EXCESSO_PAX'] = capacity_violations['TOTAL_PAX'] - capacity_violations['AIRCRAFT_CAPACITY']
                st.dataframe(
                    capacity_violations[[
                        'CALCO_DATA', 'VOO_NUMERO', 
                        'AERONAVE_OPERADOR', 'AERONAVE_MARCAS', 'AERONAVE_TIPO', 
                        'AIRCRAFT_CAPACITY', 'TOTAL_PAX', 'EXCESSO_PAX',
                        'PAX_LOCAL', 'PAX_CONEXAO_DOMESTICO', 'PAX_CONEXAO_INTERNACIONAL'
                    ]].sort_values(['EXCESSO_PAX', 'CALCO_DATA'], ascending=[False, True]),
                    hide_index=True
                )
            else:
                st.info("Não foram encontradas violações de capacidade.")

            # Aviation violations details
            st.write("### Detalhes das Violações de Aviação Geral")
            geral_violations = df[df['GERAL_PAX_VIOLATION']].copy()
            if not geral_violations.empty:
                # Detailed view of all violations
                st.write("#### Todos os Voos com Violações")
                geral_violations['CALCO_DATA'] = geral_violations['CALCO_DATA'].dt.strftime('%d/%m/%Y')
                st.dataframe(
                    geral_violations[[
                        'CALCO_DATA', 'VOO_NUMERO',
                        'AERONAVE_OPERADOR', 'AERONAVE_MARCAS', 'AERONAVE_TIPO',
                        'TOTAL_PAX', 'PAX_LOCAL', 'PAX_CONEXAO_DOMESTICO', 
                        'PAX_CONEXAO_INTERNACIONAL'
                    ]].sort_values(['TOTAL_PAX', 'CALCO_DATA'], ascending=[False, True]),
                    hide_index=True
                )
                
                # Summary by date
                st.write("#### Resumo Diário das Violações")
                daily_violations = geral_violations.groupby('CALCO_DATA').agg({
                    'VOO_NUMERO': 'count',
                    'TOTAL_PAX': 'sum',
                    'AERONAVE_MARCAS': lambda x: ', '.join(sorted(set(x)))
                }).reset_index()
                daily_violations.columns = ['Data', 'Número de Voos', 'Total de Passageiros', 'Marcas das Aeronaves']
                st.dataframe(
                    daily_violations.sort_values(['Total de Passageiros', 'Data'], ascending=[False, True]),
                    hide_index=True
                )
            else:
                st.info("Não foram encontradas violações de aviação geral.")

            # RPE em Branco violations
            st.write("### Detalhes de RPE em Branco")
            rpe_branco_violations = df[df['RPE_BRANCO_VIOLATION']].copy()
            if not rpe_branco_violations.empty:
                # Detailed view of all violations
                st.write("#### Voos Comerciais sem Passageiros (Excluindo Carga, Pouso Técnico)")
                rpe_branco_violations['CALCO_DATA'] = rpe_branco_violations['CALCO_DATA'].dt.strftime('%d/%m/%Y')
                st.dataframe(
                    rpe_branco_violations[[
                        'CALCO_DATA', 'VOO_NUMERO',
                        'AERONAVE_OPERADOR', 'AERONAVE_MARCAS', 'AERONAVE_TIPO',
                        'SERVICE_TYPE', 'TOTAL_PAX', 'PAX_LOCAL', 
                        'PAX_CONEXAO_DOMESTICO', 'PAX_CONEXAO_INTERNACIONAL'
                    ]].sort_values('CALCO_DATA', ascending=True),
                    hide_index=True
                )
                
                # Summary by operator
                st.write("#### Resumo por Operador")
                operator_summary = rpe_branco_violations.groupby(['AERONAVE_OPERADOR', 'SERVICE_TYPE']).agg({
                    'VOO_NUMERO': 'count',
                    'AERONAVE_MARCAS': lambda x: ', '.join(sorted(set(x)))
                }).reset_index()
                operator_summary.columns = ['Operador', 'Tipo de Serviço', 'Número de Voos', 'Marcas das Aeronaves']
                st.dataframe(
                    operator_summary.sort_values(['Operador', 'Número de Voos'], ascending=[True, False]),
                    hide_index=True
                )

                # Add percentage metric
                total_commercial = len(df[df['AERONAVE_OPERADOR'] != 'GERAL'])
                violation_percentage = (len(rpe_branco_violations) / total_commercial * 100) if total_commercial > 0 else 0
                st.metric(
                    "Percentual de Voos Comerciais com RPE em Branco",
                    f"{violation_percentage:.2f}%",
                    delta=None,
                    delta_color="inverse"
                )
            else:
                st.info("Não foram encontradas violações de RPE em Branco (excluindo voos Ferry e Manutenção).")

        # Update the metrics to include RPE em Branco
        st.subheader('Estatísticas Gerais')
        col1, col2, col3, col4, col5 = st.columns(5)
        
        with col1:
            st.metric(
                "Total de Operações", 
                len(df),
                delta=None,
            )
            
        with col2:
            st.metric(
                "Total de Passageiros", 
                int(df['TOTAL_PAX'].sum()),
                delta=None,
            )
            
        with col3:
            capacity_violations = df['EXCEEDS_CAPACITY'].sum()
            st.metric(
                "Violações de Capacidade",
                int(capacity_violations),
                delta=None,
                delta_color="inverse"
            )
            
        with col4:
            geral_violations = df['GERAL_PAX_VIOLATION'].sum()
            st.metric(
                "Violações PAX Aviação Geral",
                int(geral_violations),
                delta=None,
                delta_color="inverse"
            )

        with col5:
            rpe_branco_violations = df['RPE_BRANCO_VIOLATION'].sum()
            st.metric(
                "RPE em Branco",
                int(rpe_branco_violations),
                delta=None,
                delta_color="inverse"
            )

if __name__ == "__main__":
    # Set page config
    st.set_page_config(
        page_title="Análise de Voos",
        page_icon="✈️",
        layout="wide"
    )
    
    # Custom CSS to set background color and improve visibility
    st.markdown("""
        <style>
        .stApp {
            background-color: #F5F7FA;
        }
        .st-emotion-cache-10trblm {
            color: #2C3E50;
        }
        .st-emotion-cache-1629p8f {
            color: #2C3E50;
        }
        .st-emotion-cache-1inwz65 {
            color: #2C3E50;
        }
        div[data-testid="stMetricValue"] {
            color: #2C3E50;
        }
        </style>
    """, unsafe_allow_html=True)
    
    main()