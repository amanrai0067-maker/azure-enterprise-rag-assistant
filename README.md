# Azure Enterprise Knowledge Assistant

**A production-grade Retrieval-Augmented Generation (RAG) pipeline for enterprise document Q&A**

Built with Python, FastAPI, Streamlit, Azure OpenAI, and Azure AI Search — engineered for high-accuracy retrieval, strict factual grounding, and resilience against the most common RAG failure modes.

---

## Executive Summary

Standard RAG pipelines commonly suffer from hallucinated responses, inaccurate chunk retrieval, and loss of context across multi-turn conversations. This project addresses those failure modes directly through **Hybrid Search**, **Metadata-Based Versioning**, **Conversational Query Rewriting**, and **Strict Grounding Guardrails** — all deployed on a secure, cloud-native Azure architecture.

---

## Architecture

```
                              [ Clients / Users ]
                                      │
                                      ▼  HTTPS / Public Ingress
        ┌───────────────────────────────────────────────────────────┐
        │  Azure API Management (APIM) + WAF                        │
        │  • Microsoft Entra ID (OAuth2 / JWT authentication)        │
        │  • Rate limiting, throttling, DDoS protection              │
        └──────────────────────────┬────────────────────────────────┘
                                    │  Internal VNet routing
        ┌───────────────────────────────────────────────────────────┐
        │  Azure Virtual Network — Private Subnet                   │
        │                                                           │
        │  ┌─────────────────────────────────────────────────────┐  │
        │  │  Application Tier                                   │  │
        │  │  • Azure Container Apps (FastAPI + Streamlit UI)     │  │
        │  │  • Managed Identity (zero hardcoded keys)            │  │
        │  │  • Azure Cache for Redis (semantic caching)          │  │
        │  └───────────────────┬───────────────────┬─────────────┘  │
        │                      ▼                   ▼                │
        │  ┌────────────────────────┐   ┌───────────────────────┐   │
        │  │  Azure AI Search        │   │  Azure OpenAI         │   │
        │  │  • Hybrid search        │   │  • GPT-4o             │   │
        │  │    (dense + BM25)       │   │  • text-embedding-3   │   │
        │  │  • Semantic re-ranker   │   │  • Private endpoint   │   │
        │  │  • Document-level       │   │                       │   │
        │  │    security filters     │   │                       │   │
        │  └─────────────────────────┘   └───────────────────────┘   │
        │                                                           │
        │  ┌─────────────────────────────────────────────────────┐  │
        │  │  Event-Driven Ingestion Tier                         │  │
        │  │  Blob Storage → Event Grid → Azure Function          │  │
        │  │  → Document Intelligence → Chunking → Indexing       │  │
        │  └─────────────────────────────────────────────────────┘  │
        └──────────────────────────┬────────────────────────────────┘
                                    ▼
        ┌───────────────────────────────────────────────────────────┐
        │  Observability & Governance                                │
        │  • Azure Key Vault (secrets management)                    │
        │  • Azure Monitor & Application Insights (telemetry, cost)  │
        └───────────────────────────────────────────────────────────┘
```

### Core Components

| Layer | Description |
|---|---|
| **Document Ingestion** | Azure Blob Storage triggers Event Grid → Azure Functions parse files via Document Intelligence, chunk text (1000 chars, 150 overlap), generate embeddings via Azure OpenAI, and push to Azure AI Search. |
| **Search & Retrieval** | Azure AI Search with Hybrid Search (dense vectors + BM25) and semantic re-ranking. |
| **API & Compute** | FastAPI on Azure Container Apps with KEDA auto-scaling. |
| **Security & Isolation** | Zero-trust VNet with private endpoints; Microsoft Entra ID handles authentication and document-level metadata security filters. |

---

## Handling the 6 Core RAG Failure Scenarios

