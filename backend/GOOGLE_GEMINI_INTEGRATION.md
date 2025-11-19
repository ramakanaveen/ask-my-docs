# Google Gemini + LangChain Integration Guide

## Overview

Ask My Docs now uses **Google Gemini** as the primary LLM provider via **LangChain**, providing:
- State-of-the-art reasoning with Gemini 2.5 Pro
- Fast responses with Gemini 2.0 Flash
- Native embeddings with Google's embedding model
- Clean LangChain abstractions for all LLM operations

---

## Quick Start

### 1. Install Dependencies

```bash
cd backend
pip install langchain-google-genai google-generativeai
```

Dependencies are already added to `pyproject.toml`:
- `langchain-google-genai = "^1.0.0"`
- `google-generativeai = "^0.3.0"`

### 2. Get Google API Key

Get your API key from: https://makersuite.google.com/app/apikey

### 3. Update .env File

```bash
# Primary LLM Provider
GOOGLE_API_KEY=your-google-api-key-here
LLM_PROVIDER=google

# Model Selection
DEFAULT_MODEL=gemini-2.5-pro
SIMPLE_QUERY_MODEL=gemini-2.0-flash
COMPLEX_QUERY_MODEL=gemini-2.5-pro
EMBEDDING_MODEL=models/embedding-001
EMBEDDING_PROVIDER=google
```

---

## Usage Examples

### Basic LLM Service

```python
from app.services.llm_service import get_llm_service

# Get service instance
llm_service = get_llm_service()

# Simple generation
response = await llm_service.generate(
    prompt="What is machine learning?",
    system_message="You are a helpful AI assistant."
)
print(response)

# Streaming generation
async for chunk in llm_service.generate_streaming(
    prompt="Explain quantum computing in simple terms",
    system_message="You are a physics teacher."
):
    print(chunk, end="", flush=True)

# Chat with conversation history
messages = [
    {"role": "system", "content": "You are a helpful assistant."},
    {"role": "user", "content": "What is Python?"},
    {"role": "assistant", "content": "Python is a programming language."},
    {"role": "user", "content": "Tell me more about it."}
]
response = await llm_service.chat(messages)
print(response)
```

### Direct LangChain Usage

```python
from langchain_google_genai import ChatGoogleGenerativeAI

# Direct LangChain API (as shown in your example)
llm = ChatGoogleGenerativeAI(model="gemini-2.5-pro")
response = llm.invoke("Sing a ballad of LangChain.")
print(response.content)

# With message history
from langchain_core.messages import HumanMessage, SystemMessage

messages = [
    SystemMessage(content="You are a poet."),
    HumanMessage(content="Write a haiku about AI.")
]
response = llm.invoke(messages)
print(response.content)

# Streaming
for chunk in llm.stream("Tell me a story"):
    print(chunk.content, end="", flush=True)
```

### Embedding Service

```python
from app.services.embedding_service import get_embedding_service

embedding_service = get_embedding_service()

# Embed single text
vector = await embedding_service.embed_text("Hello world")
print(f"Vector dimension: {len(vector)}")  # 768 for Google embeddings

# Embed multiple texts (batched)
texts = ["Document 1", "Document 2", "Document 3"]
vectors = await embedding_service.embed_texts(texts)
print(f"Generated {len(vectors)} embeddings")

# Embed document chunk and store in PGVector
from app.models.document import DocumentChunk

chunk = DocumentChunk(content="Sample document text...")
chunk = await embedding_service.embed_document_chunk(db, chunk)
print(f"Embedded at: {chunk.embedded_at}")

# Similarity search with PGVector
results = await embedding_service.similarity_search_async(
    db=db,
    query="machine learning",
    limit=5,
    system_id=system_id
)

for chunk, score in results:
    print(f"Score: {score:.4f}")
    print(f"Content: {chunk.content[:200]}...")
    print()
```

### Query Complexity Classification

```python
from app.services.llm_service import get_llm_service

llm_service = get_llm_service()

# Classify query complexity
queries = [
    "What is the capital of France?",  # simple
    "Compare Python and JavaScript",  # moderate
    "Analyze the financial trends and create a strategic plan"  # complex
]

for query in queries:
    complexity = await llm_service.classify_query_complexity(query)
    print(f"Query: {query}")
    print(f"Complexity: {complexity}\n")
```

### Get Model for Specific Complexity

