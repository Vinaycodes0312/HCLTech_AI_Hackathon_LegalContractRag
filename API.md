# API Documentation 📡

## Base URL

```
Development: http://localhost:8000
Production: https://your-app.railway.app
```

All API endpoints are prefixed with `/api/`.

---

## Endpoints

### 1. Health Check

**GET** `/api/health`

Check system health and component status.

#### Response
```json
{
  "status": "healthy",
  "components": {
    "vector_store": true,
    "pipeline": true,
    "qa_chain": true
  },
  "vector_store_stats": {
    "total_documents": 150,
    "dimension": 768,
    "index_size": 150
  }
}
```

---

### 2. Upload Contract

**POST** `/api/upload`

Upload and process a PDF contract.

#### Request
- **Content-Type**: `multipart/form-data`
- **Body**: 
  - `file`: PDF file (max 10MB)

#### Example (cURL)
```bash
curl -X POST http://localhost:8000/api/upload \
  -F "file=@contract.pdf"
```

#### Example (Python)
```python
import requests

with open("contract.pdf", "rb") as f:
    response = requests.post(
        "http://localhost:8000/api/upload",
        files={"file": f}
    )
print(response.json())
```

#### Response
```json
{
  "message": "File uploaded and processed successfully",
  "file_name": "NDA_2024.pdf",
  "stats": {
    "file_name": "NDA_2024.pdf",
    "pages_processed": 12,
    "chunks_created": 25,
    "embeddings_generated": 25,
    "status": "success"
  }
}
```

---

### 3. Query Contracts

**POST** `/api/query`

Ask questions about uploaded contracts.

#### Request
```json
{
  "question": "What are the payment terms?",
  "top_k": 5  // Optional, default: 5
}
```

#### Example
```bash
curl -X POST http://localhost:8000/api/query \
  -H "Content-Type: application/json" \
  -d '{
    "question": "What are the payment terms?",
    "top_k": 5
  }'
```

#### Response
```json
{
  "answer": "**Answer:**\nThe payment terms specify net 30 days...\n\n**Explanation:**\nBased on the contract, payment is due within 30 days...\n\n**Sources:**\n- Vendor_Agreement.pdf (Page 3)\n- NDA_2024.pdf (Page 7)",
  "sources": [
    {
      "contract": "Vendor_Agreement.pdf",
      "page": 3
    },
    {
      "contract": "NDA_2024.pdf",
      "page": 7
    }
  ],
  "question": "What are the payment terms?",
  "success": true
}
```

---

### 4. Compare Contracts

**POST** `/api/compare`

Compare clauses across multiple contracts.

#### Request
```json
{
  "question": "Compare termination clauses across all contracts",
  "top_k": 7  // Optional
}
```

#### Example
```bash
curl -X POST http://localhost:8000/api/compare \
  -H "Content-Type: application/json" \
  -d '{
    "question": "Compare termination clauses across all contracts"
  }'
```

#### Response
```json
{
  "answer": "**Comparison Summary:**\nTermination clause comparison across 3 contracts...\n\n**Findings:**\n...",
  "sources": [...],
  "question": "Compare termination clauses",
  "success": true
}
```

---

### 5. Extract Clauses

**POST** `/api/extract`

Extract specific clause types from contracts.

#### Request
```json
{
  "clause_type": "payment terms",
  "top_k": 5  // Optional
}
```

#### Example
```bash
curl -X POST http://localhost:8000/api/extract \
  -H "Content-Type: application/json" \
  -d '{
    "clause_type": "payment terms"
  }'
```

#### Response
```json
{
  "answer": "**Clause Type:** payment terms\n\n**Extracted Clauses:**\n\n**Contract: Vendor_Agreement.pdf (Page 3)**\n- Payment due within 30 days...",
  "sources": [...],
  "clause_type": "payment terms",
  "success": true
}
```

---

### 6. List Contracts

**GET** `/api/contracts`

Get list of all uploaded contracts.

#### Example
```bash
curl http://localhost:8000/api/contracts
```

#### Response
```json
{
  "contracts": [
    {
      "name": "NDA_2024.pdf",
      "size": 245760,
      "uploaded": 1708543200.0
    },
    {
      "name": "Vendor_Agreement.pdf",
      "size": 512000,
      "uploaded": 1708543300.0
    }
  ],
  "total": 2
}
```

---

### 7. Get Statistics

**GET** `/api/stats`

