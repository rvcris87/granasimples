from flask import Blueprint, render_template, request, session
from decorators import login_required
from utils import calcular_dados_dashboard, buscar_categorias
from db import conectar

dashboard_bp = Blueprint("dashboard", __name__)


@dashboard_bp.route("/app")
@login_required
def app_dashboard():
    usuario_id = session["usuario_id"]
    mes = request.args.get("mes", "").strip()

    dados = calcular_dados_dashboard(usuario_id, mes)
    categorias = buscar_categorias(usuario_id)


    return render_template(
        "index.html",
        nome=session.get("usuario_nome", "Usuário"),
        transacoes=dados["transacoes"],
        metas=dados["metas"],
        total_entradas=dados["total_entradas"],
        total_saidas=dados["total_saidas"],
        saldo=dados["saldo"],
        categorias_labels=dados["categorias_labels"],
        categorias_valores=dados["categorias_valores"],
        categorias=categorias,
        insights=dados["insights"],
        mes=mes,
        mensagem=request.args.get("mensagem", ""),
        erro=request.args.get("erro", "")
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