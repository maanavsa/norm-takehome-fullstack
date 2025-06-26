from pydantic import BaseModel
import qdrant_client
from llama_index.vector_stores.qdrant import QdrantVectorStore
from llama_index.embeddings.openai import OpenAIEmbedding
from llama_index.llms.openai import OpenAI
from llama_index.core.schema import Document
from llama_index.core import VectorStoreIndex
from dataclasses import dataclass
import PyPDF2
import os
import re
from llama_index.core import Settings
from llama_index.core.response_synthesizers import ResponseMode

key = os.environ['OPENAI_API_KEY']

@dataclass
class Input:
    query: str
    file_path: str

@dataclass
class Citation:
    source: str
    text: str

class Output(BaseModel):
    query: str
    response: str
    citations: list[Citation]

class DocumentService:

    """
    Update this service to load the pdf and extract its contents.
    The example code below will help with the data structured required
    when using the QdrantService.load() method below. Note: for this
    exercise, ignore the subtle difference between llama-index's 
    Document and Node classes (i.e, treat them as interchangeable).

    # example code
    def create_documents() -> list[Document]:

        docs = [
            Document(
                metadata={"Section": "Law 1"},
                text="Theft is punishable by hanging",
            ),
            Document(
                metadata={"Section": "Law 2"},
                text="Tax evasion is punishable by banishment.",
            ),
        ]

        return docs

     """
    
    def __init__(self, pdf_path: str = "docs/laws.pdf"):
        self.pdf_path = pdf_path
    
    def extract_text_from_pdf(self) -> str:
        try:
            with open(self.pdf_path, 'rb') as file:
                pdf_reader = PyPDF2.PdfReader(file)
                text = ""
                for page in pdf_reader.pages:
                    text += page.extract_text() + "\n"
                return text
        except Exception as e:
            print(f"Error reading PDF: {e}")
            return ""
    
    def parse_laws(self, text: str) -> list[tuple[str, str]]:
        # First, clean up the text by joining words that are on separate lines
        lines = text.split('\n')
        cleaned_lines = []
        current_line = ""
        
        for line in lines:
            line = line.strip()
            if not line:
                if current_line:
                    cleaned_lines.append(current_line)
                    current_line = ""
                continue
            
            # If this looks like a section header (starts with number and dot)
            if re.match(r'^\d+\.', line):
                if current_line:
                    cleaned_lines.append(current_line)
                current_line = line
            # If this looks like a title (all caps or starts with capital letter)
            elif re.match(r'^[A-Z][A-Z\s]+$', line) or re.match(r'^[A-Z][a-z]+', line):
                if current_line:
                    cleaned_lines.append(current_line)
                current_line = line
            else:
                # Regular content - add to current line
                if current_line:
                    current_line += " " + line
                else:
                    current_line = line
        
        if current_line:
            cleaned_lines.append(current_line)
        
        # Now parse the cleaned lines
        laws = []
        current_law = ""
        current_content = ""
        
        for line in cleaned_lines:
            line = line.strip()
            if not line:
                continue
            
            # Check if this is a new section header
            if (re.match(r'^(Law|Section|Article)\s+\d+', line, re.IGNORECASE) or
                re.match(r'^\d+\.$', line) or  # Just a number like "6."
                re.match(r'^\d+\.\d+', line) or  # Number like "6.1."
                re.match(r'^\d+\.\d+\.\d+', line) or  # Number like "6.1.1."
                re.match(r'^[A-Z][A-Z\s]+$', line)):  # All caps title
                
                # Save previous law if exists and has content
                if current_law and current_content.strip():
                    laws.append((current_law, current_content.strip()))
                
                current_law = line
                current_content = ""
            else:
                # Regular content
                if current_law:
                    current_content += line + " "
                else:
                    current_content += line + " "
        
        # Save the last law if it has content
        if current_law and current_content.strip():
            laws.append((current_law, current_content.strip()))
        
        # Filter out laws that are just headers without substantive content
        filtered_laws = []
        for law_title, content in laws:
            # Skip if it's just a header with no real content (like "6. Thievery")
            if (re.match(r'^\d+\.$', law_title) and 
                len(content.split()) < 5):  # Very short content
                continue
            filtered_laws.append((law_title, content))
        
        return filtered_laws
    
    def create_documents(self) -> list[Document]:
        text = self.extract_text_from_pdf()
        if not text:
            return []
        
        law_sections = self.parse_laws(text)
        
        docs = []
        for i, (law_title, content) in enumerate(law_sections):
            content = re.sub(r'\s+', ' ', content).strip()
            
            if content:
                doc = Document(
                    metadata={"Section": law_title},
                    text=content
                )
                docs.append(doc)
        
        if not docs:
            cleaned_text = re.sub(r'\s+', ' ', text).strip()
            if cleaned_text:
                doc = Document(
                    metadata={"Section": "Complete Document"},
                    text=cleaned_text
                )
                docs.append(doc)
        return docs

class QdrantService:
    def __init__(self, k: int = 2):
        self.index = None
        self.k = k
    
    def connect(self) -> None:
        client = qdrant_client.QdrantClient(location=":memory:")
                
        vstore = QdrantVectorStore(client=client, collection_name='temp')

        Settings.llm = OpenAI(api_key=key, model="gpt-4")
        Settings.embed_model = OpenAIEmbedding(api_key=key)

        self.index = VectorStoreIndex.from_vector_store(vector_store=vstore)

    def load(self, docs: list[Document]):
        if self.index is None:
            raise ValueError("Index is not initialized. Call connect() first.")
        try:
            self.index.insert_nodes(docs)
    
        except Exception as e:
            print(f"Error loading documents: {e}")
            raise e
    
    def query(self, query_str: str) -> Output:

        """
        This method needs to initialize the query engine, run the query, and return
        the result as a pydantic Output class. This is what will be returned as
        JSON via the FastAPI endpount. Fee free to do this however you'd like, but
        a its worth noting that the llama-index package has a CitationQueryEngine...

        Also, be sure to make use of self.k (the number of vectors to return based
        on semantic similarity).

        # Example output object
        citations = [
            Citation(source="Law 1", text="Theft is punishable by hanging"),
            Citation(source="Law 2", text="Tax evasion is punishable by banishment."),
        ]

        output = Output(
            query=query_str, 
            response=response_text, 
            citations=citations
            )
        
        return output

        """
        from llama_index.core.query_engine import CitationQueryEngine
        
        if self.index is None:
            raise ValueError("Index is not initialized. Call connect() and load() first.")
        
        query_engine = CitationQueryEngine.from_args(
            index=self.index,
            similarity_top_k=self.k,
            response_mode=ResponseMode.COMPACT
        )
        
        response = query_engine.query(query_str)
        
        citations = []
        if hasattr(response, 'source_nodes') and response.source_nodes:
            for node in response.source_nodes:
                source = node.metadata.get("Section", "Unknown Section")
                text = node.text
                # Clean up any "Source X:" prefixes
                text = re.sub(r'^Source \d+:\s*', '', text)
                citations.append(Citation(source=source, text=text))
        
        output = Output(
            query=query_str,
            response=str(response),
            citations=citations
        )
        
        return output

if __name__ == "__main__":
    # Example workflow
    doc_serivce = DocumentService() # implemented
    docs = doc_serivce.create_documents() # NOT implemented

    index = QdrantService() # implemented
    index.connect() # implemented
    index.load(docs) # implemented

    index.query("what happens if I steal?") # NOT implemented





