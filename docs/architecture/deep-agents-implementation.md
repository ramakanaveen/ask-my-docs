# Deep Agents Implementation Strategy

Comprehensive implementation guide for Deep Agents in Ask My Docs.

## Overview

This document defines the complete Deep Agents implementation including:
- Query complexity classification
- Agent factory architecture
- Subagent definitions and specializations
- Tool specifications
- System prompts
- Integration with backend services

---

## 1. Query Complexity Classification

### Classification Logic

Queries are automatically classified into three complexity tiers to optimize cost and performance.

```python
# app/agents/complexity_classifier.py

from typing import Literal
from anthropic import Anthropic

ComplexityLevel = Literal["simple", "moderate", "complex"]

class QueryComplexityClassifier:
    """Classifies user queries into complexity tiers."""

    def __init__(self, model: str = "claude-haiku"):
        self.client = Anthropic()
        self.model = model

    def classify(self, question: str, conversation_history: list = None) -> ComplexityLevel:
        """Classify query complexity using fast LLM."""

        system_prompt = """You are a query complexity classifier for a document Q&A system.

Classify queries into three categories:

**Simple** - Single fact lookup, straightforward questions
Examples:
- "What is System A?"
- "How do I restart the service?"
- "What port does System A use?"

**Moderate** - Multi-document analysis, comparisons, synthesis
Examples:
- "Compare installation procedures for System A v1 vs v2"
- "What are all the configuration options across the documentation?"
- "Summarize the troubleshooting section"

**Complex** - Multi-step analysis, trends, data extraction, reports
Examples:
- "Analyze our financial performance across all quarterly reports"
- "Create a comparison report of all system features"
- "Extract all API endpoints and create a reference table"

Return ONLY one word: simple, moderate, or complex"""

        user_prompt = f"Question: {question}"

        if conversation_history:
            # Consider conversation context
            recent_messages = conversation_history[-3:]  # Last 3 messages
            context = "\n".join([f"{m['role']}: {m['content']}" for m in recent_messages])
            user_prompt = f"Conversation context:\n{context}\n\nNew question: {question}"

        response = self.client.messages.create(
            model=self.model,
            max_tokens=10,
            system=system_prompt,
            messages=[{"role": "user", "content": user_prompt}]
        )

        result = response.content[0].text.strip().lower()

        # Validate and default to moderate if unclear
        if result in ["simple", "moderate", "complex"]:
            return result
        else:
            return "moderate"


# Usage
classifier = QueryComplexityClassifier()
complexity = classifier.classify("How do I install System A on Ubuntu?")
# Returns: "simple"
```

### Classification Rules

| Complexity | Characteristics | Agent Type | Model |
|------------|----------------|------------|-------|
| **Simple** | Single fact, direct lookup, short answer | Basic agent, no planning | Haiku |
| **Moderate** | 2-3 documents, some synthesis, moderate length | Planning agent with HITL | Sonnet |
| **Complex** | Multi-document, data extraction, trends, reports | Full Deep Agent with subagents | Sonnet-4 |

---

## 2. Agent Factory Architecture

### Factory Pattern

