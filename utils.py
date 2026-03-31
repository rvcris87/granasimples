import re
from datetime import datetime, timedelta
from db import conectar


def email_valido(email):
    padrao = r"^[^@\s]+@[^@\s]+\.[^@\s]+$"
    return re.match(padrao, email) is not None


def senha_valida(senha):
    return len(senha) >= 8


def nome_valido(nome):
    return len(nome.strip()) >= 2


def verificar_bloqueio(email):
    conn = conectar()
    cur = conn.cursor()

    cur.execute("""
        SELECT tentativas, bloqueado_ate
        FROM login_tentativas
        WHERE email = %s
    """, (email,))

    dados = cur.fetchone()
    conn.close()

    if dados and dados["bloqueado_ate"]:
        if datetime.now() < dados["bloqueado_ate"]:
            return True

    return False


def registrar_tentativa(email):
    conn = conectar()
    cur = conn.cursor()

    cur.execute("""
        SELECT tentativas
        FROM login_tentativas
        WHERE email = %s
    """, (email,))
    dados = cur.fetchone()

    if dados:
        tentativas = int(dados["tentativas"]) + 1

        if tentativas >= 5:
            bloqueio = datetime.now() + timedelta(minutes=15)
            cur.execute("""
                UPDATE login_tentativas
                SET tentativas = %s, bloqueado_ate = %s
                WHERE email = %s
            """, (tentativas, bloqueio, email))
        else:
            cur.execute("""
                UPDATE login_tentativas
                SET tentativas = %s
                WHERE email = %s
            """, (tentativas, email))
    else:
        cur.execute("""
            INSERT INTO login_tentativas (email, tentativas, bloqueado_ate)
            VALUES (%s, 1, NULL)
        """, (email,))

    conn.commit()
    conn.close()


def resetar_tentativas(email):
    conn = conectar()
    cur = conn.cursor()

    cur.execute("""
        DELETE FROM login_tentativas
        WHERE email = %s
    """, (email,))

    conn.commit()
    conn.close()


def calcular_dados_dashboard(usuario_id, mes=""):
    conn = conectar()
    cur = conn.cursor()

    if mes:
        cur.execute("""
        SELECT
            t.*,
            c.nome AS categoria_nome,
            c.tipo AS categoria_tipo
        FROM transacoes t
        LEFT JOIN categorias c ON t.categoria_id = c.id
        WHERE t.usuario_id = %s
          AND TO_CHAR(t.data, 'YYYY-MM') = %s
        ORDER BY t.data DESC, t.id DESC
    """, (usuario_id, mes))
    else:
        cur.execute("""
        SELECT
            t.*,
            c.nome AS categoria_nome,
            c.tipo AS categoria_tipo
        FROM transacoes t
        LEFT JOIN categorias c ON t.categoria_id = c.id
        WHERE t.usuario_id = %s
        ORDER BY t.data DESC, t.id DESC
    """, (usuario_id,))

    transacoes = cur.fetchall()

    cur.execute("""
        SELECT * FROM metas
        WHERE usuario_id = %s
        ORDER BY id DESC
    """, (usuario_id,))
    metas = cur.fetchall()

    conn.close()

    total_entradas = sum(float(t["valor"]) for t in transacoes if t["tipo"] == "entrada")
    total_saidas = sum(float(t["valor"]) for t in transacoes if t["tipo"] == "saida")
    saldo = total_entradas - total_saidas

    gastos_por_categoria = {}
    for t in transacoes:
        if t["tipo"] == "saida":
            categoria = t["categoria_nome"] if t["categoria_nome"] else "Sem categoria"
            gastos_por_categoria[categoria] = gastos_por_categoria.get(categoria, 0) + float(t["valor"])

    categorias_labels = list(gastos_por_categoria.keys())
    categorias_valores = list(gastos_por_categoria.values())

    insights = []

    if total_saidas > 0 and gastos_por_categoria:
        maior_categoria = max(gastos_por_categoria, key=gastos_por_categoria.get)
        maior_valor = gastos_por_categoria[maior_categoria]
        insights.append(f"Sua maior categoria de gasto foi {maior_categoria}, com R$ {maior_valor:.2f}.")

    if total_saidas > total_entradas:
        insights.append("Você gastou mais do que entrou neste período.")
    elif total_entradas > total_saidas and total_entradas > 0:
        insights.append("Seu saldo ficou positivo neste período.")

    if saldo < 0:
        insights.append("Seu saldo está negativo. Vale revisar suas saídas.")
    elif saldo > 0:
        insights.append("Você ainda tem saldo disponível neste período.")

    if not insights:
        insights.append("Adicione mais transações para receber insights automáticos.")

    return {
        "transacoes": transacoes,
        "metas": metas,
        "total_entradas": total_entradas,
        "total_saidas": total_saidas,
        "saldo": saldo,
        "categorias_labels": categorias_labels,
        "categorias_valores": categorias_valores,
        "insights": insights
    }

def buscar_categorias(usuario_id, tipo=None):
    conn = conectar()
    cur = conn.cursor()

    if tipo:
        cur.execute("""
            SELECT id, nome, tipo
            FROM categorias
            WHERE usuario_id = %s AND tipo = %s
            ORDER BY nome ASC
        """, (usuario_id, tipo))
    else:
        cur.execute("""
            SELECT id, nome, tipo
            FROM categorias
            WHERE usuario_id = %s
            ORDER BY tipo ASC, nome ASC
        """, (usuario_id,))

    categorias = cur.fetchall()
    conn.close()

    return categorias