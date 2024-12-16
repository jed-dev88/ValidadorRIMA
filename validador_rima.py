import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime
import io
import xlsxwriter 

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

def process_flight_data(df):
    """Process flight data and create necessary groupings for visualization."""
    # Converte as datas para datetime usando o formato correto
    date_cols = ['PREVISTO_DATA', 'CALCO_DATA', 'TOQUE_DATA']
    
    for col in date_cols:
        # Primeiro tenta converter do formato original dd/mm/yyyy
        df[col] = pd.to_datetime(df[col], format='%d/%m/%Y', errors='coerce')
    
    # Remove registros com datas inválidas
    df = df.dropna(subset=['CALCO_DATA'])
    
    # Converte colunas de horário para o formato correto
    time_cols = ['PREVISTO_HORARIO', 'CALCO_HORARIO', 'TOQUE_HORARIO']
    for col in time_cols:
        df[col] = pd.to_datetime(df[col].astype(str).str.zfill(4), format='%H%M', errors='coerce').dt.time
    
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

def format_date_safely(date):
    """Formata a data de forma segura, tratando valores nulos."""
    try:
        if pd.isna(date):
            return ''
        return date.strftime('%d/%m/%Y')
    except:
        return ''






def create_violations_summary(df, airport_code):
   """Create a summary DataFrame of all violations."""
   timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
   summary_rows = []
   
   # Capacity violations
   capacity_violations = df[df['EXCEEDS_CAPACITY']]
   if not capacity_violations.empty:
       for _, row in capacity_violations.iterrows():
           summary_rows.append({
               'Data': format_date_safely(row['CALCO_DATA']),
               'Tipo_Violacao': 'Capacidade',
               'Voo': row['VOO_NUMERO'],
               'Marcas': row['AERONAVE_MARCAS'],
               'Operador': row['AERONAVE_OPERADOR'],
               'Detalhes': f"Excesso de {int(row['TOTAL_PAX'] - row['AIRCRAFT_CAPACITY'])} passageiros"
           })
   
   # GERAL violations
   geral_violations = df[df['GERAL_PAX_VIOLATION']]
   if not geral_violations.empty:
       for _, row in geral_violations.iterrows():
           summary_rows.append({
               'Data': format_date_safely(row['CALCO_DATA']),
               'Tipo_Violacao': 'Aviação Geral',
               'Voo': row['VOO_NUMERO'],
               'Marcas': row['AERONAVE_MARCAS'],
               'Operador': row['AERONAVE_OPERADOR'],
               'Detalhes': f"Total PAX: {int(row['TOTAL_PAX'])}"
           })
   
   # RPE em Branco violations
   rpe_violations = df[df['RPE_BRANCO_VIOLATION']]
   if not rpe_violations.empty:
       for _, row in rpe_violations.iterrows():
           summary_rows.append({
               'Data': format_date_safely(row['CALCO_DATA']),
               'Tipo_Violacao': 'RPE em Branco',
               'Voo': row['VOO_NUMERO'],
               'Marcas': row['AERONAVE_MARCAS'],
               'Operador': row['AERONAVE_OPERADOR'],
               'Detalhes': 'Voo comercial sem passageiros'
           })
   
   # Empty registration violations
   empty_reg = df[df['EMPTY_REGISTRATION_VIOLATION']]
   if not empty_reg.empty:
       for _, row in empty_reg.iterrows():
           summary_rows.append({
               'Data': format_date_safely(row['CALCO_DATA']),
               'Tipo_Violacao': 'Marcas Vazias',
               'Voo': row['VOO_NUMERO'],
               'Marcas': 'VAZIA',
               'Operador': row['AERONAVE_OPERADOR'],
               'Detalhes': 'Aeronave sem marcas'
           })
   
   # Time sequence violations
   time_violations = df[df['TIME_SEQUENCE_VIOLATION']]
   if not time_violations.empty:
       for _, row in time_violations.iterrows():
           summary_rows.append({
               'Data': format_date_safely(row['CALCO_DATA']),
               'Tipo_Violacao': 'Sequência de Horários',
               'Voo': row['VOO_NUMERO'],
               'Marcas': row['AERONAVE_MARCAS'],
               'Operador': row['AERONAVE_OPERADOR'],
               'Detalhes': f"Movimento {row['MOVIMENTO_TIPO']} - Calco: {row['CALCO_HORARIO']}, Toque: {row['TOQUE_HORARIO']}"
           })
   
   summary_df = pd.DataFrame(summary_rows)
   
   if not summary_df.empty:
       stats_df = pd.DataFrame([
           {'Estatística': 'Total de Violações', 'Valor': len(summary_df)},
           {'Estatística': 'Violações de Capacidade', 'Valor': len(df[df['EXCEEDS_CAPACITY']])},
           {'Estatística': 'Violações Aviação Geral', 'Valor': len(df[df['GERAL_PAX_VIOLATION']])},
           {'Estatística': 'RPE em Branco', 'Valor': len(df[df['RPE_BRANCO_VIOLATION']])},
           {'Estatística': 'Marcas Vazias', 'Valor': len(df[df['EMPTY_REGISTRATION_VIOLATION']])},
           {'Estatística': 'Violações de Horário', 'Valor': len(df[df['TIME_SEQUENCE_VIOLATION']])}
       ])
       
       output = io.BytesIO()
       with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
           summary_df.to_excel(writer, sheet_name='Violações', index=False)
           stats_df.to_excel(writer, sheet_name='Estatísticas', index=False)
       
       return output.getvalue()
   
   return None

