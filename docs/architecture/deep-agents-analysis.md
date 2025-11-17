# Deep Agents Analysis for Ask My Docs

## What are Deep Agents?

**Deep Agents** is a LangChain framework built on top of LangGraph that implements advanced agentic patterns for complex, multi-step tasks. It's not a replacement for LangGraph—it's an **enhancement** that adds sophisticated capabilities.

### Core Components

Deep Agents provide 4 key architectural enhancements:

1. **Planning Tool** (`write_todos`)
   - Break complex tasks into discrete steps
   - Adaptive planning that updates as agent learns
   - Keeps agent on track across long-running tasks

2. **Filesystem Backend**
   - File operations: `ls`, `read_file`, `write_file`, `edit_file`
   - Context management: Offload large results to prevent context overflow
   - Shared workspace for memory across execution

3. **Subagent Spawning**
   - Delegate specialized subtasks to focused agents
   - Context isolation (each subagent has clean slate)
   - Composable: Can use pre-built LangGraph graphs as subagents

4. **Detailed System Prompts**
   - Long, comprehensive instructions with examples
   - Critical for guiding behavior on complex tasks

### How It Differs from Basic LangGraph

| Aspect | Basic LangGraph | Deep Agents |
|--------|-----------------|-------------|
| **Complexity** | Simple tool-calling loops | Multi-step planning & execution |
| **Context Management** | All in memory (limited) | Filesystem for offloading |
| **Task Decomposition** | Manual in state machine | Built-in planning tool |
| **Specialization** | Single agent | Spawnable subagents |
| **Use Cases** | Simple Q&A, linear workflows | Research, coding, complex analysis |
| **HITL** | Manual interrupts | Built-in `interrupt_on` |

**Key Insight**: Deep Agents is **middleware on top of LangGraph**. It's still a LangGraph graph underneath!

---

## Perfect Fit for Our Project? ✅ YES!

### Why Deep Agents is IDEAL for Ask My Docs:

#### 1. **Planning Tool** → Human-in-the-Loop
```python
# Our design already included "Planning Phase (Human reviews plan)"
# Deep Agents provides this out of the box!

agent = create_deep_agent(
    interrupt_on=["write_todos"],  # Pause after planning
    # ... other config
)

# User sees plan:
# ✓ 1. Extract financial data from Q1-Q4 2023
# ✓ 2. Extract financial data from Q1-Q4 2024
# ✓ 3. Calculate YoY growth rates
# ✓ 4. Identify trends and anomalies
# ✓ 5. Generate visualizations
# ✓ 6. Write executive summary

# User approves → Agent executes
```

#### 2. **Filesystem** → Context Management for Large Documents
```python
# Problem: 8 quarterly reports × 50 pages = 400 pages
# Can't fit in context window!

# Solution: Deep Agents filesystem
agent.write_file("q1_2023_data.json", extracted_data)
agent.write_file("q2_2023_data.json", extracted_data)
# ... process all quarters

# Later: Read back for synthesis
all_data = [
    agent.read_file("q1_2023_data.json"),
    agent.read_file("q2_2023_data.json"),
    # ...
]
```

#### 3. **Subagents** → Specialized Analysis
```python
# Our design mentioned "Agent Tools"
# Deep Agents lets us create specialized subagents!

subagents = [
    {
        "name": "pdf-extraction-agent",
        "description": "Extract tables and numbers from PDF quarterly reports",
        "tools": [extract_pdf_tables, parse_financial_numbers],
        "system_prompt": "You are a data extraction specialist..."
    },
    {
        "name": "trend-analysis-agent",
        "description": "Analyze financial trends across quarters",
        "tools": [calculate_growth, detect_patterns, statistical_analysis],
        "system_prompt": "You are a financial analyst specializing in trend analysis..."
    },
    {
        "name": "chart-generation-agent",
        "description": "Create professional chart specifications",
        "tools": [generate_chart_spec, format_chart_data],
        "system_prompt": "You create analyst-quality visualizations..."
    },
    {
        "name": "report-synthesis-agent",
        "description": "Synthesize findings into executive report",
        "tools": [format_markdown, create_executive_summary],
        "system_prompt": "You write like a senior financial analyst..."
    }
]

# Main agent delegates to specialists
# "For data extraction, spawn pdf-extraction-agent for each report"
# "For trend analysis, spawn trend-analysis-agent with all data"
```

