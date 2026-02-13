from pathlib import Path
import streamlit as st
import altair as alt
import pandas as pd
import base64
import qrcode
from io import BytesIO
from weasyprint import HTML

# ============================================================
# CONFIGURACAO DA PAGINA
# ============================================================
st.set_page_config(
    page_title="Sistema de Calculo das Rotas - ASSEUF",
    page_icon="bus",
    layout="wide"
)

# ============================================================
# LOGO AUTOMATICO
# ============================================================
def carregar_logo():
    logo_path = Path(__file__).parent / "logo.png"
    if logo_path.exists():
        st.sidebar.image(str(logo_path), width=140)
        st.image(str(logo_path), width=220)
    else:
        st.sidebar.warning("Logo nao encontrada (logo.png)")
        st.warning("Logo nao encontrada (logo.png)")

carregar_logo()

# ============================================================
# CSS PREMIUM + FONTES
# ============================================================
st.markdown("""
    <style>
        @import url('https://fonts.googleapis.com/css2?family=Poppins:wght@300;400;600;700&family=Space+Grotesk:wght@400;600&display=swap');

        html, body, [class*="css"]  {
            font-family: 'Poppins', sans-serif;
        }

        body {
            background-color: #02040A;
        }
        .main {
            background: radial-gradient(circle at top, #10152A 0, #02040A 55%);
            color: #f5f5f5;
        }
        h1, h2, h3, h4, h5 {
            font-family: 'Space Grotesk', sans-serif;
            letter-spacing: 0.03em;
            color: #00e676 !important;
        }
        .sidebar .sidebar-content {
            background: linear-gradient(180deg, #050814, #02040A) !important;
        }
        .elevated-card {
            background: linear-gradient(145deg, #0b0f1c, #050814);
            padding: 20px;
            border-radius: 16px;
            box-shadow: 0px 0px 18px rgba(0,0,0,0.6);
            margin-bottom: 20px;
            border: 1px solid rgba(0,230,118,0.15);
        }
        .calc-card {
            background: radial-gradient(circle at top left, #10152A, #050814);
            padding: 25px;
            border-radius: 18px;
            box-shadow: 0px 0px 22px rgba(0,0,0,0.7);
            margin-top: 30px;
            border: 1px solid rgba(0,230,118,0.25);
        }
        .stButton>button {
            background: linear-gradient(135deg, #00e676, #00b248);
            color: #02040A;
            border-radius: 999px;
            font-weight: 700;
            padding: 10px 26px;
            border: none;
            box-shadow: 0px 0px 12px rgba(0,230,118,0.5);
        }
        .stButton>button:hover {
            background: linear-gradient(135deg, #00b248, #00e676);
            color: white;
            box-shadow: 0px 0px 18px rgba(0,230,118,0.8);
        }
        .metric-card {
            background: linear-gradient(145deg, #0b0f1c, #050814);
            padding: 18px 20px;
            border-radius: 14px;
            border: 1px solid rgba(255,255,255,0.06);
            box-shadow: 0px 0px 16px rgba(0,0,0,0.6);
        }
        .metric-label {
            font-size: 0.8rem;
            text-transform: uppercase;
            letter-spacing: 0.08em;
            color: #9e9e9e;
        }
        .metric-value {
            font-size: 1.4rem;
            font-weight: 700;
            color: #ffffff;
        }
        .metric-sub {
            font-size: 0.85rem;
            color: #bdbdbd;
        }
        .section-title {
            font-size: 1.1rem;
            font-weight: 600;
            text-transform: uppercase;
            letter-spacing: 0.12em;
            color: #9e9e9e;
            margin-top: 10px;
        }
        .divider {
            height: 1px;
            background: linear-gradient(90deg, transparent, #00e676, transparent);
            margin: 18px 0;
        }
        ul {
            margin-left: 18px;
        }
    </style>
""", unsafe_allow_html=True)

