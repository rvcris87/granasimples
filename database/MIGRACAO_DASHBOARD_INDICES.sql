-- Índice para acelerar filtros e ordenação do dashboard por usuário/data.

CREATE INDEX IF NOT EXISTS idx_transacoes_usuario_data
ON transacoes (usuario_id, data);
