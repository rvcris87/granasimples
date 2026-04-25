from decimal import Decimal, InvalidOperation
import logging
from flask import Blueprint, request, session

from decorators import login_required
from db import conectar
from utils import normalizar_texto, redirecionar_dashboard

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

metas_bp = Blueprint("metas", __name__)


def normalizar_titulo(titulo):
    return normalizar_texto(titulo)


def validar_titulo(titulo):
    titulo = normalizar_titulo(titulo)

    if len(titulo) < 2:
        return titulo, "O nome da meta deve ter pelo menos 2 caracteres."

    return titulo, None


def parse_valor(valor):
    try:
        valor_decimal = Decimal(valor.replace(",", "."))
    except (InvalidOperation, AttributeError):
        return None, "Valor inválido."

    if valor_decimal <= 0:
        return None, "O valor deve ser maior que zero."

    return valor_decimal, None


def meta_duplicada(cur, usuario_id, titulo, meta_id=None):
    params = [usuario_id, titulo]
    filtro_id = ""

    if meta_id:
        filtro_id = " AND id <> %s"
        params.append(meta_id)

    cur.execute(f"""
        SELECT id
        FROM metas
        WHERE usuario_id = %s
          AND lower(trim(titulo)) = lower(trim(%s))
          {filtro_id}
        LIMIT 1
    """, params)
    return cur.fetchone() is not None


def garantir_categoria_meta(cur, usuario_id, nome, tipo):
    cur.execute("""
        SELECT id
        FROM categorias
        WHERE usuario_id = %s
          AND lower(trim(nome)) = lower(trim(%s))
          AND tipo = %s
        LIMIT 1
    """, (usuario_id, nome, tipo))

    if cur.fetchone():
        return

    cur.execute("""
        INSERT INTO categorias (usuario_id, nome, tipo)
        VALUES (%s, %s, %s)
    """, (usuario_id, nome, tipo))


def nomes_categorias_meta(titulo):
    return f"Meta saída: {titulo}", f"Meta entrada: {titulo}"


@metas_bp.route("/add_meta", methods=["POST"])
@login_required
def add_meta():
    usuario_id = session["usuario_id"]
    titulo = request.form.get("titulo", "").strip()
    valor_meta = request.form.get("valor_meta", "").strip()

    titulo, erro = validar_titulo(titulo)
    if erro:
        return redirecionar_dashboard(erro, "erro")

    valor_meta, erro = parse_valor(valor_meta)
    if erro:
        return redirecionar_dashboard("Valor da meta inválido." if erro == "Valor inválido." else erro, "erro")

    conn = None
    try:
        conn = conectar()
        cur = conn.cursor()

        if meta_duplicada(cur, usuario_id, titulo):
            return redirecionar_dashboard("Essa meta já existe.", "erro")

        cur.execute("""
            INSERT INTO metas (usuario_id, titulo, valor_meta, valor_atual)
            VALUES (%s, %s, %s, 0)
        """, (usuario_id, titulo, valor_meta))

        nome_saida, nome_entrada = nomes_categorias_meta(titulo)
        garantir_categoria_meta(cur, usuario_id, nome_saida, "saida")
        garantir_categoria_meta(cur, usuario_id, nome_entrada, "entrada")

        conn.commit()
        return redirecionar_dashboard("Meta criada com sucesso.", "sucesso")

    except Exception as e:
        if conn:
            conn.rollback()
        logger.exception(f"Erro ao criar meta para usuário {usuario_id}: {e}")
        return redirecionar_dashboard("Não foi possível criar a meta. Tente novamente.", "erro")
    finally:
        if conn:
            conn.close()