```python
# app/agents/agent_factory.py

from typing import List, Optional
from deepagents import create_deep_agent
from langgraph.store.memory import InMemoryStore

from app.agents.complexity_classifier import QueryComplexityClassifier, ComplexityLevel
from app.agents.tools import get_tools_for_complexity
from app.agents.subagents import SUBAGENT_REGISTRY
from app.agents.prompts import get_system_prompt
from app.models.user import User
from app.core.websocket import WebSocketManager

class DocumentQAAgentFactory:
    """Factory for creating appropriate agents based on query complexity."""

    def __init__(self):
        self.classifier = QueryComplexityClassifier()
        self.user_stores = {}  # Cache user memory stores

    def create_agent(
        self,
        user: User,
        accessible_documents: List[str],
        system_filters: List[str],
        websocket: Optional[WebSocketManager] = None,
        force_complexity: Optional[ComplexityLevel] = None
    ):
        """Create agent based on query complexity."""

        # Get or create user's memory store
        store = self._get_user_store(user.id)

        # Determine complexity (can be forced for testing)
        complexity = force_complexity or "auto"  # Will be determined per query

        # Create agent configuration
        config = {
            "user_id": user.id,
            "accessible_documents": accessible_documents,
            "system_filters": system_filters,
            "websocket": websocket,
            "store": store
        }

        # Return factory method that creates agent per query
        def agent_factory(question: str, conversation_history: list = None):
            # Classify query if not forced
            if force_complexity:
                query_complexity = force_complexity
            else:
                query_complexity = self.classifier.classify(question, conversation_history)

            return self._create_agent_for_complexity(
                complexity=query_complexity,
                config=config
            )

        return agent_factory

    def _create_agent_for_complexity(
        self,
        complexity: ComplexityLevel,
        config: dict
    ):
        """Create specific agent based on complexity."""

        if complexity == "simple":
            return self._create_simple_agent(config)
        elif complexity == "moderate":
            return self._create_moderate_agent(config)
        else:  # complex
            return self._create_complex_agent(config)

    def _create_simple_agent(self, config: dict):
        """Simple agent for basic queries."""

        return create_deep_agent(
            tools=get_tools_for_complexity("simple", config),
            system_prompt=get_system_prompt("simple"),
            model="anthropic:claude-haiku",
            planning=False,
            filesystem=False,
            store=config["store"]
        )

    def _create_moderate_agent(self, config: dict):
        """Moderate agent with planning."""

        return create_deep_agent(
            tools=get_tools_for_complexity("moderate", config),
            system_prompt=get_system_prompt("moderate"),
            model="anthropic:claude-sonnet",
            planning=True,
            interrupt_on=["write_todos"],  # Human approval
            filesystem=False,
            store=config["store"]
        )

    def _create_complex_agent(self, config: dict):
        """Complex agent with full Deep Agents capabilities."""

        return create_deep_agent(
            tools=get_tools_for_complexity("complex", config),
            subagents=SUBAGENT_REGISTRY,
            system_prompt=get_system_prompt("complex"),
            model="anthropic:claude-sonnet-4",
            planning=True,
            interrupt_on=["write_todos"],
            filesystem=True,
            store=config["store"]
        )

    def _get_user_store(self, user_id: str) -> InMemoryStore:
        """Get or create user's memory store."""

        if user_id not in self.user_stores:
            self.user_stores[user_id] = InMemoryStore()
        return self.user_stores[user_id]
```

---

## 3. Tool Specifications

### Base Tools (All Agents)

```python
# app/agents/tools/semantic_search.py

from typing import List, Dict, Any
from pydantic import BaseModel, Field

class SemanticSearchInput(BaseModel):
    """Input for semantic search tool."""
    query: str = Field(description="The search query")
    n_results: int = Field(default=10, description="Number of results to return")
    filters: Dict[str, Any] = Field(default={}, description="Additional filters")

class SemanticSearchTool:
    """Tool for searching documents with permission filtering."""

    name = "semantic_search"
    description = """Search through accessible documents using semantic similarity.

This tool finds relevant passages from documents that match your query.
Results are automatically filtered based on user's permissions.

Use this tool when you need to:
- Find information across multiple documents
- Locate specific facts or procedures
- Get relevant context for answering questions

The tool returns:
- Matching text passages
- Source document names and page numbers
- Relevance scores"""

    def __init__(self, user_id: str, accessible_documents: List[str], vector_db):
        self.user_id = user_id
        self.accessible_documents = accessible_documents
        self.vector_db = vector_db

    async def run(self, query: str, n_results: int = 10) -> List[Dict]:
        """Execute semantic search."""

        # Generate query embedding
        from app.services.embeddings import EmbeddingService
        embedding_service = EmbeddingService()
        query_embedding = await embedding_service.embed_query(query)

        # Search with permission filter
        results = await self.vector_db.query(
            query_embedding=query_embedding,
            n_results=n_results,
            filter={
                "document_id": {"$in": self.accessible_documents}
            }
        )

        # Format results
        formatted_results = []
        for result in results:
            formatted_results.append({
                "content": result.content,
                "document_id": result.metadata["document_id"],
                "document_title": result.metadata["document_title"],
                "page_number": result.metadata.get("page_number"),
                "relevance_score": result.score,
                "citation": f"{result.metadata['document_title']}, p.{result.metadata.get('page_number', 'N/A')}"
            })

        return formatted_results
```

