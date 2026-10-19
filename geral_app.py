import streamlit as st
import pandas as pd
import os
import plotly.express as px
import unicodedata
from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib import colors

# Configuração do título da página
st.set_page_config(page_title="Visualizador de Dados", layout="wide")
st.title("📊 Painel Eleitoral Consolidado (PL vs PT)")

# Nome do seu arquivo Excel
ARQUIVO_DADOS = "votaçao_partido_presidente_2026.xlsx"

# Função para remover acentos do texto e facilitar a busca livre do usuário
def remover_acentos(texto):
    if not isinstance(texto, str):
        return ""
    return "".join(c for c in unicodedata.normalize('NFD', texto) if unicodedata.category(c) != 'Mn')

# Função para construir o arquivo PDF estruturado
def gerar_pdf(dataframe, nome_col_municipio, nome_col_sigla):
    pdf_filename = "relatorio_eleitoral_filtrado.pdf"
    doc = SimpleDocTemplate(pdf_filename, pagesize=letter, title="Relatório Eleitoral")
    story = []
    styles = getSampleStyleSheet()
    title_style = ParagraphStyle('TitleStyle', parent=styles['Heading1'], fontSize=18, textColor=colors.HexColor("#2C3E50"), spaceAfter=12)
    normal_style = ParagraphStyle('NormalStyle', parent=styles['Normal'], fontSize=10, leading=14, spaceAfter=8)
    
    story.append(Paragraph("<b>📋 Relatório Consolidado de Desempenho Eleitoral (PL vs PT)</b>", title_style))
    story.append(Paragraph("Este documento apresenta a análise computada a partir das cidades selecionadas no painel digital.", normal_style))
    story.append(Spacer(1, 10))
    
    table_data = [["Cidade", "UF", "Votos PL", "Votos PT", "Diferença Absoluta"]]
    for _, row in dataframe.iterrows():
        sinal = "+" if row["DIFERENCA_PL_PT"] >= 0 else ""
        table_data.append([
            str(row[nome_col_municipio]),
            str(row[nome_col_sigla]),
            f"{int(row['PL']):,}",
            f"{int(row['PT']):,}",
            f"{sinal}{int(row['DIFERENCA_PL_PT']):,}"
        ])
    
    t = Table(table_data, colWidths=[140, 50, 100, 100, 120])
    t.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,0), colors.HexColor("#2C3E50")),
        ('TEXTCOLOR', (0,0), (-1,0), colors.whitesmoke),
        ('ALIGN', (0,0), (-1,-1), 'CENTER'),
        ('FONTNAME', (0,0), (-1,0), 'Helvetica-Bold'),
        ('BOTTOMPADDING', (0,0), (-1,0), 6),
        ('BACKGROUND', (0,1), (-1,-1), colors.HexColor("#FAF9F6")),
        ('GRID', (0,0), (-1,-1), 0.5, colors.HexColor("#BDC3C7")),
    ]))
    story.append(t)
    doc.build(story)
    return pdf_filename