```python
from app.services.llm_service import get_llm_service

llm_service = get_llm_service()

# Get simple model (gemini-2.0-flash)
simple_llm = llm_service.get_simple_llm()
response = simple_llm.invoke("What is 2+2?")

# Get complex model (gemini-2.5-pro)
complex_llm = llm_service.get_complex_llm()
response = complex_llm.invoke("Analyze the implications of AI on society")

# Custom model and parameters
custom_llm = llm_service.get_llm(
    model="gemini-2.5-pro",
    temperature=0.9,  # Higher creativity
    max_tokens=2000
)
```

---

## Integration with HITL Workflow

### Example: Message Creation with Agent

```python
from app.services.llm_service import get_llm_service
from app.services.agent_execution_service import AgentExecutionService
from app.core.websocket import ws_manager

async def create_message_with_hitl(
    conversation_id: str,
    user_query: str,
    db: Session,
    current_user: User
):
    """Create message and execute agent with HITL support."""

    llm_service = get_llm_service()
    agent_service = AgentExecutionService(db, ws_manager)

    # 1. Classify query complexity
    complexity = await llm_service.classify_query_complexity(user_query)
    print(f"Query complexity: {complexity}")

    # 2. Create agent execution
    execution = agent_service.create_execution(
        conversation_id=conversation_id,
        agent_type=complexity,
        model_name=llm_service.settings.DEFAULT_MODEL,
        planning_enabled=(complexity == "complex"),  # HITL for complex only
        filesystem_enabled=(complexity in ["moderate", "complex"])
    )

    # 3. If complex, generate plan and pause for approval
    if complexity == "complex":
        # Generate plan using LLM
        plan_prompt = f"""Create an execution plan for this query: {user_query}

Break it down into specific steps (todos). Format as JSON:
{{
  "todos": [
    {{"content": "Step 1", "activeForm": "Doing step 1"}},
    {{"content": "Step 2", "activeForm": "Doing step 2"}}
  ]
}}"""

        plan_json = await llm_service.generate(
            prompt=plan_prompt,
            system_message="You are a planning assistant.",
            temperature=0.3
        )

        import json
        plan = json.loads(plan_json)

        # Pause for approval (HITL checkpoint)
        await agent_service.pause_for_approval(
            execution_id=execution.id,
            plan=plan,
            user_id=current_user.id
        )

        # User will approve via: POST /agent-executions/{id}/approve
        return {
            "execution_id": str(execution.id),
            "status": "awaiting_approval",
            "plan": plan
        }

    # 4. For simple/moderate, execute immediately
    else:
        # Execute query using appropriate model
        llm = llm_service.get_simple_llm() if complexity == "simple" else llm_service.get_llm()

        # Get context from documents (embedding search)
        from app.services.embedding_service import get_embedding_service
        embedding_service = get_embedding_service()

        # Search for relevant documents
        relevant_chunks = await embedding_service.similarity_search_async(
            db=db,
            query=user_query,
            limit=5,
            system_id=conversation.system_id
        )

        # Build context
        context = "\n\n".join([
            f"[Document {i+1}]\n{chunk.content}"
            for i, (chunk, score) in enumerate(relevant_chunks)
        ])

        # Generate response
        system_msg = f"""You are a helpful AI assistant. Use the following context to answer the user's question.

Context:
{context}

If the context doesn't contain relevant information, say so clearly."""

        response = await llm_service.generate(
            prompt=user_query,
            system_message=system_msg
        )

        # Create message
        message = Message(
            conversation_id=conversation_id,
            role="assistant",
            content=response,
            agent_execution_id=execution.id
        )
        db.add(message)

        # Mark execution complete
        await agent_service.complete_execution(
            execution_id=execution.id,
            message_id=message.id
        )

        db.commit()

        return {
            "execution_id": str(execution.id),
            "message_id": str(message.id),
            "status": "completed",
            "response": response
        }
```

---

## Model Comparison

| Model | Use Case | Speed | Cost | Max Tokens |
|-------|----------|-------|------|------------|
| `gemini-2.0-flash` | Simple queries, classification | ⚡ Fast | $ Low | 8K |
| `gemini-2.5-pro` | Complex reasoning, analysis | 🧠 Advanced | $$ Medium | 128K |

### When to Use Each Model

**Gemini 2.0 Flash (Simple Model):**
- Factual questions
- Query classification
- Simple summaries
- Quick responses

**Gemini 2.5 Pro (Complex Model):**
- Multi-step reasoning
- Analysis tasks
- Plan generation
- Creative writing
- Complex Q&A

---

## Configuration Reference

### Environment Variables

