from flask import Blueprint, render_template, request, session
from decorators import login_required
from utils import (
    calcular_dados_dashboard, 
    buscar_categorias,
    calcular_tendencia_6_meses,
    calcular_previsao_gastos,
    calcular_alertas_metas,
    buscar_gastos_fixos,
    calcular_insights_gastos_fixos,
    verificar_lancamentos_pendentes
)
from db import conectar

dashboard_bp = Blueprint("dashboard", __name__)


@dashboard_bp.route("/app")
@login_required
def app_dashboard():
    usuario_id = session["usuario_id"]
    mes = request.args.get("mes", "").strip()

    try:
        dados = calcular_dados_dashboard(usuario_id, mes)
    except Exception as e:
        print(f"Erro em calcular_dados_dashboard: {str(e)}")
        dados = {
            "transacoes": [],
            "metas": [],
            "total_entradas": 0,
            "total_saidas": 0,
            "saldo": 0,
            "categorias_labels": [],
            "categorias_valores": [],
            "insights": ["Erro ao carregar dados. Tente novamente."],
            "comparacao_percentual": 0,
            "mensagem_comparacao": "",
            "maior_categoria": "",
            "maior_valor": 0,
            "alertas": []
        }
    
    try:
        categorias = buscar_categorias(usuario_id) or []
    except Exception as e:
        print(f"Erro em buscar_categorias: {str(e)}")
        categorias = []
    
    try:
        tendencia = calcular_tendencia_6_meses(usuario_id) or {"labels": [], "entradas": [], "saidas": [], "saldo": []}
    except Exception as e:
        print(f"Erro em calcular_tendencia_6_meses: {str(e)}")
        tendencia = {"labels": [], "entradas": [], "saidas": [], "saldo": []}
    
    try:
        previsao = calcular_previsao_gastos(usuario_id) or {"valor": 0, "mensagem": ""}
    except Exception as e:
        print(f"Erro em calcular_previsao_gastos: {str(e)}")
        previsao = {"valor": 0, "mensagem": ""}
    
    try:
        alertas_metas = calcular_alertas_metas(usuario_id) or []
    except Exception as e:
        print(f"Erro em calcular_alertas_metas: {str(e)}")
        alertas_metas = []
    
    try:
        gastos_fixos = buscar_gastos_fixos(usuario_id) or []
    except Exception as e:
        print(f"Erro em buscar_gastos_fixos: {str(e)}")
        gastos_fixos = []
    
    try:
        insights_gastos_fixos = calcular_insights_gastos_fixos(usuario_id, dados["total_saidas"])
    except Exception as e:
        print(f"Erro em calcular_insights_gastos_fixos: {str(e)}")
        insights_gastos_fixos = {
            "total_gastos_fixos": 0,
            "quantidade_gastos_fixos": 0,
            "percentual_gastos_fixos": 0,
            "maior_categoria_gasto_fixo": "",
            "mensagem_gastos_fixos": "Erro ao carregar gastos fixos",
            "alertas_gastos_fixos": []
        }
    
    try:
        lancamentos_pendentes = verificar_lancamentos_pendentes(usuario_id) or {"possui_pendentes": False, "quantidade": 0, "mensagem": ""}
    except Exception as e:
        print(f"Erro em verificar_lancamentos_pendentes: {str(e)}")
        lancamentos_pendentes = {"possui_pendentes": False, "quantidade": 0, "mensagem": ""}

    return render_template(
        "index.html",
        nome=session.get("usuario_nome", "Usuário"),
        transacoes=dados.get("transacoes", []),
        metas=dados.get("metas", []),
        total_entradas=float(dados.get("total_entradas", 0) or 0),
        total_saidas=float(dados.get("total_saidas", 0) or 0),
        saldo=float(dados.get("saldo", 0) or 0),
        categorias_labels=dados.get("categorias_labels", []),
        categorias_valores=dados.get("categorias_valores", []),
        categorias=categorias,
        insights=dados.get("insights", []),
        comparacao_percentual=float(dados.get("comparacao_percentual", 0) or 0),
        mensagem_comparacao=dados.get("mensagem_comparacao", ""),
        maior_categoria=dados.get("maior_categoria", ""),
        maior_valor=float(dados.get("maior_valor", 0) or 0),
        alertas=dados.get("alertas", []),
        tendencia_labels=tendencia.get("labels", []),
        tendencia_entradas=tendencia.get("entradas", []),
        tendencia_saidas=tendencia.get("saidas", []),
        tendencia_saldo=tendencia.get("saldo", []),
        previsao_valor=float(previsao.get("valor", 0) or 0),
        previsao_mensagem=previsao.get("mensagem", ""),
        alertas_metas=alertas_metas,
        gastos_fixos=gastos_fixos,
        total_gastos_fixos=float(insights_gastos_fixos.get("total_gastos_fixos", 0) or 0),
        percentual_gastos_fixos=float(insights_gastos_fixos.get("percentual_gastos_fixos", 0) or 0),
        mensagem_gastos_fixos=insights_gastos_fixos.get("mensagem_gastos_fixos", ""),
        alertas_gastos_fixos=insights_gastos_fixos.get("alertas_gastos_fixos", []),
        lancamentos_pendentes=lancamentos_pendentes,
        mes=mes
    )


@dashboard_bp.route("/teste-banco")
def teste_banco():
    try:
        conn = conectar()
        cur = conn.cursor()
        cur.execute("SELECT 1 AS teste")
        resultado = cur.fetchone()
        conn.close()
        return f"Teste de conexão: {resultado['teste']}"
    except Exception as e:
        return f"Erro ao conectar ao banco: {str(e)}"