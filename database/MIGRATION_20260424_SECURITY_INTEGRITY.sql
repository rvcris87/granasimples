-- ============================================================================
-- MIGRATION: Security & Integrity Fixes for GranaSimples
-- Date: 2026-04-24
-- Purpose: Add UNIQUE constraints, NOT NULL constraints, and ON CONFLICT handling
-- ============================================================================

-- ============================================================================
-- STEP 1: Identify and Remove Duplicates Before Applying UNIQUE Constraints
-- ============================================================================

-- Check for duplicate emails in usuarios table
-- Run this query to identify duplicates BEFORE applying constraint
-- SELECT email, COUNT(*) as count FROM usuarios WHERE email IS NOT NULL GROUP BY email HAVING COUNT(*) > 1;

-- If duplicates found, review and keep only one per email:
-- Option 1: Keep the oldest (first created)
-- WITH duplicates AS (
--   SELECT id, email, ROW_NUMBER() OVER (PARTITION BY email ORDER BY id) as rn
--   FROM usuarios
--   WHERE email IS NOT NULL
-- )
-- DELETE FROM usuarios WHERE id IN (SELECT id FROM duplicates WHERE rn > 1);

-- Check for duplicate emails in login_tentativas table
-- SELECT email, COUNT(*) as count FROM login_tentativas WHERE email IS NOT NULL GROUP BY email HAVING COUNT(*) > 1;

-- If duplicates found, keep only the most recent attempt:
-- WITH duplicates AS (
--   SELECT id, email, ROW_NUMBER() OVER (PARTITION BY email ORDER BY id DESC) as rn
--   FROM login_tentativas
--   WHERE email IS NOT NULL
-- )
-- DELETE FROM login_tentativas WHERE id IN (SELECT id FROM duplicates WHERE rn > 1);


-- ============================================================================
-- STEP 2: Add NOT NULL Constraints to Essential Fields
-- ============================================================================

-- Usuarios table
ALTER TABLE usuarios ALTER COLUMN email SET NOT NULL;
ALTER TABLE usuarios ALTER COLUMN senha SET NOT NULL;
ALTER TABLE usuarios ALTER COLUMN nome SET NOT NULL;

-- Categorias table
ALTER TABLE categorias ALTER COLUMN usuario_id SET NOT NULL;
ALTER TABLE categorias ALTER COLUMN nome SET NOT NULL;
ALTER TABLE categorias ALTER COLUMN tipo SET NOT NULL;

-- Transacoes table
ALTER TABLE transacoes ALTER COLUMN usuario_id SET NOT NULL;
ALTER TABLE transacoes ALTER COLUMN descricao SET NOT NULL;
ALTER TABLE transacoes ALTER COLUMN valor SET NOT NULL;
ALTER TABLE transacoes ALTER COLUMN tipo SET NOT NULL;
ALTER TABLE transacoes ALTER COLUMN data SET NOT NULL;

-- Metas table
ALTER TABLE metas ALTER COLUMN usuario_id SET NOT NULL;
ALTER TABLE metas ALTER COLUMN nome SET NOT NULL;
ALTER TABLE metas ALTER COLUMN valor_meta SET NOT NULL;

-- Gastos Fixos table
ALTER TABLE gastos_fixos ALTER COLUMN usuario_id SET NOT NULL;
ALTER TABLE gastos_fixos ALTER COLUMN descricao SET NOT NULL;
ALTER TABLE gastos_fixos ALTER COLUMN valor SET NOT NULL;
ALTER TABLE gastos_fixos ALTER COLUMN categoria_id SET NOT NULL;
ALTER TABLE gastos_fixos ALTER COLUMN dia_vencimento SET NOT NULL;

-- Login Tentativas table
ALTER TABLE login_tentativas ALTER COLUMN email SET NOT NULL;


-- ============================================================================
-- STEP 3: Add UNIQUE Constraints
-- ============================================================================

-- Unique email in usuarios (critical for authentication)
ALTER TABLE usuarios ADD CONSTRAINT uq_usuarios_email UNIQUE (email);

-- Unique email in login_tentativas (for UPSERT operations)
ALTER TABLE login_tentativas ADD CONSTRAINT uq_login_tentativas_email UNIQUE (email);


-- ============================================================================
-- STEP 4: Add Indexes for Performance (Optional but Recommended)
-- ============================================================================

-- Index on usuarios.email for faster lookups
CREATE INDEX IF NOT EXISTS idx_usuarios_email ON usuarios(email);

-- Index on login_tentativas.email for faster lookups
CREATE INDEX IF NOT EXISTS idx_login_tentativas_email ON login_tentativas(email);

-- Index on transacoes.usuario_id for faster queries
CREATE INDEX IF NOT EXISTS idx_transacoes_usuario_id ON transacoes(usuario_id);

-- Index on categorias.usuario_id for faster queries
CREATE INDEX IF NOT EXISTS idx_categorias_usuario_id ON categorias(usuario_id);

-- Index on metas.usuario_id for faster queries
CREATE INDEX IF NOT EXISTS idx_metas_usuario_id ON metas(usuario_id);

-- Index on gastos_fixos.usuario_id for faster queries
CREATE INDEX IF NOT EXISTS idx_gastos_fixos_usuario_id ON gastos_fixos(usuario_id);


-- ============================================================================
-- STEP 5: Verify Changes
-- ============================================================================

-- Run these SELECT statements to verify constraints were applied:

-- SELECT constraint_name, table_name, column_name
-- FROM information_schema.constraint_column_usage
-- WHERE constraint_name LIKE 'uq_%' OR constraint_name LIKE 'pk_%'
-- ORDER BY table_name;

-- SELECT tablename, indexname
-- FROM pg_indexes
-- WHERE schemaname = 'public' AND indexname LIKE 'idx_%'
-- ORDER BY tablename;


-- ============================================================================
-- NOTES:
-- ============================================================================
-- 1. This migration adds data integrity and security constraints
-- 2. UNIQUE constraints prevent duplicate emails (critical for auth)
-- 3. NOT NULL constraints ensure essential data is always present
-- 4. Indexes improve query performance
-- 5. Tests required:
--    - Create new user account
--    - Attempt duplicate email registration (should fail)
--    - Login with correct/incorrect credentials
--    - All CRUD operations on transacoes, categorias, metas, gastos_fixos
-- ============================================================================
