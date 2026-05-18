import os
from datetime import timedelta
from pathlib import Path
from flask import Flask, flash, redirect, render_template, request, session, url_for
from dotenv import load_dotenv
from flask_wtf.csrf import CSRFProtect, CSRFError

from routes import (
    auth_bp,
    dashboard_bp,
    transacoes_bp,
    metas_bp,
    categorias_bp,
    gastos_fixos_bp,
)

base_dir = Path(__file__).resolve().parent
load_dotenv(dotenv_path=base_dir / ".env")

app = Flask(__name__)
secret_key = os.getenv("SECRET_KEY", "").strip()
debug_mode = os.getenv("FLASK_DEBUG", "False").lower() == "true"
is_production = os.getenv("FLASK_ENV", "").lower() == "production"

if not secret_key:
    if is_production:
        raise RuntimeError("SECRET_KEY deve ser configurada em produção.")
    secret_key = "dev-only-granasimples-secret-key"

if is_production and secret_key == "granasimples_secret_key":
    raise RuntimeError("SECRET_KEY padrão não pode ser usada em produção.")

app.secret_key = secret_key

csrf = CSRFProtect(app)

app.config["SESSION_COOKIE_HTTPONLY"] = True
app.config["SESSION_COOKIE_SAMESITE"] = "Lax"
app.config["PERMANENT_SESSION_LIFETIME"] = timedelta(hours=2)
app.config["SESSION_COOKIE_SECURE"] = is_production
app.config["PROPAGATE_EXCEPTIONS"] = False

app.register_blueprint(auth_bp)
app.register_blueprint(dashboard_bp)
app.register_blueprint(transacoes_bp)
app.register_blueprint(metas_bp)
app.register_blueprint(categorias_bp)
app.register_blueprint(gastos_fixos_bp)


@app.route("/")
def home():
    return render_template("landing.html")


@app.after_request
def aplicar_headers_cache(response):
    if request.endpoint == "dashboard.app_dashboard":
        response.headers["Cache-Control"] = "no-store, no-cache, must-revalidate, max-age=0"
        response.headers["Pragma"] = "no-cache"
        response.headers["Expires"] = "0"
    return response


@app.errorhandler(400)
def erro_400(e):
    return render_template("erro.html", codigo=400, titulo="Requisição inválida", mensagem="A solicitação não pôde ser processada."), 400


@app.errorhandler(403)
def erro_403(e):
    return render_template("erro.html", codigo=403, titulo="Acesso negado", mensagem="Você não tem permissão para acessar este recurso."), 403


@app.errorhandler(404)
def erro_404(e):
    return render_template("erro.html", codigo=404, titulo="Página não encontrada", mensagem="A página que você tentou acessar não existe."), 404


@app.errorhandler(500)
def erro_500(e):
    return render_template("erro.html", codigo=500, titulo="Erro interno", mensagem="Ocorreu um erro interno. Tente novamente em instantes."), 500

@app.errorhandler(CSRFError)
def handle_csrf_error(e):
    if session.get("usuario_id"):
        flash("Sua sessão do formulário expirou. Recarregamos o painel; tente a ação novamente.", "erro")
        return redirect(url_for("dashboard.app_dashboard"))

    if request.endpoint in {"auth.login", "auth.register"}:
        return render_template(
            request.endpoint.split(".")[-1] + ".html",
            erro="Sua sessão expirou. Recarregue a página e tente novamente."
        ), 400

    return render_template(
        "erro.html",
        codigo=400,
        titulo="Sessão expirada",
        mensagem="Sua sessão expirou ou o formulário perdeu a validade. Recarregue a página e tente novamente."
    ), 400

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=debug_mode)
