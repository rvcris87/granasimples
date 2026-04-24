from functools import wraps
from flask import session, redirect, url_for, request
from urllib.parse import urlparse


def is_safe_url(target):
    """
    Valida se a URL é segura (rota interna) para evitar open redirect.
    """
    if not target:
        return False
    
    # Verificar se é URL absoluta ou começa com //, indicando possível open redirect
    parsed = urlparse(target)
    if parsed.netloc or parsed.scheme:
        return False
    
    # Só permitir rotas locais (começam com /)
    return target.startswith('/')


def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if "usuario_id" not in session:
            # Preservar URL original para redirecionar após login bem-sucedido
            next_url = request.args.get('next')
            if next_url and is_safe_url(next_url):
                return redirect(url_for("auth.login", next=next_url))
            return redirect(url_for("auth.login"))
        return f(*args, **kwargs)
    return decorated_function