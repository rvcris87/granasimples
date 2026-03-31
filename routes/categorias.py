from flask import Blueprint, request, redirect, url_for, session
from decorators import login_required
from db import conectar

categorias_bp = Blueprint("categorias", __name__)


@categorias_bp.route("/add_categoria", methods=["POST"])
@login_required
def add_categoria():
    usuario_id = session["usuario_id"]
    nome = request.form["nome"].strip()
    tipo = request.form["tipo"].strip()

    if not nome or tipo not in ["entrada", "saida"]:
        return redirect(url_for("dashboard.app_dashboard", erro="Categoria inválida."))

    conn = conectar()
    cur = conn.cursor()

    cur.execute("""
        INSERT INTO categorias (usuario_id, nome, tipo)
        VALUES (%s, %s, %s)
    """, (usuario_id, nome, tipo))

    conn.commit()
    conn.close()

    return redirect(url_for("dashboard.app_dashboard", mensagem="Categoria criada com sucesso."))