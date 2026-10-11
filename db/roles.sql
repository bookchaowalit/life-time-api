-- Roles for the time database. Locally a superuser runs this; on Neon
-- `time-db provision` creates the same roles through the migrator.
--
-- time_migrator  owns the schema and runs migrations only.
-- time_api       the API at runtime: no superuser, no BYPASSRLS, owns nothing.
-- time_publisher sweeps and marks the outbox across workspaces; nothing else.

DO $$
BEGIN
    IF NOT EXISTS (SELECT FROM pg_roles WHERE rolname = 'time_migrator') THEN
        CREATE ROLE time_migrator LOGIN NOSUPERUSER NOCREATEROLE NOBYPASSRLS;
    END IF;
    IF NOT EXISTS (SELECT FROM pg_roles WHERE rolname = 'time_api') THEN
        CREATE ROLE time_api LOGIN NOSUPERUSER NOCREATEDB NOCREATEROLE NOBYPASSRLS NOINHERIT;
    END IF;
    IF NOT EXISTS (SELECT FROM pg_roles WHERE rolname = 'time_publisher') THEN
        CREATE ROLE time_publisher LOGIN NOSUPERUSER NOCREATEDB NOCREATEROLE NOBYPASSRLS NOINHERIT;
    END IF;
END
$$;
