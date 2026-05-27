-- Marca de inicialización completa.
-- El healthcheck de Docker espera esta tabla para evitar que Metabase se conecte
-- mientras PostgreSQL todavía está cargando DATA.sql.
CREATE TABLE IF NOT EXISTS retailmax_init_ready (
    id INT PRIMARY KEY,
    completed_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

INSERT INTO retailmax_init_ready (id)
VALUES (1)
ON CONFLICT (id) DO UPDATE
SET completed_at = NOW();