def validate_passenger_count(df):
    """Validate passenger counts and all other validations."""
    # Previous validations remain the same
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
    df['RPE_BRANCO_VIOLATION'] = (
        (df['AERONAVE_OPERADOR'] != 'GERAL') & 
        (df['TOTAL_PAX'] == 0) & 
        (~df['SERVICE_TYPE'].isin(['F','M','H','P','A','X','Y','Z']))
    )
    
    # Validate empty aircraft registration
    df['EMPTY_REGISTRATION_VIOLATION'] = df['AERONAVE_MARCAS'].isna() | (df['AERONAVE_MARCAS'] == '')
    
    # Create operation type column
    df['OPERATION_TYPE'] = df['AERONAVE_OPERADOR'].apply(
        lambda x: 'Aviação Geral' if x == 'GERAL' else 'Aviação Comercial')
    
      # Time validations
    # Convert date and time columns to complete datetime objects
    df['CALCO_DATETIME'] = pd.to_datetime(
        df['CALCO_DATA'].astype(str) + ' ' + df['CALCO_HORARIO'], 
        format='%Y-%m-%d %H:%M', 
        errors='coerce'
    )
    
    df['TOQUE_DATETIME'] = pd.to_datetime(
        df['CALCO_DATA'].astype(str) + ' ' + df['TOQUE_HORARIO'], 
        format='%Y-%m-%d %H:%M', 
        errors='coerce'
    )
    
    df['PREVISTO_DATETIME'] = pd.to_datetime(
        df['CALCO_DATA'].astype(str) + ' ' + df['PREVISTO_HORARIO'], 
        format='%Y-%m-%d %H:%M', 
        errors='coerce'
    )

    # Time sequence validation for arrivals (P) and departures (D)
    df['TIME_SEQUENCE_VIOLATION'] = False
    
    # For arrivals (P)
    arrival_mask = (df['MOVIMENTO_TIPO'] == 'P') & df['CALCO_DATETIME'].notna() & df['TOQUE_DATETIME'].notna()
    df.loc[arrival_mask, 'TIME_SEQUENCE_VIOLATION'] = df[arrival_mask].apply(
        lambda row: row['CALCO_DATETIME'] <= row['TOQUE_DATETIME'], 
        axis=1
    )

    # For departures (D)
    departure_mask = (df['MOVIMENTO_TIPO'] == 'D') & df['CALCO_DATETIME'].notna() & df['TOQUE_DATETIME'].notna()
    df.loc[departure_mask, 'TIME_SEQUENCE_VIOLATION'] = df[departure_mask].apply(
        lambda row: row['CALCO_DATETIME'] >= row['TOQUE_DATETIME'],
        axis=1
    )

    return df


