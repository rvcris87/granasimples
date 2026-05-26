from flask import Blueprint, render_template, request, redirect, url_for, session
from werkzeug.security import generate_password_hash, check_password_hash
import logging

from db import conectar
from decorators import is_safe_url, login_required
from utils import (
    email_valido,
    senha_valida,
    nome_valido,
    verificar_bloqueio,
    registrar_tentativa,
    resetar_tentativas,
)

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

auth_bp = Blueprint("auth", __name__)


@auth_bp.route("/login", methods=["GET", "POST"])
def login():
    erro = None
    email = ""

    if "usuario_id" in session:
        return redirect(url_for("dashboard.app_dashboard"))

    if request.method == "POST":
        email = request.form.get("email", "").strip().lower()
        senha = request.form.get("senha", "")

        if not email_valido(email):
            erro = "Digite um email válido."
            return render_template("login.html", erro=erro, email=email)

        if verificar_bloqueio(email):
            erro = "Muitas tentativas. Tente novamente em alguns minutos."
            return render_template("login.html", erro=erro, email=email)

        conn = None
        try:
            conn = conectar()
            cur = conn.cursor()

            cur.execute("""
                SELECT id, nome, senha
                FROM usuarios
                WHERE email = %s
            """, (email,))
            usuario = cur.fetchone()

            if usuario and check_password_hash(usuario["senha"], senha):
                resetar_tentativas(email)

                session.clear()
                session.permanent = True
                session["usuario_id"] = usuario["id"]
                session["usuario_nome"] = usuario["nome"]

                next_url = request.args.get("next") or request.form.get("next")
                if next_url and is_safe_url(next_url):
                    return redirect(next_url)
                return redirect(url_for("dashboard.app_dashboard"))
            else:
                registrar_tentativa(email)
                erro = "Email ou senha inválidos."

        except Exception as e:
            logger.exception(f"Erro ao fazer login: {e}")
            erro = "Não foi possível processar o login. Tente novamente."
        finally:
            if conn:
                conn.close()

    return render_template("login.html", erro=erro, email=email)


@auth_bp.route("/register", methods=["GET", "POST"])
def register():
    erro = None
    nome = ""
    email = ""

    if "usuario_id" in session:
        return redirect(url_for("dashboard.app_dashboard"))

    if request.method == "POST":
        nome = request.form.get("nome", "").strip()
        email = request.form.get("email", "").strip().lower()
        senha = request.form.get("senha", "")
        confirmar_senha = request.form.get("confirmar_senha", "")

        if not nome_valido(nome):
            erro = "O nome deve ter pelo menos 2 caracteres."
            return render_template("register.html", erro=erro, nome=nome, email=email)

        if not email_valido(email):
            erro = "Digite um email válido."
            return render_template("register.html", erro=erro, nome=nome, email=email)

        if not senha_valida(senha):
            erro = "A senha deve ter pelo menos 8 caracteres."
            return render_template("register.html", erro=erro, nome=nome, email=email)

        if senha != confirmar_senha:
            erro = "As senhas não conferem."
            return render_template("register.html", erro=erro, nome=nome, email=email)

        if not request.form.get("aceitar_termos"):
            erro = "Você precisa aceitar os Termos de Uso e a Política de Privacidade para criar uma conta."
            return render_template("register.html", erro=erro, nome=nome, email=email)

        conn = None
        try:
            conn = conectar()
            cur = conn.cursor()

            cur.execute("""
                SELECT id
                FROM usuarios
                WHERE email = %s
            """, (email,))
            usuario_existente = cur.fetchone()

            if usuario_existente:
                erro = "Esse email já está cadastrado."
                return render_template("register.html", erro=erro, nome=nome, email=email)

            senha_hash = generate_password_hash(senha)

            cur.execute("""
                INSERT INTO usuarios (nome, email, senha, consentimento_termos_em)
                VALUES (%s, %s, %s, NOW())
            """, (nome, email, senha_hash))

            conn.commit()

            cur.execute("""
                SELECT id, nome
                FROM usuarios
                WHERE email = %s
            """, (email,))
            usuario = cur.fetchone()

            session.clear()
            session.permanent = True
            session["usuario_id"] = usuario["id"]
            session["usuario_nome"] = usuario["nome"]

            return redirect(url_for("dashboard.app_dashboard"))

        except Exception as e:
            if conn:
                conn.rollback()
            logger.exception(f"Erro ao registrar usuário: {e}")
            erro = "Não foi possível criar a conta. Tente novamente."
            return render_template("register.html", erro=erro, nome=nome, email=email)
        finally:
            if conn:
                conn.close()

    return render_template("register.html", erro=erro, nome=nome, email=email)


