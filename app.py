# ============================================================
# HISTÓRICO MENSAL (SALVO EM historico.csv)
# ============================================================

import pandas as pd
import os

HIST_PATH = "historico.csv"

def carregar_historico():
    """Carrega o histórico se existir, senão cria um DataFrame vazio."""
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
    """Salva os dados da rota no arquivo historico.csv."""
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
# PÁGINA DE RELATÓRIOS E GRÁFICOS
# ============================================================
if pagina == "📊 Relatórios e Gráficos":

    st.markdown("<h1>📊 Relatórios e Gráficos</h1>", unsafe_allow_html=True)

    # Carrega histórico
    historico = carregar_historico()

    if historico.empty:
        st.warning("Nenhum histórico encontrado. Gere um cálculo primeiro.")
    else:
        st.subheader("📅 Histórico Mensal Registrado")
        st.dataframe(historico)

        # Botão para baixar histórico
        csv_bytes = historico.to_csv(index=False).encode("utf-8")
        st.download_button(
            label="📥 Baixar histórico completo (CSV)",
            data=csv_bytes,
            file_name="historico_rotas.csv",
            mime="text/csv"
        )

        st.divider()

        # ============================
        # GRÁFICO DE EVOLUÇÃO DA MENSALIDADE
        # ============================
        st.subheader("📈 Evolução da Mensalidade por Rota")

        graf_mensal = historico.pivot_table(
            index="mes_ref",
            columns="rota",
            values="mensalidade",
            aggfunc="mean"
        )

        st.line_chart(graf_mensal)

        st.divider()

        # ============================
        # GRÁFICO DE BARRAS (BRUTO / AJUSTADO / AUXÍLIO / FINAL)
        # ============================
        st.subheader("📊 Comparativo Financeiro por Rota")

        if "resultado" in st.session_state:
            r = st.session_state["resultado"]
            s = r["sete"]
            c = r["cur"]

            df_comp = pd.DataFrame({
                "Indicador": [
                    "Bruto", "Bruto Ajustado (10%)", "Auxílio Recebido",
                    "Valor Final (após 90%)"
                ],
                "7 Lagoas": [
                    s["bruto"], s["bruto_aj_10"], s["aux_recebido"], s["valor_final"]
                ],
                "Curvelo": [
                    c["bruto"], c["bruto_aj_10"], c["aux_recebido"], c["valor_final"]
                ]
            })

            st.bar_chart(df_comp.set_index("Indicador"))

        st.divider()

        # ============================
        # GRÁFICO DE PIZZA (ALUNOS EQUIVALENTES)
        # ============================
        st.subheader("🥧 Proporção de Alunos Equivalentes")

        if "resultado" in st.session_state:
            r = st.session_state["resultado"]
            s = r["sete"]
            c = r["cur"]

            df_pizza = pd.DataFrame({
                "Rota": ["7 Lagoas", "Curvelo"],
                "Alunos Equivalentes": [
                    s["alunos_equivalentes"],
                    c["alunos_equivalentes"]
                ]
            })

            fig = {
                "data": [{
                    "values": df_pizza["Alunos Equivalentes"],
                    "labels": df_pizza["Rota"],
                    "type": "pie"
                }],
                "layout": {"height": 400}
            }

            st.plotly_chart(fig, use_container_width=True)
def gerar_pdf_profissional_nova_logica(r: dict) -> bytes:
    # QR Code com resumo
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

    # ============================
    # TOTAIS GERAIS
    # ============================
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

    # ============================
    # HTML DO PDF
    # ============================
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

        <!-- CABEÇALHO -->
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

        <!-- RESUMO FINANCEIRO -->
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

        <!-- ALUNOS -->
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

        <!-- TOTAIS CONSOLIDADOS -->
        <div class="totais">
            <h3>📌 Resumo Consolidado Geral</h3>
            <p><strong>Total de alunos equivalentes:</strong> {total_al_eq:.2f}</p>
            <p><strong>Total de veículos:</strong> {total_veic}</p>
            <p><strong>Total de diárias:</strong> {total_diarias}</p>
            <p><strong>Valor final total:</strong> {fmt_brl(total_final)}</p>
        </div>

        <!-- RODAPÉ -->
        <div class="footer">
            Relatório gerado automaticamente pelo Sistema ASSEUF (nova lógica) em {datetime.now().strftime('%d/%m/%Y às %H:%M')}.<br>
            Metodologia: 10% → auxílio → 90% → alunos equivalentes.
        </div>

    </body>
    </html>
    """

    return HTML(string=html).write_pdf()