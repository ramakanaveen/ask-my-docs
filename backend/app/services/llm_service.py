"""LLM Service using LangChain with Google Vertex AI.

This service provides a unified interface for LLM operations:
- Chat completions
- Streaming responses
- Function calling
- Model selection based on query complexity

Primary provider: Google Vertex AI via LangChain
"""

import asyncio
import os
from typing import Any, AsyncIterator, Dict, List, Optional

from langchain_core.language_models import BaseChatModel
from langchain_core.messages import (
    AIMessage,
    BaseMessage,
    HumanMessage,
    SystemMessage,
)
from langchain_core.output_parsers import StrOutputParser
from langchain_core.prompts import ChatPromptTemplate
from langchain_google_vertexai import ChatVertexAI

from app.core.config import get_settings


class LLMService:
    """Service for LLM operations using LangChain."""

    def __init__(self):
        """Initialize LLM service with settings."""
        self.settings = get_settings()

        # Set Google Cloud credentials environment variable
        if self.settings.GOOGLE_CREDENTIALS_PATH:
            os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = self.settings.GOOGLE_CREDENTIALS_PATH

    def get_llm(
        self,
        model: Optional[str] = None,
        temperature: float = 0.7,
        max_tokens: Optional[int] = None,
        streaming: bool = False,
    ) -> BaseChatModel:
        """Get LLM instance based on provider and model.

        Args:
            model: Model name (defaults to DEFAULT_MODEL from settings)
            temperature: Sampling temperature (0.0 to 1.0)
            max_tokens: Maximum tokens to generate
            streaming: Whether to enable streaming

        Returns:
            LangChain BaseChatModel instance

        Example:
            >>> llm_service = LLMService()
            >>> llm = llm_service.get_llm(model="gemini-2.5-pro")
            >>> response = llm.invoke("What is the capital of France?")
        """
        model_name = model or self.settings.DEFAULT_MODEL

        # Primary: Google Vertex AI
        if self.settings.LLM_PROVIDER == "google":
            return ChatVertexAI(
                model_name=model_name,
                project=self.settings.GOOGLE_PROJECT_ID,
                location=self.settings.GOOGLE_LOCATION,
                temperature=temperature,
                max_output_tokens=max_tokens,
                streaming=streaming,
            )

        # Alternative: Anthropic Claude (if configured)
        elif self.settings.LLM_PROVIDER == "anthropic":
            from langchain_anthropic import ChatAnthropic

            return ChatAnthropic(
                model=model_name,
                anthropic_api_key=self.settings.ANTHROPIC_API_KEY,
                temperature=temperature,
                max_tokens=max_tokens,
                streaming=streaming,
            )

        # Alternative: OpenAI (if configured)
        elif self.settings.LLM_PROVIDER == "openai":
            from langchain_openai import ChatOpenAI

            return ChatOpenAI(
                model=model_name,
                openai_api_key=self.settings.OPENAI_API_KEY,
                temperature=temperature,
                max_tokens=max_tokens,
                streaming=streaming,
            )

        else:
            raise ValueError(f"Unknown LLM provider: {self.settings.LLM_PROVIDER}")

    def get_simple_llm(self) -> BaseChatModel:
        """Get fast model for simple queries.

        Returns:
            LLM instance configured for simple queries

        Example:
            >>> llm_service = LLMService()
            >>> simple_llm = llm_service.get_simple_llm()
            >>> response = simple_llm.invoke("Summarize this in one sentence: ...")
        """
        return self.get_llm(
            model=self.settings.SIMPLE_QUERY_MODEL,
            temperature=0.3,  # Lower temperature for factual responses
        )

    def get_complex_llm(self) -> BaseChatModel:
        """Get advanced model for complex queries.

        Returns:
            LLM instance configured for complex queries

        Example:
            >>> llm_service = LLMService()
            >>> complex_llm = llm_service.get_complex_llm()
            >>> response = complex_llm.invoke("Analyze the financial trends...")
        """
        return self.get_llm(
            model=self.settings.COMPLEX_QUERY_MODEL,
            temperature=0.7,  # Higher temperature for creative reasoning
        )

    async def generate(
        self,
        prompt: str,
        system_message: Optional[str] = None,
        model: Optional[str] = None,
        temperature: float = 0.7,
        max_tokens: Optional[int] = None,
    ) -> str:
        """Generate a response to a prompt.

        Args:
            prompt: User prompt/question
            system_message: Optional system message for context
            model: Model to use (defaults to DEFAULT_MODEL)
            temperature: Sampling temperature
            max_tokens: Maximum tokens to generate

        Returns:
            Generated response text

        Example:
            >>> llm_service = LLMService()
            >>> response = await llm_service.generate(
            ...     prompt="What is machine learning?",
            ...     system_message="You are a helpful AI assistant."
            ... )
        """
        llm = self.get_llm(
            model=model,
            temperature=temperature,
            max_tokens=max_tokens,
        )

        # Build messages
        messages: List[BaseMessage] = []
        if system_message:
            messages.append(SystemMessage(content=system_message))
        messages.append(HumanMessage(content=prompt))

        # Generate response
        response = await llm.ainvoke(messages)
        return response.content

    async def generate_streaming(
        self,
        prompt: str,
        system_message: Optional[str] = None,
        model: Optional[str] = None,
        temperature: float = 0.7,
        max_tokens: Optional[int] = None,
    ) -> AsyncIterator[str]:
        """Generate a streaming response to a prompt.

        Args:
            prompt: User prompt/question
            system_message: Optional system message for context
            model: Model to use (defaults to DEFAULT_MODEL)
            temperature: Sampling temperature
            max_tokens: Maximum tokens to generate

        Yields:
            Chunks of generated text

        Example:
            >>> llm_service = LLMService()
            >>> async for chunk in llm_service.generate_streaming(
            ...     prompt="Explain quantum computing",
            ...     system_message="You are a physics teacher."
            ... ):
            ...     print(chunk, end="", flush=True)
        """
        llm = self.get_llm(
            model=model,
            temperature=temperature,
            max_tokens=max_tokens,
            streaming=True,
        )

        # Build messages
        messages: List[BaseMessage] = []
        if system_message:
            messages.append(SystemMessage(content=system_message))
        messages.append(HumanMessage(content=prompt))

        # Stream response
        async for chunk in llm.astream(messages):
            yield chunk.content

    async def chat(
        self,
        messages: List[Dict[str, str]],
        model: Optional[str] = None,
        temperature: float = 0.7,
        max_tokens: Optional[int] = None,
    ) -> str:
        """Generate a response to a conversation.

        Args:
            messages: List of messages in format [{"role": "user|assistant|system", "content": "..."}]
            model: Model to use (defaults to DEFAULT_MODEL)
            temperature: Sampling temperature
            max_tokens: Maximum tokens to generate

        Returns:
            Generated response text

        Example:
            >>> llm_service = LLMService()
            >>> messages = [
            ...     {"role": "system", "content": "You are a helpful assistant."},
            ...     {"role": "user", "content": "What is Python?"},
            ...     {"role": "assistant", "content": "Python is a programming language."},
            ...     {"role": "user", "content": "Tell me more about it."}
            ... ]
            >>> response = await llm_service.chat(messages)
        """
        llm = self.get_llm(
            model=model,
            temperature=temperature,
            max_tokens=max_tokens,
        )

        # Convert to LangChain message format
        lc_messages: List[BaseMessage] = []
        for msg in messages:
            role = msg["role"]
            content = msg["content"]

            if role == "system":
                lc_messages.append(SystemMessage(content=content))
            elif role == "user":
                lc_messages.append(HumanMessage(content=content))
            elif role == "assistant":
                lc_messages.append(AIMessage(content=content))

        # Generate response
        response = await llm.ainvoke(lc_messages)
        return response.content

    async def chat_streaming(
        self,
        messages: List[Dict[str, str]],
        model: Optional[str] = None,
        temperature: float = 0.7,
        max_tokens: Optional[int] = None,
    ) -> AsyncIterator[str]:
        """Generate a streaming response to a conversation.

        Args:
            messages: List of messages in format [{"role": "user|assistant|system", "content": "..."}]
            model: Model to use (defaults to DEFAULT_MODEL)
            temperature: Sampling temperature
            max_tokens: Maximum tokens to generate

        Yields:
            Chunks of generated text

        Example:
            >>> llm_service = LLMService()
            >>> messages = [
            ...     {"role": "user", "content": "Write a story about AI"}
            ... ]
            >>> async for chunk in llm_service.chat_streaming(messages):
            ...     print(chunk, end="", flush=True)
        """
        llm = self.get_llm(
            model=model,
            temperature=temperature,
            max_tokens=max_tokens,
            streaming=True,
        )

        # Convert to LangChain message format
        lc_messages: List[BaseMessage] = []
        for msg in messages:
            role = msg["role"]
            content = msg["content"]

            if role == "system":
                lc_messages.append(SystemMessage(content=content))
            elif role == "user":
                lc_messages.append(HumanMessage(content=content))
            elif role == "assistant":
                lc_messages.append(AIMessage(content=content))

        # Stream response
        async for chunk in llm.astream(lc_messages):
            yield chunk.content

    async def classify_query_complexity(self, query: str) -> str:
        """Classify query as simple, moderate, or complex.

        Args:
            query: User query to classify

        Returns:
            Classification: "simple", "moderate", or "complex"

        Example:
            >>> llm_service = LLMService()
            >>> complexity = await llm_service.classify_query_complexity(
            ...     "What is the capital of France?"
            ... )
            >>> print(complexity)  # "simple"
        """
        llm = self.get_simple_llm()  # Use fast model for classification

        classification_prompt = f"""Classify the following query based on complexity:

Query: {query}

Classification criteria:
- SIMPLE: Straightforward factual question, single-step answer, no analysis needed
  Examples: "What is X?", "When did Y happen?", "Who is Z?"

- MODERATE: Requires some reasoning, comparison, or multi-step thinking
  Examples: "Compare X and Y", "Explain how Z works", "What are the benefits of X?"

- COMPLEX: Requires deep analysis, planning, multiple data sources, or multi-step reasoning
  Examples: "Analyze trends in X", "Create a plan for Y", "What insights can we derive from Z?"

Respond with ONLY one word: SIMPLE, MODERATE, or COMPLEX"""

        response = await self.generate(
            prompt=classification_prompt,
            temperature=0.1,  # Low temperature for consistent classification
            model=self.settings.SIMPLE_QUERY_MODEL,
        )

        # Parse response
        classification = response.strip().upper()
        if "SIMPLE" in classification:
            return "simple"
        elif "MODERATE" in classification:
            return "moderate"
        elif "COMPLEX" in classification:
            return "complex"
        else:
            # Default to moderate if unclear
            return "moderate"


# Singleton instance
_llm_service: Optional[LLMService] = None


def get_llm_service() -> LLMService:
    """Get singleton LLM service instance.

    Returns:
        LLM service instance

    Example:
        >>> from app.services.llm_service import get_llm_service
        >>> llm_service = get_llm_service()
        >>> response = await llm_service.generate("Hello!")
    """
    global _llm_service
    if _llm_service is None:
        _llm_service = LLMService()
    return _llm_service
