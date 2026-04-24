-- Garante que cada usuário tenha apenas uma categoria por nome/tipo.
-- Usa lower(trim(nome)) para evitar duplicatas por maiúsculas/minúsculas ou espaços.

CREATE UNIQUE INDEX IF NOT EXISTS idx_categorias_usuario_nome_tipo_unico
ON categorias (usuario_id, lower(trim(nome)), tipo);
