from langchain_core.documents import Document
from langchain_text_splitters import RecursiveCharacterTextSplitter


def split_documents(documents: list[Document]) -> list[Document]:
    splitter = RecursiveCharacterTextSplitter(
        chunk_size=500,     #每个 Chunk 大约 500 个字符。
        chunk_overlap=100,  #相邻 Chunk 重叠 100 个字符。
    )

    return splitter.split_documents(documents)