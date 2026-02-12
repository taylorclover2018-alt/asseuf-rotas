from pathlib import Path
import streamlit as st
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

    <div class="divider"></div>

    <h3>2. Desconto de 10% sobre as Passagens (Nova Regra)</h3>
    <p>
        Cada rota contribui com <b>10% do valor arrecadado em passagens</b>.
        Esse desconto é aplicado <b>individualmente</b> em cada rota, e não no total combinado.
    </p>

    <ul>
        <li>O desconto é subtraído do <b>bruto da própria rota</b>;</li>
        <li>O auxílio <b>não perde valor</b> — ele é dividido normalmente;</li>
        <li>As passagens líquidas são calculadas como:<br>
            <b>Passagens totais da rota – 10% da própria rota</b>;</li>
        <li>O líquido final considera esse ajuste antes da divisão pelos alunos.</li>
    </ul>

    <p>
        Essa regra torna o sistema mais equilibrado, justo e proporcional à arrecadação real de cada rota.
    </p>

    <div class="divider"></div>

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

    <div class="divider"></div>

    <h3>4. Bruto, Líquido e Alunos Equivalentes</h3>
    <p>
        O <b>Bruto</b> é calculado a partir das diárias dos veículos.
        O <b>Bruto Ajustado</b> é obtido após descontar os 10% das passagens.
        O <b>Líquido</b> é calculado descontando-se o auxílio e as passagens líquidas.
    </p>

    <p>
        Em seguida, o valor é dividido pelos <b>alunos equivalentes</b>, que consideram os descontos
        aplicados (50%, 70%, etc.), garantindo mensalidades proporcionais.
    </p>

    <div class="divider"></div>

    <h3>5. Benefícios da Metodologia</h3>
    <ul>
        <li><b>Justiça operacional</b>: considera diárias, passagens e diferenças entre rotas;</li>
        <li><b>Transparência</b>: todos os cálculos são claros e reproduzíveis;</li>
        <li><b>Controle mensal</b>: cada mês é independente, permitindo ajustes finos;</li>
        <li><b>Proteção financeira</b>: a regra 70/30 evita concentração injusta do auxílio;</li>
        <li><b>Equilíbrio</b>: os 10% tornam a divisão mais proporcional à arrecadação real.</li>
    </ul>