def create_operations_chart(operations_by_date):
    """Create the operations chart with separated operation types and improved contrast."""
    fig = px.bar(
        operations_by_date,
        x='CALCO_DATA',
        y='OPERATIONS_COUNT',
        color='OPERATION_TYPE',
        title='Operações Diárias por Tipo de Aviação',
        template="plotly_white",
        barmode='stack',
        color_discrete_map={
            'Aviação Comercial': '#1a5f7a',  # Azul mais escuro
            'Aviação Geral': '#c65102'       # Laranja mais escuro
        }
    )
    
    # Adiciona rótulos nas barras
    fig.update_traces(
        texttemplate='%{y:,.0f}',  # Formato: número inteiro com separador de milhares
        textposition='outside',
        textfont=dict(size=10)
    )
    
    fig.update_layout(
        plot_bgcolor='rgba(0,0,0,0)',
        paper_bgcolor='rgba(0,0,0,0)',
        font=dict(
            color='#1a1a1a',
            size=12
        ),
        title_font=dict(
            color='#1a1a1a',
            size=16
        ),
        legend_title_text='Tipo de Operação',
        xaxis_title="Data da Operação",
        yaxis_title="Quantidade de Operações",
        showlegend=True,
        legend=dict(
            bgcolor='rgba(255,255,255,0.8)',
            bordercolor='#1a1a1a',
            borderwidth=1
        ),
        annotations=[
            dict(
                text="Este gráfico mostra a distribuição diária de operações, separando aviação comercial e geral.",
                showarrow=False,
                xref='paper',
                yref='paper',
                x=0,
                y=-0.2,
                align='left',
                font=dict(size=10, color='#666666')
            )
        ]
    )
    
    return fig

def create_passengers_chart(passengers_by_date):
    """Create the passengers chart with improved contrast and annotations."""
    fig = px.bar(
        passengers_by_date,
        x='CALCO_DATA',
        y='TOTAL_PAX',
        title='Total Diário de Passageiros Processados',
        template="plotly_white"
    )
    
    # Adiciona rótulos nas barras
    fig.update_traces(
        marker_color='#1e8449',  # Verde mais escuro
        texttemplate='%{y:,.0f}',  # Formato: número inteiro com separador de milhares
        textposition='outside',
        textfont=dict(size=10),
        hovertemplate="Data: %{x}<br>Total de Passageiros: %{y:,.0f}<extra></extra>"
    )
    
    fig.update_layout(
        plot_bgcolor='rgba(0,0,0,0)',
        paper_bgcolor='rgba(0,0,0,0)',
        font=dict(
            color='#1a1a1a',
            size=12
        ),
        title_font=dict(
            color='#1a1a1a',
            size=16
        ),
        xaxis_title="Data do Processamento",
        yaxis_title="Quantidade Total de Passageiros",
        annotations=[
            dict(
                text="Este gráfico apresenta o fluxo diário total de passageiros, incluindo embarques e desembarques.",
                showarrow=False,
                xref='paper',
                yref='paper',
                x=0,
                y=-0.2,
                align='left',
                font=dict(size=10, color='#666666')
            )
        ]
    )
    
    return fig

def create_occupancy_chart(occupancy_by_aircraft):
    """Create the occupancy rate chart with improved contrast and annotations."""
    fig = px.bar(
        occupancy_by_aircraft,
        x='AERONAVE_TIPO',
        y='OCCUPANCY_RATE',
        title='Taxa Média de Ocupação por Tipo de Aeronave',
        template="plotly_white",
        text=occupancy_by_aircraft.apply(
            lambda row: f"{row['OCCUPANCY_RATE']:.1f}%\n({int(row['TOTAL_PAX']):,} PAX)",
            axis=1
        )
    )
    
    fig.update_traces(
        marker_color='#6c3483',  # Roxo mais escuro
        textposition='outside',
        textfont=dict(size=10),
        hovertemplate=(
            "Tipo de Aeronave: %{x}<br>" +
            "Taxa de Ocupação: %{y:.1f}%<br>" +
            "Capacidade: %{customdata[0]}<br>" +
            "Total de PAX: %{customdata[1]:,}<extra></extra>"
        ),
        customdata=occupancy_by_aircraft[['AIRCRAFT_CAPACITY', 'TOTAL_PAX']]
    )
    
    fig.update_layout(
        plot_bgcolor='rgba(0,0,0,0)',
        paper_bgcolor='rgba(0,0,0,0)',
        font=dict(
            color='#1a1a1a',
            size=12
        ),
        title_font=dict(
            color='#1a1a1a',
            size=16
        ),
        xaxis_title="Modelo da Aeronave",
        yaxis_title="Taxa Média de Ocupação (%)",
        yaxis_range=[0, max(100, occupancy_by_aircraft['OCCUPANCY_RATE'].max() + 15)],  # Aumentado para acomodar os rótulos
        annotations=[
            dict(
                text="Este gráfico mostra a taxa média de ocupação para cada tipo de aeronave em operação.",
                showarrow=False,
                xref='paper',
                yref='paper',
                x=0,
                y=-0.2,
                align='left',
                font=dict(size=10, color='#666666')
            )
        ]
    )
    
    return fig

