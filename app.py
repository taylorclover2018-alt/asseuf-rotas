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

def distribuir_auxilio_por_diarias(aux_total: float, bruto_aj_7l: float, bruto_aj_cur: float, d7: int, dC: int):
    """
    Divide o auxílio entre as rotas considerando:
    - O auxílio é distribuído proporcionalmente ao BRUTO AJUSTADO de cada rota
    - Bruto ajustado = bruto original - 10% das passagens da própria rota
    - Regra 70/30 aplicada sobre as diárias para ajuste fino
    """
    # Se não há diárias ou bruto, retorna zero
    if d7 == 0 and dC == 0:
        return 0.0, 0.0
    
    # Cálculo da proporção baseada no bruto ajustado
    total_bruto_aj = bruto_aj_7l + bruto_aj_cur
    
    if total_bruto_aj <= 0:
        return 0.0, 0.0
    
    # Distribuição proporcional ao bruto ajustado
    aux_7l_proporcional = aux_total * (bruto_aj_7l / total_bruto_aj)
    aux_cur_proporcional = aux_total * (bruto_aj_cur / total_bruto_aj)
    
    # Aplicar regra 70/30 para ajuste fino baseado nas diárias
    if d7 > dC and dC > 0:
        excedente = d7 - dC
        base = dC
        total_base = base * 2 + excedente
        
        # Ajuste fino: redistribuir 20% do excedente (70% - 50% = 20%)
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
        # Diárias iguais: mantém a proporção do bruto ajustado
        aux_7l = aux_7l_proporcional
        aux_cur = aux_cur_proporcional
    
    # Garantir que não fique negativo
    aux_7l = max(0, aux_7l)
    aux_cur = max(0, aux_cur)
    
    # Rebalancear para somar exatamente o aux_total
    soma = aux_7l + aux_cur
    if soma > 0:
        fator_ajuste = aux_total / soma
        aux_7l *= fator_ajuste
        aux_cur *= fator_ajuste
    
    return aux_7l, aux_cur

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
    qr_b64 = gerar_qr_base64(f"Relatório ASSEUF - {r.get('mes_ref', 'Mês atual')}")

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
                <th>7 Lagoas</th>
                <th>Curvelo</th>
                <th>Total</th>
            </tr>
            <tr>
                <td>Custo bruto original</td>
                <td>R$ {r["bruto_7l"]:,.2f}</td>
                <td>R$ {r["bruto_cur"]:,.2f}</td>
                <td>R$ {r["bruto_7l"] + r["bruto_cur"]:,.2f}</td>
            </tr>
            <tr>
                <td>(-) 10% das passagens (própria rota)</td>
                <td>R$ {r["pass_7l"] * 0.1:,.2f}</td>
                <td>R$ {r["pass_cur"] * 0.1:,.2f}</td>
                <td>R$ {(r["pass_7l"] + r["pass_cur"]) * 0.1:,.2f}</td>
            </tr>
            <tr>
                <td><strong>Custo bruto ajustado</strong></td>
                <td><strong>R$ {r["bruto_aj_7l"]:,.2f}</strong></td>
                <td><strong>R$ {r["bruto_aj_cur"]:,.2f}</strong></td>
                <td><strong>R$ {r["bruto_aj_7l"] + r["bruto_aj_cur"]:,.2f}</strong></td>
            </tr>
            <tr>
                <td>Auxílio recebido</td>
                <td>R$ {r["aux_ideal_7l"]:,.2f}</td>
                <td>R$ {r["aux_ideal_cur"]:,.2f}</td>
                <td>R$ {r["aux_ideal_7l"] + r["aux_ideal_cur"]:,.2f}</td>
            </tr>
            <tr>
                <td><strong>Líquido final (custo - auxílio)</strong></td>
                <td><strong>R$ {r["liquido_7l"]:,.2f}</strong></td>
                <td><strong>R$ {r["liquido_cur"]:,.2f}</strong></td>
                <td><strong>R$ {r["liquido_7l"] + r["liquido_cur"]:,.2f}</strong></td>
            </tr>
        </table>

        <h2>Alunos e Mensalidades</h2>
        <table>
            <tr>
                <th>Rota</th>
                <th>Alunos integrais</th>
                <th>Alunos equivalentes</th>
                <th>Mensalidade calculada</th>
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
        
        <h3>Dados Operacionais</h3>
        <table>
            <tr>
                <th>Rota</th>
                <th>Diárias rodadas</th>
                <th>Veículos</th>
            </tr>
            <tr>
                <td>7 Lagoas</td>
                <td>{r["diarias_7l"]} dias</td>
                <td>{r.get("veic_sete", 0)}</td>
            </tr>
            <tr>
                <td>Curvelo</td>
                <td>{r["diarias_cur"]} dias</td>
                <td>{r.get("veic_cur", 0)}</td>
            </tr>
        </table>

        <h3 class="section-title">Observações</h3>
        <p class="small">
            {r.get('obs_gerais', 'Nenhuma observação registrada.')}
        </p>
        <p class="small">
            <strong>Metodologia aplicada:</strong> O custo bruto de cada rota é reduzido em 10% do valor das 
            passagens arrecadadas pela própria rota. O auxílio total é distribuído proporcionalmente ao 
            custo bruto ajustado de cada rota, com ajuste fino de 70/30 baseado na diferença de diárias 
            rodadas. A mensalidade por aluno equivalente é calculada dividindo o líquido final 
            (custo bruto ajustado - auxílio recebido) pelo total de alunos equivalentes.
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
# PÁGINA 1 — INÍCIO (COM DESCRIÇÃO CORRIGIDA E COMPLETA)
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
            <b>Ajuste por diárias:</b> Se 7L rodou 5 dias a mais que Curvelo, o cálculo do ajuste fino é aplicado automaticamente pelo sistema.
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
            <li><b>✅ Profissionalismo:</b> relatório PDF com QR Code e todos os detalhes.</li>
        </ul>
    </div>
    """, unsafe_allow_html=True)

# ============================================================
# PÁGINA 2 — CADASTRO E CÁLCULO (COM CAMPOS EXTRAS)
# ============================================================
if pagina == "🧮 Cadastro e Cálculo":
    st.markdown("<h1>Cadastro e Cálculo</h1>", unsafe_allow_html=True)
    
    # ---------- MÊS DE REFERÊNCIA ----------
    st.markdown("### 🗓️ Mês de referência")
    mes_ref = st.text_input(
        "Identificação do período (ex: Janeiro/2025, Março/2025)",
        help="Utilize um nome que facilite a identificação do relatório mensal."
    )
    st.markdown("<div class='divider'></div>", unsafe_allow_html=True)

    colA, colB = st.columns(2)

    # ----------------------------
    # CARD 7 LAGOAS (COM CAMPOS EXTRAS)
    # ----------------------------
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

    # ----------------------------
    # CARD CURVELO (COM CAMPOS EXTRAS)
    # ----------------------------
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

    # ----------------------------
    # PROCESSAMENTO (COM NOVA REGRA DOS 10%)
    # ----------------------------
    st.markdown('<div class="calc-card">', unsafe_allow_html=True)
    st.markdown("## ⚙️ Processar Resultados")

    aux_total = st.number_input("Auxílio total do mês:", min_value=0.0, step=100.0)
    obs_gerais = st.text_area(
        "📝 Observações gerais do mês (opcional)",
        placeholder="Registre aqui qualquer informação relevante: feriados, manutenções, eventos especiais..."
    )

    if st.button("🔍 CALCULAR"):
        # Cálculos básicos
        bruto_7l = calcular_bruto(veic_7l)
        bruto_cur = calcular_bruto(veic_cur)

        diarias_7l = sum(v["dias"] for v in veic_7l.values())
        diarias_cur = sum(v["dias"] for v in veic_cur.values())

        # --- NOVA REGRA: abater 10% das passagens do bruto de CADA ROTA ---
        bruto_aj_7l = bruto_7l - (0.10 * pass_7l)
        bruto_aj_cur = bruto_cur - (0.10 * pass_cur)

        # Garantir que o bruto ajustado não seja negativo
        bruto_aj_7l = max(0, bruto_aj_7l)
        bruto_aj_cur = max(0, bruto_aj_cur)

        # Distribuição do auxílio proporcional ao bruto ajustado + ajuste 70/30
        aux_ideal_7l, aux_ideal_cur = distribuir_auxilio_por_diarias(
            aux_total, bruto_aj_7l, bruto_aj_cur, diarias_7l, diarias_cur
        )

        # Alunos equivalentes
        al_eq_7l = alunos_equivalentes(int_7l, desc_7l)
        al_eq_cur = alunos_equivalentes(int_cur, desc_cur)

        # Líquido final = bruto ajustado - auxílio recebido
        liquido_7l = bruto_aj_7l - aux_ideal_7l
        liquido_cur = bruto_aj_cur - aux_ideal_cur

        # Mensalidade por aluno equivalente
        mensal_7l = liquido_7l / al_eq_7l if al_eq_7l > 0 else 0
        mensal_cur = liquido_cur / al_eq_cur if al_eq_cur > 0 else 0

        # ---------- ARMAZENAMENTO EM SESSION_STATE ----------
        st.session_state["resultados"] = {
            # Gerais
            "mes_ref": mes_ref,
            "aux_total": aux_total,
            "obs_gerais": obs_gerais,
            # 7 Lagoas
            "bruto_7l": bruto_7l,
            "pass_7l": pass_7l,
            "bruto_aj_7l": bruto_aj_7l,
            "aux_ideal_7l": aux_ideal_7l,
            "liquido_7l": liquido_7l,
            "int_7l": int_7l,
            "desc_7l": desc_7l,
            "al_eq_7l": al_eq_7l,
            "mensal_7l": mensal_7l,
            "diarias_7l": diarias_7l,
            "veic_sete": veic_qtd_sete,
            "diaria_sete": diaria_motorista_sete,
            "custo_extra_sete": custo_extra_sete,
            # Curvelo
            "bruto_cur": bruto_cur,
            "pass_cur": pass_cur,
            "bruto_aj_cur": bruto_aj_cur,
            "aux_ideal_cur": aux_ideal_cur,
            "liquido_cur": liquido_cur,
            "int_cur": int_cur,
            "desc_cur": desc_cur,
            "al_eq_cur": al_eq_cur,
            "mensal_cur": mensal_cur,
            "diarias_cur": diarias_cur,
            "veic_cur": veic_qtd_cur,
            "diaria_cur": diaria_motorista_cur,
            "custo_extra_cur": custo_extra_cur,
        }

        st.success("✅ Cálculo realizado com a NOVA METODOLOGIA! Vá para a