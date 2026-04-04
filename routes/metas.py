from flask import Blueprint, request, redirect, url_for, session
from decorators import login_required
from db import conectar

metas_bp = Blueprint("metas", __name__)

@metas_bp.route("/editar_meta/<int:meta_id>", methods=["POST"])
@login_required
def editar_meta(meta_id):
    usuario_id = session["usuario_id"]
    titulo = request.form["titulo"].strip()
    valor_meta = request.form["valor_meta"].strip()

    if not titulo or not valor_meta:
        return redirect(url_for("dashboard.app_dashboard", erro="Preencha os campos da meta."))

    try:
        valor_meta = float(valor_meta)
    except ValueError:
        return redirect(url_for("dashboard.app_dashboard", erro="Valor da meta inválido."))

    if valor_meta <= 0:
        return redirect(url_for("dashboard.app_dashboard", erro="O valor da meta deve ser maior que zero."))

    conn = conectar()
    cur = conn.cursor()

    cur.execute("""
        SELECT id, titulo, valor_atual
        FROM metas
        WHERE id = %s AND usuario_id = %s
    """, (meta_id, usuario_id))
    meta = cur.fetchone()

    if not meta:
        conn.close()
        return redirect(url_for("dashboard.app_dashboard", erro="Meta não encontrada."))

    if float(meta["valor_atual"]) > valor_meta:
        conn.close()
        return redirect(
            url_for(
                "dashboard.app_dashboard",
                erro="O novo valor da meta não pode ser menor que o valor já guardado."
            )
        )

    titulo_antigo = meta["titulo"]

    cur.execute("""
        UPDATE metas
        SET titulo = %s, valor_meta = %s
        WHERE id = %s AND usuario_id = %s
    """, (titulo, valor_meta, meta_id, usuario_id))

    nome_saida_antigo = f"Meta saída: {titulo_antigo}"
    nome_saida_novo = f"Meta saída: {titulo}"

    nome_entrada_antigo = f"Meta entrada: {titulo_antigo}"
    nome_entrada_novo = f"Meta entrada: {titulo}"

    cur.execute("""
        UPDATE categorias
        SET nome = %s
        WHERE usuario_id = %s
          AND nome = %s
          AND tipo = 'saida'
    """, (nome_saida_novo, usuario_id, nome_saida_antigo))

    cur.execute("""
        UPDATE categorias
        SET nome = %s
        WHERE usuario_id = %s
          AND nome = %s
          AND tipo = 'entrada'
    """, (nome_entrada_novo, usuario_id, nome_entrada_antigo))

    cur.execute("""
        UPDATE transacoes
        SET descricao = %s
        WHERE usuario_id = %s
          AND descricao = %s
    """, (
        f"Reserva para meta: {titulo}",
        usuario_id,
        f"Reserva para meta: {titulo_antigo}"
    ))

    cur.execute("""
        UPDATE transacoes
        SET descricao = %s
        WHERE usuario_id = %s
          AND descricao = %s
    """, (
        f"Retirada da meta: {titulo}",
        usuario_id,
        f"Retirada da meta: {titulo_antigo}"
    ))

    conn.commit()
    conn.close()

    return redirect(url_for("dashboard.app_dashboard", mensagem="Meta atualizada com sucesso."))