# ============================================================
# FUNCOES DO SISTEMA
# ============================================================
def alunos_equivalentes(integrais: int, descontos: dict) -> float:
    total = integrais
    for pct, qtd in descontos.items():
        fator = (100 - pct) / 100
        total += qtd * fator
    return total

def calcular_bruto(veiculos: dict) -> float:
    return sum(v["valor"] * v["dias"] for v in veiculos.values())

def calcular_desconto_passagens(passagens: float) -> float:
    return passagens * 0.10

def dividir_auxilio(aux_total: float, d_sete: int, d_cur: int):
    if d_sete == 0 and d_cur == 0:
        return 0.0, 0.0

    if d_sete == d_cur:
        total = d_sete + d_cur
        return (
            aux_total * (d_sete / total),
            aux_total * (d_cur / total)
        )

    if d_sete > d_cur:
        excedente = d_sete - d_cur
        base = d_cur
        total_base = base * 2 + excedente
        valor_diaria = aux_total / total_base
        aux_sete = base * valor_diaria + excedente * (valor_diaria * 0.70)
        aux_cur = base * valor_diaria + excedente * (valor_diaria * 0.30)
        return aux_sete, aux_cur

    if d_cur > d_sete:
        excedente = d_cur - d_sete
        base = d_sete
        total_base = base * 2 + excedente
        valor_diaria = aux_total / total_base
        aux_sete = base * valor_diaria + excedente * (valor_diaria * 0.30)
        aux_cur = base * valor_diaria + excedente * (valor_diaria * 0.70)
        return aux_sete, aux_cur

    return 0.0, 0.0

def gerar_qr_base64(texto: str) -> str:
    qr = qrcode.QRCode(box_size=4, border=1)
    qr.add_data(texto)
    qr.make(fit=True)
    img = qr.make_image(fill_color="black", back_color="white")
    buf = BytesIO()
    img.save(buf, format="PNG")
    return base64.b64encode(buf.getvalue()).decode("utf-8")

def montar_linhas_alunos_html(nome_rota: str, int_qtd: int, mensal_base: float, desc_dict: dict) -> str:
    linhas = ""
    if int_qtd > 0:
        total_int = mensal_base * int_qtd
        linhas += f"""
        <tr>
            <td>{nome_rota}</td>
            <td>Integrais</td>
            <td>{int_qtd}</td>
            <td>R$ {mensal_base:,.2f}</td>
            <td>R$ {total_int:,.2f}</td>
        </tr>
        """
    for pct, qtd in desc_dict.items():
        if qtd > 0:
            fator = (100 - pct) / 100
            valor_ind = mensal_base * fator
            total = valor_ind * qtd
            linhas += f"""
            <tr>
                <td>{nome_rota}</td>
                <td>Desconto {pct}%</td>
                <td>{qtd}</td>
                <td>R$ {valor_ind:,.2f}</td>
                <td>R$ {total:,.2f}</td>
            </tr>
            """
    return linhas
# ============================================================
# MENU LATERAL
# ============================================================
pagina = st.sidebar.radio(
    "Navegacao",
    ["Inicio", "Cadastro e Calculo", "Relatorios e Graficos"]
)

