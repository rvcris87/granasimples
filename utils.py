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
    from datetime import datetime, timedelta
    
    conn = conectar()
    cur = conn.cursor()

    filtro_mes = ""
    params = [usuario_id]

    if mes:
        filtro_mes = " AND TO_CHAR(t.data, 'YYYY-MM') = %s"
        params.append(mes)
        print(f"\n📊 DASHBOARD - Buscando transações para: usuário_id={usuario_id}, mês={mes}")
    else:
        print(f"\n📊 DASHBOARD - Buscando transações para: usuário_id={usuario_id}, sem filtro de mês")

    # transações
    cur.execute(f"""
        SELECT
            t.id,
            t.descricao,
            t.valor,
            t.tipo,
            t.data,
            t.categoria_id,
            c.nome AS categoria_nome
        FROM transacoes t
        LEFT JOIN categorias c ON t.categoria_id = c.id
        WHERE t.usuario_id = %s
        {filtro_mes}
        ORDER BY t.data DESC, t.id DESC
    """, params)
    transacoes = cur.fetchall()
    
    print(f"  \u2192 Transações encontradas: {len(transacoes)}")
    for t in transacoes[:3]:  # Mostrar apenas as 3 primeiras
        print(f"     - {t['descricao']}: R${t['valor']:.2f} ({t['tipo']}) em {t['data']}")

    # totais
    cur.execute(f"""
        SELECT
            COALESCE(SUM(CASE WHEN tipo = 'entrada' THEN valor ELSE 0 END), 0) AS total_entradas,
            COALESCE(SUM(CASE WHEN tipo = 'saida' THEN valor ELSE 0 END), 0) AS total_saidas
        FROM transacoes t
        WHERE t.usuario_id = %s
        {filtro_mes}
    """, params)
    totais = cur.fetchone()

    total_entradas = float(totais["total_entradas"] or 0)
    total_saidas = float(totais["total_saidas"] or 0)
    saldo = total_entradas - total_saidas
    
    print(f"  \u2192 Totais: Entradas=R${total_entradas:.2f}, Saídas=R${total_saidas:.2f}, Saldo=R${saldo:.2f}")

    # metas
    cur.execute("""
        SELECT id, titulo, valor_meta, valor_atual
        FROM metas
        WHERE usuario_id = %s
        ORDER BY id DESC
    """, (usuario_id,))
    metas = cur.fetchall()

    # gráfico por categoria REAL
    cur.execute(f"""
        SELECT
            COALESCE(c.nome, 'Sem categoria') AS categoria_nome,
            COALESCE(SUM(t.valor), 0) AS total
        FROM transacoes t
        LEFT JOIN categorias c ON t.categoria_id = c.id
        WHERE t.usuario_id = %s
          AND t.tipo = 'saida'
          {filtro_mes}
        GROUP BY COALESCE(c.nome, 'Sem categoria')
        ORDER BY total DESC
    """, params)
    dados_categorias = cur.fetchall()

    categorias_labels = [linha["categoria_nome"] for linha in dados_categorias]
    categorias_valores = [float(linha["total"]) for linha in dados_categorias]
    
    print(f"  \u2192 Categorias encontradas: {len(categorias_labels)}")
    if categorias_labels:
        print(f"     Top 3: {', '.join(f'{categorias_labels[i]} (R${categorias_valores[i]:.2f})' for i in range(min(3, len(categorias_labels))))}")

    # ==== INTELIGÊNCIA DO DASHBOARD ====
    comparacao_percentual = 0
    mensagem_comparacao = ""
    maior_categoria = ""
    maior_valor = 0.0
    alertas = []

    # 1. Comparação com mês anterior
    if mes:
        # Calcular mês anterior
        data_mes = datetime.strptime(mes, "%Y-%m")
        mes_anterior = (data_mes - timedelta(days=1)).strftime("%Y-%m")
        
        # Buscar totais do mês anterior
        cur.execute("""
            SELECT
                COALESCE(SUM(CASE WHEN tipo = 'saida' THEN valor ELSE 0 END), 0) AS saidas_anterior
            FROM transacoes t
            WHERE t.usuario_id = %s
              AND TO_CHAR(t.data, 'YYYY-MM') = %s
        """, (usuario_id, mes_anterior))
        anterior = cur.fetchone()
        saidas_anterior = float(anterior["saidas_anterior"] or 0)
        
        # Calcular variação percentual
        if saidas_anterior > 0:
            comparacao_percentual = ((total_saidas - saidas_anterior) / saidas_anterior) * 100
        elif total_saidas > 0 and saidas_anterior == 0:
            comparacao_percentual = 100
        else:
            comparacao_percentual = 0
        
        # Gerar mensagem de comparação
        if saidas_anterior > 0:
            if comparacao_percentual > 0:
                mensagem_comparacao = f"📈 Você gastou {abs(comparacao_percentual):.0f}% mais que mês passado"
            elif comparacao_percentual < 0:
                mensagem_comparacao = f"📉 Você reduziu seus gastos em {abs(comparacao_percentual):.0f}% em relação ao mês passado"
            else:
                mensagem_comparacao = "➡️ Seus gastos foram iguais ao mês passado"
        elif total_saidas > 0 and saidas_anterior == 0:
            mensagem_comparacao = "📈 Você teve gastos este mês (nenhum gasto no mês anterior)"
    
    # 2. Maior categoria de gasto
    if dados_categorias:
        maior_categoria = dados_categorias[0]["categoria_nome"]
        maior_valor = float(dados_categorias[0]["total"])
    
    # 3. Alertas
    if total_saidas > total_entradas and total_entradas > 0:
        alertas.append("⚠️ Suas saídas estão maiores que suas entradas")
    
    if mes and comparacao_percentual > 20:
        alertas.append("🔥 Seus gastos aumentaram significativamente (>20%)")
    
    if total_saidas == 0 and total_entradas == 0 and mes:
        alertas.append("ℹ️ Você não registrou movimentações neste período")

    # Manter insights existentes para compatibilidade
    insights = []
    
    if total_entradas == 0 and total_saidas == 0:
        insights.append("Você ainda não registrou movimentações neste período.")
    else:
        if saldo > 0:
            insights.append("Seu saldo está positivo neste período.")
        elif saldo < 0:
            insights.append("Suas saídas estão maiores que suas entradas.")
        else:
            insights.append("Seu saldo está zerado neste período.")

        if dados_categorias:
            insights.append(f"Sua maior categoria de gasto foi {maior_categoria}: R$ {maior_valor:.2f}.")

    conn.close()

    return {
        "transacoes": transacoes,
        "metas": metas,
        "total_entradas": total_entradas,
        "total_saidas": total_saidas,
        "saldo": saldo,
        "categorias_labels": categorias_labels,
        "categorias_valores": categorias_valores,
        "insights": insights,
        "comparacao_percentual": comparacao_percentual,
        "mensagem_comparacao": mensagem_comparacao,
        "maior_categoria": maior_categoria,
        "maior_valor": maior_valor,
        "alertas": alertas
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


# ===== NOVAS FUNCIONALIDADES =====

def calcular_tendencia_6_meses(usuario_id):
    """
    Calcula tendência financeira dos últimos 6 meses
    Retorna: labels, entradas, saidas, saldo
    """
    from datetime import datetime, timedelta
    
    conn = conectar()
    cur = conn.cursor()

    # Gerar últimos 6 meses
    hoje = datetime.now()
    meses = []
    labels = []

    for i in range(5, -1, -1):
        mes_data = hoje - timedelta(days=i*30)
        mes_str = mes_data.strftime("%Y-%m")
        label = mes_data.strftime("%b").capitalize()
        meses.append(mes_str)
        labels.append(label)

    tendencia_entradas = []
    tendencia_saidas = []
    tendencia_saldo = []

    for mes in meses:
        cur.execute("""
            SELECT
                COALESCE(SUM(CASE WHEN tipo = 'entrada' THEN valor ELSE 0 END), 0) AS total_entradas,
                COALESCE(SUM(CASE WHEN tipo = 'saida' THEN valor ELSE 0 END), 0) AS total_saidas
            FROM transacoes
            WHERE usuario_id = %s
              AND TO_CHAR(data, 'YYYY-MM') = %s
        """, (usuario_id, mes))
        
        resultado = cur.fetchone()
        entradas = float(resultado["total_entradas"] or 0)
        saidas = float(resultado["total_saidas"] or 0)
        saldo = entradas - saidas

        tendencia_entradas.append(entradas)
        tendencia_saidas.append(saidas)
        tendencia_saldo.append(saldo)

    conn.close()

    return {
        "labels": labels,
        "entradas": tendencia_entradas,
        "saidas": tendencia_saidas,
        "saldo": tendencia_saldo
    }


def calcular_previsao_gastos(usuario_id):
    """
    Calcula previsão de gastos baseada em média móvel (últimos 3 meses)
    """
    from datetime import datetime, timedelta
    
    conn = conectar()
    cur = conn.cursor()

    hoje = datetime.now()
    meses = []

    for i in range(3, 0, -1):
        mes_data = hoje - timedelta(days=i*30)
        mes_str = mes_data.strftime("%Y-%m")
        meses.append(mes_str)

    gastos = []

    for mes in meses:
        cur.execute("""
            SELECT COALESCE(SUM(valor), 0) AS total
            FROM transacoes
            WHERE usuario_id = %s
              AND tipo = 'saida'
              AND TO_CHAR(data, 'YYYY-MM') = %s
        """, (usuario_id, mes))
        
        resultado = cur.fetchone()
        gasto = float(resultado["total"] or 0)
        gastos.append(gasto)

    conn.close()

    # Calcular média
    if gastos and sum(gastos) > 0:
        media_previsao = sum(gastos) / len(gastos)
        mensagem = f"Com base nos últimos 3 meses, sua previsão de gastos para o próximo mês é R$ {media_previsao:.2f}"
    else:
        media_previsao = 0
        mensagem = "Dados insuficientes para gerar previsão de gastos."

    return {
        "valor": media_previsao,
        "mensagem": mensagem
    }


def calcular_alertas_metas(usuario_id):
    """
    Compara metas cadastradas com gastos reais do mês atual
    Retorna alertas se ultrapassou ou está próximo de alcançar
    """
    from datetime import datetime
    
    conn = conectar()
    cur = conn.cursor()

    mes_atual = datetime.now().strftime("%Y-%m")
    alertas_metas = []

    # Buscar todas as metas
    cur.execute("""
        SELECT id, titulo, valor_meta, valor_atual
        FROM metas
        WHERE usuario_id = %s
    """, (usuario_id,))
    metas = cur.fetchall()

    for meta in metas:
        meta_id = meta["id"]
        titulo = meta["titulo"]
        valor_meta = float(meta["valor_meta"] or 0)
        valor_atual = float(meta["valor_atual"] or 0)

        # Calcular percentual
        if valor_meta > 0:
            percentual = (valor_atual / valor_meta) * 100
        else:
            percentual = 0

        # Gerar alertas
        if valor_atual > valor_meta:
            excesso = valor_atual - valor_meta
            alertas_metas.append({
                "tipo": "erro",
                "mensagem": f"🚨 Você ultrapassou a meta de {titulo} em R$ {excesso:.2f}"
            })
        elif percentual >= 80:
            alertas_metas.append({
                "tipo": "aviso",
                "mensagem": f"⚠️ Você já usou {percentual:.0f}% da meta de {titulo}"
            })

    conn.close()

    return alertas_metas


def buscar_gastos_fixos(usuario_id):
    """
    Busca todos os gastos fixos do usuário ordenados por dia de vencimento
    """
    conn = conectar()
    cur = conn.cursor()

    cur.execute("""
        SELECT
            gf.id,
            gf.descricao,
            gf.valor,
            gf.categoria_id,
            gf.dia_vencimento,
            gf.ativo,
            c.nome AS categoria_nome
        FROM gastos_fixos gf
        LEFT JOIN categorias c ON gf.categoria_id = c.id
        WHERE gf.usuario_id = %s
        ORDER BY gf.dia_vencimento ASC
    """, (usuario_id,))

    gastos_fixos = cur.fetchall()
    conn.close()

    return gastos_fixos


def calcular_insights_gastos_fixos(usuario_id, total_saidas):
    """
    Calcula insights sobre gastos fixos do usuário.
    Retorna: {
        total_gastos_fixos: float,
        percentual_gastos_fixos: float ou 0,
        maior_categoria_gasto_fixo: str,
        mensagem_gastos_fixos: str,
        alertas_gastos_fixos: list
    }
    """
    conn = conectar()
    cur = conn.cursor()
    
    # 1. Buscar total de gastos fixos ATIVOS
    cur.execute("""
        SELECT
            COALESCE(SUM(valor), 0) AS total_gastos_fixos,
            COUNT(*) AS quantidade
        FROM gastos_fixos
        WHERE usuario_id = %s AND ativo = TRUE
    """, (usuario_id,))
    resultado = cur.fetchone()
    
    total_gastos_fixos = float(resultado["total_gastos_fixos"] or 0)
    quantidade_gastos_fixos = int(resultado["quantidade"] or 0)
    
    # 2. Calcular percentual em relação às saídas
    percentual_gastos_fixos = 0
    if total_saidas > 0:
        percentual_gastos_fixos = (total_gastos_fixos / total_saidas) * 100
    
    # 3. Identifi car maior categoria de gasto fixo
    cur.execute("""
        SELECT
            COALESCE(c.nome, 'Sem categoria') AS categoria_nome,
            COALESCE(SUM(gf.valor), 0) AS total
        FROM gastos_fixos gf
        LEFT JOIN categorias c ON gf.categoria_id = c.id
        WHERE gf.usuario_id = %s AND gf.ativo = TRUE
        GROUP BY c.id, c.nome
        ORDER BY total DESC
        LIMIT 1
    """, (usuario_id,))
    maior_cat = cur.fetchone()
    
    maior_categoria_gasto_fixo = maior_cat["categoria_nome"] if maior_cat else ""
    
    # 4. Gerar mensagens e alertas
    mensagem_gastos_fixos = ""
    alertas_gastos_fixos = []
    
    if quantidade_gastos_fixos == 0:
        mensagem_gastos_fixos = "Você não tem gastos fixos registrados."
    else:
        mensagem_gastos_fixos = f"Seus gastos fixos totalizam R$ {total_gastos_fixos:.2f}/mês"
        
        if percentual_gastos_fixos > 0:
            mensagem_gastos_fixos += f" ({percentual_gastos_fixos:.1f}% das suas saídas)"
        
        if maior_categoria_gasto_fixo:
            mensagem_gastos_fixos += f". A maior parte está em {maior_categoria_gasto_fixo}."
        else:
            mensagem_gastos_fixos += "."
        
        # AlertasOkay
        if percentual_gastos_fixos > 60:
            alertas_gastos_fixos.append(f"🔴 Seus gastos fixos comprometem {percentual_gastos_fixos:.0f}% das suas saídas!")
        elif percentual_gastos_fixos > 40:
            alertas_gastos_fixos.append(f"🟡 Seus gastos fixos representam {percentual_gastos_fixos:.0f}% das suas saídas.")
    
    conn.close()
    
    return {
        "total_gastos_fixos": total_gastos_fixos,
        "quantidade_gastos_fixos": quantidade_gastos_fixos,
        "percentual_gastos_fixos": percentual_gastos_fixos,
        "maior_categoria_gasto_fixo": maior_categoria_gasto_fixo,
        "mensagem_gastos_fixos": mensagem_gastos_fixos,
        "alertas_gastos_fixos": alertas_gastos_fixos
    }


def verificar_lancamentos_pendentes(usuario_id):
    """
    Verifica se existem gastos fixos não lançados no mês atual.
    Retorna: {
        possui_pendentes: bool,
        quantidade: int,
        mensagem: str
    }
    """
    from datetime import date
    
    conn = conectar()
    cur = conn.cursor()
    
    mes_atual = date.today().strftime("%Y-%m")
    
    # Buscar gastos fixos ativos não lançados no mês
    cur.execute("""
        SELECT COUNT(*) AS quantidade
        FROM gastos_fixos gf
        WHERE gf.usuario_id = %s
          AND gf.ativo = TRUE
          AND NOT EXISTS (
              SELECT 1 FROM transacoes t
              WHERE t.usuario_id = gf.usuario_id
                AND t.gasto_fixo_id = gf.id
                AND t.referencia_mes = %s
          )
    """, (usuario_id, mes_atual))
    
    resultado = cur.fetchone()
    quantidade = int(resultado["quantidade"] or 0)
    
    conn.close()
    
    possui_pendentes = quantidade > 0
    mensagem = f"Você tem {quantidade} gasto(s) fixo(s) não lançado(s) neste mês" if possui_pendentes else ""
    
    return {
        "possui_pendentes": possui_pendentes,
        "quantidade": quantidade,
        "mensagem": mensagem
    }