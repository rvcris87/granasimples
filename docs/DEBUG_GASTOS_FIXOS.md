# Debug e Correção - Gastos Fixos Não Aparecem no Dashboard

## 🔍 Análise dos Problemas Encontrados

### PROBLEMA 1: Falta de Debug Print
**Status**: ✅ CORRIGIDO

A rota `lancar_gastos_fixos_mes()` não tinha nenhum print de debug, impossibilitando diagnosticar se:
- Os gastos fixos estavam sendo encontrados
- As transações estavam sendo inseridas
- Havia erros silenciosos no banco

**Solução Implementada**:
```python
# Adicionados prints detalhados em pontos críticos:
print(f"===== LANÇAMENTO DE GASTOS FIXOS =====")
print(f"Usuário: {usuario_id}")
print(f"Referência de mês: {mes_referencia}")
print(f"Gastos fixos ativos encontrados: {len(gastos_fixos)}")
print(f"Processando: {descricao} (ID: {gasto_id}, Valor: R${valor:.2f})")
print(f"✓ Transação inserida com sucesso")
print(f"✓ COMMIT realizado com sucesso")
```

---

### PROBLEMA 2: Falta de Debug no Dashboard

**Status**: ✅ CORRIGIDO

A função `calcular_dados_dashboard()` não tinha prints, dificultando identificar:
- Se buscava as transações corretamente
- Quantas transações encontrava
- Se filtro de mês estava funcionando

**Solução Implementada**:
```python
# Em calcular_dados_dashboard():
print(f"📊 DASHBOARD - Buscando transações para: usuário_id={usuario_id}, mês={mes}")
print(f"  → Transações encontradas: {len(transacoes)}")
print(f"  → Totais: Entradas=R${total_entradas:.2f}, Saídas=R${total_saidas:.2f}")
print(f"  → Categorias encontradas: {len(categorias_labels)}")
```

---

## ✅ Código Corrigido - Rota de Lançamento

