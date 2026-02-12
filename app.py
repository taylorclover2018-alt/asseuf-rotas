from pathlib import Path
import streamlit as st
import io
import os
import altair as alt
import pandas as pd
import base64
import qrcode
from io import BytesIO
from weasyprint import HTML

# ============================================================
# CONFIGURAÇÃO DA PÁGINA
# ============================================================
st.set_page_config(
    page_title="Sistema de Cálculo das Rotas - ASSEUF",
    page_icon="🚌",
    layout="wide"
)

# ============================================================
# LOGO AUTOMÁTICO
# ============================================================
def carregar_logo():
    """
    Tenta carregar automaticamente o arquivo logo.png
    da mesma pasta do app.py. Se existir, exibe no topo
    e na sidebar. Se não existir, mostra um aviso.
    """
    logo_path = Path(__file__).parent / "logo.png"
    if logo_path.exists():
        st.sidebar.image(str(logo_path), width=140)
        st.image(str(logo_path), width=220)
    else:
        st.sidebar.warning("Logo não encontrada (logo.png)")
        st.warning("Logo não encontrada (logo.png)")

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
# FUNÇÕES DO SISTEMA
# ============================================================

def alunos_equivalentes(integrais: int, descontos: dict) -> float:
    """
    Calcula alunos equivalentes considerando:
    - integrais contam como 1
    - descontos (ex: 50%, 70%) contam proporcionalmente
    """
    total = integrais
    for pct, qtd in descontos.items():
        fator = (100 - pct) / 100
        total += qtd * fator
    return total

def calcular_bruto(veiculos: dict) -> float:
    """
    Soma valor * dias de todos os veículos cadastrados.
    """
    return sum(v["valor"] * v["dias"] for v in veiculos.values())

def dividir_auxilio(aux_total: float, pass_7l: float, pass_cur: float, d7: int, dC: int):
    """
    Divide o auxílio entre as rotas considerando:
    - desconto de 10% sobre a soma das passagens
    - proporcionalidade pelas diárias
    - regra 70/30 na diferença de diárias
    """
    desconto_passagens = 0.10 * (pass_7l + pass_cur)
    aux_disponivel = aux_total - desconto_passagens

    if aux_disponivel < 0:
        aux_disponivel = 0

    # Caso diárias iguais
    if d7 == dC and d7 > 0:
        total = d7 + dC
        return (
            aux_disponivel * (d7 / total),
            aux_disponivel * (dC / total)
        )

    # 7L com mais diárias
    if d7 > dC and dC > 0:
        excedente = d7 - dC
        base = min(d7, dC)
        total_base = base * 2 + excedente
        valor_diaria = aux_disponivel / total_base
        aux_7l = base * valor_diaria + excedente * (valor_diaria * 0.70)
        aux_cur = base * valor_diaria + excedente * (valor_diaria * 0.30)
        return aux_7l, aux_cur

    # Curvelo com mais diárias
    if dC > d7 and d7 > 0:
        excedente = dC - d7
        base = min(d7, dC)
        total_base = base * 2 + excedente
        valor_diaria = aux_disponivel / total_base
        aux_7l = base * valor_diaria + excedente * (valor_diaria * 0.30)
        aux_cur = base * valor_diaria + excedente * (valor_diaria * 0.70)
        return aux_7l, aux_cur

    # Caso extremo: alguma rota com 0 diárias
    return 0.0, 0.0

def gerar_qr_base64(texto: str) -> str:
    """
    Gera um QR Code em base64 para embutir no PDF.
    """
    qr = qrcode.QRCode(box_size=4, border=1)
    qr.add_data(texto)
    qr.make(fit=True)
    img = qr.make_image(fill_color="black", back_color="white")
    buf = BytesIO()
    img.save(buf, format="PNG")
    return base64.b64encode(buf.getvalue()).decode("utf-8")

