import os
import json
from langchain_core.documents import Document
from langchain_community.vectorstores import FAISS
from langchain_community.embeddings import HuggingFaceEmbeddings
from sympy import content

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

DOC_PATH = os.path.join(BASE_DIR, "documentation")
VECTOR_PATH = os.path.join(BASE_DIR, "vectordb", "faiss_docs")

os.makedirs(VECTOR_PATH, exist_ok=True)


def format_field(value):
    """Convert lists/dicts to readable text for embeddings."""
    if not value:
        return "None"

    if isinstance(value, list):
        formatted = []
        for item in value:
            if isinstance(item, dict):
                formatted.append(", ".join(f"{k}:{v}" for k, v in item.items()))
            else:
                formatted.append(str(item))
        return "\n".join(formatted)

    if isinstance(value, dict):
        return "\n".join(f"{k}: {v}" for k, v in value.items())

    return str(value)


def load_docs():

    docs = []

    for file in os.listdir(DOC_PATH):

        if not file.endswith(".json"):
            continue

        file_path = os.path.join(DOC_PATH, file)

        with open(file_path, "r", encoding="utf-8") as f:
            data = json.load(f)

        operations = data.get("operations", [])

        if not operations:
            print(f"Skipping {file} - no operations found")
            continue

        for op in operations:

            operation = op.get("operation", "")
            method = op.get("method", "")
            endpoint = op.get("endpoint", "")

            description = op.get("description", "")
            required_params = format_field(op.get("required_parameters"))
            optional_params = format_field(op.get("optional_parameters"))
            query_params = format_field(op.get("query_parameters"))
            body_fields = format_field(op.get("body_fields"))
            keywords = format_field(op.get("keywords"))

            metadata = {
                "operation": operation,
                "method": method,
                "endpoint": endpoint,
                "required_parameters": op.get("required_parameters", []),
                "optional_parameters": op.get("optional_parameters", []),
                "query_parameters": op.get("query_parameters", []),
                "body_fields": op.get("body_fields", []),
                "source": file
            }

            # Description chunk
            docs.append(
                Document(
                    page_content=f"""
API Operation: {operation}

Description:
{description}
""".strip(),
                    metadata=metadata
                )
            )

            # Endpoint + Method chunk
            docs.append(
                Document(
                    page_content=f"""
API Operation: {operation}

HTTP Method:
{method}

Endpoint:
{endpoint}
""".strip(),
                    metadata=metadata
                )
            )

            # Parameters chunk
            docs.append(
                Document(
                    page_content=f"""
API Operation: {operation}

Required Parameters:
{required_params}

Optional Parameters:
{optional_params}

Query Parameters:
{query_params}

Body Fields:
{body_fields}
""".strip(),
                    metadata=metadata
                )
            )

            # Keywords chunk
            docs.append(
                Document(
                    page_content=f"""
API Operation: {operation}

Keywords:
{keywords}
""".strip(),
                    metadata=metadata
                )
            )

    print(f"Loaded {len(docs)} documentation chunks")

    return docs


def create_vector_db():

    documents = load_docs()

    if not documents:
        print("No documents found. Vector DB not created.")
        return

    embeddings = HuggingFaceEmbeddings(
        model_name="sentence-transformers/all-MiniLM-L6-v2"
    )

    vectorstore = FAISS.from_documents(documents, embeddings)

    vectorstore.save_local(VECTOR_PATH)

    print("Documentation VectorDB created successfully")


if __name__ == "__main__":
    create_vector_db()