@metas_bp.route("/adicionar_valor_meta/<int:meta_id>", methods=["POST"])
@login_required
def adicionar_valor_meta(meta_id):
    usuario_id = session["usuario_id"]
    valor_str = request.form.get("valor_adicionar", "").strip()

    if not valor_str:
        return redirecionar_dashboard("Informe um valor para adicionar à meta.", "erro")

    valor, erro = parse_valor(valor_str)
    if erro:
        return redirecionar_dashboard("Valor inválido para adicionar à meta.", "erro")

    conn = None
    try:
        conn = conectar()
        cur = conn.cursor()

        cur.execute("""
            SELECT id, titulo, valor_atual, valor_meta
            FROM metas
            WHERE id = %s AND usuario_id = %s
        """, (meta_id, usuario_id))
        meta = cur.fetchone()

        if not meta:
            return redirecionar_dashboard("Meta não encontrada.", "erro")

        novo_valor_atual = Decimal(meta["valor_atual"] or 0) + valor

        if novo_valor_atual > Decimal(meta["valor_meta"]):
            return redirecionar_dashboard("O valor adicionado excede o limite da meta.", "erro")

        cur.execute("""
            UPDATE metas
            SET valor_atual = %s
            WHERE id = %s AND usuario_id = %s
        """, (novo_valor_atual, meta_id, usuario_id))

        cur.execute("""
            INSERT INTO transacoes (usuario_id, descricao, valor, tipo, data, meta_id)
            VALUES (%s, %s, %s, 'saida', CURRENT_DATE, %s)
        """, (usuario_id, f"Reserva para meta: {meta['titulo']}", valor, meta_id))

        conn.commit()
        return redirecionar_dashboard("Valor adicionado à meta com sucesso.", "sucesso")

    except Exception as e:
        if conn:
            conn.rollback()
        logger.exception(f"Erro ao adicionar valor à meta {meta_id} para usuário {usuario_id}: {e}")
        return redirecionar_dashboard("Não foi possível adicionar o valor à meta. Tente novamente.", "erro")
    finally:
        if conn:
            conn.close()


@metas_bp.route("/retirar_valor_meta/<int:meta_id>", methods=["POST"])
@login_required
def retirar_valor_meta(meta_id):
    usuario_id = session["usuario_id"]
    valor_str = request.form.get("valor_retirar", "").strip()

    if not valor_str:
        return redirecionar_dashboard("Informe um valor para retirar da meta.", "erro")

    valor, erro = parse_valor(valor_str)
    if erro:
        return redirecionar_dashboard("Valor inválido para retirar da meta.", "erro")

    conn = None
    try:
        conn = conectar()
        cur = conn.cursor()

        cur.execute("""
            SELECT id, titulo, valor_atual
            FROM metas
            WHERE id = %s AND usuario_id = %s
        """, (meta_id, usuario_id))
        meta = cur.fetchone()

        if not meta:
            return redirecionar_dashboard("Meta não encontrada.", "erro")

        valor_atual = Decimal(meta["valor_atual"] or 0)

        if valor_atual < valor:
            return redirecionar_dashboard("Valor insuficiente na meta.", "erro")

        novo_valor_atual = valor_atual - valor

        cur.execute("""
            UPDATE metas
            SET valor_atual = %s
            WHERE id = %s AND usuario_id = %s
        """, (novo_valor_atual, meta_id, usuario_id))

        cur.execute("""
            INSERT INTO transacoes (usuario_id, descricao, valor, tipo, data, meta_id)
            VALUES (%s, %s, %s, 'entrada', CURRENT_DATE, %s)
        """, (usuario_id, f"Retirada da meta: {meta['titulo']}", valor, meta_id))

        conn.commit()
        return redirecionar_dashboard("Valor retirado da meta com sucesso.", "sucesso")

    except Exception as e:
        if conn:
            conn.rollback()
        logger.exception(f"Erro ao retirar valor da meta {meta_id} para usuário {usuario_id}: {e}")
        return redirecionar_dashboard("Não foi possível retirar o valor da meta. Tente novamente.", "erro")
    finally:
        if conn:
            conn.close()


