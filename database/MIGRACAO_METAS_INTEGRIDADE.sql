-- Melhora a integridade das metas e vincula transações geradas por metas.

ALTER TABLE transacoes
ADD COLUMN IF NOT EXISTS meta_id INTEGER REFERENCES metas(id) ON DELETE CASCADE;

CREATE INDEX IF NOT EXISTS idx_transacoes_usuario_meta_id
ON transacoes (usuario_id, meta_id);

CREATE UNIQUE INDEX IF NOT EXISTS idx_metas_usuario_titulo_unico
ON metas (usuario_id, lower(trim(titulo)));
