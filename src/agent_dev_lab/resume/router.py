from pathlib import Path
from tempfile import TemporaryDirectory

from fastapi import APIRouter, HTTPException, UploadFile
from pypdf.errors import PdfReadError
from starlette.concurrency import run_in_threadpool

from agent_dev_lab.auth.dependencies import CurrentUser, DatabasePool
from agent_dev_lab.rag.embeddings import create_embeddings
from agent_dev_lab.resume.repository import save_resume
from agent_dev_lab.resume.service import split_resume


router = APIRouter(prefix="/resumes", tags=["Resumes"])

MAX_FILE_SIZE = 10 * 1024 * 1024


def _extract_resume_texts(content: bytes) -> list[str]:
    """将上传的 PDF 写入临时目录，提取并返回各个文本片段。"""
    with TemporaryDirectory() as temp_dir:
        pdf_path = Path(temp_dir) / "resume.pdf"
        pdf_path.write_bytes(content)

        chunks = split_resume(pdf_path)

        texts = []
        for chunk in chunks:
            texts.append(chunk.page_content)

        return texts


@router.post("")
async def upload_resume(
    file: UploadFile,
    current_user: CurrentUser,
    pool: DatabasePool,
):
    """上传 PDF 简历，生成向量并保存到当前用户名下。"""
    filename = file.filename or ""
    if not filename.lower().endswith(".pdf"):
        raise HTTPException(status_code=415, detail="请上传 PDF 文件")

    # 多读一个字节，用来判断文件是否超过上限。
    content = await file.read(MAX_FILE_SIZE + 1)
    if len(content) > MAX_FILE_SIZE:
        raise HTTPException(status_code=413, detail="简历不能超过 10 MB")

    # 写临时文件和解析 PDF 都是同步操作，放到线程池执行。
    # run_in_threadpool(函数名, 参数)，把这个同步函数交给线程池运行，运行完后把结果交给 texts。
    try:
        texts = await run_in_threadpool(_extract_resume_texts, content)
    except (PdfReadError, ValueError) as exc:
        raise HTTPException(
            status_code=422,
            detail="无法从 PDF 提取文字，请检查文件是否损坏或为扫描件",
        ) from exc

    # 向量顺序和 texts 一致，保存时按顺序一一配对。
    #aembed_documents(texts)：将文本内容转化成向量
    embeddings = await create_embeddings().aembed_documents(texts)

    # 用登录用户的 ID 绑定简历归属。
    resume_id = await save_resume(
        pool=pool,
        user_id=current_user.id,
        filename=filename,
        texts=texts,
        embeddings=embeddings,
    )

    return {
        "resume_id": str(resume_id),
        "filename": filename,
        "chunk_count": len(texts),
    }