---

### Moderate Complexity Tools

```python
# app/agents/tools/extract_data.py

class ExtractDataTool:
    """Tool for extracting structured data from documents."""

    name = "extract_data"
    description = """Extract structured data from document passages.

Use this tool to:
- Pull out specific data points (dates, numbers, names)
- Create structured summaries of sections
- Extract tables or lists

Input: Document passage and extraction template
Output: Structured JSON data"""

    async def run(
        self,
        content: str,
        extraction_template: Dict[str, str]
    ) -> Dict[str, Any]:
        """Extract structured data from content."""

        from anthropic import Anthropic
        client = Anthropic()

        prompt = f"""Extract the following information from this text:

{extraction_template}

Text:
{content}

Return as JSON matching the template structure."""

        response = client.messages.create(
            model="claude-haiku",
            max_tokens=2000,
            messages=[{"role": "user", "content": prompt}]
        )

        import json
        return json.loads(response.content[0].text)
```

---

### Complex Tools

```python
# app/agents/tools/pdf_extraction.py

class PDFTableExtractionTool:
    """Tool for extracting tables from PDF documents."""

    name = "extract_pdf_tables"
    description = """Extract tables and tabular data from PDF documents.

Use for:
- Financial reports with data tables
- Technical specifications with structured info
- Any PDF containing tables

Returns: List of tables as structured data (pandas DataFrames)"""

    async def run(self, document_id: str, page_numbers: List[int] = None) -> List[Dict]:
        """Extract tables from PDF."""

        import tabula
        from app.services.document_storage import DocumentStorageService

        storage = DocumentStorageService()
        pdf_path = await storage.get_document_path(document_id)

        # Extract tables
        if page_numbers:
            tables = tabula.read_pdf(
                pdf_path,
                pages=page_numbers,
                multiple_tables=True
            )
        else:
            tables = tabula.read_pdf(pdf_path, pages="all", multiple_tables=True)

        # Convert to JSON-serializable format
        results = []
        for i, table in enumerate(tables):
            results.append({
                "table_index": i,
                "headers": table.columns.tolist(),
                "rows": table.values.tolist(),
                "shape": table.shape,
                "data": table.to_dict(orient="records")
            })

        return results


# app/agents/tools/chart_generation.py

class ChartSpecGenerationTool:
    """Tool for generating chart specifications."""

    name = "generate_chart_spec"
    description = """Generate professional chart specifications for visualization.

Use for:
- Creating line charts for trends
- Bar charts for comparisons
- Tables for structured data display

Input: Data and chart requirements
Output: JSON spec for frontend rendering (Recharts format)"""

    async def run(
        self,
        data: Dict[str, Any],
        chart_type: str,
        title: str,
        description: str = None
    ) -> Dict:
        """Generate chart specification."""

        spec = {
            "type": chart_type,  # "line", "bar", "pie", "table"
            "title": title,
            "description": description,
            "data": data,
            "config": self._get_default_config(chart_type)
        }

        return spec

    def _get_default_config(self, chart_type: str) -> Dict:
        """Get default configuration for chart type."""

        configs = {
            "line": {
                "xAxis": {"type": "category"},
                "yAxis": {"type": "value"},
                "colors": ["#3B82F6", "#10B981", "#F59E0B"],
                "smooth": True
            },
            "bar": {
                "xAxis": {"type": "category"},
                "yAxis": {"type": "value"},
                "colors": ["#3B82F6"]
            },
            "table": {
                "striped": True,
                "bordered": True,
                "hover": True
            }
        }

        return configs.get(chart_type, {})
```

---

### Tool Registry

