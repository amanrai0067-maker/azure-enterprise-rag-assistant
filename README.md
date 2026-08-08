Markdown# Azure Enterprise Knowledge Assistant (Production-Grade RAG Pipeline)

An enterprise-ready **Retrieval-Augmented Generation (RAG)** solution built to demonstrate high-accuracy document retrieval, strict factual grounding, and resilience against common RAG failure modes. Architected on **Python**, **FastAPI**, **Streamlit**, **Azure OpenAI**, and **Azure AI Search** with production-grade security, networking, and scaling patterns.

---

## Executive Summary

Standard RAG pipelines often suffer from hallucinated responses, inaccurate chunk retrieval, and loss of context in multi-turn conversations. This project implements advanced retrieval strategies—including **Hybrid Search**, **Metadata Filtering**, **Conversational Query Rewriting**, and **Strict System Grounding**—backed by a secure cloud-native Azure architecture.

---

## 📐 Enterprise Production Architecture

```text
 [ Clients / Users ]
         │
         ▼ (HTTPS / Public Ingress)
┌──────────────────────────────────────────────────────────────────────────────────────┐
│  AZURE API MANAGEMENT (APIM) + WAF                                                   │
│   • Microsoft Entra ID (OAuth2 / JWT Authentication)                                 │
│   • Rate Limiting, Throttling & DDoS Protection                                      │
└────────────────────────────────────────┬─────────────────────────────────────────────┘
                                         │ (Internal VNet Routing)
┌────────────────────────────────────────▼─────────────────────────────────────────────┐
│  AZURE VIRTUAL NETWORK (VNet) - PRIVATE SUBNET                                       │
│                                                                                      │
│  ┌────────────────────────────────────────────────────────────────────────────────┐  │
│  │ APPLICATION TIER                                                               │  │
│  │  • Azure Container Apps (FastAPI Backend + Streamlit UI)                        │  │
│  │  • Managed Identity (Zero Hardcoded Keys)                                      │  │
│  │  • Azure Cache for Redis (Semantic Caching)                                    │  │
│  └─────────────────────────────────┬──────────────────────────────────────────────┘  │
│                                    │                                                 │
│       ┌────────────────────────────┴─────────────────────────────┐                   │
│       ▼                                                          ▼                   │
│  ┌───────────────────────────────┐                          ┌─────────────────────┐  │
│  │ AZURE AI SEARCH               │                          │ AZURE OPENAI        │  │
│  │  • Hybrid Search (Dense+BM25) │                          │  • GPT-4o           │  │
│  │  • Semantic Re-ranker         │                          │  • Embeddings-3     │  │
│  │  • Document Security Filters  │                          │  • Private Endpoint │  │
│  └───────────────────────────────┘                          └─────────────────────┘  │
│                                                                                      │
│  ┌────────────────────────────────────────────────────────────────────────────────┐  │
│  │ EVENT-DRIVEN INGESTION TIER                                                    │  │
│  │  Blob Storage ──► Event Grid ──► Azure Function ──► Document Intelligence      │  │
│  └────────────────────────────────────────────────────────────────────────────────┘  │
└────────────────────────────────────────┬─────────────────────────────────────────────┘
                                         │
┌────────────────────────────────────────▼─────────────────────────────────────────────┐
│ OBSERVABILITY & GOVERNANCE                                                           │
│  • Azure Key Vault (Secrets Management)                                              │
│  • Azure Monitor & Application Insights (Telemetry & Cost Tracking)                    │
└────────────────────────────────────────┬─────────────────────────────────────────────┘
Core ComponentsDocument Ingestion: Azure Blob Storage triggers Azure Event Grid ➔ Azure Functions parse files via Azure AI Document Intelligence, chunk text (1000 char / 150 overlap), generate embeddings via Azure OpenAI, and push to Azure AI Search.Search & Retrieval: Azure AI Search using Hybrid Search (Dense Vectors + BM25) and Bing-powered Semantic Re-ranking.API & Compute: FastAPI hosted on Azure Container Apps with KEDA auto-scaling.Security & Isolation: Zero-Trust Virtual Network (VNet) with Private Endpoints. Microsoft Entra ID manages user authentication and document-level metadata security filters.🛠️ Handling 6 Core RAG Failure ScenariosThis pipeline is engineered to overcome the six major failure modes common in basic implementations:Failure ScenarioRoot CauseEngineering Solution Implemented1. Correct Doc, Wrong ChunkSuboptimal chunk boundaries splitting critical context and key terms.Hybrid Search (Dense + BM25) combined with Bing-powered Semantic Re-ranking and recursive chunking.2. Multi-Section InformationFixed top-$K$ limits missing fragmented context spread across pages.Query Decomposition: Breaking comparative prompts into parallel sub-queries and expanding the context window ($K=6$ to $10$).3. Conflicting / Outdated PoliciesVector similarity pulling older document versions alongside newer ones.Metadata Filtering & Versioning: Enforcing OData filters (status eq 'active') and recency boosting.4. Hallucination on Missing DataLLMs generating synthetic answers when data is absent from context.Strict Grounding: Setting LLM temperature=0.0 with strict prompt guardrails and score thresholds.5. Ambiguous QueryShort or vague queries ("What is the limit?") causing noisy retrieval.Clarification Guardrails: Checking conversation history or proactively asking clarifying questions.6. Multi-Turn Context LossEphemeral dialogue state causing follow-up queries ("What about Standard?") to fail.Conversational Query Rewriting: Transforming follow-up prompts into standalone, context-rich search queries.📈 Scalability: 10,000 vs. 10,000,000 DocumentsArchitectural Component10,000 Documents (~10–50 GB)10,000,000 Documents (~10–50 TB)Ingestion EngineAzure Functions / Single-worker processingDistributed Processing: Apache Spark on Azure Databricks for massive parallel parsing.Vector & Search StoreAzure AI Search Basic / S1 TierAzure AI Search S3 High-Density Tier: Multi-partition horizontal scaling with dedicated read replicas.LLM Inference LimitsPay-As-You-Go API endpointsProvisioned Throughput Units (PTU): Dedicated capacity reservation to prevent rate-limiting (429).Caching LayerBasic In-memory cachingAzure Cache for Redis Enterprise: Semantic caching to instantly serve repeated identical queries.Tech Stack & QuickstartRuntime: Python 3.11+, FastAPI, StreamlitAI Services: Azure OpenAI (GPT-4o, text-embedding-3-large), Azure AI SearchClone & Run:Bashgit clone [https://github.com/amanrai0067-maker/azure-enterprise-rag-assistant.git](https://github.com/amanrai0067-maker/azure-enterprise-rag-assistant.git)
cd azure-enterprise-rag-assistant
pip install -r requirements.txt
uvicorn app.main:app --reload
