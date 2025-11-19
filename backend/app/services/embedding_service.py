"""Embedding Service using Google Vertex AI or OpenAI.

This service provides embedding operations for document chunks:
- Generate embeddings for text
- Store embeddings in PGVector
- Similarity search

Primary provider: Google Vertex AI Embeddings
"""

import os
from typing import List, Optional, Tuple

from langchain_core.embeddings import Embeddings
from langchain_google_vertexai import VertexAIEmbeddings
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.models.document import DocumentChunk


class EmbeddingService:
    """Service for embedding operations."""

    def __init__(self):
        """Initialize embedding service with settings."""
        self.settings = get_settings()
        self._embeddings: Optional[Embeddings] = None

        # Set Google Cloud credentials environment variable
        if self.settings.GOOGLE_CREDENTIALS_PATH:
            os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = self.settings.GOOGLE_CREDENTIALS_PATH

    @property
    def embeddings(self) -> Embeddings:
        """Get embeddings instance (lazy loading).

        Returns:
            LangChain Embeddings instance
        """
        if self._embeddings is None:
            if self.settings.EMBEDDING_PROVIDER == "google":
                self._embeddings = VertexAIEmbeddings(
                    model_name=self.settings.GOOGLE_EMBEDDING_MODEL_NAME,
                    project=self.settings.GOOGLE_PROJECT_ID,
                    location=self.settings.GOOGLE_EMBEDDING_LOCATION,
                )
            elif self.settings.EMBEDDING_PROVIDER == "openai":
                from langchain_openai import OpenAIEmbeddings

                self._embeddings = OpenAIEmbeddings(
                    model=self.settings.EMBEDDING_MODEL,
                    openai_api_key=self.settings.OPENAI_API_KEY,
                )
            else:
                raise ValueError(
                    f"Unknown embedding provider: {self.settings.EMBEDDING_PROVIDER}"
                )

        return self._embeddings

    async def embed_text(self, text: str) -> List[float]:
        """Generate embedding for a single text.

        Args:
            text: Text to embed

        Returns:
            Embedding vector as list of floats

        Example:
            >>> embedding_service = EmbeddingService()
            >>> vector = await embedding_service.embed_text("Hello world")
            >>> len(vector)  # 768 for Google embeddings
            768
        """
        return await self.embeddings.aembed_query(text)

    async def embed_texts(self, texts: List[str]) -> List[List[float]]:
        """Generate embeddings for multiple texts (batched).

        Args:
            texts: List of texts to embed

        Returns:
            List of embedding vectors

        Example:
            >>> embedding_service = EmbeddingService()
            >>> texts = ["Hello", "World", "AI"]
            >>> vectors = await embedding_service.embed_texts(texts)
            >>> len(vectors)
            3
        """
        return await self.embeddings.aembed_documents(texts)

    async def embed_document_chunk(
        self,
        db: Session,
        chunk: DocumentChunk,
    ) -> DocumentChunk:
        """Generate and store embedding for a document chunk.

        Args:
            db: Database session
            chunk: Document chunk to embed

        Returns:
            Updated chunk with embedding

        Example:
            >>> from app.models.document import DocumentChunk
            >>> chunk = DocumentChunk(content="Sample text...")
            >>> chunk = await embedding_service.embed_document_chunk(db, chunk)
            >>> chunk.embedding is not None
            True
        """
        from datetime import datetime

        # Generate embedding
        embedding = await self.embed_text(chunk.content)

        # Update chunk
        chunk.embedding = embedding
        chunk.embedded_at = datetime.utcnow()
        chunk.embedding_model = self.settings.EMBEDDING_MODEL

        db.commit()
        db.refresh(chunk)

        return chunk

    async def embed_document_chunks(
        self,
        db: Session,
        chunks: List[DocumentChunk],
        batch_size: int = 100,
    ) -> List[DocumentChunk]:
        """Generate and store embeddings for multiple document chunks (batched).

        Args:
            db: Database session
            chunks: List of document chunks to embed
            batch_size: Number of chunks to embed in each batch

        Returns:
            Updated chunks with embeddings

        Example:
            >>> chunks = [DocumentChunk(content="Text 1"), DocumentChunk(content="Text 2")]
            >>> chunks = await embedding_service.embed_document_chunks(db, chunks)
        """
        from datetime import datetime

        # Process in batches
        for i in range(0, len(chunks), batch_size):
            batch = chunks[i : i + batch_size]
            texts = [chunk.content for chunk in batch]

            # Generate embeddings for batch
            embeddings = await self.embed_texts(texts)

            # Update chunks
            for chunk, embedding in zip(batch, embeddings):
                chunk.embedding = embedding
                chunk.embedded_at = datetime.utcnow()
                chunk.embedding_model = self.settings.EMBEDDING_MODEL

        db.commit()
        return chunks

    def similarity_search(
        self,
        db: Session,
        query: str,
        query_embedding: Optional[List[float]] = None,
        limit: int = 10,
        system_id: Optional[str] = None,
        document_ids: Optional[List[str]] = None,
    ) -> List[Tuple[DocumentChunk, float]]:
        """Search for similar document chunks using PGVector.

        Args:
            db: Database session
            query: Query text (if query_embedding not provided)
            query_embedding: Pre-computed query embedding
            limit: Maximum number of results
            system_id: Optional system ID filter
            document_ids: Optional list of document IDs to search within

        Returns:
            List of (chunk, similarity_score) tuples

        Example:
            >>> results = embedding_service.similarity_search(
            ...     db,
            ...     query="machine learning",
            ...     limit=5
            ... )
            >>> for chunk, score in results:
            ...     print(f"Score: {score}, Content: {chunk.content[:100]}...")
        """
        from sqlalchemy import func
        from app.models.document import Document

        # Get query embedding if not provided
        if query_embedding is None:
            import asyncio

            query_embedding = asyncio.run(self.embed_text(query))

        # Build query with PGVector similarity search
        query_obj = db.query(
            DocumentChunk,
            func.cosine_distance(DocumentChunk.embedding, query_embedding).label(
                "distance"
            ),
        )

        # Apply filters
        if system_id:
            query_obj = query_obj.join(Document).filter(Document.system_id == system_id)

        if document_ids:
            query_obj = query_obj.filter(DocumentChunk.document_id.in_(document_ids))

        # Execute search
        results = (
            query_obj.order_by("distance")  # Closer is more similar
            .limit(limit)
            .all()
        )

        # Convert distance to similarity score (1 - distance)
        return [(chunk, 1 - distance) for chunk, distance in results]

    async def similarity_search_async(
        self,
        db: Session,
        query: str,
        query_embedding: Optional[List[float]] = None,
        limit: int = 10,
        system_id: Optional[str] = None,
        document_ids: Optional[List[str]] = None,
    ) -> List[Tuple[DocumentChunk, float]]:
        """Async version of similarity search.

        Args:
            db: Database session
            query: Query text (if query_embedding not provided)
            query_embedding: Pre-computed query embedding
            limit: Maximum number of results
            system_id: Optional system ID filter
            document_ids: Optional list of document IDs to search within

        Returns:
            List of (chunk, similarity_score) tuples
        """
        # Get query embedding if not provided
        if query_embedding is None:
            query_embedding = await self.embed_text(query)

        # Use sync similarity search (PGVector doesn't support async)
        return self.similarity_search(
            db=db,
            query=query,
            query_embedding=query_embedding,
            limit=limit,
            system_id=system_id,
            document_ids=document_ids,
        )


# Singleton instance
_embedding_service: Optional[EmbeddingService] = None


def get_embedding_service() -> EmbeddingService:
    """Get singleton embedding service instance.

    Returns:
        Embedding service instance

    Example:
        >>> from app.services.embedding_service import get_embedding_service
        >>> embedding_service = get_embedding_service()
        >>> vector = await embedding_service.embed_text("Hello!")
    """
    global _embedding_service
    if _embedding_service is None:
        _embedding_service = EmbeddingService()
    return _embedding_service
