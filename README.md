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
---

## 📊 Step 4 — RAG Evaluation & Benchmarking

To prove the effectiveness of the enterprise upgrades, we built a test evaluation dataset covering diverse query types and measured performance across **Retrieval**, **Generation**, and **System Metrics** before and after optimizations.

### 1. Evaluation Dataset Sample (Test Suite)

| Question | Expected Document | Expected Section | Difficulty | Query Type |
| :--- | :--- | :--- | :--- | :--- |
| "What is the file retention period?" | `Data_Retention_Policy.pdf` | Section 3.1 | Easy | Straightforward |
| "Compare refund policy for Enterprise vs Standard." | `Enterprise_Terms.pdf` & `Standard_Terms.pdf` | Sections 4 & 2 | Hard | Multi-Document |
| "What is the limit?" | N/A | N/A | Medium | Ambiguous |
| "What is the CEO's home address?" | N/A (Missing Data) | N/A | Hard | No Answer / Hallucination Trap |
| "What about Standard?" (Follow-up) | `Standard_Pricing.pdf` | Section 1.2 | Medium | Follow-up |

---

### 2. Evaluation Workflow (Before vs. After)

```text
 [ Baseline Basic RAG ] 
         │ (High failure rate on multi-doc, ambiguous & edge cases)
         ▼
 [ Identify Failures ] (Weak chunks, outdated versions, hallucinated answers)
         │
         ▼
 [ Improve Architecture ] (Hybrid search, query rewriting, strict prompt grounding)
         │
         ▼
 [ Re-run Evaluation & Benchmark ]
---

## 🧠 Step 5 — Architecture & Problem-Solving Deep Dive

### 1. Retrieval Quality: Debugging 1 Relevant Chunk out of 5
* **Debugging Methodology:**
  1. **Examine Chunk Boundaries:** Check if the document was split mid-sentence or broke critical contextual relationships. Adjust chunk size to 1000 characters with 150 overlap.
  2. **Analyze Vector vs. Keyword Weights:** If pure vector search is retrieving semantic neighbors that lack exact terminology, switch immediately to **Hybrid Search (Dense + BM25)**.
  3. **Tune Reranker Depth:** Increase candidate pool size (e.g., fetch top 50 via hybrid search) and apply a **Semantic Reranker** to push the single relevant chunk to position 1.
  4. **Evaluate Top-$K$:** Reduce default $K$ from 5 to 3 if noisy chunks dominate the context window.

---

### 2. Latency Bottleneck: Identifying 3s to 12s Inflation
* **Identification Process:**
  1. Use **Azure Application Insights & Distributed Tracing** to inspect end-to-end request duration across layers (API Gateway, Search Service, OpenAI API).
  2. **Isolate Bottlenecks:**
     * *If Search Tier is slow:* Check Azure AI Search replica/partition utilization or unindexed queries.
     * *If OpenAI Tier is slow:* Check for rate-limiting (`429 Too Many Requests`) causing automatic SDK retries, or excessive context token counts (>8k tokens).
* **Optimizations:** Implement **Azure Cache for Redis** for semantic caching and switch to asynchronous FastAPI non-blocking workers.

---

### 3. Scale: Moving from 10k to 5 Million Documents
* **Architectural Changes:**
  * **Ingestion Pipeline:** Replace single-worker Azure Functions with **Apache Spark on Azure Databricks** or Azure Batch for distributed, parallel document parsing and embedding generation.
  * **Search Storage:** Upgrade from Basic/S1 tier to **Azure AI Search S3 High-Density Tier**, leveraging multi-partition horizontal scaling and dedicated read replicas to handle high QPS.
  * **LLM Inference:** Migrate from Pay-As-You-Go API endpoints to **Provisioned Throughput Units (PTU)** to guarantee dedicated compute capacity and eliminate latency spikes.

---

### 4. Security: Multi-Department Access-Controlled RAG (HR, Finance, Legal, Engineering)
* **Architectural Solution:**
  * **Metadata Tagging:** Ingest every document chunk with strict access control tags (e.g., `department: ["HR"]`, `classification: "confidential"`).
  * **Dynamic OData Filtering:** Extract the user's active security groups from their Microsoft Entra ID JWT token at the FastAPI gateway.
  * **Search-Time Enforcement:** Automatically inject OData security filters into every Azure AI Search query:
    ```text
    search.in(department, 'Engineering,Public') and classification le 'Internal'
    ```
    *Result:* Unauthorized HR documents are filtered out at the database layer before retrieval, ensuring zero data leakage.

---

### 5. Cost Optimization: Mitigating Azure OpenAI Cost Spikes
* **Identification & Optimization Strategy:**
  * **Tokens & Context:** Implement dynamic top-$K$ selection and extractive summarization to pass only high-value chunks rather than bloated raw text blocks.
  * **Model Selection:** Route low-complexity tasks (query rewriting, intent classification, guardrail checks) to lightweight models (`gpt-4o-mini`), reserving flagship models (`gpt-4o`) strictly for final answer synthesis.
  * **Semantic Caching:** Deploy Redis Semantic Cache to serve identical or semantically equivalent user queries instantly without hitting OpenAI endpoints.
  * **Embeddings:** Generate and store static document embeddings once during offline ingestion, avoiding repeated on-the-fly embedding API calls.

---

### 6. Production Failure: Debugging Correct Answer with Invalid/Fake Citation
* **Systematic Debugging Methodology:**
  1. **User Query Analysis:** Check if ambiguous phrasing triggered cross-document search interference.
  2. **Retrieval Inspection:** Verify if the search engine pulled a decoy chunk that shared high keyword overlap but belonged to an obsolete document version.
  3. **Ranking Evaluation:** Check if the semantic reranker failed to penalize a hallucinated chunk score.
  4. **Context & Prompt Review:** Inspect whether passing multiple conflicting chunks confused the LLM regarding source attribution.
  5. **LLM & Citation Generation:** Identify if the model hallucinated a plausible filename based on training priors despite instructions.
* **Fix:** Enforce strict system prompt boundaries requiring the model to cite exact chunk metadata IDs supplied in context, paired with a post-generation citation validation layer that rejects outputs referencing non-existent files.
