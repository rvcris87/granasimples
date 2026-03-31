from flask import Blueprint, request, redirect, url_for, session
from decorators import login_required
from db import conectar

transacoes_bp = Blueprint("transacoes", __name__)


@transacoes_bp.route("/add_transacao", methods=["POST"])
@login_required
def add_transacao():
    usuario_id = session["usuario_id"]
    descricao = request.form["descricao"].strip()
    valor = request.form["valor"].strip()
    tipo = request.form["tipo"].strip()
    categoria_id = request.form.get("categoria_id", "").strip()
    data = request.form["data"]

    if not descricao or not valor or tipo not in ["entrada", "saida"] or not data:
        return redirect(url_for("dashboard.app_dashboard", erro="Preencha os campos corretamente."))

    try:
        valor = float(valor)
    except ValueError:
        return redirect(url_for("dashboard.app_dashboard", erro="Valor inválido."))

    try:
        categoria_id = int(categoria_id) if categoria_id else None
    except ValueError:
        return redirect(url_for("dashboard.app_dashboard", erro="Categoria inválida."))

    conn = conectar()
    cur = conn.cursor()

    if categoria_id:
        cur.execute("""
            SELECT id, tipo
            FROM categorias
            WHERE id = %s AND usuario_id = %s
        """, (categoria_id, usuario_id))
        categoria = cur.fetchone()

        if not categoria:
            conn.close()
            return redirect(url_for("dashboard.app_dashboard", erro="Categoria não encontrada."))

        if categoria["tipo"] != tipo:
            conn.close()
            return redirect(url_for("dashboard.app_dashboard", erro="A categoria não corresponde ao tipo da transação."))

    cur.execute("""
        INSERT INTO transacoes (usuario_id, descricao, valor, tipo, categoria_id, data)
        VALUES (%s, %s, %s, %s, %s, %s)
    """, (usuario_id, descricao, valor, tipo, categoria_id, data))

    conn.commit()
    conn.close()

    return redirect(url_for("dashboard.app_dashboard", mensagem="Transação adicionada com sucesso."))


@transacoes_bp.route("/editar_transacao/<int:transacao_id>", methods=["POST"])
@login_required
def editar_transacao(transacao_id):
    usuario_id = session["usuario_id"]
    descricao = request.form["descricao"].strip()
    valor = request.form["valor"].strip()
    tipo = request.form["tipo"].strip()
    categoria_id = request.form.get("categoria_id", "").strip()
    data = request.form["data"]

    if not descricao or not valor or tipo not in ["entrada", "saida"] or not data:
        return redirect(url_for("dashboard.app_dashboard", erro="Preencha os campos corretamente."))

    try:
        valor = float(valor)
    except ValueError:
        return redirect(url_for("dashboard.app_dashboard", erro="Valor inválido."))

    try:
        categoria_id = int(categoria_id) if categoria_id else None
    except ValueError:
        return redirect(url_for("dashboard.app_dashboard", erro="Categoria inválida."))

    conn = conectar()
    cur = conn.cursor()

    cur.execute("""
        SELECT id
        FROM transacoes
        WHERE id = %s AND usuario_id = %s
    """, (transacao_id, usuario_id))
    transacao = cur.fetchone()

    if not transacao:
        conn.close()
        return redirect(url_for("dashboard.app_dashboard", erro="Transação não encontrada."))

    if categoria_id:
        cur.execute("""
            SELECT id, tipo
            FROM categorias
            WHERE id = %s AND usuario_id = %s
        """, (categoria_id, usuario_id))
        categoria = cur.fetchone()

        if not categoria:
            conn.close()
            return redirect(url_for("dashboard.app_dashboard", erro="Categoria não encontrada."))

        if categoria["tipo"] != tipo:
            conn.close()
            return redirect(url_for("dashboard.app_dashboard", erro="A categoria não corresponde ao tipo da transação."))

    cur.execute("""
        UPDATE transacoes
        SET descricao = %s,
            valor = %s,
            tipo = %s,
            categoria_id = %s,
            data = %s
        WHERE id = %s AND usuario_id = %s
    """, (descricao, valor, tipo, categoria_id, data, transacao_id, usuario_id))

    conn.commit()
    conn.close()

    return redirect(url_for("dashboard.app_dashboard", mensagem="Transação atualizada com sucesso."))


@transacoes_bp.route("/excluir_transacao/<int:transacao_id>")
@login_required
def excluir_transacao(transacao_id):
    usuario_id = session["usuario_id"]

    conn = conectar()
    cur = conn.cursor()

    cur.execute("""
        SELECT id
        FROM transacoes
        WHERE id = %s AND usuario_id = %s
    """, (transacao_id, usuario_id))
    transacao = cur.fetchone()

    if not transacao:
        conn.close()
        return redirect(url_for("dashboard.app_dashboard", erro="Transação não encontrada."))

    cur.execute("""
        DELETE FROM transacoes
        WHERE id = %s AND usuario_id = %s
    """, (transacao_id, usuario_id))

    conn.commit()
    conn.close()

    return redirect(url_for("dashboard.app_dashboard", mensagem="Transação excluída com sucesso."))