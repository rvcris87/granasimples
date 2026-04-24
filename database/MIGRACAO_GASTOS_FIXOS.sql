-- ===== MIGRAÇÃO: INTEGRAÇÃO DE GASTOS FIXOS =====
-- 
-- Adiciona rastreamento para evitar duplicação de gastos fixos lançados como transações

-- 1. Adicionar coluna em transacoes para rastrear gastos fixos lançados
ALTER TABLE transacoes
ADD COLUMN IF NOT EXISTS gasto_fixo_id INTEGER REFERENCES gastos_fixos(id) ON DELETE SET NULL,
ADD COLUMN IF NOT EXISTS referencia_mes VARCHAR(7); -- Formato: YYYY-MM

-- 2. Criar índice para buscar rápido transações de gastos fixos
CREATE INDEX IF NOT EXISTS idx_transacoes_gasto_fixo_id 
ON transacoes(usuario_id, gasto_fixo_id, referencia_mes);

-- 3. Criar tabela de auditoria opcional (se quiser rastrear histórico de lançamentos)
-- Esta tabela é OPCIONAL, usa apenas se quiser histórico completo
CREATE TABLE IF NOT EXISTS gastos_fixos_lancamentos (
    id SERIAL PRIMARY KEY,
    usuario_id INTEGER NOT NULL REFERENCES usuarios(id) ON DELETE CASCADE,
    gasto_fixo_id INTEGER NOT NULL REFERENCES gastos_fixos(id) ON DELETE CASCADE,
    referencia_mes VARCHAR(7) NOT NULL, -- YYYY-MM
    transacao_id INTEGER REFERENCES transacoes(id) ON DELETE SET NULL,
    lancado_em TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(usuario_id, gasto_fixo_id, referencia_mes)
);

CREATE INDEX IF NOT EXISTS idx_gastos_fixos_lancamentos 
ON gastos_fixos_lancamentos(usuario_id, referencia_mes);
