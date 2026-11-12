from uuid import UUID

from langchain_core.tools import tool
from psycopg_pool import AsyncConnectionPool

from agent_dev_lab.rag.embeddings import create_embeddings
from agent_dev_lab.resume.repository import find_resume_chunks


def create_resume_tool(
    pool: AsyncConnectionPool | None,
    user_id: UUID | None,
):
    """为当前用户创建一个简历检索工具。"""

    @tool
    async def search_resume(query: str) -> str:
        """Search the current user's uploaded resume for relevant experience."""

        # 命令行模式没有登录用户，无法确定应该查询谁的简历。
        if pool is None or user_id is None:
            return "请登录后再使用简历检索。"

        # 把用户的问题转换成向量，用来和简历片段的向量比较。
        embedding_client = create_embeddings()
        query_embedding = await embedding_client.aembed_query(query)

        # 查询这个用户最新上传的简历，取最相关的 5 个片段。
        chunks = await find_resume_chunks(
            pool=pool,
            user_id=user_id,
            query_embedding=query_embedding,
            limit=5,
        )

        if not chunks:
            return "没有检索到可用的简历内容。请确认已上传简历。"

        # 将片段拼接成文本，中间用分隔线隔开。
        result = "\n\n---\n\n".join(chunks)
        return result

    return search_resume