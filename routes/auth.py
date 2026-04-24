from flask import Blueprint, render_template, request, redirect, url_for, session
from werkzeug.security import generate_password_hash, check_password_hash

from db import conectar
from utils import (
    email_valido,
    senha_valida,
    nome_valido,
    verificar_bloqueio,
    registrar_tentativa,
    resetar_tentativas,
)

auth_bp = Blueprint("auth", __name__)


@auth_bp.route("/login", methods=["GET", "POST"])
def login():
    erro = None

    if request.method == "POST":
        email = request.form.get("email", "").strip().lower()
        senha = request.form.get("senha", "")

        if not email_valido(email):
            erro = "Digite um email válido."
            return render_template("login.html", erro=erro)

        if verificar_bloqueio(email):
            erro = "Muitas tentativas. Tente novamente em alguns minutos."
            return render_template("login.html", erro=erro)

        conn = conectar()
        cur = conn.cursor()

        cur.execute("""
            SELECT id, nome, senha
            FROM usuarios
            WHERE email = %s
        """, (email,))
        usuario = cur.fetchone()
        conn.close()

        if usuario and check_password_hash(usuario["senha"], senha):
            resetar_tentativas(email)

            session.clear()
            session.permanent = True
            session["usuario_id"] = usuario["id"]
            session["usuario_nome"] = usuario["nome"]

            return redirect(url_for("dashboard.app_dashboard"))
        else:
            registrar_tentativa(email)
            erro = "Email ou senha inválidos."

    return render_template("login.html", erro=erro)


@auth_bp.route("/register", methods=["GET", "POST"])
def register():
    erro = None

    if request.method == "POST":
        nome = request.form.get("nome", "").strip()
        email = request.form.get("email", "").strip().lower()
        senha = request.form.get("senha", "")

        if not nome_valido(nome):
            erro = "O nome deve ter pelo menos 2 caracteres."
            return render_template("register.html", erro=erro)

        if not email_valido(email):
            erro = "Digite um email válido."
            return render_template("register.html", erro=erro)

        if not senha_valida(senha):
            erro = "A senha deve ter pelo menos 8 caracteres."
            return render_template("register.html", erro=erro)

        conn = conectar()
        cur = conn.cursor()

        cur.execute("""
            SELECT id
            FROM usuarios
            WHERE email = %s
        """, (email,))
        usuario_existente = cur.fetchone()

        if usuario_existente:
            conn.close()
            erro = "Esse email já está cadastrado."
            return render_template("register.html", erro=erro)

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
        conn.close()

        session.clear()
        session.permanent = True
        session["usuario_id"] = usuario["id"]
        session["usuario_nome"] = usuario["nome"]

        return redirect(url_for("dashboard.app_dashboard"))

    return render_template("register.html", erro=erro)


@auth_bp.route("/logout", methods=["POST"])
def logout():
    session.clear()
    return redirect(url_for("home"))