def create_cargo_mail_chart(df):
    """Create a chart showing daily cargo and mail volumes."""
    # Agrupa os dados por data, somando carga e correio
    daily_cargo = df.groupby('CALCO_DATA').agg({
        'CARGA': 'sum',
        'CORREIO': 'sum'
    }).reset_index()
    
    # Cria o gráfico de barras agrupadas
    fig = go.Figure()
    
    # Adiciona barra para Carga
    fig.add_trace(go.Bar(
        name='Carga',
        x=daily_cargo['CALCO_DATA'],
        y=daily_cargo['CARGA'],
        text=daily_cargo['CARGA'].apply(lambda x: f'{x:,.0f}kg'),
        textposition='outside',
        marker_color='#2c3e50',  # Azul escuro
        hovertemplate="Data: %{x}<br>Carga: %{y:,.0f}kg<extra></extra>"
    ))
    
    # Adiciona barra para Correio
    fig.add_trace(go.Bar(
        name='Correio',
        x=daily_cargo['CALCO_DATA'],
        y=daily_cargo['CORREIO'],
        text=daily_cargo['CORREIO'].apply(lambda x: f'{x:,.0f}kg'),
        textposition='outside',
        marker_color='#e67e22',  # Laranja
        hovertemplate="Data: %{x}<br>Correio: %{y:,.0f}kg<extra></extra>"
    ))
    
    # Atualiza o layout
    fig.update_layout(
        title='Movimentação Diária de Carga e Correio',
        barmode='group',
        plot_bgcolor='rgba(0,0,0,0)',
        paper_bgcolor='rgba(0,0,0,0)',
        font=dict(
            color='#1a1a1a',
            size=12
        ),
        title_font=dict(
            color='#1a1a1a',
            size=16
        ),
        xaxis_title="Data",
        yaxis_title="Peso (kg)",
        showlegend=True,
        legend=dict(
            bgcolor='rgba(255,255,255,0.8)',
            bordercolor='#1a1a1a',
            borderwidth=1
        ),
        annotations=[
            dict(
                text="Este gráfico apresenta o volume diário de carga e correio movimentados no aeroporto.",
                showarrow=False,
                xref='paper',
                yref='paper',
                x=0,
                y=-0.2,
                align='left',
                font=dict(size=10, color='#666666')
            )
        ]
    )
    
    return fig


def create_geral_validation_chart(df):
    """Create the GERAL validation chart with improved contrast and annotations."""
    geral_flights = df[df['AERONAVE_OPERADOR'] == 'GERAL'].copy()
    geral_flights['VALIDATION_STATUS'] = geral_flights['TOTAL_PAX'].apply(
        lambda x: 'Inválido (PAX > 0)' if x > 0 else 'Válido (PAX = 0)'
    )
    
    validation_counts = geral_flights['VALIDATION_STATUS'].value_counts().reset_index()
    validation_counts.columns = ['Status', 'Count']
    
    colors = {
        'Válido (PAX = 0)': '#1e8449',    # Verde mais escuro
        'Inválido (PAX > 0)': '#c0392b'    # Vermelho mais escuro
    }
    
    fig = px.pie(
        validation_counts,
        values='Count',
        names='Status',
        title='Validação de Passageiros em Voos da Aviação Geral',
        color='Status',
        color_discrete_map=colors
    )
    
    # Adiciona rótulos com percentuais e contagens
    fig.update_traces(
        textposition='inside',
        textinfo='percent+value',
        textfont_size=12,
        hovertemplate="Status: %{label}<br>Quantidade: %{value}<br>Percentual: %{percent}<extra></extra>"
    )
    
    fig.update_layout(
        plot_bgcolor='rgba(0,0,0,0)',
        paper_bgcolor='rgba(0,0,0,0)',
        font=dict(
            color='#1a1a1a',
            size=12
        ),
        title_font=dict(
            color='#1a1a1a',
            size=16
        ),
        showlegend=True,
        legend=dict(
            bgcolor='rgba(255,255,255,0.8)',
            bordercolor='#1a1a1a',
            borderwidth=1
        ),
        annotations=[
            dict(
                text="Este gráfico apresenta a proporção de voos da aviação geral com registro correto (sem passageiros) e incorreto (com passageiros).",
                showarrow=False,
                xref='paper',
                yref='paper',
                x=0,
                y=-0.2,
                align='left',
                font=dict(size=10, color='#666666')
            )
        ]
    )
    
    return fig, geral_flights[geral_flights['TOTAL_PAX'] > 0]


