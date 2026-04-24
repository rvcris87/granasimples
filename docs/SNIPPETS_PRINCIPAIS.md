# 📋 SNIPPETS PRINCIPAIS - REFERÊNCIA RÁPIDA

## 🔧 1. NOVA ROTA EM gastos_fixos.py

```python
from flask import Blueprint, request, redirect, url_for, session, flash
from decorators import login_required
from db import conectar
from datetime import datetime, date

@gastos_fixos_bp.route("/lancar_gastos_fixos_mes", methods=["POST"])
@login_required
def lancar_gastos_fixos_mes():
    """Lança gastos fixos ativos como transações do mês"""
    usuario_id = session["usuario_id"]
    mes_referencia = request.form.get("mes", "").strip()
    
    if not mes_referencia:
        hoje = date.today()
        mes_referencia = hoje.strftime("%Y-%m")
    
    try:
        datetime.strptime(mes_referencia, "%Y-%m")
    except ValueError:
        flash("Format de mês inválido (use YYYY-MM).", "erro")
        return redirect(url_for("dashboard.app_dashboard"))
    
    conn = conectar()
    cur = conn.cursor()
    
    try:
        # Buscar gastos fixos ativos
        cur.execute("""
            SELECT id, descricao, valor, categoria_id, dia_vencimento
            FROM gastos_fixos
            WHERE usuario_id = %s AND ativo = TRUE
        """, (usuario_id,))
        gastos_fixos = cur.fetchall()
        
        if not gastos_fixos:
            flash("Nenhum gasto fixo ativo para lançar.", "aviso")
            conn.close()
            return redirect(url_for("dashboard.app_dashboard"))
        
        lancados = 0
        
        for gasto in gastos_fixos:
            # Verificar duplicação
            cur.execute("""
                SELECT id FROM transacoes
                WHERE usuario_id = %s
                  AND gasto_fixo_id = %s
                  AND referencia_mes = %s
            """, (usuario_id, gasto["id"], mes_referencia))
            
            if cur.fetchone():
                continue  # Já lançado
            
            # Calcular data
            try:
                data_trans = datetime.strptime(
                    f"{mes_referencia}-{gasto['dia_vencimento']:02d}", 
                    "%Y-%m-%d"
                ).date()
            except ValueError:
                # Último dia do mês
                ano, mes = map(int, mes_referencia.split("-"))
                if mes == 2:
                    ultimo_dia = 29 if ano % 4 == 0 else 28
                elif mes in [4, 6, 9, 11]:
                    ultimo_dia = 30
                else:
                    ultimo_dia = 31
                data_trans = date(ano, mes, min(gasto["dia_vencimento"], ultimo_dia))
            
            # Lançar transação
            cur.execute("""
                INSERT INTO transacoes 
                (usuario_id, descricao, valor, tipo, categoria_id, data, gasto_fixo_id, referencia_mes)
                VALUES (%s, %s, %s, 'saida', %s, %s, %s, %s)
            """, (usuario_id, gasto["descricao"], gasto["valor"], 
                  gasto["categoria_id"], data_trans, gasto["id"], mes_referencia))
            
            lancados += 1
        
        conn.commit()
        
        if lancados > 0:
            flash(f"✅ {lancados} gasto(s) fixo(s) lançado(s) com sucesso!", "sucesso")
        else:
            flash("ℹ️ Todos os gastos fixos já foram lançados neste mês.", "aviso")
    
    except Exception as e:
        conn.rollback()
        flash(f"Erro ao lançar gastos fixos: {str(e)}", "erro")
    finally:
        conn.close()
    
    return redirect(url_for("dashboard.app_dashboard"))
```

---

## 📊 2. FUNÇÕES EM utils.py

