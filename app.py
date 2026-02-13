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
    page_title="Sistema de Cálculo das Rotas - ASSEUF (Nova Lógica)",
    page_icon="🚌",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ============================================================
# LOGO
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
# CSS
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
        .divider {
            height: 1px;
            background: linear-gradient(90deg, transparent, #00e676, transparent);
            margin: 18px 0;
        }
    </style>
""", unsafe_allow_html=True)

# ============================================================
# FUNÇÕES DE CÁLCULO
# ============================================================
def alunos_equivalentes(integrais: int, descontos: dict) -> float:
    """
    descontos: {percentual: quantidade}
    ex: {50: 3, 70: 1, 30: 2}
    """
    total = float(integrais)
    for pct, qtd in descontos.items():
        fator = (100 - pct) / 100.0
        total += qtd * fator
    return total


def calcular_bruto(veiculos: dict) -> float:
    return sum(v["valor"] * v["dias"] for v in veiculos.values())


def distribuir_auxilio_por_diarias(aux_total: float, d7: int, dC: int):
    if aux_total <= 0:
        return 0.0, 0.0
    if d7 == 0 and dC == 0:
        return 0.0, 0.0
    if d7 == 0:
        return 0.0, aux_total
    if dC == 0:
        return aux_total, 0.0

    if d7 == dC:
        total = d7 + dC
        return aux_total * d7 / total, aux_total * dC / total

    if d7 > dC:
        excedente = d7 - dC
        base = dC
        total_base = base * 2 + excedente
        valor_diaria = aux_total / total_base
        aux7 = base * valor_diaria + excedente * (valor_diaria * 0.70)
        auxc = base * valor_diaria + excedente * (valor_diaria * 0.30)
        return aux7, auxc

    excedente = dC - d7
    base = d7
    total_base = base * 2 + excedente
    valor_diaria = aux_total / total_base
    aux7 = base * valor_diaria + excedente * (valor_diaria * 0.30)
    auxc = base * valor_diaria + excedente * (valor_diaria * 0.70)
    return aux7, auxc


def calcular_rota_nova_logica(
    veiculos: dict,
    passagens: float,
    integrais: int,
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
    al_eq = alunos_equivalentes(integrais, descontos)
    mensalidade = valor_final / al_eq if al_eq > 0 else 0.0

    return {
        "bruto": bruto,
        "passagens": passagens,
        "dez_porcento": dez_porcento,
        "bruto_aj_10": bruto_aj_10,
        "aux_recebido": aux_recebido,
        "pos_aux": pos_aux,
        "noventa_porcento": noventa_porcento,
        "valor_final": valor_final,
        "alunos_equivalentes": al_eq,
        "mensalidade": mensalidade,
        "integrais": integrais,
        "descontos": descontos,
        "diarias": diarias_rota,
        "veiculos_qtd": len(veiculos),
    }

# ============================================================
# HISTÓRICO MENSAL
# ============================================================
HIST_PATH = "historico.csv"

def carregar_historico():
    if os.path.exists(HIST_PATH):
        return pd.read_csv(HIST_PATH)
    return pd.DataFrame(columns=[
        "mes_ref",
        "rota",
        "bruto",
        "passagens",
        "dez_porcento",
        "bruto_aj_10",
        "aux_recebido",
        "pos_aux",
        "noventa_porcento",
        "valor_final",
        "alunos_equivalentes",
        "mensalidade",
        "veiculos",
        "diarias",
        "data_registro"
    ])

def salvar_historico(mes_ref, rota_nome, dados):
    df = carregar_historico()
    novo = {
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
        "alunos_equivalentes": dados["alunos_equivalentes"],
        "mensalidade": dados["mensalidade"],
        "veiculos": dados["veiculos_qtd"],
        "diarias": dados["diarias"],
        "data_registro": datetime.now().strftime("%d/%m/%Y %H:%M")
    }
    df = pd.concat([df, pd.DataFrame([novo])], ignore_index=True)
    df.to_csv(HIST_PATH, index=False)

# ============================================================
# QR + PDF
# ============================================================
def gerar_qr_base64(texto: str) -> str:
    qr = qrcode.QRCode(box_size=4, border=1)
    qr.add_data(texto)
    qr.make(fit=True)
    img = qr.make_image(fill_color="black", back_color="white")
    buf = BytesIO()
    img.save(buf, format="PNG")
    return base64.b64encode(buf.getvalue()).decode("utf-8")


def gerar_pdf_profissional_nova_logica(r: dict) -> bytes:
    resumo_qr = (
        f"ASSEUF - {r.get('mes_ref', 'Mês não informado')} | "
        f"7L: R$ {r['sete']['valor_final']:,.2f} | "
        f"Cur: R$ {r['cur']['valor_final']:,.2f}"
    )
    qr_b64 = gerar_qr_base64(resumo_qr)

    def fmt_brl(val):
        try:
            return f"R$ {float(val):,.2f}"
        except:
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
    total_al_eq = s["alunos_equivalentes"] + c["alunos_equivalentes"]
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
                font-family: 'Helvetica', 'Arial', sans-serif;
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
                font-size: 24px;
                margin: 0;
            }}
            .qr img {{
                width: 90px;
                height: 90px;
            }}
            h2 {{
                color: #004d40;
                font-size: 18px;
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
                padding: 10px 5px;
                border: 1px solid #b0bec5;
                text-align: center;
                font-weight: 600;
            }}
            td {{
                padding: 8px 5px;
                border: 1px solid #b0bec5;
                text-align: right;
            }}
            td:first-child {{
                text-align: left;
                font-weight: 500;
            }}
            .footer {{
                margin-top: 40px;
                text-align: center;
                font-size: 10px;
                color: #95a5a6;
                border-top: 1px solid #ecf0f1;
                padding-top: 15px;
            }}
            .totais {{
                background-color: #f1f8e9;
                border-left: 5px solid #00e676;
                padding: 12px;
                margin-top: 25px;
            }}
        </style>
    </head>
    <body>

        <div class="header">
            <div class="title">
                <h1>ASSEUF • Relatório Mensal</h1>
                <span>Nova metodologia: 10% → auxílio → 90% → alunos equivalentes</span>
            </div>
            <div class="qr">
                <img src="data:image/png;base64,{qr_b64}" alt="QR Code">
            </div>
        </div>

        <p><strong>Mês de referência:</strong> {r.get('mes_ref', 'Não informado')}</p>

        <h2>📊 Resumo Financeiro por Rota</h2>
        <table>
            <tr>
                <th>Etapa</th>
                <th>7 Lagoas</th>
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
                <td><strong>Custo após 10%</strong></td>
                <td><strong>{fmt_brl(s['bruto_aj_10'])}</strong></td>
                <td><strong>{fmt_brl(c['bruto_aj_10'])}</strong></td>
                <td><strong>{fmt_brl(total_bruto_aj)}</strong></td>
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

        <h2>👥 Alunos e Mensalidades</h2>
        <table>
            <tr>
                <th>Rota</th>
                <th>Alunos equivalentes</th>
                <th>Mensalidade</th>
            </tr>
            <tr>
                <td>7 Lagoas</td>
                <td style="text-align:center;">{s['alunos_equivalentes']:.2f}</td>
                <td>{fmt_brl(s['mensalidade'])}</td>
            </tr>
            <tr>
                <td>Curvelo</td>
                <td style="text-align:center;">{c['alunos_equivalentes']:.2f}</td>
                <td>{fmt_brl(c['mensalidade'])}</td>
            </tr>
        </table>

        <div class="totais">
            <h3>📌 Resumo Consolidado Geral</h3>
            <p><strong>Total de alunos equivalentes:</strong> {total_al_eq:.2f}</p>
            <p><strong>Total de veículos:</strong> {total_veic}</p>
            <p><strong>Total de diárias:</strong> {total_diarias}</p>
            <p><strong>Valor final total:</strong> {fmt_brl(total_final)}</p>
        </div>

        <div class="footer">
            Relatório gerado automaticamente pelo Sistema ASSEUF (nova lógica) em {datetime.now().strftime('%d/%m/%Y às %H:%M')}.<br>
            Metodologia: 10% → auxílio → 90% → alunos equivalentes.
        </div>

    </body>
    </html>
    """
    return HTML(string=html).write_pdf()

# ============================================================
# NAVEGAÇÃO
# ============================================================
pagina = st.sidebar.radio(
    "Navegação",
    ["🏠 Início", "🧮 Cadastro e Cálculo", "📊 Relatórios e Gráficos", "📄 PDF"]
)

# ============================================================
# PÁGINA INÍCIO
# ============================================================
if pagina == "🏠 Início":
    st.markdown("<h1>Nova Lógica de Cálculo - ASSEUF</h1>", unsafe_allow_html=True)
    st.markdown("""
    <div class="elevated-card">
        <h3>Fluxo da nova metodologia</h3>
        <div class="divider"></div>
        <ul>
            <li>1️⃣ Calcula o <b>custo bruto</b> da rota (diária × dias × veículos).</li>
            <li>2️⃣ Calcula <b>10% das passagens</b> e abate esse valor do bruto.</li>
            <li>3️⃣ Divide o <b>auxílio</b> entre as rotas pela regra das diárias + 70/30.</li>
            <li>4️⃣ Abate o <b>auxílio</b> do custo já ajustado pelos 10%.</li>
            <li>5️⃣ Abate os <b>90% restantes das passagens</b> da própria rota.</li>
            <li>6️⃣ O valor que sobra é dividido pelos <b>alunos equivalentes</b> da rota.</li>
        </ul>
    </div>
    """, unsafe_allow_html=True)

# ============================================================
# PÁGINA CADASTRO E CÁLCULO (COM DESCONTOS DINÂMICOS)
# ============================================================
if pagina == "🧮 Cadastro e Cálculo":
    st.markdown("<h1>Cadastro e Cálculo das Rotas</h1>", unsafe_allow_html=True)

    mes_ref = st.text_input("Mês de referência (ex: Janeiro/2026)", value="")

    aux_total = st.number_input("Auxílio total do mês (R$)", min_value=0.0, step=100.0)

    # ---------- ROTA 7 LAGOAS ----------
    st.markdown("### Dados da Rota 7 Lagoas")
    veic_7 = st.number_input("Quantidade de veículos - 7 Lagoas", min_value=1, step=1, value=1)
    veiculos_7 = {}
    for i in range(veic_7):
        st.markdown(f"**Veículo {i+1} - 7 Lagoas**")
        v = st.number_input(f"Valor da diária (R$) - Veículo {i+1} (7L)", min_value=0.0, step=10.0, key=f"v7_{i}")
        d = st.number_input(f"Dias rodados - Veículo {i+1} (7L)", min_value=0, step=1, key=f"d7_{i}")
        veiculos_7[f"veic_{i+1}"] = {"valor": v, "dias": d}

    pass_7 = st.number_input("Total de passagens arrecadadas - 7 Lagoas (R$)", min_value=0.0, step=50.0)
    int_7 = st.number_input("Alunos integrais - 7 Lagoas", min_value=0, step=1)

    st.markdown("#### Alunos com desconto - 7 Lagoas")
    qtd_faixas_7 = st.number_input("Quantas faixas de desconto existem em 7 Lagoas?", min_value=0, step=1, value=0)
    descontos_7 = {}
    for i in range(qtd_faixas_7):
        col1, col2 = st.columns(2)
        with col1:
            pct = st.number_input(f"Percentual de desconto da faixa {i+1} (%) - 7L", min_value=0, max_value=100, step=5, key=f"pct7_{i}")
        with col2:
            qtd = st.number_input(f"Quantidade de alunos nessa faixa {i+1} - 7L", min_value=0, step=1, key=f"qtd7_{i}")
        if pct > 0 and qtd > 0:
            descontos_7[pct] = descontos_7.get(pct, 0) + qtd

    diarias_7 = st.number_input("Total de diárias da rota 7 Lagoas", min_value=0, step=1)

    # ---------- ROTA CURVELO ----------
    st.markdown("### Dados da Rota Curvelo")
    veic_c = st.number_input("Quantidade de veículos - Curvelo", min_value=1, step=1, value=1)
    veiculos_c = {}
    for i in range(veic_c):
        st.markdown(f"**Veículo {i+1} - Curvelo**")
        v = st.number_input(f"Valor da diária (R$) - Veículo {i+1} (Cur)", min_value=0.0, step=10.0, key=f"vc_{i}")
        d = st.number_input(f"Dias rodados - Veículo {i+1} (Cur)", min_value=0, step=1, key=f"dc_{i}")
        veiculos_c[f"veic_{i+1}"] = {"valor": v, "dias": d}

    pass_c = st.number_input("Total de passagens arrecadadas - Curvelo (R$)", min_value=0.0, step=50.0)
    int_c = st.number_input("Alunos integrais - Curvelo", min_value=0, step=1)

    st.markdown("#### Alunos com desconto - Curvelo")
    qtd_faixas_c = st.number_input("Quantas faixas de desconto existem em Curvelo?", min_value=0, step=1, value=0)
    descontos_c = {}
    for i in range(qtd_faixas_c):
        col1, col2 = st.columns(2)
        with col1:
            pct = st.number_input(f"Percentual de desconto da faixa {i+1} (%) - Cur", min_value=0, max_value=100, step=5, key=f"pctc_{i}")
        with col2:
            qtd = st.number_input(f"Quantidade de alunos nessa faixa {i+1} - Cur", min_value=0, step=1, key=f"qtdc_{i}")
        if pct > 0 and qtd > 0:
            descontos_c[pct] = descontos_c.get(pct, 0) + qtd

    diarias_c = st.number_input("Total de diárias da rota Curvelo", min_value=0, step=1)

    if st.button("Calcular"):
        aux_7, aux_c = distribuir_auxilio_por_diarias(aux_total, diarias_7, diarias_c)

        res_7 = calcular_rota_nova_logica(
            veiculos_7, pass_7, int_7, descontos_7, aux_recebido=aux_7, diarias_rota=diarias_7
        )
        res_c = calcular_rota_nova_logica(
            veiculos_c, pass_c, int_c, descontos_c, aux_recebido=aux_c, diarias_rota=diarias_c
        )

        st.session_state["resultado"] = {
            "mes_ref": mes_ref,
            "sete": res_7,
            "cur": res_c,
        }

        salvar_historico(mes_ref, "7 Lagoas", res_7)
        salvar_historico(mes_ref, "Curvelo", res_c)

        st.success("Cálculo realizado, histórico salvo e pronto para gerar PDF.")
        st.write("### Resumo rápido - 7 Lagoas")
        st.json(res_7)
        st.write("### Resumo rápido - Curvelo")
        st.json(res_c)
# ============================================================
# PÁGINA RELATÓRIOS E GRÁFICOS
# ============================================================
if pagina == "📊 Relatórios e Gráficos":
    st.markdown("<h1>📊 Relatórios e Gráficos</h1>", unsafe_allow_html=True)

    historico = carregar_historico()

    if historico.empty:
        st.warning("Nenhum histórico encontrado. Gere um cálculo primeiro.")
    else:
        st.subheader("📅 Histórico Mensal Registrado")
        st.dataframe(historico)

        csv_bytes = historico.to_csv(index=False).encode("utf-8")
        st.download_button(
            label="📥 Baixar histórico completo (CSV)",
            data=csv_bytes,
            file_name="historico_rotas.csv",
            mime="text/csv"
        )

        st.divider()

        st.subheader("📈 Evolução da Mensalidade por Rota")
        graf_mensal = historico.groupby(["mes_ref", "rota"])["mensalidade"].mean().reset_index()
        chart_mensal = alt.Chart(graf_mensal).mark_line(point=True).encode(
            x=alt.X("mes_ref:N", title="Mês"),
            y=alt.Y("mensalidade:Q", title="Mensalidade (R$)"),
            color=alt.Color("rota:N", title="Rota"),
            tooltip=["mes_ref", "rota", "mensalidade"]
        )
        st.altair_chart(chart_mensal, use_container_width=True)

        st.divider()

        if "resultado" in st.session_state:
            r = st.session_state["resultado"]
            s = r["sete"]
            c = r["cur"]

            st.subheader("📊 Comparativo Financeiro (Bruto, Ajustado, Auxílio, Final)")

            df_comp = pd.DataFrame([
                {"Indicador": "Bruto", "Rota": "7 Lagoas", "Valor": s["bruto"]},
                {"Indicador": "Bruto Ajustado (10%)", "Rota": "7 Lagoas", "Valor": s["bruto_aj_10"]},
                {"Indicador": "Auxílio Recebido", "Rota": "7 Lagoas", "Valor": s["aux_recebido"]},
                {"Indicador": "Valor Final (após 90%)", "Rota": "7 Lagoas", "Valor": s["valor_final"]},
                {"Indicador": "Bruto", "Rota": "Curvelo", "Valor": c["bruto"]},
                {"Indicador": "Bruto Ajustado (10%)", "Rota": "Curvelo", "Valor": c["bruto_aj_10"]},
                {"Indicador": "Auxílio Recebido", "Rota": "Curvelo", "Valor": c["aux_recebido"]},
                {"Indicador": "Valor Final (após 90%)", "Rota": "Curvelo", "Valor": c["valor_final"]},
            ])

            chart_comp = alt.Chart(df_comp).mark_bar().encode(
                x=alt.X("Indicador:N", title="Etapa"),
                y=alt.Y("Valor:Q", title="Valor (R$)"),
                color=alt.Color("Rota:N", title="Rota"),
                column=alt.Column("Rota:N", title=""),
                tooltip=["Indicador", "Rota", "Valor"]
            )
            st.altair_chart(chart_comp, use_container_width=True)

# ============================================================
# PÁGINA PDF
# ============================================================
if pagina == "📄 PDF":
    st.markdown("<h1>Geração de PDF</h1>", unsafe_allow_html=True)

    if "resultado" not in st.session_state:
        st.warning("Nenhum cálculo encontrado. Vá na aba 'Cadastro e Cálculo' primeiro.")
    else:
        r = st.session_state["resultado"]
        pdf_bytes = gerar_pdf_profissional_nova_logica(r)
        b64 = base64.b64encode(pdf_bytes).decode("utf-8")
        href = f'<a href="data:application/pdf;base64,{b64}" download="relatorio_asseuf_nova_logica.pdf">📥 Baixar PDF</a>'
        st.markdown(href, unsafe_allow_html=True)