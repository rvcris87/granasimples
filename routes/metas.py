from flask import Blueprint, request, redirect, url_for, session, flash
from decorators import login_required
from db import conectar

metas_bp = Blueprint("metas", __name__)

@metas_bp.route("/add_meta", methods=["POST"])
@login_required
def add_meta():
    usuario_id = session["usuario_id"]
    titulo = request.form.get("titulo", "").strip()
    valor_meta = request.form.get("valor_meta", "").strip()

    if not titulo or not valor_meta:
        flash("Preencha os campos da meta.", "erro")
        return redirect(url_for("dashboard.app_dashboard"))

    try:
        valor_meta = float(valor_meta)
    except ValueError:
        flash("Valor da meta inválido.", "erro")
        return redirect(url_for("dashboard.app_dashboard"))

    if valor_meta <= 0:
        flash("O valor da meta deve ser maior que zero.", "erro")
        return redirect(url_for("dashboard.app_dashboard"))

    conn = conectar()
    cur = conn.cursor()

    try:
        cur.execute("""
            INSERT INTO metas (usuario_id, titulo, valor_meta, valor_atual)
            VALUES (%s, %s, %s, 0)
            RETURNING id
        """, (usuario_id, titulo, valor_meta))

        meta_id = cur.fetchone()["id"]

        nome_saida = f"Meta saída: {titulo}"
        nome_entrada = f"Meta entrada: {titulo}"

        cur.execute("""
            INSERT INTO categorias (usuario_id, nome, tipo)
            VALUES (%s, %s, %s)
        """, (usuario_id, nome_saida, "saida"))

        cur.execute("""
            INSERT INTO categorias (usuario_id, nome, tipo)
            VALUES (%s, %s, %s)
        """, (usuario_id, nome_entrada, "entrada"))

        conn.commit()
    except Exception as e:
        conn.rollback()
        conn.close()
        flash(f"Erro ao criar meta: {str(e)}", "erro")
        return redirect(url_for("dashboard.app_dashboard"))

    conn.close()

    flash("Meta criada com sucesso.", "sucesso")
    return redirect(url_for("dashboard.app_dashboard"))

@metas_bp.route("/adicionar_valor_meta/<int:meta_id>", methods=["POST"])
@login_required
def adicionar_valor_meta(meta_id):
    usuario_id = session["usuario_id"]
    valor_str = request.form.get("valor_adicionar", "").strip()

    if not valor_str:
        flash("Informe um valor para adicionar à meta.", "erro")
        return redirect(url_for("dashboard.app_dashboard"))

    try:
        valor = float(valor_str)
    except ValueError:
        flash("Valor inválido para adicionar à meta.", "erro")
        return redirect(url_for("dashboard.app_dashboard"))

    if valor <= 0:
        flash("O valor deve ser maior que zero.", "erro")
        return redirect(url_for("dashboard.app_dashboard"))

    conn = conectar()
    cur = conn.cursor()

    cur.execute("""
        SELECT id, titulo, valor_atual, valor_meta
        FROM metas
        WHERE id = %s AND usuario_id = %s
    """, (meta_id, usuario_id))
    meta = cur.fetchone()

    if not meta:
        conn.close()
        flash("Meta não encontrada.", "erro")
        return redirect(url_for("dashboard.app_dashboard"))

    novo_valor_atual = float(meta["valor_atual"]) + valor

    if novo_valor_atual > float(meta["valor_meta"]):
        conn.close()
        flash("O valor adicionado excede o limite da meta.", "erro")
        return redirect(url_for("dashboard.app_dashboard"))

    cur.execute("""
        UPDATE metas
        SET valor_atual = %s
        WHERE id = %s AND usuario_id = %s
    """, (novo_valor_atual, meta_id, usuario_id))

    cur.execute("""
        INSERT INTO transacoes (usuario_id, descricao, valor, tipo, data)
        VALUES (%s, %s, %s, 'saida', CURRENT_DATE)
    """, (usuario_id, f"Reserva para meta: {meta['titulo']}", valor))

    conn.commit()
    conn.close()

    flash("Valor adicionado à meta com sucesso.", "sucesso")
    return redirect(url_for("dashboard.app_dashboard"))

