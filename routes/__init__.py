"""
Routes package para GranaSimples.
Centraliza importação de blueprints da aplicação.
"""

from routes.auth import auth_bp
from routes.dashboard import dashboard_bp
from routes.transacoes import transacoes_bp
from routes.metas import metas_bp
from routes.categorias import categorias_bp
from routes.gastos_fixos import gastos_fixos_bp

__all__ = [
    'auth_bp',
    'dashboard_bp',
    'transacoes_bp',
    'metas_bp',
    'categorias_bp',
    'gastos_fixos_bp',
]
