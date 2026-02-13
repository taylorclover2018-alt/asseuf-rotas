import streamlit as st
import pandas as pd
import altair as alt
from io import BytesIO
from xhtml2pdf import pisa
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

    # Integrais
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

    # Descontos
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
            aux_sete = aux_cur = 0

        # Passagens líquidas
        pass_liq_sete = pass_sete - desc10_sete
        pass_liq_cur = pass_cur - desc10_cur

        # Líquido final
        liquido_sete = bruto_aj_sete + aux_sete - pass_liq_sete
        liquido_cur = bruto_aj_cur + aux_cur - pass_liq_cur

        # Alunos equivalentes
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
# FUNÇÃO PARA GERAR PDF PROFISSIONAL (USANDO XHTML2PDF)
# ============================================================
def gerar_pdf_profissional(r: dict) -> bytes:
    qr_b64 = gerar_qr_base64("Relatorio ASSEUF - Rotas Sete Lagoas e Curvelo")
    mes_ref = r.get("mes_ref", "").strip() or "Mes nao informado"

    # Montar linhas das tabelas
    linhas_sete = montar_linhas_alunos_html(
        "Sete Lagoas",
        r["int_sete"],
        r["mensal_sete"],
        r["desc_sete"]
    )

    linhas_cur = montar_linhas_alunos_html(
        "Curvelo",
        r["int_cur"],
        r["mensal_cur"],
        r["desc_cur"]
    )

    # HTML do PDF
    html = f"""
    <html>
    <head>
        <meta charset="utf-8">
        <style>
            body {{
                font-family: Arial, sans-serif;
                margin: 30px;
                color: #222;
            }}
            h1, h2, h3 {{
                color: #00695c;
            }}
            table {{
                width: 100%;
                border-collapse: collapse;
                margin-top: 15px;
                margin-bottom: 20px;
            }}
            th, td {{
                border: 1px solid #bbb;
                padding: 6px 8px;
                font-size: 12px;
            }}
            th {{
                background-color: #e0f2f1;
            }}
            .small {{
                font-size: 11px;
                color: #555;
            }}
        </style>
    </head>

    <body>
        <h1>ASSEUF - Relatório Mensal</h1>
        <p class="small">Mês de referência: {mes_ref}</p>

        <h2>Resumo Financeiro</h2>
        <table>
            <tr><th>Indicador</th><th>Sete Lagoas</th><th>Curvelo</th></tr>

            <tr><td>Bruto original</td>
                <td>R$ {r["bruto_sete"]:,.2f}</td>
                <td>R$ {r["bruto_cur"]:,.2f}</td></tr>

            <tr><td>10% das passagens</td>
                <td>R$ {r["desc10_sete"]:,.2f}</td>
                <td>R$ {r["desc10_cur"]:,.2f}</td></tr>

            <tr><td>Bruto ajustado</td>
                <td>R$ {r["bruto_aj_sete"]:,.2f}</td>
                <td>R$ {r["bruto_aj_cur"]:,.2f}</td></tr>

            <tr><td>Auxílio recebido</td>
                <td>R$ {r["aux_sete"]:,.2f}</td>
                <td>R$ {r["aux_cur"]:,.2f}</td></tr>

            <tr><td>Passagens líquidas</td>
                <td>R$ {r["pass_liq_sete"]:,.2f}</td>
                <td>R$ {r["pass_liq_cur"]:,.2f}</td></tr>

            <tr><td>Liquido final</td>
                <td>R$ {r["liquido_sete"]:,.2f}</td>
                <td>R$ {r["liquido_cur"]:,.2f}</td></tr>
        </table>

        <h2>Alunos e Mensalidades</h2>
        <table>
            <tr>
                <th>Rota</th>
                <th>Tipo</th>
                <th>Quantidade</th>
                <th>Valor individual</th>
                <th>Total</th>
            </tr>

            {linhas_sete}
            {linhas_cur}
        </table>

        <p class="small">
            Relatório gerado automaticamente pelo Sistema ASSEUF.
        </p>
    </body>
    </html>
    """

    # Gerar PDF em memória
    pdf_buffer = BytesIO()
    pisa.CreatePDF(html, dest=pdf_buffer)

    return pdf_buffer.getvalue()
