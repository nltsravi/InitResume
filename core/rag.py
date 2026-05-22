import os
from langchain_community.document_loaders import PyPDFLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_openai import OpenAIEmbeddings
from langchain_community.vectorstores import Chroma

class ResumeRAGPipeline:
    def __init__(self, persist_directory: str = "./chroma_db"):
        self.persist_directory = persist_directory
        self.embeddings = OpenAIEmbeddings(model="text-embedding-3-small")
        self.text_splitter = RecursiveCharacterTextSplitter(chunk_size=500, chunk_overlap=50)

    def ingest_resume(self, file_path: str):
        """
        Ingests a resume PDF, splits it, and embeds it into Chroma vector store.
        """
        print(f"[RAG] Ingesting resume at path: {file_path}...")
        if not os.path.exists(file_path):
            print(f"[RAG] Warning: File {file_path} not found. Skipping ingestion.")
            return None
            
        loader = PyPDFLoader(file_path)
        documents = loader.load()
        chunks = self.text_splitter.split_documents(documents)
        
        vector_store = Chroma.from_documents(
            documents=chunks,
            embedding=self.embeddings,
            persist_directory=self.persist_directory
        )
        vector_store.persist()
        print(f"[RAG] Ingestion completed. Ingested {len(chunks)} chunks.")
        return vector_store

    def retrieve_relevant_experience(self, query: str, limit: int = 3) -> list:
        """
        Queries Chroma vector store to retrieve chunks of the resume that match the query.
        """
        print(f"[RAG] Querying vector store for: '{query}'...")
        if not os.path.exists(self.persist_directory):
            return ["No experience found. Chroma vector store not initialized."]
            
        vector_store = Chroma(
            persist_directory=self.persist_directory,
            embedding_function=self.embeddings
        )
        results = vector_store.similarity_search(query, k=limit)
        return [doc.page_content for doc in results]
