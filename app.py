from pathlib import Path
import streamlit as st

logo_path = Path(__file__).parent / "logo.png"
st.image(str(logo_path))
import streamlit as st
import io
import os

# ============================
# CONFIGURAÇÃO DA PÁGINA
# ============================
st.set_page_config(
    page_title="Sistema de Cálculo das Rotas - ASSEUF",
    page_icon="🚌",
    layout="wide"
)

# ============================
# CSS PREMIUM
# ============================
st.markdown("""
    <style>
        body {
            background-color: #000000;
        }
        .main {
            background-color: #000000;
            color: white;
        }
        h1, h2, h3, h4, h5 {
            color: #00e676 !important;
        }
        .sidebar .sidebar-content {
            background-color: #0d0d0d !important;
        }
        .elevated-card {
            background-color: #111;
            padding: 20px;
            border-radius: 12px;
            box-shadow: 0px 0px 12px rgba(0,0,0,0.4);
            margin-bottom: 20px;
        }
        .calc-card {
            background-color: #111;
            padding: 25px;
            border-radius: 14px;
            box-shadow: 0px 0px 14px rgba(0,0,0,0.45);
            margin-top: 30px;
        }
        .stButton>button {
            background-color: #00e676;
            color: black;
            border-radius: 8px;
            font-weight: bold;
            padding: 10px 20px;
        }
        .stButton>button:hover {
            background-color: #00b248;
            color: white;
        }
    </style>
""", unsafe_allow_html=True)

# ============================
# FUNÇÕES DO SISTEMA
# ============================

def alunos_equivalentes(integrais, descontos):
    total = integrais
    for pct, qtd in descontos.items():
        fator = (100 - pct) / 100
        total += qtd * fator
    return total

def calcular_bruto(veiculos):
    return sum(v["valor"] * v["dias"] for v in veiculos.values())

def dividir_auxilio(aux_total, pass_7l, pass_cur, d7, dC):
    desconto_passagens = 0.10 * (pass_7l + pass_cur)
    aux_disponivel = aux_total - desconto_passagens

    if d7 == dC and d7 > 0:
        total = d7 + dC
        return (
            aux_disponivel * (d7 / total),
            aux_disponivel * (dC / total)
        )

    if d7 > dC and dC > 0:
        excedente = d7 - dC
        base = min(d7, dC)
        total_base = base * 2 + excedente
        valor_diaria = aux_disponivel / total_base
        aux_7l = base * valor_diaria + excedente * (valor_diaria * 0.70)
        aux_cur = base * valor_diaria + excedente * (valor_diaria * 0.30)
        return aux_7l, aux_cur

    if dC > d7 and d7 > 0:
        excedente = dC - d7
        base = min(d7, dC)
        total_base = base * 2 + excedente
        valor_diaria = aux_disponivel / total_base
        aux_7l = base * valor_diaria + excedente * (valor_diaria * 0.30)
        aux_cur = base * valor_diaria + excedente * (valor_diaria * 0.70)
        return aux_7l, aux_cur

    return 0.0, 0.0
# ============================
# NOVA FUNÇÃO DE RELATÓRIO (ATUALIZADA)
# ============================

def gerar_relatorio_texto(
    bruto_7l, bruto_cur,
    aux_ideal_7l, aux_ideal_cur,
    pass_7l, pass_cur,
    al_eq_7l, al_eq_cur,
    mensal_7l, mensal_cur,
    diarias_7l, diarias_cur,
    desc_7l, desc_cur
):
    buf = io.StringIO()
    buf.write("===== RELATÓRIO DAS ROTAS - ASSEUF =====\n\n")

    # ============================
    # ROTA 7 LAGOAS
    # ============================
    buf.write("ROTA 7 LAGOAS\n")
    buf.write(f"Bruto: R$ {bruto_7l:.2f}\n")
    buf.write(f"Auxílio ideal: R$ {aux_ideal_7l:.2f}\n")
    buf.write(f"Passagens arrecadadas: R$ {pass_7l:.2f}\n")
    buf.write(f"Alunos equivalentes: {al_eq_7l:.2f}\n\n")

    buf.write("💰 Valores por aluno (7 Lagoas):\n")
    buf.write(f"- Mensalidade integral: R$ {mensal_7l:.2f}\n")

    if desc_7l:
        buf.write("Alunos com desconto:\n")
        for pct, qtd in desc_7l.items():
            valor_desconto = mensal_7l * ((100 - pct) / 100)
            buf.write(f"- {pct}% ({qtd} alunos): R$ {valor_desconto:.2f} cada\n")
    else:
        buf.write("Nenhum aluno com desconto.\n")

    buf.write("\n\n")

    # ============================
    # ROTA CURVELO
    # ============================
    buf.write("ROTA CURVELO\n")
    buf.write(f"Bruto: R$ {bruto_cur:.2f}\n")
    buf.write(f"Auxílio ideal: R$ {aux_ideal_cur:.2f}\n")
    buf.write(f"Passagens arrecadadas: R$ {pass_cur:.2f}\n")
    buf.write(f"Alunos equivalentes: {al_eq_cur:.2f}\n\n")

    buf.write("💰 Valores por aluno (Curvelo):\n")
    buf.write(f"- Mensalidade integral: R$ {mensal_cur:.2f}\n")

    if desc_cur:
        buf.write("Alunos com desconto:\n")
        for pct, qtd in desc_cur.items():
            valor_desconto = mensal_cur * ((100 - pct) / 100)
            buf.write(f"- {pct}% ({qtd} alunos): R$ {valor_desconto:.2f} cada\n")
    else:
        buf.write("Nenhum aluno com desconto.\n")

    buf.write("\n\n")

    # ============================
    # COMPARAÇÃO
    # ============================
    buf.write("COMPARAÇÃO\n")
    buf.write(f"Diárias 7 Lagoas: {diarias_7l}\n")
    buf.write(f"Diárias Curvelo: {diarias_cur}\n")

    return buf.getvalue().encode("utf-8")

