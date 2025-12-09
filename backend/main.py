"""
FastAPI Backend for Regulatory Document Explorer
Integrates with SEC Edgar API and Google Gemini AI
"""

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Optional
import httpx
import os
import json
from datetime import datetime
import xml.etree.ElementTree as ET
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Initialize FastAPI app
app = FastAPI(
    title="Regulatory Document Explorer API",
    description="API for fetching and analyzing regulatory documents",
    version="1.0.0"
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",  # Vite default
        "http://localhost:3000",  # Alternative
        "http://127.0.0.1:5173",
        "http://127.0.0.1:3000",
        "*"  # Allow all (remove in production)
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Configure Gemini AI - Read from environment variable
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
if not GEMINI_API_KEY:
    print("WARNING: GEMINI_API_KEY not found in .env file!")
    print("Please add GEMINI_API_KEY=your-key-here to your .env file")

GEMINI_API_URL = "https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash:generateContent"

# Pydantic models
class Document(BaseModel):
    id: str
    title: str
    date: str
    agency: str
    type: str
    summary: str
    link: str
    fullText: str

class SearchRequest(BaseModel):
    query: str
    documents: List[Document]

class SummaryRequest(BaseModel):
    document: Document

class SearchResponse(BaseModel):
    relevantDocs: List[Document]
    message: str

class SummaryResponse(BaseModel):
    summary: str


@app.get("/")
async def root():
    """Health check endpoint"""
    return {
        "status": "online",
        "message": "Regulatory Document Explorer API",
        "version": "1.0.0"
    }


@app.get("/api/documents", response_model=List[Document])
async def get_documents():
    """
    Fetch regulatory documents from SEC Edgar API
    Returns a list of recent SEC filings
    """
    try:
        # Fetch from SEC Edgar API
        async with httpx.AsyncClient() as client:
            response = await client.get(
                "https://www.sec.gov/cgi-bin/browse-edgar",
                params={
                    "action": "getcurrent",
                    "CIK": "",
                    "type": "10-K",
                    "company": "",
                    "dateb": "",
                    "owner": "exclude",
                    "start": "0",
                    "count": "40",
                    "output": "atom"
                },
                headers={
                    "User-Agent": "Regulatory Explorer demo@example.com"
                },
                timeout=10.0
            )
        
        if response.status_code != 200:
            raise HTTPException(status_code=502, detail="Failed to fetch from SEC API")
        
        # Parse XML response
        root = ET.fromstring(response.text)
        namespace = {'atom': 'http://www.w3.org/2005/Atom'}
        
        documents = []
        entries = root.findall('.//atom:entry', namespace)[:20]
        
        for idx, entry in enumerate(entries):
            title_elem = entry.find('atom:title', namespace)
            updated_elem = entry.find('atom:updated', namespace)
            summary_elem = entry.find('atom:summary', namespace)
            link_elem = entry.find('atom:link', namespace)
            
            title = title_elem.text if title_elem is not None else "Untitled"
            updated = updated_elem.text if updated_elem is not None else datetime.now().isoformat()
            summary = summary_elem.text if summary_elem is not None else "No summary available"
            link = link_elem.get('href') if link_elem is not None else "#"
            
            # Parse date
            try:
                date_obj = datetime.fromisoformat(updated.replace('Z', '+00:00'))
                formatted_date = date_obj.strftime('%Y-%m-%d')
            except:
                formatted_date = datetime.now().strftime('%Y-%m-%d')
            
            # Determine document type
            doc_type = "10-K"
            if "10-Q" in title:
                doc_type = "10-Q"
            elif "8-K" in title:
                doc_type = "8-K"
            
            documents.append(Document(
                id=f"doc-{idx}",
                title=title[:100],
                date=formatted_date,
                agency="SEC",
                type=doc_type,
                summary=summary[:200] + "...",
                link=link,
                fullText=summary
            ))
        
        return documents
    
    except httpx.TimeoutException:
        # Return mock data if SEC API fails
        return generate_mock_documents()
    except Exception as e:
        print(f"Error fetching documents: {e}")
        # Return mock data as fallback
        return generate_mock_documents()


def generate_mock_documents() -> List[Document]:
    """Generate mock regulatory documents for demonstration"""
    agencies = ["SEC", "FDA", "FCC", "EPA"]
    types = ["10-K", "10-Q", "8-K", "Drug Approval", "Compliance Report"]
    
    documents = []
    for i in range(15):
        agency = agencies[i % len(agencies)]
        doc_type = types[i % len(types)]
        
        documents.append(Document(
            id=f"doc-{i}",
            title=f"Regulatory Filing {i + 1} - {doc_type}",
            date=datetime.now().strftime('%Y-%m-%d'),
            agency=agency,
            type=doc_type,
            summary=f"This is a regulatory document from {agency} regarding compliance and reporting requirements. The document contains important information about regulatory standards and obligations.",
            link="#",
            fullText=f"This regulatory document from {agency} provides comprehensive information about compliance requirements, reporting obligations, and regulatory standards. It includes detailed guidelines for organizations to follow and maintain regulatory compliance. The document outlines specific procedures, timelines, and requirements that must be met to ensure full compliance with applicable regulations."
        ))
    
    return documents


async def call_gemini_api(prompt: str) -> str:
    """
    Call Gemini API directly via HTTP
    """
    try:
        payload = {
            "contents": [{
                "parts": [{
                    "text": prompt
                }]
            }]
        }
        
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{GEMINI_API_URL}?key={GEMINI_API_KEY}",
                json=payload,
                timeout=30.0
            )
            
            if response.status_code != 200:
                raise Exception(f"Gemini API error: {response.status_code}")
            
            data = response.json()
            
            # Extract text from response
            if "candidates" in data and len(data["candidates"]) > 0:
                candidate = data["candidates"][0]
                if "content" in candidate and "parts" in candidate["content"]:
                    parts = candidate["content"]["parts"]
                    if len(parts) > 0 and "text" in parts[0]:
                        return parts[0]["text"]
            
            raise Exception("Unexpected response format from Gemini API")
    
    except Exception as e:
        raise Exception(f"Failed to call Gemini API: {str(e)}")