# ============================================================
# PAGINA 1 - INICIO
# ============================================================
if pagina == "Inicio":
    st.markdown("<h1>Bem-vindo ao Sistema da ASSEUF</h1>", unsafe_allow_html=True)

    st.markdown("""
<div class="elevated-card">
<div class="section-title">Visao Geral</div>
<h2>Modelo de Divisao do Auxilio entre as Rotas</h2>

<p>
Este sistema foi desenvolvido para garantir uma divisao justa, transparente e auditavel
do auxilio financeiro entre as rotas 7 Lagoas e Curvelo, refletindo o custo real
de operacao de cada uma.
</p>

<div class="divider"></div>

<h3>1. Proporcionalidade pelas Diarias Rodadas</h3>
<p>
A base da divisao e o numero de diarias rodadas por cada rota no mes.
Meses com calendarios academicos diferentes entre as rotas sao automaticamente contemplados.
</p>

<div class="divider"></div>

<h3>2. Desconto de 10% sobre as Passagens</h3>
<p>
Cada rota contribui com 10% do valor arrecadado em passagens.
Esse desconto e aplicado individualmente em cada rota.
</p>

<ul>
<li>O desconto e subtraido do bruto da propria rota;</li>
<li>O auxilio nao perde valor;</li>
<li>As passagens liquidas sao: total da rota menos 10%;</li>
<li>O liquido final considera esse ajuste.</li>
</ul>

<div class="divider"></div>

<h3>3. Regra de Compensacao 70/30</h3>
<p>
Quando uma rota roda mais diarias que a outra:
</p>

<ul>
<li>A rota que rodou mais recebe 70% da diaria excedente;</li>
<li>A rota que rodou menos recebe 30%.</li>
</ul>

<div class="divider"></div>

<h3>4. Bruto, Liquido e Alunos Equivalentes</h3>
<p>
O bruto vem das diarias. O bruto ajustado desconta os 10%.
O liquido desconta auxilio e passagens liquidas.
</p>

<p>
O valor final e dividido pelos alunos equivalentes.
</p>

<div class="divider"></div>

<h3>5. Beneficios</h3>
<ul>
<li>Justica operacional;</li>
<li>Transparencia total;</li>
<li>Controle mensal;</li>
<li>Protecao financeira;</li>
<li>Equilibrio entre rotas.</li>
</ul>

</div>
""", unsafe_allow_html=True)

