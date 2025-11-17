# Ask My Docs - Backend

Agentic document intelligence system backend built with FastAPI and Deep Agents.

## 🚀 Quick Start

### Prerequisites

- Python 3.11+
- PostgreSQL 15+
- Redis 7+
- Poetry (recommended) or pip

### Installation

```bash
# Install dependencies with Poetry
poetry install

# Or with pip
pip install -r requirements.txt

# Copy environment template
cp .env.example .env

# Edit .env with your configuration
nano .env
```

### Database Setup

```bash
# Initialize database (creates tables)
poetry run python scripts/init_db.py

# Run migrations
poetry run alembic upgrade head

# Seed test data (optional)
poetry run python scripts/seed_data.py
```

### Running the Application

```bash
# Development server with auto-reload
poetry run uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

# Production server
poetry run uvicorn app.main:app --host 0.0.0.0 --port 8000 --workers 4
```

### Running Background Workers

```bash
# Celery worker for document processing
poetry run celery -A app.tasks.celery_app worker --loglevel=info

# Celery beat for scheduled tasks
poetry run celery -A app.tasks.celery_app beat --loglevel=info
```

## 📁 Project Structure

```
backend/
├── app/
│   ├── api/              # API endpoints
│   ├── core/             # Core functionality (config, security, database)
│   ├── models/           # SQLAlchemy ORM models
│   ├── schemas/          # Pydantic schemas for validation
│   ├── services/         # Business logic layer
│   ├── agents/           # Deep Agents implementation
│   ├── tasks/            # Celery background tasks
│   ├── utils/            # Utility functions
│   └── main.py           # FastAPI application entry point
├── tests/                # Test suite
├── alembic/              # Database migrations
├── scripts/              # Utility scripts
└── data/                 # Local data storage (development)
```

## 🧪 Testing

```bash
# Run all tests
poetry run pytest

# Run with coverage
poetry run pytest --cov=app --cov-report=html

# Run specific test file
poetry run pytest tests/api/test_auth.py

# Run with verbose output
poetry run pytest -v
```

## 🔧 Development Tools

### Code Formatting

```bash
# Format code with Black
poetry run black app tests

# Sort imports with isort
poetry run isort app tests

# Run both
poetry run black app tests && poetry run isort app tests
```

### Code Quality

```bash
# Lint with Ruff
poetry run ruff app tests

# Type check with mypy
poetry run mypy app
```

### Database Migrations

```bash
# Create a new migration
poetry run alembic revision --autogenerate -m "Description of changes"

# Apply migrations
poetry run alembic upgrade head

# Rollback one migration
poetry run alembic downgrade -1

# View migration history
poetry run alembic history
```

## 📚 API Documentation

Once the server is running, visit:

- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc

## 🔐 Environment Variables

See `.env.example` for all available configuration options.

Key variables to configure:

- `DATABASE_URL` - PostgreSQL connection string
- `REDIS_URL` - Redis connection string
- `SECRET_KEY` - JWT signing secret
- `ANTHROPIC_API_KEY` - Anthropic API key for Claude
- `OPENAI_API_KEY` - OpenAI API key for embeddings

## 🐳 Docker

```bash
# Build image
docker build -t askmydocs-backend .

# Run container
docker run -p 8000:8000 --env-file .env askmydocs-backend

# Using Docker Compose
docker-compose up -d
```

## 📖 Documentation

For detailed documentation, see:

- [Architecture](../docs/architecture/backend-structure.md)
- [Database Schema](../docs/database/schema.md)
- [API Specification](../docs/api/rest-api.md)
- [Deep Agents Implementation](../docs/architecture/deep-agents-implementation.md)

## 🤝 Contributing

1. Create a feature branch: `git checkout -b feature/your-feature`
2. Follow the coding standards (Black, isort, type hints)
3. Write tests for new functionality
4. Run linters and tests: `poetry run pytest && poetry run black app && poetry run ruff app`
5. Create a pull request

### Coding Standards

- Use Black for code formatting (100 character line length)
- Use isort for import sorting
- Use type hints for all function parameters and returns
- Write docstrings in Google style
- Maintain >80% test coverage
- Follow RESTful API design principles

## 🐛 Troubleshooting

### Common Issues

**Database connection errors:**
```bash
# Check PostgreSQL is running
psql -h localhost -U askmydocs -d askmydocs

# Reset database (WARNING: deletes all data)
poetry run python scripts/init_db.py --reset
```

**Celery worker not processing tasks:**
```bash
# Check Redis is running
redis-cli ping

# Clear Redis queue
redis-cli FLUSHDB
```

**Import errors:**
```bash
# Reinstall dependencies
poetry install --no-cache

# Clear Python cache
find . -type d -name __pycache__ -exec rm -rf {} +
```

## 📝 License

MIT License - See LICENSE file for details

---

**Status**: 🚀 Ready for Implementation
**Version**: 0.1.0
