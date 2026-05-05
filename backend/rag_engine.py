import os
from langchain_community.embeddings import HuggingFaceEmbeddings
from langchain_community.vectorstores import FAISS
from langchain_community.document_loaders import DirectoryLoader, TextLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from dotenv import load_dotenv

load_dotenv()

KNOWLEDGE_BASE_PATH = "data/knowledge_base/"
VECTOR_DB_PATH = "faiss_index"

def build_vector_db():
    """Load documents, chunk them, and create FAISS index."""
    if not os.path.exists(KNOWLEDGE_BASE_PATH):
        print(f"Path not found: {KNOWLEDGE_BASE_PATH}")
        return None

    loader = DirectoryLoader(
        KNOWLEDGE_BASE_PATH,
        glob="**/*.md",
        loader_cls=TextLoader,
        loader_kwargs={"encoding": "utf-8"}
    )
    documents = loader.load()

    if not documents:
        print("No documents found in knowledge base.")
        return None

    text_splitter = RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=100)
    chunks = text_splitter.split_documents(documents)

    embeddings = HuggingFaceEmbeddings(model_name="all-MiniLM-L6-v2")
    vector_db = FAISS.from_documents(chunks, embeddings)
    vector_db.save_local(VECTOR_DB_PATH)
    return vector_db

def get_retriever():
    """Load existing vector db or build it if not found."""
    try:
        embeddings = HuggingFaceEmbeddings(model_name="all-MiniLM-L6-v2")
        if os.path.exists(VECTOR_DB_PATH):
            vector_db = FAISS.load_local(VECTOR_DB_PATH, embeddings, allow_dangerous_deserialization=True)
        else:
            vector_db = build_vector_db()

        if vector_db:
            return vector_db.as_retriever(search_kwargs={"k": 3})
    except Exception as e:
        print(f"RAG retriever error: {e}")
    return None