```python
# app/agents/tools/__init__.py

from typing import List
from app.agents.tools.semantic_search import SemanticSearchTool
from app.agents.tools.extract_data import ExtractDataTool
from app.agents.tools.pdf_extraction import PDFTableExtractionTool
from app.agents.tools.chart_generation import ChartSpecGenerationTool

def get_tools_for_complexity(complexity: str, config: dict) -> List:
    """Get appropriate tools for complexity level."""

    # Base tools (all agents)
    semantic_search = SemanticSearchTool(
        user_id=config["user_id"],
        accessible_documents=config["accessible_documents"],
        vector_db=config.get("vector_db")
    )

    if complexity == "simple":
        return [semantic_search]

    elif complexity == "moderate":
        extract_data = ExtractDataTool()
        return [semantic_search, extract_data]

    else:  # complex
        extract_data = ExtractDataTool()
        extract_tables = PDFTableExtractionTool()
        generate_charts = ChartSpecGenerationTool()

        return [
            semantic_search,
            extract_data,
            extract_tables,
            generate_charts
        ]
```

---

## 4. Subagent Definitions

### PDF Extraction Subagent

```python
# app/agents/subagents/pdf_extraction.py

PDF_EXTRACTION_SUBAGENT = {
    "name": "pdf-extraction-agent",
    "description": "Specialized agent for extracting data from PDF documents",

    "tools": [
        "extract_pdf_tables",
        "extract_pdf_text_by_section",
        "parse_financial_numbers"
    ],

    "system_prompt": """You are a specialized data extraction agent for PDF documents.

Your expertise:
- Identifying document structure (sections, headings, tables)
- Extracting tabular data with high accuracy
- Parsing financial numbers and dates correctly
- Handling multi-page tables
- Preserving data relationships and context

When extracting data:
1. Identify the document type (quarterly report, technical doc, etc.)
2. Locate relevant sections based on the task
3. Extract tables using appropriate tools
4. Parse and validate numbers (handle $, %, M, K suffixes)
5. Maintain source references (page numbers)
6. Return structured JSON output

Quality standards:
- Preserve exact numbers (no rounding unless specified)
- Include units and currencies
- Note any ambiguities or unclear data
- Cite page numbers for all extracted data

Example output format:
{
    "document_id": "uuid",
    "document_title": "Q1 2023 Financial Report",
    "extraction_date": "2024-01-20",
    "data": {
        "revenue": {"value": 125.5, "unit": "M", "currency": "USD", "page": 12},
        "expenses": {"value": 98.3, "unit": "M", "currency": "USD", "page": 13}
    },
    "tables": [...],
    "notes": ["Revenue includes one-time gain from asset sale"]
}"""
}
```

---

### Trend Analysis Subagent

```python
# app/agents/subagents/trend_analysis.py

TREND_ANALYSIS_SUBAGENT = {
    "name": "trend-analysis-agent",
    "description": "Specialized agent for analyzing trends and patterns in data",

    "tools": [
        "calculate_growth_rates",
        "detect_patterns",
        "statistical_analysis",
        "compare_periods"
    ],

    "system_prompt": """You are a specialized trend analysis agent.

Your expertise:
- Time series analysis
- Growth rate calculations (QoQ, YoY)
- Pattern detection (seasonal, cyclical, trending)
- Comparative analysis across periods
- Statistical significance testing
- Anomaly detection

Analysis methodology:
1. Validate input data completeness
2. Calculate key metrics (growth rates, averages, volatility)
3. Identify trends (increasing, decreasing, stable, volatile)
4. Detect patterns and seasonality
5. Flag significant changes or anomalies
6. Provide statistical context (confidence levels)

Metrics to calculate:
- Period-over-period change (absolute and percentage)
- Compound growth rates (CAGR)
- Moving averages
- Volatility measures
- Correlation between metrics

Output format:
{
    "metric": "revenue",
    "period": "Q1 2023 - Q4 2024",
    "trend": "increasing",
    "growth_rate_avg": 8.5,
    "growth_rate_range": [5.2, 12.3],
    "pattern": "strong upward trend with Q4 seasonality",
    "anomalies": [
        {"period": "Q2 2024", "value": 155.2, "expected": 142.1, "significance": "2.3 std dev"}
    ],
    "key_insights": [
        "Revenue grew 42% YoY",
        "Q4 consistently shows 15-20% seasonal increase",
        "Q2 2024 showed unusual spike, investigate further"
    ]
}"""
}
```

