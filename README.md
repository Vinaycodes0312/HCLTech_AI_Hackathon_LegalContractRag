# Bussiness Contract Search System 📄⚖️

A production-ready Retrieval-Augmented Generation (RAG) system for legal contract analysis using Google's Gemini API, FAISS vector search, and FastAPI.

## 🎯 Features

- **Gemini-Powered Intelligence**: Uses Gemini 1.5 Flash for fast, accurate contract analysis
- **Smart Document Processing**: Advanced chunking optimized for legal documents (1200 tokens with 200 overlap)
- **FAISS Vector Search**: Lightning-fast semantic retrieval
- **Citation Support**: Every answer includes source document and page references
- **Grounded Responses**: Hallucination prevention with strict grounding
- **Multi-Document Support**: Query across multiple contracts simultaneously
- **Clean Architecture**: Modular, swappable components

## 🏗️ Architecture

```
User Question → FastAPI → FAISS Retrieval → Gemini LLM → Grounded Answer + Citations
```

### Ingestion Flow
```
Upload PDFs → Extract Text → Chunk + Metadata → Gemini Embeddings → FAISS Index
```

## 📁 Project Structure

```
app/
├── ingestion/          # Document processing pipeline
│   ├── pdf_loader.py   # PDF text extraction
│   ├── chunker.py      # Smart chunking with metadata
│   ├── gemini_embedder.py  # Gemini embedding generation
│   └── pipeline.py     # End-to-end ingestion pipeline
├── retrieval/          # Vector search and retrieval
│   ├── vector_store.py # FAISS index management
│   └── retriever.py    # Semantic retrieval logic
├── rag/                # RAG core logic
│   ├── gemini_llm.py   # Gemini API integration
│   ├── prompt_templates.py  # Optimized prompts
│   └── qa_chain.py     # Question-answering chain
├── api/                # FastAPI endpoints
│   └── routes.py       # API routes
├── config.py           # Configuration management
└── main.py             # Application entry point
```

## 🚀 Quick Start

### 1. Clone and Setup

```bash
cd GenZ
python -m venv venv
venv\Scripts\activate  # Windows
pip install -r requirements.txt
```

### 2. Configure API Key

Copy `.env.example` to `.env` and add your Gemini API key:

```env
GEMINI_API_KEY=your_actual_api_key_here
```

Get your API key from: https://makersuite.google.com/app/apikey

### 3. Create Data Directories

```bash
mkdir data\uploads data\faiss_index
```

### 4. Run the Application

```bash
python -m uvicorn app.main:app --reload
```

The API will be available at: `http://localhost:8000`

## 📡 API Endpoints

### Upload Contract
```http
POST /upload
Content-Type: multipart/form-data

file: <PDF file>
```

### Query Contracts
```http
POST /query
Content-Type: application/json

{
  "question": "What is the termination clause?",
  "top_k": 5
}
```

### List Uploaded Contracts
```http
GET /contracts
```

### Clear Index
```http
DELETE /clear
```

## 💡 Usage Examples

### Upload a Contract
```python
import requests

with open("NDA_2024.pdf", "rb") as f:
    response = requests.post(
        "http://localhost:8000/upload",
        files={"file": f}
    )
print(response.json())
```

### Query the System
```python
response = requests.post(
    "http://localhost:8000/query",
    json={"question": "What are the payment terms?"}
)
print(response.json())
```

## 🎨 Features in Detail

### Smart Chunking
- **Chunk Size**: 1200 tokens (optimized for Gemini's context window)
- **Overlap**: 200 tokens (preserves context across chunks)
- **Metadata Tracking**: Contract name, page number for citations

### Hallucination Prevention
- Low temperature (0.1) for consistent outputs
- Strict grounding instructions
- Context-only answering
- Explicit uncertainty handling

### Citation System
Every answer includes:
- Direct answer
- Brief explanation
- Source citations (Contract Name + Page Number)

Example:
```
Answer: The contract can be terminated with 30 days written notice.

Explanation: Both parties have the right to terminate with advance notice.

Sources:
- NDA_2024.pdf (Page 12)
- Vendor_Agreement.pdf (Page 7)
```

## 🔧 Configuration

Edit `.env` to customize:

| Parameter | Default | Description |
|-----------|---------|-------------|
| `CHUNK_SIZE` | 1200 | Tokens per chunk |
| `CHUNK_OVERLAP` | 200 | Overlap between chunks |
| `TOP_K_RETRIEVAL` | 7 | Initial retrieval count |
| `TOP_K_FINAL` | 5 | Final chunks sent to LLM |
| `TEMPERATURE` | 0.1 | LLM temperature (lower = less creative) |
| `GENERATION_MODEL` | gemini-1.5-flash | Gemini model for answers |

## 🏆 Why This Wins Hackathons

✅ **Real LLM API Integration** - Not a toy project  
✅ **Clean Modular Architecture** - Easy to understand and extend  
✅ **Grounded Answers** - Production-ready accuracy  
✅ **Citations** - Traceable, verifiable responses  
✅ **Legal Domain Optimization** - Smart chunking for contracts  
✅ **Scalable Design** - Ready for cloud deployment  

## 🚀 Deployment

### Railway / Render
```bash
# Uses Procfile automatically
git push railway main
```

### GCP Cloud Run (Recommended for Gemini)
```bash
gcloud run deploy contract-rag \
  --source . \
  --platform managed \
  --region us-central1 \
  --allow-unauthenticated
```

## 📊 Performance Tips

1. **Cache Embeddings**: Embeddings are saved in FAISS index
2. **Batch Processing**: Upload multiple PDFs at once
3. **Index Persistence**: FAISS index saved to disk, loads instantly
4. **Async API**: FastAPI handles concurrent requests efficiently

##  License

MIT License - Use freely for hackathons and projects!

## 🤝 Contributing

Contributions welcome! This is a hackathon starter template.

## 📧 Support

For issues or questions, create an issue in the repository.

---

**Built with ❤️ using Gemini AI, FAISS, and FastAPI**
