import os
from langchain_community.embeddings.fastembed import FastEmbedEmbeddings
from langchain_community.vectorstores import FAISS

DEFAULT_PATH = "vectorstore/resume_index"


def get_embeddings():
    return FastEmbedEmbeddings(model_name="BAAI/bge-small-en-v1.5")


def build_vectorstore(chunks: list, path: str = DEFAULT_PATH) -> FAISS:
    vectorstore = FAISS.from_documents(chunks, get_embeddings())
    vectorstore.save_local(path)
    return vectorstore


def load_vectorstore(path: str = DEFAULT_PATH) -> FAISS:
    return FAISS.load_local(path, get_embeddings(), allow_dangerous_deserialization=True)


def vectorstore_exists(path: str = DEFAULT_PATH) -> bool:
    return os.path.exists(path)
