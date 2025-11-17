# Development Documentation

Setup guides, coding standards, testing strategies, and contribution guidelines.

## 📑 Documents

- **[setup.md](setup.md)** - Local development setup *(Coming soon)*
- **[coding-standards.md](coding-standards.md)** - Code style and conventions *(Coming soon)*
- **[testing.md](testing.md)** - Testing strategy and guidelines *(Coming soon)*
- **[deployment.md](deployment.md)** - Deployment procedures *(Coming soon)*

## 🛠️ Development Stack

### Backend
- Python 3.11+
- FastAPI for APIs
- LangGraph for agent orchestration
- PostgreSQL for data
- ChromaDB for vectors

### Frontend
- React 18+ with TypeScript
- TailwindCSS for styling
- Vite for build tooling
- Recharts/D3.js for charts

## 📋 Coding Standards (Draft)

### Python
- **Style**: Follow PEP 8
- **Formatting**: Use `black` and `isort`
- **Linting**: `ruff` or `pylint`
- **Type Hints**: Required for all functions
- **Docstrings**: Google style

Example:
```python
from typing import List, Optional

def get_user_documents(
    user_id: str,
    tags: Optional[List[str]] = None
) -> List[Document]:
    """Get all documents accessible to a user.

    Args:
        user_id: The ID of the user
        tags: Optional list of tags to filter by

    Returns:
        List of Document objects
    """
    # Implementation
    pass
```

### TypeScript/React
- **Style**: Airbnb style guide
- **Formatting**: Prettier
- **Linting**: ESLint
- **Components**: Functional components with hooks
- **Props**: Use TypeScript interfaces

Example:
```typescript
interface UserDocumentsProps {
  userId: string;
  tags?: string[];
  onDocumentClick: (doc: Document) => void;
}

export const UserDocuments: React.FC<UserDocumentsProps> = ({
  userId,
  tags,
  onDocumentClick
}) => {
  // Implementation
};
```

## 🧪 Testing Strategy (Planned)

### Backend Tests
- **Unit Tests**: pytest for all business logic
- **Integration Tests**: Test API endpoints
- **Agent Tests**: Test reasoning and tool usage
- **Performance Tests**: Load testing with locust

### Frontend Tests
- **Unit Tests**: Vitest for utilities
- **Component Tests**: React Testing Library
- **E2E Tests**: Playwright for critical flows
- **Visual Tests**: Chromatic for UI changes

## 🚀 Development Workflow

1. **Create feature branch**: `git checkout -b feature/your-feature`
2. **Write code**: Follow coding standards
3. **Write tests**: Maintain >80% coverage
4. **Run linters**: `black`, `isort`, `ruff`, `prettier`, `eslint`
5. **Run tests**: All tests must pass
6. **Commit**: Use conventional commits
7. **Push & PR**: Create pull request for review

## 📦 Project Structure (Planned)

```
ask-my-docs/
├── backend/
│   ├── app/
│   │   ├── api/         # API endpoints
│   │   ├── core/        # Config, security
│   │   ├── models/      # Database models
│   │   ├── schemas/     # Pydantic schemas
│   │   ├── services/    # Business logic
│   │   ├── agents/      # Agent orchestration
│   │   └── utils/       # Utilities
│   ├── tests/
│   ├── alembic/         # Database migrations
│   └── requirements.txt
├── frontend/
│   ├── src/
│   │   ├── components/  # React components
│   │   ├── pages/       # Page components
│   │   ├── hooks/       # Custom hooks
│   │   ├── api/         # API client
│   │   ├── store/       # State management
│   │   └── utils/       # Utilities
│   ├── tests/
│   └── package.json
├── docs/                # This folder
├── claude.md           # Project overview
└── README.md           # Getting started
```

---

*Last updated: 2025-11-15*