```bash
# Required
GOOGLE_API_KEY=your-api-key

# Optional Configuration
LLM_PROVIDER=google  # google, anthropic, or openai
DEFAULT_MODEL=gemini-2.5-pro
SIMPLE_QUERY_MODEL=gemini-2.0-flash
COMPLEX_QUERY_MODEL=gemini-2.5-pro
EMBEDDING_MODEL=models/embedding-001
EMBEDDING_PROVIDER=google
```

### Available Google Models

**Chat Models:**
- `gemini-2.5-pro` - Most capable model
- `gemini-2.0-flash` - Fast and efficient
- `gemini-2.0-pro` - Balanced performance

**Embedding Models:**
- `models/embedding-001` - Google's embedding model (768 dimensions)

---

## LangChain Features

### Chains

```python
from langchain.chains import LLMChain
from langchain_core.prompts import ChatPromptTemplate
from langchain_google_genai import ChatGoogleGenerativeAI

llm = ChatGoogleGenerativeAI(model="gemini-2.5-pro")

prompt = ChatPromptTemplate.from_messages([
    ("system", "You are a helpful assistant specialized in {topic}."),
    ("user", "{question}")
])

chain = prompt | llm

response = chain.invoke({
    "topic": "machine learning",
    "question": "What is supervised learning?"
})
```

### RAG (Retrieval-Augmented Generation)

```python
from langchain.chains import RetrievalQA
from langchain_google_genai import ChatGoogleGenerativeAI, GoogleGenerativeAIEmbeddings
from langchain_community.vectorstores import PGVector

# Setup
llm = ChatGoogleGenerativeAI(model="gemini-2.5-pro")
embeddings = GoogleGenerativeAIEmbeddings(model="models/embedding-001")

# Create PGVector store
connection_string = "postgresql://user:pass@localhost/db"
vectorstore = PGVector(
    connection_string=connection_string,
    embedding_function=embeddings,
)

# Create RAG chain
qa_chain = RetrievalQA.from_chain_type(
    llm=llm,
    retriever=vectorstore.as_retriever(search_kwargs={"k": 5}),
    return_source_documents=True
)

# Query
result = qa_chain({"query": "What is the main topic of these documents?"})
print(result["result"])
print(result["source_documents"])
```

### Agents

```python
from langchain.agents import AgentExecutor, create_tool_calling_agent
from langchain_core.tools import tool
from langchain_google_genai import ChatGoogleGenerativeAI

@tool
def search_documents(query: str) -> str:
    """Search through documents for relevant information."""
    # Your search logic here
    return f"Found information about: {query}"

llm = ChatGoogleGenerativeAI(model="gemini-2.5-pro")
tools = [search_documents]

agent = create_tool_calling_agent(llm, tools, prompt)
agent_executor = AgentExecutor(agent=agent, tools=tools)

result = agent_executor.invoke({"input": "Find information about AI"})
```

---

## Migration from Anthropic/OpenAI

If you previously used Anthropic Claude or OpenAI, the migration is simple:

### Old (Anthropic):
```python
from anthropic import Anthropic

client = Anthropic(api_key=api_key)
response = client.messages.create(
    model="claude-sonnet-4",
    messages=[{"role": "user", "content": "Hello"}]
)
```

### New (Google Gemini via LangChain):
```python
from langchain_google_genai import ChatGoogleGenerativeAI

llm = ChatGoogleGenerativeAI(model="gemini-2.5-pro")
response = llm.invoke("Hello")
```

**Or use our service:**
```python
from app.services.llm_service import get_llm_service

llm_service = get_llm_service()
response = await llm_service.generate("Hello")
```

---

## Troubleshooting

### API Key Issues

```bash
# Test your API key
python3 -c "
from langchain_google_genai import ChatGoogleGenerativeAI
llm = ChatGoogleGenerativeAI(model='gemini-2.5-pro')
print(llm.invoke('Hello').content)
"
```

### Import Errors

```bash
# Reinstall if needed
pip install --upgrade langchain-google-genai google-generativeai
```

### Rate Limits

Google Gemini has generous rate limits, but if you hit them:
- Use `gemini-2.0-flash` for non-critical queries
- Implement retry logic with exponential backoff
- Consider caching responses

---

## Next Steps

1. **Initialize Database**: Run `python scripts/init_db.py`
2. **Test LLM Service**: Create a test script
3. **Implement Authentication**: Create auth endpoints
4. **Build Message Endpoint**: Integrate with HITL workflow
5. **Add Document Upload**: Process and embed documents

---

**Last Updated:** 2025-11-19
**Status:** ✅ Google Gemini Integration Complete - Ready to Use
