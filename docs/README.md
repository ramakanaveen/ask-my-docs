# Ask My Docs - Documentation

Welcome to the Ask My Docs documentation! This is organized for both humans and AI assistants.

## 📚 Documentation Structure

### Quick Start
- **[../README.md](../README.md)** - Getting started guide
- **[../claude.md](../claude.md)** - Complete project vision (start here for full context!)

### Detailed Documentation

#### 🏗️ [Architecture](architecture/)
System design, components, and data flow
- System overview and high-level architecture
- Backend architecture and services
- Frontend architecture and state management
- Agent orchestration and reasoning
- Data flow and processing pipelines

#### 🗄️ [Database](database/)
Database schema, models, and migrations
- Complete database schema with all tables
- Migration strategy and versioning
- SQLAlchemy/Pydantic models

#### 🔌 [API](api/)
REST API, WebSocket, and MCP server specifications
- RESTful API endpoints and contracts
- WebSocket events for real-time updates
- MCP server tools and integration

#### 🎨 [Design](design/)
UI/UX design, workflows, and wireframes
- Component library and design system
- User workflows and journeys
- Wireframes and mockups
- Professional output formatting guidelines

#### 🛠️ [Development](development/)
Setup, coding standards, and testing
- Local development setup
- Coding standards and conventions
- Testing strategy and guidelines
- Deployment procedures

## 🎯 Current Status

**Phase**: Design & Planning - Core Design Complete ✅

Completed:
1. ✅ Project vision and requirements ([claude.md](../claude.md))
2. ✅ Documentation structure setup
3. ✅ Database schema design ([database/schema.md](database/schema.md))
4. ✅ Backend architecture design ([architecture/backend-structure.md](architecture/backend-structure.md))
5. ✅ API specifications ([api/rest-api.md](api/rest-api.md), [api/websocket-api.md](api/websocket-api.md))
6. ✅ Deep Agents implementation strategy ([architecture/deep-agents-implementation.md](architecture/deep-agents-implementation.md))
7. ✅ Use case technical design ([design/use-case-technical-design.md](design/use-case-technical-design.md))

Next Steps:
- UI/UX design and wireframes
- Frontend architecture
- Begin implementation

## 🤖 For AI Assistants (Claude Code, Copilot, etc.)

When working on this codebase:

1. **Start with context**: Read [claude.md](../claude.md) for full project vision
2. **Check architecture**: Review relevant docs in [architecture/](architecture/)
3. **Database models**: See [database/](database/) for schema
4. **API contracts**: Check [api/](api/) for endpoint specs
5. **Coding standards**: Follow guidelines in [development/](development/)

## 📖 How to Use This Documentation

### For Developers
1. Read the [README](../README.md) for quick overview
2. Review [claude.md](../claude.md) for complete vision
3. Check architecture docs before implementing features
4. Refer to API specs when building endpoints
5. Follow coding standards in development docs

### For Designers
1. Start with user workflows in [design/](design/)
2. Review design principles and personas
3. Create wireframes based on use cases
4. Ensure designs align with UX goals

### For Project Managers
1. Check roadmap in [README](../README.md)
2. Review use cases in [claude.md](../claude.md)
3. Track progress against development phases
4. Use architecture docs to understand technical decisions

## 🔄 Keeping Docs Updated

As we develop:
- Update docs alongside code changes
- Keep diagrams in sync with implementation
- Document important design decisions
- Add examples and code snippets
- Link to relevant code files

## 📝 Documentation Format

All documentation is written in **Markdown** for:
- Easy version control
- AI assistant readability
- Beautiful rendering on GitHub/GitLab
- Simple editing in any text editor

## 🤝 Contributing to Docs

Found something unclear? Want to add more details?
1. Edit the relevant markdown file
2. Follow the existing structure
3. Use clear headings and examples
4. Submit a pull request

---

**Last Updated**: 2025-11-15
**Status**: 🎨 Design Phase
**Next**: Database Schema Design
