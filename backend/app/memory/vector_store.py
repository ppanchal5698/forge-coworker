"""Vector store.

Thin wrapper around pgvector — embeds and stores past actions/file summaries,
and performs similarity search against them.
"""

import uuid
from sqlalchemy import select
from langchain_openai import OpenAIEmbeddings

from app.config import get_settings
from app.db.session import get_session_factory
from app.db.models.memory import Memory


def get_embeddings_model() -> OpenAIEmbeddings:
    settings = get_settings()
    return OpenAIEmbeddings(
        base_url=settings.resolved_llm_base_url,
        api_key=settings.resolved_llm_api_key,
        model=settings.resolved_embedding_model_name,
        check_embedding_ctx_length=False
    )


async def store_memory(workspace_id: uuid.UUID, content: str) -> None:
    """Embed text content and store it in the workspace's semantic memory."""
    embeddings_model = get_embeddings_model()
    # aembed_query returns a single list of floats
    embedding = await embeddings_model.aembed_query(content)
    
    factory = get_session_factory()
    async with factory() as session:
        memory = Memory(
            workspace_id=workspace_id,
            content=content,
            embedding=embedding
        )
        session.add(memory)
        await session.commit()


async def search_similar(workspace_id: uuid.UUID, query: str, top_k: int = 5) -> list[str]:
    """Search for the top_k most similar memory entries in the workspace."""
    embeddings_model = get_embeddings_model()
    query_embedding = await embeddings_model.aembed_query(query)
    
    factory = get_session_factory()
    async with factory() as session:
        # Use pgvector's cosine distance operator `<=>`
        stmt = (
            select(Memory.content)
            .where(Memory.workspace_id == workspace_id)
            .where(Memory.embedding != None)
            .order_by(Memory.embedding.cosine_distance(query_embedding))
            .limit(top_k)
        )
        
        result = await session.execute(stmt)
        rows = result.scalars().all()
        return list(rows)
