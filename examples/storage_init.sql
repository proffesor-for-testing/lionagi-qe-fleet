-- Storage Initialization SQL
-- This file creates the necessary tables for the storage modes example
-- It runs automatically when the Docker container starts for the first time

-- Create agent_memory table for persistent storage
CREATE TABLE IF NOT EXISTS agent_memory (
    id SERIAL PRIMARY KEY,
    key VARCHAR(512) NOT NULL UNIQUE,
    value JSONB NOT NULL,
    partition VARCHAR(128) DEFAULT 'default',
    ttl INTEGER,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    expires_at TIMESTAMP WITH TIME ZONE,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Create indexes for efficient querying
CREATE INDEX IF NOT EXISTS idx_agent_memory_key ON agent_memory(key);
CREATE INDEX IF NOT EXISTS idx_agent_memory_partition ON agent_memory(partition);
CREATE INDEX IF NOT EXISTS idx_agent_memory_expires_at ON agent_memory(expires_at);
CREATE INDEX IF NOT EXISTS idx_agent_memory_created_at ON agent_memory(created_at);

-- Create GIN index for JSONB value column (enables fast JSON queries)
CREATE INDEX IF NOT EXISTS idx_agent_memory_value_gin ON agent_memory USING GIN(value);

-- Create function to automatically update updated_at timestamp
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ language 'plpgsql';

-- Create trigger to call the update function
DROP TRIGGER IF EXISTS update_agent_memory_updated_at ON agent_memory;
CREATE TRIGGER update_agent_memory_updated_at
    BEFORE UPDATE ON agent_memory
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

-- Create function to automatically set expires_at based on ttl
CREATE OR REPLACE FUNCTION set_expires_at()
RETURNS TRIGGER AS $$
BEGIN
    IF NEW.ttl IS NOT NULL THEN
        NEW.expires_at = CURRENT_TIMESTAMP + (NEW.ttl || ' seconds')::INTERVAL;
    ELSE
        NEW.expires_at = NULL;
    END IF;
    RETURN NEW;
END;
$$ language 'plpgsql';

-- Create trigger to set expires_at
DROP TRIGGER IF EXISTS set_agent_memory_expires_at ON agent_memory;
CREATE TRIGGER set_agent_memory_expires_at
    BEFORE INSERT OR UPDATE ON agent_memory
    FOR EACH ROW
    EXECUTE FUNCTION set_expires_at();

-- Insert example data for testing
INSERT INTO agent_memory (key, value, partition, ttl)
VALUES
    ('aqe/example/welcome', '{"message": "Storage system initialized successfully", "timestamp": "2025-11-05T12:00:00Z"}', 'examples', 86400),
    ('aqe/config/version', '{"version": "1.0.0", "storage_mode": "production"}', 'config', NULL)
ON CONFLICT (key) DO NOTHING;

-- Display initialization status
SELECT
    'agent_memory' as table_name,
    COUNT(*) as row_count,
    pg_size_pretty(pg_total_relation_size('agent_memory')) as total_size
FROM agent_memory;

-- Display example data
SELECT
    key,
    partition,
    created_at,
    expires_at
FROM agent_memory
ORDER BY created_at DESC
LIMIT 5;
