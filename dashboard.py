import pandas as pd
import streamlit as st
import plotly.express as px
import locale
import plotly.graph_objects as go

locale.setlocale(locale.LC_TIME, 'pt_BR.UTF-8')

class RelatorioChamados:
    def __init__(self):
        self.all_option = "Selecionar Tudo"
        st.set_page_config(layout='wide')
        st.sidebar.image('logo.png', width=200)
        self.load_and_transform_data()
        self.create_filters()
    
    def load_and_transform_data(self)->None:
        # Carregue os dados, conforme necessário
        field_map = {
            'TICKET':'ticket',
            'TIPO DO TICKET':'tipo',
            'DATA DE CRIAÇÃO DO TICKET':'data_criacao',
            'DATA DA SOLUÇÃO':'data_solucao',
            'TEMPO TOTAL DE ATENDIMENTO':'tempo_atendimento',
            'NOME FANTASIA DO CLIENTE':'cliente',
            'NOME DA CATEGORIA PRIMÁRIA':'categoria',
            'NOME DA CATEGORIA SECUNDÁRIA':'subcategoria',
            'NOME DO TÉCNICO':'tecnico',
            'NOTA DA AVALIAÇÃO':'nota',
            'DESCRIÇÃO DA AVALIAÇÃO':'avaliacao',
            'DESCRIÇÃO DA MESA DE TRABALHO':'mesa_trabalho',
            'STATUS SLA RESPOSTA':'sla_resposta',
            'STATUS SLA SOLUÇÃO':'sla_solucao',
            'STATUS DO TICKET':'status',
            'PRIORIDADE':'prioridade',}
        self.dataset = (
            pd.read_excel('Relatorio personalizado.xlsx')
            .loc[:, list(field_map.keys())]
            .rename(columns=field_map)
            .assign(
                ticket=lambda d_: d_['ticket'].astype(int),
                data_criacao=lambda d_: pd.to_datetime(d_['data_criacao'], format='%d/%m/%Y'),
                data_solucao=lambda d_: (
                    pd.to_datetime(d_['data_solucao'].replace('nao possui', pd.NaT),
                                   errors='coerce')),
                mes_ano=lambda d_: d_['data_criacao'].dt.strftime('%b/%Y').str.lower(),
                dia_mes=lambda d_: d_['data_criacao'].dt.strftime('%d/%b').str.lower(),
                ordem=lambda d_: pd.to_datetime(d_['mes_ano'], format='%b/%Y').dt.to_period('M').astype(int),
                count_ticket = 1,
                sla_resposta_indicador=0)
            .sort_values(by='ordem'))

    def create_filters(self)->None:
        # Crie os filtros na barra lateral com a seleção padrão "Todos"
        self.months = [self.all_option] + self.dataset['mes_ano'].unique().tolist()
        self.clients = [self.all_option] + self.dataset.sort_values(by='cliente')['cliente'].unique().tolist()
        self.desks = [self.all_option] + self.dataset.sort_values(by='mesa_trabalho')['mesa_trabalho'].unique().tolist()

    def apply_filters(self):
        # Lógica de filtragem com base nas seleções
        selected_months = st.sidebar.multiselect("Mês/Ano", self.months, default=[self.all_option])
        selected_clients = st.sidebar.multiselect("Cliente", self.clients, default=[self.all_option])
        selected_desks = st.sidebar.multiselect("Mesa de Trabalho", self.desks, default=[self.all_option])

        if self.all_option in selected_months:
            self.df_filtered = self.dataset
        else:
            self.df_filtered = self.dataset[self.dataset['mes_ano'].isin(selected_months)]

        if self.all_option in selected_clients:
            self.df_filtered = self.df_filtered
        else:
            self.df_filtered = self.df_filtered[self.df_filtered['cliente'].isin(selected_clients)]

        if self.all_option in selected_desks:
            self.df_filtered = self.df_filtered
        else:
            self.df_filtered = self.df_filtered[self.df_filtered['mesa_trabalho'].isin(selected_desks)]

    def _create_graphicts(self):
        col1, col2, col3, col4, col5, col6 = st.columns(6)
        col7, col8 = st.columns(2)
        col9, col10, col11 = st.columns(3)
        card_total_tickets = self._cards(valor=self.df_filtered['ticket'].nunique(), title="Tickets")
        card_tickets_a_fazer = self._cards(
            valor= self.df_filtered.loc[self.df_filtered['status']=='A fazer']['ticket'].nunique(),
            title="Tickets a Fazer")
        card_tickets_atendendo = self._cards(
            valor= self.df_filtered.loc[self.df_filtered['status']=='Atendendo']['ticket'].nunique(),
            title="Tickets Atendendo")
        card_tickets_pausados = self._cards(
            valor= self.df_filtered.loc[self.df_filtered['status']=='Pausado']['ticket'].nunique(),
            title="Tickets Pausados")
        card_tickets_conferencia = self._cards(
            valor= self.df_filtered.loc[self.df_filtered['status']=='Não possui']['ticket'].nunique(),
            title="Tickets Em Conferência")
        card_qtd_clientes = self._cards(
            valor= self.df_filtered['cliente'].nunique(),
            title="Qtd Clientes")
        col1.markdown(card_total_tickets, unsafe_allow_html=True)
        col2.markdown(card_tickets_a_fazer, unsafe_allow_html=True)
        col3.markdown(card_tickets_atendendo, unsafe_allow_html=True)
        col4.markdown(card_tickets_pausados, unsafe_allow_html=True)
        col5.markdown(card_tickets_conferencia, unsafe_allow_html=True)
        col6.markdown(card_qtd_clientes, unsafe_allow_html=True)
        
        grafico_cliente = self._inverted_bar_chart(
            values = (
                self.df_filtered
                .groupby('cliente')['ticket']
                .nunique()
                .reset_index(name='quantidade_t')),
            eixo_x='quantidade_t',
            eixo_y='cliente')
        
        grafico_categoria = self._inverted_bar_chart(
            values = (
                self.df_filtered
                .groupby('categoria')['ticket']
                .nunique()
                .reset_index(name='quantidade_t')),
            eixo_x='quantidade_t',
            eixo_y='categoria')
        
        grafico_subcategoria = self._inverted_bar_chart(
            values = (
                self.df_filtered
                .groupby('subcategoria')['ticket']
                .nunique()
                .reset_index(name='quantidade_t')),
            eixo_x='quantidade_t',
            eixo_y='subcategoria')
        
        grafico_tipo = self._pie_chart_tipo()
        
        col7.plotly_chart(grafico_cliente, use_container_witdth = True)
        col8.plotly_chart(grafico_tipo, use_container_witdth = True)
        col9.plotly_chart(grafico_categoria, use_container_witdth = True)
        col10.plotly_chart(grafico_subcategoria, use_container_witdth = True)
    
    def _cards(self, valor:float, title:str)->str:
        """Método que monta e retorna um card com valor e título"""
        return (
                f"""
                <div style="
                    text-align: center;
                    border: 1px solid #333333;
                    border-radius: 10px;
                    padding: 10px;
                    width: 150px;
                ">
                    <h3 style="margin: 0;">{valor}</h3>
                    <p style="margin: 0; font-size: 12px;">{title}</p>
                </div>
                """)

    def _inverted_bar_chart(self, values: pd.Series, eixo_x:str, eixo_y:str):
        # Crie o gráfico de tickets por categoria
        return (
            px.bar(
                values,
                x=eixo_x,
                y=eixo_y,
                title='Chamados por Categoria',
                labels={eixo_x: eixo_x, eixo_y: eixo_y},
                text=eixo_x)
            .update_layout(barmode='stack')
            .update_traces(
                marker=dict(color='#004169', line=dict(width=1)),
                texttemplate='%{text}',
                textposition='inside',
                textangle=0)
            .update_layout(showlegend=False)
            .update_yaxes(
                type='category',
                categoryorder='total ascending',
                title='')
            .update_xaxes(
                title=''))

    def _pie_chart_tipo(self):
        colors = {
            'Incidente': '#FF8D02',
            'Requisição de Serviço': '#00990D',
            'Problema': '#B82601',
            'Não possui': '#7E00B8',
            'Preventivo Técnico': '#FFBB00',
            'Conferência Backup': '#7CBB00',
            'Preventivo Cliente': '#0375B4',
            'Preventivo': '#0375B4'}
        df_tipo_tickets = (
            self.df_filtered
            .groupby('tipo')['count_ticket']
            .sum()
            .reset_index()
            .assign(cor = lambda d_: d_['tipo'].map(colors)))
        return (
            go.Figure()
            .add_trace(
                go.Pie(
                    labels=df_tipo_tickets['tipo'],
                    values=df_tipo_tickets['count_ticket'],
                    hole=0.6,
                    title = 'Tipo',
                    marker=dict(colors=df_tipo_tickets['cor']),))
            .update_layout(
                showlegend=True,
                title='Distribuição de Tickets por Tipo'))
    
if __name__ == "__main__":
    relatorio_chamados = RelatorioChamados()
    relatorio_chamados.apply_filters()
    relatorio_chamados._create_graphicts()
