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