@auth_bp.route("/logout", methods=["POST"])
@login_required
def logout():
    session.clear()
    return redirect(url_for("home"))


@auth_bp.route("/exportar-dados", methods=["GET"])
@login_required
def exportar_dados():
    import decimal
    import datetime
    import json
    from flask import Response

    usuario_id = session["usuario_id"]
    conn = None
    try:
        conn = conectar()
        cur = conn.cursor()

        def serialize_data(val):
            if isinstance(val, (datetime.datetime, datetime.date)):
                return val.isoformat()
            if isinstance(val, decimal.Decimal):
                return float(val)
            return val

        def format_rows(rows):
            return [{k: serialize_data(v) for k, v in row.items()} for row in rows]

        cur.execute("""
            SELECT id, nome, email, created_at, consentimento_termos_em
            FROM usuarios
            WHERE id = %s
        """, (usuario_id,))
        usuario_info = cur.fetchone()

        if not usuario_info:
            return "Usuário não encontrado.", 404

        export_data = {
            "perfil": {k: serialize_data(v) for k, v in usuario_info.items()},
            "exportado_em": datetime.datetime.now().isoformat(),
            "dados": {}
        }

        cur.execute("""
            SELECT id, nome, tipo
            FROM categorias
            WHERE usuario_id = %s
            ORDER BY nome
        """, (usuario_id,))
        export_data["dados"]["categorias"] = format_rows(cur.fetchall())

        cur.execute("""
            SELECT id, descricao, valor, tipo, data, categoria_id, meta_id, gasto_fixo_id
            FROM transacoes
            WHERE usuario_id = %s
            ORDER BY data DESC
        """, (usuario_id,))
        export_data["dados"]["transacoes"] = format_rows(cur.fetchall())

        cur.execute("""
            SELECT id, titulo, valor_meta, valor_atual, arquivada_em, created_at, ativo
            FROM metas
            WHERE usuario_id = %s
            ORDER BY created_at DESC
        """, (usuario_id,))
        export_data["dados"]["metas"] = format_rows(cur.fetchall())

        cur.execute("""
            SELECT id, meta_id, tipo, valor, observacao, criado_em
            FROM meta_movimentacoes
            WHERE usuario_id = %s
            ORDER BY criado_em DESC
        """, (usuario_id,))
        export_data["dados"]["meta_movimentacoes"] = format_rows(cur.fetchall())

        cur.execute("""
            SELECT id, descricao, valor, dia_vencimento, ativo, created_at
            FROM gastos_fixos
            WHERE usuario_id = %s
            ORDER BY dia_vencimento
        """, (usuario_id,))
        export_data["dados"]["gastos_fixos"] = format_rows(cur.fetchall())

        json_data = json.dumps(export_data, indent=2, ensure_ascii=False)
        filename = f"granasimples_dados_usuario_{usuario_id}.json"

        return Response(
            json_data,
            mimetype="application/json",
            headers={"Content-disposition": f"attachment; filename={filename}"}
        )

    except Exception as e:
        logger.exception(f"Erro ao exportar dados do usuário {usuario_id}: {e}")
        return "Não foi possível exportar seus dados. Tente novamente mais tarde.", 500
    finally:
        if conn:
            conn.close()


@auth_bp.route("/registrar-consentimento", methods=["POST"])
@login_required
def registrar_consentimento():
    usuario_id = session["usuario_id"]
    conn = None
    try:
        conn = conectar()
        cur = conn.cursor()
        cur.execute("""
            UPDATE usuarios
            SET consentimento_termos_em = NOW()
            WHERE id = %s
        """, (usuario_id,))
        conn.commit()
    except Exception as e:
        logger.exception(f"Erro ao registrar consentimento do usuário {usuario_id}: {e}")
        return "Não foi possível salvar o consentimento. Tente novamente.", 500
    finally:
        if conn:
            conn.close()

    return redirect(url_for("dashboard.app_dashboard"))

