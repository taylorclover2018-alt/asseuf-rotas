import streamlit as st
import pandas as pd
import altair as alt
from io import BytesIO
import qrcode
import base64

# ============================================================
# CONFIGURAÇÃO DA PÁGINA
# ============================================================
st.set_page_config(
    page_title="ASSEUF - Sistema de Cálculo",
    layout="wide",
)

# ============================================================
# CSS GLOBAL
# ============================================================
st.markdown("""
<style>
.metric-card {
    background: #f5f5f5;
    padding: 15px;
    border-radius: 8px;
    text-align: center;
    border: 1px solid #ddd;
}
.metric-label {
    font-size: 14px;
    color: #555;
}
.metric-value {
    font-size: 22px;
    font-weight: bold;
    color: #00695c;
}
.metric-sub {
    font-size: 11px;
    color: #777;
}
.divider {
    margin: 25px 0;
    border-bottom: 2px solid #ccc;
}
</style>
""", unsafe_allow_html=True)

# ============================================================
# FUNÇÃO PARA GERAR QR CODE EM BASE64
# ============================================================
def gerar_qr_base64(texto: str) -> str:
    qr = qrcode.QRCode(box_size=2, border=2)
    qr.add_data(texto)
    qr.make(fit=True)
    img = qr.make_image(fill_color="black", back_color="white")

    buffer = BytesIO()
    img.save(buffer, format="PNG")
    return base64.b64encode(buffer.getvalue()).decode()

# ============================================================
# FUNÇÃO PARA MONTAR LINHAS DE ALUNOS EM HTML
# ============================================================
def montar_linhas_alunos_html(nome_rota, integrais, mensalidade, descontos):
    html = ""

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
# FUNÇÃO PARA GERAR PDF PROFISSIONAL (USANDO PDFME)
# ============================================================
def gerar_pdf_profissional(r: dict) -> bytes:
    from pdfme import build_pdf, Document
    from io import BytesIO

    mes_ref = r.get("mes_ref", "").strip() or "Mês não informado"

    conteudo = [
        {"h1": "ASSEUF - Relatório Mensal"},
        {"p": f"Mês de referência: {mes_ref}"},
        {"h2": "Resumo Financeiro"},
        {
            "table": {
                "data": [
                    ["Indicador", "Sete Lagoas", "Curvelo"],
                    ["Bruto original", f"R$ {r['bruto_sete']:,.2f}", f"R$ {r['bruto_cur']:,.2f}"],
                    ["10% das passagens", f"R$ {r['desc10_sete']:,.2f}", f"R$ {r['desc10_cur']:,.2f}"],
                    ["Bruto ajustado", f"R$ {r['bruto_aj_sete']:,.2f}", f"R$ {r['bruto_aj_cur']:,.2f}"],
                    ["Auxílio recebido", f"R$ {r['aux_sete']:,.2f}", f"R$ {r['aux_cur']:,.2f}"],
                    ["Passagens líquidas", f"R$ {r['pass_liq_sete']:,.2f}", f"R$ {r['pass_liq_cur']:,.2f}"],
                    ["Líquido final", f"R$ {r['liquido_sete']:,.2f}", f"R$ {r['liquido_cur']:,.2f}"],
                ]
            }
        },
        {"h2": "Mensalidades e Alunos"},
        {
            "table": {
                "data": [
                    ["Rota", "Tipo", "Qtd", "Valor individual", "Total"],
                    ["Sete Lagoas", "Integrais", r["int_sete"], f"R$ {r['mensal_sete']:,.2f}", f"R$ {r['int_sete'] * r['mensal_sete']:,.2f}"],
                ]
            }
        }
    ]

    # Descontos Sete Lagoas
    for pct, qtd in r["desc_sete"].items():
        valor_ind = r["mensal_sete"] * ((100 - pct) / 100)
        conteudo.append({
            "table": {
                "data": [
                    ["Sete Lagoas", f"{pct}% desconto", qtd, f"R$ {valor_ind:,.2f}", f"R$ {valor_ind * qtd:,.2f}"]
                ]
            }
        })

    # Integrais Curvelo
    conteudo.append({
        "table": {
            "data": [
                ["Curvelo", "Integrais", r["int_cur"], f"R$ {r['mensal_cur']:,.2f}", f"R$ {r['int_cur'] * r['mensal_cur']:,.2f}"]
            ]
        }
    })

    # Descontos Curvelo
    for pct, qtd in r["desc_cur"].items():
        valor_ind = r["mensal_cur"] * ((100 - pct) / 100)
        conteudo.append({
            "table": {
                "data": [
                    ["Curvelo", f"{pct}% desconto", qtd, f"R$ {valor_ind:,.2f}", f"R$ {valor_ind * qtd:,.2f}"]
                ]
            }
        })

    conteudo.append({"p": "Relatório gerado automaticamente pelo Sistema ASSEUF."})

    buffer = BytesIO()
    build_pdf(Document(conteudo), buffer)
    return buffer.getvalue()