---

### Chart Generation Subagent

```python
# app/agents/subagents/chart_generation.py

CHART_GENERATION_SUBAGENT = {
    "name": "chart-generation-agent",
    "description": "Specialized agent for creating professional chart specifications",

    "tools": [
        "generate_line_chart",
        "generate_bar_chart",
        "generate_table",
        "format_chart_data"
    ],

    "system_prompt": """You are a specialized data visualization agent.

Your expertise:
- Choosing appropriate chart types for data
- Creating clear, professional visualizations
- Following data visualization best practices
- Formatting numbers and labels properly
- Applying professional color schemes
- Ensuring accessibility

Chart selection guidelines:
- **Line charts**: Time series, trends over time
- **Bar charts**: Comparisons across categories
- **Stacked bar charts**: Part-to-whole over categories
- **Tables**: Exact numbers, detailed data
- **Combination charts**: Multiple metrics with different scales

Design principles:
1. **Clarity**: Clear title, labeled axes, legend when needed
2. **Accuracy**: Appropriate scales, no misleading visualizations
3. **Professional**: Consistent colors, clean layout
4. **Accessible**: Good contrast, colorblind-safe palettes
5. **Context**: Include units, currencies, sources

Number formatting:
- Currency: $125.5M (not $125500000)
- Percentages: 15.5% (one decimal place)
- Large numbers: 1.2M, 3.5B
- Dates: Q1 2023, Jan 2024

Color palette (primary):
- Blue: #3B82F6 (primary metric)
- Green: #10B981 (positive/growth)
- Orange: #F59E0B (secondary metric)
- Red: #EF4444 (negative/decline)

Output format:
{
    "type": "line",
    "title": "Revenue Trend: Q1 2023 - Q4 2024",
    "subtitle": "Year-over-year comparison",
    "data": {
        "labels": ["Q1", "Q2", "Q3", "Q4"],
        "datasets": [
            {
                "label": "2023",
                "data": [125.5, 132.1, 128.9, 145.2],
                "color": "#3B82F6"
            },
            {
                "label": "2024",
                "data": [138.7, 155.2, 148.3, 167.8],
                "color": "#10B981"
            }
        ]
    },
    "xAxis": {"label": "Quarter"},
    "yAxis": {"label": "Revenue ($M)"},
    "legend": {"position": "top-right"},
    "notes": ["Source: Quarterly Financial Reports"]
}"""
}
```

---

### Report Synthesis Subagent

```python
# app/agents/subagents/report_synthesis.py

REPORT_SYNTHESIS_SUBAGENT = {
    "name": "report-synthesis-agent",
    "description": "Specialized agent for synthesizing findings into executive reports",

    "tools": [
        "format_markdown",
        "create_executive_summary",
        "cite_sources",
        "structure_report"
    ],

    "system_prompt": """You are a specialized report writing agent.

Your expertise:
- Writing like a senior analyst at a top consulting firm
- Creating clear, concise executive summaries
- Structuring complex information logically
- Supporting claims with data and citations
- Professional business writing

Report structure:
1. **Executive Summary** (2-3 key sentences)
   - Most important findings first
   - Quantify impact when possible
   - Actionable insights

2. **Key Findings** (3-5 main points)
   - Each finding supported by data
   - Include relevant visualizations
   - Cite specific sources

3. **Detailed Analysis**
   - Organized by theme or time period
   - Tables and charts embedded where relevant
   - Clear headings and subheadings

4. **Insights & Recommendations**
   - Based on evidence from analysis
   - Prioritized by impact
   - Actionable and specific

5. **Appendix** (if needed)
   - Detailed tables
   - Methodology notes
   - Data sources

Writing style:
- **Concise**: Short sentences, active voice
- **Precise**: Specific numbers, avoid vague terms
- **Professional**: Formal but readable
- **Evidence-based**: Every claim cited

Citation format:
"Revenue increased 42% YoY (Q4 2023 Financial Report, p.12)"

Example executive summary:
## Executive Summary

Our financial performance in 2024 showed strong growth across all key metrics. Revenue increased 42% YoY to $167.8M, driven primarily by Q2 and Q4 performance. Operating margins improved from 18% to 22%, indicating successful cost management initiatives. However, Q2 2024 showed an unusual 17.5% spike that requires further investigation.

Output: Well-structured markdown document with embedded charts and proper citations."""
}
```