@metas_bp.route("/retirar_valor_meta/<int:meta_id>", methods=["POST"])
@login_required
def retirar_valor_meta(meta_id):
    usuario_id = session["usuario_id"]
    valor_str = request.form.get("valor_retirar", "").strip()

    if not valor_str:
        flash("Informe um valor para retirar da meta.", "erro")
        return redirect(url_for("dashboard.app_dashboard"))

    try:
        valor = float(valor_str)
    except ValueError:
        flash("Valor inválido para retirar da meta.", "erro")
        return redirect(url_for("dashboard.app_dashboard"))

    if valor <= 0:
        flash("O valor deve ser maior que zero.", "erro")
        return redirect(url_for("dashboard.app_dashboard"))

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
        flash("Meta não encontrada.", "erro")
        return redirect(url_for("dashboard.app_dashboard"))

    if float(meta["valor_atual"]) < valor:
        conn.close()
        flash("Valor insuficiente na meta.", "erro")
        return redirect(url_for("dashboard.app_dashboard"))

    novo_valor_atual = float(meta["valor_atual"]) - valor

    cur.execute("""
        UPDATE metas
        SET valor_atual = %s
        WHERE id = %s AND usuario_id = %s
    """, (novo_valor_atual, meta_id, usuario_id))

    cur.execute("""
        INSERT INTO transacoes (usuario_id, descricao, valor, tipo, data)
        VALUES (%s, %s, %s, 'entrada', CURRENT_DATE)
    """, (usuario_id, f"Retirada da meta: {meta['titulo']}", valor))

    conn.commit()
    conn.close()

    flash("Valor retirado da meta com sucesso.", "sucesso")
    return redirect(url_for("dashboard.app_dashboard"))

@metas_bp.route("/editar_meta/<int:meta_id>", methods=["POST"])
@login_required
def editar_meta(meta_id):
    usuario_id = session["usuario_id"]
    titulo = request.form.get("titulo", "").strip()
    valor_meta = request.form.get("valor_meta", "").strip()

    if not titulo or not valor_meta:
        flash("Preencha os campos da meta.", "erro")
        return redirect(url_for("dashboard.app_dashboard"))

    try:
        valor_meta = float(valor_meta)
    except ValueError:
        flash("Valor da meta inválido.", "erro")
        return redirect(url_for("dashboard.app_dashboard"))

    if valor_meta <= 0:
        flash("O valor da meta deve ser maior que zero.", "erro")
        return redirect(url_for("dashboard.app_dashboard"))

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
        flash("Meta não encontrada.", "erro")
        return redirect(url_for("dashboard.app_dashboard"))

    if float(meta["valor_atual"]) > valor_meta:
        conn.close()
        flash("O novo valor da meta não pode ser menor que o valor já guardado.", "erro")
        return redirect(url_for("dashboard.app_dashboard"))

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

    flash("Meta atualizada com sucesso.", "sucesso")
    return redirect(url_for("dashboard.app_dashboard"))

@metas_bp.route("/delete_meta/<int:meta_id>", methods=["POST"])
@login_required
def delete_meta(meta_id):
    usuario_id = session["usuario_id"]
    
    conn = conectar()
    cur = conn.cursor()

    cur.execute("""
        SELECT id, titulo
        FROM metas
        WHERE id = %s AND usuario_id = %s
    """, (meta_id, usuario_id))
    meta = cur.fetchone()

    if not meta:
        conn.close()
        flash("Meta não encontrada.", "erro")
        return redirect(url_for("dashboard.app_dashboard"))

    titulo_meta = meta["titulo"]

    try:
        # Deletar categorias associadas
        nome_saida = f"Meta saída: {titulo_meta}"
        nome_entrada = f"Meta entrada: {titulo_meta}"

        cur.execute("""
            DELETE FROM categorias
            WHERE usuario_id = %s AND nome IN (%s, %s)
        """, (usuario_id, nome_saida, nome_entrada))

        # Deletar transações associadas
        cur.execute("""
            DELETE FROM transacoes
            WHERE usuario_id = %s AND (
                descricao LIKE %s OR descricao LIKE %s
            )
        """, (usuario_id, f"Reserva para meta: {titulo_meta}%", f"Retirada da meta: {titulo_meta}%"))

        # Deletar a meta
        cur.execute("""
            DELETE FROM metas
            WHERE id = %s AND usuario_id = %s
        """, (meta_id, usuario_id))

        conn.commit()
    except Exception as e:
        conn.rollback()
        conn.close()
        flash(f"Erro ao excluir meta: {str(e)}", "erro")
        return redirect(url_for("dashboard.app_dashboard"))

    conn.close()

    flash("Meta excluída com sucesso.", "sucesso")
    return redirect(url_for("dashboard.app_dashboard"))