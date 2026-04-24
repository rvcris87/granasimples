from flask import Blueprint, request, redirect, url_for, session, flash
from decorators import login_required
from db import conectar
from datetime import datetime, date

gastos_fixos_bp = Blueprint("gastos_fixos", __name__)

@gastos_fixos_bp.route("/add_gasto_fixo", methods=["POST"])
@login_required
def add_gasto_fixo():
    usuario_id = session["usuario_id"]
    descricao = request.form.get("descricao", "").strip()
    valor = request.form.get("valor", "").strip()
    categoria_id = request.form.get("categoria_id", "").strip()
    dia_vencimento = request.form.get("dia_vencimento", "").strip()

    if not descricao or not valor or not dia_vencimento:
        return redirect(url_for("dashboard.app_dashboard", erro="Preencha os campos do gasto fixo."))

    try:
        valor = float(valor)
    except ValueError:
        return redirect(url_for("dashboard.app_dashboard", erro="Valor inválido."))

    if valor <= 0:
        return redirect(url_for("dashboard.app_dashboard", erro="O valor deve ser maior que zero."))

    try:
        dia_vencimento = int(dia_vencimento)
    except ValueError:
        return redirect(url_for("dashboard.app_dashboard", erro="Dia de vencimento inválido."))

    if dia_vencimento < 1 or dia_vencimento > 31:
        return redirect(url_for("dashboard.app_dashboard", erro="O dia de vencimento deve estar entre 1 e 31."))

    try:
        categoria_id = int(categoria_id) if categoria_id else None
    except ValueError:
        return redirect(url_for("dashboard.app_dashboard", erro="Categoria inválida."))

    conn = conectar()
    cur = conn.cursor()

    try:
        if categoria_id:
            cur.execute("""
                SELECT id
                FROM categorias
                WHERE id = %s AND usuario_id = %s
            """, (categoria_id, usuario_id))
            if not cur.fetchone():
                conn.close()
                return redirect(url_for("dashboard.app_dashboard", erro="Categoria não encontrada."))

        cur.execute("""
            INSERT INTO gastos_fixos (usuario_id, descricao, valor, categoria_id, dia_vencimento, ativo)
            VALUES (%s, %s, %s, %s, %s, TRUE)
        """, (usuario_id, descricao, valor, categoria_id, dia_vencimento))

        conn.commit()
    except Exception as e:
        conn.rollback()
        conn.close()
        return redirect(url_for("dashboard.app_dashboard", erro=f"Erro ao salvar gasto fixo: {str(e)}"))

    conn.close()

    return redirect(url_for("dashboard.app_dashboard", mensagem="Gasto fixo adicionado com sucesso."))