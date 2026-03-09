import os
from langchain_community.vectorstores import FAISS
from langchain_community.embeddings import HuggingFaceEmbeddings

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

VECTOR_PATH = os.path.join(BASE_DIR, "vectordb", "faiss_docs")

embeddings = HuggingFaceEmbeddings(
    model_name="sentence-transformers/all-MiniLM-L6-v2"
)

vectorstore = FAISS.load_local(
    VECTOR_PATH,
    embeddings,
    allow_dangerous_deserialization=True
)

def normalize_query(q):

    q = q.lower()

    replacements = {
        "edit": "update",
        "modify": "update",
        "change": "update",
        "remove": "delete",
        "add": "create"
    }

    for k, v in replacements.items():
        q = q.replace(k, v)

    return q

def semantic_doc_search(query):

    query_lower = normalize_query(query)

    docs_with_scores = vectorstore.similarity_search_with_score(query_lower, k=10)

    docs = [doc for doc, _ in docs_with_scores]

    if not docs:
        return []

    # detect best operation from top result
    operation = docs[0].metadata.get("operation")

    # return only chunks belonging to that operation
    operation_docs = [d for d in docs if d.metadata.get("operation") == operation]

    return operation_docs

