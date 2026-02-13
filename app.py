from pathlib import Path
import streamlit as st
import pandas as pd
import altair as alt
import base64
import qrcode
from io import BytesIO
from weasyprint import HTML
from datetime import datetime

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
# CSS PREMIUM
# ============================================================
st.markdown("""
    <style>
        @import url('https://fonts.googleapis.com/css2?family=Poppins:wght@300;400;600;700&family=Space+Grotesk:wght@400;600&display=swap');
        html, body, [class*="css"] { font-family: 'Poppins', sans-serif; }
        body { background-color: #02040A; }
        .main { background: radial-gradient(circle at top, #10152A 0, #02040A 55%); color: #f5f5f5; }
        h1, h2, h3, h4, h5 { font-family: 'Space Grotesk', sans-serif; letter-spacing: 0.03em; color: #00e676 !important; }
        .sidebar .sidebar-content { background: linear-gradient(180deg, #050814, #02040A) !important; }
        .elevated-card { background: linear-gradient(145deg, #0b0f1c, #050814); padding: 20px; border-radius: 16px; box-shadow: 0px 0px 18px rgba(0,0,0,0.6); margin-bottom: 20px; border: 1px solid rgba(0,230,118,0.15); }
        .calc-card { background: radial-gradient(circle at top left, #10152A, #050814); padding: 25px; border-radius: 18px; box-shadow: 0px 0px 22px rgba(0,0,0,0.7); margin-top: 30px; border: 1px solid rgba(0,230,118,0.25); }
        .stButton>button { background: linear-gradient(135deg, #00e676, #00b248); color: #02040A; border-radius: 999px; font-weight: 700; padding: 10px 26px; border: none; box-shadow: 0px 0px 12px rgba(0,230,118,0.5); transition: all 0.3s ease; }
        .stButton>button:hover { background: linear-gradient(135deg, #00b248, #00e676); color: white; box-shadow: 0px 0px 18px rgba(0,230,118,0.8); transform: scale(1.02); }
        .metric-card { background: linear-gradient(145deg, #0b0f1c, #050814); padding: 18px 20px; border-radius: 14px; border: 1px solid rgba(255,255,255,0.06); box-shadow: 0px 0px 16px rgba(0,0,0,0.6); }
        .metric-label { font-size: 0.8rem; text-transform: uppercase; letter-spacing: 0.08em; color: #9e9e9e; }
        .metric-value { font-size: 1.4rem; font-weight: 700; color: #ffffff; }
        .metric-sub { font-size: 0.85rem; color: #bdbdbd; }
        .section-title { font-size: 1.1rem; font-weight: 600; text-transform: uppercase; letter-spacing: 0.12em; color: #9e9e9e; margin-top: 10px; }
        .divider { height: 1px; background: linear-gradient(90deg, transparent, #00e676, transparent); margin: 18px 0; }
        ul { margin-left: 18px; }
        .stDownloadButton>button { background: linear-gradient(135deg, #2979ff, #1565c0) !important; color: white !important; box-shadow: 0px 0px 12px rgba(41,121,255,0.5); }
        .stDownloadButton>button:hover { background: linear-gradient(135deg, #1565c0, #0d47a1) !important; }
    </style>
""", unsafe_allow_html=True)

# ============================================================
# FUNÇÕES DO SISTEMA
# ============================================================
def alunos_equivalentes(integrais: int, descontos: dict) -> float:
    total = float(integrais)
    for pct, qtd in descontos.items():
        fator = (100 - pct) / 100.0
        total += qtd * fator
    return total

def calcular_bruto(veiculos: dict) -> float:
    return sum(v["valor"] * v["dias"] for v in veiculos.values())