# ============================
# LOGO AUTOMÁTICO
# ============================

def carregar_logo():
    if os.path.exists("logo.png"):
        st.sidebar.image("logo.png", width=140)
        st.image("logo.png", width=180)
    else:
        st.sidebar.warning("Logo não encontrado (logo.png)")
        st.warning("Logo não encontrado (logo.png)")

carregar_logo()

# ============================
# MENU LATERAL
# ============================

pagina = st.sidebar.radio(
    "Navegação",
    ["🏠 Início", "🧮 Cadastro e Cálculo", "📊 Relatórios"]
)

# ============================
# PÁGINA 1 — INÍCIO
# ============================

if pagina == "🏠 Início":
    st.markdown("<h1>Bem-vindo ao Sistema da ASSEUF</h1>", unsafe_allow_html=True)
    st.write("""
        Sistema oficial para cálculo mensal das rotas **7 Lagoas** e **Curvelo**.
        Use o menu à esquerda para navegar.
    """)
# ============================
# PÁGINA 2 — CADASTRO E CÁLCULO
# ============================

if pagina == "🧮 Cadastro e Cálculo":
    st.markdown("<h1>Cadastro e Cálculo</h1>", unsafe_allow_html=True)

    colA, colB = st.columns(2)

    # ============================
    # CARD 7 LAGOAS
    # ============================
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

    # ============================
    # CARD CURVELO
    # ============================
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

    # ============================
    # CARD DE PROCESSAMENTO
    # ============================
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
            "desc_cur": desc_cur
        }

        st.success("Cálculo realizado! Vá para a aba 'Relatórios'.")

    st.markdown('</div>', unsafe_allow_html=True)

# ============================
# PÁGINA 3 — RELATÓRIOS
# ============================

if pagina == "📊 Relatórios":
    st.markdown("<h1>Relatórios</h1>", unsafe_allow_html=True)

    if "resultados" not in st.session_state:
        st.warning("Nenhum cálculo encontrado.")
    else:
        r = st.session_state["resultados"]

        col1, col2 = st.columns(2)

        with col1:
            st.markdown('<div class="elevated-card">', unsafe_allow_html=True)
            st.markdown("### 🟦 7 Lagoas")
            st.write(f"Bruto: R$ {r['bruto_7l']:,.2f}")
            st.write(f"Auxílio ideal: R$ {r['aux_ideal_7l']:,.2f}")
            st.write(f"Mensalidade integral: R$ {r['mensal_7l']:,.2f}")
            st.markdown('</div>', unsafe_allow_html=True)

        with col2:
            st.markdown('<div class="elevated-card">', unsafe_allow_html=True)
            st.markdown("### 🟩 Curvelo")
            st.write(f"Bruto: R$ {r['bruto_cur']:,.2f}")
            st.write(f"Auxílio ideal: R$ {r['aux_ideal_cur']:,.2f}")
            st.write(f"Mensalidade integral: R$ {r['mensal_cur']:,.2f}")
            st.markdown('</div>', unsafe_allow_html=True)

        st.markdown("### 📈 Gráfico de Mensalidades")

        st.bar_chart({
            "7 Lagoas": [r["mensal_7l"]],
            "Curvelo": [r["mensal_cur"]],
        })

        st.markdown("### 📄 Baixar Relatório")

        relatorio_bytes = gerar_relatorio_texto(
            r["bruto_7l"], r["bruto_cur"],
            r["aux_ideal_7l"], r["aux_ideal_cur"],
            r["pass_7l"], r["pass_cur"],
            r["al_eq_7l"], r["al_eq_cur"],
            r["mensal_7l"], r["mensal_cur"],
            r["diarias_7l"], r["diarias_cur"],
            r["desc_7l"], r["desc_cur"]
        )

        st.download_button(
            label="📥 Baixar relatório",
            data=relatorio_bytes,
            file_name="relatorio_rotas.txt",
            mime="text/plain"
        )