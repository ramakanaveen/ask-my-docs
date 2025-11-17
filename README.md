# Ask My Docs - Document Intelligence System

> An agentic, human-in-the-loop document intelligence system for multi-document analysis and report generation

[![Python](https://img.shields.io/badge/Python-3.11+-blue.svg)](https://www.python.org/downloads/)
[![FastAPI](https://img.shields.io/badge/FastAPI-Latest-green.svg)](https://fastapi.tiangolo.com/)
[![React](https://img.shields.io/badge/React-18+-61DAFB.svg)](https://reactjs.org/)
[![License](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

## 🚀 Quick Start

**Project Status:** 🎉 Design Phase Complete - Ready for Implementation

We've completed comprehensive design documentation. Check out our [project overview](claude.md) for the complete vision.

## 📋 What is Ask My Docs?

Ask My Docs is an intelligent document processing system that allows users to:

- 📤 **Upload documents** (PDF, PPT, Word, Excel, Code, Images)
- 🏷️ **Organize by tags** (System A, Financial Reports, Projects, etc.)
- 🤖 **Ask questions** to an AI agent that analyzes documents intelligently
- 📊 **Get rich reports** with professional charts, tables, and insights
- ✏️ **Edit & export** results as PDF or Markdown
- 🔍 **Track everything** for compliance and system improvement

### Key Features

- **Multi-User System**: Document Managers curate collections, Users query them
- **Instant Personal Uploads**: Upload and query documents on-the-fly
- **Persistent Storage**: Documents uploaded once, queried across many sessions
- **Agentic AI**: Multi-step reasoning with human-in-the-loop checkpoints
- **Professional Output**: Analyst-quality reports with charts and visualizations
- **Full Audit Trail**: All Q&A logged for compliance and analytics

## 🏗️ Architecture

```
┌─────────────────────────────────────────────────┐
│           User Interfaces (React + Streamlit)    │
├─────────────────────────────────────────────────┤
│         Backend API (FastAPI + MCP Server)      │
├─────────────────────────────────────────────────┤
│    Agent Orchestration (LangGraph + LangChain)  │
├─────────────────────────────────────────────────┤
│   Document Processing (Multi-format Support)    │
├─────────────────────────────────────────────────┤
│  Storage (PostgreSQL + Vector DB + S3)          │
├─────────────────────────────────────────────────┤
│       LLM Providers (Claude, Gemini, GPT)       │
└─────────────────────────────────────────────────┘
```

For detailed architecture, see [System Architecture](docs/architecture/01-system-overview.md) *(coming soon)*

## 📚 Documentation

Our documentation is organized for both humans and AI assistants (Claude Code, Copilot, etc.):

### For Quick Understanding
- **[claude.md](claude.md)** - Complete project vision and requirements (start here!)
- **[README.md](README.md)** - This file (getting started guide)

### For Detailed Design
- **[docs/architecture/](docs/architecture/)** - System design, Deep Agents implementation ✅
- **[docs/database/](docs/database/)** - Complete database schema with 15 tables ✅
- **[docs/api/](docs/api/)** - REST API & WebSocket specifications ✅
- **[docs/design/](docs/design/)** - Use case technical design ✅
- **[docs/development/](docs/development/)** - Setup, coding standards, testing

## 🎯 Project Roadmap

### Phase 0: Design & Planning ✅ *Complete*
- [x] Project vision and requirements
- [x] Complete database schema (15 tables with relationships)
- [x] REST API specification (70+ endpoints)
- [x] WebSocket event specification
- [x] Deep Agents implementation strategy
- [x] Backend project structure
- [x] Use case technical design

### Phase 1: Foundation & Authentication *(Ready to Start)*
- [ ] Implement database schema with Alembic migrations
- [ ] User authentication (JWT)
- [ ] System-centric RBAC implementation
- [ ] Basic FastAPI server with core endpoints

### Phase 2: Document Processing *(Not Started)*
- [ ] Multi-format document processing (PDF, PPT, Word, Excel, etc.)
- [ ] Storage setup (PostgreSQL + Vector DB)
- [ ] Embedding generation
- [ ] Tag and permission system

### Phase 3: Agent Core *(Not Started)*
- [ ] LangGraph agent setup
- [ ] Basic RAG implementation
- [ ] Permission-filtered retrieval
- [ ] Simple CLI interface

### Phase 4: Advanced Agent Features *(Not Started)*
- [ ] Multi-step reasoning
- [ ] Human-in-the-loop checkpoints
- [ ] Rich output generation (charts, tables)
- [ ] Session persistence

### Phase 5: MCP Server *(Not Started)*
- [ ] MCP protocol implementation
- [ ] Standardized tools
- [ ] Integration testing

### Phase 6: Streamlit UI *(Not Started)*
- [ ] Document manager interface
- [ ] User query interface
- [ ] Analytics dashboard

### Phase 7: React UI *(Not Started)*
- [ ] Production web app
- [ ] Rich editing capabilities
- [ ] Export features

### Phase 8: Production Ready *(Not Started)*
- [ ] Performance optimization
- [ ] Security hardening
- [ ] Compliance features

## 🛠️ Tech Stack

### Backend
- **Python 3.11+** - Core language
- **FastAPI** - API framework
- **LangGraph** - Agent orchestration
- **LangChain** - Tool management
- **PostgreSQL** - Metadata & user data
- **ChromaDB/Pinecone** - Vector database
- **Celery** - Background tasks
- **Redis** - Caching & queues

### Frontend
- **React 18+** - UI framework
- **TypeScript** - Type safety
- **TailwindCSS** - Styling
- **Streamlit** - Rapid prototyping
- **Recharts/D3.js** - Visualizations
- **TipTap** - Rich text editing

### AI/ML
- **Anthropic Claude** - Primary LLM
- **Google Gemini** - Alternative LLM
- **OpenAI GPT** - Vision & embeddings
- **Sentence Transformers** - Embeddings

### Document Processing
- **PyMuPDF** - PDF processing
- **python-pptx** - PowerPoint
- **python-docx** - Word documents
- **openpyxl** - Excel files
- **Unstructured.io** - Unified processing
- **Tesseract** - OCR

## 🚦 Getting Started (Coming Soon)

Once we're ready to code, setup will look like:

```bash
# Clone the repository
git clone <repo-url>
cd ask-my-docs

# Backend setup
cd backend
python -m venv venv
source venv/bin/activate  # or `venv\Scripts\activate` on Windows
pip install -r requirements.txt

# Frontend setup
cd ../frontend
npm install

# Environment configuration
cp .env.example .env
# Edit .env with your API keys and configuration

# Run development servers
# Backend: uvicorn main:app --reload
# Frontend: npm run dev
```

## 🤝 Contributing

**Design Phase: Complete!** ✅

We've completed comprehensive design documentation:
1. ✅ **Architecture Design** - Deep Agents implementation strategy
2. ✅ **Database Schema** - 15 tables with full relationships and indexes
3. ✅ **API Specifications** - REST (70+ endpoints) and WebSocket
4. ✅ **Backend Structure** - Complete module organization
5. ✅ **Use Case Design** - End-to-end technical flows

**Next: Implementation Phase**

Ready to start building! We're now moving to implementation:
- Setting up backend project structure
- Creating database migrations
- Implementing authentication
- Building core API endpoints

Want to contribute? Check out the issues or reach out!

## 📖 Use Cases

### Use Case 1: System Documentation Q&A
Document Manager uploads "System A" manuals → Users ask installation questions → Get instant answers with citations

### Use Case 2: Instant Personal Upload
User uploads a contract → Immediately asks about payment terms → Gets answer, all logged for compliance

### Use Case 3: Financial Analysis
CFO queries quarterly reports → Gets professional analysis with charts → Edits in UI → Exports as PDF for board meeting

See [claude.md](claude.md) for detailed use case walkthroughs.

## 📄 License

MIT License - See [LICENSE](LICENSE) file for details

## 🔗 Links

- **Documentation**: [/docs](docs/)
- **Project Vision**: [claude.md](claude.md)
- **Issues**: (Coming soon)
- **Discussions**: (Coming soon)

## 📞 Contact

For questions or collaboration, please open an issue or reach out to the maintainers.

---

**Status**: ✅ Design Complete → 🚀 Implementation Ready | **Next**: Backend Setup → Database Migrations → Core API

Built with ❤️ using Claude Code and modern AI tools