# ============================================================
# PAGINA 2 - CADASTRO E CALCULO
# ============================================================
if pagina == "Cadastro e Calculo":
    st.markdown("<h1>Cadastro e Calculo</h1>", unsafe_allow_html=True)

    st.markdown('<div class="elevated-card">', unsafe_allow_html=True)
    mes_ref = st.text_input("Mes de referencia do fechamento (ex: Marco/2025):")
    st.markdown('</div>', unsafe_allow_html=True)

    # ROTA SETE LAGOAS
    with st.expander("Rota Sete Lagoas", expanded=False):
        st.markdown('<div class="elevated-card">', unsafe_allow_html=True)

        veic_sete = {}
        qtd_sete = st.number_input("Quantos tipos de veiculos? (Sete Lagoas)", min_value=0, step=1, key="qtd_sete")

        for i in range(qtd_sete):
            tipo = st.text_input(f"Tipo do veiculo {i+1} (Sete Lagoas)", key=f"tsete{i}")
            valor = st.number_input(f"Valor da diaria ({tipo})", min_value=0.0, step=1.0, key=f"vsete{i}")
            dias = st.number_input(f"Diarias rodadas ({tipo})", min_value=0, step=1, key=f"dsete{i}")
            if tipo:
                veic_sete[tipo] = {"valor": valor, "dias": dias}

        pass_sete = st.number_input("Passagens arrecadadas (Sete Lagoas):", min_value=0.0, step=1.0)
        int_sete = st.number_input("Alunos integrais (Sete Lagoas):", min_value=0, step=1)

        desc_sete = {}
        qtd_desc_sete = st.number_input("Tipos de desconto (Sete Lagoas):", min_value=0, step=1)

        for i in range(qtd_desc_sete):
            pct = st.number_input(f"Desconto {i+1} (%) - Sete Lagoas", min_value=0, max_value=100, step=1, key=f"psete{i}")
            qtd = st.number_input(f"Quantidade de alunos com {pct}% (Sete Lagoas)", min_value=0, step=1, key=f"qsete{i}")
            if qtd > 0:
                desc_sete[pct] = qtd

        st.markdown('</div>', unsafe_allow_html=True)
    # ROTA CURVELO
    with st.expander("Rota Curvelo", expanded=False):
        st.markdown('<div class="elevated-card">', unsafe_allow_html=True)

        veic_cur = {}
        qtd_cur = st.number_input("Quantos tipos de veiculos? (Curvelo)", min_value=0, step=1, key="qtd_cur")

        for i in range(qtd_cur):
            tipo = st.text_input(f"Tipo do veiculo {i+1} (Curvelo)", key=f"tcur{i}")
            valor = st.number_input(f"Valor da diaria ({tipo})", min_value=0.0, step=1.0, key=f"vcur{i}")
            dias = st.number_input(f"Diarias rodadas ({tipo})", min_value=0, step=1, key=f"dcur{i}")
            if tipo:
                veic_cur[tipo] = {"valor": valor, "dias": dias}

        pass_cur = st.number_input("Passagens arrecadadas (Curvelo):", min_value=0.0, step=1.0)
        int_cur = st.number_input("Alunos integrais (Curvelo):", min_value=0, step=1)

        desc_cur = {}
        qtd_desc_cur = st.number_input("Tipos de desconto (Curvelo):", min_value=0, step=1)

        for i in range(qtd_desc_cur):
            pct = st.number_input(f"Desconto {i+1} (%) - Curvelo", min_value=0, max_value=100, step=1, key=f"pcur{i}")
            qtd = st.number_input(f"Quantidade de alunos com {pct}% (Curvelo)", min_value=0, step=1, key=f"qcur{i}")
            if qtd > 0:
                desc_cur[pct] = qtd

        st.markdown('</div>', unsafe_allow_html=True)

    # PROCESSAMENTO
    st.markdown('<div class="calc-card">', unsafe_allow_html=True)
    st.markdown("## Processar Resultados")

    aux_total = st.number_input("Auxilio total do mes:", min_value=0.0, step=1.0)

    if st.button("Calcular"):
        bruto_sete = calcular_bruto(veic_sete)
        bruto_cur = calcular_bruto(veic_cur)

        desc10_sete = calcular_desconto_passagens(pass_sete)
        desc10_cur = calcular_desconto_passagens(pass_cur)

        bruto_aj_sete = bruto_sete - desc10_sete
        bruto_aj_cur = bruto_cur - desc10_cur

        pass_liq_sete = pass_sete - desc10_sete
        pass_liq_cur = pass_cur - desc10_cur

        diarias_sete = sum(v["dias"] for v in veic_sete.values())
        diarias_cur = sum(v["dias"] for v in veic_cur.values())

        aux_sete, aux_cur = dividir_auxilio(aux_total, diarias_sete, diarias_cur)

        al_eq_sete = alunos_equivalentes(int_sete, desc_sete)
        al_eq_cur = alunos_equivalentes(int_cur, desc_cur)

        liquido_sete = bruto_aj_sete - aux_sete - pass_liq_sete
        liquido_cur = bruto_aj_cur - aux_cur - pass_liq_cur

        mensal_sete = liquido_sete / al_eq_sete if al_eq_sete > 0 else 0
        mensal_cur = liquido_cur / al_eq_cur if al_eq_cur > 0 else 0
        st.session_state["resultados"] = {
            "mes_ref": mes_ref,
            "bruto_sete": bruto_sete,
            "bruto_cur": bruto_cur,
            "desc10_sete": desc10_sete,
            "desc10_cur": desc10_cur,
            "bruto_aj_sete": bruto_aj_sete,
            "bruto_aj_cur": bruto_aj_cur,
            "pass_sete": pass_sete,
            "pass_cur": pass_cur,
            "pass_liq_sete": pass_liq_sete,
            "pass_liq_cur": pass_liq_cur,
            "aux_sete": aux_sete,
            "aux_cur": aux_cur,
            "liquido_sete": liquido_sete,
            "liquido_cur": liquido_cur,
            "mensal_sete": mensal_sete,
            "mensal_cur": mensal_cur,
            "diarias_sete": diarias_sete,
            "diarias_cur": diarias_cur,
            "desc_sete": desc_sete,
            "desc_cur": desc_cur,
            "aux_total": aux_total,
            "int_sete": int_sete,
            "int_cur": int_cur
        }

        st.success("Calculo realizado! Va para a aba 'Relatorios e Graficos'.")

    st.markdown('</div>', unsafe_allow_html=True)

