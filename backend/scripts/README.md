# Database Scripts

This directory contains utility scripts for managing the Ask My Docs database.

## Scripts

### `init_db.sh` / `init_db.py`

Initialize the PostgreSQL database from scratch.

**Features:**
- Creates PostgreSQL database and user
- Enables PGVector extension
- Runs Alembic migrations to create all 15 tables
- Creates/updates `.env` file with database connection string

**Prerequisites:**
- PostgreSQL 15+ installed and running
- Python 3.11+ (for Python version)
- psycopg2-binary installed (for Python version)

**Usage:**

**Bash version (Linux/macOS):**
```bash
cd backend
./scripts/init_db.sh
```

**Python version (Cross-platform):**
```bash
cd backend
python scripts/init_db.py
```

**Environment Variables:**

You can customize the database settings using environment variables:

```bash
export DB_NAME=askmydocs
export DB_USER=askmydocs
export DB_PASSWORD=password
export DB_HOST=localhost
export DB_PORT=5432
export POSTGRES_USER=postgres
export POSTGRES_PASSWORD=yourpassword  # Optional, Python version only

# Run the script
./scripts/init_db.sh
# or
python scripts/init_db.py
```

**What It Does:**

1. **Checks PostgreSQL Connection**
   - Verifies PostgreSQL is running
   - Tests connection with provided credentials

2. **Drops Existing Database** (if exists)
   - ⚠️ **Warning:** This will delete all existing data!
   - Comment out this step in the script if you want to preserve data

3. **Creates Database User**
   - Creates a new PostgreSQL user
   - Grants SUPERUSER privileges (needed for PGVector)

4. **Creates Database**
   - Creates new database
   - Sets owner to the created user
   - Grants all privileges

5. **Enables PGVector Extension**
   - Adds PGVector support for embedding storage
   - Required for semantic search

6. **Runs Alembic Migrations**
   - Creates all 15 database tables
   - Sets up indexes including PGVector similarity search index

7. **Creates/Updates .env File**
   - Copies from `.env.example` if needed
   - Updates DATABASE_URL with correct connection string

**Output:**

The script provides colored output showing progress:
- 🟢 Green: Success messages
- 🟡 Yellow: Information/warnings
- 🔴 Red: Errors

**After Running:**

The database will be fully initialized with:
- ✅ All 15 tables created
- ✅ PGVector extension enabled
- ✅ HITL support ready
- ✅ Indexes created
- ✅ Foreign keys configured

**Next Steps:**

1. Update `.env` file with:
   - `ANTHROPIC_API_KEY`
   - `OPENAI_API_KEY` (for embeddings)
   - Other API keys as needed

2. Start the backend:
   ```bash
   uvicorn app.main:app --reload
   ```

## Database Schema

The migration creates these 15 tables:

### Core Tables
1. **users** - User authentication and profiles
2. **systems** - Document collections
3. **user_systems** - User permissions per system
4. **documents** - Document metadata
5. **document_chunks** - Text chunks with PGVector embeddings
6. **tags** - Document tags
7. **document_tags** - Document-tag relationships

### Conversation Tables
8. **conversations** - Chat sessions
9. **messages** - Individual messages
10. **message_edits** - Message version history

### HITL Tables
11. **agent_executions** - Agent runs with HITL approval workflow
12. **agent_filesystem** - Deep Agents temporary storage

### Analytics Tables
13. **qa_analytics** - Question-answer tracking
14. **user_feedback** - User ratings and corrections
15. **exports** - PDF/Markdown export tracking
16. **audit_logs** - Full audit trail

## Troubleshooting

### PostgreSQL Not Running

```bash
# macOS (Homebrew)
brew services start postgresql@15

# Linux (systemd)
sudo systemctl start postgresql

# Check status
psql --version
```

### Permission Denied

If you get "permission denied" when running the bash script:

```bash
chmod +x scripts/init_db.sh
```

### Connection Refused

Check PostgreSQL is listening on the correct port:

```bash
psql -h localhost -p 5432 -U postgres -c '\conninfo'
```

### PGVector Extension Not Available

Install PGVector extension:

```bash
# macOS (Homebrew)
brew install pgvector

# Ubuntu/Debian
sudo apt install postgresql-15-pgvector

# From source
git clone https://github.com/pgvector/pgvector.git
cd pgvector
make
make install
```

### Alembic Migration Fails

Check if all Python dependencies are installed:

```bash
pip install -r requirements.txt
# or
poetry install
```

Verify `.env` file has correct DATABASE_URL:

```bash
cat .env | grep DATABASE_URL
```

## Manual Database Setup

If scripts don't work, you can set up manually:

```sql
-- Connect to PostgreSQL
psql -U postgres

-- Create user
CREATE USER askmydocs WITH PASSWORD 'password';
ALTER USER askmydocs WITH SUPERUSER;

-- Create database
CREATE DATABASE askmydocs OWNER askmydocs;
GRANT ALL PRIVILEGES ON DATABASE askmydocs TO askmydocs;

-- Connect to new database
\c askmydocs

-- Enable PGVector
CREATE EXTENSION IF NOT EXISTS vector;

-- Exit
\q
```

Then run migrations:

```bash
cd backend
alembic upgrade head
```