#### 4. **Long-term Memory** → Session Persistence
```python
# Our requirement: "Documents uploaded once, queried many times"
# Deep Agents: Built-in persistent storage across threads!

from langgraph.store.memory import InMemoryStore

store = InMemoryStore()
agent = create_deep_agent(
    store=store,  # Persists across conversations
    # ...
)
```

---

## Mapping to Our Use Cases

### **Use Case 1: System Documentation Q&A**

**Simple Queries** → Basic mode (fast)
```python
# "How do I install System A on Linux?"
simple_agent = create_deep_agent(
    tools=[semantic_search],
    system_prompt="Answer questions from documentation concisely.",
    model="anthropic:claude-haiku"  # Fast & cheap
)
```

**Complex Queries** → Deep mode with planning
```python
# "Compare installation procedures across System A v1, v2, v3"
deep_agent = create_deep_agent(
    tools=[semantic_search, compare_documents],
    planning=True,
    model="anthropic:claude-sonnet"
)
```

### **Use Case 2: Instant Personal Upload**

**Contract Analysis** → Subagents for specialized tasks
```python
contract_agent = create_deep_agent(
    tools=[extract_text, semantic_search],
    subagents=[
        {
            "name": "legal-extraction-agent",
            "description": "Extract legal obligations and terms",
            "system_prompt": "You identify legal obligations, payment terms, liabilities..."
        },
        {
            "name": "risk-analysis-agent",
            "description": "Identify potential risks and red flags",
            "system_prompt": "You are a legal risk analyst..."
        }
    ]
)

# User: "What are the risks in this contract?"
# Agent: Plans → Extract terms → Analyze risks → Report
```

### **Use Case 3: Financial Analysis** ⭐ PERFECT FIT

**Full Deep Agents Workflow**:

```python
financial_agent = create_deep_agent(
    tools=[
        semantic_search_documents,
        extract_pdf_tables,
        calculate_financial_metrics,
        generate_chart_spec,
        write_file,  # Filesystem
        read_file
    ],
    subagents=[
        pdf_extraction_agent,
        trend_analysis_agent,
        chart_generation_agent,
        report_synthesis_agent
    ],
    system_prompt="""You are a senior financial analyst.

When analyzing quarterly reports:
1. Create a detailed plan using write_todos
2. Extract data from each quarter (delegate to pdf-extraction-agent)
3. Store extracted data in filesystem
4. Analyze trends (delegate to trend-analysis-agent)
5. Generate visualizations (delegate to chart-generation-agent)
6. Synthesize report (delegate to report-synthesis-agent)
7. Present for human review before finalizing
""",
    interrupt_on=["write_todos"],  # Human approves plan
    model="anthropic:claude-sonnet-4"
)

# Execution flow:
# 1. User: "Analyze our financial performance over 2 years"
# 2. Agent creates plan → PAUSES for human approval
# 3. User approves
# 4. Agent spawns pdf-extraction-agent for each report
# 5. Stores results in filesystem (q1_2023.json, q2_2023.json, ...)
# 6. Spawns trend-analysis-agent with all data
# 7. Spawns chart-generation-agent for visualizations
# 8. Spawns report-synthesis-agent for final report
# 9. Returns rich output with charts, tables, insights
```

---

## Implementation Strategy

### **Recommended Architecture**

```python
# Agent Router: Classify query complexity
def get_agent_for_query(question: str, system_filter: List[str]) -> Agent:
    """Route to appropriate agent based on query complexity."""

    complexity = classify_query_complexity(question)

    if complexity == "simple":
        # Fast, cheap agent for lookups
        return create_deep_agent(
            tools=[semantic_search],
            model="anthropic:claude-haiku",
            planning=False
        )

    elif complexity == "moderate":
        # Medium agent with planning
        return create_deep_agent(
            tools=[semantic_search, extract_data],
            model="anthropic:claude-sonnet",
            planning=True,
            interrupt_on=["write_todos"]
        )

    elif complexity == "complex":
        # Full deep agent with subagents
        return create_deep_agent(
            tools=[semantic_search, extract_tables, calculate_metrics],
            subagents=SPECIALIZED_SUBAGENTS,
            model="anthropic:claude-sonnet",
            planning=True,
            interrupt_on=["write_todos"],
            filesystem=True
        )


def classify_query_complexity(question: str) -> str:
    """Classify query complexity using LLM."""

    prompt = f"""Classify this query's complexity:

    Question: {question}

    Simple: Single fact lookup, short answer
    Moderate: Requires analyzing 2-3 documents, some synthesis
    Complex: Multi-document analysis, trends, comparisons, reports

    Return: simple, moderate, or complex"""

    return llm.invoke(prompt).strip().lower()
```

