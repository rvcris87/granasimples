import os
import logging
from flask import Blueprint, render_template, request, session, redirect, url_for, abort
from decorators import login_required
from utils import (
    calcular_dados_dashboard, 
    buscar_categorias,
    calcular_tendencia_6_meses,
    calcular_previsao_gastos,
    calcular_alertas_metas,
    buscar_gastos_fixos,
    calcular_insights_gastos_fixos,
    verificar_lancamentos_pendentes,
    parse_mes
)
from db import conectar

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

dashboard_bp = Blueprint("dashboard", __name__)


@dashboard_bp.route("/app")
@login_required
def app_dashboard():
    usuario_id = session["usuario_id"]
    mes = request.args.get("mes", "").strip()

    if mes:
        try:
            parse_mes(mes)
        except ValueError:
            # Mensagem genérica para o usuário
            return render_template(
                "erro.html",
                codigo=400,
                titulo="Filtro inválido",
                mensagem="O filtro de mês fornecido é inválido. Use o seletor de mês."
            ), 400

    conn = None
    try:
        conn = conectar()
        conn.autocommit = True

        dados = calcular_dados_dashboard(usuario_id, mes, conn=conn)
        categorias = buscar_categorias(usuario_id, conn=conn) or []
        tendencia = calcular_tendencia_6_meses(usuario_id, conn=conn) or {"labels": [], "entradas": [], "saidas": [], "saldo": []}
        previsao = calcular_previsao_gastos(usuario_id, conn=conn) or {"valor": 0, "mensagem": ""}
        alertas_metas = calcular_alertas_metas(usuario_id, conn=conn) or []
        gastos_fixos = buscar_gastos_fixos(usuario_id, conn=conn) or []
        insights_gastos_fixos = calcular_insights_gastos_fixos(usuario_id, dados["total_saidas"], conn=conn)
        lancamentos_pendentes = verificar_lancamentos_pendentes(usuario_id, conn=conn) or {"possui_pendentes": False, "quantidade": 0, "mensagem": ""}

    except Exception as e:
        logger.exception(f"Erro ao carregar dashboard para usuário {usuario_id}: {e}")
        return render_template(
            "erro.html",
            codigo=500,
            titulo="Erro ao carregar dados",
            mensagem="Não foi possível carregar os dados do dashboard. Tente novamente em alguns instantes."
        ), 500
    finally:
        if conn:
            conn.close()

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
@login_required
def teste_banco():
    if os.getenv("FLASK_ENV", "").lower() == "production":
        abort(404)

    conn = None
    try:
        conn = conectar()
        cur = conn.cursor()
        cur.execute("SELECT 1 AS teste")
        resultado = cur.fetchone()
        return f"Teste de conexão: {resultado['teste']}"
    except Exception as e:
        logger.exception(f"Erro ao testar conexão: {e}")
        return "Erro ao conectar ao banco. Verifique os logs.", 500
    finally:
        if conn:
            conn.close()