```python
@gastos_fixos_bp.route("/lancar_gastos_fixos_mes", methods=["POST"])
@login_required
def lancar_gastos_fixos_mes():
    """
    Lança todos os gastos fixos ativos do mês como transações.
    Evita duplicação usando gasto_fixo_id e referencia_mes.
    """
    usuario_id = session["usuario_id"]
    mes_referencia = request.form.get("mes", "").strip()
    
    # Se não informar mês, usar mês atual
    if not mes_referencia:
        hoje = date.today()
        mes_referencia = hoje.strftime("%Y-%m")
    
    # DEBUG
    print(f"\n===== LANÇAMENTO DE GASTOS FIXOS =====")
    print(f"Usuário: {usuario_id}")
    print(f"Referência de mês: {mes_referencia}")
    
    # Validar formato YYYY-MM
    try:
        datetime.strptime(mes_referencia, "%Y-%m")
    except ValueError:
        flash("Format de mês inválido (use YYYY-MM).", "erro")
        return redirect(url_for("dashboard.app_dashboard"))
    
    conn = conectar()
    cur = conn.cursor()
    
    try:
        # 1. Buscar todos os gastos fixos ATIVOS do usuário
        cur.execute("""
            SELECT id, descricao, valor, categoria_id, dia_vencimento
            FROM gastos_fixos
            WHERE usuario_id = %s AND ativo = TRUE
            ORDER BY dia_vencimento ASC
        """, (usuario_id,))
        gastos_fixos = cur.fetchall()
        
        print(f"Gastos fixos ativos encontrados: {len(gastos_fixos)}")
        
        if not gastos_fixos:
            flash("Nenhum gasto fixo ativo para lançar.", "aviso")
            conn.close()
            return redirect(url_for("dashboard.app_dashboard"))
        
        lancados = 0
        duplicados = 0
        
        # 2. Para cada gasto fixo, criar transação se não existir
        for gasto in gastos_fixos:
            gasto_id = gasto["id"]
            descricao = gasto["descricao"]
            valor = gasto["valor"]
            categoria_id = gasto["categoria_id"]
            dia_vencimento = gasto["dia_vencimento"]
            
            print(f"\nProcessando: {descricao} (ID: {gasto_id}, Valor: R${valor:.2f})")
            
            # Verificar se já foi lançado neste mês
            cur.execute("""
                SELECT id FROM transacoes
                WHERE usuario_id = %s
                  AND gasto_fixo_id = %s
                  AND referencia_mes = %s
            """, (usuario_id, gasto_id, mes_referencia))
            
            if cur.fetchone():
                # Já foi lançado
                print(f"  → Duplicada: já foi lançado em {mes_referencia}")
                duplicados += 1
                continue
            
            # Calcular a data da transação
            try:
                data_trans = datetime.strptime(
                    f"{mes_referencia}-{dia_vencimento:02d}", 
                    "%Y-%m-%d"
                ).date()
            except ValueError:
                # Dia inválido para o mês (ex: 31 de fevereiro)
                ano, mes = map(int, mes_referencia.split("-"))
                if mes == 2:
                    ultimo_dia = 29 if ano % 4 == 0 and (ano % 100 != 0 or ano % 400 == 0) else 28
                elif mes in [4, 6, 9, 11]:
                    ultimo_dia = 30
                else:
                    ultimo_dia = 31
                
                if dia_vencimento > ultimo_dia:
                    data_trans = date(ano, mes, ultimo_dia)
                else:
                    data_trans = date(ano, mes, dia_vencimento)
            
            # Inserir transação
            print(f"  → Inserindo transação com data: {data_trans}")
            print(f"    Categoria: {categoria_id}, Gasto_fixo_id: {gasto_id}, Ref: {mes_referencia}")
            
            try:
                cur.execute("""
                    INSERT INTO transacoes 
                    (usuario_id, descricao, valor, tipo, categoria_id, data, gasto_fixo_id, referencia_mes)
                    VALUES (%s, %s, %s, 'saida', %s, %s, %s, %s)
                """, (usuario_id, descricao, valor, categoria_id, data_trans, gasto_id, mes_referencia))
                print(f"  ✓ Transação inserida com sucesso")
                lancados += 1
            except Exception as insert_error:
                print(f"  ✗ ERRO ao inserir: {str(insert_error)}")
                raise
        
        conn.commit()
        print(f"\n✓ COMMIT realizado com sucesso")
        print(f"Resumo: {lancados} lançados, {duplicados} duplicados")
        print(f"=====================================\n")
        
        # Mensagem de feedback
        if lancados > 0 and duplicados > 0:
            flash(f"✅ {lancados} gasto(s) fixo(s) lançado(s). {duplicados} já estava(m) lançado(s).", "sucesso")
        elif lancados > 0:
            flash(f"✅ {lancados} gasto(s) fixo(s) lançado(s) com sucesso!", "sucesso")
        elif duplicados > 0:
            flash(f"ℹ️ Todos os {duplicados} gasto(s) fixo(s) já foram lançados neste mês.", "aviso")
        else:
            flash("Nenhum gasto fixo para lançar.", "aviso")
    
    except Exception as e:
        conn.rollback()
        print(f"✗ ERRO: {str(e)}")
        print(f"=====================================\n")
        flash(f"Erro ao lançar gastos fixos: {str(e)}", "erro")
    finally:
        conn.close()
    
    return redirect(url_for("dashboard.app_dashboard"))
```

---

## ✅ Dashboard com Debug

```python
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

    # Transações
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
    
    print(f"  → Transações encontradas: {len(transacoes)}")
    for t in transacoes[:3]:  # Mostrar apenas as 3 primeiras
        print(f"     - {t['descricao']}: R${t['valor']:.2f} ({t['tipo']}) em {t['data']}")
    
    # Totais
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
    
    print(f"  → Totais: Entradas=R${total_entradas:.2f}, Saídas=R${total_saidas:.2f}, Saldo=R${saldo:.2f}")
    
    # Categorias
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
    
    print(f"  → Categorias encontradas: {len(categorias_labels)}")
    if categorias_labels:
        print(f"     Top 3: {', '.join(f'{categorias_labels[i]} (R${categorias_valores[i]:.2f})' for i in range(min(3, len(categorias_labels))))}")
    
    # ... rest of function
```