### **Updated Backend Architecture**

```python
# app/agents/deep_agent_factory.py
from deepagents import create_deep_agent
from typing import List

class DocumentQAAgentFactory:
    """Factory for creating appropriate agents."""

    @staticmethod
    def create_for_query(
        question: str,
        accessible_documents: List[str],
        user_id: str,
        websocket: WebSocket
    ) -> Agent:

        complexity = classify_query_complexity(question)

        # Create agent with appropriate configuration
        agent = create_deep_agent(
            tools=get_tools_for_complexity(complexity),
            subagents=get_subagents_for_complexity(complexity),
            system_prompt=get_system_prompt(complexity),
            model=get_model_for_complexity(complexity),
            planning=(complexity in ["moderate", "complex"]),
            interrupt_on=["write_todos"] if complexity == "complex" else None,
            filesystem=(complexity == "complex")
        )

        # Wrap with our custom logic for permission filtering, analytics, etc.
        return PermissionAwareAgent(
            agent=agent,
            user_id=user_id,
            accessible_documents=accessible_documents,
            websocket=websocket
        )
```

---

## Benefits for Our Project

### ✅ Advantages

1. **Already Designed For It**: Our use case technical design anticipated this pattern
2. **Human-in-the-Loop**: Built-in with `interrupt_on`
3. **Context Management**: Filesystem solves large document problem
4. **Specialization**: Subagents for extraction, analysis, synthesis
5. **Native LangGraph**: Compatible with all LangGraph features (streaming, memory, Studio)
6. **Cost-Effective**: Route simple queries to basic mode (Haiku), complex to deep mode (Sonnet)
7. **Scalable**: Add more subagents as needed
8. **Explainable**: Todo list shows users the plan

### ⚠️ Considerations

1. **Latency**: Complex queries with subagents will take longer (10-60 seconds)
   - **Solution**: Show progress, stream updates, set expectations

2. **Cost**: More LLM calls = higher cost
   - **Solution**: Route appropriately, use cheaper models where possible

3. **Complexity**: More moving parts to debug
   - **Solution**: LangGraph Studio for visualization, good logging

4. **Learning Curve**: Team needs to understand Deep Agents patterns
   - **Solution**: Start simple, add complexity incrementally

---

## Recommendation

### ✅ **USE DEEP AGENTS - Strongly Recommended**

**Why:**
1. Perfect match for our complex use cases (especially financial analysis)
2. Provides exactly the capabilities we need (planning, HITL, context management)
3. Built on LangGraph (not a replacement, an enhancement)
4. Cost-effective with hybrid approach (simple vs. complex routing)
5. Our design already anticipated this architecture

**Implementation Plan:**

### Phase 1 (MVP):
- Basic Deep Agent for simple queries (no subagents)
- Planning tool with human approval
- Test with Use Case 1 (System Documentation)

### Phase 2:
- Add filesystem for context management
- Implement subagents for Use Case 3 (Financial Analysis)
- Query complexity routing

### Phase 3:
- Optimize subagent specialization
- Add more sophisticated planning
- Fine-tune system prompts

---

## Code Example: Complete Implementation

