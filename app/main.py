from fastapi import FastAPI, Query, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from app.utils import Output, DocumentService, QdrantService

app = FastAPI(
    title="NormAI Query API",
    description="API for querying legal documents",
    version="1.0.0"
)


app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


document_service = None
qdrant_service = None

@app.on_event("startup")
async def startup_event():

    global document_service, qdrant_service
    
    try:
        document_service = DocumentService()
        
        docs = document_service.create_documents()
        
        qdrant_service = QdrantService() 
        qdrant_service.connect()
        
        qdrant_service.load(docs)
        
        
    except Exception as e:
        raise e


@app.get("/query", response_model=Output)
async def query_documents(query: str = Query(..., description="The query string to search for in legal documents")):
    if not qdrant_service:
        raise HTTPException(status_code=503, detail="Qdrant service not initialized")
    
    if not query or not query.strip():
        raise HTTPException(status_code=400, detail="Query string cannot be empty")
    
    try:
        result = qdrant_service.query(query.strip())
        return result
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error processing query: {str(e)}")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=80)