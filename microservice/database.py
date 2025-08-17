import os
import json
import logging
from typing import Dict, Any, Optional, List
from datetime import datetime
import httpx

logger = logging.getLogger(__name__)

class SupabaseClient:
    def __init__(self):
        self.supabase_url = os.getenv('SUPABASE_URL')
        self.supabase_key = os.getenv('SUPABASE_ANON_KEY')
        
        if not self.supabase_url or not self.supabase_key:
            logger.warning("Supabase credentials not found in environment variables")
            self.enabled = False
        else:
            self.enabled = True
            logger.info("Supabase client initialized")
    
    async def store_hotel_quote_request(
        self,
        email_content: Optional[str] = None,
        email_file_name: Optional[str] = None,
        email_file_size: Optional[int] = None,
        proposal_file_name: Optional[str] = None,
        proposal_file_size: Optional[int] = None,
        proposal_url: Optional[str] = None,
        urls_found: Optional[List[str]] = None,
        sources_used: Optional[List[str]] = None,
        content_length: Optional[int] = None,
        firecrawl_scraped: bool = False,
        firecrawl_content_length: Optional[int] = None
    ) -> Optional[str]:
        """Store a new hotel quote request and return the request ID"""
        if not self.enabled:
            logger.warning("Supabase not enabled, skipping database storage")
            return None
            
        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    f"{self.supabase_url}/rest/v1/hotel_quote_requests",
                    headers={
                        "apikey": self.supabase_key,
                        "Authorization": f"Bearer {self.supabase_key}",
                        "Content-Type": "application/json",
                        "Prefer": "return=representation"
                    },
                    json={
                        "email_content": email_content,
                        "email_file_name": email_file_name,
                        "email_file_size": email_file_size,
                        "proposal_file_name": proposal_file_name,
                        "proposal_file_size": proposal_file_size,
                        "proposal_url": proposal_url,
                        "urls_found": urls_found or [],
                        "sources_used": sources_used or [],
                        "content_length": content_length,
                        "firecrawl_scraped": firecrawl_scraped,
                        "firecrawl_content_length": firecrawl_content_length,
                        "processing_status": "completed"
                    }
                )
                
                if response.status_code == 201:
                    result = response.json()
                    request_id = result[0]['id'] if result else None
                    logger.info(f"Stored hotel quote request with ID: {request_id}")
                    return request_id
                else:
                    logger.error(f"Failed to store request: {response.status_code} - {response.text}")
                    return None
                    
        except Exception as e:
            logger.error(f"Error storing hotel quote request: {e}")
            return None
    
    async def store_hotel_quote_data(
        self,
        request_id: str,
        quote_data: Dict[str, Any]
    ) -> bool:
        """Store the extracted hotel quote data"""
        if not self.enabled:
            logger.warning("Supabase not enabled, skipping database storage")
            return False
            
        try:
            # Extract the main quote data
            quote_insert = {
                "request_id": request_id,
                "total_quote_status": quote_data.get('total_quote', {}).get('status'),
                "total_quote_value": quote_data.get('total_quote', {}).get('value'),
                "total_quote_currency": quote_data.get('total_quote', {}).get('currency', 'USD'),
                "total_quote_provenance": quote_data.get('total_quote', {}).get('provenance_snippet'),
                "total_quote_notes": quote_data.get('total_quote', {}).get('notes'),
                
                "guestroom_total_status": quote_data.get('guestroom_total', {}).get('status'),
                "guestroom_total_value": quote_data.get('guestroom_total', {}).get('value'),
                "guestroom_total_currency": quote_data.get('guestroom_total', {}).get('currency', 'USD'),
                "guestroom_total_provenance": quote_data.get('guestroom_total', {}).get('provenance_snippet'),
                "guestroom_total_notes": quote_data.get('guestroom_total', {}).get('notes'),
                
                "meeting_room_total_status": quote_data.get('meeting_room_total', {}).get('status'),
                "meeting_room_total_value": quote_data.get('meeting_room_total', {}).get('value'),
                "meeting_room_total_currency": quote_data.get('meeting_room_total', {}).get('currency', 'USD'),
                "meeting_room_total_provenance": quote_data.get('meeting_room_total', {}).get('provenance_snippet'),
                "meeting_room_total_notes": quote_data.get('meeting_room_total', {}).get('notes'),
                
                "fnb_total_status": quote_data.get('fnb_total', {}).get('status'),
                "fnb_total_value": quote_data.get('fnb_total', {}).get('value'),
                "fnb_total_currency": quote_data.get('fnb_total', {}).get('currency', 'USD'),
                "fnb_total_provenance": quote_data.get('fnb_total', {}).get('provenance_snippet'),
                "fnb_total_notes": quote_data.get('fnb_total', {}).get('notes'),
                
                # Extras
                "room_nights": quote_data.get('extras', {}).get('room_nights'),
                "nightly_rate": quote_data.get('extras', {}).get('nightly_rate'),
                "tax_rate_pct": quote_data.get('extras', {}).get('tax_rate_pct'),
                "service_rate_pct": quote_data.get('extras', {}).get('service_rate_pct'),
                "fnb_minimum": quote_data.get('extras', {}).get('fnb_minimum'),
                "proposal_url": quote_data.get('extras', {}).get('proposal_url'),
                "guestroom_base": quote_data.get('extras', {}).get('guestroom_base'),
                "guestroom_taxes_fees": quote_data.get('extras', {}).get('guestroom_taxes_fees'),
                "estimated_fnb_gross": quote_data.get('extras', {}).get('estimated_fnb_gross'),
                "effective_value_offsets": json.dumps(quote_data.get('extras', {}).get('effective_value_offsets', []))
            }
            
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    f"{self.supabase_url}/rest/v1/hotel_quote_data",
                    headers={
                        "apikey": self.supabase_key,
                        "Authorization": f"Bearer {self.supabase_key}",
                        "Content-Type": "application/json",
                        "Prefer": "return=representation"
                    },
                    json=quote_insert
                )
                
                if response.status_code == 201:
                    logger.info(f"Stored hotel quote data for request: {request_id}")
                    return True
                else:
                    logger.error(f"Failed to store quote data: {response.status_code} - {response.text}")
                    return False
                    
        except Exception as e:
            logger.error(f"Error storing hotel quote data: {e}")
            return False
    
    async def store_property_info(
        self,
        request_id: str,
        property_data: Dict[str, Any]
    ) -> bool:
        """Store property information"""
        if not self.enabled or not property_data:
            return False
            
        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    f"{self.supabase_url}/rest/v1/hotel_properties",
                    headers={
                        "apikey": self.supabase_key,
                        "Authorization": f"Bearer {self.supabase_key}",
                        "Content-Type": "application/json",
                        "Prefer": "return=representation"
                    },
                    json={
                        "request_id": request_id,
                        "name": property_data.get('name'),
                        "address": property_data.get('address'),
                        "phone": property_data.get('phone'),
                        "website": property_data.get('website'),
                        "contact_name": property_data.get('contact_name'),
                        "contact_email": property_data.get('contact_email'),
                        "contact_phone": property_data.get('contact_phone'),
                        "property_data": json.dumps(property_data)
                    }
                )
                
                if response.status_code == 201:
                    logger.info(f"Stored property info for request: {request_id}")
                    return True
                else:
                    logger.error(f"Failed to store property info: {response.status_code} - {response.text}")
                    return False
                    
        except Exception as e:
            logger.error(f"Error storing property info: {e}")
            return False
    
    async def store_concessions(
        self,
        request_id: str,
        concessions: List[Dict[str, Any]]
    ) -> bool:
        """Store concessions information"""
        if not self.enabled or not concessions:
            return False
            
        try:
            concession_inserts = []
            for concession in concessions:
                concession_inserts.append({
                    "request_id": request_id,
                    "concession_text": concession.get('text'),
                    "concession_type": concession.get('type'),
                    "value_impact": concession.get('value_impact'),
                    "conditions": concession.get('conditions')
                })
            
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    f"{self.supabase_url}/rest/v1/hotel_concessions",
                    headers={
                        "apikey": self.supabase_key,
                        "Authorization": f"Bearer {self.supabase_key}",
                        "Content-Type": "application/json",
                        "Prefer": "return=representation"
                    },
                    json=concession_inserts
                )
                
                if response.status_code == 201:
                    logger.info(f"Stored {len(concessions)} concessions for request: {request_id}")
                    return True
                else:
                    logger.error(f"Failed to store concessions: {response.status_code} - {response.text}")
                    return False
                    
        except Exception as e:
            logger.error(f"Error storing concessions: {e}")
            return False
    
    async def get_recent_requests(self, limit: int = 10) -> List[Dict[str, Any]]:
        """Get recent hotel quote requests"""
        if not self.enabled:
            return []
            
        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(
                    f"{self.supabase_url}/rest/v1/hotel_quote_requests?select=*&order=created_at.desc&limit={limit}",
                    headers={
                        "apikey": self.supabase_key,
                        "Authorization": f"Bearer {self.supabase_key}"
                    }
                )
                
                if response.status_code == 200:
                    return response.json()
                else:
                    logger.error(f"Failed to get recent requests: {response.status_code} - {response.text}")
                    return []
                    
        except Exception as e:
            logger.error(f"Error getting recent requests: {e}")
            return []

# Global Supabase client instance
supabase_client = SupabaseClient()
