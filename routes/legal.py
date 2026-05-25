from flask import Blueprint, render_template

legal_bp = Blueprint("legal", __name__)


@legal_bp.route("/privacidade")
def privacidade():
    return render_template("privacidade.html")


@legal_bp.route("/termos")
def termos():
    return render_template("termos.html")
