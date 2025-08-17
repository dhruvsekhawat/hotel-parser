#!/usr/bin/env python3
"""
Test script for the Hotel Quote Parser Microservice
"""

import requests
import json
import time

# Microservice URL
MICROSERVICE_URL = "http://localhost:8000"

def test_health():
    """Test the health endpoint"""
    try:
        response = requests.get(f"{MICROSERVICE_URL}/health")
        print(f"Health check: {response.status_code}")
        print(f"Response: {response.json()}")
        return response.status_code == 200
    except Exception as e:
        print(f"Health check failed: {e}")
        return False

def test_extract_text():
    """Test text extraction"""
    test_content = """
    Hotel Quote Summary:
    
    Guestroom Total: $84,975 (55 rooms × 5 nights × $309)
    Food & Beverage: Minimum $100,000++
    Meeting Rooms: Waived with F&B minimum
    Total Quote: $184,975
    
    Tax Rate: 11.75%
    Service Charge: 25%
    """
    
    try:
        response = requests.post(
            f"{MICROSERVICE_URL}/extract-text",
            json=test_content
        )
        print(f"Text extraction: {response.status_code}")
        if response.status_code == 200:
            result = response.json()
            print("Success!")
            print(json.dumps(result, indent=2))
        else:
            print(f"Error: {response.text}")
        return response.status_code == 200
    except Exception as e:
        print(f"Text extraction failed: {e}")
        return False

def test_extract_form():
    """Test form data extraction"""
    try:
        # Create form data
        data = {
            'email_content': 'Please find attached our proposal for your event.',
            'proposal_url': 'https://example.com/proposal/123'
        }
        
        response = requests.post(
            f"{MICROSERVICE_URL}/extract",
            data=data
        )
        print(f"Form extraction: {response.status_code}")
        if response.status_code == 200:
            result = response.json()
            print("Success!")
            print(json.dumps(result, indent=2))
        else:
            print(f"Error: {response.text}")
        return response.status_code == 200
    except Exception as e:
        print(f"Form extraction failed: {e}")
        return False

def main():
    print("Testing Hotel Quote Parser Microservice")
    print("=" * 50)
    
    # Test health endpoint
    print("\n1. Testing health endpoint...")
    if not test_health():
        print("ERROR: Health check failed. Is the microservice running?")
        return
    
    # Test text extraction
    print("\n2. Testing text extraction...")
    test_extract_text()
    
    # Test form extraction
    print("\n3. Testing form extraction...")
    test_extract_form()
    
    print("\nSUCCESS: Testing completed!")

if __name__ == "__main__":
    main()