| # | Scenario | Root Cause | Engineering Solution |
|---|---|---|---|
| 1 | **Correct document, wrong chunk** | Suboptimal chunk boundaries split critical context and key terms. | Recursive chunking + Hybrid Search (dense + BM25) with semantic re-ranking. |
| 2 | **Multi-section information** | Fixed Top-K limits miss context fragmented across pages. | Query decomposition into parallel sub-queries; expanded context window (K = 6–10). |
| 3 | **Conflicting / outdated policies** | Vector similarity retrieves older document versions alongside newer ones. | Metadata filtering and versioning — OData filters (`status eq 'active'`) plus recency boosting. |
| 4 | **Hallucination on missing data** | The LLM generates a plausible-sounding answer when context is absent. | Strict grounding: `temperature = 0.0`, enforced prompt guardrails, and a minimum-evidence score threshold. |
| 5 | **Ambiguous query** | Short or vague queries (e.g. "What is the limit?") produce noisy retrieval. | Clarification guardrails — check conversation history, or proactively ask a clarifying question. |
| 6 | **Multi-turn context loss** | Ephemeral dialogue state causes follow-ups (e.g. "What about Standard?") to fail. | Conversational query rewriting — transforms follow-ups into standalone, context-rich search queries. |

---

## Scalability: 10K vs. 10M Documents

| Architectural Component | 10,000 Documents (~10–50 GB) | 10,000,000 Documents (~10–50 TB) |
|---|---|---|
| **Ingestion Engine** | Azure Functions, single-worker processing | Apache Spark on Azure Databricks for distributed, parallel parsing |
| **Vector / Search Store** | Azure AI Search Basic / S1 tier | Azure AI Search S3 High-Density tier — multi-partition horizontal scaling with dedicated read replicas |
| **LLM Inference** | Pay-as-you-go API endpoints | Provisioned Throughput Units (PTU) — dedicated capacity, no rate-limit (429) risk |
| **Caching Layer** | Basic in-memory caching | Azure Cache for Redis Enterprise — semantic caching for repeated queries |

---

## Tech Stack

- **Runtime:** Python 3.11+, FastAPI, Streamlit
- **AI Services:** Azure OpenAI (GPT-4o, text-embedding-3-large), Azure AI Search
- **Infrastructure:** Azure Container Apps, Azure Functions, Azure Key Vault, Application Insights

### Quickstart

```bash
git clone https://github.com/amanrai0067-maker/azure-enterprise-rag-assistant.git
cd azure-enterprise-rag-assistant
pip install -r requirements.txt
uvicorn app.main:app --reload
```

---

## RAG Evaluation & Benchmarking

To validate the enterprise-grade upgrades, a test evaluation dataset covering diverse query types was built, measuring **Retrieval**, **Generation**, and **System** metrics before and after each optimization.

### Evaluation Dataset (Sample)

| Question | Expected Document(s) | Expected Section | Difficulty | Query Type |
|---|---|---|---|---|
| "What is the file retention period?" | `Data_Retention_Policy.pdf` | Section 3.1 | Easy | Straightforward |
| "Compare the refund policy for Enterprise vs. Standard." | `Enterprise_Terms.pdf`, `Standard_Terms.pdf` | Sections 4 & 2 | Hard | Multi-document |
| "What is the limit?" | — | — | Medium | Ambiguous |
| "What is the CEO's home address?" | — (not in knowledge base) | — | Hard | No-answer / hallucination trap |
| "What about Standard?" *(follow-up)* | `Standard_Pricing.pdf` | Section 1.2 | Medium | Follow-up |

### Evaluation Workflow

```
Baseline RAG
     │   (high failure rate on multi-doc, ambiguous, and edge cases)
     ▼
Identify Failures
     │   (weak chunk boundaries, outdated versions, hallucinated answers)
     ▼
Improve Architecture
     │   (hybrid search, query rewriting, strict prompt grounding)
     ▼
Re-run Evaluation & Benchmark
```

---

## Architecture & Problem-Solving Deep Dive

### 1. Retrieval Quality — Debugging "1 Relevant Chunk out of 5"

