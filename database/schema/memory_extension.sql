-- ============================================================================
-- QE Memory Extension - General Purpose Memory Storage
-- ============================================================================
-- Extends existing lionagi_qe_learning database with memory table
-- Reuses existing connection pool and infrastructure
--
-- Purpose: Add general-purpose persistent memory storage for QE agents
--          that reuses the existing PostgreSQL infrastructure from Q-learning
--
-- Schema: Adds 1 table (qe_memory) to the 7 existing Q-learning tables
-- Namespace: All keys must start with 'aqe/' prefix
-- TTL Support: Automatic expiration via expires_at column
-- Performance: Indexed on partition, expiration, and key prefix
--
-- Usage:
--   sudo docker exec -i lionagi-qe-postgres psql -U qe_agent -d lionagi_qe_learning \
--     < database/schema/memory_extension.sql
--
-- Verification:
--   sudo docker exec lionagi-qe-postgres psql -U qe_agent -d lionagi_qe_learning -c "\dt"
--   # Should show 8 tables (7 existing + qe_memory)
-- ============================================================================

-- Create qe_memory table for general-purpose persistent memory
CREATE TABLE IF NOT EXISTS qe_memory (
    key VARCHAR(255) PRIMARY KEY,
    value JSONB NOT NULL,
    partition VARCHAR(50) DEFAULT 'default',
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    expires_at TIMESTAMPTZ,
    metadata JSONB DEFAULT '{}'::jsonb,

    -- Constraint: Enforce aqe/* namespace
    CONSTRAINT qe_memory_key_format CHECK (key ~ '^aqe/.*')
);

-- Index for partition-based queries (e.g., clear_partition())
CREATE INDEX IF NOT EXISTS idx_qe_memory_partition
    ON qe_memory(partition);

-- Index for expiration cleanup (only index non-NULL expires_at)
CREATE INDEX IF NOT EXISTS idx_qe_memory_expires
    ON qe_memory(expires_at)
    WHERE expires_at IS NOT NULL;

-- Index for key prefix searches (e.g., list_keys('aqe/test-plan/'))
CREATE INDEX IF NOT EXISTS idx_qe_memory_key_prefix
    ON qe_memory(key text_pattern_ops);

-- Function to clean up expired entries
CREATE OR REPLACE FUNCTION cleanup_expired_memory()
RETURNS TABLE(deleted_count INTEGER) AS $$
DECLARE
    count_deleted INTEGER;
BEGIN
    DELETE FROM qe_memory
    WHERE expires_at IS NOT NULL
    AND expires_at < NOW();

    GET DIAGNOSTICS count_deleted = ROW_COUNT;

    RETURN QUERY SELECT count_deleted;
END;
$$ LANGUAGE plpgsql;

-- Optional: Create periodic cleanup job (requires pg_cron extension)
-- Uncomment if pg_cron is installed:
-- SELECT cron.schedule(
--     'cleanup-qe-memory',           -- Job name
--     '0 * * * *',                    -- Every hour
--     'SELECT cleanup_expired_memory();'
-- );

-- Table and column comments for documentation
COMMENT ON TABLE qe_memory IS 'General-purpose persistent memory for QE agents. All keys must use aqe/* namespace. Supports TTL-based expiration and partition-based organization. Reuses existing Q-learning database connection pool.';

COMMENT ON COLUMN qe_memory.key IS 'Unique memory key (e.g., aqe/test-plan/generated, aqe/coverage/gaps). Must start with aqe/ prefix per namespace constraint.';

COMMENT ON COLUMN qe_memory.value IS 'JSONB value storing any serializable data. Supports nested objects, arrays, and efficient querying.';

COMMENT ON COLUMN qe_memory.partition IS 'Logical partition for organization (e.g., test-plan, coverage, quality). Used for bulk operations like clear_partition().';

COMMENT ON COLUMN qe_memory.expires_at IS 'Automatic expiration timestamp (NULL = never expires). Expired entries are cleaned up by cleanup_expired_memory() function.';

COMMENT ON COLUMN qe_memory.metadata IS 'Optional metadata for tracking provenance, versioning, or custom attributes.';

-- Grant permissions to qe_agent user
GRANT SELECT, INSERT, UPDATE, DELETE ON qe_memory TO qe_agent;
GRANT EXECUTE ON FUNCTION cleanup_expired_memory() TO qe_agent;

-- Display success message
DO $$
BEGIN
    RAISE NOTICE 'QE Memory Extension installed successfully!';
    RAISE NOTICE 'Table: qe_memory (namespace: aqe/*)';
    RAISE NOTICE 'Indexes: partition, expires_at, key_prefix';
    RAISE NOTICE 'Function: cleanup_expired_memory()';
    RAISE NOTICE '';
    RAISE NOTICE 'Next steps:';
    RAISE NOTICE '1. Verify: \dt';
    RAISE NOTICE '2. Test: INSERT INTO qe_memory (key, value) VALUES (''aqe/test'', ''{}'');';
    RAISE NOTICE '3. Use: PostgresMemory class in src/lionagi_qe/persistence/';
END;
$$ LANGUAGE plpgsql;
