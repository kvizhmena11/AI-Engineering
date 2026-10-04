Set-Content -Path data/runbooks/postgres_pool_exhaustion.md -Value @"
# Runbook: PostgreSQL Connection Pool Exhaustion

## Incident Overview
Applications fail to communicate with PostgreSQL due to reaching `max_connections` limits or exhaustion of application-side connection pools (e.g., PgBouncer, HikariCP, SQLAlchemy).

## Failure Signatures
- Error message: `FATAL: remaining connection slots are reserved for non-replication superuser connections`
- Error message: `psycopg2.OperationalError: FATAL: sorry, too many clients already`
- Spike in HTTP 500 errors across backend services.

## Diagnostic Steps
1. Query active connection count by database and state:
   ```sql
   SELECT datname, state, count(*) 
   FROM pg_stat_activity 
   GROUP BY datname, state;