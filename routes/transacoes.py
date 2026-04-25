from flask import Blueprint, request, session
import logging
from decorators import login_required
from db import conectar
from datetime import datetime
from utils import redirecionar_dashboard

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

transacoes_bp = Blueprint("transacoes", __name__)


def validar_valor(valor):
    try:
        valor_convertido = float(valor)
    except ValueError:
        return None, "Valor inválido."

    if valor_convertido <= 0:
        return None, "O valor deve ser maior que zero."

    return valor_convertido, None


def validar_data(data):
    try:
        return datetime.strptime(data, "%Y-%m-%d").date(), None
    except ValueError:
        return None, "Data inválida."


def validar_categoria(categoria_id):
    try:
        return int(categoria_id) if categoria_id else None, None
    except ValueError:
        return None, "Categoria inválida."


@transacoes_bp.route("/add_transacao", methods=["POST"])
@login_required
def add_transacao():
    usuario_id = session["usuario_id"]
    descricao = request.form.get("descricao", "").strip()
    valor = request.form.get("valor", "").strip()
    tipo = request.form.get("tipo", "").strip()
    categoria_id = request.form.get("categoria_id", "").strip()
    data = request.form.get("data", "").strip()

    if not descricao or not valor or tipo not in ["entrada", "saida"] or not data:
        return redirecionar_dashboard("Preencha os campos corretamente.", "erro")

    valor, erro = validar_valor(valor)
    if erro:
        return redirecionar_dashboard(erro, "erro")

    data, erro = validar_data(data)
    if erro:
        return redirecionar_dashboard(erro, "erro")

    categoria_id, erro = validar_categoria(categoria_id)
    if erro:
        return redirecionar_dashboard(erro, "erro")

    conn = None
    try:
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
                return redirecionar_dashboard("Categoria não encontrada.", "erro")

            if categoria["tipo"] != tipo:
                return redirecionar_dashboard("A categoria não corresponde ao tipo da transação.", "erro")

        cur.execute("""
            INSERT INTO transacoes (usuario_id, descricao, valor, tipo, categoria_id, data)
            VALUES (%s, %s, %s, %s, %s, %s)
        """, (usuario_id, descricao, valor, tipo, categoria_id, data))

        conn.commit()
        return redirecionar_dashboard("Transação adicionada com sucesso.", "sucesso")

    except Exception as e:
        if conn:
            conn.rollback()
        logger.exception(f"Erro ao adicionar transação para usuário {usuario_id}: {e}")
        return redirecionar_dashboard("Não foi possível salvar a transação. Tente novamente.", "erro")
    finally:
        if conn:
            conn.close()


@transacoes_bp.route("/editar_transacao/<int:transacao_id>", methods=["POST"])
@login_required
def editar_transacao(transacao_id):
    usuario_id = session["usuario_id"]
    descricao = request.form.get("descricao", "").strip()
    valor = request.form.get("valor", "").strip()
    tipo = request.form.get("tipo", "").strip()
    categoria_id = request.form.get("categoria_id", "").strip()
    data = request.form.get("data", "").strip()

    if not descricao or not valor or tipo not in ["entrada", "saida"] or not data:
        return redirecionar_dashboard("Preencha os campos corretamente.", "erro")

    valor, erro = validar_valor(valor)
    if erro:
        return redirecionar_dashboard(erro, "erro")

    data, erro = validar_data(data)
    if erro:
        return redirecionar_dashboard(erro, "erro")

    categoria_id, erro = validar_categoria(categoria_id)
    if erro:
        return redirecionar_dashboard(erro, "erro")

    conn = None
    try:
        conn = conectar()
        cur = conn.cursor()

        cur.execute("""
            SELECT id
            FROM transacoes
            WHERE id = %s AND usuario_id = %s
        """, (transacao_id, usuario_id))
        transacao = cur.fetchone()

        if not transacao:
            return redirecionar_dashboard("Transação não encontrada.", "erro")

        if categoria_id:
            cur.execute("""
                SELECT id, tipo
                FROM categorias
                WHERE id = %s AND usuario_id = %s
            """, (categoria_id, usuario_id))
            categoria = cur.fetchone()

            if not categoria:
                return redirecionar_dashboard("Categoria não encontrada.", "erro")

            if categoria["tipo"] != tipo:
                return redirecionar_dashboard("A categoria não corresponde ao tipo da transação.", "erro")

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
        return redirecionar_dashboard("Transação atualizada com sucesso.", "sucesso")

    except Exception as e:
        if conn:
            conn.rollback()
        logger.exception(f"Erro ao editar transação {transacao_id} para usuário {usuario_id}: {e}")
        return redirecionar_dashboard("Não foi possível atualizar a transação. Tente novamente.", "erro")
    finally:
        if conn:
            conn.close()


@transacoes_bp.route("/excluir_transacao/<int:transacao_id>", methods=["POST"])
@login_required
def excluir_transacao(transacao_id):
    usuario_id = session["usuario_id"]

    conn = None
    try:
        conn = conectar()
        cur = conn.cursor()

        cur.execute("""
            SELECT id
            FROM transacoes
            WHERE id = %s AND usuario_id = %s
        """, (transacao_id, usuario_id))
        transacao = cur.fetchone()

        if not transacao:
            return redirecionar_dashboard("Transação não encontrada.", "erro")

        cur.execute("""
            DELETE FROM transacoes
            WHERE id = %s AND usuario_id = %s
        """, (transacao_id, usuario_id))

        conn.commit()
        return redirecionar_dashboard("Transação excluída com sucesso.", "sucesso")

    except Exception as e:
        if conn:
            conn.rollback()
        logger.exception(f"Erro ao excluir transação {transacao_id} para usuário {usuario_id}: {e}")
        return redirecionar_dashboard("Não foi possível excluir a transação. Tente novamente.", "erro")
    finally:
        if conn:
            conn.close()
