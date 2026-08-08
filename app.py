import os
import logging
import warnings
from typing import List, Dict, Any
from dotenv import load_dotenv

warnings.filterwarnings("ignore", category=DeprecationWarning)

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field

from langchain_community.document_loaders import PyPDFLoader, TextLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser
from langchain_core.runnables import RunnablePassthrough

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("RAG_Assistant")

load_dotenv()

app = FastAPI(
    title="Azure Enterprise RAG Assistant",
    description="Production-Grade Knowledge Assistant using Azure OpenAI and Azure AI Search",
    version="1.0.0"
)

AZURE_OPENAI_ENDPOINT = os.getenv("AZURE_OPENAI_ENDPOINT", "")
AZURE_OPENAI_API_KEY = os.getenv("AZURE_OPENAI_API_KEY", "")
AZURE_OPENAI_CHAT_DEPLOYMENT = os.getenv("AZURE_OPENAI_CHAT_DEPLOYMENT", "gpt-4o")
AZURE_OPENAI_EMBEDDING_DEPLOYMENT = os.getenv("AZURE_OPENAI_EMBEDDING_DEPLOYMENT", "text-embedding-3-large")
AZURE_SEARCH_ENDPOINT = os.getenv("AZURE_SEARCH_SERVICE_ENDPOINT", "")
AZURE_SEARCH_KEY = os.getenv("AZURE_SEARCH_API_KEY", "")
INDEX_NAME = os.getenv("AZURE_SEARCH_INDEX_NAME", "enterprise-knowledge-index")

# Check if active Azure credentials are set
IS_MOCK_MODE = "your-azure-openai" in AZURE_OPENAI_ENDPOINT or not AZURE_OPENAI_API_KEY

if not IS_MOCK_MODE:
    try:
        from langchain_openai import AzureOpenAIEmbeddings, AzureChatOpenAI
        from langchain_community.vectorstores.azuresearch import AzureSearch

        embeddings = AzureOpenAIEmbeddings(
            azure_deployment=AZURE_OPENAI_EMBEDDING_DEPLOYMENT,
            openai_api_version="2024-02-01",
            azure_endpoint=AZURE_OPENAI_ENDPOINT,
            api_key=AZURE_OPENAI_API_KEY,
        )

        vector_store = AzureSearch(
            azure_search_endpoint=AZURE_SEARCH_ENDPOINT,
            azure_search_key=AZURE_SEARCH_KEY,
            index_name=INDEX_NAME,
            embedding_function=embeddings.embed_query,
            additional_search_args={"search_type": "hybrid"}
        )

        llm = AzureChatOpenAI(
            azure_deployment=AZURE_OPENAI_CHAT_DEPLOYMENT,
            openai_api_version="2024-02-01",
            azure_endpoint=AZURE_OPENAI_ENDPOINT,
            api_key=AZURE_OPENAI_API_KEY,
            temperature=0.0
        )
        logger.info("Connected successfully to Azure OpenAI and Azure AI Search.")
    except Exception as e:
        logger.warning(f"Failed to connect to Azure: {e}. Falling back to Mock Mode.")
        IS_MOCK_MODE = True
else:
    logger.info("Running in Azure Architecture Simulation (Mock Mode) for local demonstration.")


class QueryRequest(BaseModel):
    query: str = Field(..., example="What is the policy duration?")

class SourceCitation(BaseModel):
    document_name: str
    page_number: int
    snippet: str

class QueryResponse(BaseModel):
    answer: str
    citations: List[SourceCitation]

def parse_and_chunk_document(file_path: str):
    loader = PyPDFLoader(file_path) if file_path.endswith(".pdf") else TextLoader(file_path)
    raw_docs = loader.load()

    splitter = RecursiveCharacterTextSplitter(
        chunk_size=1000,
        chunk_overlap=200,
        separators=["\n\n", "\n", ". ", " ", ""]
    )
    return splitter.split_documents(raw_docs)

@app.post("/api/v1/ingest")
async def ingest_document(file_path: str):
    try:
        chunks = parse_and_chunk_document(file_path)
        if not IS_MOCK_MODE:
            vector_store.add_documents(chunks)
        return {"status": "Success", "chunks_created": len(chunks), "mode": "Azure Live" if not IS_MOCK_MODE else "Local Simulation"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

GROUNDED_SYSTEM_PROMPT = """You are an Enterprise Knowledge Assistant. Answer based EXCLUSIVELY on the provided context below.

STRICT RULES:
1. Answer ONLY using facts in Context. If missing, say: "I do not have enough information in the provided knowledge base to answer this question."
2. Every factual statement must have citations: [Source: <filename>, Page: <page_number>].

Context:
{context}

Question:
{question}
"""

prompt_template = ChatPromptTemplate.from_template(GROUNDED_SYSTEM_PROMPT)

@app.post("/api/v1/query", response_model=QueryResponse)
async def query_knowledge_base(request: QueryRequest):
    try:
        if IS_MOCK_MODE:
            # Simulated response showing RAG grounding & citations
            return QueryResponse(
                answer=f"Based on the enterprise documentation, the requested information regarding '{request.query}' is fully compliant with company policy. [Source: company_policy.pdf, Page: 1]",
                citations=[
                    SourceCitation(
                        document_name="company_policy.pdf",
                        page_number=1,
                        snippet="Enterprise RAG Search results retrieved via Azure AI Search Hybrid Index..."
                    )
                ]
            )

        retriever = vector_store.as_retriever(search_type="hybrid", k=4)
        retrieved_docs = retriever.invoke(request.query)

        context_str = "\n\n".join([f"--- Document: {os.path.basename(doc.metadata.get('source', 'Doc'))} (Page {doc.metadata.get('page', 1)}) ---\n{doc.page_content}" for doc in retrieved_docs])

        chain = (
            {"context": lambda x: context_str, "question": RunnablePassthrough()}
            | prompt_template
            | llm
            | StrOutputParser()
        )

        llm_response = chain.invoke(request.query)

        citations = [
            SourceCitation(
                document_name=os.path.basename(doc.metadata.get("source", "Unknown")),
                page_number=doc.metadata.get("page", 1),
                snippet=doc.page_content[:150] + "..."
            )
            for doc in retrieved_docs
        ]

        return QueryResponse(answer=llm_response, citations=citations)

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app:app", host="0.0.0.0", port=8000, reload=True)