# ============================================================
# PAGINA 1 - CADASTRO E CALCULO
# ============================================================
pagina = st.sidebar.selectbox(
    "Navegação",
    ["Cadastro e Calculo", "Relatorios e Graficos"]
)

if pagina == "Cadastro e Calculo":
    st.markdown("<h1>Cadastro e Cálculo das Rotas</h1>", unsafe_allow_html=True)

    # Entrada do mês de referência
    mes_ref = st.text_input("Mês de referência (ex: Janeiro/2025)")

    # ============================================================
    # ROTA SETE LAGOAS
    # ============================================================
    st.markdown("## Dados da Rota Sete Lagoas")

    bruto_sete = st.number_input("Bruto original (Sete Lagoas)", min_value=0.0, step=0.01)
    pass_sete = st.number_input("Passagens totais (Sete Lagoas)", min_value=0.0, step=0.01)
    int_sete = st.number_input("Quantidade de alunos integrais (Sete Lagoas)", min_value=0, step=1)

    st.markdown("### Descontos Sete Lagoas")
    desc_sete = {}
    colA, colB = st.columns(2)

    with colA:
        pct_desc_sete = st.multiselect("Percentuais de desconto (Sete Lagoas)", [10, 20, 30, 40, 50])

    with colB:
        for pct in pct_desc_sete:
            qtd = st.number_input(f"Qtd com {pct}% desc (Sete Lagoas)", min_value=0, step=1)
            if qtd > 0:
                desc_sete[pct] = qtd

    st.markdown("<div class='divider'></div>", unsafe_allow_html=True)

    # ============================================================
    # ROTA CURVELO
    # ============================================================
    st.markdown("## Dados da Rota Curvelo")

    bruto_cur = st.number_input("Bruto original (Curvelo)", min_value=0.0, step=0.01)
    pass_cur = st.number_input("Passagens totais (Curvelo)", min_value=0.0, step=0.01)
    int_cur = st.number_input("Quantidade de alunos integrais (Curvelo)", min_value=0, step=1)

    st.markdown("### Descontos Curvelo")
    desc_cur = {}
    colC, colD = st.columns(2)

    with colC:
        pct_desc_cur = st.multiselect("Percentuais de desconto (Curvelo)", [10, 20, 30, 40, 50])

    with colD:
        for pct in pct_desc_cur:
            qtd = st.number_input(f"Qtd com {pct}% desc (Curvelo)", min_value=0, step=1)
            if qtd > 0:
                desc_cur[pct] = qtd

    st.markdown("<div class='divider'></div>", unsafe_allow_html=True)

    # ============================================================
    # AUXÍLIO TOTAL
    # ============================================================
    st.markdown("## Auxílio total do mês")
    aux_total = st.number_input("Valor total do auxílio recebido", min_value=0.0, step=0.01)

    # ============================================================
    # BOTÃO DE CÁLCULO
    # ============================================================
    if st.button("Calcular"):
        # 10% das passagens
        desc10_sete = pass_sete * 0.10
        desc10_cur = pass_cur * 0.10

        # Bruto ajustado
        bruto_aj_sete = bruto_sete - desc10_sete
        bruto_aj_cur = bruto_cur - desc10_cur

        # Divisão proporcional do auxílio
        soma_aj = bruto_aj_sete + bruto_aj_cur
        if soma_aj > 0:
            aux_sete = aux_total * (bruto_aj_sete / soma_aj)
            aux_cur = aux_total * (bruto_aj_cur / soma_aj)
        else:
            aux_sete = 0
            aux_cur = 0

        # Passagens líquidas
        pass_liq_sete = pass_sete - desc10_sete
        pass_liq_cur = pass_cur - desc10_cur

        # Líquido final
        liquido_sete = bruto_aj_sete + aux_sete - pass_liq_sete
        liquido_cur = bruto_aj_cur + aux_cur - pass_liq_cur

        # Função para calcular alunos equivalentes
        def alunos_equivalentes(integrais, descontos):
            total = integrais
            for pct, qtd in descontos.items():
                total += qtd * ((100 - pct) / 100)
            return total

        eq_sete = alunos_equivalentes(int_sete, desc_sete)
        eq_cur = alunos_equivalentes(int_cur, desc_cur)

        # Mensalidade base
        mensal_sete = liquido_sete / eq_sete if eq_sete > 0 else 0
        mensal_cur = liquido_cur / eq_cur if eq_cur > 0 else 0

        # Guardar resultados
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
        }

        st.success("Cálculo realizado com sucesso! Vá para a aba 'Relatórios e Gráficos'.")
