from uuid import UUID, uuid4

from psycopg_pool import AsyncConnectionPool

from agent_dev_lab.config import EMBEDDING_MODEL


async def save_resume(
    pool: AsyncConnectionPool,
    user_id: UUID,
    filename: str,
    texts: list[str],
    embeddings: list[list[float]],
) -> UUID:
    resume_id = uuid4()
    rows = [
        (resume_id, index, text, str(embedding))
        for index, (text, embedding) in enumerate(
            zip(texts, embeddings, strict=True)
        )
    ]

    async with pool.connection() as conn:
        async with conn.transaction():
            await conn.execute(
                """
                INSERT INTO resumes (id, user_id, filename, embedding_model)
                VALUES (%s, %s, %s, %s)
                """,
                (resume_id, user_id, filename, EMBEDDING_MODEL),
            )
            async with conn.cursor() as cursor:
                await cursor.executemany(
                    """
                    INSERT INTO resume_chunks
                        (resume_id, chunk_index, content, embedding)
                    VALUES (%s, %s, %s, %s::vector)
                    """,
                    rows,
                )

    return resume_id


async def find_resume_chunks(
    pool: AsyncConnectionPool,
    user_id: UUID,
    query_embedding: list[float],
    limit: int = 5,
) -> list[str]:
    async with pool.connection() as conn:
        cursor = await conn.execute(
            """
            WITH latest_resume AS (
                SELECT id, embedding_model
                FROM resumes
                WHERE user_id = %s
                ORDER BY created_at DESC, id DESC
                LIMIT 1
            )
            SELECT chunk.content
            FROM resume_chunks AS chunk
            JOIN latest_resume AS resume ON resume.id = chunk.resume_id
            WHERE resume.embedding_model = %s
              AND vector_dims(chunk.embedding) = %s
            ORDER BY chunk.embedding <=> %s::vector, chunk.chunk_index
            LIMIT %s
            """,
            (
                user_id,
                EMBEDDING_MODEL,
                len(query_embedding),
                str(query_embedding),
                limit,
            ),
        )
        rows = await cursor.fetchall()

    return [row["content"] for row in rows]