# ============================================================
# PAGINA 3 - RELATORIOS E GRAFICOS
# ============================================================
if pagina == "Relatorios e Graficos":
    st.markdown("<h1>Relatorios e Analises Visuais</h1>", unsafe_allow_html=True)

    if "resultados" not in st.session_state:
        st.warning("Nenhum calculo encontrado. Volte a aba 'Cadastro e Calculo' e processe os dados.")
    else:
        r = st.session_state["resultados"]

        mes_ref = r.get("mes_ref", "").strip()
        if mes_ref:
            st.markdown(f"### Mes de referencia: **{mes_ref}**")

        # METRICAS EM CARDS
        col1, col2, col3, col4 = st.columns(4)

        with col1:
            st.markdown('<div class="metric-card">', unsafe_allow_html=True)
            st.markdown('<div class="metric-label">Auxilio total</div>', unsafe_allow_html=True)
            st.markdown(f'<div class="metric-value">R$ {r["aux_total"]:,.2f}</div>', unsafe_allow_html=True)
            st.markdown('<div class="metric-sub">Valor informado para o mes</div>', unsafe_allow_html=True)
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
            st.markdown('<div class="metric-label">Liquido total</div>', unsafe_allow_html=True)
            st.markdown(f'<div class="metric-value">R$ {total_liq:,.2f}</div>', unsafe_allow_html=True)
            st.markdown('<div class="metric-sub">Apos auxilio e passagens liquidas</div>', unsafe_allow_html=True)
            st.markdown('</div>', unsafe_allow_html=True)

        st.markdown('<div class="divider"></div>', unsafe_allow_html=True)

        # DETALHAMENTO POR ROTA
        st.markdown("## Detalhamento por rota")

        # SETE LAGOAS
        st.markdown("### Rota Sete Lagoas")
        st.markdown(f"""
        - Bruto original: R$ {r["bruto_sete"]:,.2f}  
        - 10% das passagens: R$ {r["desc10_sete"]:,.2f}  
        - Bruto ajustado: R$ {r["bruto_aj_sete"]:,.2f}  
        - Auxilio recebido: R$ {r["aux_sete"]:,.2f}  
        - Passagens totais: R$ {r["pass_sete"]:,.2f}  
        - Passagens liquidas: R$ {r["pass_liq_sete"]:,.2f}  
        - Liquido final: R$ {r["liquido_sete"]:,.2f}  
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

        # CURVELO
        st.markdown("### Rota Curvelo")
        st.markdown(f"""
        - Bruto original: R$ {r["bruto_cur"]:,.2f}  
        - 10% das passagens: R$ {r["desc10_cur"]:,.2f}  
        - Bruto ajustado: R$ {r["bruto_aj_cur"]:,.2f}  
        - Auxilio recebido: R$ {r["aux_cur"]:,.2f}  
        - Passagens totais: R$ {r["pass_cur"]:,.2f}  
        - Passagens liquidas: R$ {r["pass_liq_cur"]:,.2f}  
        - Liquido final: R$ {r["liquido_cur"]:,.2f}  
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

        # GRAFICO AUXILIO
        st.markdown("## Distribuicao do Auxilio entre as Rotas")

        aux_data = pd.DataFrame([
            {"Rota": "Sete Lagoas", "Auxilio": r["aux_sete"]},
            {"Rota": "Curvelo", "Auxilio": r["aux_cur"]},
        ])

        aux_data["Percentual"] = aux_data["Auxilio"] / aux_data["Auxilio"].sum() * 100

        chart_aux = alt.Chart(aux_data).mark_arc(outerRadius=110).encode(
            theta="Auxilio",
            color=alt.Color("Rota", scale=alt.Scale(range=["#00e676", "#40c4ff"])),
            tooltip=[
                alt.Tooltip("Rota", title="Rota"),
                alt.Tooltip("Auxilio", title="Auxilio (R$)", format=",.2f"),
                alt.Tooltip("Percentual", title="Percentual", format=".2f")
            ]
        ).properties(width=380, height=320)

        st.altair_chart(chart_aux, use_container_width=True)

        st.markdown('<div class="divider"></div>', unsafe_allow_html=True)

        # GRAFICO PASSAGENS
        st.markdown("## Comparacao da Arrecadacao de Passagens")

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

        # PDF
        st.markdown("## Gerar Relatorio em PDF")

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
# FUNCAO PARA GERAR PDF PROFISSIONAL
# ============================================================
def gerar_pdf_profissional(r: dict) -> bytes:
    qr_b64 = gerar_qr_base64("Relatorio ASSEUF - Rotas Sete Lagoas e Curvelo")
    mes_ref = r.get("mes_ref", "").strip()
    if not mes_ref:
        mes_ref = "Mes nao informado"

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
            .header {{
                display: flex;
                justify-content: space-between;
                align-items: center;
                border-bottom: 2px solid #00695c;
                padding-bottom: 10px;
                margin-bottom: 20px;
            }}
            .logo-title {{
                display: flex;
                flex-direction: column;
            }}
            .qr {{
                text-align: right;
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
            .section-title {{
                margin-top: 25px;
                font-size: 16px;
                font-weight: bold;
                color: #004d40;
            }}
            .small {{
                font-size: 11px;
                color: #555;
            }}
        </style>
    </head>

    <body>
        <div class="header">
            <div class="logo-title">
                <h1>ASSEUF - Relatorio Mensal</h1>
                <span class="small">Sistema de Calculo das Rotas - Sete Lagoas e Curvelo</span>
                <span class="small">Mes de referencia: {mes_ref}</span>
            </div>
            <div class="qr">
                <img src="data:image/png;base64,{qr_b64}" width="90">
                <div class="small">Validacao do relatorio</div>
            </div>
        </div>

        <h2>Resumo Financeiro</h2>
        <table>
            <tr>
                <th>Indicador</th>
                <th>Sete Lagoas</th>
                <th>Curvelo</th>
            </tr>

            <tr><td>Bruto original</td>
                <td>R$ {r["bruto_sete"]:,.2f}</td>
                <td>R$ {r["bruto_cur"]:,.2f}</td></tr>

            <tr><td>10% das passagens</td>
                <td>R$ {r["desc10_sete"]:,.2f}</td>
                <td>R$ {r["desc10_cur"]:,.2f}</td></tr>

            <tr><td>Bruto ajustado</td>
                <td>R$ {r["bruto_aj_sete"]:,.2f}</td>
                <td>R$ {r["bruto_aj_cur"]:,.2f}</td></tr>

            <tr><td>Auxilio recebido</td>
                <td>R$ {r["aux_sete"]:,.2f}</td>
                <td>R$ {r["aux_cur"]:,.2f}</td></tr>

            <tr><td>Passagens totais</td>
                <td>R$ {r["pass_sete"]:,.2f}</td>
                <td>R$ {r["pass_cur"]:,.2f}</td></tr>

            <tr><td>Passagens liquidas</td>
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

        <h3 class="section-title">Observacoes</h3>
        <p class="small">
            Este relatorio foi gerado automaticamente pelo Sistema de Calculo das Rotas da ASSEUF.
            A metodologia considera:
            <br>- Contribuicao obrigatoria de 10% das passagens por rota
            <br>- Bruto ajustado antes da divisao do auxilio
            <br>- Regra 70/30 nas diarias excedentes
            <br>- Calculo de mensalidades baseado no liquido final e alunos equivalentes
        </p>
    </body>
    </html>
    """

    return HTML(string=html).write_pdf()