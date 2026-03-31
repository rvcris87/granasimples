from flask import Blueprint, request, redirect, url_for, session
from decorators import login_required
from db import conectar

metas_bp = Blueprint("metas", __name__)


def buscar_ou_criar_categoria_meta(cur, usuario_id, titulo_meta, tipo_categoria):
    if tipo_categoria == "saida":
        nome_categoria = f"Meta saída: {titulo_meta}"
    else:
        nome_categoria = f"Meta entrada: {titulo_meta}"

    cur.execute("""
        SELECT id
        FROM categorias
        WHERE usuario_id = %s AND nome = %s AND tipo = %s
    """, (usuario_id, nome_categoria, tipo_categoria))
    categoria = cur.fetchone()

    if categoria:
        return categoria["id"]

    cur.execute("""
        INSERT INTO categorias (usuario_id, nome, tipo)
        VALUES (%s, %s, %s)
        RETURNING id
    """, (usuario_id, nome_categoria, tipo_categoria))
    nova_categoria = cur.fetchone()

    return nova_categoria["id"]


@metas_bp.route("/add_meta", methods=["POST"])
@login_required
def add_meta():
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
        INSERT INTO metas (usuario_id, titulo, valor_meta, valor_atual)
        VALUES (%s, %s, %s, 0)
    """, (usuario_id, titulo, valor_meta))

    conn.commit()
    conn.close()

    return redirect(url_for("dashboard.app_dashboard", mensagem="Meta criada com sucesso."))


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
        WHERE usuario_id = %s AND nome = %s AND tipo = 'saida'
    """, (nome_saida_novo, usuario_id, nome_saida_antigo))

    cur.execute("""
        UPDATE categorias
        SET nome = %s
        WHERE usuario_id = %s AND nome = %s AND tipo = 'entrada'
    """, (nome_entrada_novo, usuario_id, nome_entrada_antigo))

    conn.commit()
    conn.close()

    return redirect(url_for("dashboard.app_dashboard", mensagem="Meta atualizada com sucesso."))


@metas_bp.route("/excluir_meta/<int:meta_id>")
@login_required
def excluir_meta(meta_id):
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
        return redirect(url_for("dashboard.app_dashboard", erro="Meta não encontrada."))

    cur.execute("""
        DELETE FROM metas
        WHERE id = %s AND usuario_id = %s
    """, (meta_id, usuario_id))

    conn.commit()
    conn.close()

    return redirect(url_for("dashboard.app_dashboard", mensagem="Meta excluída com sucesso."))


@metas_bp.route("/adicionar_valor_meta/<int:meta_id>", methods=["POST"])
@login_required
def adicionar_valor_meta(meta_id):
    usuario_id = session["usuario_id"]
    valor = request.form["valor_adicionar"].strip()

    try:
        valor = float(valor)
    except ValueError:
        return redirect(url_for("dashboard.app_dashboard", erro="Valor inválido para adicionar à meta."))

    if valor <= 0:
        return redirect(url_for("dashboard.app_dashboard", erro="O valor para adicionar deve ser maior que zero."))

    conn = conectar()
    cur = conn.cursor()

    cur.execute("""
        SELECT id, valor_meta, valor_atual
        FROM metas
        WHERE id = %s AND usuario_id = %s
    """, (meta_id, usuario_id))
    meta = cur.fetchone()

    if not meta:
        conn.close()
        return redirect(url_for("dashboard.app_dashboard", erro="Meta não encontrada."))

    novo_valor_atual = float(meta["valor_atual"]) + valor

    if novo_valor_atual > float(meta["valor_meta"]):
        novo_valor_atual = float(meta["valor_meta"])

    cur.execute("""
        UPDATE metas
        SET valor_atual = %s
        WHERE id = %s AND usuario_id = %s
    """, (novo_valor_atual, meta_id, usuario_id))

    conn.commit()
    conn.close()

    return redirect(url_for("dashboard.app_dashboard", mensagem="Valor adicionado à meta com sucesso."))


