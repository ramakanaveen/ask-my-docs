# Google Vertex AI Migration Summary

## What Changed

Successfully migrated from **Google Gemini API** (API key based) to **Google Vertex AI** (service account based) for both LLM and embeddings.

### Key Changes

1. **LLM Service** (`app/services/llm_service.py`)
   - Changed from `langchain_google_genai.ChatGoogleGenerativeAI`
   - To `langchain_google_vertexai.ChatVertexAI`
   - Now uses service account credentials instead of API key

2. **Embedding Service** (`app/services/embedding_service.py`)
   - Changed from `langchain_google_genai.GoogleGenerativeAIEmbeddings`
   - To `langchain_google_vertexai.VertexAIEmbeddings`
   - Now uses service account credentials instead of API key

3. **Configuration** (`app/core/config.py`)
   - Added `GOOGLE_CREDENTIALS_PATH`: Path to service account JSON file
   - Added `GOOGLE_PROJECT_ID`: GCP project ID
   - Added `GOOGLE_LOCATION`: Vertex AI region for LLM
   - Added `GOOGLE_EMBEDDING_LOCATION`: Vertex AI region for embeddings
   - Added `GOOGLE_EMBEDDING_MODEL_NAME`: Specific embedding model name
   - Removed dependency on `GOOGLE_API_KEY`

4. **Dependencies** (`requirements.txt` and `pyproject.toml`)
   - Added `langchain-google-vertexai>=2.0.0`
   - Added `google-cloud-aiplatform>=1.38.0`
   - Removed `google-generativeai`

## Environment Configuration

Your `.env` file now uses:

```bash
# Google Vertex AI Configuration
GOOGLE_CREDENTIALS_PATH=/Users/naveenramaka/Downloads/naveen-0203-3263b8c0400b.json
GOOGLE_PROJECT_ID=naveen-0203
GOOGLE_LOCATION=us-central1
GOOGLE_EMBEDDING_LOCATION=us-central1

# Gemini model settings
GEMINI_MODEL_NAME=gemini-2.5-pro
GEMINI_TEMPERATURE=0.2
GEMINI_TOP_P=0.95

# Embedding model
GOOGLE_EMBEDDING_MODEL_NAME=text-embedding-005
```

## How It Works

### Authentication
Both services automatically set the `GOOGLE_APPLICATION_CREDENTIALS` environment variable on initialization:

```python
if self.settings.GOOGLE_CREDENTIALS_PATH:
    os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = self.settings.GOOGLE_CREDENTIALS_PATH
```

This allows the Google Cloud SDK to authenticate using your service account JSON file.

### LLM Usage Example

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
    prompt="Explain quantum computing",
):
    print(chunk, end="", flush=True)

# Get specific model
llm = llm_service.get_llm(model="gemini-2.5-pro")
response = llm.invoke("Hello!")
```

### Embedding Usage Example

```python
from app.services.embedding_service import get_embedding_service

# Get service instance
embedding_service = get_embedding_service()

# Single text embedding
vector = await embedding_service.embed_text("Hello world")
print(f"Vector dimension: {len(vector)}")  # 768 for text-embedding-005

# Multiple texts (batched)
texts = ["Hello", "World", "AI"]
vectors = await embedding_service.embed_texts(texts)

# Similarity search (with database)
results = await embedding_service.similarity_search_async(
    db=db,
    query="machine learning",
    limit=5
)
for chunk, score in results:
    print(f"Score: {score}, Content: {chunk.content[:100]}...")
```

## Testing the Migration

### 1. Install Dependencies

```bash
cd backend
pip install -r requirements.txt
# or
poetry install
```

### 2. Verify Configuration

```bash
# Check your .env file has the required fields
cat .env | grep GOOGLE
```

### 3. Test LLM Service

Create a test script `test_llm.py`:

```python
import asyncio
from app.services.llm_service import get_llm_service

async def test_llm():
    llm_service = get_llm_service()

    # Test simple generation
    print("Testing LLM generation...")
    response = await llm_service.generate(
        prompt="Say 'Hello from Vertex AI!'",
        temperature=0.7
    )
    print(f"Response: {response}")

    # Test streaming
    print("\nTesting streaming...")
    async for chunk in llm_service.generate_streaming(
        prompt="Count from 1 to 5"
    ):
        print(chunk, end="", flush=True)
    print("\n")

if __name__ == "__main__":
    asyncio.run(test_llm())
```

Run it:
```bash
cd backend
python test_llm.py
```

### 4. Test Embedding Service

Create a test script `test_embeddings.py`:

```python
import asyncio
from app.services.embedding_service import get_embedding_service

async def test_embeddings():
    embedding_service = get_embedding_service()

    # Test single embedding
    print("Testing single text embedding...")
    vector = await embedding_service.embed_text("Hello from Vertex AI!")
    print(f"Vector dimension: {len(vector)}")
    print(f"First 5 values: {vector[:5]}")

    # Test batch embeddings
    print("\nTesting batch embeddings...")
    texts = ["Machine learning", "Artificial intelligence", "Deep learning"]
    vectors = await embedding_service.embed_texts(texts)
    print(f"Embedded {len(vectors)} texts")
    for i, text in enumerate(texts):
        print(f"  {text}: dimension {len(vectors[i])}")

if __name__ == "__main__":
    asyncio.run(test_embeddings())
```

Run it:
```bash
cd backend
python test_embeddings.py
```

## Expected Behavior

### Success Indicators
- ✅ No authentication errors
- ✅ LLM returns coherent responses
- ✅ Embeddings are 768-dimensional vectors (for text-embedding-005)
- ✅ Streaming works smoothly

### Common Issues

1. **Authentication Error**: `Could not automatically determine credentials`
   - **Fix**: Verify `GOOGLE_CREDENTIALS_PATH` points to a valid JSON file
   - **Fix**: Ensure the service account has Vertex AI permissions

2. **Permission Denied**: `Permission 'aiplatform.endpoints.predict' denied`
   - **Fix**: Enable Vertex AI API in your GCP project
   - **Fix**: Grant the service account `Vertex AI User` role

3. **Region Error**: `Location not found`
   - **Fix**: Use valid regions like `us-central1`, `us-east1`, `europe-west1`
   - **Fix**: Check available regions: https://cloud.google.com/vertex-ai/docs/general/locations

4. **Model Not Found**: `Model 'X' not found`
   - **Fix**: Use supported models: `gemini-2.5-pro`, `gemini-2.0-flash-001`, etc.
   - **Fix**: Check model availability in your region

## Benefits of Vertex AI

✅ **Service Account Authentication**: More secure than API keys
✅ **Enterprise Grade**: Better for production deployments
✅ **Fine-grained IAM**: Control access at the service level
✅ **Audit Logs**: Track all API usage in GCP
✅ **Private Networking**: VPC support for secure communication
✅ **Better Rate Limits**: Higher quotas for production workloads

## Next Steps

1. Test the migration with your existing workflows
2. Monitor API usage in GCP Console
3. Adjust quotas if needed
4. Consider implementing caching to reduce API calls
5. Set up monitoring and alerting for API errors

## Rollback Plan

If you need to rollback to API key approach:

1. Add `GOOGLE_API_KEY` to `.env`
2. Change imports back to `langchain_google_genai`
3. Update the service initialization code
4. Revert `requirements.txt` changes

However, Vertex AI is recommended for production use.
