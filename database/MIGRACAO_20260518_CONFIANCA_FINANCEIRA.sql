-- ============================================================================
-- MIGRAÇÃO: Confiança técnica e financeira
-- Data: 2026-05-18
-- Banco: Supabase/PostgreSQL
--
-- Objetivos:
-- 1. Alinhar metas.titulo com o código atual, sem apagar metas.nome se existir.
-- 2. Manter gastos_fixos.categoria_id opcional, como o formulário/backend atuais.
-- 3. Criar histórico próprio para movimentações de metas.
-- 4. Permitir arquivamento de metas sem remover transações ou histórico.
-- 5. Copiar movimentações legadas de transacoes.meta_id para meta_movimentacoes.
--
-- Execute este arquivo no SQL Editor do Supabase antes de publicar o backend
-- atualizado. O script é idempotente e não apaga dados existentes.
-- ============================================================================

BEGIN;

-- 1. Corrigir/garantir coluna usada pelo código atual: metas.titulo.
ALTER TABLE metas
ADD COLUMN IF NOT EXISTS titulo TEXT;

DO $$
BEGIN
    IF EXISTS (
        SELECT 1
        FROM information_schema.columns
        WHERE table_schema = 'public'
          AND table_name = 'metas'
          AND column_name = 'nome'
    ) THEN
        UPDATE metas
        SET titulo = COALESCE(NULLIF(trim(titulo), ''), NULLIF(trim(nome), ''), 'Meta sem nome')
        WHERE titulo IS NULL OR trim(titulo) = '';
    ELSE
        UPDATE metas
        SET titulo = COALESCE(NULLIF(trim(titulo), ''), 'Meta sem nome')
        WHERE titulo IS NULL OR trim(titulo) = '';
    END IF;
END $$;

ALTER TABLE metas
ALTER COLUMN titulo SET NOT NULL;

UPDATE metas
SET valor_meta = 0
WHERE valor_meta IS NULL;

ALTER TABLE metas
ALTER COLUMN valor_meta SET NOT NULL;

-- 2. Metas passam a ser arquivadas, não removidas.
ALTER TABLE metas
ADD COLUMN IF NOT EXISTS ativo BOOLEAN DEFAULT TRUE;

ALTER TABLE metas
ADD COLUMN IF NOT EXISTS arquivada_em TIMESTAMP;

UPDATE metas
SET ativo = TRUE
WHERE ativo IS NULL;

ALTER TABLE metas
ALTER COLUMN ativo SET DEFAULT TRUE,
ALTER COLUMN ativo SET NOT NULL;

-- 3. Categoria de gasto fixo continua opcional, como no formulário/backend.
ALTER TABLE gastos_fixos
ALTER COLUMN categoria_id DROP NOT NULL;

-- 4. Histórico próprio de metas, separado das transações reais.
ALTER TABLE transacoes
ADD COLUMN IF NOT EXISTS meta_id INTEGER REFERENCES metas(id) ON DELETE SET NULL;

CREATE TABLE IF NOT EXISTS public.meta_movimentacoes (
    id SERIAL PRIMARY KEY,
    usuario_id INTEGER NOT NULL REFERENCES usuarios(id) ON DELETE CASCADE,
    meta_id INTEGER NOT NULL REFERENCES metas(id),
    tipo VARCHAR(20) NOT NULL,
    valor NUMERIC(12, 2) NOT NULL,
    observacao TEXT,
    criado_em TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT ck_meta_movimentacoes_tipo
        CHECK (tipo IN ('aporte', 'retirada', 'uso_saldo', 'ajuste')),
    CONSTRAINT ck_meta_movimentacoes_valor
        CHECK (valor > 0)
);

CREATE INDEX IF NOT EXISTS idx_meta_movimentacoes_usuario_meta
ON public.meta_movimentacoes (usuario_id, meta_id, criado_em DESC);

-- 5. Copiar lançamentos legados de metas que estavam misturados em transacoes.
-- Não remove nem altera as transações antigas; apenas preserva uma cópia no
-- histórico próprio de metas para o app novo conseguir consultar essa trilha.
INSERT INTO public.meta_movimentacoes (usuario_id, meta_id, tipo, valor, observacao, criado_em)
SELECT
    t.usuario_id,
    t.meta_id,
    CASE
        WHEN t.tipo = 'entrada' THEN 'retirada'
        ELSE 'aporte'
    END AS tipo,
    t.valor,
    COALESCE(t.descricao, 'Movimentação legada de meta') AS observacao,
    COALESCE(t.data::timestamp, CURRENT_TIMESTAMP) AS criado_em
FROM transacoes t
WHERE t.meta_id IS NOT NULL
  AND NOT EXISTS (
      SELECT 1
      FROM public.meta_movimentacoes mm
      WHERE mm.usuario_id = t.usuario_id
        AND mm.meta_id = t.meta_id
        AND mm.valor = t.valor
        AND mm.tipo = CASE WHEN t.tipo = 'entrada' THEN 'retirada' ELSE 'aporte' END
        AND COALESCE(mm.observacao, '') = COALESCE(t.descricao, '')
        AND mm.criado_em::date = COALESCE(t.data, CURRENT_DATE)
  );

-- 6. Trocar unicidade antiga por unicidade apenas entre metas ativas.
DROP INDEX IF EXISTS idx_metas_usuario_titulo_unico;

CREATE UNIQUE INDEX IF NOT EXISTS idx_metas_usuario_titulo_ativo_unico
ON metas (usuario_id, lower(trim(titulo)))
WHERE ativo = TRUE;

-- 7. Índices usados pelo dashboard novo.
CREATE INDEX IF NOT EXISTS idx_metas_usuario_ativo
ON metas (usuario_id, ativo);

CREATE INDEX IF NOT EXISTS idx_transacoes_usuario_meta_id
ON transacoes (usuario_id, meta_id);

COMMIT;