# ============================================================
# PAGINA 2 - RELATÓRIOS, GRÁFICOS E PDF
# ============================================================
if pagina == "Relatorios e Graficos":
    st.markdown("<h1>Relatórios e Gráficos</h1>", unsafe_allow_html=True)

    if "resultados" not in st.session_state:
        st.warning("Nenhum cálculo encontrado. Volte para a aba 'Cadastro e Cálculo'.")
        st.stop()

    r = st.session_state["resultados"]

    # ============================================================
    # RESUMO FINANCEIRO
    # ============================================================
    st.markdown("## Resumo Financeiro")

    col1, col2, col3 = st.columns(3)

    with col1:
        st.markdown("<div class='metric-card'>", unsafe_allow_html=True)
        st.markdown("<div class='metric-label'>Líquido Sete Lagoas</div>", unsafe_allow_html=True)
        st.markdown(f"<div class='metric-value'>R$ {r['liquido_sete']:,.2f}</div>", unsafe_allow_html=True)
        st.markdown("</div>", unsafe_allow_html=True)

    with col2:
        st.markdown("<div class='metric-card'>", unsafe_allow_html=True)
        st.markdown("<div class='metric-label'>Líquido Curvelo</div>", unsafe_allow_html=True)
        st.markdown(f"<div class='metric-value'>R$ {r['liquido_cur']:,.2f}</div>", unsafe_allow_html=True)
        st.markdown("</div>", unsafe_allow_html=True)

    with col3:
        total_liq = r["liquido_sete"] + r["liquido_cur"]
        st.markdown("<div class='metric-card'>", unsafe_allow_html=True)
        st.markdown("<div class='metric-label'>Total Geral</div>", unsafe_allow_html=True)
        st.markdown(f"<div class='metric-value'>R$ {total_liq:,.2f}</div>", unsafe_allow_html=True)
        st.markdown("</div>", unsafe_allow_html=True)

    st.markdown("<div class='divider'></div>", unsafe_allow_html=True)

    # ============================================================
    # GRÁFICO DE BARRAS
    # ============================================================
    st.markdown("## Comparativo das Rotas")

    df_graf = pd.DataFrame({
        "Rota": ["Sete Lagoas", "Curvelo"],
        "Líquido": [r["liquido_sete"], r["liquido_cur"]]
    })

    graf = (
        alt.Chart(df_graf)
        .mark_bar(color="#00695c")
        .encode(
            x="Rota",
            y="Líquido"
        )
        .properties(height=300)
    )

    st.altair_chart(graf, use_container_width=True)

    st.markdown("<div class='divider'></div>", unsafe_allow_html=True)

    # ============================================================
    # BOTÃO PARA GERAR PDF
    # ============================================================
    st.markdown("## Gerar Relatório em PDF")

    if st.button("Baixar PDF"):
        pdf_bytes = gerar_pdf_profissional(r)

        st.download_button(
            label="Clique aqui para baixar o PDF",
            data=pdf_bytes,
            file_name="relatorio_asseuf.pdf",
            mime="application/pdf"
        )
# ============================================================
# RODAPÉ FINAL
# ============================================================
st.markdown("<div class='divider'></div>", unsafe_allow_html=True)

st.markdown(
    """
    <p style='text-align:center; font-size:12px; color:#777;'>
        Sistema ASSEUF • Relatórios automáticos das rotas Sete Lagoas e Curvelo<br>
        Desenvolvido para auxiliar no cálculo mensal e geração de documentos
    </p>
    """,
    unsafe_allow_html=True
)