def distribuir_auxilio_por_diarias(aux_total: float, bruto_aj_7l: float, bruto_aj_cur: float, d7: int, dC: int):
    if d7 == 0 and dC == 0:
        return 0.0, 0.0
    total_bruto_aj = bruto_aj_7l + bruto_aj_cur
    if total_bruto_aj <= 0:
        return 0.0, 0.0
    aux_7l_proporcional = aux_total * (bruto_aj_7l / total_bruto_aj)
    aux_cur_proporcional = aux_total * (bruto_aj_cur / total_bruto_aj)
    if d7 > dC and dC > 0:
        excedente = d7 - dC
        base = dC
        total_base = base * 2 + excedente
        valor_ajuste = aux_total * 0.20 * (excedente / total_base)
        aux_7l = aux_7l_proporcional + valor_ajuste
        aux_cur = aux_cur_proporcional - valor_ajuste
    elif dC > d7 and d7 > 0:
        excedente = dC - d7
        base = d7
        total_base = base * 2 + excedente
        valor_ajuste = aux_total * 0.20 * (excedente / total_base)
        aux_7l = aux_7l_proporcional - valor_ajuste
        aux_cur = aux_cur_proporcional + valor_ajuste
    else:
        aux_7l = aux_7l_proporcional
        aux_cur = aux_cur_proporcional
    aux_7l = max(0, aux_7l)
    aux_cur = max(0, aux_cur)
    soma = aux_7l + aux_cur
    if soma > 0:
        fator_ajuste = aux_total / soma
        aux_7l *= fator_ajuste
        aux_cur *= fator_ajuste
    return aux_7l, aux_cur

def gerar_qr_base64(texto: str) -> str:
    qr = qrcode.QRCode(box_size=4, border=1)
    qr.add_data(texto)
    qr.make(fit=True)
    img = qr.make_image(fill_color="black", back_color="white")
    buf = BytesIO()
    img.save(buf, format="PNG")
    return base64.b64encode(buf.getvalue()).decode("utf-8")

