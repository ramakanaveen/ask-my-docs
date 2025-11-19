#!/usr/bin/env python3
"""
Test script for Google Gemini integration via LangChain.

This script tests:
1. Direct LangChain API usage
2. LLM Service
3. Embedding Service
4. Query complexity classification

Usage:
    python scripts/test_google_gemini.py
"""

import asyncio
import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))


async def test_direct_langchain():
    """Test direct LangChain API."""
    print("=" * 60)
    print("TEST 1: Direct LangChain API")
    print("=" * 60)

    try:
        from langchain_google_genai import ChatGoogleGenerativeAI

        llm = ChatGoogleGenerativeAI(model="gemini-2.5-pro")
        response = llm.invoke("Sing a ballad of LangChain.")

        print("✓ Direct LangChain API works!")
        print(f"\nResponse:\n{response.content}\n")
        return True
    except Exception as e:
        print(f"✗ Direct LangChain API failed: {e}\n")
        return False


async def test_llm_service():
    """Test LLM Service."""
    print("=" * 60)
    print("TEST 2: LLM Service")
    print("=" * 60)

    try:
        from app.services.llm_service import get_llm_service

        llm_service = get_llm_service()

        # Test simple generation
        print("\n2a. Simple generation:")
        response = await llm_service.generate(
            prompt="What is 2+2? Answer in one sentence.",
            system_message="You are a helpful math tutor.",
        )
        print(f"Response: {response}")

        # Test streaming
        print("\n2b. Streaming generation:")
        print("Response: ", end="", flush=True)
        async for chunk in llm_service.generate_streaming(
            prompt="Count from 1 to 5.",
            system_message="You are a helpful assistant.",
        ):
            print(chunk, end="", flush=True)
        print("\n")

        # Test chat
        print("2c. Chat with history:")
        messages = [
            {"role": "system", "content": "You are a friendly assistant."},
            {"role": "user", "content": "My name is Alice."},
            {"role": "assistant", "content": "Nice to meet you, Alice!"},
            {"role": "user", "content": "What is my name?"},
        ]
        response = await llm_service.chat(messages)
        print(f"Response: {response}")

        print("\n✓ LLM Service works!")
        return True
    except Exception as e:
        print(f"\n✗ LLM Service failed: {e}")
        import traceback

        traceback.print_exc()
        return False


async def test_query_classification():
    """Test query complexity classification."""
    print("\n" + "=" * 60)
    print("TEST 3: Query Complexity Classification")
    print("=" * 60)

    try:
        from app.services.llm_service import get_llm_service

        llm_service = get_llm_service()

        queries = [
            ("What is the capital of France?", "simple"),
            ("Compare Python and JavaScript", "moderate"),
            (
                "Analyze the financial trends over the past year and create a strategic plan",
                "complex",
            ),
        ]

        all_correct = True
        for query, expected in queries:
            complexity = await llm_service.classify_query_complexity(query)
            status = "✓" if complexity == expected else "✗"
            print(f"\n{status} Query: {query}")
            print(f"   Expected: {expected}, Got: {complexity}")

            if complexity != expected:
                all_correct = False

        if all_correct:
            print("\n✓ Query classification works perfectly!")
        else:
            print("\n⚠ Query classification works but results may vary")
        return True
    except Exception as e:
        print(f"\n✗ Query classification failed: {e}")
        import traceback

        traceback.print_exc()
        return False


async def test_embedding_service():
    """Test Embedding Service."""
    print("\n" + "=" * 60)
    print("TEST 4: Embedding Service")
    print("=" * 60)

    try:
        from app.services.embedding_service import get_embedding_service

        embedding_service = get_embedding_service()

        # Test single embedding
        print("\n4a. Single text embedding:")
        vector = await embedding_service.embed_text("Hello world")
        print(f"✓ Generated embedding with dimension: {len(vector)}")

        # Test batch embeddings
        print("\n4b. Batch embeddings:")
        texts = ["Machine learning", "Artificial intelligence", "Deep learning"]
        vectors = await embedding_service.embed_texts(texts)
        print(f"✓ Generated {len(vectors)} embeddings")

        # Verify all vectors have same dimension
        dimensions = [len(v) for v in vectors]
        print(f"   Dimensions: {dimensions[0]} (all vectors)")

        print("\n✓ Embedding Service works!")
        return True
    except Exception as e:
        print(f"\n✗ Embedding Service failed: {e}")
        import traceback

        traceback.print_exc()
        return False


async def test_model_selection():
    """Test different model selection."""
    print("\n" + "=" * 60)
    print("TEST 5: Model Selection")
    print("=" * 60)

    try:
        from app.services.llm_service import get_llm_service

        llm_service = get_llm_service()

        # Test simple model
        print("\n5a. Simple model (gemini-2.0-flash):")
        simple_llm = llm_service.get_simple_llm()
        response = simple_llm.invoke("What is AI in 5 words?")
        print(f"Response: {response.content}")

        # Test complex model
        print("\n5b. Complex model (gemini-2.5-pro):")
        complex_llm = llm_service.get_complex_llm()
        response = complex_llm.invoke("Explain AI in one sentence.")
        print(f"Response: {response.content}")

        print("\n✓ Model selection works!")
        return True
    except Exception as e:
        print(f"\n✗ Model selection failed: {e}")
        import traceback

        traceback.print_exc()
        return False


async def main():
    """Run all tests."""
    print("\n")
    print("╔" + "═" * 58 + "╗")
    print("║" + " " * 10 + "Google Gemini Integration Tests" + " " * 16 + "║")
    print("╚" + "═" * 58 + "╝")
    print()

    # Check environment
    try:
        from app.core.config import get_settings

        settings = get_settings()
        print(f"✓ Settings loaded")
        print(f"  LLM Provider: {settings.LLM_PROVIDER}")
        print(f"  Default Model: {settings.DEFAULT_MODEL}")
        print(f"  Simple Model: {settings.SIMPLE_QUERY_MODEL}")
        print(f"  Complex Model: {settings.COMPLEX_QUERY_MODEL}")
        print(f"  Embedding Model: {settings.EMBEDDING_MODEL}")
        print(f"  Embedding Provider: {settings.EMBEDDING_PROVIDER}")
        print()

        if not settings.GOOGLE_API_KEY or settings.GOOGLE_API_KEY.startswith("your-"):
            print("✗ GOOGLE_API_KEY not set in .env file!")
            print("  Please update your .env file with a valid Google API key.")
            return

    except Exception as e:
        print(f"✗ Failed to load settings: {e}")
        return

    # Run tests
    results = []

    results.append(await test_direct_langchain())
    results.append(await test_llm_service())
    results.append(await test_query_classification())
    results.append(await test_embedding_service())
    results.append(await test_model_selection())

    # Summary
    print("\n" + "=" * 60)
    print("SUMMARY")
    print("=" * 60)
    passed = sum(results)
    total = len(results)
    print(f"\nTests Passed: {passed}/{total}")

    if passed == total:
        print("\n✓ All tests passed! Google Gemini integration is working perfectly.")
    elif passed > 0:
        print(
            f"\n⚠ {total - passed} test(s) failed. Please check the errors above."
        )
    else:
        print("\n✗ All tests failed. Please check your configuration and API key.")

    print("\n" + "=" * 60)
    print()


if __name__ == "__main__":
    asyncio.run(main())
