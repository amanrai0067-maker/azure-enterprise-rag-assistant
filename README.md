# Azure Enterprise Knowledge Assistant (Production-Grade RAG Pipeline)

An enterprise-ready **Retrieval-Augmented Generation (RAG)** solution built to demonstrate high-accuracy document retrieval, strict factual grounding, and resilience against common RAG failure modes. Architected on **Python**, **FastAPI**, **Streamlit**, **Azure OpenAI**, and **Azure AI Search**.

---

## Executive Summary

Standard RAG pipelines often suffer from hallucinated responses, inaccurate chunk retrieval, and loss of context in multi-turn conversations. This project implements advanced retrieval strategies—including **Hybrid Search**, **Metadata Filtering**, **Conversational Query Rewriting**, and **Strict System Grounding**—to achieve near-zero hallucination rates and high retrieval accuracy for enterprise documentation.

---

## Key System Architecture

```text
[ Document Ingestion Pipeline ]
  PDF Upload ➔ Text Parsing ➔ Recursive Chunking ➔ Embedding Generation ➔ Azure AI Search Index
                                                                                  │
[ Retrieval & Generation Pipeline ]                                                │
  User Prompt ➔ Query Rewriter ➔ Hybrid Search (Dense + Sparse) ◄─────────────────┘
                                         │
                                Context Synthesis
                                         │
                                Azure OpenAI (GPT-4o) ➔ Grounded Answer + Source Citations
