# ============================================================
# ASSEUF - SISTEMA DE CÁLCULO E RELATÓRIOS
# Versão completa, comentada, com PDF, QR Code e UX fluida
# ============================================================

import streamlit as st
import pandas as pd
import altair as alt
from io import BytesIO
import qrcode
import base64
from datetime import datetime

# ============================================================
# CONFIGURAÇÃO DA PÁGINA
# ============================================================
st.set_page_config(
    page_title="ASSEUF - Sistema de Cálculo",
    layout="wide",
)

# ============================================================
# CSS GLOBAL (ESTILO NEON + CARDS)
# ============================================================
st.markdown("""
<style>
body {
    background-color: #0b0c10;
    color: #f5f5f5;
    font-family: "Segoe UI", sans-serif;
}

/* Container principal do app */
.main {
    background: linear-gradient(135deg, #0b0c10 0%, #1f2833 50%, #0b0c10 100%);
}

/* Título neon */
.neon-title {
    font-size: 32px;
    font-weight: 800;
    text-align: center;
    color: #66fcf1;
    text-shadow:
        0 0 5px #66fcf1,
        0 0 10px #45a29e,
        0 0 20px #45a29e;
    margin-bottom: 5px;
}

/* Subtítulo */
.neon-subtitle {
    font-size: 16px;
    text-align: center;
    color: #c5c6c7;
    margin-bottom: 20px;
}

/* Caixa de explicação inicial */
.info-box {
    border-radius: 10px;
    border: 1px solid #45a29e;
    padding: 15px;
    background: rgba(15, 32, 39, 0.85);
    color: #f5f5f5;
    margin-bottom: 20px;
}

/* Cards de métricas */
.metric-card {
    background: rgba(31, 40, 51, 0.95);
    padding: 15px;
    border-radius: 10px;
    text-align: center;
    border: 1px solid #45a29e;
    box-shadow: 0 0 10px rgba(69, 162, 158, 0.4);
}
.metric-label {
    font-size: 14px;
    color: #c5c6c7;
}
.metric-value {
    font-size: 22px;
    font-weight: bold;
    color: #66fcf1;
}
.metric-sub {
    font-size: 11px;
    color: #9a9a9a;
}

/* Divisor */
.divider {
    margin: 25px 0;
    border-bottom: 2px solid #45a29e;
}

/* Títulos de seção */
.section-title {
    font-size: 22px;
    font-weight: 700;
    color: #66fcf1;
    margin-top: 10px;
}

/* Tabelas HTML no PDF (quando exibidas em preview) */
table {
    border-collapse: collapse;
}
th, td {
    border: 1px solid #999;
    padding: 4px 6px;
    font-size: 12px;
}
th {
    background-color: #1f2833;
    color: #f5f5f5;
}
</style>
""", unsafe_allow_html=True)

# ============================================================
# CABEÇALHO COM LOGO + TÍTULO NEON
# ============================================================
col_logo, col_title = st.columns([1, 3])

with col_logo:
    # Você pode trocar essa URL pela logo oficial da ASSEUF
    st.image(
        "https://upload.wikimedia.org/wikipedia/commons/thumb/3/3f/Logo_Unicamp_vertical.svg/1200px-Logo_Unicamp_vertical.svg.png",
        width=90,
        caption="Logo ilustrativa (troque pela da ASSEUF)"
    )

with col_title:
    st.markdown("<div class='neon-title'>ASSEUF • Sistema de Cálculo e Relatórios</div>", unsafe_allow_html=True)
    st.markdown(
        "<div class='neon-subtitle'>Gestão das rotas Sete Lagoas e Curvelo • Cálculos, critérios, relatórios e PDF profissional</div>",
        unsafe_allow_html=True
    )

# ============================================================
# EXPLICAÇÃO INICIAL DOS CRITÉRIOS (CAIXA DETALHADA)
# ============================================================
with st.expander("📘 Como funciona o sistema e quais são os critérios? (clique para ver)", expanded=True):
    st.markdown(
        """
        Este sistema foi pensado para **organizar e automatizar** os cálculos mensais das rotas da ASSEUF, com foco em:

        - 🚌 **Rotas atendidas:** Sete Lagoas e Curvelo  
        - 👨‍🎓 **Tipos de alunos:** integrais e com desconto  
        - 💸 **Critérios de cálculo:**  
          - Cálculo do **bruto original** por rota  
          - Desconto automático de **10% sobre o total de passagens**  
          - Cálculo do **bruto ajustado** (bruto - 10% das passagens)  
          - Distribuição **proporcional do auxílio** entre as rotas  
          - Cálculo das **passagens líquidas**  
          - Cálculo do **líquido final** por rota  
          - Cálculo da **mensalidade base** por aluno equivalente  

        - 🧮 **Aluno equivalente:**  
          - 1 aluno integral = 1,0 equivalente  
          - 1 aluno com 10% de desconto = 0,9 equivalente  
          - 1 aluno com 20% de desconto = 0,8 equivalente  
          - ... e assim por diante  

        - 📊 **O que você poderá ver:**  
          - Resumo financeiro por rota  
          - Comparativo visual entre Sete Lagoas e Curvelo  
          - Detalhamento de alunos, descontos e valores  
          - Geração de **PDF profissional** com todos os dados  
          - Inclusão de **QR Code** no relatório (opcional)  

        - 🧷 **Campos adicionais nesta versão completa:**  
          - Número de veículos por rota  
          - Diárias de motoristas  
          - Custos extras (manutenção, pedágio, etc.)  
          - Observações gerais do mês  

        Use este sistema como **base de transparência e organização**, mantendo um histórico mensal confiável.
        """,
        unsafe_allow_html=True
    )

