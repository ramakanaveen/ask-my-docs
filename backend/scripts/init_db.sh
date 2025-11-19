#!/bin/bash

###############################################################################
# Database Initialization Script
#
# This script initializes the PostgreSQL database for Ask My Docs:
# - Creates database and user
# - Enables PGVector extension
# - Runs Alembic migrations
###############################################################################

set -e  # Exit on error

# Colors for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# Default values (can be overridden by environment variables)
DB_NAME="${DB_NAME:-askmydocs}"
DB_USER="${DB_USER:-askmydocs}"
DB_PASSWORD="${DB_PASSWORD:-password}"
DB_HOST="${DB_HOST:-localhost}"
DB_PORT="${DB_PORT:-5432}"
POSTGRES_USER="${POSTGRES_USER:-postgres}"

echo -e "${GREEN}========================================${NC}"
echo -e "${GREEN}Ask My Docs - Database Initialization${NC}"
echo -e "${GREEN}========================================${NC}"
echo ""

# Check if PostgreSQL is running
echo -e "${YELLOW}→ Checking PostgreSQL connection...${NC}"
if ! psql -h "$DB_HOST" -p "$DB_PORT" -U "$POSTGRES_USER" -c '\q' 2>/dev/null; then
    echo -e "${RED}✗ Cannot connect to PostgreSQL at $DB_HOST:$DB_PORT${NC}"
    echo -e "${RED}  Please ensure PostgreSQL is running and credentials are correct.${NC}"
    echo -e "${YELLOW}  You may need to set POSTGRES_USER environment variable.${NC}"
    exit 1
fi
echo -e "${GREEN}✓ PostgreSQL is running${NC}"
echo ""

# Drop database if it exists (optional - comment out if you want to preserve data)
echo -e "${YELLOW}→ Checking if database exists...${NC}"
if psql -h "$DB_HOST" -p "$DB_PORT" -U "$POSTGRES_USER" -lqt | cut -d \| -f 1 | grep -qw "$DB_NAME"; then
    echo -e "${YELLOW}  Database '$DB_NAME' already exists. Dropping it...${NC}"
    psql -h "$DB_HOST" -p "$DB_PORT" -U "$POSTGRES_USER" -c "DROP DATABASE IF EXISTS $DB_NAME;" || true
    echo -e "${GREEN}✓ Dropped existing database${NC}"
fi
echo ""

# Drop user if exists (to recreate with fresh permissions)
echo -e "${YELLOW}→ Checking if user exists...${NC}"
if psql -h "$DB_HOST" -p "$DB_PORT" -U "$POSTGRES_USER" -tAc "SELECT 1 FROM pg_roles WHERE rolname='$DB_USER'" | grep -q 1; then
    echo -e "${YELLOW}  User '$DB_USER' already exists. Dropping it...${NC}"
    psql -h "$DB_HOST" -p "$DB_PORT" -U "$POSTGRES_USER" -c "DROP USER IF EXISTS $DB_USER;" || true
    echo -e "${GREEN}✓ Dropped existing user${NC}"
fi
echo ""

# Create database user
echo -e "${YELLOW}→ Creating database user '$DB_USER'...${NC}"
psql -h "$DB_HOST" -p "$DB_PORT" -U "$POSTGRES_USER" <<-EOSQL
    CREATE USER $DB_USER WITH PASSWORD '$DB_PASSWORD';
    ALTER USER $DB_USER WITH SUPERUSER;
EOSQL
echo -e "${GREEN}✓ User created${NC}"
echo ""

# Create database
echo -e "${YELLOW}→ Creating database '$DB_NAME'...${NC}"
psql -h "$DB_HOST" -p "$DB_PORT" -U "$POSTGRES_USER" <<-EOSQL
    CREATE DATABASE $DB_NAME OWNER $DB_USER;
    GRANT ALL PRIVILEGES ON DATABASE $DB_NAME TO $DB_USER;
EOSQL
echo -e "${GREEN}✓ Database created${NC}"
echo ""

# Enable PGVector extension
echo -e "${YELLOW}→ Enabling PGVector extension...${NC}"
psql -h "$DB_HOST" -p "$DB_PORT" -U "$POSTGRES_USER" -d "$DB_NAME" <<-EOSQL
    CREATE EXTENSION IF NOT EXISTS vector;
EOSQL
echo -e "${GREEN}✓ PGVector extension enabled${NC}"
echo ""

# Run Alembic migrations
echo -e "${YELLOW}→ Running database migrations...${NC}"
cd "$(dirname "$0")/.." || exit 1  # Go to backend directory

# Check if .env file exists
if [ ! -f .env ]; then
    echo -e "${YELLOW}  No .env file found. Creating from .env.example...${NC}"
    cp .env.example .env
    # Update DATABASE_URL in .env
    sed -i.bak "s|DATABASE_URL=.*|DATABASE_URL=postgresql://$DB_USER:$DB_PASSWORD@$DB_HOST:$DB_PORT/$DB_NAME|g" .env
    rm .env.bak 2>/dev/null || true
    echo -e "${GREEN}✓ Created .env file${NC}"
fi

# Run migrations
echo -e "${YELLOW}  Applying migrations...${NC}"
alembic upgrade head
echo -e "${GREEN}✓ Migrations completed${NC}"
echo ""

# Display summary
echo -e "${GREEN}========================================${NC}"
echo -e "${GREEN}✓ Database initialization complete!${NC}"
echo -e "${GREEN}========================================${NC}"
echo ""
echo "Database Details:"
echo "  Host:     $DB_HOST"
echo "  Port:     $DB_PORT"
echo "  Database: $DB_NAME"
echo "  User:     $DB_USER"
echo "  Password: $DB_PASSWORD"
echo ""
echo "Connection String:"
echo "  postgresql://$DB_USER:$DB_PASSWORD@$DB_HOST:$DB_PORT/$DB_NAME"
echo ""
echo -e "${YELLOW}Next steps:${NC}"
echo "  1. Update your .env file with the correct API keys"
echo "  2. Run the backend: uvicorn app.main:app --reload"
echo ""