```python
# app/agents/financial_analysis_agent.py
from deepagents import create_deep_agent
from typing import List, Dict, Any

# Define specialized subagents
PDF_EXTRACTION_SUBAGENT = {
    "name": "pdf-extraction-agent",
    "description": "Extract financial tables and data from PDF quarterly reports",
    "tools": [extract_pdf_tables, parse_financial_numbers, identify_sections],
    "system_prompt": """You are a data extraction specialist.

When given a quarterly financial report PDF:
1. Identify key sections (Income Statement, Balance Sheet, Cash Flow)
2. Extract tables with financial data
3. Parse numbers and dates carefully
4. Return structured JSON with all extracted data
5. Include source page numbers for citations

Be precise with numbers and maintain decimal places."""
}

TREND_ANALYSIS_SUBAGENT = {
    "name": "trend-analysis-agent",
    "description": "Analyze financial trends across multiple quarters",
    "tools": [calculate_growth_rates, detect_patterns, statistical_analysis],
    "system_prompt": """You are a financial analyst specializing in trend analysis.

When given financial data across quarters:
1. Calculate quarter-over-quarter growth rates
2. Calculate year-over-year comparisons
3. Identify trends (increasing, decreasing, stable)
4. Detect anomalies or significant changes
5. Provide statistical measures (averages, std dev, etc.)

Present findings clearly with supporting data."""
}

CHART_GENERATION_SUBAGENT = {
    "name": "chart-generation-agent",
    "description": "Generate professional chart specifications",
    "tools": [create_line_chart, create_bar_chart, create_table],
    "system_prompt": """You create professional, analyst-quality chart specifications.

When asked to visualize financial data:
1. Choose appropriate chart type (line for trends, bar for comparisons, etc.)
2. Use clear, descriptive labels
3. Format numbers with proper units ($M, %, etc.)
4. Use professional color schemes
5. Return JSON specifications for frontend rendering

Follow the chart spec format exactly."""
}

REPORT_SYNTHESIS_SUBAGENT = {
    "name": "report-synthesis-agent",
    "description": "Synthesize findings into executive report",
    "tools": [format_markdown, create_executive_summary, cite_sources],
    "system_prompt": """You write like a senior financial analyst at a top consulting firm.

When synthesizing financial analysis:
1. Start with executive summary (2-3 key sentences)
2. Present key findings with data support
3. Use professional language and structure
4. Include visualizations at appropriate points
5. Cite sources (document name, page number)
6. End with recommendations

Use markdown formatting for clarity."""
}

# Create the main financial analysis agent
def create_financial_analysis_agent(
    user_id: str,
    accessible_documents: List[str],
    websocket: WebSocket
) -> Agent:
    """Create a deep agent for financial analysis."""

    return create_deep_agent(
        tools=[
            semantic_search_documents,
            extract_pdf_tables,
            calculate_financial_metrics,
            generate_chart_spec,
            write_file,
            read_file,
            list_files
        ],
        subagents=[
            PDF_EXTRACTION_SUBAGENT,
            TREND_ANALYSIS_SUBAGENT,
            CHART_GENERATION_SUBAGENT,
            REPORT_SYNTHESIS_SUBAGENT
        ],
        system_prompt="""You are a senior financial analyst conducting multi-quarter analysis.

When analyzing quarterly financial reports:

1. **Planning**: Create detailed plan using write_todos
   - Break down: data extraction, trend analysis, visualization, synthesis
   - Estimate which quarters need analysis

2. **Data Extraction**:
   - Spawn pdf-extraction-agent for each quarterly report
   - Store extracted data in filesystem (q1_2023.json, q2_2023.json, etc.)

3. **Trend Analysis**:
   - Read all extracted data from filesystem
   - Spawn trend-analysis-agent with consolidated data
   - Store trend analysis results

4. **Visualization**:
   - Spawn chart-generation-agent for key metrics
   - Request line charts for trends, bar charts for comparisons

5. **Report Synthesis**:
   - Spawn report-synthesis-agent with all findings
   - Generate professional executive report

6. **Quality Check**:
   - Verify all claims have source citations
   - Ensure numbers are accurate
   - Check visualizations are clear

Always maintain professional, analyst-quality output.""",

        interrupt_on=["write_todos"],  # Pause after planning for human approval

        model="anthropic:claude-sonnet-4",  # Best model for complex analysis

        store=get_user_store(user_id),  # Persistent memory

        # Custom config for our use case
        config={
            "accessible_documents": accessible_documents,
            "user_id": user_id,
            "websocket": websocket
        }
    )


# Usage in our API
@router.post("/messages")
async def create_message(
    message_request: MessageCreate,
    current_user: User = Depends(get_current_user),
    websocket: WebSocket = Depends(get_websocket)
):
    # Get accessible documents (permission filtered)
    accessible_docs = get_user_accessible_documents(
        current_user,
        systems=message_request.system_filters
    )

    # Classify query complexity
    complexity = classify_query_complexity(message_request.content)

    if complexity == "complex":
        # Use deep agent for complex financial analysis
        agent = create_financial_analysis_agent(
            user_id=current_user.id,
            accessible_documents=[d.id for d in accessible_docs],
            websocket=websocket
        )
    else:
        # Use simple agent for basic queries
        agent = create_simple_qa_agent(...)

    # Execute agent
    response = await agent.ainvoke({
        "messages": [{"role": "user", "content": message_request.content}]
    })

    # Save and return (as before)
    # ...
```

---

## Next Steps

1. ✅ **Approve Deep Agents approach**
2. Update technical design to use Deep Agents architecture
3. Design database schema with filesystem/memory considerations
4. Implement MVP with basic Deep Agent
5. Add subagents incrementally
6. Test with real quarterly reports

---

**Decision: Should we proceed with Deep Agents?**

I strongly recommend **YES** - it's a perfect fit for our use cases and provides exactly the capabilities we need!