# ============================================================
# FUNÇÃO PARA GERAR QR CODE EM BASE64
# ============================================================
def gerar_qr_base64(texto: str) -> str:
    """
    Gera um QR Code a partir de um texto e retorna a imagem em base64,
    para ser usada tanto na interface quanto dentro do PDF.
    """
    qr = qrcode.QRCode(box_size=2, border=2)
    qr.add_data(texto)
    qr.make(fit=True)
    img = qr.make_image(fill_color="black", back_color="white")

    buffer = BytesIO()
    img.save(buffer, format="PNG")
    return base64.b64encode(buffer.getvalue()).decode()

# ============================================================
# FUNÇÃO PARA MONTAR LINHAS DE ALUNOS EM HTML (PARA PDF)
# ============================================================
def montar_linhas_alunos_html(nome_rota, integrais, mensalidade, descontos):
    """
    Monta as linhas de uma tabela HTML com:
    - alunos integrais
    - alunos com desconto
    para uma rota específica.
    Essa função é usada na construção do PDF.
    """
    html = ""

    # Linha de alunos integrais
    total_int = integrais * mensalidade
    html += f"""
        <tr>
            <td>{nome_rota}</td>
            <td>Integrais</td>
            <td>{integrais}</td>
            <td>R$ {mensalidade:,.2f}</td>
            <td>R$ {total_int:,.2f}</td>
        </tr>
    """

    # Linhas de alunos com desconto
    if descontos:
        for pct, qtd in descontos.items():
            fator = (100 - pct) / 100
            valor_ind = mensalidade * fator
            total = valor_ind * qtd

            html += f"""
                <tr>
                    <td>{nome_rota}</td>
                    <td>{pct}% desconto</td>
                    <td>{qtd}</td>
                    <td>R$ {valor_ind:,.2f}</td>
                    <td>R$ {total:,.2f}</td>
                </tr>
            """

    return html

# ============================================================
# FUNÇÃO AUXILIAR: CÁLCULO DE ALUNOS EQUIVALENTES
# ============================================================
def calcular_alunos_equivalentes(integrais: int, descontos: dict) -> float:
    """
    Calcula o total de alunos equivalentes, considerando:
    - 1,0 para integrais
    - (100 - pct_desconto)/100 para cada aluno com desconto
    """
    total = float(integrais)
    for pct, qtd in descontos.items():
        fator = (100 - pct) / 100
        total += qtd * fator
    return total
