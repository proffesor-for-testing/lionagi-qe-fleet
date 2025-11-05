-- LionAGI QE Fleet - PostgreSQL Initialization Script
-- This script runs automatically on first container startup
-- Database and user are created by PostgreSQL based on environment variables

-- Enable extensions for enhanced functionality
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "pg_trgm";  -- For full-text search on test patterns
CREATE EXTENSION IF NOT EXISTS "hstore";    -- For storing JSON-like data

-- Create schema for Q-Learning components
CREATE SCHEMA IF NOT EXISTS qlearning;

-- Grant permissions to qe_agent user for all schemas
GRANT USAGE ON SCHEMA public TO qe_agent;
GRANT USAGE ON SCHEMA qlearning TO qe_agent;
GRANT CREATE ON SCHEMA public TO qe_agent;
GRANT CREATE ON SCHEMA qlearning TO qe_agent;

-- Allow qe_agent to modify all future objects in these schemas
ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT SELECT, INSERT, UPDATE, DELETE ON TABLES TO qe_agent;
ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT USAGE, SELECT ON SEQUENCES TO qe_agent;
ALTER DEFAULT PRIVILEGES IN SCHEMA qlearning GRANT SELECT, INSERT, UPDATE, DELETE ON TABLES TO qe_agent;
ALTER DEFAULT PRIVILEGES IN SCHEMA qlearning GRANT USAGE, SELECT ON SEQUENCES TO qe_agent;

-- Create indexes for performance optimization
CREATE INDEX IF NOT EXISTS idx_public_created_at ON public.* (created_at DESC);
CREATE INDEX IF NOT EXISTS idx_qlearning_created_at ON qlearning.* (created_at DESC);

-- Set search path for qe_agent user
ALTER ROLE qe_agent SET search_path = public, qlearning;

-- Log initialization completion
SELECT pg_catalog.set_config('application_name', 'lionagi-qe-init', false);
