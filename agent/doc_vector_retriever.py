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

    # retrieve more chunks so parameter chunks are not missed
    docs_with_scores = vectorstore.similarity_search_with_score(query_lower, k=8)

    filtered_docs = []

    for doc, score in docs_with_scores:
        if score < 1.2:
            filtered_docs.append(doc)

    if not filtered_docs:
        filtered_docs = [doc for doc, _ in docs_with_scores]

    # operation boosting
    if "create" in query_lower:
        filtered_docs = [d for d in filtered_docs if "create" in d.metadata.get("operation","")] or filtered_docs

    elif "update" in query_lower:
        filtered_docs = [d for d in filtered_docs if "update" in d.metadata.get("operation","")] or filtered_docs

    elif "delete" in query_lower:
        filtered_docs = [d for d in filtered_docs if "delete" in d.metadata.get("operation","")] or filtered_docs

    elif "list" in query_lower or "all" in query_lower:
        filtered_docs = [d for d in filtered_docs if "list" in d.metadata.get("operation","")] or filtered_docs

    # return more chunks so documentation_node can extract parameters
    return filtered_docs[:6]