@metas_bp.route("/retirar_valor_meta/<int:meta_id>", methods=["POST"])
@login_required
def retirar_valor_meta(meta_id):
    usuario_id = session["usuario_id"]
    valor = request.form["valor_retirar"].strip()

    try:
        valor = float(valor)
    except ValueError:
        return redirect(url_for("dashboard.app_dashboard", erro="Valor inválido para retirar da meta."))

    if valor <= 0:
        return redirect(url_for("dashboard.app_dashboard", erro="O valor para retirar deve ser maior que zero."))

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

    valor_atual = float(meta["valor_atual"])

    if valor > valor_atual:
        conn.close()
        return redirect(url_for("dashboard.app_dashboard", erro="Você não pode retirar mais do que já guardou na meta."))

    novo_valor_atual = valor_atual - valor

    categoria_id = buscar_ou_criar_categoria_meta(cur, usuario_id, meta["titulo"], "entrada")

    cur.execute("""
        UPDATE metas
        SET valor_atual = %s
        WHERE id = %s AND usuario_id = %s
    """, (novo_valor_atual, meta_id, usuario_id))

    cur.execute("""
        INSERT INTO transacoes (usuario_id, descricao, valor, tipo, categoria_id, data)
        VALUES (%s, %s, %s, %s, %s, CURRENT_DATE)
    """, (
        usuario_id,
        f"Retirada da meta: {meta['titulo']}",
        valor,
        "entrada",
        categoria_id
    ))

    conn.commit()
    conn.close()

    return redirect(url_for("dashboard.app_dashboard", mensagem="Valor retirado da meta e devolvido ao saldo com sucesso."))


@metas_bp.route("/usar_saldo_meta/<int:meta_id>", methods=["POST"])
@login_required
def usar_saldo_meta(meta_id):
    usuario_id = session["usuario_id"]
    valor = request.form["valor_usar_saldo"].strip()

    try:
        valor = float(valor)
    except ValueError:
        return redirect(url_for("dashboard.app_dashboard", erro="Valor inválido para reservar na meta."))

    if valor <= 0:
        return redirect(url_for("dashboard.app_dashboard", erro="O valor deve ser maior que zero."))

    conn = conectar()
    cur = conn.cursor()

    cur.execute("""
        SELECT id, titulo, valor_meta, valor_atual
        FROM metas
        WHERE id = %s AND usuario_id = %s
    """, (meta_id, usuario_id))
    meta = cur.fetchone()

    if not meta:
        conn.close()
        return redirect(url_for("dashboard.app_dashboard", erro="Meta não encontrada."))

    cur.execute("""
        SELECT
            COALESCE(SUM(CASE WHEN tipo = 'entrada' THEN valor ELSE 0 END), 0) AS total_entradas,
            COALESCE(SUM(CASE WHEN tipo = 'saida' THEN valor ELSE 0 END), 0) AS total_saidas
        FROM transacoes
        WHERE usuario_id = %s
    """, (usuario_id,))
    saldo = cur.fetchone()

    saldo_disponivel = float(saldo["total_entradas"]) - float(saldo["total_saidas"])

    if saldo_disponivel <= 0:
        conn.close()
        return redirect(url_for("dashboard.app_dashboard", erro="Você não tem saldo disponível."))

    if valor > saldo_disponivel:
        conn.close()
        return redirect(url_for("dashboard.app_dashboard", erro="O valor informado é maior que o saldo disponível."))

    novo_valor_atual = float(meta["valor_atual"]) + valor

    if novo_valor_atual > float(meta["valor_meta"]):
        conn.close()
        return redirect(url_for("dashboard.app_dashboard", erro="Esse valor ultrapassa o objetivo da meta."))

    categoria_id = buscar_ou_criar_categoria_meta(cur, usuario_id, meta["titulo"], "saida")

    cur.execute("""
        UPDATE metas
        SET valor_atual = %s
        WHERE id = %s AND usuario_id = %s
    """, (novo_valor_atual, meta_id, usuario_id))

    cur.execute("""
        INSERT INTO transacoes (usuario_id, descricao, valor, tipo, categoria_id, data)
        VALUES (%s, %s, %s, %s, %s, CURRENT_DATE)
    """, (
        usuario_id,
        f"Reserva para meta: {meta['titulo']}",
        valor,
        "saida",
        categoria_id
    ))

    conn.commit()
    conn.close()

    return redirect(url_for("dashboard.app_dashboard", mensagem="Saldo reservado para a meta com sucesso."))