---

### Subagent Registry

```python
# app/agents/subagents/__init__.py

from app.agents.subagents.pdf_extraction import PDF_EXTRACTION_SUBAGENT
from app.agents.subagents.trend_analysis import TREND_ANALYSIS_SUBAGENT
from app.agents.subagents.chart_generation import CHART_GENERATION_SUBAGENT
from app.agents.subagents.report_synthesis import REPORT_SYNTHESIS_SUBAGENT

SUBAGENT_REGISTRY = [
    PDF_EXTRACTION_SUBAGENT,
    TREND_ANALYSIS_SUBAGENT,
    CHART_GENERATION_SUBAGENT,
    REPORT_SYNTHESIS_SUBAGENT
]
```

---

## 5. System Prompts

```python
# app/agents/prompts.py

def get_system_prompt(complexity: str) -> str:
    """Get system prompt for agent complexity level."""

    prompts = {
        "simple": SIMPLE_AGENT_PROMPT,
        "moderate": MODERATE_AGENT_PROMPT,
        "complex": COMPLEX_AGENT_PROMPT
    }

    return prompts.get(complexity, MODERATE_AGENT_PROMPT)


SIMPLE_AGENT_PROMPT = """You are a helpful documentation assistant.

Your role:
- Answer user questions from documentation quickly and accurately
- Search relevant documents using semantic search
- Provide concise, direct answers
- Always cite your sources with document name and page number

Response format:
1. Direct answer to the question (2-3 sentences)
2. Supporting details if needed
3. Source citations in format: (Document Name, p.XX)

If you cannot find the answer:
- Say so clearly
- Suggest related topics if available
- Do not make up information

Example:
User: "How do I install System A on Ubuntu?"

Answer: "To install System A on Ubuntu, first update your package lists with `sudo apt-get update`, then install with `sudo apt-get install system-a`. The service will start automatically after installation (System A Installation Guide, p.12)."
"""


MODERATE_AGENT_PROMPT = """You are an expert documentation analyst.

Your capabilities:
- Multi-document analysis and synthesis
- Comparing information across sources
- Creating structured summaries
- Extracting and organizing complex information

Workflow:
1. **Plan your approach** using write_todos
   - Break down complex questions into steps
   - Identify which documents to search
   - Plan synthesis strategy

2. **Execute research**
   - Search relevant documents
   - Extract key information
   - Compare and contrast sources

3. **Synthesize answer**
   - Organize information logically
   - Provide clear, structured response
   - Include all relevant citations

Response structure:
- Use headings for organization
- Bullet points for lists
- Code blocks for technical content
- Tables for comparisons
- Always cite sources: (Document Name, p.XX)

Quality standards:
- Accurate: Verify all facts
- Complete: Address all aspects of question
- Clear: Well-organized and easy to understand
- Cited: Every claim has a source

Example plan for "Compare System A v1 vs v2 installation":
1. Find System A v1 installation documentation
2. Find System A v2 installation documentation
3. Extract key steps from each
4. Identify differences
5. Create comparison table
6. Summarize key changes
"""


COMPLEX_AGENT_PROMPT = """You are a senior analyst with advanced research and reporting capabilities.

Your expertise:
- Complex multi-document analysis
- Data extraction and trend analysis
- Professional report generation
- Chart and visualization creation

Capabilities:
- **Planning**: Break complex tasks into manageable steps
- **Delegation**: Spawn specialized subagents for specific tasks
- **Filesystem**: Store intermediate results for large analyses
- **Synthesis**: Combine findings into professional outputs

Available subagents:
1. **pdf-extraction-agent**: Extract tables and data from PDFs
2. **trend-analysis-agent**: Analyze trends and patterns
3. **chart-generation-agent**: Create professional visualizations
4. **report-synthesis-agent**: Write executive-quality reports

Workflow for complex analysis:

1. **Planning Phase**
   - Create detailed execution plan with write_todos
   - Identify required documents and data
   - Determine which subagents to use
   - Estimate scope and complexity

2. **Data Extraction Phase**
   - Spawn pdf-extraction-agent for each source document
   - Store extracted data in filesystem (JSON files)
   - Validate data completeness

3. **Analysis Phase**
   - Read extracted data from filesystem
   - Spawn trend-analysis-agent with consolidated data
   - Calculate metrics, identify patterns
   - Store analysis results

4. **Visualization Phase**
   - Spawn chart-generation-agent for key findings
   - Create line charts for trends
   - Create bar charts for comparisons
   - Create tables for detailed data

5. **Synthesis Phase**
   - Spawn report-synthesis-agent with all findings
   - Generate executive summary
   - Structure detailed analysis
   - Include visualizations and citations

6. **Quality Assurance**
   - Verify all numbers are accurate
   - Ensure all claims are cited
   - Check visualizations are clear
   - Review for completeness

File naming conventions:
- `extracted_data_{document_id}.json` - Extracted document data
- `trend_analysis_{metric}.json` - Trend analysis results
- `chart_specs.json` - All chart specifications
- `final_report.md` - Synthesized report

Example: Financial Analysis Task
User: "Analyze our financial performance over the past 2 years"

Plan:
1. Identify all quarterly reports (2023-2024)
2. Extract financial data from each quarter using pdf-extraction-agent
3. Store extracted data in filesystem
4. Analyze trends using trend-analysis-agent
5. Generate visualizations with chart-generation-agent
6. Synthesize executive report with report-synthesis-agent
7. Present comprehensive analysis with charts and insights

Quality standards:
- **Accurate**: All numbers verified against sources
- **Professional**: Analyst-quality output
- **Comprehensive**: Address all aspects
- **Actionable**: Provide insights and recommendations
- **Well-cited**: Every claim has source reference
"""
```