# ============================================================
# FUNÇÃO PARA GERAR PDF PROFISSIONAL (USANDO PDFME)
# ============================================================
def gerar_pdf_profissional(dados: dict) -> bytes:
    """
    Gera um PDF profissional com:
    - Logo
    - QR Code
    - Resumo financeiro
    - Tabelas de alunos e descontos
    - Informações adicionais (veículos, diárias, custos extras)
    - Observações do mês

    Usa a biblioteca pdfme, que é compatível com o ambiente do Render.
    """
    from pdfme import build_pdf, Document
    from io import BytesIO

    # --------------------------------------------------------
    # 1. Coleta de dados principais
    # --------------------------------------------------------
    mes_ref = dados.get("mes_ref", "").strip() or "Mês não informado"

    # Rotas
    bruto_sete = dados["bruto_sete"]
    bruto_cur = dados["bruto_cur"]
    pass_sete = dados["pass_sete"]
    pass_cur = dados["pass_cur"]
    desc10_sete = dados["desc10_sete"]
    desc10_cur = dados["desc10_cur"]
    bruto_aj_sete = dados["bruto_aj_sete"]
    bruto_aj_cur = dados["bruto_aj_cur"]
    aux_total = dados["aux_total"]
    aux_sete = dados["aux_sete"]
    aux_cur = dados["aux_cur"]
    pass_liq_sete = dados["pass_liq_sete"]
    pass_liq_cur = dados["pass_liq_cur"]
    liquido_sete = dados["liquido_sete"]
    liquido_cur = dados["liquido_cur"]

    # Alunos e descontos
    int_sete = dados["int_sete"]
    int_cur = dados["int_cur"]
    desc_sete = dados["desc_sete"]
    desc_cur = dados["desc_cur"]
    mensal_sete = dados["mensal_sete"]
    mensal_cur = dados["mensal_cur"]

    # Campos adicionais
    veic_sete = dados.get("veic_sete", 0)
    veic_cur = dados.get("veic_cur", 0)
    diaria_sete = dados.get("diaria_sete", 0.0)
    diaria_cur = dados.get("diaria_cur", 0.0)
    custo_extra_sete = dados.get("custo_extra_sete", 0.0)
    custo_extra_cur = dados.get("custo_extra_cur", 0.0)
    obs_gerais = dados.get("obs_gerais", "").strip()

    # QR Code (texto resumido do relatório)
    texto_qr = f"Relatório ASSEUF - {mes_ref} | Sete Lagoas: R$ {liquido_sete:,.2f} | Curvelo: R$ {liquido_cur:,.2f}"
    qr_b64 = gerar_qr_base64(texto_qr)

    # --------------------------------------------------------
    # 2. Construção do conteúdo do PDF (estrutura pdfme)
    # --------------------------------------------------------
    conteudo = []

    # Cabeçalho com título
    conteudo.append({"h1": "ASSEUF - Relatório Mensal das Rotas"})
    conteudo.append({"p": f"Mês de referência: {mes_ref}"})

    # Logo + QR Code em tabela
    conteudo.append(
        {
            "table": {
                "data": [
                    [
                        {"image": {
                            # Aqui você pode trocar por um caminho local ou outro recurso
                            "url": "https://upload.wikimedia.org/wikipedia/commons/thumb/3/3f/Logo_Unicamp_vertical.svg/1200px-Logo_Unicamp_vertical.svg.png",
                            "width": 80,
                            "height": 80
                        }},
                        {"image": {
                            "data": qr_b64,
                            "format": "png",
                            "width": 80,
                            "height": 80
                        }},
                    ]
                ],
                "col_widths": [1, 1]
            }
        }
    )

    conteudo.append({"p": " "})
    conteudo.append({"h2": "Resumo Financeiro por Rota"})

    # Tabela de resumo financeiro
    conteudo.append(
        {
            "table": {
                "data": [
                    ["Indicador", "Sete Lagoas", "Curvelo"],
                    ["Bruto original", f"R$ {bruto_sete:,.2f}", f"R$ {bruto_cur:,.2f}"],
                    ["10% das passagens", f"R$ {desc10_sete:,.2f}", f"R$ {desc10_cur:,.2f}"],
                    ["Bruto ajustado", f"R$ {bruto_aj_sete:,.2f}", f"R$ {bruto_aj_cur:,.2f}"],
                    ["Auxílio recebido", f"R$ {aux_sete:,.2f}", f"R$ {aux_cur:,.2f}"],
                    ["Passagens líquidas", f"R$ {pass_liq_sete:,.2f}", f"R$ {pass_liq_cur:,.2f}"],
                    ["Líquido final", f"R$ {liquido_sete:,.2f}", f"R$ {liquido_cur:,.2f}"],
                ]
            }
        }
    )

    # Informações adicionais: veículos, diárias, custos extras
    conteudo.append({"h2": "Informações Operacionais"})
    conteudo.append(
        {
            "table": {
                "data": [
                    ["Rota", "Nº de veículos", "Diárias (R$)", "Custos extras (R$)"],
                    ["Sete Lagoas", str(veic_sete), f"R$ {diaria_sete:,.2f}", f"R$ {custo_extra_sete:,.2f}"],
                    ["Curvelo", str(veic_cur), f"R$ {diaria_cur:,.2f}", f"R$ {custo_extra_cur:,.2f}"],
                ]
            }
        }
    )

    # Tabela de alunos e mensalidades
    conteudo.append({"h2": "Alunos, Descontos e Mensalidades"})

    tabela_alunos = [
        ["Rota", "Tipo", "Qtd", "Valor individual", "Total"]
    ]

    # Integrais Sete Lagoas
    total_int_sete = int_sete * mensal_sete
    tabela_alunos.append(
        ["Sete Lagoas", "Integrais", int_sete, f"R$ {mensal_sete:,.2f}", f"R$ {total_int_sete:,.2f}"]
    )

    # Descontos Sete Lagoas
    for pct, qtd in desc_sete.items():
        fator = (100 - pct) / 100
        valor_ind = mensal_sete * fator
        total = valor_ind * qtd
        tabela_alunos.append(
            ["Sete Lagoas", f"{pct}% desconto", qtd, f"R$ {valor_ind:,.2f}", f"R$ {total:,.2f}"]
        )

    # Integrais Curvelo
    total_int_cur = int_cur * mensal_cur
    tabela_alunos.append(
        ["Curvelo", "Integrais", int_cur, f"R$ {mensal_cur:,.2f}", f"R$ {total_int_cur:,.2f}"]
    )

    # Descontos Curvelo
    for pct, qtd in desc_cur.items():
        fator = (100 - pct) / 100
        valor_ind = mensal_cur * fator
        total = valor_ind * qtd
        tabela_alunos.append(
            ["Curvelo", f"{pct}% desconto", qtd, f"R$ {valor_ind:,.2f}", f"R$ {total:,.2f}"]
        )

    conteudo.append({"table": {"data": tabela_alunos}})

    # Observações gerais
    conteudo.append({"h2": "Observações do mês"})
    if obs_gerais:
        conteudo.append({"p": obs_gerais})
    else:
        conteudo.append({"p": "Nenhuma observação adicional registrada para este mês."})

    # Rodapé
    agora = datetime.now().strftime("%d/%m/%Y %H:%M")
    conteudo.append(
        {
            "p": f"Relatório gerado automaticamente pelo Sistema ASSEUF em {agora}."
        }
    )

    # --------------------------------------------------------
    # 3. Geração do PDF em memória
    # --------------------------------------------------------
    buffer = BytesIO()
    build_pdf(Document(conteudo), buffer)
    return buffer.getvalue()