def gerar_pdf_profissional(r: dict) -> bytes:
    qr_b64 = gerar_qr_base64(f"Relatório ASSEUF - {r.get('mes_ref', 'Mês atual')}")
    def fmt_brl(val):
        try:
            return f"R$ {float(val):,.2f}"
        except:
            return "R$ 0,00"
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
            .title span {{
                font-size: 12px;
                color: #7f8c8d;
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
            .obs {{
                background-color: #f9f9f9;
                padding: 12px;
                border-left: 4px solid #00e676;
                font-style: italic;
                font-size: 11px;
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
                <span>Sistema de Cálculo das Rotas - 7 Lagoas & Curvelo</span>
            </div>
            <div class="qr">
                <img src="data:image/png;base64,{qr_b64}" alt="QR Code">
                <p style="font-size:9px; margin:0;">Validação do relatório</p>
            </div>
        </div>
        <p style="font-size:14px;"><strong>Mês de referência:</strong> {r.get('mes_ref', 'Não informado')}</p>
        <h2>📊 Resumo Financeiro</h2>
        <table>
            <tr>
                <th>Indicador</th>
                <th>7 Lagoas</th>
                <th>Curvelo</th>
                <th>Total</th>
            </tr>
            <tr>
                <td>Custo bruto original</td>
                <td>{fmt_brl(r['bruto_7l'])}</td>
                <td>{fmt_brl(r['bruto_cur'])}</td>
                <td>{fmt_brl(r['bruto_7l'] + r['bruto_cur'])}</td>
            </tr>
            <tr>
                <td>(-) 10% das passagens (própria rota)</td>
                <td>{fmt_brl(r['pass_7l'] * 0.1)}</td>
                <td>{fmt_brl(r['pass_cur'] * 0.1)}</td>
                <td>{fmt_brl((r['pass_7l'] + r['pass_cur']) * 0.1)}</td>
            </tr>
            <tr>
                <td><strong>Custo bruto ajustado</strong></td>
                <td><strong>{fmt_brl(r['bruto_aj_7l'])}</strong></td>
                <td><strong>{fmt_brl(r['bruto_aj_cur'])}</strong></td>
                <td><strong>{fmt_brl(r['bruto_aj_7l'] + r['bruto_aj_cur'])}</strong></td>
            </tr>
            <tr>
                <td>Auxílio recebido</td>
                <td>{fmt_brl(r['aux_ideal_7l'])}</td>
                <td>{fmt_brl(r['aux_ideal_cur'])}</td>
                <td>{fmt_brl(r['aux_ideal_7l'] + r['aux_ideal_cur'])}</td>
            </tr>
            <tr>
                <td><strong>Líquido final (custo - auxílio)</strong></td>
                <td><strong>{fmt_brl(r['liquido_7l'])}</strong></td>
                <td><strong>{fmt_brl(r['liquido_cur'])}</strong></td>
                <td><strong>{fmt_brl(r['liquido_7l'] + r['liquido_cur'])}</strong></td>
            </tr>
        </table>
        <h2>👥 Alunos e Mensalidades</h2>
        <table>
            <tr>
                <th>Rota</th>
                <th>Alunos integrais</th>
                <th>Alunos equivalentes</th>
                <th>Mensalidade calculada</th>
            </tr>
            <tr>
                <td>7 Lagoas</td>
                <td style="text-align:center;">{r['int_7l']}</td>
                <td style="text-align:center;">{r['al_eq_7l']:.2f}</td>
                <td>{fmt_brl(r['mensal_7l'])}</td>
            </tr>
            <tr>
                <td>Curvelo</td>
                <td style="text-align:center;">{r['int_cur']}</td>
                <td style="text-align:center;">{r['al_eq_cur']:.2f}</td>
                <td>{fmt_brl(r['mensal_cur'])}</td>
            </tr>
        </table>
        <h2>🚌 Informações Operacionais</h2>
        <table>
            <tr>
                <th>Rota</th>
                <th>Nº de veículos</th>
                <th>Total de diárias</th>
                <th>Diárias motoristas</th>
                <th>Custos extras</th>
            </tr>
            <tr>
                <td>7 Lagoas</td>
                <td style="text-align:center;">{r.get('veic_sete', 0)}</td>
                <td style="text-align:center;">{r['diarias_7l']}</td>
                <td>{fmt_brl(r.get('diaria_sete', 0))}</td>
                <td>{fmt_brl(r.get('custo_extra_sete', 0))}</td>
            </tr>
            <tr>
                <td>Curvelo</td>
                <td style="text-align:center;">{r.get('veic_cur', 0)}</td>
                <td style="text-align:center;">{r['diarias_cur']}</td>
                <td>{fmt_brl(r.get('diaria_cur', 0))}</td>
                <td>{fmt_brl(r.get('custo_extra_cur', 0))}</td>
            </tr>
        </table>
        <h2>📋 Observações do Mês</h2>
        <div class="obs">
            {r.get('obs_gerais', 'Nenhuma observação registrada.')}
        </div>
        <div class="footer">
            Relatório gerado automaticamente pelo Sistema ASSEUF em {datetime.now().strftime('%d/%m/%Y às %H:%M')}.<br>
            Metodologia: custo bruto abatido de 10% das passagens por rota; distribuição proporcional ao custo ajustado + regra 70/30; mensalidade baseada em alunos equivalentes.
        </div>
    </body>
    </html>
    """
    return HTML(string=html).write_pdf()

# ============================================================
# MENU DE NAVEGAÇÃO
# ============================================================
pagina = st.sidebar.radio(
    "Navegação",
    ["🏠 Início", "🧮 Cadastro e Cálculo", "📊 Relatórios e Gráficos"]
)

# ============================================================
# PÁGINA 1 — INÍCIO (VERSÃO CORRIGIDA SEM ERROS)
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
        
        <h3>1. Abatimento de 10% das Passagens no Custo Bruto (por rota)</h3>
        <p>
            <span style="color: #00e676; font-weight: bold;">✅ NOVA METODOLOGIA IMPLEMENTADA</span>
        </p>
        <p>
            Diferentemente do modelo anterior, agora o desconto de <b>10% sobre as passagens</b> é aplicado 
            diretamente no <b>custo bruto de CADA ROTA individualmente</b>. Ou seja:
        </p>
        <ul>
            <li><b>Custo bruto 7 Lagoas</b> → reduzido em <b>10% das passagens da 7 Lagoas</b></li>
            <li><b>Custo bruto Curvelo</b> → reduzido em <b>10% das passagens do Curvelo</b></li>
        </ul>
        <p>
            Isso torna o cálculo mais justo e vinculado à realidade operacional de cada rota:
            quem arrecada mais em passagens contribui mais para reduzir seu próprio custo.
        </p>
        
        <h3>2. Distribuição do Auxílio Proporcional ao Custo Ajustado</h3>
        <p>
            Após o abatimento dos 10% das passagens, temos o <b>custo bruto ajustado</b> de cada rota.
            O auxílio total é então distribuído <b>proporcionalmente ao custo bruto ajustado</b> de cada rota.
        </p>
        <p>
            Isso garante que rotas com maior custo operacional (mais veículos, mais diárias, 
            maior distância) recebam uma parcela maior do auxílio, independentemente da arrecadação 
            de passagens.
        </p>
        
        <h3>3. Regra de Compensação 70% / 30% (ajuste fino por diárias)</h3>
        <p>
            Após a distribuição proporcional, aplica-se um <b>ajuste fino</b> baseado nas diárias rodadas:
        </p>
        <ul>
            <li>A rota que rodou <b>mais diárias</b> recebe um acréscimo de <b>20% do valor proporcional ao excedente</b>;</li>
            <li>A rota que rodou <b>menos diárias</b> tem esse mesmo valor deduzido do seu auxílio.</li>
        </ul>
        <p>
            Isso corresponde à regra 70/30 sobre as diárias excedentes, mas aplicada como ajuste 
            sobre a distribuição baseada no custo.
        </p>
        
        <h3>4. Exemplo Prático</h3>
        <p>
            <b>Rota 7 Lagoas:</b> Bruto R$ 10.000 | Passagens R$ 2.000 → Abate 10%: R$ 200 → Bruto ajustado: R$ 9.800<br>
            <b>Rota Curvelo:</b> Bruto R$ 8.000 | Passagens R$ 1.000 → Abate 10%: R$ 100 → Bruto ajustado: R$ 7.900<br>
            <b>Auxílio total:</b> R$ 5.000<br>
            <b>Distribuição proporcional:</b> 7L: R$ 5.000 × (9.800 / 17.700) = R$ 2.768 | Curvelo: R$ 2.232<br>
            <b>Ajuste por diárias:</b> Se 7L rodou 5 dias a mais que Curvelo, o sistema aplica automaticamente o ajuste de 20% sobre o excedente.
        </p>
        
        <h3>5. Líquido, Alunos Equivalentes e Mensalidade</h3>
        <p>
            O <b>Líquido final</b> de cada rota é obtido subtraindo o auxílio recebido do custo bruto ajustado.
            Este valor é então dividido pelos <b>alunos equivalentes</b> (integrais = 1,0; descontos = proporcional),
            gerando a <b>mensalidade base</b> por aluno equivalente.
        </p>
        
        <h3>6. Benefícios da Nova Metodologia</h3>
        <ul>
            <li><b>✅ Justiça tributária:</b> quem arrecada mais passagens paga mais para reduzir seu próprio custo;</li>
            <li><b>✅ Proporcionalidade real:</b> o auxílio é distribuído onde o custo é maior;</li>
            <li><b>✅ Equilíbrio operacional:</b> ajuste 70/30 compensa esforço de quem roda mais diárias;</li>
            <li><b>✅ Transparência total:</b> todos os cálculos são claros e auditáveis;</li>
            <li><b>✅ Profissionalismo:</b> relatório PDF com QR Code e todos os detalhes;</li>
            <li><b>✅ Efeito visual:</b> balões comemorativos ao finalizar o cálculo!</li>
        </ul>
    </div>
    """, unsafe_allow_html=True)

# ============================================================
# PÁGINA 2 — CADASTRO E CÁLCULO
# ============================================================
if pagina == "🧮 Cadastro e Cálculo":
    st.markdown("<h1>Cadastro e Cálculo</h1>", unsafe_allow_html=True)
    st.markdown("### 🗓️ Mês de referência")
    mes_ref = st.text_input("Identificação do período (ex: Janeiro/2025, Março/2025)")
    st.markdown("<div class='divider'></div>", unsafe_allow_html=True)

    colA, colB = st.columns(2)
    with colA:
        with st.expander("🟦 Rota 7 Lagoas - dados completos", expanded=False):
            st.markdown('<div class="elevated-card">', unsafe_allow_html=True)
            st.markdown("**🚛 Veículos e diárias rodadas**")
            veic_7l = {}
            qtd_7l = st.number_input("Quantos tipos de veículos? (7L)", min_value=0, step=1, key="qtd_7l")
            for i in range(qtd_7l):
                tipo = st.text_input(f"Tipo do veículo {i+1}", key=f"t7{i}")
                valor = st.number_input(f"Valor da diária ({tipo if tipo else '...'})", min_value=0.0, step=10.0, key=f"v7{i}")
                dias = st.number_input(f"Diárias rodadas ({tipo if tipo else '...'})", min_value=0, step=1, key=f"d7{i}")
                if tipo:
                    veic_7l[tipo] = {"valor": valor, "dias": dias}
            st.markdown("---")
            pass_7l = st.number_input("💰 Passagens arrecadadas (7L):", min_value=0.0, step=10.0)
            int_7l = st.number_input("👤 Alunos integrais (7L):", min_value=0, step=1)
            st.markdown("**🎯 Descontos aplicados**")
            desc_7l = {}
            qtd_desc_7l = st.number_input("Quantas faixas de desconto? (7L)", min_value=0, step=1, key="qtd_desc_7l")
            for i in range(qtd_desc_7l):
                col_p, col_q = st.columns(2)
                with col_p:
                    pct = st.number_input(f"Desconto {i+1} (%)", min_value=0, max_value=100, step=5, key=f"p7{i}")
                with col_q:
                    qtd = st.number_input(f"Quantidade ({pct}%)", min_value=0, step=1, key=f"q7{i}")
                if qtd > 0 and pct > 0:
                    desc_7l[pct] = qtd
            st.markdown("---")
            st.markdown("**⚙️ Dados operacionais adicionais**")
            veic_qtd_sete = st.number_input("Nº total de veículos na rota (7L)", min_value=0, step=1, key="veic_sete")
            diaria_motorista_sete = st.number_input("Diárias de motoristas (R$) - 7L", min_value=0.0, step=10.0, key="diaria_sete")
            custo_extra_sete = st.number_input("Custos extras (manutenção, pedágio, etc.) - 7L", min_value=0.0, step=10.0, key="custo_extra_sete")
            st.markdown('</div>', unsafe_allow_html=True)
    
    with colB:
        with st.expander("🟩 Rota Curvelo - dados completos", expanded=False):
            st.markdown('<div class="elevated-card">', unsafe_allow_html=True)
            st.markdown("**🚛 Veículos e diárias rodadas**")
            veic_cur = {}
            qtd_cur = st.number_input("Quantos tipos de veículos? (Curvelo)", min_value=0, step=1, key="qtd_cur")
            for i in range(qtd_cur):
                tipo = st.text_input(f"Tipo do veículo {i+1}", key=f"tc{i}")
                valor = st.number_input(f"Valor da diária ({tipo if tipo else '...'})", min_value=0.0, step=10.0, key=f"vc{i}")
                dias = st.number_input(f"Diárias rodadas ({tipo if tipo else '...'})", min_value=0, step=1, key=f"dc{i}")
                if tipo:
                    veic_cur[tipo] = {"valor": valor, "dias": dias}
            st.markdown("---")
            pass_cur = st.number_input("💰 Passagens arrecadadas (Curvelo):", min_value=0.0, step=10.0)
            int_cur = st.number_input("👤 Alunos integrais (Curvelo):", min_value=0, step=1)
            st.markdown("**🎯 Descontos aplicados**")
            desc_cur = {}
            qtd_desc_cur = st.number_input("Quantas faixas de desconto? (Curvelo)", min_value=0, step=1, key="qtd_desc_cur")
            for i in range(qtd_desc_cur):
                col_p, col_q = st.columns(2)
                with col_p:
                    pct = st.number_input(f"Desconto {i+1} (%)", min_value=0, max_value=100, step=5, key=f"pc{i}")
                with col_q:
                    qtd = st.number_input(f"Quantidade ({pct}%)", min_value=0, step=1, key=f"qc{i}")
                if qtd > 0 and pct > 0:
                    desc_cur[pct] = qtd
            st.markdown("---")
            st.markdown("**⚙️ Dados operacionais adicionais**")
            veic_qtd_cur = st.number_input("Nº total de veículos na rota (Curvelo)", min_value=0, step=1, key="veic_cur")
            diaria_motorista_cur = st.number_input("Diárias de motoristas (R$) - Curvelo", min_value=0.0, step=10.0, key="diaria_cur")
            custo_extra_cur = st.number_input("Custos extras (manutenção, pedágio, etc.) - Curvelo", min_value=0.0, step=10.0, key="custo_extra_cur")
            st.markdown('</div>', unsafe_allow_html=True)

    st.markdown('<div class="calc-card">', unsafe_allow_html=True)
    st.markdown("## ⚙️ Processar Resultados do Mês")
    aux_total = st.number_input("Auxílio total do mês (R$):", min_value=0.0, step=100.0)
    obs_gerais = st.text_area("📝 Observações gerais do mês (opcional)", placeholder="Registre aqui qualquer informação relevante...")

    if st.button("🔍 CALCULAR E GERAR RESULTADOS"):
        bruto_7l = calcular_bruto(veic_7l)
        bruto_cur = calcular_bruto(veic_cur)
        diarias_7l = sum(v["dias"] for v in veic_7l.values())
        diarias_cur = sum(v["dias"] for v in veic_cur.values())
        bruto_aj_7l = max(0, bruto_7l - (0.10 * pass_7l))
        bruto_aj_cur = max(0, bruto_cur - (0.10 * pass_cur))
        aux_7l, aux_cur = distribuir_auxilio_por_diarias(aux_total, bruto_aj_7l, bruto_aj_cur, diarias_7l, diarias_cur)
        al_eq_7l = alunos_equivalentes(int_7l, desc_7l)
        al_eq_cur = alunos_equivalentes(int_cur, desc_cur)
        liquido_7l = bruto_aj_7l - aux_7l
        liquido_cur = bruto_aj_cur - aux_cur
        mensal_7l = liquido_7l / al_eq_7l if al_eq_7l > 0 else 0.0
        mensal_cur = liquido_cur / al_eq_cur if al_eq_cur > 0 else 0.0
        
        st.session_state["resultados"] = {
            "mes_ref": mes_ref, "aux_total": aux_total, "obs_gerais": obs_gerais,
            "bruto_7l": bruto_7l, "pass_7l": pass_7l, "bruto_aj_7l": bruto_aj_7l,
            "aux_ideal_7l": aux_7l, "liquido_7l": liquido_7l, "int_7l": int_7l,
            "desc_7l": desc_7l, "al_eq_7l": al_eq_7l, "mensal_7l": mensal_7l,
            "diarias_7l": diarias_7l, "veic_sete": veic_qtd_sete,
            "diaria_sete": diaria_motorista_sete, "custo_extra_sete": custo_extra_sete,
            "bruto_cur": bruto_cur, "pass_cur": pass_cur, "bruto_aj_cur": bruto_aj_cur,
            "aux_ideal_cur": aux_cur, "liquido_cur": liquido_cur, "int_cur": int_cur,
            "desc_cur": desc_cur, "al_eq_cur": al_eq_cur, "mensal_cur": mensal_cur,
            "diarias_cur": diarias_cur, "veic_cur": veic_qtd_cur,
            "diaria_cur": diaria_motorista_cur, "custo_extra_cur": custo_extra_cur,
        }
        st.success("✅ Cálculo realizado com a NOVA METODOLOGIA! Acesse a aba 'Relatórios e Gráficos'.")
        st.balloons()
    st.markdown('</div>', unsafe_allow_html=True)

# ============================================================
# PÁGINA 3 — RELATÓRIOS E GRÁFICOS (COMPLETA)
# ============================================================
if pagina == "📊 Relatórios e Gráficos":
    st.markdown("<h1>Relatórios e Análises Visuais</h1>", unsafe_allow_html=True)
    
    if "resultados" not in st.session_state:
        st.warning("Nenhum cálculo encontrado. Volte à aba 'Cadastro e Cálculo' e processe os dados.")
    else:
        r = st.session_state["resultados"]
        
        # MÉTRICAS
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            st.markdown('<div class="metric-card">', unsafe_allow_html=True)
            st.markdown('<div class="metric-label">Auxílio total</div>', unsafe_allow_html=True)
            st.markdown(f'<div class="metric-value">R$ {r["aux_total"]:,.2f}</div>', unsafe_allow_html=True)
            st.markdown(f'<div class="metric-sub">{r.get("mes_ref", "Mês atual")}</div>', unsafe_allow_html=True)
            st.markdown('</div>', unsafe_allow_html=True)
        with col2:
            total_aux_dist = r["aux_ideal_7l"] + r["aux_ideal_cur"]
            st.markdown('<div class="metric-card">', unsafe_allow_html=True)
            st.markdown('<div class="metric-label">Auxílio distribuído</div>', unsafe_allow_html=True)
            st.markdown(f'<div class="metric-value">R$ {total_aux_dist:,.2f}</div>', unsafe_allow_html=True)
            st.markdown('<div class="metric-sub">100% do total</div>', unsafe_allow_html=True)
            st.markdown('</div>', unsafe_allow_html=True)
        with col3:
            total_pass = r["pass_7l"] + r["pass_cur"]
            st.markdown('<div class="metric-card">', unsafe_allow_html=True)
            st.markdown('<div class="metric-label">Passagens totais</div>', unsafe_allow_html=True)
            st.markdown(f'<div class="metric-value">R$ {total_pass:,.2f}</div>', unsafe_allow_html=True)
            st.markdown('<div class="metric-sub">10% abatido no bruto</div>', unsafe_allow_html=True)
            st.markdown('</div>', unsafe_allow_html=True)
        with col4:
            total_liquido = r["liquido_7l"] + r["liquido_cur"]
            st.markdown('<div class="metric-card">', unsafe_allow_html=True)
            st.markdown('<div class="metric-label">Líquido total</div>', unsafe_allow_html=True)
            st.markdown(f'<div class="metric-value">R$ {total_liquido:,.2f}</div>', unsafe_allow_html=True)
            st.markdown('<div class="metric-sub">a ratear entre alunos</div>', unsafe_allow_html=True)
            st.markdown('</div>', unsafe_allow_html=True)
        
        st.markdown('<div class="divider"></div>', unsafe_allow_html=True)
        
        # GRÁFICO 1 - DISTRIBUIÇÃO DO AUXÍLIO
        st.markdown("### 📊 Distribuição do Auxílio entre as Rotas")
        aux_data = pd.DataFrame([
            {"Rota": "7 Lagoas", "Auxílio": r["aux_ideal_7l"]},
            {"Rota": "Curvelo", "Auxílio": r["aux_ideal_cur"]},
        ])
        soma_aux = aux_data["Auxílio"].sum()
        if soma_aux > 0:
            aux_data["Percentual"] = aux_data["Auxílio"] / soma_aux * 100
        else:
            aux_data["Percentual"] = 0.0
        chart_aux = alt.Chart(aux_data).mark_arc(outerRadius=110).encode(
            theta=alt.Theta(field="Auxílio", type="quantitative"),
            color=alt.Color("Rota", scale=alt.Scale(range=["#00e676", "#40c4ff"])),
            tooltip=[
                alt.Tooltip("Rota", title="Rota"),
                alt.Tooltip("Auxílio", title="Auxílio (R$)", format=",.2f"),
                alt.Tooltip("Percentual", title="% do total", format=".2f")
            ]
        ).properties(width=380, height=320, title="Participação no auxílio")
        colA, colB = st.columns(2)
        with colA:
            st.altair_chart(chart_aux, use_container_width=True)
        with colB:
            st.markdown("""
            <div class="elevated-card">
                <div class="section-title">Interpretação</div>
                <p>Este gráfico mostra a <b>porcentagem do auxílio</b> que cada rota recebe.</p>
            </div>
            """, unsafe_allow_html=True)
        
        st.markdown('<div class="divider"></div>', unsafe_allow_html=True)
        
        # GRÁFICO 2 - PASSAGENS
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
        ).properties(width=420, height=320, title="Passagens por rota")
        colC, colD = st.columns(2)
        with colC:
            st.altair_chart(chart_pass, use_container_width=True)
        with colD:
            st.markdown("""
            <div class="elevated-card">
                <div class="section-title">Detalhe operacional</div>
                <p><strong>10% das passagens</strong> de cada rota são abatidos diretamente do seu custo bruto.</p>
            </div>
            """, unsafe_allow_html=True)
        
        st.markdown('<div class="divider"></div>', unsafe_allow_html=True)
        
        # GRÁFICO 3 - ALUNOS
        st.markdown("### 👥 Alunos Integrais vs Equivalentes")
        alunos_data = pd.DataFrame([
            {"Rota": "7 Lagoas", "Tipo": "Integrais", "Quantidade": r["int_7l"]},
            {"Rota": "7 Lagoas", "Tipo": "Equivalentes", "Quantidade": round(r["al_eq_7l"], 1)},
            {"Rota": "Curvelo", "Tipo": "Integrais", "Quantidade": r["int_cur"]},
            {"Rota": "Curvelo", "Tipo": "Equivalentes", "Quantidade": round(r["al_eq_cur"], 1)},
        ])
        chart_alunos = alt.Chart(alunos_data).mark_bar().encode(
            x=alt.X("Rota:N", title="Rota"),
            y=alt.Y("Quantidade:Q", title="Quantidade"),
            color=alt.Color("Tipo:N", scale=alt.Scale(range=["#00e676", "#ffb300"])),
            column=alt.Column("Tipo:N", title="")
        ).properties(width=200, height=300)
        st.altair_chart(chart_alunos, use_container_width=True)
        
        st.markdown('<div class="divider"></div>', unsafe_allow_html=True)
        
        # RESUMO OPERACIONAL
        st.markdown("### 🚌 Resumo Operacional do Mês")
        col_op1, col_op2, col_op3 = st.columns(3)
        with col_op1:
            st.markdown(f"**Mês:** {r.get('mes_ref', 'Não informado')}")
            st.markdown(f"**Diárias 7L:** {r['diarias_7l']} dias")
            st.markdown(f"**Diárias Curvelo:** {r['diarias_cur']} dias")
        with col_op2:
            st.markdown(f"**Veículos 7L:** {r.get('veic_sete', 0)}")
            st.markdown(f"**Diárias motoristas 7L:** R$ {r.get('diaria_sete', 0):,.2f}")
            st.markdown(f"**Custos extras 7L:** R$ {r.get('custo_extra_sete', 0):,.2f}")
        with col_op3:
            st.markdown(f"**Veículos Curvelo:** {r.get('veic_cur', 0)}")
            st.markdown(f"**Diárias motoristas Curvelo:** R$ {r.get('diaria_cur', 0):,.2f}")
            st.markdown(f"**Custos extras Curvelo:** R$ {r.get('custo_extra_cur', 0):,.2f}")
        
        st.markdown("#### 📋 Observações")
        st.info(r.get('obs_gerais', 'Nenhuma observação registrada.'))
        
        st.markdown('<div class="divider"></div>', unsafe_allow_html=True)
        
        # DOWNLOAD PDF
        st.markdown("### 📄 Relatório Profissional em PDF")
        if st.button("📥 Gerar PDF do Relatório"):
            try:
                with st.spinner("Gerando PDF..."):
                    pdf_bytes = gerar_pdf_profissional(r)
                st.download_button(
                    label="⬇️ Clique para baixar o PDF",
                    data=pdf_bytes,
                    file_name=f"relatorio_asseuf_{r.get('mes_ref', 'sem_mes').replace('/', '_')}.pdf",
                    mime="application/pdf"
                )
                st.success("✅ PDF gerado com sucesso!")
            except Exception as e:
                st.error(f"Erro ao gerar PDF: {e}")
                st.warning("""
                **Dica para deploy no Render:**  
                Adicione um arquivo `aptfile` na raiz com:
                ```
                libpango-1.0-0
                libpangoft2-1.0-0
                libcairo2
                libffi-dev
                shared-mime-info
                ```
                """)
        
        # DOWNLOAD TXT
        with st.expander("📁 Baixar relatório em texto simples"):
            relatorio_txt = f"""
=========================================
RELATÓRIO ASSEUF - ROTAS 7 LAGOAS E CURVELO
=========================================
Mês: {r.get('mes_ref', 'Não informado')}
Auxílio total: R$ {r['aux_total']:,.2f}

ROTA 7 LAGOAS
-----------------------------------------
Custo bruto: R$ {r['bruto_7l']:,.2f}
Passagens: R$ {r['pass_7l']:,.2f}
(-10%): R$ {r['pass_7l'] * 0.1:,.2f}
Custo ajustado: R$ {r['bruto_aj_7l']:,.2f}
Auxílio: R$ {r['aux_ideal_7l']:,.2f}
Líquido: R$ {r['liquido_7l']:,.2f}
Mensalidade: R$ {r['mensal_7l']:,.2f}

ROTA CURVELO
-----------------------------------------
Custo bruto: R$ {r['bruto_cur']:,.2f}
Passagens: R$ {r['pass_cur']:,.2f}
(-10%): R$ {r['pass_cur'] * 0.1:,.2f}
Custo ajustado: R$ {r['bruto_aj_cur']:,.2f}
Auxílio: R$ {r['aux_ideal_cur']:,.2f}
Líquido: R$ {r['liquido_cur']:,.2f}
Mensalidade: R$ {r['mensal_cur']:,.2f}
            """
            st.download_button(
                label="📄 Baixar .txt",
                data=relatorio_txt,
                file_name=f"relatorio_asseuf_{r.get('mes_ref', 'sem_mes').replace('/', '_')}.txt"
            )
        
        st.markdown("""
        <div class="elevated-card" style="margin-top: 30px;">
            <div class="section-title">✅ SISTEMA FUNCIONANDO</div>
            <p style="color: #00e676; text-align: center; font-size: 1.2rem;">
                NOVA METODOLOGIA DOS 10% POR ROTA IMPLEMENTADA!
            </p>
        </div>
        """, unsafe_allow_html=True)