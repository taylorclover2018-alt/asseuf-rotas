from pathlib import Path
import streamlit as st
import base64
import qrcode
from io import BytesIO
from datetime import datetime
from weasyprint import HTML
import pandas as pd
import os
import altair as alt

# ============================================================
# CONFIGURAÇÃO DA PÁGINA
# ============================================================
st.set_page_config(
    page_title="Sistema de Cálculo das Rotas - ASSEUF",
    page_icon="🚌",
    layout="wide"
)

# ============================================================
# LOGO
# ============================================================
def carregar_logo():
    logo_path = Path(__file__).parent / "logo.png"
    if logo_path.exists():
        st.image(str(logo_path), width=220)
    else:
        st.warning("Logo não encontrada (logo.png)")

carregar_logo()

# ============================================================
# CSS GLOBAL
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
        .divider {
            height: 1px;
            background: linear-gradient(90deg, transparent, #00e676, transparent);
            margin: 18px 0;
        }
        .top-menu button {
            width: 100%;
        }
        .stButton>button {
            background: linear-gradient(135deg, #00e676, #00b248);
            color: #02040A;
            border-radius: 999px;
            font-weight: 700;
            padding: 8px 18px;
            border: none;
            box-shadow: 0px 0px 12px rgba(0,230,118,0.5);
            transition: all 0.3s ease;
        }
        .stButton>button:hover {
            background: linear-gradient(135deg, #00b248, #00e676);
            color: white;
            box-shadow: 0px 0px 18px rgba(0,230,118,0.8);
            transform: scale(1.02);
        }
        .stDownloadButton>button {
            background: linear-gradient(135deg, #2979ff, #1565c0) !important;
            color: white !important;
            box-shadow: 0px 0px 12px rgba(41,121,255,0.5);
        }
        .stDownloadButton>button:hover {
            background: linear-gradient(135deg, #1565c0, #0d47a1) !important;
        }
    </style>
""", unsafe_allow_html=True)

# ============================================================
# CONSTANTES E HISTÓRICO
# ============================================================
HIST_PATH = "historico_rotas.csv"

def carregar_historico():
    if os.path.exists(HIST_PATH):
        try:
            return pd.read_csv(HIST_PATH)
        except Exception:
            return pd.DataFrame()
    return pd.DataFrame()

def salvar_historico(mes_ref, rota_nome, dados):
    df = carregar_historico()
    base = {
        "mes_ref": mes_ref,
        "rota": rota_nome,
        "bruto": dados["bruto"],
        "passagens": dados["passagens"],
        "dez_porcento": dados["dez_porcento"],
        "bruto_aj_10": dados["bruto_aj_10"],
        "aux_recebido": dados["aux_recebido"],
        "pos_aux": dados["pos_aux"],
        "noventa_porcento": dados["noventa_porcento"],
        "valor_final": dados["valor_final"],
        "alunos_integrais": dados["alunos_integrais"],
        "alunos_desconto_total": dados["alunos_desconto_total"],
        "mensalidade_media": dados["mensalidade_media"],
        "veiculos": dados["veiculos_qtd"],
        "diarias": dados["diarias"],
        "data_registro": datetime.now().strftime("%d/%m/%Y %H:%M")
    }
    df = pd.concat([df, pd.DataFrame([base])], ignore_index=True)
    df.to_csv(HIST_PATH, index=False)
# ============================================================
# FUNÇÕES DE CÁLCULO
# ============================================================
def calcular_bruto(veiculos: dict) -> float:
    return sum(v["valor"] * v["dias"] for v in veiculos.values())

def calcular_peso_alunos(alunos_integrais: int, descontos: dict) -> float:
    """
    descontos: {percentual_desconto: quantidade}
    Ex: {50: 3, 30: 2}
    Internamente usamos peso, mas na interface só falamos
    em 'alunos integrais' e 'alunos com desconto'.
    """
    peso = float(alunos_integrais)
    for pct, qtd in descontos.items():
        fator = (100 - pct) / 100.0
        peso += qtd * fator
    return peso

def distribuir_auxilio_por_diarias(aux_total: float, d_sete: int, d_cur: int):
    if aux_total <= 0:
        return 0.0, 0.0
    if d_sete == 0 and d_cur == 0:
        return 0.0, 0.0
    if d_sete == 0:
        return 0.0, aux_total
    if d_cur == 0:
        return aux_total, 0.0

    if d_sete == d_cur:
        total = d_sete + d_cur
        return aux_total * d_sete / total, aux_total * d_cur / total

    if d_sete > d_cur:
        excedente = d_sete - d_cur
        base = d_cur
        total_base = base * 2 + excedente
        valor_diaria = aux_total / total_base
        aux_sete = base * valor_diaria + excedente * (valor_diaria * 0.70)
        aux_cur = base * valor_diaria + excedente * (valor_diaria * 0.30)
        return aux_sete, aux_cur

    excedente = d_cur - d_sete
    base = d_sete
    total_base = base * 2 + excedente
    valor_diaria = aux_total / total_base
    aux_sete = base * valor_diaria + excedente * (valor_diaria * 0.30)
    aux_cur = base * valor_diaria + excedente * (valor_diaria * 0.70)
    return aux_sete, aux_cur

def calcular_rota(
    veiculos: dict,
    passagens: float,
    alunos_integrais: int,
    descontos: dict,
    aux_recebido: float,
    diarias_rota: int,
):
    bruto = calcular_bruto(veiculos)
    dez_porcento = passagens * 0.10
    bruto_aj_10 = bruto - dez_porcento
    pos_aux = bruto_aj_10 - aux_recebido
    noventa_porcento = passagens * 0.90
    valor_final = pos_aux - noventa_porcento

    peso_alunos = calcular_peso_alunos(alunos_integrais, descontos)
    alunos_desconto_total = sum(descontos.values())
    mensalidade_media = valor_final / peso_alunos if peso_alunos > 0 else 0.0

    return {
        "bruto": bruto,
        "passagens": passagens,
        "dez_porcento": dez_porcento,
        "bruto_aj_10": bruto_aj_10,
        "aux_recebido": aux_recebido,
        "pos_aux": pos_aux,
        "noventa_porcento": noventa_porcento,
        "valor_final": valor_final,
        "alunos_integrais": alunos_integrais,
        "alunos_desconto_total": alunos_desconto_total,
        "mensalidade_media": mensalidade_media,
        "descontos": descontos,
        "diarias": diarias_rota,
        "veiculos_qtd": len(veiculos),
    }

# ============================================================
# QR CODE
# ============================================================
def gerar_qr_base64(texto: str) -> str:
    qr = qrcode.QRCode(box_size=4, border=1)
    qr.add_data(texto)
    qr.make(fit=True)
    img = qr.make_image(fill_color="black", back_color="white")
    buf = BytesIO()
    img.save(buf, format="PNG")
    return base64.b64encode(buf.getvalue()).decode("utf-8")
# ============================================================
# MENU SUPERIOR (OPÇÃO A)
# ============================================================
col1, col2, col3, col4 = st.columns(4)
with col1:
    btn_inicio = st.button("🏠 Início")
with col2:
    btn_calc = st.button("🧮 Cadastro e Cálculo")
with col3:
    btn_rel = st.button("📊 Relatórios")
with col4:
    btn_pdf = st.button("📄 PDF")

if "pagina" not in st.session_state:
    st.session_state["pagina"] = "inicio"

if btn_inicio:
    st.session_state["pagina"] = "inicio"
elif btn_calc:
    st.session_state["pagina"] = "calculo"
elif btn_rel:
    st.session_state["pagina"] = "relatorios"
elif btn_pdf:
    st.session_state["pagina"] = "pdf"

pagina = st.session_state["pagina"]

# ============================================================
# PÁGINA INÍCIO
# ============================================================
if pagina == "inicio":
    st.markdown("<h1>Sistema de Cálculo das Rotas - ASSEUF</h1>", unsafe_allow_html=True)

    st.markdown("""
    <div class="elevated-card">
        <h3>Visão geral da metodologia</h3>
        <div class="divider"></div>
        <p>
            Este sistema foi pensado para refletir, com o máximo de fidelidade possível,
            o custo real de operação das rotas <b>Sete Lagoas</b> e <b>Curvelo</b>.
            A ideia é transformar um cenário complexo (veículos, diárias, auxílio, passagens,
            alunos integrais e com desconto) em um cálculo claro, auditável e visualmente organizado.
        </p>
        <p>
            A lógica segue uma sequência bem definida, sempre por rota:
        </p>
        <ul>
            <li><b>1. Custo bruto:</b> soma de (valor da diária × dias rodados) de cada veículo.</li>
            <li><b>2. Desconto de 10% das passagens:</b> esse valor é abatido diretamente do bruto.</li>
            <li><b>3. Auxílio:</b> o total do auxílio do mês é dividido entre as rotas
                com base nas diárias rodadas e na regra de compensação 70/30.</li>
            <li><b>4. Abatimento do auxílio:</b> o auxílio recebido por cada rota é subtraído
                do custo já ajustado pelos 10%.</li>
            <li><b>5. Desconto dos 90% restantes das passagens:</b> o valor restante das passagens
                (90%) é abatido da própria rota.</li>
            <li><b>6. Rateio entre alunos:</b> o valor final é dividido considerando
                <b>alunos integrais</b> e <b>alunos com desconto</b>, onde cada faixa de desconto
                tem um peso proporcional.</li>
        </ul>
        <p>
            O resultado final é uma visão detalhada por rota: quanto custou, quanto foi abatido,
            quanto de auxílio entrou e qual é a mensalidade média esperada por aluno,
            respeitando os diferentes níveis de desconto.
        </p>
    </div>
    """, unsafe_allow_html=True)
# ============================================================
# PÁGINA CADASTRO E CÁLCULO
# ============================================================
if pagina == "calculo":
    st.markdown("<h1>Cadastro e Cálculo das Rotas</h1>", unsafe_allow_html=True)

    mes_ref = st.text_input("Mês de referência (ex: Janeiro/2026)", value="")

    aux_total = st.number_input("Auxílio total do mês (R$)", min_value=0.0, step=100.0)

    # ---------------- ROTA SETE LAGOS ----------------
    st.markdown("### 🚍 Rota Sete Lagoas")

    veic_sete = st.number_input("Quantidade de veículos - Sete Lagoas", min_value=1, step=1, value=1)
    veiculos_sete = {}

    for i in range(veic_sete):
        st.markdown(f"**Veículo {i+1} - Sete Lagoas**")
        nome_veic = st.text_input(f"Nome/Tipo do veículo {i+1} (ex: Micro-ônibus, Van)", key=f"nome_sete_{i}")
        v = st.number_input(f"Valor da diária (R$) - Veículo {i+1}", min_value=0.0, step=10.0, key=f"v_sete_{i}")
        d = st.number_input(f"Dias rodados - Veículo {i+1}", min_value=0, step=1, key=f"d_sete_{i}")
        veiculos_sete[f"veic_{i+1}"] = {"valor": v, "dias": d, "nome": nome_veic}

    pass_sete = st.number_input("Total de passagens arrecadadas - Sete Lagoas (R$)", min_value=0.0, step=50.0)
    int_sete = st.number_input("Alunos integrais - Sete Lagoas", min_value=0, step=1)

    st.markdown("#### Alunos com desconto - Sete Lagoas")
    qtd_faixas_sete = st.number_input("Quantas faixas de desconto existem em Sete Lagoas?", min_value=0, step=1, value=0)

    descontos_sete = {}
    for i in range(qtd_faixas_sete):
        col1, col2 = st.columns(2)
        with col1:
            pct = st.number_input(f"Percentual de desconto da faixa {i+1} (%)", min_value=0, max_value=100, step=5, key=f"pct_sete_{i}")
        with col2:
            qtd = st.number_input(f"Quantidade de alunos nessa faixa {i+1}", min_value=0, step=1, key=f"qtd_sete_{i}")
        if pct > 0 and qtd > 0:
            descontos_sete[pct] = descontos_sete.get(pct, 0) + qtd

    diarias_sete = st.number_input("Total de diárias da rota Sete Lagoas", min_value=0, step=1)

    # ---------------- ROTA CURVELO ----------------
    st.markdown("### 🚍 Rota Curvelo")

    veic_cur = st.number_input("Quantidade de veículos - Curvelo", min_value=1, step=1, value=1)
    veiculos_cur = {}

    for i in range(veic_cur):
        st.markdown(f"**Veículo {i+1} - Curvelo**")
        nome_veic = st.text_input(f"Nome/Tipo do veículo {i+1} (ex: Ônibus, Van)", key=f"nome_cur_{i}")
        v = st.number_input(f"Valor da diária (R$) - Veículo {i+1}", min_value=0.0, step=10.0, key=f"v_cur_{i}")
        d = st.number_input(f"Dias rodados - Veículo {i+1}", min_value=0, step=1, key=f"d_cur_{i}")
        veiculos_cur[f"veic_{i+1}"] = {"valor": v, "dias": d, "nome": nome_veic}

    pass_cur = st.number_input("Total de passagens arrecadadas - Curvelo (R$)", min_value=0.0, step=50.0)
    int_cur = st.number_input("Alunos integrais - Curvelo", min_value=0, step=1)

    st.markdown("#### Alunos com desconto - Curvelo")
    qtd_faixas_cur = st.number_input("Quantas faixas de desconto existem em Curvelo?", min_value=0, step=1, value=0)

    descontos_cur = {}
    for i in range(qtd_faixas_cur):
        col1, col2 = st.columns(2)
        with col1:
            pct = st.number_input(f"Percentual de desconto da faixa {i+1} (%) - Curvelo", min_value=0, max_value=100, step=5, key=f"pct_cur_{i}")
        with col2:
            qtd = st.number_input(f"Quantidade de alunos nessa faixa {i+1} - Curvelo", min_value=0, step=1, key=f"qtd_cur_{i}")
        if pct > 0 and qtd > 0:
            descontos_cur[pct] = descontos_cur.get(pct, 0) + qtd

    diarias_cur = st.number_input("Total de diárias da rota Curvelo", min_value=0, step=1)

    # ---------------- BOTÃO CALCULAR ----------------
    if st.button("Calcular rotas"):
        aux_sete, aux_cur = distribuir_auxilio_por_diarias(aux_total, diarias_sete, diarias_cur)

        res_sete = calcular_rota(
            {k: {"valor": v["valor"], "dias": v["dias"]} for k, v in veiculos_sete.items()},
            pass_sete,
            int_sete,
            descontos_sete,
            aux_recebido=aux_sete,
            diarias_rota=diarias_sete
        )
        res_cur = calcular_rota(
            {k: {"valor": v["valor"], "dias": v["dias"]} for k, v in veiculos_cur.items()},
            pass_cur,
            int_cur,
            descontos_cur,
            aux_recebido=aux_cur,
            diarias_rota=diarias_cur
        )

        st.session_state["resultado"] = {
            "mes_ref": mes_ref,
            "sete": res_sete,
            "cur": res_cur,
        }

        salvar_historico(mes_ref, "Sete Lagoas", res_sete)
        salvar_historico(mes_ref, "Curvelo", res_cur)

        st.success("Cálculo realizado e histórico salvo com sucesso.")

        st.markdown("### Resumo - Sete Lagoas")
        st.json(res_sete)

        st.markdown("### Resumo - Curvelo")
        st.json(res_cur)
# ============================================================
# PÁGINA RELATÓRIOS E GRÁFICOS
# ============================================================
if pagina == "relatorios":
    st.markdown("<h1>Relatórios e Gráficos</h1>", unsafe_allow_html=True)

    historico = carregar_historico()

    if historico.empty:
        st.warning("Nenhum histórico encontrado. Gere um cálculo na aba de Cadastro e Cálculo.")
    else:
        st.markdown("### Histórico mensal registrado")
        st.dataframe(historico)

        csv_bytes = historico.to_csv(index=False).encode("utf-8")
        st.download_button(
            label="📥 Baixar histórico completo (CSV)",
            data=csv_bytes,
            file_name="historico_rotas.csv",
            mime="text/csv"
        )

        st.markdown("---")
        st.markdown("### Evolução da mensalidade média por rota")

        graf_mensal = historico.groupby(["mes_ref", "rota"])["mensalidade_media"].mean().reset_index()

        if not graf_mensal.empty:
            chart_mensal = alt.Chart(graf_mensal).mark_line(point=True).encode(
                x=alt.X("mes_ref:N", title="Mês"),
                y=alt.Y("mensalidade_media:Q", title="Mensalidade média (R$)"),
                color=alt.Color("rota:N", title="Rota"),
                tooltip=["mes_ref", "rota", "mensalidade_media"]
            ).properties(height=350)
            st.altair_chart(chart_mensal, use_container_width=True)

        st.markdown("---")
        st.markdown("### Comparativo financeiro da última simulação")

        if "resultado" in st.session_state:
            r = st.session_state["resultado"]
            s = r["sete"]
            c = r["cur"]

            df_comp = pd.DataFrame([
                {"Indicador": "Bruto", "Rota": "Sete Lagoas", "Valor": s["bruto"]},
                {"Indicador": "Bruto ajustado (10%)", "Rota": "Sete Lagoas", "Valor": s["bruto_aj_10"]},
                {"Indicador": "Auxílio recebido", "Rota": "Sete Lagoas", "Valor": s["aux_recebido"]},
                {"Indicador": "Valor final", "Rota": "Sete Lagoas", "Valor": s["valor_final"]},
                {"Indicador": "Bruto", "Rota": "Curvelo", "Valor": c["bruto"]},
                {"Indicador": "Bruto ajustado (10%)", "Rota": "Curvelo", "Valor": c["bruto_aj_10"]},
                {"Indicador": "Auxílio recebido", "Rota": "Curvelo", "Valor": c["aux_recebido"]},
                {"Indicador": "Valor final", "Rota": "Curvelo", "Valor": c["valor_final"]},
            ])

            chart_comp = alt.Chart(df_comp).mark_bar().encode(
                x=alt.X("Indicador:N", title="Etapa"),
                y=alt.Y("Valor:Q", title="Valor (R$)"),
                color=alt.Color("Rota:N", title="Rota"),
                tooltip=["Indicador", "Rota", "Valor"]
            ).properties(height=350)

            st.altair_chart(chart_comp, use_container_width=True)
        else:
            st.info("Nenhuma simulação ativa encontrada. Faça um cálculo para ver o comparativo.")
# ============================================================
# FUNÇÃO PDF
# ============================================================
def gerar_pdf_profissional(r: dict) -> bytes:
    resumo_qr = (
        f"ASSEUF - {r.get('mes_ref', 'Mês não informado')} | "
        f"Sete Lagoas: R$ {r['sete']['valor_final']:,.2f} | "
        f"Curvelo: R$ {r['cur']['valor_final']:,.2f}"
    )
    qr_b64 = gerar_qr_base64(resumo_qr)

    def fmt_brl(val):
        try:
            return f"R$ {float(val):,.2f}"
        except Exception:
            return "R$ 0,00"

    s = r["sete"]
    c = r["cur"]

    total_bruto = s["bruto"] + c["bruto"]
    total_pass = s["passagens"] + c["passagens"]
    total_10 = s["dez_porcento"] + c["dez_porcento"]
    total_bruto_aj = s["bruto_aj_10"] + c["bruto_aj_10"]
    total_aux = s["aux_recebido"] + c["aux_recebido"]
    total_pos_aux = s["pos_aux"] + c["pos_aux"]
    total_90 = s["noventa_porcento"] + c["noventa_porcento"]
    total_final = s["valor_final"] + c["valor_final"]
    total_alunos_int = s["alunos_integrais"] + c["alunos_integrais"]
    total_alunos_desc = s["alunos_desconto_total"] + c["alunos_desconto_total"]
    total_veic = s["veiculos_qtd"] + c["veiculos_qtd"]
    total_diarias = s["diarias"] + c["diarias"]

    html = f"""
    <!DOCTYPE html>
    <html lang="pt-BR">
    <head>
        <meta charset="UTF-8">
        <title>Relatório ASSEUF - {r.get('mes_ref', '')}</title>
        <style>
            @page {{ size: A4; margin: 1.8cm; }}
            body {{
                font-family: Arial, sans-serif;
                color: #2c3e50;
                line-height: 1.5;
            }}
            .header {{
                display: flex;
                justify-content: space-between;
                align-items: center;
                border-bottom: 3px solid #00e676;
                padding-bottom: 12px;
                margin-bottom: 25px;
            }}
            .title h1 {{
                color: #00695c;
                font-size: 22px;
                margin: 0;
            }}
            .qr img {{
                width: 90px;
                height: 90px;
            }}
            h2 {{
                color: #004d40;
                font-size: 17px;
                margin-top: 25px;
                margin-bottom: 10px;
                border-left: 5px solid #00e676;
                padding-left: 10px;
            }}
            table {{
                width: 100%;
                border-collapse: collapse;
                margin-bottom: 20px;
                font-size: 12px;
            }}
            th {{
                background-color: #e0f2f1;
                color: #004d40;
                padding: 8px;
                border: 1px solid #b0bec5;
                text-align: center;
                font-weight: bold;
            }}
            td {{
                padding: 7px;
                border: 1px solid #b0bec5;
                text-align: right;
            }}
            td:first-child {{
                text-align: left;
                font-weight: 500;
            }}
            .totais {{
                background-color: #f1f8e9;
                border-left: 5px solid #00e676;
                padding: 12px;
                margin-top: 25px;
            }}
            .footer {{
                margin-top: 40px;
                text-align: center;
                font-size: 10px;
                color: #95a5a6;
                border-top: 1px solid #ecf0f1;
                padding-top: 15px;
            }}
        </style>
    </head>
    <body>

        <div class="header">
            <div class="title">
                <h1>ASSEUF • Relatório Mensal</h1>
                <span>Metodologia: 10% → auxílio → 90% → alunos integrais e com desconto</span>
            </div>
            <div class="qr">
                <img src="data:image/png;base64,{qr_b64}">
            </div>
        </div>

        <p><strong>Mês de referência:</strong> {r.get('mes_ref', 'Não informado')}</p>

        <h2>Resumo financeiro por rota</h2>
        <table>
            <tr>
                <th>Etapa</th>
                <th>Sete Lagoas</th>
                <th>Curvelo</th>
                <th>Total</th>
            </tr>
            <tr>
                <td>Custo bruto</td>
                <td>{fmt_brl(s['bruto'])}</td>
                <td>{fmt_brl(c['bruto'])}</td>
                <td>{fmt_brl(total_bruto)}</td>
            </tr>
            <tr>
                <td>Passagens arrecadadas</td>
                <td>{fmt_brl(s['passagens'])}</td>
                <td>{fmt_brl(c['passagens'])}</td>
                <td>{fmt_brl(total_pass)}</td>
            </tr>
            <tr>
                <td>(-) 10% das passagens</td>
                <td>{fmt_brl(s['dez_porcento'])}</td>
                <td>{fmt_brl(c['dez_porcento'])}</td>
                <td>{fmt_brl(total_10)}</td>
            </tr>
            <tr>
                <td>Custo após 10%</td>
                <td>{fmt_brl(s['bruto_aj_10'])}</td>
                <td>{fmt_brl(c['bruto_aj_10'])}</td>
                <td>{fmt_brl(total_bruto_aj)}</td>
            </tr>
            <tr>
                <td>(-) Auxílio recebido</td>
                <td>{fmt_brl(s['aux_recebido'])}</td>
                <td>{fmt_brl(c['aux_recebido'])}</td>
                <td>{fmt_brl(total_aux)}</td>
            </tr>
            <tr>
                <td>Valor após auxílio</td>
                <td>{fmt_brl(s['pos_aux'])}</td>
                <td>{fmt_brl(c['pos_aux'])}</td>
                <td>{fmt_brl(total_pos_aux)}</td>
            </tr>
            <tr>
                <td>(-) 90% das passagens</td>
                <td>{fmt_brl(s['noventa_porcento'])}</td>
                <td>{fmt_brl(c['noventa_porcento'])}</td>
                <td>{fmt_brl(total_90)}</td>
            </tr>
            <tr>
                <td><strong>Valor final</strong></td>
                <td><strong>{fmt_brl(s['valor_final'])}</strong></td>
                <td><strong>{fmt_brl(c['valor_final'])}</strong></td>
                <td><strong>{fmt_brl(total_final)}</strong></td>
            </tr>
        </table>

        <h2>Alunos e mensalidade</h2>
        <table>
            <tr>
                <th>Rota</th>
                <th>Alunos integrais</th>
                <th>Alunos com desconto</th>
                <th>Mensalidade média</th>
            </tr>
            <tr>
                <td>Sete Lagoas</td>
                <td style="text-align:center;">{s['alunos_integrais']}</td>
                <td style="text-align:center;">{s['alunos_desconto_total']}</td>
                <td>{fmt_brl(s['mensalidade_media'])}</td>
            </tr>
            <tr>
                <td>Curvelo</td>
                <td style="text-align:center;">{c['alunos_integrais']}</td>
                <td style="text-align:center;">{c['alunos_desconto_total']}</td>
                <td>{fmt_brl(c['mensalidade_media'])}</td>
            </tr>
        </table>

        <div class="totais">
            <h3>Resumo consolidado</h3>
            <p><strong>Total de alunos integrais:</strong> {total_alunos_int}</p>
            <p><strong>Total de alunos com desconto:</strong> {total_alunos_desc}</p>
            <p><strong>Total de veículos:</strong> {total_veic}</p>
            <p><strong>Total de diárias:</strong> {total_diarias}</p>
            <p><strong>Valor final total:</strong> {fmt_brl(total_final)}</p>
        </div>

        <div class="footer">
            Relatório gerado automaticamente pelo Sistema ASSEUF em {datetime.now().strftime('%d/%m/%Y %H:%M')}.
        </div>

    </body>
    </html>
    """

    return HTML(string=html).write_pdf()

# ============================================================
# PÁGINA PDF
# ============================================================
if pagina == "pdf":
    st.markdown("<h1>Geração de PDF</h1>", unsafe_allow_html=True)

    if "resultado" not in st.session_state:
        st.warning("Nenhuma simulação encontrada. Vá em 'Cadastro e Cálculo' e gere um cálculo primeiro.")
    else:
        r = st.session_state["resultado"]
        pdf_bytes = gerar_pdf_profissional(r)
        b64 = base64.b64encode(pdf_bytes).decode("utf-8")
        href = f'<a href="data:application/pdf;base64,{b64}" download="relatorio_asseuf.pdf">📥 Baixar relatório em PDF</a>'
        st.markdown(href, unsafe_allow_html=True)