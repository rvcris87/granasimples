import os
import psycopg2
from psycopg2.extras import RealDictCursor


def conectar():
    return psycopg2.connect(
        host=os.getenv("DB_HOST", "").strip(),
        dbname=os.getenv("DB_NAME", "").strip(),
        user=os.getenv("DB_USER", "").strip(),
        password=os.getenv("DB_PASSWORD", "").strip(),
        port=os.getenv("DB_PORT", "").strip(),
        sslmode="require",
        cursor_factory=RealDictCursor
    )