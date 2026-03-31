import os
from datetime import timedelta
from flask import Flask, render_template
from dotenv import load_dotenv
from flask_wtf.csrf import CSRFProtect

from routes.auth import auth_bp
from routes.dashboard import dashboard_bp
from routes.transacoes import transacoes_bp
from routes.metas import metas_bp
from routes.categorias import categorias_bp

load_dotenv(dotenv_path=".env")

app = Flask(__name__)
app.secret_key = os.getenv("SECRET_KEY", "granasimples_secret_key")

csrf = CSRFProtect(app)

app.config["SESSION_COOKIE_HTTPONLY"] = True
app.config["SESSION_COOKIE_SAMESITE"] = "Lax"
app.config["PERMANENT_SESSION_LIFETIME"] = timedelta(hours=2)
app.config["SESSION_COOKIE_SECURE"] = False
app.config["PROPAGATE_EXCEPTIONS"] = False

app.register_blueprint(auth_bp)
app.register_blueprint(dashboard_bp)
app.register_blueprint(transacoes_bp)
app.register_blueprint(metas_bp)
app.register_blueprint(categorias_bp)


@app.route("/")
def home():
    return render_template("landing.html")


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


if __name__ == "__main__":
    debug_mode = os.getenv("FLASK_DEBUG", "False").lower() == "true"
    app.run(debug=debug_mode)