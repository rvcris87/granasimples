import os
import psycopg2
from psycopg2.extras import RealDictCursor


class DatabaseConfigError(RuntimeError):
    pass


def conectar():
    campos_obrigatorios = {
        "DB_HOST": os.getenv("DB_HOST", "").strip(),
        "DB_NAME": os.getenv("DB_NAME", "").strip(),
        "DB_USER": os.getenv("DB_USER", "").strip(),
        "DB_PASSWORD": os.getenv("DB_PASSWORD", "").strip(),
        "DB_PORT": os.getenv("DB_PORT", "").strip(),
    }
    campos_ausentes = [campo for campo, valor in campos_obrigatorios.items() if not valor]

    if campos_ausentes:
        raise DatabaseConfigError(
            "Configuração do banco incompleta: " + ", ".join(campos_ausentes)
        )

    return psycopg2.connect(
        host=campos_obrigatorios["DB_HOST"],
        dbname=campos_obrigatorios["DB_NAME"],
        user=campos_obrigatorios["DB_USER"],
        password=campos_obrigatorios["DB_PASSWORD"],
        port=campos_obrigatorios["DB_PORT"],
        sslmode="require",
        cursor_factory=RealDictCursor
    )
