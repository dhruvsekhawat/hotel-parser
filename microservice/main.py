from fastapi import FastAPI, HTTPException, UploadFile, File, Form
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional, Dict, Any, List
import json
import tempfile
import os
import re
import asyncio
import logging
from pathlib import Path
import sys
import httpx
from database import supabase_client

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Add the script directory to path so we can import the extraction logic
sys.path.append(str(Path(__file__).parent.parent / "script"))

# Import the extraction functions from the Python script
try:
    from extract_hotel_quotes import (
        extract_text, 
        read_prompt, 
        get_client, 
        get_model, 
        call_llm, 
        normalize_result
    )
    logger.info("Successfully imported extraction functions")
except Exception as e:
    logger.error(f"Failed to import extraction functions: {e}")
    raise

app = FastAPI(
    title="Hotel Quote Parser Microservice",
    description="Extract structured hotel quote data from PDFs, HTML, and text",
    version="1.0.0"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class ExtractionResponse(BaseModel):
    success: bool
    data: Optional[Dict[str, Any]] = None
    error: Optional[str] = None
    sources: List[str] = []
    urls_found: List[str] = []

# URL detection patterns for proposal/quote links
URL_PATTERNS = [
    r'https?://[^\s]+proposal[^\s]*',
    r'https?://[^\s]+quote[^\s]*', 
    r'https?://[^\s]+booking[^\s]*',
    r'https?://[^\s]+estimate[^\s]*',
    r'https?://[^\s]+event[^\s]*',
    r'https?://[^\s]+meeting[^\s]*',
    r'https?://[^\s]+bookmarriott[^\s]*',  # Marriott specific
    r'https?://[^\s]+marriott[^\s]*',      # Marriott specific
    r'https?://[^\s]+view/[^\s]*',         # Generic view URLs
    r'https?://[^\s]+proposals/[^\s]*'     # Generic proposals
]

def extract_urls(text: str) -> List[str]:
    """Extract URLs from text using regex patterns."""
    logger.info(f"Extracting URLs from text (length: {len(text)})")
    urls = []
    for pattern in URL_PATTERNS:
        matches = re.findall(pattern, text, re.IGNORECASE)
        if matches:
            logger.info(f"Found {len(matches)} URLs with pattern {pattern}: {matches}")
        urls.extend(matches)
    unique_urls = list(set(urls))
    logger.info(f"Total unique URLs found: {len(unique_urls)}")
    return unique_urls

async def call_firecrawl_scrape(url: str) -> Optional[str]:
    """Call Firecrawl scrape API to get clean markdown from a URL"""
    logger.info(f"Attempting Firecrawl scrape for URL: {url}")
    
    # Get Firecrawl API key from environment
    firecrawl_api_key = os.getenv('FIRECRAWL_API_KEY')
    if not firecrawl_api_key:
        logger.warning("FIRECRAWL_API_KEY not found in environment")
        return None
    
    try:
        async with httpx.AsyncClient() as client:
            # Call Firecrawl scrape endpoint
            response = await client.post(
                "https://api.firecrawl.dev/v1/scrape",
                headers={
                    "Authorization": f"Bearer {firecrawl_api_key}",
                    "Content-Type": "application/json"
                },
                json={
                    "url": url,
                    "formats": ["markdown"],
                    "onlyMainContent": True,
                    "timeout": 60000  # 60 seconds
                },
                timeout=70.0
            )
            
            if response.status_code == 200:
                result = response.json()
                if result.get('success') and result.get('data', {}).get('markdown'):
                    markdown_content = result['data']['markdown']
                    logger.info(f"Successfully scraped {len(markdown_content)} characters of markdown")
                    logger.info(f"Markdown preview (first 500 chars): {markdown_content[:500]}")
                    
                    # Save the full markdown to a file for debugging
                    debug_file = f"/tmp/firecrawl_debug_{url.split('/')[-1]}.md"
                    try:
                        with open(debug_file, 'w', encoding='utf-8') as f:
                            f.write(f"# Firecrawl Scrape Debug\n")
                            f.write(f"URL: {url}\n")
                            f.write(f"Length: {len(markdown_content)} characters\n\n")
                            f.write(markdown_content)
                        logger.info(f"Full markdown saved to: {debug_file}")
                    except Exception as e:
                        logger.warning(f"Could not save debug file: {e}")
                    
                    return markdown_content
                else:
                    logger.error(f"Firecrawl scrape failed: {result}")
                    return None
            else:
                logger.error(f"Firecrawl scrape failed with status {response.status_code}: {response.text}")
                return None
                
    except Exception as e:
        logger.error(f"Firecrawl scrape failed: {e}")
        return None

async def process_text_content(content: str, source_type: str) -> Dict[str, Any]:
    """Process text content using the LLM extraction logic."""
    try:
        logger.info(f"Processing {source_type} content (length: {len(content)})")
        
        # Get the system prompt
        logger.info("Reading system prompt...")
        system_prompt = read_prompt(None)
        logger.info(f"System prompt loaded (length: {len(system_prompt)})")
        
        # Get OpenAI client
        logger.info("Initializing OpenAI client...")
        client = get_client()
        model = get_model(None)
        logger.info(f"Using model: {model}")
        
        # Call the LLM
        logger.info("Calling OpenAI API...")
        result = call_llm(client, model, system_prompt, content)
        logger.info("OpenAI API call completed successfully")
        
        # Add source metadata
        result["source"] = source_type
        result["content_length"] = len(content)
        
        logger.info(f"Text processing completed for {source_type}")
        return result
        
    except Exception as e:
        logger.error(f"Failed to process {source_type} content: {str(e)}")
        raise Exception(f"Failed to process {source_type} content: {str(e)}")

async def process_uploaded_file(file: UploadFile) -> Dict[str, Any]:
    """Process uploaded file (PDF/HTML) using the extraction logic."""
    try:
        logger.info(f"Processing uploaded file: {file.filename} (type: {file.content_type}, size: {file.size})")
        
        # Create temporary file
        with tempfile.NamedTemporaryFile(delete=False, suffix=Path(file.filename).suffix) as tmp_file:
            content = await file.read()
            logger.info(f"Read {len(content)} bytes from uploaded file")
            tmp_file.write(content)
            tmp_file_path = tmp_file.name
            logger.info(f"Created temporary file: {tmp_file_path}")
        
        try:
            # Extract text using the existing logic
            logger.info("Extracting text from file...")
            extracted_text = extract_text(tmp_file_path)
            logger.info(f"Extracted text (length: {len(extracted_text)})")
            
            # Process the extracted text
            result = await process_text_content(extracted_text, "file")
            result["filename"] = file.filename
            result["file_size"] = len(content)
            
            logger.info(f"File processing completed successfully")
            return result
            
        finally:
            # Clean up temp file
            os.unlink(tmp_file_path)
            logger.info(f"Cleaned up temporary file: {tmp_file_path}")
            
    except Exception as e:
        logger.error(f"Failed to process uploaded file: {str(e)}")
        raise Exception(f"Failed to process uploaded file: {str(e)}")

async def process_url_content(url: str) -> Dict[str, Any]:
    """Process content from URL using Firecrawl scrape + LLM."""
    try:
        logger.info(f"Processing URL content: {url}")
        
        # Call Firecrawl to scrape markdown
        markdown_content = await call_firecrawl_scrape(url)
        if markdown_content:
            logger.info("Firecrawl scrape successful, processing with LLM...")
            
            # Process the markdown content with our existing LLM prompt
            try:
                # Read the system prompt
                system_prompt = read_prompt(None)
                logger.info(f"System prompt loaded (length: {len(system_prompt)})")
                
                # Initialize OpenAI client
                client = get_client()
                model = get_model(None)  # Pass None for cli argument
                logger.info(f"Using model: {model}")
                
                # Call OpenAI API with the markdown content
                logger.info("Calling OpenAI API with scraped markdown...")
                logger.info(f"Markdown content length: {len(markdown_content)}")
                logger.info(f"System prompt length: {len(system_prompt)}")
                
                # Log a sample of the markdown content to see what we're processing
                logger.info(f"Markdown sample (first 1000 chars): {markdown_content[:1000]}")
                
                llm_result = call_llm(client, model, system_prompt, markdown_content)
                
                if llm_result:
                    # Normalize the result
                    normalized_result = normalize_result(llm_result)
                    # Add proposal URL to the data
                    normalized_result['proposal_url'] = url
                    logger.info(f"Successfully processed URL with LLM: {url}")
                    return normalized_result
                else:
                    logger.warning(f"LLM processing failed for URL: {url}")
                    raise Exception("LLM processing failed")
            except Exception as e:
                logger.error(f"Error processing markdown with LLM: {e}")
                raise Exception(f"LLM processing error: {e}")
        else:
            logger.warning(f"Failed to scrape markdown from URL: {url}")
            raise Exception("Failed to scrape markdown from URL")
        
    except Exception as e:
        logger.error(f"Failed to process URL {url}: {str(e)}")
        raise Exception(f"Failed to process URL {url}: {str(e)}")

def merge_extraction_results(extracted_data: Dict[str, Any]) -> Dict[str, Any]:
    """Merge extraction results using precedence rules."""
    logger.info(f"Merging extraction results from sources: {list(extracted_data.keys())}")
    
    if "proposal" in extracted_data and "email" in extracted_data:
        # Merge proposal and email data
        proposal = extracted_data["proposal"]
        email = extracted_data["email"]
        
        # Start with proposal data (authoritative for financials)
        merged = proposal.copy()
        
        # CRITICAL: Fix totals if they're 0 but we have the data in extras
        if merged.get("totals"):
            totals = merged["totals"]
            extras = merged.get("extras", {})
            
            # Fix guestroom total
            if totals.get("guestroom_total", {}).get("amount") == 0 and extras.get("guestroom_base"):
                guestroom_base = extras["guestroom_base"]
                guestroom_taxes = extras.get("guestroom_taxes_fees", 0)
                totals["guestroom_total"]["amount"] = guestroom_base + guestroom_taxes
                logger.info(f"Fixed guestroom total: {totals['guestroom_total']['amount']}")
            
            # Fix F&B total
            if totals.get("fnb_total", {}).get("amount") == 0 and extras.get("estimated_fnb_gross"):
                totals["fnb_total"]["amount"] = extras["estimated_fnb_gross"]
                logger.info(f"Fixed F&B total: {totals['fnb_total']['amount']}")
            elif totals.get("fnb_total", {}).get("amount") == 0 and extras.get("fnb_minimum"):
                # Calculate F&B gross if we have the minimum and rates
                fnb_min = extras["fnb_minimum"]
                service_rate = extras.get("service_rate_pct", 0)
                tax_rate = extras.get("tax_rate_pct", 0)
                
                if service_rate > 0 or tax_rate > 0:
                    service_charge = fnb_min * (service_rate / 100)
                    tax_on_service = service_charge * (tax_rate / 100) if service_rate > 0 else 0
                    tax_on_fnb = fnb_min * (tax_rate / 100)
                    estimated_gross = fnb_min + service_charge + tax_on_service + tax_on_fnb
                    
                    totals["fnb_total"]["amount"] = estimated_gross
                    extras["estimated_fnb_gross"] = estimated_gross
                    logger.info(f"Calculated F&B total: {estimated_gross}")
            
            # Fix total quote
            if totals.get("total_quote", {}).get("amount") == 0:
                guestroom = totals.get("guestroom_total", {}).get("amount", 0)
                meeting = totals.get("meeting_room_total", {}).get("amount", 0)
                fnb = totals.get("fnb_total", {}).get("amount", 0)
                total_quote = guestroom + meeting + fnb
                totals["total_quote"]["amount"] = total_quote
                logger.info(f"Calculated total quote: {total_quote}")
        
        # Fill gaps from email data
        if not merged.get("property") and email.get("property"):
            merged["property"] = email["property"]
        
        if not merged.get("program") and email.get("program"):
            merged["program"] = email["program"]
        
        # Merge concessions
        proposal_concessions = merged.get("concessions", [])
        email_concessions = email.get("concessions", [])
        merged["concessions"] = list(set(proposal_concessions + email_concessions))
        
        # Add source metadata
        merged["sources"] = ["proposal", "email"]
        
        logger.info("Successfully merged proposal and email data")
        return merged
        
    elif "proposal" in extracted_data:
        result = extracted_data["proposal"]
        result["sources"] = ["proposal"]
        logger.info("Using proposal data only")
        return result
        
    elif "email" in extracted_data:
        result = extracted_data["email"]
        result["sources"] = ["email"]
        logger.info("Using email data only")
        return result
        
    else:
        logger.error("No valid data to merge")
        raise Exception("No valid data to merge")

@app.get("/")
async def root():
    logger.info("Root endpoint called")
    return {"message": "Hotel Quote Parser Microservice", "status": "running"}

@app.get("/health")
async def health_check():
    logger.info("Health check endpoint called")
    return {"status": "healthy", "service": "hotel-quote-parser"}

@app.post("/extract", response_model=ExtractionResponse)
async def extract_quote(
    email_content: Optional[str] = Form(None),
    email_file: Optional[UploadFile] = File(None),
    proposal_file: Optional[UploadFile] = File(None),
    proposal_url: Optional[str] = Form(None)
):
    """
    Extract hotel quote data from multiple sources.
    
    Ideal workflow:
    1. Process email content (text or file)
    2. Process proposal file (PDF/HTML)
    3. Extract URLs from content
    4. Try Firecrawl for URLs, fallback to GPT
    5. Merge results with precedence rules
    """
    logger.info("=== Starting extraction process ===")
    logger.info(f"Received request with:")
    logger.info(f"  - email_content: {'Yes' if email_content else 'No'}")
    logger.info(f"  - email_file: {email_file.filename if email_file else 'No'}")
    logger.info(f"  - proposal_file: {proposal_file.filename if proposal_file else 'No'}")
    logger.info(f"  - proposal_url: {proposal_url if proposal_url else 'No'}")
    
    try:
        sources = []
        extracted_data = {}
        all_urls = []
        
        # Process email content if provided
        if email_content:
            logger.info("Processing email content...")
            sources.append("email")
            email_data = await process_text_content(email_content, "email")
            extracted_data["email"] = email_data
            
            # Extract URLs from email content
            email_urls = extract_urls(email_content)
            all_urls.extend(email_urls)
        
        # Process email file if provided
        if email_file:
            logger.info("Processing email file...")
            sources.append("email_file")
            email_data = await process_uploaded_file(email_file)
            extracted_data["email"] = email_data
            
            # Extract URLs from email file content if it's text-based
            if email_file.content_type in ['text/html', 'text/plain']:
                file_content = await email_file.read()
                file_text = file_content.decode('utf-8')
                file_urls = extract_urls(file_text)
                all_urls.extend(file_urls)
        
        # Process proposal file if provided
        if proposal_file:
            logger.info("Processing proposal file...")
            sources.append("proposal_file")
            proposal_data = await process_uploaded_file(proposal_file)
            extracted_data["proposal"] = proposal_data
            
            # Extract URLs from proposal content if it's text-based
            if proposal_file.content_type in ['text/html', 'text/plain']:
                file_content = await proposal_file.read()
                file_text = file_content.decode('utf-8')
                file_urls = extract_urls(file_text)
                all_urls.extend(file_urls)
        
        # Process proposal URL if provided directly
        if proposal_url:
            logger.info("Processing proposal URL...")
            sources.append("proposal_url")
            all_urls.append(proposal_url)
        
        # Remove duplicate URLs
        unique_urls = list(set(all_urls))
        logger.info(f"All URLs found: {unique_urls}")
        
        # Check if we have any extracted data and look for URLs in the AI response
        if not unique_urls and extracted_data:
            logger.info("No URLs found via regex, checking AI response for URLs...")
            for source_key, source_data in extracted_data.items():
                if isinstance(source_data, dict):
                    # Check extras.proposal_url
                    if source_data.get('extras', {}).get('proposal_url'):
                        url = source_data['extras']['proposal_url']
                        logger.info(f"Found URL in AI response: {url}")
                        unique_urls.append(url)
                        break
        
        # Try to process URLs with Firecrawl
        if unique_urls:
            logger.info("Attempting to process URLs with Firecrawl...")
            for url in unique_urls:
                try:
                    url_data = await process_url_content(url)
                    if url_data:
                        extracted_data["proposal"] = url_data
                        sources.append("proposal_url")
                        logger.info(f"Successfully processed URL: {url}")
                        break  # Use first successful URL
                except Exception as e:
                    logger.warning(f"Failed to process URL {url}: {e}")
                    continue
        
        if not extracted_data:
            logger.error("No content provided for extraction")
            raise HTTPException(status_code=400, detail="No content provided for extraction")
        
        # Merge the data using precedence rules
        logger.info("Merging extracted data...")
        merged_data = merge_extraction_results(extracted_data)
        
        # Store data in Supabase database
        try:
            logger.info("Storing data in Supabase database...")
            
            # Store the main request
            request_id = await supabase_client.store_hotel_quote_request(
                email_content=email_content,
                email_file_name=email_file.filename if email_file else None,
                email_file_size=email_file.size if email_file else None,
                proposal_file_name=proposal_file.filename if proposal_file else None,
                proposal_file_size=proposal_file.size if proposal_file else None,
                proposal_url=proposal_url,
                urls_found=unique_urls,
                sources_used=sources,
                content_length=len(email_content) if email_content else 0,
                firecrawl_scraped=len(unique_urls) > 0,
                firecrawl_content_length=0  # We'll get this from the actual scrape if needed
            )
            
            if request_id:
                # Store the quote data
                await supabase_client.store_hotel_quote_data(request_id, merged_data)
                
                # Store property info if available
                if merged_data.get('property'):
                    await supabase_client.store_property_info(request_id, merged_data['property'])
                
                # Store concessions if available
                if merged_data.get('concessions'):
                    await supabase_client.store_concessions(request_id, merged_data['concessions'])
                
                logger.info(f"Successfully stored all data in database with request ID: {request_id}")
            else:
                logger.warning("Failed to store data in database")
                
        except Exception as e:
            logger.error(f"Error storing data in database: {e}")
            # Don't fail the request if database storage fails
        
        logger.info("=== Extraction process completed successfully ===")
        
        return ExtractionResponse(
            success=True,
            data=merged_data,
            sources=sources,
            urls_found=unique_urls
        )
        
    except Exception as e:
        logger.error(f"=== Extraction process failed: {str(e)} ===")
        return ExtractionResponse(
            success=False,
            error=str(e),
            sources=[],
            urls_found=[]
        )

@app.post("/extract-text")
async def extract_from_text(content: str):
    """Extract hotel quote data from plain text content."""
    logger.info(f"Extract text endpoint called with content length: {len(content)}")
    try:
        result = await process_text_content(content, "text")
        logger.info("Text extraction completed successfully")
        return {"success": True, "data": result}
    except Exception as e:
        logger.error(f"Text extraction failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/recent-requests")
async def get_recent_requests(limit: int = 10):
    """Get recent hotel quote requests from the database."""
    try:
        requests = await supabase_client.get_recent_requests(limit)
        return {"success": True, "data": requests}
    except Exception as e:
        logger.error(f"Failed to get recent requests: {e}")
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    import uvicorn
    logger.info("Starting Hotel Quote Parser Microservice...")
    uvicorn.run(app, host="0.0.0.0", port=8000)