# ============================================================
# PAGINA 2 - RELATORIOS E GRAFICOS
# ============================================================
if pagina == "Relatorios e Graficos":
    st.markdown("<h1>Relatórios e Análises Visuais</h1>", unsafe_allow_html=True)

    if "resultados" not in st.session_state:
        st.warning("Nenhum cálculo encontrado. Volte à aba 'Cadastro e Cálculo' e processe os dados.")
    else:
        r = st.session_state["resultados"]

        mes_ref = r.get("mes_ref", "").strip()
        if mes_ref:
            st.markdown(f"### Mês de referência: **{mes_ref}**")

        # ============================================================
        # MÉTRICAS EM CARDS
        # ============================================================
        col1, col2, col3, col4 = st.columns(4)

        with col1:
            st.markdown('<div class="metric-card">', unsafe_allow_html=True)
            st.markdown('<div class="metric-label">Auxílio total</div>', unsafe_allow_html=True)
            st.markdown(f'<div class="metric-value">R$ {r["aux_total"]:,.2f}</div>', unsafe_allow_html=True)
            st.markdown('<div class="metric-sub">Valor informado para o mês</div>', unsafe_allow_html=True)
            st.markdown('</div>', unsafe_allow_html=True)

        with col2:
            total_pass = r["pass_sete"] + r["pass_cur"]
            st.markdown('<div class="metric-card">', unsafe_allow_html=True)
            st.markdown('<div class="metric-label">Passagens totais</div>', unsafe_allow_html=True)
            st.markdown(f'<div class="metric-value">R$ {total_pass:,.2f}</div>', unsafe_allow_html=True)
            st.markdown('<div class="metric-sub">Soma das duas rotas</div>', unsafe_allow_html=True)
            st.markdown('</div>', unsafe_allow_html=True)

        with col3:
            total_bruto = r["bruto_sete"] + r["bruto_cur"]
            st.markdown('<div class="metric-card">', unsafe_allow_html=True)
            st.markdown('<div class="metric-label">Bruto total</div>', unsafe_allow_html=True)
            st.markdown(f'<div class="metric-value">R$ {total_bruto:,.2f}</div>', unsafe_allow_html=True)
            st.markdown('<div class="metric-sub">Antes dos 10% das passagens</div>', unsafe_allow_html=True)
            st.markdown('</div>', unsafe_allow_html=True)

        with col4:
            total_liq = r["liquido_sete"] + r["liquido_cur"]
            st.markdown('<div class="metric-card">', unsafe_allow_html=True)
            st.markdown('<div class="metric-label">Líquido total</div>', unsafe_allow_html=True)
            st.markdown(f'<div class="metric-value">R$ {total_liq:,.2f}</div>', unsafe_allow_html=True)
            st.markdown('<div class="metric-sub">Após auxílio e passagens líquidas</div>', unsafe_allow_html=True)
            st.markdown('</div>', unsafe_allow_html=True)

        st.markdown('<div class="divider"></div>', unsafe_allow_html=True)

        # ============================================================
        # DETALHAMENTO POR ROTA
        # ============================================================
        st.markdown("## Detalhamento por rota")

        # ------------------ SETE LAGOAS ------------------
        st.markdown("### Rota Sete Lagoas")
        st.markdown(f"""
        - Bruto original: R$ {r["bruto_sete"]:,.2f}  
        - 10% das passagens: R$ {r["desc10_sete"]:,.2f}  
        - Bruto ajustado: R$ {r["bruto_aj_sete"]:,.2f}  
        - Auxílio recebido: R$ {r["aux_sete"]:,.2f}  
        - Passagens totais: R$ {r["pass_sete"]:,.2f}  
        - Passagens líquidas: R$ {r["pass_liq_sete"]:,.2f}  
        - Líquido final: R$ {r["liquido_sete"]:,.2f}  
        - Mensalidade base: R$ {r["mensal_sete"]:,.2f}  
        """)

        st.markdown("#### Alunos")
        st.markdown(f"- Integrais: {r['int_sete']} pagando R$ {r['mensal_sete']:,.2f} cada.")

        if r["desc_sete"]:
            for pct, qtd in r["desc_sete"].items():
                fator = (100 - pct) / 100
                valor_ind = r["mensal_sete"] * fator
                st.markdown(f"- {qtd} alunos com {pct}% de desconto, pagando R$ {valor_ind:,.2f} cada.")
        else:
            st.markdown("- Nenhum aluno com desconto cadastrado.")

        st.markdown('<div class="divider"></div>', unsafe_allow_html=True)

        # ------------------ CURVELO ------------------
        st.markdown("### Rota Curvelo")
        st.markdown(f"""
        - Bruto original: R$ {r["bruto_cur"]:,.2f}  
        - 10% das passagens: R$ {r["desc10_cur"]:,.2f}  
        - Bruto ajustado: R$ {r["bruto_aj_cur"]:,.2f}  
        - Auxílio recebido: R$ {r["aux_cur"]:,.2f}  
        - Passagens totais: R$ {r["pass_cur"]:,.2f}  
        - Passagens líquidas: R$ {r["pass_liq_cur"]:,.2f}  
        - Líquido final: R$ {r["liquido_cur"]:,.2f}  
        - Mensalidade base: R$ {r["mensal_cur"]:,.2f}  
        """)

        st.markdown("#### Alunos")
        st.markdown(f"- Integrais: {r['int_cur']} pagando R$ {r['mensal_cur']:,.2f} cada.")

        if r["desc_cur"]:
            for pct, qtd in r["desc_cur"].items():
                fator = (100 - pct) / 100
                valor_ind = r["mensal_cur"] * fator
                st.markdown(f"- {qtd} alunos com {pct}% de desconto, pagando R$ {valor_ind:,.2f} cada.")
        else:
            st.markdown("- Nenhum aluno com desconto cadastrado.")

        st.markdown('<div class="divider"></div>', unsafe_allow_html=True)

        # ============================================================
        # GRÁFICO AUXÍLIO
        # ============================================================
        st.markdown("## Distribuição do Auxílio entre as Rotas")

        aux_data = pd.DataFrame([
            {"Rota": "Sete Lagoas", "Auxílio": r["aux_sete"]},
            {"Rota": "Curvelo", "Auxílio": r["aux_cur"]},
        ])

        aux_data["Percentual"] = aux_data["Auxílio"] / aux_data["Auxílio"].sum() * 100

        chart_aux = alt.Chart(aux_data).mark_arc(outerRadius=110).encode(
            theta="Auxílio",
            color=alt.Color("Rota", scale=alt.Scale(range=["#00e676", "#40c4ff"])),
            tooltip=[
                alt.Tooltip("Rota", title="Rota"),
                alt.Tooltip("Auxílio", title="Auxílio (R$)", format=",.2f"),
                alt.Tooltip("Percentual", title="Percentual", format=".2f")
            ]
        ).properties(width=380, height=320)

        st.altair_chart(chart_aux, use_container_width=True)

        st.markdown('<div class="divider"></div>', unsafe_allow_html=True)

        # ============================================================
        # GRÁFICO PASSAGENS
        # ============================================================
        st.markdown("## Comparação da Arrecadação de Passagens")

        pass_data = pd.DataFrame([
            {"Rota": "Sete Lagoas", "Passagens": r["pass_sete"]},
            {"Rota": "Curvelo", "Passagens": r["pass_cur"]},
        ])

        chart_pass = alt.Chart(pass_data).mark_bar(size=60).encode(
            x=alt.X("Rota", sort=None),
            y=alt.Y("Passagens", title="Valor arrecadado (R$)"),
            color=alt.Color("Rota", scale=alt.Scale(range=["#00e676", "#40c4ff"])),
            tooltip=[
                alt.Tooltip("Rota", title="Rota"),
                alt.Tooltip("Passagens", title="Passagens (R$)", format=",.2f")
            ]
        ).properties(width=420, height=320)

        st.altair_chart(chart_pass, use_container_width=True)

        st.markdown('<div class="divider"></div>', unsafe_allow_html=True)

        # ============================================================
        # GERAR PDF
        # ============================================================
        st.markdown("## Gerar Relatório em PDF")

        if st.button("Gerar PDF profissional"):
            try:
                pdf_bytes = gerar_pdf_profissional(r)
                st.success("PDF gerado com sucesso!")

                st.download_button(
                    label="Baixar PDF",
                    data=pdf_bytes,
                    file_name="relatorio_asseuf.pdf",
                    mime="application/pdf"
                )
            except Exception as e:
                st.error("Erro ao gerar o PDF. Detalhes abaixo:")
                st.exception(e)
# ============================================================
# RODAPÉ / FINALIZAÇÃO
# ============================================================
st.markdown("<div class='divider'></div>", unsafe_allow_html=True)

st.markdown(
    """
    <p style='text-align:center; font-size:12px; color:#777;'>
        Sistema ASSEUF • Desenvolvido para auxiliar no cálculo das rotas de Sete Lagoas e Curvelo<br>
        Relatórios, gráficos e PDF gerados automaticamente
    </p>
    """,
    unsafe_allow_html=True
)