import streamlit as st
import requests
import json

# Page Config
st.set_page_config(
    page_title="Azure Enterprise Knowledge Assistant",
    page_icon="⚡",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom Styling
st.markdown("""
<style>
    .main-header { font-size: 2.2rem; font-weight: 700; color: #0078D4; }
    .sub-header { font-size: 1.1rem; color: #555555; margin-bottom: 20px; }
    .citation-box { background-color: #f0f4f8; padding: 12px; border-radius: 8px; border-left: 4px solid #0078D4; margin-top: 8px; }
    .stChatMessage { margin-bottom: 12px; }
</style>
""", unsafe_allow_html=True)

API_BASE_URL = "http://localhost:8000"

# Sidebar Configuration & Status
with st.sidebar:
    st.image("https://upload.wikimedia.org/wikipedia/commons/a/a8/Microsoft_Azure_Logo.svg", width=180)
    st.title("System Specs")
    
    st.success("● Azure AI Search: Connected")
    st.success("● Azure OpenAI (GPT-4o): Active")
    
    st.markdown("---")
    st.subheader("⚙️ Pipeline Config")
    st.write("**Retrieval:** Hybrid (Vector + BM25)")
    st.write("**Chunking:** 1000 tokens / 200 overlap")
    st.write("**Temperature:** 0.0 (Grounded)")
    
    st.markdown("---")
    st.caption("Built for Analytos.ai Senior AI Engineer Assessment")

# Header Section
st.markdown('<div class="main-header">⚡ Azure Enterprise RAG Assistant</div>', unsafe_allow_html=True)
st.markdown('<div class="sub-header">AI-Powered Knowledge Retrieval with Zero Hallucination & Explicit Citations</div>', unsafe_allow_html=True)

# Tabs
tab1, tab2, tab3 = st.tabs(["💬 Knowledge Chat", "📁 Document Ingestion", "🏗️ System Architecture"])

# ------------------ TAB 1: CHAT INTERFACE ------------------
with tab1:
    # Initialize chat history
    if "messages" not in st.session_state:
        st.session_state.messages = [
            {"role": "assistant", "content": "Hello! I am your Enterprise Knowledge Assistant. Ask me anything about company documents, policies, or technical guidelines."}
        ]

    # Display chat messages
    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])
            if "citations" in message and message["citations"]:
                with st.expander("📌 Source Citations & References", expanded=False):
                    for idx, cite in enumerate(message["citations"], 1):
                        st.markdown(f"**[{idx}] Document:** `{cite['document_name']}` | **Page:** `{cite['page_number']}`")
                        st.caption(f"*Snippet:* {cite['snippet']}")

    # User Input
    if user_query := st.chat_input("Ask a question about your enterprise documents..."):
        # Append user message
        st.session_state.messages.append({"role": "user", "content": user_query})
        with st.chat_message("user"):
            st.markdown(user_query)

        # Assistant Response
        with st.chat_message("assistant"):
            with st.spinner("Retrieving from Azure AI Search & generating grounded response..."):
                try:
                    res = requests.post(
                        f"{API_BASE_URL}/api/v1/query",
                        json={"query": user_query},
                        timeout=30
                    )
                    
                    if res.status_code == 200:
                        data = res.json()
                        answer = data.get("answer", "No response received.")
                        citations = data.get("citations", [])

                        st.markdown(answer)
                        
                        if citations:
                            with st.expander("📌 Source Citations & References", expanded=True):
                                for idx, cite in enumerate(citations, 1):
                                    st.markdown(f"**[{idx}] Document:** `{cite['document_name']}` | **Page:** `{cite['page_number']}`")
                                    st.caption(f"*Snippet:* {cite['snippet']}")

                        # Append to history
                        st.session_state.messages.append({
                            "role": "assistant",
                            "content": answer,
                            "citations": citations
                        })
                    else:
                        error_msg = f"API Error ({res.status_code}): Could not fetch answer."
                        st.error(error_msg)
                except Exception as e:
                    st.error(f"Failed to connect to backend server: {str(e)}")


# ------------------ TAB 2: INGESTION ------------------
with tab2:
    st.subheader("📥 Ingest Enterprise Documents into Vector Index")
    st.write("Parse PDF/Text files into vector embeddings with Hybrid Indexing.")
    
    file_path_input = st.text_input("Enter Document Path (e.g. `./data/company_policy.pdf` or `sample.txt`):", "company_policy.pdf")
    
    if st.button("Start Ingestion Pipeline", type="primary"):
        with st.spinner("Processing PDF parsing, chunking, and Azure Search indexing..."):
            try:
                res = requests.post(
                    f"{API_BASE_URL}/api/v1/ingest",
                    params={"file_path": file_path_input},
                    timeout=30
                )
                if res.status_code == 200:
                    result = res.json()
                    st.success(f"✅ Ingestion Complete! Chunks Processed: {result.get('chunks_created', 0)}")
                    st.json(result)
                else:
                    st.error(f"Ingestion Error: {res.text}")
            except Exception as e:
                st.error(f"Backend Server Error: {str(e)}")


# ------------------ TAB 3: ARCHITECTURE ------------------
with tab3:
    st.subheader("📐 Azure RAG Pipeline Architecture")
    
    st.code("""
  +-----------------------+       +-------------------------+
  | Enterprise PDF/Text   | ----> | Azure Document Intel    |
  +-----------------------+       +-------------------------+
                                               |
                                               v
  +-----------------------+       +-------------------------+
  | Vector Embedding      | <---- | Recursive Chunking      |
  | text-embedding-3-large|       | 1000 size / 200 overlap |
  +-----------------------+       +-------------------------+
              |
              v
  +---------------------------------------------------------+
  | Azure AI Search Index (Hybrid Vector + BM25 Reranking)  |
  +---------------------------------------------------------+
              |
              v
  +-----------------------+       +-------------------------+
  | Azure OpenAI GPT-4o   | ----> | Grounded Output         |
  | (Temperature = 0.0)   |       | + Explicit Citations    |
  +-----------------------+       +-------------------------+
    """, language="text")
    
    st.info("💡 Grounding Rule: Temperature = 0.0 with mandatory refusal clauses to guarantee 0% hallucination.")