def main():
    st.title('Análise de Operações e Passageiros')
    
    # File upload
    uploaded_file = st.file_uploader("Escolha um arquivo CSV", type="csv")
    
    if uploaded_file is not None:
        # Read CSV with specific encoding and separator
        df = pd.read_csv(uploaded_file, sep=';', encoding='utf-8')

        # Get airport code from filename (first 4 letters)
        airport_code = uploaded_file.name[:4].upper()
        
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

        # Add download button at the top of the page
        summary_data = create_violations_summary(df, airport_code)
        if summary_data is not None:
            st.download_button(
                label="📥 Baixar Resumo de Violações",
                data=summary_data,
                file_name=f"violacoes_{airport_code}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
            )
        
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

            col3, col4 = st.columns(2)
            with col3:
                total_cargo = df['CARGA'].fillna(0).sum()
                st.metric(
                    "Total de Carga",
                    f"{int(total_cargo):,} kg",
                    delta=None
                )
            with col4:
                # Corrigido para tratar valores nulos
                total_mail = df['CORREIO'].fillna(0).sum()
                st.metric(
                    "Total de Correio",
                    f"{int(total_mail):,} kg",
                    delta=None
                )
            
            # Display operations and passengers charts
            st.plotly_chart(create_operations_chart(operations_by_date), use_container_width=True)
            st.plotly_chart(create_passengers_chart(passengers_by_date), use_container_width=True)
            st.plotly_chart(create_cargo_mail_chart(df), use_container_width=True)
        
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

            st.write("### Violações de Horários")
        

            # Time sequence violations
            st.write("#### Sequência de Horários Incorreta")
            time_sequence_violations = df[df['TIME_SEQUENCE_VIOLATION']].copy()
            if not time_sequence_violations.empty:
                time_sequence_violations['CALCO_DATA'] = time_sequence_violations['CALCO_DATA'].dt.strftime('%d/%m/%Y')
                st.dataframe(
                    time_sequence_violations[[
                        'CALCO_DATA', 'VOO_NUMERO', 'MOVIMENTO_TIPO',
                        'CALCO_HORARIO', 'TOQUE_HORARIO'
                    ]].sort_values('CALCO_DATA'),
                    hide_index=True
                )


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

            st.write("### Detalhes de Marcas de Aeronave Vazias")
            empty_registration = df[df['EMPTY_REGISTRATION_VIOLATION']].copy()
            if not empty_registration.empty:
                empty_registration['CALCO_DATA'] = empty_registration['CALCO_DATA'].dt.strftime('%d/%m/%Y')
                st.dataframe(
                    empty_registration[[
                        'CALCO_DATA', 'VOO_NUMERO',
                        'AERONAVE_OPERADOR', 'AERONAVE_TIPO',
                        'SERVICE_TYPE', 'TOTAL_PAX'
                    ]].sort_values('CALCO_DATA', ascending=True),
                hide_index=True
                )
            else:
                 st.info("Não foram encontradas violações de marcas de aeronave vazias.")        


        # Update the metrics to include RPE em Branco
        st.subheader('Estatísticas Gerais')
        col1, col2, col3, col4, col5, col6, col7  = st.columns(7)
        
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
        with col6:  # Add new column
            empty_reg_violations = df['EMPTY_REGISTRATION_VIOLATION'].sum()
            st.metric(
                "Marcas Vazias",
                int(empty_reg_violations),
                delta=None,
                delta_color="inverse"
            )

        with col7:
            time_sequence_violations = df['TIME_SEQUENCE_VIOLATION'].sum()
            st.metric(
                "Sequência de Horários Incorreta",
                int(time_sequence_violations),
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
    
if __name__ == '__main__':
    main()
