from flask import Blueprint, request, redirect, url_for, session, flash
import logging
from decorators import login_required
from db import conectar
from datetime import datetime, date
import calendar

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

gastos_fixos_bp = Blueprint("gastos_fixos", __name__)

def redirecionar_dashboard(mensagem, categoria):
    flash(mensagem, categoria)
    return redirect(url_for("dashboard.app_dashboard"))


@gastos_fixos_bp.route("/add_gasto_fixo", methods=["POST"])
@login_required
def add_gasto_fixo():
    usuario_id = session["usuario_id"]
    descricao = request.form.get("descricao", "").strip()
    valor = request.form.get("valor", "").strip()
    categoria_id = request.form.get("categoria_id", "").strip()
    dia_vencimento = request.form.get("dia_vencimento", "").strip()

    if not descricao or not valor or not dia_vencimento:
        return redirecionar_dashboard("Preencha os campos do gasto fixo.", "erro")

    try:
        valor = float(valor)
    except ValueError:
        return redirecionar_dashboard("Valor inválido.", "erro")

    if valor <= 0:
        return redirecionar_dashboard("O valor deve ser maior que zero.", "erro")

    try:
        dia_vencimento = int(dia_vencimento)
    except ValueError:
        return redirecionar_dashboard("Dia de vencimento inválido.", "erro")

    if dia_vencimento < 1 or dia_vencimento > 31:
        return redirecionar_dashboard("O dia de vencimento deve estar entre 1 e 31.", "erro")

    try:
        categoria_id = int(categoria_id) if categoria_id else None
    except ValueError:
        return redirecionar_dashboard("Categoria inválida.", "erro")

    conn = None
    try:
        conn = conectar()
        cur = conn.cursor()

        if categoria_id:
            cur.execute("""
                SELECT id
                FROM categorias
                WHERE id = %s AND usuario_id = %s
            """, (categoria_id, usuario_id))
            if not cur.fetchone():
                return redirecionar_dashboard("Categoria não encontrada.", "erro")

        cur.execute("""
            INSERT INTO gastos_fixos (usuario_id, descricao, valor, categoria_id, dia_vencimento, ativo)
            VALUES (%s, %s, %s, %s, %s, TRUE)
        """, (usuario_id, descricao, valor, categoria_id, dia_vencimento))

        conn.commit()
        return redirecionar_dashboard("Gasto fixo adicionado com sucesso.", "sucesso")

    except Exception as e:
        if conn:
            conn.rollback()
        logger.exception(f"Erro ao adicionar gasto fixo para usuário {usuario_id}: {e}")
        return redirecionar_dashboard("Não foi possível salvar o gasto fixo. Tente novamente.", "erro")
    finally:
        if conn:
            conn.close()


@gastos_fixos_bp.route("/toggle_gasto_fixo/<int:gasto_id>", methods=["POST"])
@login_required
def toggle_gasto_fixo(gasto_id):
    usuario_id = session["usuario_id"]
    conn = None

    try:
        conn = conectar()
        cur = conn.cursor()

        cur.execute("""
            UPDATE gastos_fixos
            SET ativo = NOT ativo
            WHERE id = %s AND usuario_id = %s
        """, (gasto_id, usuario_id))
        conn.commit()

        if cur.rowcount == 0:
            flash("Gasto fixo não encontrado.", "erro")
        else:
            flash("Status do gasto fixo atualizado.", "sucesso")

    except Exception as e:
        if conn:
            conn.rollback()
        logger.exception(f"Erro ao atualizar gasto fixo {gasto_id} para usuário {usuario_id}: {e}")
        flash("Não foi possível atualizar o gasto fixo. Tente novamente.", "erro")
    finally:
        if conn:
            conn.close()

    return redirect(url_for("dashboard.app_dashboard"))


@gastos_fixos_bp.route("/excluir_gasto_fixo/<int:gasto_id>", methods=["POST"])
@login_required
def excluir_gasto_fixo(gasto_id):
    usuario_id = session["usuario_id"]
    conn = None

    try:
        conn = conectar()
        cur = conn.cursor()

        cur.execute("""
            DELETE FROM gastos_fixos
            WHERE id = %s AND usuario_id = %s
        """, (gasto_id, usuario_id))
        conn.commit()

        if cur.rowcount == 0:
            flash("Gasto fixo não encontrado.", "erro")
        else:
            flash("Gasto fixo excluído com sucesso.", "sucesso")

    except Exception as e:
        if conn:
            conn.rollback()
        logger.exception(f"Erro ao excluir gasto fixo {gasto_id} para usuário {usuario_id}: {e}")
        flash("Não foi possível excluir o gasto fixo. Tente novamente.", "erro")
    finally:
        if conn:
            conn.close()

    return redirect(url_for("dashboard.app_dashboard"))


@gastos_fixos_bp.route("/lancar_gastos_fixos_mes", methods=["POST"])
@login_required
def lancar_gastos_fixos_mes():
    usuario_id = session["usuario_id"]
    mes_referencia = request.form.get("mes", "").strip() or date.today().strftime("%Y-%m")

    try:
        datetime.strptime(mes_referencia, "%Y-%m")
    except ValueError:
        flash("Formato de mês inválido.", "erro")
        return redirect(url_for("dashboard.app_dashboard"))

    conn = None
    try:
        conn = conectar()
        cur = conn.cursor()

        cur.execute("""
            SELECT id, descricao, valor, categoria_id, dia_vencimento
            FROM gastos_fixos
            WHERE usuario_id = %s AND ativo = TRUE
        """, (usuario_id,))
        gastos_fixos = cur.fetchall()

        lancados = 0
        ano, mes = map(int, mes_referencia.split("-"))
        ultimo_dia = calendar.monthrange(ano, mes)[1]

        for gasto in gastos_fixos:
            cur.execute("""
                SELECT id
                FROM transacoes
                WHERE usuario_id = %s
                  AND gasto_fixo_id = %s
                  AND referencia_mes = %s
            """, (usuario_id, gasto["id"], mes_referencia))

            if cur.fetchone():
                continue

            dia = min(int(gasto["dia_vencimento"]), ultimo_dia)
            data_transacao = date(ano, mes, dia)

            cur.execute("""
                INSERT INTO transacoes
                    (usuario_id, descricao, valor, tipo, categoria_id, data, gasto_fixo_id, referencia_mes)
                VALUES (%s, %s, %s, 'saida', %s, %s, %s, %s)
            """, (
                usuario_id,
                gasto["descricao"],
                gasto["valor"],
                gasto["categoria_id"],
                data_transacao,
                gasto["id"],
                mes_referencia,
            ))
            lancados += 1

        conn.commit()

        if lancados:
            flash(f"{lancados} gasto(s) fixo(s) lançado(s) com sucesso.", "sucesso")
        else:
            flash("Todos os gastos fixos já foram lançados neste mês.", "aviso")

    except Exception as e:
        if conn:
            conn.rollback()
        logger.exception(f"Erro ao lançar gastos fixos para usuário {usuario_id}: {e}")
        flash("Não foi possível lançar os gastos fixos. Tente novamente.", "erro")
    finally:
        if conn:
            conn.close()

    return redirect(url_for("dashboard.app_dashboard"))
