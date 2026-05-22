from langchain_community.document_loaders import PDFLoader
from langchain_openai import OpenAIEmbeddings
from langchain_community.vectorstores import Chroma

def build_candidate_vectorstore(pdf_path: str):
    loader = PDFLoader(pdf_path)
    docs = loader.load_and_split()
    embeddings = OpenAIEmbeddings(model="text-embedding-3-small")
    vectorstore = Chroma.from_documents(docs, embeddings, persist_directory="./chroma_db")
    return vectorstore

def get_relevant_experience(query: str):
    vectorstore = Chroma(persist_directory="./chroma_db", embedding_function=OpenAIEmbeddings(model="text-embedding-3-small"))
    return vectorstore.similarity_search(query, k=3)
