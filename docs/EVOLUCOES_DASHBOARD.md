================================================================================
4 EVOLUÇÕES DO DASHBOARD FINANCEIRO - GUIA DE IMPLEMENTAÇÃO COMPLETO
================================================================================

Todas as mudanças foram aplicadas ao projeto existente mantendo a estrutura.

================================================================================
1. SQL - TABELA PARA GASTOS FIXOS
================================================================================

Execute no PostgreSQL:

```sql
CREATE TABLE IF NOT EXISTS gastos_fixos (
    id SERIAL PRIMARY KEY,
    usuario_id INTEGER NOT NULL,
    descricao VARCHAR(200) NOT NULL,
    valor DECIMAL(10, 2) NOT NULL,
    categoria_id INTEGER,
    dia_vencimento INTEGER NOT NULL,
    ativo BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (usuario_id) REFERENCES usuarios(id) ON DELETE CASCADE,
    FOREIGN KEY (categoria_id) REFERENCES categorias(id) ON DELETE SET NULL
);

CREATE INDEX idx_gastos_fixos_usuario ON gastos_fixos(usuario_id);
```

================================================================================
2. TRECHOS DE HTML/JINJA PARA O TEMPLATE
================================================================================

A. Gráfico de Tendência (6 Meses) - Adicione em index.html após o gráfico de categorias:

```html
<!-- GRÁFICO DE TENDÊNCIA (ÚLTIMOS 6 MESES) -->
<section class="painel-card">
    <h2>Tendência Financeira</h2>
    <div class="grafico-box">
        <h3>Últimos 6 Meses</h3>
        <canvas id="graficoTendencia"></canvas>
    </div>
</section>

<div
    id="dados-tendencia"
    data-labels='{{ tendencia_labels | tojson | safe }}'
    data-entradas='{{ tendencia_entradas | tojson | safe }}'
    data-saidas='{{ tendencia_saidas | tojson | safe }}'
    data-saldo='{{ tendencia_saldo | tojson | safe }}'>
</div>
```

B. Card de Previsão de Gastos - Adicione na seção de insights:

```html
<!-- PREVISÃO DE GASTOS -->
<div class="insight-item insight-previsao">
    📊 {{ previsao_mensagem }}
</div>
```

C. Alertas de Metas vs Gastos - Adicione após os alertas existentes:

```html
<!-- ALERTAS DE METAS -->
{% if alertas_metas %}
<div class="alertas-metas">
    {% for alerta_meta in alertas_metas %}
    <div class="insight-item {% if alerta_meta.tipo == 'erro' %}insight-alerta{% else %}insight-aviso{% endif %}">
        {{ alerta_meta.mensagem }}
    </div>
    {% endfor %}
</div>
{% endif %}
```

D. Seção de Gastos Fixos - Adicione na coluna lateral ou onde preferir:

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
                    <button type="submit" class="btn-icon" title="{% if gf.ativo %}Desativar{% else %}Ativar{% endif %}">
                        {% if gf.ativo %}🔴{% else %}⚪{% endif %}
                    </button>
                </form>
                
                <form method="POST" action="{{ url_for('gastos_fixos.excluir_gasto_fixo', gasto_id=gf.id) }}" style="display:inline;">
                    <input type="hidden" name="csrf_token" value="{{ csrf_token() }}">
                    <button type="submit" class="btn-icon" title="Excluir">🗑️</button>
                </form>
            </div>
        </div>
        {% endfor %}
    </div>
    {% endif %}
</section>
```

================================================================================
3. JAVASCRIPT PARA O GRÁFICO DE TENDÊNCIA
================================================================================

Adicione este código no script de gráficos (antes do fechamento da tag script):

```javascript
// GRÁFICO DE TENDÊNCIA (6 MESES)
const dadosTendencia = document.getElementById("dados-tendencia");
const canvasTendencia = document.getElementById("graficoTendencia");

if (dadosTendencia && canvasTendencia) {
    let tendenciaLabels = [];
    let tendenciaEntradas = [];
    let tendenciaSaidas = [];
    let tendenciaSaldo = [];

    try {
        tendenciaLabels = JSON.parse(dadosTendencia.dataset.labels || "[]");
        tendenciaEntradas = JSON.parse(dadosTendencia.dataset.entradas || "[]");
        tendenciaSaidas = JSON.parse(dadosTendencia.dataset.saidas || "[]");
        tendenciaSaldo = JSON.parse(dadosTendencia.dataset.saldo || "[]");
    } catch (erro) {
        console.error("Erro ao ler dados de tendência:", erro);
    }

    new Chart(canvasTendencia, {
        type: "line",
        data: {
            labels: tendenciaLabels,
            datasets: [
                {
                    label: "Entradas",
                    data: tendenciaEntradas,
                    borderColor: "#3ecf8e",
                    backgroundColor: "rgba(62, 207, 142, 0.1)",
                    tension: 0.4,
                    fill: true,
                    pointRadius: 5,
                    pointBackgroundColor: "#3ecf8e",
                    pointHoverRadius: 7
                },
                {
                    label: "Saídas",
                    data: tendenciaSaidas,
                    borderColor: "#f87171",
                    backgroundColor: "rgba(248, 113, 113, 0.1)",
                    tension: 0.4,
                    fill: true,
                    pointRadius: 5,
                    pointBackgroundColor: "#f87171",
                    pointHoverRadius: 7
                },
                {
                    label: "Saldo",
                    data: tendenciaSaldo,
                    borderColor: "#60a5fa",
                    backgroundColor: "rgba(96, 165, 250, 0.1)",
                    tension: 0.4,
                    fill: true,
                    pointRadius: 5,
                    pointBackgroundColor: "#60a5fa",
                    pointHoverRadius: 7
                }
            ]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                legend: {
                    display: true,
                    labels: {
                        color: "#d4d4d8",
                        padding: 15,
                        font: { size: 13 }
                    }
                },
                tooltip: {
                    callbacks: {
                        label: function(context) {
                            return context.dataset.label + ": R$ " + Number(context.raw).toFixed(2);
                        }
                    }
                }
            },
            scales: {
                x: {
                    ticks: { color: "#a1a1aa" },
                    grid: { display: false }
                },
                y: {
                    beginAtZero: true,
                    ticks: {
                        color: "#a1a1aa",
                        callback: function(value) {
                            return "R$ " + value;
                        }
                    },
                    grid: { color: "rgba(255,255,255,0.05)" }
                }
            }
        }
    });
}
```

================================================================================
4. CSS EXTRA PARA ESTILIZAÇÃO
================================================================================

Adicione isto no final do style.css:

```css
/* PREVISÃO DE GASTOS */
.insight-previsao {
    border-left-color: #a78bfa;
    background: linear-gradient(135deg, rgba(167, 139, 250, 0.08) 0%, rgba(167, 139, 250, 0.02) 100%);
    color: #d8bfd8;
}

