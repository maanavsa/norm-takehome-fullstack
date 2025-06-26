# Westerosi Capital Group

---

## Setup and Run Instructions

```bash
docker build -t norm-ai-takehome .
docker run -p 80:80 -e OPENAI_API_KEY=your_api_key norm-ai-takehome
```

### **Query the Application Using Swagger UI**

Once the application is running:

1. Open your browser and go to: [http://localhost:80/docs](http://localhost:80/docs)
2. Use the interactive Swagger UI to submit queries to `/query`

---

## 📄 Assumptions, Design Choices, and Important Details

### Assumptions
- The legal document corpus is provided as a single PDF (`docs/laws.pdf`).
- The application is intended for demonstration and evaluation, not for production use as-is.

### Design Choices
- **CORS** is set to allow all origins for ease of testing (should be restricted in production).

### Important Details
- **PDF Parsing**: The `DocumentService` parses the PDF into logical law sections using regex. If no structure is found, it falls back to paragraph/sentence splitting.
- **Querying**: The `/query` endpoint uses semantic search to find the top-k most relevant law sections and returns them with citations.
