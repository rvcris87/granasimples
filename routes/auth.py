from flask import Blueprint, render_template, request, redirect, url_for, session
from werkzeug.security import generate_password_hash, check_password_hash
import logging

from db import conectar
from decorators import is_safe_url
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

                # Redirecionar para 'next' se fornecido e seguro, caso contrário para dashboard
                next_url = request.args.get('next') or request.form.get('next')
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
                INSERT INTO usuarios (nome, email, senha)
                VALUES (%s, %s, %s)
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
def logout():
    session.clear()
    return redirect(url_for("home"))