---

## 6. Integration with Backend

### FastAPI Endpoint Integration

```python
# app/api/v1/endpoints/messages.py

from fastapi import APIRouter, Depends, HTTPException
from app.agents.agent_factory import DocumentQAAgentFactory
from app.models.user import User
from app.services.permissions import get_user_accessible_documents
from app.core.websocket import WebSocketManager

router = APIRouter()
agent_factory = DocumentQAAgentFactory()

@router.post("/conversations/{conversation_id}/messages")
async def create_message(
    conversation_id: str,
    message_request: MessageCreate,
    current_user: User = Depends(get_current_user),
    websocket: WebSocketManager = Depends(get_websocket_manager)
):
    """Send a message (ask a question)."""

    # Get conversation and validate ownership
    conversation = await get_conversation(conversation_id)
    if conversation.user_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not your conversation")

    # Get accessible documents
    accessible_docs = await get_user_accessible_documents(
        user=current_user,
        system_filters=conversation.system_filters
    )

    # Create agent factory for this user
    create_agent = agent_factory.create_agent(
        user=current_user,
        accessible_documents=[d.id for d in accessible_docs],
        system_filters=conversation.system_filters,
        websocket=websocket
    )

    # Create user message
    user_message = await create_message_in_db(
        conversation_id=conversation_id,
        role="user",
        content=message_request.content
    )

    # Get conversation history
    conversation_history = await get_conversation_messages(conversation_id)

    # Create agent for this specific query
    agent = create_agent(
        question=message_request.content,
        conversation_history=conversation_history
    )

    # Create agent execution record
    execution = await create_agent_execution(
        conversation_id=conversation_id,
        agent_type=agent.agent_type,
        model_name=agent.model_name
    )

    # Execute agent asynchronously
    from app.tasks.agent_execution import execute_agent_task
    task = execute_agent_task.delay(
        execution_id=execution.id,
        agent_config=agent.config,
        question=message_request.content
    )

    # Return immediately
    return {
        "message": user_message,
        "agent_execution": {
            "id": execution.id,
            "status": "running",
            "agent_type": agent.agent_type,
            "model_name": agent.model_name,
            "started_at": execution.started_at
        },
        "websocket_channel": f"execution:{execution.id}"
    }
```

