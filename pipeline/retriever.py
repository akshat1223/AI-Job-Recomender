from langchain_community.vectorstores import FAISS


def get_relevant_resume_context(vectorstore: FAISS, query: str, k: int = 4) -> str:
    """Retrieve top-k relevant chunks from the resume for a given query."""
    docs = vectorstore.similarity_search(query, k=k)
    return "\n\n".join([doc.page_content for doc in docs])