# ============================================================
# NAVEGAÇÃO PRINCIPAL
# ============================================================
pagina = st.sidebar.selectbox(
    "Navegação",
    ["📥 Cadastro e Cálculo", "📊 Relatórios e Gráficos"]
)

# ============================================================
# PÁGINA 1 - CADASTRO E CÁLCULO
# ============================================================
if pagina == "📥 Cadastro e Cálculo":
    st.markdown("<div class='section-title'>📥 Cadastro e Cálculo das Rotas</div>", unsafe_allow_html=True)
    st.markdown(
        """
        Nesta etapa você informa os dados brutos do mês, os alunos, descontos, veículos e custos.
        Ao final, o sistema calcula automaticamente:
        - o **líquido por rota**  
        - a **mensalidade base por aluno equivalente**  
        - a **distribuição do auxílio**  
        """,
        unsafe_allow_html=True
    )

    # --------------------------------------------------------
    # MÊS DE REFERÊNCIA
    # --------------------------------------------------------
    st.markdown("### 🗓️ Mês de referência")
    mes_ref = st.text_input("Mês de referência (ex: Janeiro/2025)")

    st.markdown("<div class='divider'></div>", unsafe_allow_html=True)

    # --------------------------------------------------------
    # ROTA SETE LAGOAS - DADOS PRINCIPAIS
    # --------------------------------------------------------
    st.markdown("<div class='section-title'>🚌 Rota Sete Lagoas</div>", unsafe_allow_html=True)
    st.markdown(
        "Informe os dados financeiros e operacionais da rota **Sete Lagoas**.",
        unsafe_allow_html=True
    )

    col_s1, col_s2, col_s3 = st.columns(3)

    with col_s1:
        bruto_sete = st.number_input(
            "Bruto original (Sete Lagoas)",
            min_value=0.0,
            step=0.01,
            help="Valor bruto total recebido pela rota Sete Lagoas antes de qualquer desconto."
        )

    with col_s2:
        pass_sete = st.number_input(
            "Passagens totais (Sete Lagoas)",
            min_value=0.0,
            step=0.01,
            help="Total de passagens consideradas para cálculo do desconto de 10%."
        )

    with col_s3:
        int_sete = st.number_input(
            "Qtd de alunos integrais (Sete Lagoas)",
            min_value=0,
            step=1,
            help="Quantidade de alunos que pagam o valor cheio, sem desconto."
        )

    # Campos adicionais: veículos, diárias, custos extras
    st.markdown("#### ⚙️ Operação da rota Sete Lagoas")
    col_sv1, col_sv2, col_sv3 = st.columns(3)

    with col_sv1:
        veic_sete = st.number_input(
            "Nº de veículos (Sete Lagoas)",
            min_value=0,
            step=1,
            help="Quantidade de veículos utilizados na rota Sete Lagoas."
        )

    with col_sv2:
        diaria_sete = st.number_input(
            "Diárias de motoristas (Sete Lagoas)",
            min_value=0.0,
            step=0.01,
            help="Total gasto com diárias de motoristas na rota Sete Lagoas."
        )

    with col_sv3:
        custo_extra_sete = st.number_input(
            "Custos extras (Sete Lagoas)",
            min_value=0.0,
            step=0.01,
            help="Outros custos (manutenção, pedágio, etc.) relacionados à rota Sete Lagoas."
        )

    # Descontos Sete Lagoas
    st.markdown("#### 🎯 Descontos aplicados em Sete Lagoas")
    st.markdown(
        "Selecione os **percentuais de desconto** utilizados e informe a **quantidade de alunos** em cada faixa.",
        unsafe_allow_html=True
    )

    desc_sete = {}
    col_ds1, col_ds2 = st.columns(2)

    with col_ds1:
        pct_desc_sete = st.multiselect(
            "Percentuais de desconto (Sete Lagoas)",
            [10, 20, 30, 40, 50],
            help="Escolha os percentuais de desconto que foram aplicados nesta rota."
        )

    with col_ds2:
        for pct in pct_desc_sete:
            qtd = st.number_input(
                f"Qtd de alunos com {pct}% desc (Sete Lagoas)",
                min_value=0,
                step=1
            )
            if qtd > 0:
                desc_sete[pct] = qtd

    st.markdown("<div class='divider'></div>", unsafe_allow_html=True)

    # --------------------------------------------------------
    # ROTA CURVELO - DADOS PRINCIPAIS
    # --------------------------------------------------------
    st.markdown("<div class='section-title'>🚌 Rota Curvelo</div>", unsafe_allow_html=True)
    st.markdown(
        "Informe os dados financeiros e operacionais da rota **Curvelo**.",
        unsafe_allow_html=True
    )

    col_c1, col_c2, col_c3 = st.columns(3)

    with col_c1:
        bruto_cur = st.number_input(
            "Bruto original (Curvelo)",
            min_value=0.0,
            step=0.01,
            help="Valor bruto total recebido pela rota Curvelo antes de qualquer desconto."
        )

    with col_c2:
        pass_cur = st.number_input(
            "Passagens totais (Curvelo)",
            min_value=0.0,
            step=0.01,
            help="Total de passagens consideradas para cálculo do desconto de 10%."
        )

    with col_c3:
        int_cur = st.number_input(
            "Qtd de alunos integrais (Curvelo)",
            min_value=0,
            step=1,
            help="Quantidade de alunos que pagam o valor cheio, sem desconto."
        )

    # Campos adicionais: veículos, diárias, custos extras
    st.markdown("#### ⚙️ Operação da rota Curvelo")
    col_cv1, col_cv2, col_cv3 = st.columns(3)

    with col_cv1:
        veic_cur = st.number_input(
            "Nº de veículos (Curvelo)",
            min_value=0,
            step=1,
            help="Quantidade de veículos utilizados na rota Curvelo."
        )

    with col_cv2:
        diaria_cur = st.number_input(
            "Diárias de motoristas (Curvelo)",
            min_value=0.0,
            step=0.01,
            help="Total gasto com diárias de motoristas na rota Curvelo."
        )

    with col_cv3:
        custo_extra_cur = st.number_input(
            "Custos extras (Curvelo)",
            min_value=0.0,
            step=0.01,
            help="Outros custos (manutenção, pedágio, etc.) relacionados à rota Curvelo."
        )

    # Descontos Curvelo
    st.markdown("#### 🎯 Descontos aplicados em Curvelo")
    st.markdown(
        "Selecione os **percentuais de desconto** utilizados e informe a **quantidade de alunos** em cada faixa.",
        unsafe_allow_html=True
    )

    desc_cur = {}
    col_dc1, col_dc2 = st.columns(2)

    with col_dc1:
        pct_desc_cur = st.multiselect(
            "Percentuais de desconto (Curvelo)",
            [10, 20, 30, 40, 50],
            help="Escolha os percentuais de desconto que foram aplicados nesta rota."
        )

    with col_dc2:
        for pct in pct_desc_cur:
            qtd = st.number_input(
                f"Qtd de alunos com {pct}% desc (Curvelo)",
                min_value=0,
                step=1
            )
            if qtd > 0:
                desc_cur[pct] = qtd

    st.markdown("<div class='divider'></div>", unsafe_allow_html=True)

    # --------------------------------------------------------
    # AUXÍLIO TOTAL DO MÊS
    # --------------------------------------------------------
    st.markdown("<div class='section-title'>💰 Auxílio total do mês</div>", unsafe_allow_html=True)
    st.markdown(
        "Informe o valor total do **auxílio recebido** no mês. Ele será distribuído **proporcionalmente** entre as rotas, "
        "de acordo com o **bruto ajustado** de cada uma.",
        unsafe_allow_html=True
    )

    aux_total = st.number_input(
        "Valor total do auxílio recebido",
        min_value=0.0,
        step=0.01
    )

    st.markdown("<div class='divider'></div>", unsafe_allow_html=True)

    # --------------------------------------------------------
    # OBSERVAÇÕES GERAIS DO MÊS
    # --------------------------------------------------------
    st.markdown("<div class='section-title'>📝 Observações gerais do mês</div>", unsafe_allow_html=True)
    obs_gerais = st.text_area(
        "Registre aqui qualquer observação relevante (ex: atrasos, manutenção extraordinária, mudanças de rota, etc.)",
        height=120
    )

    st.markdown("<div class='divider'></div>", unsafe_allow_html=True)

    # --------------------------------------------------------
    # BOTÃO DE CÁLCULO
    # --------------------------------------------------------
    st.markdown("### ✅ Finalizar cadastro e calcular valores")

    if st.button("Calcular e salvar resultados"):
        # 10% das passagens
        desc10_sete = pass_sete * 0.10
        desc10_cur = pass_cur * 0.10

        # Bruto ajustado
        bruto_aj_sete = bruto_sete - desc10_sete
        bruto_aj_cur = bruto_cur - desc10_cur

        # Distribuição proporcional do auxílio
        soma_aj = bruto_aj_sete + bruto_aj_cur
        if soma_aj > 0:
            aux_sete = aux_total * (bruto_aj_sete / soma_aj)
            aux_cur = aux_total * (bruto_aj_cur / soma_aj)
        else:
            aux_sete = 0.0
            aux_cur = 0.0

        # Passagens líquidas
        pass_liq_sete = pass_sete - desc10_sete
        pass_liq_cur = pass_cur - desc10_cur

        # Líquido final
        liquido_sete = bruto_aj_sete + aux_sete - pass_liq_sete - diaria_sete - custo_extra_sete
        liquido_cur = bruto_aj_cur + aux_cur - pass_liq_cur - diaria_cur - custo_extra_cur

        # Alunos equivalentes
        eq_sete = calcular_alunos_equivalentes(int_sete, desc_sete)
        eq_cur = calcular_alunos_equivalentes(int_cur, desc_cur)

        # Mensalidade base
        mensal_sete = liquido_sete / eq_sete if eq_sete > 0 else 0.0
        mensal_cur = liquido_cur / eq_cur if eq_cur > 0 else 0.0

        # Guardar tudo no session_state
        st.session_state["resultados"] = {
            "mes_ref": mes_ref,
            "bruto_sete": bruto_sete,
            "bruto_cur": bruto_cur,
            "pass_sete": pass_sete,
            "pass_cur": pass_cur,
            "desc10_sete": desc10_sete,
            "desc10_cur": desc10_cur,
            "bruto_aj_sete": bruto_aj_sete,
            "bruto_aj_cur": bruto_aj_cur,
            "aux_total": aux_total,
            "aux_sete": aux_sete,
            "aux_cur": aux_cur,
            "pass_liq_sete": pass_liq_sete,
            "pass_liq_cur": pass_liq_cur,
            "liquido_sete": liquido_sete,
            "liquido_cur": liquido_cur,
            "int_sete": int_sete,
            "int_cur": int_cur,
            "desc_sete": desc_sete,
            "desc_cur": desc_cur,
            "mensal_sete": mensal_sete,
            "mensal_cur": mensal_cur,
            "veic_sete": veic_sete,
            "veic_cur": veic_cur,
            "diaria_sete": diaria_sete,
            "diaria_cur": diaria_cur,
            "custo_extra_sete": custo_extra_sete,
            "custo_extra_cur": custo_extra_cur,
            "obs_gerais": obs_gerais,
        }

        st.success("✅ Cálculo realizado e resultados salvos! Vá para a aba '📊 Relatórios e Gráficos'.")