```python
def calcular_insights_gastos_fixos(usuario_id, total_saidas):
    """Calcula insights sobre gastos fixos"""
    conn = conectar()
    cur = conn.cursor()
    
    cur.execute("""
        SELECT
            COALESCE(SUM(valor), 0) AS total,
            COUNT(*) AS quantidade
        FROM gastos_fixos
        WHERE usuario_id = %s AND ativo = TRUE
    """, (usuario_id,))
    resultado = cur.fetchone()
    
    total_gastos_fixos = float(resultado["total"] or 0)
    percentual = (total_gastos_fixos / total_saidas * 100) if total_saidas > 0 else 0
    
    # Maior categoria
    cur.execute("""
        SELECT COALESCE(c.nome, 'Sem categoria') AS categoria
        FROM gastos_fixos gf
        LEFT JOIN categorias c ON gf.categoria_id = c.id
        WHERE gf.usuario_id = %s AND gf.ativo = TRUE
        GROUP BY c.id, c.nome
        ORDER BY SUM(gf.valor) DESC
        LIMIT 1
    """, (usuario_id,))
    maior = cur.fetchone()
    
    # Mensagem
    mensagem = f"Seus gastos fixos totalizam R$ {total_gastos_fixos:.2f}/mês"
    if percentual > 0:
        mensagem += f" ({percentual:.1f}% das suas saídas)"
    if maior:
        mensagem += f". A maior parte está em {maior['categoria']}."
    
    # Alertas
    alertas = []
    if percentual > 60:
        alertas.append(f"🔴 Seus gastos fixos comprometem {percentual:.0f}% das suas saídas!")
    elif percentual > 40:
        alertas.append(f"🟡 Seus gastos fixos representam {percentual:.0f}% das suas saídas.")
    
    conn.close()
    
    return {
        "total_gastos_fixos": total_gastos_fixos,
        "percentual_gastos_fixos": percentual,
        "maior_categoria_gasto_fixo": maior["categoria"] if maior else "",
        "mensagem_gastos_fixos": mensagem,
        "alertas_gastos_fixos": alertas
    }


def verificar_lancamentos_pendentes(usuario_id):
    """Verifica se há gastos fixos não lançados no mês"""
    from datetime import date
    
    conn = conectar()
    cur = conn.cursor()
    
    mes_atual = date.today().strftime("%Y-%m")
    
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
    
    return {
        "possui_pendentes": quantidade > 0,
        "quantidade": quantidade,
        "mensagem": f"Você tem {quantidade} gasto(s) fixo(s) não lançado(s) neste mês" if quantidade > 0 else ""
    }
```

---

## 🎨 3. SEÇÃO DO TEMPLATE (Jinja2)