if os.path.exists(ARQUIVO_DADOS):
    # Carrega a planilha Excel
    df = pd.read_excel(ARQUIVO_DADOS)
    
    # Limpa espaços em branco ocultos nos nomes das colunas originais
    df.columns = [str(col).strip() for col in df.columns]
    
    # Descobre os nomes exatos das colunas por posição física
    NOME_COL_MUNICIPIO = df.columns[0]  # Primeira coluna (Coluna A)
    NOME_COL_SIGLA = df.columns[1]      # Segunda coluna (Coluna B)
    
    # Filtro Inteligente: Remove as linhas onde o município é idêntico ao estado, totais gerais ou nulos
    df_limpo = df[
        (df[NOME_COL_MUNICIPIO].astype(str).str.strip() != df[NOME_COL_SIGLA].astype(str).str.strip()) &
        (df[NOME_COL_MUNICIPIO].astype(str).str.upper().str.strip() != "TOTAL GERAL") &
        (df[NOME_COL_MUNICIPIO].astype(str).str.upper().str.strip() != "ZZ") &
        (df[NOME_COL_MUNICIPIO].notna())
    ].copy()
    
    # Realiza os cálculos de margem (PL - PT)
    df_limpo["DIFERENCA_PL_PT"] = df_limpo["PL"] - df_limpo["PT"]
    
    # GARANTIA DA SIGLA: Monta estritamente o Nome da Cidade e a UF entre parênteses
    df_limpo["Cidade_UF"] = df_limpo[NOME_COL_MUNICIPIO].astype(str).str.strip() + " (" + df_limpo[NOME_COL_SIGLA].astype(str).str.strip() + ")"
    
    st.sidebar.header("🔧 Configurações da Análise")
    
    # Filtro dinâmico de Partidos para o Gráfico 1
    colunas_excluir = [NOME_COL_MUNICIPIO, NOME_COL_SIGLA, "Total Geral", "TOTAL GERAL", "CHAVE_UF", "GEOCODIGO", "chave_uf", "geocodigo", "CIDADE_UF", "Cidade_UF", "DIFERENCA_PL_PT"]
    colunas_partidos = [col for col in df_limpo.columns if col not in colunas_excluir]
    
    partidos_selecionados = st.sidebar.multiselect(
        "Escolha os Partidos para comparar:",
        options=colunas_partidos,
        default=[p for p in ["PT", "PL"] if p in colunas_partidos] if len([p for p in ["PT", "PL"] if p in colunas_partidos]) == 2 else colunas_partidos[:2]
    )
    
    # === NOVO FILTRO DE ESTADOS ADICIONADO AQUI ===
    lista_estados_disponiveis = sorted(df_limpo[NOME_COL_SIGLA].unique().astype(str))
    estados_selecionados = st.sidebar.multiselect(
        "Filtre os Estados (UF) desejados:",
        options=lista_estados_disponiveis,
        default=[]  # Deixe vazio para listar todas as cidades inicialmente
    )
    
    # Filtrando dinamicamente a base de dados que alimenta a caixa de seleção de cidades
    if estados_selecionados:
        df_filtrado_por_estado = df_limpo[df_limpo[NOME_COL_SIGLA].isin(estados_selecionados)]
    else:
        df_filtrado_por_estado = df_limpo
    
    # Ordena a lista de busca em ordem alfabética (A-Z) considerando o filtro de estados acima
    lista_busca_completa = sorted(df_filtrado_por_estado["Cidade_UF"].unique(), key=lambda s: remover_acentos(s).lower())
    
    # Pré-seleciona Ariquemes e Cacoal com o formato correto se estiverem disponíveis na lista filtrada
    opcoes_padrao = [c for c in lista_busca_completa if "ARIQUEMES (RO)" in c or "CACOAL (RO)" in c]
    
    cidades_uf_selecionadas = st.sidebar.multiselect(
        "Busque e adicione cidades para analisar (Ordem A-Z):",
        options=lista_busca_completa,
        default=opcoes_padrao if opcoes_padrao else lista_busca_completa[:2]
    )
    
    # Filtragem e ordenação final das cidades selecionadas pelo usuário
    df_final = df_limpo[df_limpo["Cidade_UF"].isin(cidades_uf_selecionadas)]
    df_final = df_final.sort_values(by=NOME_COL_MUNICIPIO, key=lambda col: col.apply(remover_acentos))
    
    # Geração do botão para baixar o relatório em PDF na barra lateral
    if not df_final.empty:
        st.sidebar.subheader("📄 Exportação")
        try:
            nome_pdf = gerar_pdf(df_final, NOME_COL_MUNICIPIO, NOME_COL_SIGLA)
            with open(nome_pdf, "rb") as pdf_file:
                st.sidebar.download_button(
                    label="📥 Baixar Relatório em PDF",
                    data=pdf_file,
                    file_name="relatorio_eleitoral_pl_pt.pdf",
                    mime="application/pdf"
                )
        except Exception as e:
            st.sidebar.error("Erro ao gerar o PDF.")
            
    # Exibição dos Gráficos na tela principal
    if not df_final.empty:
        st.subheader("📊 Gráfico 1: Votação Absoluta por Partido")
        df_melted = df_final.melt(id_vars=["Cidade_UF"], value_vars=partidos_selecionados, var_name="Partido", value_name="Votos")
        cores_mapa = {"PL": "#1E90FF", "PT": "#FF1A1A", "PSD": "#00CC96", "NOVO": "#FF7F0E"}
        
        fig1 = px.bar(
            df_melted,
            x="Cidade_UF",
            y="Votos",
            color="Partido",
            barmode="group",
            color_discrete_map=cores_mapa,
            category_orders={"Cidade_UF": [c for c in lista_busca_completa if c in cidades_uf_selecionadas]},
            labels={"Cidade_UF": "Cidade (UF)", "Votos": "Quantidade de Votos"}
        )
        st.plotly_chart(fig1, use_container_width=True)
        
        st.subheader("⚖️ Gráfico 2: Margem de Diferença de Votos com Cor do Ganhador")
        st.caption("Barras VERMELHAS para baixo = PT na frente | Barras AZUIS para cima = PL na frente")
        
        df_final = df_final.copy()
        df_final["Cor_Partido"] = df_final["DIFERENCA_PL_PT"].apply(lambda x: "Vantagem PL" if x >= 0 else "Vantagem PT")
        
        fig2 = px.bar(
            df_final,
            x="Cidade_UF",
            y="DIFERENCA_PL_PT",
            color="Cor_Partido",
            color_discrete_map={"Vantagem PL": "#1E90FF", "Vantagem PT": "#FF1A1A"},
            category_orders={"Cidade_UF": [c for c in lista_busca_completa if c in cidades_uf_selecionadas]},
            labels={"Cidade_UF": "Cidade (UF)", "DIFERENCA_PL_PT": "Diferença Absoluta (PL - PT)"}
        )
        st.plotly_chart(fig2, use_container_width=True)
        
        st.subheader("📝 Demonstrativo Detalhado de Diferenças")
        df_tabela_resumo = df_final[[NOME_COL_MUNICIPIO, NOME_COL_SIGLA, "PL", "PT", "DIFERENCA_PL_PT"]].copy()
        df_tabela_resumo.columns = ["Cidade", "UF", "Votos PL", "Votos PT", "Diferença Absoluta (PL - PT)"]
        st.dataframe(df_tabela_resumo.set_index("Cidade"), use_container_width=True)
        
    else:
        st.warning("Selecione cidades na barra lateral para carregar os gráficos.")
        
    st.subheader("📋 Tabela Completa de Dados (Planilha Original)")
    st.dataframe(df, use_container_width=True)
    
else:
    st.error(f"❌ O arquivo '{ARQUIVO_DADOS}' não foi encontrado.")