1. **Examine chunk boundaries** — check whether documents were split mid-sentence, breaking contextual relationships; standardize to 1000-character chunks with 150-character overlap.
2. **Compare vector vs. keyword weighting** — if pure vector search returns semantic neighbors lacking exact terminology, switch to Hybrid Search (dense + BM25).
3. **Tune re-ranker depth** — widen the candidate pool (e.g., fetch top 50 via hybrid search) and apply a semantic re-ranker to surface the correct chunk at position 1.
4. **Re-evaluate Top-K** — reduce K from 5 to 3 if noisy chunks dominate the context window.

### 2. Latency — Diagnosing a 3s → 12s Regression

1. Use Azure Application Insights and distributed tracing to inspect end-to-end request duration across every layer (API gateway, search service, OpenAI API).
2. Isolate the bottleneck:
   - **Search tier slow** → check Azure AI Search replica/partition utilization or unindexed query patterns.
   - **OpenAI tier slow** → check for `429 Too Many Requests` triggering SDK retries, or excessive context length (> 8K tokens).
3. **Mitigate** with Azure Cache for Redis (semantic caching) and asynchronous, non-blocking FastAPI workers.

### 3. Scale — Moving from 10K to 5M Documents

- **Ingestion:** replace single-worker Azure Functions with Apache Spark on Azure Databricks (or Azure Batch) for distributed, parallel parsing and embedding generation.
- **Search storage:** upgrade from Basic/S1 to Azure AI Search S3 High-Density tier, with multi-partition horizontal scaling and dedicated read replicas for high QPS.
- **LLM inference:** migrate from pay-as-you-go to Provisioned Throughput Units (PTU) to guarantee dedicated capacity and eliminate latency spikes.

### 4. Security — Access-Controlled RAG Across HR, Finance, Legal, and Engineering

- **Metadata tagging:** every document chunk is ingested with access-control tags, e.g. `department: ["HR"]`, `classification: "confidential"`.
- **Dynamic OData filtering:** the user's active security groups are extracted from their Microsoft Entra ID JWT at the FastAPI gateway.
- **Search-time enforcement:** every Azure AI Search query is automatically scoped, e.g.:
  ```
  search.in(department, 'Engineering,Public') and classification le 'Internal'
  ```
  Unauthorized documents are filtered out at the database layer before retrieval — guaranteeing zero data leakage.

### 5. Cost — Mitigating Azure OpenAI Cost Spikes

- **Tokens & context:** apply dynamic Top-K selection and extractive summarization to pass only high-value chunks instead of bloated raw text.
- **Model routing:** send low-complexity tasks (query rewriting, intent classification, guardrail checks) to `gpt-4o-mini`, reserving `gpt-4o` for final answer synthesis.
- **Semantic caching:** deploy Redis Semantic Cache to instantly serve identical or semantically equivalent queries without hitting the OpenAI endpoint.
- **Embeddings:** generate and store embeddings once during offline ingestion, avoiding repeated on-the-fly calls.

### 6. Production Failure — Correct Answer, Invalid Citation

1. **Query analysis** — check whether ambiguous phrasing triggered cross-document interference.
2. **Retrieval inspection** — verify whether the search engine returned a decoy chunk with high keyword overlap but from an obsolete document version.
3. **Ranking evaluation** — check whether the semantic re-ranker failed to penalize a hallucinated chunk score.
4. **Context & prompt review** — assess whether conflicting chunks confused the LLM's source attribution.
5. **LLM & citation generation** — determine whether the model fabricated a plausible-looking filename despite explicit instructions.

**Fix:** enforce strict system-prompt boundaries requiring the model to cite exact chunk metadata IDs supplied in context, paired with a post-generation citation-validation layer that rejects any output referencing a non-existent file.

---

## Author

**Aman Rai**
[GitHub](https://github.com/amanrai0067-maker) · [LinkedIn](https://www.linkedin.com/in/aman-rai-39101332a/)