# ============================================================
# PÁGINA 2 - RELATÓRIOS, GRÁFICOS E PDF
# ============================================================
if pagina == "📊 Relatórios e Gráficos":
    st.markdown("<div class='section-title'>📊 Relatórios, Gráficos e PDF</div>", unsafe_allow_html=True)

    if "resultados" not in st.session_state:
        st.warning("Nenhum cálculo encontrado. Volte para a aba '📥 Cadastro e Cálculo' e finalize o cadastro.")
        st.stop()

    r = st.session_state["resultados"]

    # --------------------------------------------------------
    # RESUMO FINANCEIRO EM CARDS
    # --------------------------------------------------------
    st.markdown("### 💰 Resumo financeiro por rota")

    col_f1, col_f2, col_f3 = st.columns(3)

    with col_f1:
        st.markdown("<div class='metric-card'>", unsafe_allow_html=True)
        st.markdown("<div class='metric-label'>Líquido Sete Lagoas</div>", unsafe_allow_html=True)
        st.markdown(f"<div class='metric-value'>R$ {r['liquido_sete']:,.2f}</div>", unsafe_allow_html=True)
        st.markdown("<div class='metric-sub'>Após descontos, auxílio, diárias e custos extras</div>", unsafe_allow_html=True)
        st.markdown("</div>", unsafe_allow_html=True)

    with col_f2:
        st.markdown("<div class='metric-card'>", unsafe_allow_html=True)
        st.markdown("<div class='metric-label'>Líquido Curvelo</div>", unsafe_allow_html=True)
        st.markdown(f"<div class='metric-value'>R$ {r['liquido_cur']:,.2f}</div>", unsafe_allow_html=True)
        st.markdown("<div class='metric-sub'>Após descontos, auxílio, diárias e custos extras</div>", unsafe_allow_html=True)
        st.markdown("</div>", unsafe_allow_html=True)

    with col_f3:
        total_liq = r["liquido_sete"] + r["liquido_cur"]
        st.markdown("<div class='metric-card'>", unsafe_allow_html=True)
        st.markdown("<div class='metric-label'>Total geral (todas as rotas)</div>", unsafe_allow_html=True)
        st.markdown(f"<div class='metric-value'>R$ {total_liq:,.2f}</div>", unsafe_allow_html=True)
        st.markdown("<div class='metric-sub'>Soma dos líquidos das duas rotas</div>", unsafe_allow_html=True)
        st.markdown("</div>", unsafe_allow_html=True)

    st.markdown("<div class='divider'></div>", unsafe_allow_html=True)

    # --------------------------------------------------------
    # TABELA DE RESUMO FINANCEIRO
    # --------------------------------------------------------
    st.markdown("### 📋 Tabela de resumo financeiro detalhado")

    df_resumo = pd.DataFrame(
        [
            {
                "Rota": "Sete Lagoas",
                "Bruto original": r["bruto_sete"],
                "10% passagens": r["desc10_sete"],
                "Bruto ajustado": r["bruto_aj_sete"],
                "Auxílio recebido": r["aux_sete"],
                "Passagens líquidas": r["pass_liq_sete"],
                "Líquido final": r["liquido_sete"],
                "Veículos": r["veic_sete"],
                "Diárias": r["diaria_sete"],
                "Custos extras": r["custo_extra_sete"],
            },
            {
                "Rota": "Curvelo",
                "Bruto original": r["bruto_cur"],
                "10% passagens": r["desc10_cur"],
                "Bruto ajustado": r["bruto_aj_cur"],
                "Auxílio recebido": r["aux_cur"],
                "Passagens líquidas": r["pass_liq_cur"],
                "Líquido final": r["liquido_cur"],
                "Veículos": r["veic_cur"],
                "Diárias": r["diaria_cur"],
                "Custos extras": r["custo_extra_cur"],
            },
        ]
    )

    st.dataframe(
        df_resumo.style.format(
            {
                "Bruto original": "R$ {:,.2f}",
                "10% passagens": "R$ {:,.2f}",
                "Bruto ajustado": "R$ {:,.2f}",
                "Auxílio recebido": "R$ {:,.2f}",
                "Passagens líquidas": "R$ {:,.2f}",
                "Líquido final": "R$ {:,.2f}",
                "Diárias": "R$ {:,.2f}",
                "Custos extras": "R$ {:,.2f}",
            }
        ),
        use_container_width=True
    )

    st.markdown("<div class='divider'></div>", unsafe_allow_html=True)

    # --------------------------------------------------------
    # GRÁFICO COMPARATIVO DAS ROTAS
    # --------------------------------------------------------
    st.markdown("### 📈 Comparativo visual das rotas")

    df_graf = pd.DataFrame({
        "Rota": ["Sete Lagoas", "Curvelo"],
        "Líquido final": [r["liquido_sete"], r["liquido_cur"]],
        "Bruto ajustado": [r["bruto_aj_sete"], r["bruto_aj_cur"]],
    })

    graf_liq = (
        alt.Chart(df_graf)
        .mark_bar()
        .encode(
            x=alt.X("Rota", sort=None),
            y=alt.Y("Líquido final", title="Líquido final (R$)"),
            color=alt.value("#66fcf1")
        )
        .properties(
            height=300,
            title="Líquido final por rota"
        )
    )

    graf_bruto = (
        alt.Chart(df_graf)
        .mark_bar()
        .encode(
            x=alt.X("Rota", sort=None),
            y=alt.Y("Bruto ajustado", title="Bruto ajustado (R$)"),
            color=alt.value("#45a29e")
        )
        .properties(
            height=300,
            title="Bruto ajustado por rota"
        )
    )

    col_g1, col_g2 = st.columns(2)
    with col_g1:
        st.altair_chart(graf_liq, use_container_width=True)
    with col_g2:
        st.altair_chart(graf_bruto, use_container_width=True)

    st.markdown("<div class='divider'></div>", unsafe_allow_html=True)

    # --------------------------------------------------------
    # TABELA DE ALUNOS, DESCONTOS E MENSALIDADES
    # --------------------------------------------------------
    st.markdown("### 👨‍🎓 Alunos, descontos e mensalidades")

    linhas_alunos = []

    # Sete Lagoas - integrais
    total_int_sete = r["int_sete"] * r["mensal_sete"]
    linhas_alunos.append(
        {
            "Rota": "Sete Lagoas",
            "Tipo": "Integrais",
            "Qtd": r["int_sete"],
            "Valor individual": r["mensal_sete"],
            "Total": total_int_sete,
        }
    )

    # Sete Lagoas - descontos
    for pct, qtd in r["desc_sete"].items():
        fator = (100 - pct) / 100
        valor_ind = r["mensal_sete"] * fator
        total = valor_ind * qtd
        linhas_alunos.append(
            {
                "Rota": "Sete Lagoas",
                "Tipo": f"{pct}% desconto",
                "Qtd": qtd,
                "Valor individual": valor_ind,
                "Total": total,
            }
        )

    # Curvelo - integrais
    total_int_cur = r["int_cur"] * r["mensal_cur"]
    linhas_alunos.append(
        {
            "Rota": "Curvelo",
            "Tipo": "Integrais",
            "Qtd": r["int_cur"],
            "Valor individual": r["mensal_cur"],
            "Total": total_int_cur,
        }
    )

    # Curvelo - descontos
    for pct, qtd in r["desc_cur"].items():
        fator = (100 - pct) / 100
        valor_ind = r["mensal_cur"] * fator
        total = valor_ind * qtd
        linhas_alunos.append(
            {
                "Rota": "Curvelo",
                "Tipo": f"{pct}% desconto",
                "Qtd": qtd,
                "Valor individual": valor_ind,
                "Total": total,
            }
        )

    df_alunos = pd.DataFrame(linhas_alunos)

    st.dataframe(
        df_alunos.style.format(
            {
                "Valor individual": "R$ {:,.2f}",
                "Total": "R$ {:,.2f}",
            }
        ),
        use_container_width=True
    )

    st.markdown("<div class='divider'></div>", unsafe_allow_html=True)

    # --------------------------------------------------------
    # OBSERVAÇÕES DO MÊS
    # --------------------------------------------------------
    st.markdown("### 📝 Observações gerais do mês")

    if r.get("obs_gerais", "").strip():
        st.info(r["obs_gerais"])
    else:
        st.write("Nenhuma observação adicional registrada para este mês.")

    st.markdown("<div class='divider'></div>", unsafe_allow_html=True)

    # --------------------------------------------------------
    # GERAÇÃO DO PDF
    # --------------------------------------------------------
    st.markdown("### 📄 Geração de relatório em PDF")

    st.markdown(
        "Clique no botão abaixo para gerar um **PDF profissional** com todos os dados deste mês, "
        "incluindo resumo financeiro, alunos, descontos, veículos, diárias, custos extras e observações.",
        unsafe_allow_html=True
    )

    if st.button("📄 Gerar e baixar PDF"):
        pdf_bytes = gerar_pdf_profissional(r)

        st.download_button(
            label="⬇️ Clique aqui para baixar o PDF",
            data=pdf_bytes,
            file_name=f"relatorio_asseuf_{r['mes_ref'].replace('/', '_') or 'sem_mes'}.pdf",
            mime="application/pdf"
        )
# ============================================================
# RODAPÉ FINAL
# ============================================================
st.markdown("<div class='divider'></div>", unsafe_allow_html=True)

col_rod1, col_rod2 = st.columns([2, 1])

with col_rod1:
    st.markdown(
        """
        <p style='font-size:13px; color:#c5c6c7;'>
            <b>Sobre este sistema:</b><br>
            Este painel foi desenvolvido para apoiar a gestão das rotas da ASSEUF, permitindo:
            acompanhamento financeiro detalhado, cálculo de mensalidades por aluno equivalente,
            registro de custos operacionais e geração de relatórios em PDF com QR Code.
            <br><br>
            Use-o como base de transparência, prestação de contas e organização interna.
        </p>
        """,
        unsafe_allow_html=True
    )

with col_rod2:
    st.markdown(
        """
        <p style='font-size:12px; text-align:right; color:#9a9a9a;'>
            Sistema ASSEUF • Versão completa<br>
            Desenvolvido para uso interno das rotas<br>
            Sete Lagoas & Curvelo
        </p>
        """,
        unsafe_allow_html=True
    )