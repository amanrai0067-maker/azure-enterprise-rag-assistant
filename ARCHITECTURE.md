# Enterprise Production Architecture Design

This document details the production-grade deployment architecture for the Enterprise Azure RAG Assistant, covering security, scaling, ingestion, and search strategies.

---

## 1. Visual Architecture Flow

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
└──────────────────────────────────────────────────────────────────────────────────────┘
2. Core Architectural Components
Document Ingestion: Azure Blob Storage triggers Azure Event Grid ➔ Azure Functions parse files via Azure AI Document Intelligence, chunk text, generate embeddings via Azure OpenAI, and push to Azure AI Search.

Search & Retrieval: Azure AI Search using Hybrid Search (Dense Vectors + BM25) and Bing-powered Semantic Re-ranking.

API & Compute: FastAPI hosted on Azure Container Apps with KEDA auto-scaling (0 to N instances).

Security & Isolation: Zero-Trust Virtual Network (VNet) with Private Endpoints. Microsoft Entra ID manages user authentication and document-level metadata security filters.

Secrets Management: Azure Key Vault for credentials with automated rotation.

Monitoring: Azure Application Insights tracks latency, token usage, and RAG quality metrics.

3. Key Design Decisions & Interview Explanations
Q1: Why did you choose this architecture?
Decoupled & Event-Driven: Heavy PDF ingestion runs asynchronously via Azure Functions, ensuring file uploads never slow down live user chat queries.

Zero-Trust Security: Private Endpoints and Managed Identities ensure data never travels over the public internet, satisfying enterprise compliance standards.

Q2: Why Azure AI Search?
Native enterprise features built-in: simultaneous vector search, keyword search, semantic re-ranking, document-level security ACL filters, and Entra ID integration.

Q3: Semantic vs Vector vs Hybrid — Which and Why?
Choice: Hybrid Search + Semantic Re-ranking.

Reasoning: Vector search captures semantic meaning, BM25 captures exact key terms/SKUs, and the Semantic Re-ranker ensures the best contextual chunk is placed at the top before sending to GPT-4o.

Q4: How does it scale from 10k to 10M documents?
10,000 Documents: Single Azure Function worker, Basic/S1 Azure AI Search tier, standard API endpoints.

10,000,000 Documents: Distributed batch processing via Apache Spark on Azure Databricks, Azure AI Search S3 High-Density tier (multi-partition/replica), Azure OpenAI PTUs (Provisioned Throughput), and Redis Semantic Caching.


---