Get system statistics and configuration.

#### Example
```bash
curl http://localhost:8000/api/stats
```

#### Response
```json
{
  "vector_store": {
    "total_documents": 150,
    "dimension": 768,
    "index_size": 150
  },
  "contracts_uploaded": 5,
  "settings": {
    "chunk_size": 1200,
    "chunk_overlap": 200,
    "top_k_retrieval": 7,
    "embedding_model": "models/embedding-001",
    "generation_model": "gemini-1.5-flash"
  }
}
```

---

### 8. Clear Index

**DELETE** `/api/clear`

Clear the entire vector store index.

⚠️ **Warning**: This action cannot be undone.

#### Example
```bash
curl -X DELETE http://localhost:8000/api/clear
```

#### Response
```json
{
  "message": "Vector store cleared successfully",
  "status": "success"
}
```

---

### 9. Delete Contract

**DELETE** `/api/contracts/{filename}`

Delete a specific uploaded contract file.

#### Example
```bash
curl -X DELETE http://localhost:8000/api/contracts/NDA_2024.pdf
```

#### Response
```json
{
  "message": "Contract 'NDA_2024.pdf' deleted successfully",
  "status": "success"
}
```

---

## Error Responses

All endpoints return errors in this format:

```json
{
  "detail": "Error message here"
}
```

### Common HTTP Status Codes

| Code | Meaning |
|------|---------|
| 200 | Success |
| 400 | Bad Request (invalid input) |
| 404 | Not Found |
| 500 | Internal Server Error |

---

## Rate Limiting

Currently no rate limiting is enforced in development.

For production deployment, consider:
- 100 requests/minute per IP
- 1000 requests/hour per API key

---

## Authentication (Future)

To add authentication:

1. **API Key Method**
```bash
curl -H "X-API-Key: your_key_here" \
  http://localhost:8000/api/query
```

2. **JWT Method**
```bash
curl -H "Authorization: Bearer your_jwt_token" \
  http://localhost:8000/api/query
```

---

## Interactive Documentation

Visit these URLs for interactive API documentation:

- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc

---

## Python SDK Example

```python
import requests

class ContractRAGClient:
    def __init__(self, base_url="http://localhost:8000"):
        self.base_url = base_url
        self.api_url = f"{base_url}/api"
    
    def upload(self, file_path):
        with open(file_path, 'rb') as f:
            response = requests.post(
                f"{self.api_url}/upload",
                files={"file": f}
            )
        return response.json()
    
    def query(self, question, top_k=5):
        response = requests.post(
            f"{self.api_url}/query",
            json={"question": question, "top_k": top_k}
        )
        return response.json()
    
    def compare(self, question, top_k=7):
        response = requests.post(
            f"{self.api_url}/compare",
            json={"question": question, "top_k": top_k}
        )
        return response.json()
    
    def extract(self, clause_type, top_k=5):
        response = requests.post(
            f"{self.api_url}/extract",
            json={"clause_type": clause_type, "top_k": top_k}
        )
        return response.json()
    
    def get_stats(self):
        response = requests.get(f"{self.api_url}/stats")
        return response.json()


# Usage
client = ContractRAGClient()

# Upload contract
result = client.upload("contract.pdf")
print(result)

# Ask question
answer = client.query("What are the payment terms?")
print(answer['answer'])
print("Sources:", answer['sources'])

# Get stats
stats = client.get_stats()
print(f"Total documents: {stats['vector_store']['total_documents']}")
```

---

## JavaScript/TypeScript Example

```javascript
class ContractRAGClient {
  constructor(baseUrl = 'http://localhost:8000') {
    this.apiUrl = `${baseUrl}/api`;
  }

  async upload(file) {
    const formData = new FormData();
    formData.append('file', file);
    
    const response = await fetch(`${this.apiUrl}/upload`, {
      method: 'POST',
      body: formData
    });
    
    return response.json();
  }

  async query(question, topK = 5) {
    const response = await fetch(`${this.apiUrl}/query`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json'
      },
      body: JSON.stringify({ question, top_k: topK })
    });
    
    return response.json();
  }

  async getStats() {
    const response = await fetch(`${this.apiUrl}/stats`);
    return response.json();
  }
}

// Usage
const client = new ContractRAGClient();

// Ask question
const answer = await client.query("What are the payment terms?");
console.log(answer.answer);
console.log('Sources:', answer.sources);
```

---

Happy coding! 🚀