---

### Celery Task for Agent Execution

```python
# app/tasks/agent_execution.py

from celery import Celery
from app.agents.agent_factory import DocumentQAAgentFactory
from app.core.database import get_db
from app.core.websocket import WebSocketManager

celery_app = Celery("ask_my_docs")

@celery_app.task
async def execute_agent_task(
    execution_id: str,
    agent_config: dict,
    question: str
):
    """Execute agent and handle results."""

    db = get_db()
    ws = WebSocketManager()

    try:
        # Notify start
        await ws.send_to_channel(
            channel=f"execution:{execution_id}",
            message={
                "type": "agent.execution.started",
                "data": {"execution_id": execution_id, "status": "running"}
            }
        )

        # Execute agent
        # (Implementation of agent execution with event streaming)

        # On completion, create assistant message
        assistant_message = await create_message_in_db(
            conversation_id=agent_config["conversation_id"],
            role="assistant",
            content=result.content,
            rich_content=result.rich_content,
            agent_execution_id=execution_id
        )

        # Notify completion
        await ws.send_to_channel(
            channel=f"execution:{execution_id}",
            message={
                "type": "agent.execution.completed",
                "data": {
                    "execution_id": execution_id,
                    "message_id": assistant_message.id,
                    "status": "completed"
                }
            }
        )

    except Exception as e:
        # Handle errors
        await update_execution_status(execution_id, "failed", error=str(e))
        await ws.send_to_channel(
            channel=f"execution:{execution_id}",
            message={
                "type": "agent.execution.failed",
                "data": {"execution_id": execution_id, "error": str(e)}
            }
        )
```

---

## 7. Testing Strategy

### Unit Tests for Tools

```python
# tests/agents/tools/test_semantic_search.py

import pytest
from app.agents.tools.semantic_search import SemanticSearchTool

@pytest.mark.asyncio
async def test_semantic_search_basic():
    """Test basic semantic search."""

    tool = SemanticSearchTool(
        user_id="test-user",
        accessible_documents=["doc1", "doc2"],
        vector_db=mock_vector_db
    )

    results = await tool.run(
        query="How do I install System A?",
        n_results=5
    )

    assert len(results) <= 5
    assert all("citation" in r for r in results)
    assert all("relevance_score" in r for r in results)
```

---

### Integration Tests for Agents

```python
# tests/agents/test_agent_factory.py

import pytest
from app.agents.agent_factory import DocumentQAAgentFactory

@pytest.mark.asyncio
async def test_simple_agent_creation():
    """Test simple agent creation."""

    factory = DocumentQAAgentFactory()
    create_agent = factory.create_agent(
        user=test_user,
        accessible_documents=["doc1"],
        system_filters=["system-a"],
        force_complexity="simple"
    )

    agent = create_agent("What is System A?")
    assert agent.model_name == "claude-haiku"
    assert agent.planning == False
```

---

## Summary

This implementation provides:

✅ **Automatic complexity classification** for cost optimization
✅ **Factory pattern** for flexible agent creation
✅ **Comprehensive tool library** with permission filtering
✅ **Specialized subagents** for complex tasks
✅ **Professional system prompts** with clear guidelines
✅ **Full backend integration** with FastAPI and Celery
✅ **WebSocket event streaming** for real-time updates
✅ **Testing framework** for reliability

**Next Steps:**
1. Implement agent factory and tools
2. Create subagent implementations
3. Set up Celery task queue
4. Integrate WebSocket event streaming
5. Build frontend components for HITL
6. Test with real-world queries

---

**Last Updated**: 2025-11-15
**Status**: Complete implementation strategy