@app.post("/api/search", response_model=SearchResponse)
async def ai_search(request: SearchRequest):
    """
    AI-powered natural language search using Gemini
    Analyzes search query and returns relevant documents
    """
    try:
        # Create prompt for Gemini
        docs_list = "\n".join([
            f"{idx}. {doc.title} ({doc.agency}, {doc.type}, {doc.date})"
            for idx, doc in enumerate(request.documents)
        ])
        
        prompt = f"""Given this natural language search query: "{request.query}"

And these available regulatory documents:
{docs_list}

Analyze the search query and identify which documents are most relevant. 
Consider document titles, agencies, types, and dates.
Respond with ONLY a JSON array of document indices (0-based) that match the query, ordered by relevance.

Example format: [0, 3, 7, 12]

If no documents match, return an empty array: []"""

        # Call Gemini API
        result_text = await call_gemini_api(prompt)
        
        # Clean up the response
        result_text = result_text.replace('```json', '').replace('```', '').strip()
        
        # Parse JSON response
        indices = json.loads(result_text)
        
        # Get relevant documents
        relevant_docs = [
            request.documents[idx] 
            for idx in indices 
            if 0 <= idx < len(request.documents)
        ]
        
        message = f"Found {len(relevant_docs)} relevant documents"
        if len(relevant_docs) == 0:
            message = "No documents matched your search query"
        
        return SearchResponse(
            relevantDocs=relevant_docs,
            message=message
        )
    
    except Exception as e:
        print(f"AI search error: {e}")
        # Fallback to simple text search
        query_lower = request.query.lower()
        relevant_docs = [
            doc for doc in request.documents
            if query_lower in doc.title.lower() or
               query_lower in doc.summary.lower() or
               query_lower in doc.agency.lower() or
               query_lower in doc.type.lower()
        ]
        
        return SearchResponse(
            relevantDocs=relevant_docs,
            message=f"Found {len(relevant_docs)} documents (using fallback search)"
        )


@app.post("/api/summarize", response_model=SummaryResponse)
async def generate_summary(request: SummaryRequest):
    """
    Generate AI-powered compliance summary using Gemini
    Analyzes document and provides key insights
    """
    try:
        doc = request.document
        
        prompt = f"""Analyze this regulatory document and provide a comprehensive compliance analysis:

Title: {doc.title}
Agency: {doc.agency}
Type: {doc.type}
Date: {doc.date}
Content: {doc.fullText}

Please provide:
1. Brief Summary (2-3 sentences)
2. Key Compliance Points (3-5 bullet points)
3. Potential Impact (1-2 sentences)

Format your response in a clear, structured manner."""

        # Call Gemini API
        summary = await call_gemini_api(prompt)
        
        return SummaryResponse(summary=summary)
    
    except Exception as e:
        print(f"Summary generation error: {e}")
        return SummaryResponse(
            summary=f"Unable to generate AI summary at this time. Error: {str(e)}\n\nPlease try again later or check your API configuration."
        )


@app.get("/api/agencies")
async def get_agencies():
    """Get list of available agencies"""
    return {
        "agencies": ["SEC", "FDA", "FCC", "EPA"]
    }


# Run with: uvicorn main:app --reload --port 8000
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)