---

## 📋 Possíveis Erros que Podem Impedir Aparecer

### 1. **categoria_id = NULL** ❌
Se o gasto fixo foi criado sem categoria:
```sql
INSERT INTO transacoes (..., categoria_id, ...) VALUES (..., NULL, ...)
```
Isso é VÁLIDO e deve funcionar (LEFT JOIN cuida disso).

### 2. **data Incorreta** ❌
Se a data não for formatada corretamente no banco:
```
data = '2026-04-15'   ✅ CORRETO
data = '15/04/2026'   ❌ ERRADO
```
O código trata isso com `date()` que retorna formato correto.

### 3. **gasto_fixo_id Duplicado** ❌
Se tentar inserir duas vezes o mesmo gasto_fixo_id + referencia_mes:
```
UNIQUE(usuario_id, gasto_fixo_id, referencia_mes)
```
O código verifica isso ANTES de inserir.

### 4. **Filtro de Mês Incorreto** ❌
Se o mês no dashboard não corresponder ao mês de lançamento:
```
DASHBOARD: mes = '2026-04'
TRANSAÇÃO: data = '2026-04-15'  ✅ MATCH
TRANSAÇÃO: data = '2026-03-15'  ❌ NO MATCH
```
O code usa `TO_CHAR(t.data, 'YYYY-MM')` que é correto.

### 5. **Commit não executado** ❌
Se `conn.commit()` não executar:
- As transações ficariam em modo PENDING
- Não apareceriam em queries

O código agora tem `try/except/finally` com `conn.commit()` no lugar certo.

---

## 🧪 Como Debugar Manualmente

### 1. Olhar os prints do terminal
```
python app.py
# Fazer o lançamento
# Ver output de prints no PyCharm/Terminal:

===== LANÇAMENTO DE GASTOS FIXOS =====
Usuário: 1
Referência de mês: 2026-04
Gastos fixos ativos encontrados: 2

Processando: Netflix (ID: 1, Valor: R$39.90)
  → Inserindo transação com data: 2026-04-05
    Categoria: 5, Gasto_fixo_id: 1, Ref: 2026-04
  ✓ Transação inserida com sucesso

✓ COMMIT realizado com sucesso
Resumo: 1 lançados, 0 duplicados
```

### 2. Verificar no banco diretamente
```sql
SELECT * FROM transacoes 
WHERE usuario_id = 1 
  AND referencia_mes = '2026-04';
```

### 3. Ver logs do Dashboard
```
python app.py
# Acessar /app no navegador
# Ver output de prints:

📊 DASHBOARD - Buscando transações para: usuário_id=1, mês=2026-04
  → Transações encontradas: 15
     - Netflix: R$39.90 (saida) em 2026-04-05
     - Conta de Luz: R$150.00 (saida) em 2026-04-03
     - Salário: R$5000.00 (entrada) em 2026-04-01
```

---

## 🎯 Resumo das Correções

| Item | Antes | Depois |
|------|-------|--------|
| Debug Lançamento | ❌ Nenhum | ✅ 10+ prints |
| Debug Dashboard | ❌ Nenhum | ✅ 5+ prints |
| Tratamento de Erro | ❌ Silencioso | ✅ Print + Flash |
| Duplicação | ✅ Verifica | ✅ Verifica + print |
| Insert | ✅ Funciona | ✅ Funciona + print |
| Commit | ✅ Faz | ✅ Faz + print |

---

## ✨ Próximos Passos

1. **Rodar e testar**:
   - Criar um gasto fixo
   - Clicar em "Lançar Gastos Fixos do Mês"
   - Ver prints no terminal
   - Verificar se aparecem no dashboard

2. **Se não aparecer**: Usar os prints para identificar onde está falhando

3. **Remover prints após debug**: Depois de resolvido, pode remover os `print()` ou deixá-los em `debug=False`