</div>
""", unsafe_allow_html=True)
# ============================================================
# PÁGINA 2 — CADASTRO E CÁLCULO
# ============================================================
if pagina == "🧮 Cadastro e Cálculo":
    st.markdown("<h1>Cadastro e Cálculo</h1>", unsafe_allow_html=True)

    st.markdown('<div class="elevated-card">', unsafe_allow_html=True)
    mes_ref = st.text_input("Mês de referência do fechamento (ex: Março/2025):")
    st.markdown('</div>', unsafe_allow_html=True)

    # ----------------------------
    # ROTA SETE LAGOAS
    # ----------------------------
    with st.expander("🟦 Rota Sete Lagoas", expanded=False):
        st.markdown('<div class="elevated-card">', unsafe_allow_html=True)

        veic_sete = {}
        qtd_sete = st.number_input("Quantos tipos de veículos? (Sete Lagoas)", min_value=0, step=1, key="qtd_sete")

        for i in range(qtd_sete):
            tipo = st.text_input(f"Tipo do veículo {i+1} (Sete Lagoas)", key=f"tsete{i}")
            valor = st.number_input(f"Valor da diária ({tipo})", min_value=0.0, step=1.0, key=f"vsete{i}")
            dias = st.number_input(f"Diárias rodadas ({tipo})", min_value=0, step=1, key=f"dsete{i}")
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

    # ----------------------------
    # ROTA CURVELO
    # ----------------------------
    with st.expander("🟩 Rota Curvelo", expanded=False):
        st.markdown('<div class="elevated-card">', unsafe_allow_html=True)

        veic_cur = {}
        qtd_cur = st.number_input("Quantos tipos de veículos? (Curvelo)", min_value=0, step=1, key="qtd_cur")

        for i in range(qtd_cur):
            tipo = st.text_input(f"Tipo do veículo {i+1} (Curvelo)", key=f"tcur{i}")
            valor = st.number_input(f"Valor da diária ({tipo})", min_value=0.0, step=1.0, key=f"vcur{i}")
            dias = st.number_input(f"Diárias rodadas ({tipo})", min_value=0, step=1, key=f"dcur{i}")
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

    # ----------------------------
    # PROCESSAMENTO
    # ----------------------------
    st.markdown('<div class="calc-card">', unsafe_allow_html=True)
    st.markdown("## ⚙️ Processar Resultados")

    aux_total = st.number_input("Auxílio total do mês:", min_value=0.0, step=1.0)

    if st.button("🔍 CALCULAR"):
        # BRUTOS ORIGINAIS
        bruto_sete = calcular_bruto(veic_sete)
        bruto_cur = calcular_bruto(veic_cur)

        # DESCONTO 10% DAS PASSAGENS
        desc10_sete = calcular_desconto_passagens(pass_sete)
        desc10_cur = calcular_desconto_passagens(pass_cur)

        # BRUTOS AJUSTADOS
        bruto_aj_sete = bruto_sete - desc10_sete
        bruto_aj_cur = bruto_cur - desc10_cur

        # PASSAGENS LÍQUIDAS
        pass_liq_sete = pass_sete - desc10_sete
        pass_liq_cur = pass_cur - desc10_cur

        # DIÁRIAS
        diarias_sete = sum(v["dias"] for v in veic_sete.values())
        diarias_cur = sum(v["dias"] for v in veic_cur.values())

        # DIVISÃO DO AUXÍLIO
        aux_sete, aux_cur = dividir_auxilio(aux_total, diarias_sete, diarias_cur)

        # ALUNOS EQUIVALENTES
        al_eq_sete = alunos_equivalentes(int_sete, desc_sete)
        al_eq_cur = alunos_equivalentes(int_cur, desc_cur)

        # LÍQUIDO FINAL
        liquido_sete = bruto_aj_sete - aux_sete - pass_liq_sete
        liquido_cur = bruto_aj_cur - aux_cur - pass_liq_cur

        # MENSALIDADES
        mensal_sete = liquido_sete / al_eq_sete if al_eq_sete > 0 else 0
        mensal_cur = liquido_cur / al_eq_cur if al_eq_cur > 0 else 0

        # SALVAR RESULTADOS
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

        mes_ref = r.get("mes_ref", "").strip()
        if mes_ref:
            st.markdown(f"### 📅 Mês de referência: **{mes_ref}**")

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

        # ----------------------------
        # DETALHAMENTO POR ROTA
        # ----------------------------
        st.markdown("## 📘 Detalhamento por rota")

        # SETE LAGOAS
        st.markdown("### 🟦 Rota Sete Lagoas")
        st.markdown(f"""
        - **Bruto original:** R$ {r["bruto_sete"]:,.2f}  
        - **10% das passagens:** R$ {r["desc10_sete"]:,.2f}  
        - **Bruto ajustado:** R$ {r["bruto_aj_sete"]:,.2f}  
        - **Auxílio recebido:** R$ {r["aux_sete"]:,.2f}  
        - **Passagens totais:** R$ {r["pass_sete"]:,.2f}  
        - **Passagens líquidas:** R$ {r["pass_liq_sete"]:,.2f}  
        - **Líquido final:** R$ {r["liquido_sete"]:,.2f}  
        - **Mensalidade base:** R$ {r["mensal_sete"]:,.2f}  
        """)

        st.markdown("#### 👥 Alunos")
        st.markdown(f"- **Integrais:** {r['int_sete']} pagando **R$ {r['mensal_sete']:,.2f}** cada.")

        if r["desc_sete"]:
            for pct, qtd in r["desc_sete"].items():
                fator = (100 - pct) / 100
                valor_ind = r["mensal_sete"] * fator
                st.markdown(f"- **{qtd} alunos com {pct}% de desconto**, pagando **R$ {valor_ind:,.2f}** cada.")
        else:
            st.markdown("- Nenhum aluno com desconto cadastrado.")

        st.markdown('<div class="divider"></div>', unsafe_allow_html=True)

        # CURVELO
        st.markdown("### 🟩 Rota Curvelo")
        st.markdown(f"""
        - **Bruto original:** R$ {r["bruto_cur"]:,.2f}  
        - **10% das passagens:** R$ {r["desc10_cur"]:,.2f}  
        - **Bruto ajustado:** R$ {r["bruto_aj_cur"]:,.2f}  
        - **Auxílio recebido:** R$ {r["aux_cur"]:,.2f}  
        - **Passagens totais:** R$ {r["pass_cur"]:,.2f}  
        - **Passagens líquidas:** R$ {r["pass_liq_cur"]:,.2f}  
        - **Líquido final:** R$ {r["liquido_cur"]:,.2f}  
        - **Mensalidade base:** R$ {r["mensal_cur"]:,.2f}  
        """)

        st.markdown("#### 👥 Alunos")
        st.markdown(f"- **Integrais:** {r['int_cur']} pagando **R$ {r['mensal_cur']:,.2f}** cada.")

        if r["desc_cur"]:
            for pct, qtd in r["desc_cur"].items():
                fator = (100 - pct) / 100
                valor_ind = r["mensal_cur"] * fator
                st.markdown(f"- **{qtd} alunos com {pct}% de desconto**, pagando **R$ {valor_ind:,.2f}** cada.")
        else:
            st.markdown("- Nenhum aluno com desconto cadastrado.")

        st.markdown('<div class="divider"></div>', unsafe_allow_html=True)

        # ----------------------------
        # GRÁFICO 1 — AUXÍLIO
        # ----------------------------
        st.markdown("## 📊 Distribuição do Auxílio entre as Rotas")

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
                alt.Tooltip("Percentual", title="% do auxílio", format=".2f")
            ]
        ).properties(width=380, height=320)

        colA, colB = st.columns(2)
        with colA:
            st.altair_chart(chart_aux, use_container_width=True)

        with colB:
            st.markdown("""
            <div class="elevated-card">
                <div class="section-title">Interpretação</div>
                <p>
                    Este gráfico mostra a <b>porcentagem do auxílio</b> que cada rota recebe após a aplicação 
                    da metodologia (10% das passagens + regra 70/30 nas diárias excedentes).
                </p>
            </div>
            """, unsafe_allow_html=True)

        st.markdown('<div class="divider"></div>', unsafe_allow_html=True)

        # ----------------------------
        # GRÁFICO 2 — PASSAGENS
        # ----------------------------
        st.markdown("## 💸 Comparação da Arrecadação de Passagens")

        pass_data = pd.DataFrame([
            {"Rota": "Sete Lagoas", "Passagens": r["pass_sete"]},
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
        ).properties(width=420, height=320)

        st.altair_chart(chart_pass, use_container_width=True)

        st.markdown('<div class="divider"></div>', unsafe_allow_html=True)

        # ----------------------------
        # BOTÃO PARA PDF
        # ----------------------------
        st.markdown("## 📝 Gerar Relatório em PDF")

        if st.button("📄 Gerar PDF profissional"):
            from_part5_pdf = gerar_pdf_profissional(r)
            st.success("PDF gerado com sucesso! Use o botão abaixo para baixar.")

            st.download_button(
                label="⬇️ Baixar PDF",
                data=from_part5_pdf,
                file_name="relatorio_asseuf.pdf",
                mime="application/pdf"
            )

#