def gerar_pdf_profissional(r: dict) -> bytes:
    """
    Gera um PDF profissional com:
    - cabeçalho
    - QR Code
    - tabelas de resumo
    - observações
    """
    qr_b64 = gerar_qr_base64("Relatório ASSEUF - Rotas 7L e Curvelo")

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
                <h1>ASSEUF - Relatório Mensal</h1>
                <span class="small">Sistema de Cálculo das Rotas - 7 Lagoas e Curvelo</span>
            </div>
            <div class="qr">
                <img src="data:image/png;base64,{qr_b64}" width="90">
                <div class="small">Validação do relatório</div>
            </div>
        </div>

        <h2>Resumo Financeiro</h2>
        <table>
            <tr>
                <th>Indicador</th>
                <th>Valor</th>
            </tr>
            <tr><td>Auxílio total</td><td>R$ {r["aux_total"]:,.2f}</td></tr>
            <tr><td>Auxílio 7 Lagoas</td><td>R$ {r["aux_ideal_7l"]:,.2f}</td></tr>
            <tr><td>Auxílio Curvelo</td><td>R$ {r["aux_ideal_cur"]:,.2f}</td></tr>
            <tr><td>Passagens 7 Lagoas</td><td>R$ {r["pass_7l"]:,.2f}</td></tr>
            <tr><td>Passagens Curvelo</td><td>R$ {r["pass_cur"]:,.2f}</td></tr>
            <tr><td>Custo bruto 7 Lagoas</td><td>R$ {r["bruto_7l"]:,.2f}</td></tr>
            <tr><td>Custo bruto Curvelo</td><td>R$ {r["bruto_cur"]:,.2f}</td></tr>
        </table>

        <h2>Alunos e Mensalidades</h2>
        <table>
            <tr>
                <th>Rota</th>
                <th>Alunos integrais</th>
                <th>Alunos equivalentes</th>
                <th>Mensalidade média</th>
            </tr>
            <tr>
                <td>7 Lagoas</td>
                <td>{r["int_7l"]}</td>
                <td>{r["al_eq_7l"]:,.2f}</td>
                <td>R$ {r["mensal_7l"]:,.2f}</td>
            </tr>
            <tr>
                <td>Curvelo</td>
                <td>{r["int_cur"]}</td>
                <td>{r["al_eq_cur"]:,.2f}</td>
                <td>R$ {r["mensal_cur"]:,.2f}</td>
            </tr>
        </table>

        <h3 class="section-title">Observações</h3>
        <p class="small">
            Este relatório foi gerado automaticamente pelo Sistema de Cálculo das Rotas da ASSEUF,
            considerando a metodologia de divisão do auxílio (desconto de 10% das passagens e regra 70/30
            nas diárias excedentes), bem como o cálculo de alunos equivalentes para definição de mensalidades.
        </p>
    </body>
    </html>
    """
    return HTML(string=html).write_pdf()

# ============================================================
# MENU LATERAL
# ============================================================
pagina = st.sidebar.radio(
    "Navegação",
    ["🏠 Início", "🧮 Cadastro e Cálculo", "📊 Relatórios e Gráficos"]
)

# ============================================================
# PÁGINA 1 — INÍCIO
# ============================================================
if pagina == "🏠 Início":
    st.markdown("<h1>Bem-vindo ao Sistema da ASSEUF</h1>", unsafe_allow_html=True)

    st.markdown("""
    <div class="elevated-card">
        <div class="section-title">Visão Geral</div>
        <h2>Modelo de Divisão do Auxílio entre as Rotas</h2>
        <p>
            Este sistema foi desenvolvido para garantir uma divisão <b>justa, transparente e auditável</b> 
            do auxílio financeiro entre as rotas <b>7 Lagoas</b> e <b>Curvelo</b>, refletindo o custo real 
            de operação de cada uma.
        </p>
        <div class="divider"></div>
        <h3>1. Proporcionalidade pelas Diárias Rodadas</h3>
        <p>
            A base da divisão é o número de <b>diárias rodadas</b> por cada rota no mês. 
            Meses com calendários acadêmicos diferentes entre as rotas (feriados locais, recessos, 
            semanas de prova, ajustes de calendário) são automaticamente contemplados, pois o sistema 
            considera o número real de dias em que cada rota operou.
        </p>
        <h3>2. Desconto de 10% sobre a Arrecadação de Passagens</h3>
        <p>
            Antes de dividir o auxílio, é aplicado um desconto de <b>10% sobre a soma das passagens</b> 
            arrecadadas pelas duas rotas. Isso evita que uma rota que arrecada mais em passagens 
            receba um volume desproporcional de auxílio.
        </p>
        <h3>3. Regra de Compensação 70% / 30%</h3>
        <p>
            Quando uma rota roda mais diárias que a outra, ela não recebe 100% da diferença. 
            Em vez disso, aplica-se a regra:
        </p>
        <ul>
            <li>A rota que rodou mais recebe <b>70%</b> da diária excedente;</li>
            <li>A rota que rodou menos recebe <b>30%</b> da diária excedente.</li>
        </ul>
        <p>
            Isso garante equilíbrio: reconhece o esforço operacional de quem rodou mais, 
            mas protege a outra rota de ficar desassistida.
        </p>
        <h3>4. Bruto, Líquido e Alunos Equivalentes</h3>
        <p>
            O <b>Bruto</b> é calculado a partir das diárias dos veículos. 
            O <b>Líquido</b> é obtido descontando-se o auxílio ideal e as passagens. 
            Em seguida, o valor é dividido pelos <b>alunos equivalentes</b>, 
            que consideram os descontos aplicados (50%, 70%, etc.), garantindo mensalidades proporcionais.
        </p>
        <h3>5. Benefícios da Metodologia</h3>
        <ul>
            <li><b>Justiça operacional</b>: considera diárias, passagens e diferenças entre rotas;</li>
            <li><b>Transparência</b>: todos os cálculos são claros e reproduzíveis;</li>
            <li><b>Controle mensal</b>: cada mês é independente, permitindo ajustes finos;</li>
            <li><b>Proteção financeira</b>: a regra 70/30 evita concentração injusta do auxílio.</li>
        </ul>
    </div>
    """, unsafe_allow_html=True)

# ============================================================
# PÁGINA 2 — CADASTRO E CÁLCULO
# ============================================================
if pagina == "🧮 Cadastro e Cálculo":
    st.markdown("<h1>Cadastro e Cálculo</h1>", unsafe_allow_html=True)

    colA, colB = st.columns(2)

    # ----------------------------
    # CARD 7 LAGOAS
    # ----------------------------
    with colA:
        with st.expander("🟦 Rota 7 Lagoas", expanded=False):
            st.markdown('<div class="elevated-card">', unsafe_allow_html=True)

            veic_7l = {}
            qtd_7l = st.number_input("Quantos tipos de veículos? (7L)", min_value=0, step=1, key="qtd_7l")

            for i in range(qtd_7l):
                tipo = st.text_input(f"Tipo do veículo {i+1}", key=f"t7{i}")
                valor = st.number_input(f"Valor da diária ({tipo})", min_value=0.0, step=1.0, key=f"v7{i}")
                dias = st.number_input(f"Diárias rodadas ({tipo})", min_value=0, step=1, key=f"d7{i}")
                if tipo:
                    veic_7l[tipo] = {"valor": valor, "dias": dias}

            pass_7l = st.number_input("Passagens arrecadadas (7L):", min_value=0.0, step=1.0)
            int_7l = st.number_input("Alunos integrais (7L):", min_value=0, step=1)

            desc_7l = {}
            qtd_desc_7l = st.number_input("Tipos de desconto (7L):", min_value=0, step=1)

            for i in range(qtd_desc_7l):
                pct = st.number_input(f"Desconto {i+1} (%)", min_value=0, max_value=100, step=1, key=f"p7{i}")
                qtd = st.number_input(f"Quantidade ({pct}%)", min_value=0, step=1, key=f"q7{i}")
                if qtd > 0:
                    desc_7l[pct] = qtd

            st.markdown('</div>', unsafe_allow_html=True)

    # ----------------------------
    # CARD CURVELO
    # ----------------------------
    with colB:
        with st.expander("🟩 Rota Curvelo", expanded=False):
            st.markdown('<div class="elevated-card">', unsafe_allow_html=True)

            veic_cur = {}
            qtd_cur = st.number_input("Quantos tipos de veículos? (Curvelo)", min_value=0, step=1, key="qtd_cur")

            for i in range(qtd_cur):
                tipo = st.text_input(f"Tipo do veículo {i+1}", key=f"tc{i}")
                valor = st.number_input(f"Valor da diária ({tipo})", min_value=0.0, step=1.0, key=f"vc{i}")
                dias = st.number_input(f"Diárias rodadas ({tipo})", min_value=0, step=1, key=f"dc{i}")
                if tipo:
                    veic_cur[tipo] = {"valor": valor, "dias": dias}

            pass_cur = st.number_input("Passagens arrecadadas (Curvelo):", min_value=0.0, step=1.0)
            int_cur = st.number_input("Alunos integrais (Curvelo):", min_value=0, step=1)

            desc_cur = {}
            qtd_desc_cur = st.number_input("Tipos de desconto (Curvelo):", min_value=0, step=1)

            for i in range(qtd_desc_cur):
                pct = st.number_input(f"Desconto {i+1} (%)", min_value=0, max_value=100, step=1, key=f"pc{i}")
                qtd = st.number_input(f"Quantidade ({pct}%)", min_value=0, step=1, key=f"qc{i}")
                if qtd > 0:
                    desc_cur[pct] = qtd

            st.markdown('</div>', unsafe_allow_html=True)

    # ----------------------------
    # PROCESSAMENTO
    # ----------------------------
    st.markdown('<div class="calc-card">', unsafe_allow_html=True)
    st.markdown("## ⚙️ Processar Resultados")

    aux_total = st.number_input("Auxílio total do mês:", min_value=0.0, step=1.0)

    if st.button("🔍 CALCULAR"):
        bruto_7l = calcular_bruto(veic_7l)
        bruto_cur = calcular_bruto(veic_cur)

        diarias_7l = sum(v["dias"] for v in veic_7l.values())
        diarias_cur = sum(v["dias"] for v in veic_cur.values())

        aux_ideal_7l, aux_ideal_cur = dividir_auxilio(aux_total, pass_7l, pass_cur, diarias_7l, diarias_cur)

        al_eq_7l = alunos_equivalentes(int_7l, desc_7l)
        al_eq_cur = alunos_equivalentes(int_cur, desc_cur)

        liquido_7l = bruto_7l - aux_ideal_7l - pass_7l
        liquido_cur = bruto_cur - aux_ideal_cur - pass_cur

        mensal_7l = liquido_7l / al_eq_7l if al_eq_7l > 0 else 0
        mensal_cur = liquido_cur / al_eq_cur if al_eq_cur > 0 else 0

        st.session_state["resultados"] = {
            "bruto_7l": bruto_7l,
            "bruto_cur": bruto_cur,
            "aux_ideal_7l": aux_ideal_7l,
            "aux_ideal_cur": aux_ideal_cur,
            "pass_7l": pass_7l,
            "pass_cur": pass_cur,
            "al_eq_7l": al_eq_7l,
            "al_eq_cur": al_eq_cur,
            "mensal_7l": mensal_7l,
            "mensal_cur": mensal_cur,
            "diarias_7l": diarias_7l,
            "diarias_cur": diarias_cur,
            "desc_7l": desc_7l,
            "desc_cur": desc_cur,
            "aux_total": aux_total,
            "int_7l": int_7l,
            "int_cur": int_cur
        }

        st.success("Cálculo realizado! Vá para a aba 'Relatórios e Gráficos'.")

    st.markdown('</div>', unsafe_allow_html=True)

# ============================================================
# PÁGINA 3 — RELATÓRIOS E GRÁFICOS
# ============================================================
if pagina == "📊 Relatórios e Gráficos":
    st.markdown("<h1>Relatórios e Análises Visuais</h1>", unsafe_allow_html=True)

    if "resultados" not in st.session_state:
        st.warning("Nenhum cálculo encontrado. Volte à aba 'Cadastro e Cálculo' e processe os dados.")
    else:
        r = st.session_state["resultados"]

        # ----------------------------
        # MÉTRICAS EM CARDS
        # ----------------------------
        col1, col2, col3, col4 = st.columns(4)

        with col1:
            st.markdown('<div class="metric-card">', unsafe_allow_html=True)
            st.markdown('<div class="metric-label">Auxílio total</div>', unsafe_allow_html=True)
            st.markdown(f'<div class="metric-value">R$ {r["aux_total"]:,.2f}</div>', unsafe_allow_html=True)
            st.markdown('<div class="metric-sub">Valor informado para o mês</div>', unsafe_allow_html=True)
            st.markdown('</div>', unsafe_allow_html=True)

        with col2:
            total_aux_rotas = r["aux_ideal_7l"] + r["aux_ideal_cur"]
            st.markdown('<div class="metric-card">', unsafe_allow_html=True)
            st.markdown('<div class="metric-label">Auxílio distribuído</div>', unsafe_allow_html=True)
            st.markdown(f'<div class="metric-value">R$ {total_aux_rotas:,.2f}</div>', unsafe_allow_html=True)
            st.markdown('<div class="metric-sub">Após desconto de 10% das passagens</div>', unsafe_allow_html=True)
            st.markdown('</div>', unsafe_allow_html=True)

        with col3:
            total_pass = r["pass_7l"] + r["pass_cur"]
            st.markdown('<div class="metric-card">', unsafe_allow_html=True)
            st.markdown('<div class="metric-label">Passagens totais</div>', unsafe_allow_html=True)
            st.markdown(f'<div class="metric-value">R$ {total_pass:,.2f}</div>', unsafe_allow_html=True)
            st.markdown('<div class="metric-sub">Soma das duas rotas</div>', unsafe_allow_html=True)
            st.markdown('</div>', unsafe_allow_html=True)

        with col4:
            total_bruto = r["bruto_7l"] + r["bruto_cur"]
            st.markdown('<div class="metric-card">', unsafe_allow_html=True)
            st.markdown('<div class="metric-label">Custo bruto total</div>', unsafe_allow_html=True)
            st.markdown(f'<div class="metric-value">R$ {total_bruto:,.2f}</div>', unsafe_allow_html=True)
            st.markdown('<div class="metric-sub">Soma dos custos das duas rotas</div>', unsafe_allow_html=True)
            st.markdown('</div>', unsafe_allow_html=True)

        st.markdown('<div class="divider"></div>', unsafe_allow_html=True)

        # ----------------------------
        # GRÁFICO 1 — PORCENTAGEM DO AUXÍLIO POR ROTA
        # ----------------------------
        st.markdown("### 📊 Distribuição do Auxílio entre as Rotas")

        aux_data = pd.DataFrame([
            {"Rota": "7 Lagoas", "Auxílio": r["aux_ideal_7l"]},
            {"Rota": "Curvelo", "Auxílio": r["aux_ideal_cur"]},
        ])

        aux_data["Percentual"] = aux_data["Auxílio"] / aux_data["Auxílio"].sum() * 100

        chart_aux = alt.Chart(aux_data).mark_arc(outerRadius=110).encode(
            theta="Auxílio",
            color=alt.Color("Rota", scale=alt.Scale(range=["#00e676", "#40c4ff"])),
            tooltip=[
                alt.Tooltip("Rota", title="Rota"),
                alt.Tooltip("Auxílio", title="Auxílio (R$)", format=",.2f"),
                alt.Tooltip("Percentual", title="% do auxílio", format=".2f")
            ]
        ).properties(
            width=380,
            height=320
        )

        colA, colB = st.columns(2)
        with colA:
            st.altair_chart(chart_aux, use_container_width=True)

        with colB:
            st.markdown("""
            <div class="elevated-card">
                <div class="section-title">Interpretação</div>
                <p>
                    Este gráfico mostra a <b>porcentagem do auxílio</b> que cada rota recebe após a aplicação 
                    da metodologia (desconto de 10% das passagens + regra 70/30 nas diárias excedentes).
                </p>
                <p>
                    A leitura é direta: quanto maior a fatia, maior a participação da rota no auxílio daquele mês.
                    Diferenças podem ocorrer por:
                </p>
                <ul>
                    <li>Mais diárias rodadas;</li>
                    <li>Diferenças no calendário acadêmico;</li>
                    <li>Diferenças na arrecadação de passagens.</li>
                </ul>
            </div>
            """, unsafe_allow_html=True)

        st.markdown('<div class="divider"></div>', unsafe_allow_html=True)

        # ----------------------------
        # GRÁFICO 2 — COMPARAÇÃO DAS PASSAGENS
        # ----------------------------
        st.markdown("### 💸 Comparação da Arrecadação de Passagens")

        pass_data = pd.DataFrame([
            {"Rota": "7 Lagoas", "Passagens": r["pass_7l"]},
            {"Rota": "Curvelo", "Passagens": r["pass_cur"]},
        ])

        chart_pass = alt.Chart(pass_data).mark_bar(size=60, cornerRadiusTopLeft=8, cornerRadiusTopRight=8).encode(
            x=alt.X("Rota", sort=None),
            y=alt.Y("Passagens", title="Valor arrecadado (R$)"),
            color=alt.Color("Rota", scale=alt.Scale(range=["#00e676", "#40c4ff"])),
            tooltip=[
                alt.Tooltip("Rota", title="Rota"),
                alt.Tooltip("Passagens", title="Passagens (R$)", format=",.2f")
            ]
        ).properties(
            width=420,
            height=320
        )

        colC, colD = st.columns(2)
        with colC:
            st.altair_chart(chart_pass, use_container_width=True)

        with colD:
            st.markdown("""
            <div class="elevated-card">
                <div class="section-title">Leitura das passagens</div>
                <p>
                    Aqui comparamos a arrecadação de passagens entre as duas rotas. 
                    Diferenças significativas podem indicar variações de demanda, calendário ou perfil dos alunos.
                </p>
            </div>
            """, unsafe_allow_html=True)

        st.markdown('<div class="divider"></div>', unsafe_allow_html=True)

        # ----------------------------
        # GRÁFICOS SOBRE ALUNOS
        # ----------------------------
        st.markdown("### 👥 Alunos integrais e equivalentes")

        alunos_data = pd.DataFrame([
            {"Rota": "7 Lagoas", "Tipo": "Integrais", "Quantidade": r["int_7l"]},
            {"Rota": "7 Lagoas", "Tipo": "Equivalentes", "Quantidade": r["al_eq_7l"]},
            {"Rota": "Curvelo", "Tipo": "Integrais", "Quantidade": r["int_cur"]},
            {"Rota": "Curvelo", "Tipo": "Equivalentes", "Quantidade": r["al_eq_cur"]},
        ])

        chart_alunos = alt.Chart(alunos_data).mark_bar().encode(
            x=alt.X("Rota:N", title="Rota"),
            y=alt.Y("Quantidade:Q", title="Quantidade"),
            color=alt.Color("Tipo:N", scale=alt.Scale(range=["#00e676", "#ffb300"])),
            column=alt.Column("Tipo:N", title="")
        ).properties(
            width=180,
            height=300
        )

        st.altair_chart(chart_alunos, use_container_width=True)

        st.markdown('<div class="divider"></div>', unsafe_allow_html=True)

        # ----------------------------
        # GERAR PDF PROFISSIONAL
        # ----------------------------
        st.markdown("## 📝 Gerar Relatório em PDF")

        if st.button("📄 Gerar PDF profissional"):
            pdf_bytes = gerar_pdf_profissional(r)
            st.success("PDF gerado com sucesso! Use o botão abaixo para baixar.")

            st.download_button(
                label="⬇️ Baixar PDF",
                data=pdf_bytes,
                file_name="relatorio_asseuf.pdf",
                mime="application/pdf"
            )

        st.markdown("""
        <div class="elevated-card">
            <div class="section-title">Fim do relatório</div>
            <p>
                Utilize os gráficos, métricas e o PDF profissional para auditoria,
                prestação de contas e análise financeira das rotas.
            </p>
        </div>
        """, unsafe_allow_html=True)