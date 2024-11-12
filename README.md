# ValidadorRIMA

Validador de Consistência de Voos
📋 Descrição
O Validador de Consistência de Voos é uma aplicação web desenvolvida em Python para análise e validação de dados operacionais de voos. A ferramenta permite identificar inconsistências nos dados, analisar métricas operacionais e visualizar informações importantes sobre as operações aéreas.

🚀 Funcionalidades Principais
1. Validações de Dados

Verificação de Capacidade: Identifica voos onde o número de passageiros excede a capacidade da aeronave
Validação de Aviação Geral: Detecta voos de aviação geral com registros irregulares de passageiros
RPE em Branco: Identifica voos comerciais sem passageiros (excluindo voos Ferry e Manutenção)
Validação de Datas: Tratamento robusto de diferentes formatos de data

2. Análises Operacionais

Métricas de Ocupação: Visualização da taxa de ocupação por tipo de aeronave
Análise Temporal: Gráficos de operações diárias e total de passageiros por dia
Segmentação por Tipo: Separação entre aviação comercial e aviação geral

3. Visualizações

Gráficos Interativos: Utilização de gráficos Plotly para visualização dinâmica dos dados
Dashboards: Painéis organizados com métricas principais
Detalhamento de Violações: Visão detalhada de todas as inconsistências encontradas

💻 Tecnologias Utilizadas

Python 3.x
Streamlit: Framework para criação da interface web
Pandas: Manipulação e análise de dados
Plotly: Criação de gráficos interativos

📌 Pré-requisitos
bashCopy# Instalação das dependências
pip install streamlit pandas plotly
🔧 Como Usar

Clone o repositório

bashCopygit clone https://github.com/seu-usuario/validador-consistencia-voos.git

Instale as dependências

bashCopypip install -r requirements.txt

Execute a aplicação

bashCopystreamlit run validador_consistencia_voos.py
📊 Formato dos Dados de Entrada
A aplicação espera um arquivo CSV no padrão da ANAC:


🎯 Validações Implementadas
Capacidade da Aeronave

Verifica se o total de passageiros está dentro da capacidade máxima de cada tipo de aeronave
Considera diferentes configurações para cada modelo de aeronave

Aviação Geral

Identifica voos de aviação geral com registros de passageiros (que deveriam ser zero)
Fornece detalhamento por data e operador

RPE em Branco

Detecta voos comerciais sem passageiros
Exclui automaticamente voos Ferry (F) e Manutenção (M)
Apresenta análise por operador e tipo de serviço

📈 Visualizações Disponíveis

Gráficos de operações diárias
Distribuição de passageiros por data
Taxa de ocupação por tipo de aeronave
Resumos detalhados de violações
Métricas gerais de operação

🤝 Contribuições
Contribuições são bem-vindas! Sinta-se à vontade para:

Reportar bugs
Sugerir novas funcionalidades
Melhorar a documentação
Submeter pull requests