@metas_bp.route("/editar_meta/<int:meta_id>", methods=["POST"])
@login_required
def editar_meta(meta_id):
    usuario_id = session["usuario_id"]
    titulo = request.form.get("titulo", "").strip()
    valor_meta = request.form.get("valor_meta", "").strip()

    titulo, erro = validar_titulo(titulo)
    if erro:
        return redirecionar_dashboard(erro, "erro")

    valor_meta, erro = parse_valor(valor_meta)
    if erro:
        return redirecionar_dashboard("Valor da meta inválido." if erro == "Valor inválido." else erro, "erro")

    conn = None
    try:
        conn = conectar()
        cur = conn.cursor()

        cur.execute("""
            SELECT id, titulo, valor_atual
            FROM metas
            WHERE id = %s AND usuario_id = %s
        """, (meta_id, usuario_id))
        meta = cur.fetchone()

        if not meta:
            return redirecionar_dashboard("Meta não encontrada.", "erro")

        if Decimal(meta["valor_atual"] or 0) > valor_meta:
            return redirecionar_dashboard("O novo valor da meta não pode ser menor que o valor já guardado.", "erro")

        if meta_duplicada(cur, usuario_id, titulo, meta_id):
            return redirecionar_dashboard("Essa meta já existe.", "erro")

        titulo_antigo = meta["titulo"]

        cur.execute("""
            UPDATE metas
            SET titulo = %s, valor_meta = %s
            WHERE id = %s AND usuario_id = %s
        """, (titulo, valor_meta, meta_id, usuario_id))

        nome_saida_antigo, nome_entrada_antigo = nomes_categorias_meta(titulo_antigo)
        nome_saida_novo, nome_entrada_novo = nomes_categorias_meta(titulo)

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
              AND meta_id = %s
              AND descricao = %s
        """, (
            f"Reserva para meta: {titulo}",
            usuario_id,
            meta_id,
            f"Reserva para meta: {titulo_antigo}"
        ))

        cur.execute("""
            UPDATE transacoes
            SET descricao = %s
            WHERE usuario_id = %s
              AND meta_id = %s
              AND descricao = %s
        """, (
            f"Retirada da meta: {titulo}",
            usuario_id,
            meta_id,
            f"Retirada da meta: {titulo_antigo}"
        ))

        conn.commit()
        return redirecionar_dashboard("Meta atualizada com sucesso.", "sucesso")

    except Exception as e:
        if conn:
            conn.rollback()
        logger.exception(f"Erro ao atualizar meta {meta_id} para usuário {usuario_id}: {e}")
        return redirecionar_dashboard("Não foi possível atualizar a meta. Tente novamente.", "erro")
    finally:
        if conn:
            conn.close()


@metas_bp.route("/delete_meta/<int:meta_id>", methods=["POST"])
@login_required
def delete_meta(meta_id):
    usuario_id = session["usuario_id"]
    conn = None

    try:
        conn = conectar()
        cur = conn.cursor()

        cur.execute("""
            SELECT id, titulo
            FROM metas
            WHERE id = %s AND usuario_id = %s
        """, (meta_id, usuario_id))
        meta = cur.fetchone()

        if not meta:
            return redirecionar_dashboard("Meta não encontrada.", "erro")

        titulo_meta = meta["titulo"]
        nome_saida, nome_entrada = nomes_categorias_meta(titulo_meta)

        cur.execute("""
            DELETE FROM transacoes
            WHERE usuario_id = %s
              AND (
                  meta_id = %s
                  OR descricao IN (%s, %s)
              )
        """, (
            usuario_id,
            meta_id,
            f"Reserva para meta: {titulo_meta}",
            f"Retirada da meta: {titulo_meta}",
        ))

        cur.execute("""
            DELETE FROM categorias
            WHERE usuario_id = %s
              AND nome IN (%s, %s)
              AND NOT EXISTS (
                  SELECT 1 FROM transacoes t
                  WHERE t.usuario_id = categorias.usuario_id
                    AND t.categoria_id = categorias.id
              )
        """, (usuario_id, nome_saida, nome_entrada))

        cur.execute("""
            DELETE FROM metas
            WHERE id = %s AND usuario_id = %s
        """, (meta_id, usuario_id))

        conn.commit()
        return redirecionar_dashboard("Meta excluída com sucesso.", "sucesso")

    except Exception as e:
        if conn:
            conn.rollback()
        logger.exception(f"Erro ao excluir meta {meta_id} para usuário {usuario_id}: {e}")
        return redirecionar_dashboard("Não foi possível excluir a meta. Tente novamente.", "erro")
    finally:
        if conn:
            conn.close()
