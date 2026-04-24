from flask import Blueprint, request, redirect, url_for, session, flash
import logging
from decorators import login_required
from db import conectar

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

categorias_bp = Blueprint("categorias", __name__)


def redirecionar_dashboard(mensagem, categoria):
    flash(mensagem, categoria)
    return redirect(url_for("dashboard.app_dashboard"))


def normalizar_nome(nome):
    return " ".join(nome.split())


def validar_categoria(nome, tipo):
    nome = normalizar_nome(nome)

    if len(nome) < 2:
        return nome, "O nome da categoria deve ter pelo menos 2 caracteres."

    if tipo not in ["entrada", "saida"]:
        return nome, "Tipo de categoria inválido."

    return nome, None


def categoria_duplicada(cur, usuario_id, nome, tipo, categoria_id=None):
    params = [usuario_id, nome, tipo]
    filtro_id = ""

    if categoria_id:
        filtro_id = " AND id <> %s"
        params.append(categoria_id)

    cur.execute(f"""
        SELECT id
        FROM categorias
        WHERE usuario_id = %s
          AND lower(trim(nome)) = lower(trim(%s))
          AND tipo = %s
          {filtro_id}
        LIMIT 1
    """, params)
    return cur.fetchone() is not None


@categorias_bp.route("/add_categoria", methods=["POST"])
@login_required
def add_categoria():
    usuario_id = session["usuario_id"]
    nome = request.form.get("nome", "").strip()
    tipo = request.form.get("tipo", "").strip()

    nome, erro = validar_categoria(nome, tipo)
    if erro:
        return redirecionar_dashboard(erro, "erro")

    conn = None
    try:
        conn = conectar()
        cur = conn.cursor()

        if categoria_duplicada(cur, usuario_id, nome, tipo):
            return redirecionar_dashboard("Essa categoria já existe.", "erro")

        cur.execute("""
            INSERT INTO categorias (usuario_id, nome, tipo)
            VALUES (%s, %s, %s)
        """, (usuario_id, nome, tipo))

        conn.commit()
        return redirecionar_dashboard("Categoria criada com sucesso.", "sucesso")

    except Exception as e:
        if conn:
            conn.rollback()
        logger.exception(f"Erro ao criar categoria para usuário {usuario_id}: {e}")
        return redirecionar_dashboard("Não foi possível salvar a categoria. Tente novamente.", "erro")
    finally:
        if conn:
            conn.close()


@categorias_bp.route("/editar_categoria/<int:categoria_id>", methods=["POST"])
@login_required
def editar_categoria(categoria_id):
    usuario_id = session["usuario_id"]
    nome = request.form.get("nome", "").strip()
    tipo = request.form.get("tipo", "").strip()

    nome, erro = validar_categoria(nome, tipo)
    if erro:
        return redirecionar_dashboard(erro, "erro")

    conn = None
    try:
        conn = conectar()
        cur = conn.cursor()

        cur.execute("""
            SELECT id
            FROM categorias
            WHERE id = %s AND usuario_id = %s
        """, (categoria_id, usuario_id))

        if not cur.fetchone():
            return redirecionar_dashboard("Categoria não encontrada.", "erro")

        if categoria_duplicada(cur, usuario_id, nome, tipo, categoria_id):
            return redirecionar_dashboard("Essa categoria já existe.", "erro")

        cur.execute("""
            UPDATE categorias
            SET nome = %s, tipo = %s
            WHERE id = %s AND usuario_id = %s
        """, (nome, tipo, categoria_id, usuario_id))

        conn.commit()
        return redirecionar_dashboard("Categoria atualizada com sucesso.", "sucesso")

    except Exception as e:
        if conn:
            conn.rollback()
        logger.exception(f"Erro ao atualizar categoria {categoria_id} para usuário {usuario_id}: {e}")
        return redirecionar_dashboard("Não foi possível atualizar a categoria. Tente novamente.", "erro")
    finally:
        if conn:
            conn.close()


@categorias_bp.route("/excluir_categoria/<int:categoria_id>", methods=["POST"])
@login_required
def excluir_categoria(categoria_id):
    usuario_id = session["usuario_id"]
    conn = None

    try:
        conn = conectar()
        cur = conn.cursor()

        cur.execute("""
            SELECT id
            FROM categorias
            WHERE id = %s AND usuario_id = %s
        """, (categoria_id, usuario_id))

        if not cur.fetchone():
            return redirecionar_dashboard("Categoria não encontrada.", "erro")

        cur.execute("""
            SELECT COUNT(*) AS total
            FROM transacoes
            WHERE categoria_id = %s AND usuario_id = %s
        """, (categoria_id, usuario_id))
        transacoes = int(cur.fetchone()["total"] or 0)

        cur.execute("""
            SELECT COUNT(*) AS total
            FROM gastos_fixos
            WHERE categoria_id = %s AND usuario_id = %s
        """, (categoria_id, usuario_id))
        gastos_fixos = int(cur.fetchone()["total"] or 0)

        if transacoes or gastos_fixos:
            return redirecionar_dashboard("Não é possível excluir uma categoria em uso.", "erro")

        cur.execute("""
            DELETE FROM categorias
            WHERE id = %s AND usuario_id = %s
        """, (categoria_id, usuario_id))

        conn.commit()
        return redirecionar_dashboard("Categoria excluída com sucesso.", "sucesso")

    except Exception as e:
        if conn:
            conn.rollback()
        logger.exception(f"Erro ao excluir categoria {categoria_id} para usuário {usuario_id}: {e}")
        return redirecionar_dashboard("Não foi possível excluir a categoria. Tente novamente.", "erro")
    finally:
        if conn:
            conn.close()