```html
<!-- GASTOS FIXOS -->
<section class="painel-card" id="gastos-fixos">
    <h2>Gastos Fixos</h2>

    <form method="POST" action="{{ url_for('gastos_fixos.add_gasto_fixo') }}">
        <input type="hidden" name="csrf_token" value="{{ csrf_token() }}">
        <input type="text" name="descricao" placeholder="Descrição do gasto" required>
        <input type="number" step="0.01" name="valor" placeholder="Valor" required>
        
        <select name="categoria_id">
            <option value="">Categoria (opcional)</option>
            {% for c in categorias %}
            <option value="{{ c.id }}">{{ c.nome }}</option>
            {% endfor %}
        </select>
        
        <input type="number" name="dia_vencimento" min="1" max="31" placeholder="Dia do vencimento" required>
        <button class="btn">Adicionar</button>
    </form>

    {% if gastos_fixos %}
    <div class="gastos-fixos-lista">
        {% for gf in gastos_fixos %}
        <div class="gasto-fixo-item {% if not gf.ativo %}inativo{% endif %}">
            <div>
                <p><strong>{{ gf.descricao }}</strong></p>
                <small>{{ gf.categoria_nome or "Sem categoria" }} • Dia {{ gf.dia_vencimento }}</small>
            </div>
            <strong>R$ {{ "%.2f"|format(gf.valor) }}</strong>
            
            <div class="gasto-fixo-actions">
                <form method="POST" action="{{ url_for('gastos_fixos.toggle_gasto_fixo', gasto_id=gf.id) }}" style="display:inline;">
                    <input type="hidden" name="csrf_token" value="{{ csrf_token() }}">
                    <button type="submit" class="btn-icon">
                        {% if gf.ativo %}🔴{% else %}⚪{% endif %}
                    </button>
                </form>
                
                <form method="POST" action="{{ url_for('gastos_fixos.excluir_gasto_fixo', gasto_id=gf.id) }}" style="display:inline;">
                    <input type="hidden" name="csrf_token" value="{{ csrf_token() }}">
                    <button type="submit" class="btn-icon">🗑️</button>
                </form>
            </div>
        </div>
        {% endfor %}
    </div>

    <!-- INSIGHTS GASTOS FIXOS -->
    {% if mensagem_gastos_fixos %}
    <div class="gastos-fixos-insights">
        <div class="insight-item">
            <p><strong>📊 Análise de Gastos Fixos</strong></p>
            <p>{{ mensagem_gastos_fixos }}</p>
        </div>
        
        {% if alertas_gastos_fixos %}
        {% for alerta in alertas_gastos_fixos %}
        <div class="insight-item insight-alerta">
            {{ alerta }}
        </div>
        {% endfor %}
        {% endif %}

        <!-- BOTÃO DE LANÇAMENTO -->
        {% if lancamentos_pendentes.possui_pendentes %}
        <div class="lancamentos-pendentes">
            <p>{{ lancamentos_pendentes.mensagem }}</p>
            <form method="POST" action="{{ url_for('gastos_fixos.lancar_gastos_fixos_mes') }}" style="display:inline;">
                <input type="hidden" name="csrf_token" value="{{ csrf_token() }}">
                <button type="submit" class="btn btn-lancar">
                    🚀 Lançar Gastos Fixos do Mês
                </button>
            </form>
        </div>
        {% else %}
        <div class="lancamentos-ok">
            <p>✅ Todos os gastos fixos do mês já foram lançados como transações.</p>
        </div>
        {% endif %}
    </div>
    {% endif %}
    {% endif %}
</section>
```

---

## 🔧 4. ATUALIZAÇÃO EM dashboard.py

```python
from utils import (
    # ... imports existentes ...
    calcular_insights_gastos_fixos,
    verificar_lancamentos_pendentes
)

@dashboard_bp.route("/app")
@login_required
def app_dashboard():
    usuario_id = session["usuario_id"]
    mes = request.args.get("mes", "").strip()

    dados = calcular_dados_dashboard(usuario_id, mes)
    categorias = buscar_categorias(usuario_id)
    tendencia = calcular_tendencia_6_meses(usuario_id)
    previsao = calcular_previsao_gastos(usuario_id)
    alertas_metas = calcular_alertas_metas(usuario_id)
    gastos_fixos = buscar_gastos_fixos(usuario_id)
    
    # NOVOS DADOS
    insights_gastos_fixos = calcular_insights_gastos_fixos(usuario_id, dados["total_saidas"])
    lancamentos_pendentes = verificar_lancamentos_pendentes(usuario_id)

    return render_template(
        "index.html",
        # ... variáveis existentes ...
        # NOVAS VARIÁVEIS
        total_gastos_fixos=insights_gastos_fixos["total_gastos_fixos"],
        percentual_gastos_fixos=insights_gastos_fixos["percentual_gastos_fixos"],
        mensagem_gastos_fixos=insights_gastos_fixos["mensagem_gastos_fixos"],
        alertas_gastos_fixos=insights_gastos_fixos["alertas_gastos_fixos"],
        lancamentos_pendentes=lancamentos_pendentes,
    )
```

---

## 📝 5. MIGRAÇÃO SQL

```sql
-- Adicionar colunas
ALTER TABLE transacoes
ADD COLUMN IF NOT EXISTS gasto_fixo_id INTEGER REFERENCES gastos_fixos(id) ON DELETE SET NULL,
ADD COLUMN IF NOT EXISTS referencia_mes VARCHAR(7);

-- Criar índice
CREATE INDEX IF NOT EXISTS idx_transacoes_gasto_fixo_id 
ON transacoes(usuario_id, gasto_fixo_id, referencia_mes);
```

---

**Todos os snippets estão prontos para copiar-e-colar! ✅**