/* ALERTAS DE METAS */
.alertas-metas {
    display: flex;
    flex-direction: column;
    gap: 10px;
    margin-top: 10px;
}

.insight-aviso {
    border-left-color: #fbbf24;
    background: linear-gradient(135deg, rgba(251, 191, 36, 0.08) 0%, rgba(251, 191, 36, 0.02) 100%);
    color: #fcd34d;
}

/* GASTOS FIXOS */
.gastos-fixos-lista {
    display: flex;
    flex-direction: column;
    gap: 12px;
    margin-top: 16px;
}

.gasto-fixo-item {
    padding: 14px;
    border-radius: 12px;
    background: rgba(255, 255, 255, 0.02);
    border: 1px solid rgba(255, 255, 255, 0.04);
    display: flex;
    justify-content: space-between;
    align-items: center;
    gap: 12px;
    transition: opacity 0.2s;
}

.gasto-fixo-item.inativo {
    opacity: 0.6;
    background: rgba(255, 255, 255, 0.01);
}

.gasto-fixo-item p {
    margin: 0;
    color: #f4f4f5;
    font-weight: 600;
}

.gasto-fixo-item small {
    display: block;
    color: #a1a1aa;
    font-size: 0.85rem;
    margin-top: 4px;
}

.gasto-fixo-actions {
    display: flex;
    gap: 8px;
}

.btn-icon {
    background: none;
    border: none;
    cursor: pointer;
    font-size: 1.2rem;
    padding: 4px 8px;
    transition: transform 0.2s;
}

.btn-icon:hover {
    transform: scale(1.1);
}

/* GRÁFICO DE TENDÊNCIA */
.grafico-box canvas {
    width: 100% !important;
    height: 300px !important;
}
```

================================================================================
SUMÁRIO DAS MUDANÇAS REALIZADAS
================================================================================

✅ ARQUIVOS MODIFICADOS:
  1. utils.py - Adicionadas 4 novas funções:
     - calcular_tendencia_6_meses()
     - calcular_previsao_gastos()
     - calcular_alertas_metas()
     - buscar_gastos_fixos()

  2. app.py - Adicionado import e registro do blueprint gastos_fixos

  3. routes/dashboard.py - Atualizado para passar novos dados ao template

✅ NOVOS ARQUIVOS:
  1. routes/gastos_fixos.py - Novo blueprint com operações CRUD

✅ TODO NO TEMPLATE (index.html):
  1. Adicione a seção de gráfico de tendência
  2. Adicione o card de previsão de gastos
  3. Adicione alertas de metas
  4. Adicione a seção de gastos fixos
  5. Adicione o script do gráfico de tendência

✅ CSS (style.css):
  1. Adicione estilos para previsão, alertas e gastos fixos

================================================================================
FLUXO DE FUNCIONAMENTO DAS EVOLUÇÕES
================================================================================

1. GRÁFICO DE TENDÊNCIA:
   - Backend calcula totais de entrada/saída/saldo para os últimos 6 meses
   - Frontend renderiza com Chart.js (line chart com 3 séries)
   - Mostra evolução visual mês a mês

2. PREVISÃO DE GASTOS:
   - Backend calcula média dos últimos 3 meses de saídas
   - Usa essa média como previsão do próximo mês
   - Exibe mensagem amigável mesmo com dados insuficientes

3. ALERTAS DE METAS:
   - Backend compara valor_atual vs valor_meta
   - Gera alertas se atingiu 80% ou ultrapassou
   - Exibe na seção de insights com emojis e cores distintivas

4. GASTOS FIXOS:
   - Tabela no banco para armazenar gastos recorrentes
   - CRUD completo (add, edit, toggle, delete)
   - Integrado ao sistema de categorias existente
   - Segurança: @login_required em todas as rotas

================================================================================
PRÓXIMAS MELHORIAS (OPCIONAL)
================================================================================

Se quiser evoluir ainda mais:
1. Lançamento automático de gastos fixos como transações no dia do vencimento
2. Exportação de relatório em PDF
3. Integração com webhooks para notificações
4. Gráfico de evolução de metas ao longo do tempo
5. Análise de gastos com IA/ML para classificação automática

================================================================================
